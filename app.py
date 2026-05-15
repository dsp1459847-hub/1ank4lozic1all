import streamlit as st
import pandas as pd
from collections import Counter

# Page Configuration
st.set_page_config(page_title="MAYA v66.0 - Trend Adaptive", layout="wide")

# High-Fi UI Styling
st.markdown("""
    <style>
    .status-card { background: #0f172a; color: #fbbf24; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .pattern-box { background: #ffffff; border-radius: 10px; padding: 15px; border: 2px solid #e2e8f0; text-align: center; transition: 0.3s; }
    .pattern-box:hover { border-color: #3b82f6; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .ank-val { font-size: 32px; font-weight: bold; color: #1e40af; }
    .trend-up { color: #16a34a; font-size: 12px; font-weight: bold; }
    .trend-down { color: #dc2626; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v66.0 (Trend-Adaptive & Error Fix)")

def get_pattern_val(base_val, p_id):
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    # Core 32 Pattern Logics (Refined)
    logics = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        19: f"{(d1+2)%10}{(d2+8)%10}",
        28: f"{(d1+1)%10}{d2}",
        32: f"{(d1+5)%10}{(d2+5)%10}"
    }
    return logics.get(p_id, f"{(d1+2)%10}{(d2+2)%10}")

def analyze_adaptive_trends(df, target_shift, flat_data, curr_pos):
    """Pichle 15 din ka 'Hot' trend aur 1 saal ka 'Base' trend compare karna"""
    pattern_pool = [1, 7, 14, 19, 28, 32]
    
    # 1. Short Term Trend (Last 15 Days of this shift)
    short_term = {p: 0 for p in pattern_pool}
    for i in range(curr_pos - 90, curr_pos, 6): # Last ~15 days
        if i < 6: continue
        actual = str(flat_data[i]).zfill(2)
        prev = flat_data[i-1]
        if prev >= 0:
            for p in pattern_pool:
                if get_pattern_val(prev, p) == actual: short_term[p] += 5 # High weight to recent

    # 2. Long Term Base (Last 1 Year)
    long_term = {p: 0 for p in pattern_pool}
    for i in range(curr_pos - 1000, curr_pos, 6): # ~6-8 Months
        if i < 6: continue
        actual = str(flat_data[i]).zfill(2)
        prev = flat_data[i-1]
        if prev >= 0:
            for p in pattern_pool:
                if get_pattern_val(prev, p) == actual: long_term[p] += 1

    # Combine: (Short Term * 2) + Long Term
    final_scores = {p: (short_term[p] + long_term[p]) for p in pattern_pool}
    best_patterns = sorted(final_scores, key=final_scores.get, reverse=True)
    
    return best_patterns[:3], final_scores

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'GZB': 'GB'})
    
    shifts = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) >= 0 else -1)
            
    sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift:", options=shifts)
    
    date_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    curr_pos = (date_idx * 6) + shifts.index(target_s)
    
    # Adaptive Trigger
    best_p_ids, scores = analyze_adaptive_trends(df, target_s, flat_data, curr_pos)
    
    # UI Header
    res_raw = str(df.iloc[date_idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="status-card"><h1>SHIFT: {target_s} | RESULT: {res_raw}</h1><p>Adaptive Scanner: Trending Patterns Only</p></div>', unsafe_allow_html=True)
    
    # Display Predictions
    base_val = flat_data[curr_pos - 1]
    cols = st.columns(3)
    for i, pid in enumerate(best_p_ids):
        pred = get_pattern_val(base_val, pid)
        with cols[i]:
            st.markdown(f"""
                <div class="pattern-box">
                    <p style="color:gray; font-size:12px;">Adaptive Pattern {pid}</p>
                    <span class="ank-val">{pred}</span><br>
                    <span class="trend-up">Trend Score: {scores[pid]}</span>
                </div>
            """, unsafe_allow_html=True)

    # History Analysis
    st.divider()
    st.subheader(f"📜 {target_s} - Adaptive Accuracy Backtest")
    hist_list = []
    for i in range(date_idx - 15, date_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + shifts.index(target_s)
        h_ids, _ = analyze_adaptive_trends(df, target_s, flat_data, p_idx)
        h_base = flat_data[p_idx - 1]
        h_preds = [get_pattern_val(h_base, pid) for pid in h_ids]
        
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 TREND HIT"
            
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
    
