import streamlit as st
import pandas as pd
from collections import Counter

st.set_page_config(page_title="MAYA v63.0 - Data Fix & Split", layout="wide")

st.markdown("""
    <style>
    .live-card { background: #0f172a; color: #fbbf24; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; }
    .split-container { display: flex; gap: 20px; margin-top: 20px; }
    .match-pane { flex: 1; background: #f0fdf4; border: 2px solid #22c55e; padding: 15px; border-radius: 12px; }
    .unmatch-pane { flex: 1; background: #fef2f2; border: 2px solid #ef4444; padding: 15px; border-radius: 12px; }
    .grid-ank { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    .ank-box { background: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v63.0 (Data Correction & Split Tracking)")

def get_clean_val(val):
    """Excel data ko strictly clean karne ke liye"""
    try:
        s_val = str(val).strip().split('.')[0]
        if s_val.isdigit():
            return s_val.zfill(2)
    except:
        pass
    return "XX"

def calculate_v63(df, date_idx, target_s):
    # Data Extraction with strict cleaning
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            val = get_clean_val(row.get(s, "XX"))
            flat_data.append(int(val) if val != "XX" else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 36-Base Logic
    base_val = -1
    for i in range(1, 20):
        if curr_pos - i >= 0 and flat_data[curr_pos-i] > 0:
            base_val = flat_data[curr_pos-i]; break
    if base_val == -1: base_val = 14
    
    d1, d2 = base_val // 10, base_val % 10
    pa, pb = (d1 + 1) % 10 if d1 != d2 else (d1 + 5) % 10, (d2 + 1) % 10
    ra, rb = (pa + 5) % 10, (pb + 5) % 10
    
    blocked = set()
    for a in {pa, ra}:
        for i in range(10): blocked.add(f"{a}{i}")
    for b in {pb, rb}:
        for i in range(10): blocked.add(f"{i}{b}")
    
    t36_base = [str(i).zfill(2) for i in range(100) if str(i).zfill(2) not in blocked]
    
    # Current 25 & History 30
    curr_25 = t36_base[:25]
    hist_data = df[target_s].tail(90).dropna()
    hist_vals = [get_clean_val(v) for v in hist_data if get_clean_val(v) != "XX"]
    hist_30 = [k for k, v in Counter(hist_vals).most_common(30)]
    
    # SPLIT LOGIC
    matched_anks = [j for j in curr_25 if j in hist_30]
    unmatched_anks = [j for j in curr_25 if j not in hist_30]
    
    return matched_anks, unmatched_anks

uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    # Column Normalization
    df.columns = [str(c).strip().upper() for c in df.columns]
    mapping = {'FD': 'FB', 'FBD': 'FB', 'GD': 'GB', 'GZB': 'GB', 'GZ': 'GB'}
    df = df.rename(columns=mapping)
    
    sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    matched, unmatched = calculate_v63(df, idx, target_s)
    
    # Live Result with fix
    res_raw = get_clean_val(df.iloc[idx].get(target_s, "XX"))
    st.markdown(f'<div class="live-card">LIVE RESULT: <span style="font-size:35px;">{res_raw}</span></div>', unsafe_allow_html=True)

    # DUAL PANE TRACKING
    st.markdown('<div class="split-container">', unsafe_allow_html=True)
    
    # Match Pane
    st.markdown(f"""
        <div class="match-pane">
            <h3 style="color:#166534;">💎 MATCHING ANKS ({len(matched)})</h3>
            <p style="font-size:12px;">Ye history aur prediction dono mein hain.</p>
            <div class="grid-ank">
                {"".join([f'<div class="ank-box" style="color:#166534; border-color:#22c55e;">{j}</div>' for j in matched])}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Unmatch Pane
    st.markdown(f"""
        <div class="unmatch-pane">
            <h3 style="color:#b91c1c;">🚫 UNMATCH ANKS ({len(unmatched)})</h3>
            <p style="font-size:12px;">Ye sirf current prediction mein hain.</p>
            <div class="grid-ank">
                {"".join([f'<div class="ank-box" style="color:#b91c1c; border-color:#ef4444;">{j}</div>' for j in unmatched])}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Analysis Backtest
    st.divider()
    st.subheader("📜 Efficiency Tracker (Last 15 Shifts)")
    hist_list = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 15, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        h_match, h_unmatch = calculate_v63(df, d_idx, s_name)
        actual = get_clean_val(df.iloc[d_idx].get(s_name, "XX"))
        status = "❌"
        if actual != "XX":
            if actual in h_match: status = "💎 MATCH HIT"
            elif actual in h_unmatch: status = "✅ UNMATCH HIT"
        hist_list.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))

