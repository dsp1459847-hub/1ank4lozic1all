import streamlit as st
import pandas as pd
import numpy as np

# साधारण पेज सेटिंग (नो कलर, नो थीम)
st.set_page_config(page_title="Shift Prediction Engine", layout="wide")

st.title("Shift Prediction Engine")
st.write("Dream Light & Gate of Night Systems (Date-Based with Live History)")
st.markdown("---")

# 1. डेटा लोड और क्लीनिंग फंक्शन
@st.cache_data
def load_and_clean_data(file):
    try:
        df = pd.read_excel(file)
        
        # पहले कॉलम को तारीख (Date) में बदलना
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
        
        # तारीख के हिसाब से डेटा को सॉर्ट करना (पुराना पहले, नया बाद में)
        df = df.sort_values('Date').reset_index(drop=True)
        
        # शिफ्ट वाले कॉलम्स को न्यूमेरिक में बदलना (XX को NaN बनाना)
        shift_cols = [col for col in df.columns if 'S.' not in col.upper() and 'DATE' not in col.upper() and 'SEASON' not in col.upper()]
        for col in shift_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df, shift_cols
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, None

# 2. प्रेडिक्शन और इतिहास निकालने का लॉजिक
def calculate_predictions_with_history(df, shift_cols, target_idx):
    history_df = df.iloc[:target_idx]
    current_day_data = df.iloc[target_idx]
    
    if len(history_df) < 5:
        return None, None
        
    predictions = {}
    live_history_data = {}
    
    for target_shift in shift_cols:
        score_card = np.zeros(100)
        
        # --- पैटर्न 1: क्रॉस-शिफ्ट संबंध ---
        for other_shift in shift_cols:
            if target_shift != other_shift:
                today_val = current_day_data[other_shift]
                if not np.isnan(today_val):
                    matches = history_df[history_df[other_shift] == today_val][target_shift].dropna()
                    for val in matches:
                        score_card[int(val)] += 2.5

        # --- पैटर्न 2: डे-टू-डे लैग संबंध (और लाइव हिस्ट्री निकालना) ---
        prev_day_data = history_df.iloc[-1]
        prev_val = prev_day_data[target_shift]
        
        shift_history_records = []
        if not np.isnan(prev_val):
            for i in range(len(history_df) - 1):
                if history_df.iloc[i][target_shift] == prev_val:
                    next_val = history_df.iloc[i+1][target_shift]
                    if not np.isnan(next_val):
                        score_card[int(next_val)] += 4.0
                        # लाइव हिस्ट्री के लिए रिकॉर्ड सुरक्षित करना
                        match_date = history_df.iloc[i]['Date'].strftime('%Y-%m-%d') if pd.notnull(history_df.iloc[i]['Date']) else f"Row {i}"
                        shift_history_records.append({
                            "Past Date/Row": match_date,
                            "Trigger Number": int(prev_val),
                            "Next Day Opened": f"{int(next_val):02d}"
                        })

        # स्कोर कैलकुलेट करना
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

        # प्रेडिक्शन आउटपुट
        predictions[target_shift] = {
            "Single_Ank": f"{top_indices[0]:02d}",
            "Top_10_Support": [f"{x:02d}" for x in top_indices[1:11]],
            "Confidence_Score": f"{confidence_pct}%",
            "Real_Result": f"{int(current_day_data[target_shift]):02d}" if not np.isnan(current_day_data[target_shift]) else "XX"
        }
        
        # लाइव हिस्ट्री टेबल डेटा
        live_history_data[target_shift] = pd.DataFrame(shift_history_records)
        
    return predictions, live_history_data

# --- यूजर इंटरफेस (Plain UI) ---

st.sidebar.subheader("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload 0DSP0.xlsx", type=["xlsx"])

if uploaded_file is not None:
    df, shift_cols = load_and_clean_data(uploaded_file)
    
    if df is not None and len(shift_cols) > 0:
        st.sidebar.success("File Loaded Successfully.")
        
        # तारीख चुनने का विकल्प
        st.sidebar.subheader("Select Date")
        # जिन तारीखों में डेटा है केवल वही दिखाएँ
        available_dates = df['Date'].dropna().dt.date.unique()
        
        if len(available_dates) > 0:
            selected_date = st.sidebar.selectbox("Choose Date", sorted(available_dates, reverse=True))
            
            # चुनी गई तारीख का इंडेक्स निकालना
            matching_rows = df[df['Date'].dt.date == selected_date]
            idx = matching_rows.index[0]
            
            # कैलकुलेशन इंजन रन करना
            results, history_tables = calculate_predictions_with_history(df, shift_cols, idx)
            
            if results:
                st.write(f"### 📅 Selected Date: {selected_date.strftime('%d-%m-%Y')}")
                st.markdown("---")
                
                # हर शिफ्ट के लिए अलग सेक्शन (सादा लुक)
                for shift in shift_cols:
                    st.text(f"--- SHIFT: {shift} ---")
                    
                    # परिणाम और प्रेडिक्शन एक लाइन में
                    st.write(f"**Real Result (एक्सेल में जो आया):** `{results[shift]['Real_Result']}` | **Predicted Single Ank:** `{results[shift]['Single_Ank']}` | **Confidence:** {results[shift]['Confidence_Score']}")
                    st.write(f"**Support Numbers:** {', '.join(results[shift]['Top_10_Support'])}")
                    
                    # लाइव हिस्ट्री टेबल दिखाना (तुलना करने के लिए)
                    st.text(f"Live Pattern History for {shift}:")
                    if not history_tables[shift].empty:
                        st.dataframe(history_tables[shift], use_container_width=True, hide_index=True)
                    else:
                        st.write("इतिहास में इस नंबर के बाद का कोई पिछला पैटर्न नहीं मिला (New Number Pattern).")
                        
                    st.markdown("<br>", unsafe_allowed_html=True)
            else:
                st.warning("Not enough history data for this selection.")
        else:
            st.error("No valid dates found in the first column. Ensure it contains dates.")
else:
    st.info("Please upload your Excel file from the sidebar to start.")
    
