import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# साधारण पेज सेटिंग
st.set_page_config(page_title="Shift Prediction Engine", layout="wide")

st.title("Shift Prediction Engine")
st.write("Dream Light & Gate of Night Systems")
st.markdown("---")

# 1. डेटा लोड करने का फंक्शन
@st.cache_data
def load_and_clean_data(file):
    try:
        df = pd.read_excel(file)
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
        
        shift_cols = df.columns[2:]
        for col in shift_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df, shift_cols
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, None

# 2. प्रेडिक्शन कैलकुलेटर कोर लॉजिक
def calculate_predictions(df, shift_cols, target_date_idx):
    history_df = df.iloc[:target_date_idx]
    current_day_data = df.iloc[target_date_idx]
    
    if len(history_df) < 5:
        return None
        
    predictions = {}
    
    for target_shift in shift_cols:
        score_card = np.zeros(100)
        
        # पैटर्न 1: क्रॉस-शिफ्ट संबंध
        for other_shift in shift_cols:
            if target_shift != other_shift:
                today_val = current_day_data[other_shift]
                if not np.isnan(today_val):
                    matches = history_df[history_df[other_shift] == today_val][target_shift].dropna()
                    for val in matches:
                        score_card[int(val)] += 2.5

        # पैटर्न 2: डे-टू-डे लैग संबंध
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
    
    if df is not None:
        st.sidebar.success("File Loaded.")
        
        st.sidebar.subheader("Select Date")
        available_dates = df['Date'].dropna().dt.date.unique()
        selected_date = st.sidebar.selectbox("Choose Date", sorted(available_dates, reverse=True))
        
        matching_rows = df[df['Date'].dt.date == selected_date]
        if not matching_rows.empty:
            idx = matching_rows.index[0]
            results = calculate_predictions(df, shift_cols, idx)
            
            if results:
                st.write(f"### Date: {selected_date.strftime('%d-%m-%Y')}")
                st.markdown("---")
                
                # बिना किसी कलर या थीम के साधारण टेबल/कॉलम व्यू
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
                st.warning("Not enough history data for this date.")
else:
    st.info("Please upload your Excel file from the sidebar to start.")
    
