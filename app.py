import streamlit as st
import pandas as pd
from collections import Counter

st.set_page_config(page_title="MAYA v64.0 - Step Pattern Matrix", layout="wide")

st.markdown("""
    <style>
    .matrix-box { background: #1e293b; color: #fbbf24; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #3b82f6; }
    .pattern-card { background: #ffffff; border-left: 5px solid #3b82f6; padding: 12px; border-radius: 8px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .ank-val { font-size: 24px; font-weight: bold; color: #1e40af; }
    .eff-text { font-size: 12px; color: #16a34a; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v64.0 (History-Linked Step Patterns)")

def get_pattern_logic(val, p_type):
    """32 Patterns mein se top types ka logic"""
    if val == -1: return "XX"
    d1, d2 = val // 10, val % 10
    if p_type == 7: return f"{(d1+5)%10}{(d2+1)%10}"
    if p_type == 14: return f"{d2}{(d1+2)%10}"
    if p_type == 28: return f"{(d1+1)%10}{d2}"
    return f"{(d1+2)%10}{(d2+2)%10}" # Pattern 32 fallback

def analyze_step_pattern_efficiency(flat_data, curr_pos):
    """Pichle 90 timeframes mein kaunsa pattern sabse zyada pass hua"""
    pattern_scores = {7: 0, 14: 0, 28: 0, 32: 0}
    
    # Scan last 50 shifts to see which pattern followed which step-jump
    for p in range(curr_pos - 50, curr_pos):
        if p < 20: continue
        actual_res = str(flat_data[p]).zfill(2)
        
        # Check each Step-Jump (Time-Frame) from 1 to 20
        for step in range(1, 21):
            prev_val = flat_data[p - step]
            if prev_val != -1:
                # Check if any of our patterns on this 'step-value' match the 'actual result'
                for pt in [7, 14, 28, 32]:
                    if get_pattern_logic(prev_val, pt) == actual_res:
                        pattern_scores[pt] += 1
    
    # Best Pattern according to Time-Frame history
    best_p = max(pattern_scores, key=pattern_scores.get)
    return best_p, pattern_scores

def calculate_v64(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Analyze which pattern is currently 'HOT' based on Time-Frames
    best_pattern_id, all_scores = analyze_step_pattern_efficiency(flat_data, curr_pos)
    
    # 2. Prediction: Apply this best pattern to the last 3-4 Time-Frames
    final_predictions = []
    for step in [1, 2, 5, 7]: # Common Time-Frames
        base_val = flat_data[curr_pos - step]
        if base_val != -1:
            pred = get_pattern_logic(base_val, best_pattern_id)
            if pred not in final_predictions:
                final_predictions.append(pred)
                
    return final_predictions, best_pattern_id, all_scores

uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'GZ': 'GB', 'GZB': 'GB'})

    sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    preds, best_id, scores = calculate_v64(df, idx, target_s)
    
    # UI Output
    res_raw = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="matrix-box">RESULT: {res_raw} | <b>HOT PATTERN: No. {best_id}</b></div>', unsafe_allow_html=True)

    st.subheader("🧪 Time-Frame Pattern Analysis")
    cols = st.columns(4)
    for i, (pid, score) in enumerate(scores.items()):
        with cols[i]:
            st.markdown(f"""
                <div class="pattern-card">
                    <p style="color:gray; font-size:11px;">Pattern {pid}</p>
                    <span style="font-size:18px; font-weight:bold;">Score: {score}</span>
                    <p class="eff-text">{"🔥 ACTIVE" if pid == best_id else "💤 STABLE"}</p>
                </div>
            """, unsafe_allow_html=True)

    st.divider()
    
    st.subheader("💎 Final Strong Anks (Applied to Time-Frames)")
    if preds:
        p_cols = st.columns(len(preds))
        for i, p in enumerate(preds):
            p_cols[i].markdown(f'<div class="pattern-card" style="text-align:center;"><span class="ank-val">{p}</span></div>', unsafe_allow_html=True)

    # History
    st.divider()
    st.subheader("📜 15-Shift Pattern Accuracy Backtest")
    hist_list = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 15, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        h_preds, _, _ = calculate_v64(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 PATTERN HIT"
        hist_list.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
                
