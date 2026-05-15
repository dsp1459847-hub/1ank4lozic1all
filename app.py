import streamlit as st
import pandas as pd
from collections import Counter

# Page Configuration
st.set_page_config(page_title="MAYA v60.0 - Match & Filter", layout="wide")

# High-Fi UI Styling
st.markdown("""
    <style>
    .live-card { background: #0f172a; color: #fbbf24; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .box-container { background: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 12px; margin-bottom: 15px; }
    .grid-small { display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; }
    .grid-main { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    .item-norm { background: #f8fafc; color: #475569; padding: 8px; border-radius: 6px; text-align: center; font-size: 14px; border: 1px solid #cbd5e1; }
    .item-match { background: #f0fdf4; color: #166534; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; border: 2px solid #22c55e; font-size: 18px; }
    .item-diamond { background: #fffbeb; color: #92400e; padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; border: 2px solid #f59e0b; font-size: 20px; }
    .badge { font-size: 10px; padding: 2px 5px; border-radius: 4px; margin-top: 3px; display: block; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v60.0 (Historical Match & Comparison)")

def get_history_25_30(df, target_s):
    """Pichle 3 mahine ke results se top 30 frequency jodis"""
    hist_data = df[target_s].tail(90).dropna().astype(str)
    all_vals = [v.split('.')[0].zfill(2) for v in hist_data if v.split('.')[0].isdigit()]
    counts = Counter(all_vals)
    return [k for k, v in counts.most_common(30)]

def calculate_v60(df, date_idx, target_s):
    # Standard Logic for 36-Base
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # Base 36 Selection (Original)
    base_val = -1
    for i in range(1, 15):
        if curr_pos - i >= 0 and flat_data[curr_pos-i] > 0:
            base_val = flat_data[curr_pos-i]; break
    if base_val == -1: base_val = 14
    
    d1, d2 = base_val // 10, base_val % 10
    pa, pb = (d1 + 1) % 10 if d1 != d2 else (d1 + 5) % 10, (d2 + 1) % 10
    ra, rb = (pa + 5) % 10, (pb + 5) % 10
    
    blocked_64 = set()
    for a in {pa, ra}:
        for i in range(10): blocked_64.add(f"{a}{i}")
    for b in {pb, rb}:
        for i in range(10): blocked_64.add(f"{i}{b}")
    
    t36_base = [str(i).zfill(2) for i in range(100) if str(i).zfill(2) not in blocked_64]
    
    # Current Prediction (Top 25)
    curr_target = t36_base[:25]
    
    # Historical Top 30
    hist_target = get_history_25_30(df, target_s)
    
    # 1. Matching Jodis (In both Current and History)
    matched = [j for j in curr_target if j in hist_target]
    
    # 2. Mines Logic (Bache huye in 36)
    unmatched = [j for j in t36_base if j not in matched]
    
    return t36_base, curr_target, hist_target, matched, unmatched[:16]

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    sel_date = st.selectbox("📅 Selection Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Selection Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    t36, curr, hist, matched, final_16 = calculate_v60(df, idx, target_s)
    
    # UI Header
    res_raw = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-card">LIVE RESULT: <span style="font-size:35px;">{res_raw}</span></div>', unsafe_allow_html=True)

    # Side-by-Side View
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📋 Current Prediction (Top 25)")
        st.markdown('<div class="grid-small">', unsafe_allow_html=True)
        for j in curr: st.markdown(f'<div class="item-norm">{j}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.subheader("📜 3-Month History (Top 30)")
        st.markdown('<div class="grid-small">', unsafe_allow_html=True)
        for j in hist: st.markdown(f'<div class="item-norm" style="background:#fff3e0;">{j}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # Match Logic Result
    st.subheader("💎 Strongest Matches (Result of Both Tables)")
    if matched:
        col_m = st.columns(len(matched) if len(matched) < 8 else 8)
        for i, j in enumerate(matched):
            col_m[i % 8].markdown(f'<div class="item-match">{j}</div>', unsafe_allow_html=True)
    else:
        st.write("No direct matches found. Shifting to Unmatch Logic.")

    # Final 16 Specialists
    st.subheader("✅ Final 16 Specialist Anks (Best Accuracy)")
    grid_16 = '<div class="grid-main">'
    for j in final_16: grid_16 += f'<div class="item-diamond">{j}</div>'
    grid_16 += '</div>'
    st.markdown(grid_16, unsafe_allow_html=True)

    # Backtest Compare
    st.divider()
    st.subheader("📜 Backtest Comparison (Current vs Match Logic)")
    hist_list = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        _, h_curr, h_hist, h_match, h_final = calculate_v60(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h_match: status = "💎 MATCH HIT"
            elif rv in h_final: status = "✅ SPECIALIST HIT"
            elif rv in h_curr: status = "🟡 BASIC HIT"
        hist_list.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
    
