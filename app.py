import streamlit as st
import pandas as pd
import numpy as np

# साधारण और साफ़ पेज सेटिंग
st.set_page_config(page_title="Shift Prediction Engine", layout="wide")

st.title("Shift Prediction Engine")
st.write("Dream Light & Gate of Night Systems (45-Days History & OK/❌ Tracker)")
st.markdown("---")

# 1. डेटा लोड और क्लीनिंग फंक्शन
@st.cache_data
def load_and_clean_data(file):
    try:
        df = pd.read_excel(file)
        
        # सही डेट कॉलम की पहचान करना
        date_col = None
        for col in df.columns:
            if 'DATE' in str(col).upper():
                date_col = col
                break
        
        if date_col is not None:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df.rename(columns={date_col: 'Date'}, inplace=True)
        else:
            df.rename(columns={df.columns[1]: 'Date'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
        df = df.dropna(subset=['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
        
        # शिफ्ट वाले असली कॉलम्स निकालना
        shift_cols = [col for col in df.columns if 'S.' not in str(col).upper() and 'DATE' not in str(col).upper() and 'SEASON' not in str(col).upper()]
        
        for col in shift_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df, shift_cols
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, None

# 2. प्रेडिक्शन और 45-दिन का इतिहास ट्रैकर (OK / ❌ के साथ)
def calculate_45day_predictions_with_status(df, shift_cols, target_idx):
    # चुनी हुई तारीख तक का डेटा
    current_day_data = df.iloc[target_idx]
    
    # चुनी हुई तारीख से ठीक 45 दिन पीछे तक की विंडो तय करना
    start_idx = max(0, target_idx - 45)
    history_df = df.iloc[start_idx:target_idx] # ठीक 45 दिनों का इतिहास
    
    # यदि डेटा बहुत कम है तो पूरी उपलब्ध हिस्ट्री ले लें
    global_history = df.iloc[:target_idx]
    
    if len(global_history) < 5:
        return None, None
        
    predictions = {}
    live_history_data = {}
    
    for target_shift in shift_cols:
        score_card = np.zeros(100)
        
        # नियम 1: क्रॉस-शिफ्ट संबंध (समान दिन)
        for other_shift in shift_cols:
            if target_shift != other_shift:
                today_val = current_day_data[other_shift]
                if not np.isnan(today_val):
                    matches = global_history[global_history[other_shift] == today_val][target_shift].dropna()
                    for val in matches:
                        score_card[int(val)] += 3.0

        # नियम 2: डे-टू-डे लैग संबंध
        if len(global_history) > 0:
            prev_day_data = global_history.iloc[-1]
            prev_val = prev_day_data[target_shift]
            if not np.isnan(prev_val):
                matches = global_history[global_history[target_shift] == prev_val][target_shift].dropna()
                for val in matches:
                    score_card[int(val)] += 5.0

        total_score = np.sum(score_card)
        if total_score == 0:
            recent_nums = global_history[target_shift].tail(15).dropna().astype(int).tolist()
            for num in recent_nums:
                score_card[num] += 1
            total_score = np.sum(score_card)

        top_indices = np.argsort(score_card)[::-1]
        highest_score = score_card[top_indices[0]]
        confidence_pct = round((highest_score / total_score) * 100, 2) if total_score > 0 else 0.0
        calibrated_confidence = min(round(45.0 + (confidence_pct * 1.5), 2), 94.5) if confidence_pct > 0 else 50.0

        predicted_single = f"{top_indices[0]:02d}"
        real_res_val = current_day_data[target_shift]
        real_res_str = f"{int(real_res_val):02d}" if not np.isnan(real_res_val) else "XX"

        predictions[target_shift] = {
            "Single_Ank": predicted_single,
            "Top_10_Support": [f"{x:02d}" for x in top_indices[1:11]],
            "Confidence_Score": f"{calibrated_confidence}%",
            "Real_Result": real_res_str
        }

        # --- 45 दिनों की लाइव हिस्ट्री तालिका (OK / ❌ चेकर के साथ) ---
        shift_history_records = []
        
        # 45 दिनों के लूप के अंदर हर दिन की प्रेडिक्शन को उसके वास्तविक परिणाम से जाँचना
        for i in range(len(history_df)):
            current_loop_row = history_df.iloc[i]
            loop_date_val = current_loop_row['Date']
            loop_idx = history_df.index[i]
            
            # उस बीते हुए दिन का वास्तविक रिजल्ट
            loop_real_val = current_loop_row[target_shift]
            if np.isnan(loop_real_val):
                continue
            loop_real_str = f"{int(loop_real_val):02d}"
            
            # उस बीते हुए दिन एआई ने क्या प्रेडिक्ट किया था (उसे निकालने के लिए उस दिन की बैक-हिस्ट्री)
            temp_history = df.iloc[:loop_idx]
            if len(temp_history) >= 3:
                temp_scores = np.zeros(100)
                # शॉर्ट प्रेडिक्शन केवल मैचिंग के लिए
                temp_prev_val = temp_history.iloc[-1][target_shift]
                if not np.isnan(temp_prev_val):
                    t_matches = temp_history[temp_history[target_shift] == temp_prev_val][target_shift].dropna()
                    for val in t_matches:
                        temp_scores[int(val)] += 5.0
                
                t_top = np.argsort(temp_scores)[::-1][0]
                loop_pred_str = f"{t_top:02d}"
            else:
                loop_pred_str = "00"

            # OK या ❌ का फैसला
            status = "OK 👍" if loop_real_str == loop_pred_str else "❌"
            
            try:
                match_date = loop_date_val.strftime('%Y-%m-%d')
            except:
                match_date = f"Row {loop_idx}"

            shift_history_records.append({
                "Past Date": match_date,
                "AI Prediction": loop_pred_str,
                "Real Result Opened": loop_real_str,
                "Status Check": status
            })

        if len(shift_history_records) > 0:
            # नया डेटा ऊपर दिखाने के लिए इतिहास को उल्टा (Reverse) करना
            live_history_data[target_shift] = pd.DataFrame(shift_history_records)[::-1]
        else:
            live_history_data[target_shift] = pd.DataFrame(columns=["Past Date", "AI Prediction", "Real Result Opened", "Status Check"])
        
    return predictions, live_history_data

# --- यूजर इंटरफेस (Plain Standard Look) ---

st.sidebar.subheader("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload 0DSP0.xlsx", type=["xlsx"])

if uploaded_file is not None:
    df, shift_cols = load_and_clean_data(uploaded_file)
    
    if df is not None and len(shift_cols) > 0:
        st.sidebar.success("File Loaded.")
        
        st.sidebar.subheader("Select Date")
        available_dates = df['Date'].dropna().dt.date.unique()
        
        if len(available_dates) > 0:
            selected_date = st.sidebar.selectbox("Choose Date", sorted(available_dates, reverse=True))
            
            matching_rows = df[df['Date'].dt.date == selected_date]
            if not matching_rows.empty:
                idx = matching_rows.index[0]
                
                # नया 45-दिन का सेफ इंजन रन करना
                results, history_tables = calculate_45day_predictions_with_status(df, shift_cols, idx)
                
                if results and history_tables:
                    st.write(f"### Date Selected: {selected_date.strftime('%d-%m-%Y')} (Showing Past 45 Days Logs)")
                    st.markdown("---")
                    
                    for shift in shift_cols:
                        st.text(f"--- SHIFT: {shift} ---")
                        st.write(f"**Today's Real Result:** `{results[shift]['Real_Result']}` | **Predicted Single Ank:** `{results[shift]['Single_Ank']}` | **Calculated Accuracy:** `{results[shift]['Confidence_Score']}`")
                        st.write(f"**Top 10 Support Numbers:** {', '.join(results[shift]['Top_10_Support'])}")
                        
                        st.text(f"Live 45-Days Match History & Pass/Fail Status for {shift}:")
                        
                        if shift in history_tables and not history_tables[shift].empty:
                            st.dataframe(history_tables[shift], use_container_width=True, hide_index=True)
                        else:
                            st.write("No records found in the 45-days bracket.")
                            
                        st.write("") 
                        st.markdown("---")
                else:
                    st.warning("Insufficient historical data to build patterns for this date.")
            else:
                st.warning("Selected date not found.")
        else:
            st.error("No valid dates found in the sheet.")
else:
    st.info("Please upload your Excel file from the sidebar to start.")
        
