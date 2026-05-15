import streamlit as st
import pandas as pd
from collections import Counter

st.set_page_config(page_title="MAYA v65.0 - Shift Specialist", layout="wide")

st.markdown("""
    <style>
    .shift-header { background: #1e293b; color: #fbbf24; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .pattern-card { background: #ffffff; border-top: 4px solid #ef4444; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .ank-display { font-size: 28px; font-weight: bold; color: #1e40af; display: block; margin: 10px 0; }
    .accuracy-tag { font-size: 12px; color: #16a34a; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v65.0 (Shift-Specific Pattern Hunter)")

def get_pattern_val(base_val, p_id):
    """32 Patterns ka Core Logic (Fixed)"""
    if base_val <= 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    if p_id == 1: return f"{(d1+1)%10}{(d2+1)%10}"
    if p_id == 7: return f"{(d1+5)%10}{(d2+1)%10}"
    if p_id == 14: return f"{d2}{(d1+2)%10}"
    if p_id == 28: return f"{(d1+1)%10}{d2}"
    if p_id == 32: return f"{(d1+5)%10}{(d2+5)%10}"
    return f"{(d1+2)%10}{(d2+2)%10}"

def get_best_patterns_for_shift(df, target_shift, flat_data, curr_pos):
    """Har shift ke liye pichle 8 mahine ke best patterns nikalna"""
    # Pattern pool to test
    pattern_pool = [1, 7, 14, 28, 32]
    shift_performance = {p: 0 for p in pattern_pool}
    
    # Shifts in sequence
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    target_s_idx = shifts_order.index(target_shift)
    
    # Back-scan pichle 150-200 records (approx 8 mahine)
    # Sirf usi shift ka data check karenge
    for i in range(curr_pos - 120, curr_pos, 6): # Jump by 6 to stay on the same shift
        if i < 6: continue
        actual_res = str(flat_data[i]).zfill(2)
        
        # Is shift ke liye pichle base se kaunsa pattern match hua tha?
        prev_base = flat_data[i-1] # Previous shift in chain
        if prev_base > 0:
            for p_id in pattern_pool:
                if get_pattern_val(prev_base, p_id) == actual_res:
                    shift_performance[p_id] += 1
                    
    # Top 3 patterns for THIS specific shift
    sorted_patterns = sorted(shift_performance, key=shift_performance.get, reverse=True)
    return sorted_patterns[:3], shift_performance

uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'GZB': 'GB', 'GZ': 'GB'})
    
    # Flatten data for chain analysis
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) >= 0 else -1)
            
    sel_date = st.selectbox("📅 Selection Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Selection Shift:", options=shifts_order)
    
    date_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # Analysis
    best_p_ids, all_scores = get_best_patterns_for_shift(df, target_s, flat_data, curr_pos)
    
    # UI: Header
    st.markdown(f'<div class="shift-header"><h1>SHIFT: {target_s}</h1><p>Pichle 8 mahine ke top patterns sirf is shift ke liye</p></div>', unsafe_allow_html=True)
    
    # Predictions
    st.subheader(f"💎 Top 3 Specialist Patterns for {target_s}")
    cols = st.columns(3)
    base_val = flat_data[curr_pos - 1] # Trigger from previous shift
    
    for i, p_id in enumerate(best_p_ids):
        pred_ank = get_pattern_val(base_val, p_id)
        with cols[i]:
            st.markdown(f"""
                <div class="pattern-card">
                    <p style="color:gray;">Pattern No. {p_id}</p>
                    <span class="ank-display">{pred_ank}</span>
                    <span class="accuracy-tag">Hist Score: {all_scores[p_id]}</span>
                </div>
            """, unsafe_allow_html=True)

    # History Specific to this Logic
    st.divider()
    st.subheader(f"📜 {target_s} Shift - History Backtest")
    hist_list = []
    # Test last 10 days of THIS shift
    for i in range(date_idx - 10, date_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + shifts_order.index(target_s)
        h_best_ids, _ = get_best_patterns_for_shift(df, target_s, flat_data, p_idx)
        h_base = flat_data[p_idx - 1]
        h_preds = [get_pattern_val(h_base, pid) for pid in h_best_ids]
        
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 SHIFT HIT"
            
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    
    st.table(pd.DataFrame(hist_list))
    
