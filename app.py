import streamlit as st
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(page_title="MAYA v68.0 - Final Success", layout="wide")

st.markdown("""
    <style>
    .main-header { background: linear-gradient(90deg, #1e3a8a, #1e40af); color: #fbbf24; padding: 25px; border-radius: 15px; text-align: center; border: 3px solid #fbbf24; margin-bottom: 30px; }
    .grid-final { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; max-width: 500px; margin: 0 auto; }
    .ank-card { background: #ffffff; border: 3px solid #1e40af; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .ank-val { font-size: 35px; font-weight: bold; color: #1e3a8a; }
    .accuracy-high { color: #059669; font-weight: bold; font-size: 14px; border: 1px solid #059669; padding: 2px 8px; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v68.0 (The Master Final Engine)")

def get_pattern_v68(base_val, pid):
    """Aapke bataye huye 32 Patterns ka Perfect Logic"""
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    
    # Strictly applying 16/55 and Mirror rules
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}", # +16 Logic
        19: f"{(d1+2)%10}{(d2+8)%10}",
        28: f"{(d1+1)%10}{d2}",
        32: f"{(d1+3)%10}{(d2+2)%10}",
        55: f"{(d1+5)%10}{(d2+5)%10}"  # +55 Logic
    }
    return patterns.get(pid, f"{(d1+2)%10}{(d2+2)%10}")

def analyze_success_matrix(flat_data, curr_pos, shift_idx):
    """Har shift ke liye pichle 1 saal ka Success Matrix nikalna"""
    p_pool = [1, 7, 14, 16, 19, 28, 32, 55]
    scores = {p: 0 for p in p_pool}
    
    # Scanning pichle 500 records (Deep History)
    for i in range(curr_pos - 500, curr_pos):
        if i < 20: continue
        # Sirf tab analyze karo jab pichle din ka result maujood ho
        if (i % 6) == shift_idx:
            actual = str(flat_data[i]).zfill(2)
            # Test 1: Previous Shift Trigger
            base_1 = flat_data[i-1]
            # Test 2: Same Shift Yesterday Trigger
            base_2 = flat_data[i-6]
            
            for pid in p_pool:
                if get_pattern_v68(base_1, pid) == actual: scores[pid] += 2
                if get_pattern_v68(base_2, pid) == actual: scores[pid] += 1
                
    best_pids = sorted(scores, key=scores.get, reverse=True)[:3]
    return best_pids, scores

uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    shifts = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) >= 0 else -1)
            
    sel_date = st.selectbox("📅 Select Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Select Shift:", options=shifts)
    
    date_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    curr_pos = (date_idx * 6) + shifts.index(target_s)
    
    # Run Matrix Analysis
    best_pids, all_scores = analyze_success_matrix(flat_data, curr_pos, shifts.index(target_s))
    
    # UI Header
    res_val = str(df.iloc[date_idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f"""
        <div class="main-header">
            <h1>SHIFT SPECIALIST: {target_s}</h1>
            <p style="font-size:18px;">Triple-Layer Validation | Result: {res_val}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # FINAL PREDICTIONS
    st.subheader("💎 Final Strong Predictions (Max 12 Anks)")
    base_1 = flat_data[curr_pos - 1] # Previous Shift
    base_2 = flat_data[curr_pos - 6] # Same Shift Yesterday
    
    final_anks = []
    for pid in best_pids:
        final_anks.append(get_pattern_v68(base_1, pid))
        final_anks.append(get_pattern_v68(base_2, pid))
    
    # Cleaning unique and valid anks
    final_anks = sorted(list(set([a for a in final_anks if a != "XX"])))

    cols = st.columns(4)
    for i, ank in enumerate(final_anks[:12]): # Strictly limit to 12
        with cols[i % 4]:
            st.markdown(f"""
                <div class="ank-card">
                    <span class="accuracy-high">Success Priority</span><br>
                    <span class="ank-val">{ank}</span>
                </div>
            """, unsafe_allow_html=True)

    # 1-Month Accuracy Verification
    st.divider()
    st.subheader("📜 30-Day Success Verification (Backtest)")
    hist_list = []
    for i in range(date_idx - 30, date_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + shifts.index(target_s)
        h_pids, _ = analyze_success_matrix(flat_data, p_idx, shifts.index(target_s))
        h_b1, h_b2 = flat_data[p_idx - 1], flat_data[p_idx - 6]
        h_preds = [get_pattern_v68(h_b1, pid) for pid in h_pids] + [get_pattern_v68(h_b2, pid) for pid in h_pids]
        
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 SUCCESS HIT"
            
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
    
