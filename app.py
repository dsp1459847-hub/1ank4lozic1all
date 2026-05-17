import streamlit as st
import pandas as pd
import numpy as np

# साधारण पेज सेटिंग
st.set_page_config(page_title="Shift Prediction Engine", layout="wide")

st.title("Shift Prediction Engine")
st.write("Dream Light & Gate of Night Systems")
st.markdown("---")

# 1. डेटा लोड करने का फंक्शन (आपकी फ़ाइल के स्ट्रक्चर के अनुसार)
@st.cache_data
def load_and_clean_data(file):
    try:
        df = pd.read_excel(file)
        
        # 'S. NUMBER' या 'S.No' जैसे इंडेक्स कॉलम को हटाना या पहचानना
        # हम मान रहे हैं कि पहला कॉलम इंडेक्स/सीरियल नंबर है और दूसरा कॉलम डेट हो सकता है, या सीधे शिफ्ट्स हैं।
        # सुरक्षा के लिए हम केवल उन्हीं कॉलम्स को लेंगे जो शिफ्ट का डेटा हैं।
        
        # सभी कॉलम्स में से टेक्स्ट या 'XX' को हटाकर नंबर में बदलना
        for col in df.columns:
            if col != 'Date' and 'DATE' not in col.upper() and 'S.' not in col.upper():
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        # शिफ्ट वाले कॉलम्स की लिस्ट बनाना (S. NUMBER और Date को छोड़कर)
        shift_cols = [col for col in df.columns if 'S.' not in col.upper() and 'DATE' not in col.upper() and 'SEASON' not in col.upper()]
        
        return df, shift_cols
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, None

# 2. प्रेडिक्शन कैलकुलेटर कोर लॉजिक (S. NUMBER / Index के आधार पर)
def calculate_predictions(df, shift_cols, target_idx):
    # टारगेट इंडेक्स से पहले का सारा इतिहास (History)
    history_df = df.iloc[:target_idx]
    current_day_data = df.iloc[target_idx]
    
    if len(history_df) < 5:
        return None
        
    predictions = {}
    
    for target_shift in shift_cols:
        score_card = np.zeros(100)
        
        # पैटर्न 1: क्रॉस-शिफ्ट संबंध (उसी रो की बाकी शिफ्ट्स का असर)
        for other_shift in shift_cols:
            if target_shift != other_shift:
                today_val = current_day_data[other_shift]
                if not np.isnan(today_val):
                    matches = history_df[history_df[other_shift] == today_val][target_shift].dropna()
                    for val in matches:
                        score_card[int(val)] += 2.5

        # पैटर्न 2: डे-टू-डे लैग संबंध (पिछली रो/दिन का असर)
        prev_day_data = history_df.iloc[-1]
        prev_val = prev_day_data[target_shift]
        if not np.isnan(prev_val):
            for i in range(len(history_df) - 1):
                if history_df.iloc[i][target_shift] == prev_val:
                    next_val = history_df.iloc[i+1][target_shift]
                    if not np.isnan(next_val):
                        score_card[int(next_val)] += 4.0

        total_score = np.sum(score_card)
        if total_score == 0:
            recent_numbers = history_df[target_shift].tail(15).dropna().astype(int).tolist()
            if recent_numbers:
                for num in recent_numbers:
                    score_card[num] += 1
            total_score = np.sum(score_card)

        top_indices = np.argsort(score_card)[::-1]
        highest_score = score_card[top_indices[0]]
        confidence_pct = round((highest_score / total_score) * 100, 2) if total_score > 0 else 0.0

        predictions[target_shift] = {
            "Single_Ank": f"{top_indices[0]:02d}",
            "Top_10_Support": [f"{x:02d}" for x in top_indices[1:11]],
            "Confidence_Score": f"{confidence_pct}%"
        }
    return predictions

# --- यूजर इंटरफेस (Plain UI) ---

st.sidebar.subheader("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload 0DSP0.xlsx", type=["xlsx"])

if uploaded_file is not None:
    df, shift_cols = load_and_clean_data(uploaded_file)
    
    if df is not None and len(shift_cols) > 0:
        st.sidebar.success("File Loaded Successfully.")
        
        # तारीख की जगह "S. NUMBER" या Row Index चुनने का विकल्प ताकि एरर न आए
        st.sidebar.subheader("Select Row / Serial Number")
        
        # अगर शीट में 'S. NUMBER' कॉलम है तो उसे दिखाएँ, नहीं तो इंडेक्स नंबर दिखाएँ
        s_num_col = [col for col in df.columns if 'S.' in col.upper()]
        
        if s_num_col:
            available_rows = df[s_num_col[0]].dropna().tolist()
            selected_row = st.sidebar.selectbox("Choose Serial Number", sorted(available_rows, reverse=True))
            idx = df[df[s_num_col[0]] == selected_row].index[0]
        else:
            available_rows = list(range(len(df)))
            selected_row = st.sidebar.selectbox("Choose Row Index", sorted(available_rows, reverse=True))
            idx = selected_row
        
        # कैलकुलेशन शुरू करना
        results = calculate_predictions(df, shift_cols, idx)
        
        if results:
            if s_num_col:
                st.write(f"### Analysis for Serial Number: {selected_row}")
            else:
                st.write(f"### Analysis for Row Index: {selected_row}")
            st.markdown("---")
            
            # साधारण टेबल/कॉलम व्यू (नो कलर)
            cols = st.columns(len(shift_cols))
            for i, shift in enumerate(shift_cols):
                with cols[i]:
                    st.text(f"Shift: {shift}")
                    st.text(f"Confidence: {results[shift]['Confidence_Score']}")
                    st.metric(label="Single Ank", value=results[shift]['Single_Ank'])
                    st.text("Support:")
                    st.write(", ".join(results[shift]['Top_10_Support']))
                    st.markdown("---")
        else:
            st.warning("Not enough history data for this selection.")
    else:
        st.error("Could not find any valid shift columns. Please check sheet columns.")
else:
    st.info("Please upload your Excel file from the sidebar to start.")
        
