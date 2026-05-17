import streamlit as st
import pandas as pd
import numpy as np

# साधारण और साफ़ पेज सेटिंग
st.set_page_config(page_title="Shift Prediction Engine", layout="wide")

st.title("Shift Prediction Engine")
st.write("Dream Light & Gate of Night Systems (Fixed Date & Upgraded Pattern Frequency)")
st.markdown("---")

# 1. डेटा लोड और क्लीनिंग फंक्शन (एरर फिक्स)
@st.cache_data
def load_and_clean_data(file):
    try:
        df = pd.read_excel(file)
        
        # एरर फिक्स: सही डेट कॉलम की पहचान करना
        # हम उस कॉलम को ढूंढेंगे जिसके नाम में 'DATE' हो, न कि 'S. NUMBER'
        date_col = None
        for col in df.columns:
            if 'DATE' in str(col).upper():
                date_col = col
                break
        
        if date_col is not None:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df.rename(columns={date_col: 'Date'}, inplace=True)
        else:
            # अगर DATE नाम का कॉलम नहीं मिला, तो मान लेते हैं दूसरा कॉलम डेट है (S. NUMBER के बाद वाला)
            df.rename(columns={df.columns[1]: 'Date'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
        # डेटा को तारीख के अनुसार सही क्रम में लगाना
        df = df.sort_values('Date').reset_index(drop=True)
        
        # शिफ्ट वाले असली कॉलम्स निकालना (S. NUMBER, DATE और SEASON को छोड़कर)
        shift_cols = [col for col in df.columns if 'S.' not in str(col).upper() and 'DATE' not in str(col).upper() and 'SEASON' not in str(col).upper()]
        
        # सभी शिफ्ट वैल्यूज को केवल नंबर्स में बदलना
        for col in shift_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df, shift_cols
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, None

# 2. अपग्रेड की गई वेकेंसी/फ्रीक्वेंसी वाला कैलकुलेटर लॉजिक
def calculate_predictions_advanced(df, shift_cols, target_idx):
    history_df = df.iloc[:target_idx]
    current_day_data = df.iloc[target_idx]
    
    # विश्लेषण के लिए कम से कम 10 दिनों का इतिहास होना जरूरी है
    if len(history_df) < 10:
        return None, None
        
    predictions = {}
    live_history_data = {}
    
    for target_shift in shift_cols:
        score_card = np.zeros(100)
        
        # नियम 1: क्रॉस-शिफ्ट इंटरफेरेंस (समान दिन का प्रभाव)
        for other_shift in shift_cols:
            if target_shift != other_shift:
                today_val = current_day_data[other_shift]
                if not np.isnan(today_val):
                    matches = history_df[history_df[other_shift] == today_val][target_shift].dropna()
                    for val in matches:
                        score_card[int(val)] += 3.0 # हाई फ्रीक्वेंसी वेट

        # नियम 2: अपग्रेडेड 3-डे-लूप वेकेंसी (पिछले 3 दिनों के अंकों का इतिहास में मिलान)
        # हम देखेंगे कि अतीत में जब भी इस शिफ्ट में यह विशिष्ट अंक आया, तो अगले दिन क्या खुला
        prev_day_data = history_df.iloc[-1]
        prev_val = prev_day_data[target_shift]
        
        shift_history_records = []
        if not np.isnan(prev_val):
            for i in range(len(history_df) - 1):
                if history_df.iloc[i][target_shift] == prev_val:
                    next_val = history_df.iloc[i+1][target_shift]
                    if not np.isnan(next_val):
                        score_card[int(next_val)] += 5.0 # सबसे मजबूत वेटेज
                        
                        # लाइव हिस्ट्री रिकॉर्ड्स तैयार करना
                        match_date = history_df.iloc[i]['Date'].strftime('%Y-%m-%d') if pd.notnull(history_df.iloc[i]['Date']) else f"Row {i}"
                        shift_history_records.append({
                            "Past Date": match_date,
                            "Trigger Number": int(prev_val),
                            "Next Day Opened": f"{int(next_val):02d}"
                        })

        # नियम 3: हॉट नंबर्स वेकेंसी (हालिया 30 दिनों में सबसे ज्यादा आवृत्ति वाले अंक)
        recent_30 = history_df[target_shift].tail(30).dropna().astype(int).tolist()
        for num in recent_30:
            score_card[num] += 1.0 # निरंतरता बोनस

        # गणना और स्कोरिंग
        total_score = np.sum(score_card)
        top_indices = np.argsort(score_card)[::-1]
        
        highest_score = score_card[top_indices[0]]
        confidence_pct = round((highest_score / total_score) * 100, 2) if total_score > 0 else 0.0

        # प्रेडिक्शन आउटपुट शीट डाटा के अनुसार
        predictions[target_shift] = {
            "Single_Ank": f"{top_indices[0]:02d}",
            "Top_10_Support": [f"{x:02d}" for x in top_indices[1:11]],
            "Confidence_Score": f"{confidence_pct}%",
            "Real_Result": f"{int(current_day_data[target_shift]):02d}" if not np.isnan(current_day_data[target_shift]) else "XX"
        }
        
        live_history_data[target_shift] = pd.DataFrame(shift_history_records)
        
    return predictions, live_history_data

# --- यूजर इंटरफेस (Plain Standard Look) ---

st.sidebar.subheader("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload 0DSP0.xlsx", type=["xlsx"])

if uploaded_file is not None:
    df, shift_cols = load_and_clean_data(uploaded_file)
    
    if df is not None and len(shift_cols) > 0:
        st.sidebar.success("File Loaded.")
        
        # तारीख चुनने का विकल्प
        st.sidebar.subheader("Select Date")
        available_dates = df['Date'].dropna().dt.date.unique()
        
        if len(available_dates) > 0:
            selected_date = st.sidebar.selectbox("Choose Date", sorted(available_dates, reverse=True))
            
            # तारीख का इंडेक्स मैच करना
            matching_rows = df[df['Date'].dt.date == selected_date]
            idx = matching_rows.index[0]
            
            # एडवांस कैलकुलेशन इंजन रन करना
            results, history_tables = calculate_predictions_advanced(df, shift_cols, idx)
            
            if results:
                st.write(f"### Date Selected: {selected_date.strftime('%d-%m-%Y')}")
                st.markdown("---")
                
                # हर शिफ्ट का अलग सेक्शन बिना किसी भड़कीले रंग के
                for shift in shift_cols:
                    st.text(f"--- SHIFT: {shift} ---")
                    
                    # रियल रिजल्ट बनाम प्रेडिक्शन एक सादे फॉर्मेट में
                    st.write(f"**Real Result:** `{results[shift]['Real_Result']}` | **Predicted Single Ank:** `{results[shift]['Single_Ank']}` | **Confidence:** {results[shift]['Confidence_Score']}")
                    st.write(f"**Support Numbers:** {', '.join(results[shift]['Top_10_Support'])}")
                    
                    # लाइव इतिहास की तालिका
                    st.text(f"Live History Patterns for {shift}:")
                    if not history_tables[shift].empty:
                        st.dataframe(history_tables[shift].tail(10), use_container_width=True, hide_index=True)
                    else:
                        st.write("No matching past patterns found for this specific transition.")
                        
                    st.markdown("<br>", unsafe_allowed_html=True)
            else:
                st.warning("Insufficient historical data to build patterns for this date.")
        else:
            st.error("No valid dates found in the sheet. Please verify column formatting.")
else:
    st.info("Please upload your Excel file from the sidebar to start.")
                        
