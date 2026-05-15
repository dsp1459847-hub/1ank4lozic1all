import streamlit as st
import pandas as pd

# Page Setup
st.set_page_config(page_title="MAYA v52.0 - Master Engine", layout="wide")

# High-Visibility UI Styling
st.markdown("""
    <style>
    .live-res-box { background: #1e293b; color: #fbbf24; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .grid-64 { display: grid; grid-template-columns: repeat(8, 1fr); gap: 4px; margin-bottom: 20px; }
    .item-64 { background: #f8fafc; color: #64748b; padding: 4px; border-radius: 4px; text-align: center; font-size: 11px; border: 1px solid #e2e8f0; }
    .grid-16 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; max-width: 400px; margin: 10px auto; }
    .grid-9 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 300px; margin: 10px auto; }
    .item-target { background: #ffffff; color: #1e40af; padding: 15px; border-radius: 10px; font-size: 22px; font-weight: bold; text-align: center; border: 2px solid #bfdbfe; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .item-diamond { background: #fffbeb; color: #92400e; padding: 18px; border-radius: 10px; font-size: 26px; font-weight: bold; text-align: center; border: 2px solid #fde68a; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .status-hit { color: #16a34a; font-weight: bold; }
    .gap-tag { background: #fee2e2; color: #b91c1c; padding: 2px 8px; border-radius: 4px; font-size: 12px; border: 1px solid #fecaca; margin-right: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v52.0 (Triple-Level Elimination)")

def get_worst_gap_logic(all_vals, current_pos):
    """1 se 90 gaps mein se sabse bekar (Zero Accuracy) wala dhoondhna"""
    gap_failure_report = {}
    for g in range(1, 91):
        if current_pos - g - 15 < 0: continue
        matches = 0
        for check in range(current_pos - 15, current_pos):
            if check - g >= 0 and all_vals[check-g] == all_vals[check] and all_vals[check] != -1:
                matches += 1
        gap_failure_report[g] = matches
    
    # Sort gaps by least matches (worst performing)
    sorted_gaps = sorted(gap_failure_report, key=gap_failure_report.get)
    
    for g in sorted_gaps:
        val = all_vals[current_pos - g]
        if val > 0:
            d1, d2 = val // 10, val % 10
            pa, pb = (d1 + 1) % 10, (d2 + 1) % 10
            ra, rb = (pa + 5) % 10, (pb + 5) % 10
            if len({pa, ra, pb, rb}) == 4:
                return pa, ra, pb, rb, g
    return 1, 6, 2, 7, 0

def calculate_v52(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Level 1: 64 Elimination (Target 36)
    pa, ra, pb, rb, gap_used = get_worst_gap_logic(flat_data, curr_pos)
    blocked_64 = set()
    for a in {pa, ra}:
        for i in range(10): blocked_64.add(f"{a}{i}")
    for b in {pb, rb}:
        for i in range(10): blocked_64.add(f"{i}{b}")
    
    t36 = [str(i).zfill(2) for i in range(100) if str(i).zfill(2) not in blocked_64]
    
    # 2. Level 2 & 3: Deep Elimination (Filtering the 36)
    # Using the next worst gap to filter more
    extra_hatao = set()
    _, _, w2a, w2b, _ = get_worst_gap_logic(flat_data, curr_pos - 10) 
    for i in range(10):
        extra_hatao.add(f"{w2a}{i}")
        extra_hatao.add(f"{i}{w2b}")
        
    t16 = [j for j in t36 if j not in extra_hatao]
    return t36, t16[:16], t16[:9], gap_used

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    c1, c2 = st.columns(2)
    with c1: sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    with c2: target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    t36, t16, t9, used_g = calculate_v52(df, idx, target_s)
    
    # --- LIVE DISPLAY ---
    res_raw = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-res-box"><span style="font-size:14px;">LIVE RESULT</span><br><span style="font-size:35px; font-weight:bold;">{res_raw}</span><br><span class="gap-tag">Optimal Worst Gap: {used_g}</span></div>', unsafe_allow_html=True)

    # STEP 1: 64 Foundation
    st.subheader("📋 Level 1: 36-Jodi Base (After 64 Eliminated)")
    grid_64 = '<div class="grid-64">'
    for j in t36: grid_64 += f'<div class="item-64">{j}</div>'
    grid_64 += '</div>'
    st.markdown(grid_64, unsafe_allow_html=True)

    st.divider()

    # STEP 2 & 3: 16 Stable & 9 Diamond
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("✅ Level 2: 16 Stable Anks")
        grid_16 = '<div class="grid-16">'
        for j in t16: grid_16 += f'<div class="item-target">{j}</div>'
        grid_16 += '</div>'
        st.markdown(grid_16, unsafe_allow_html=True)

    with col_r:
        st.subheader("💎 Level 3: 9 Diamond Anks")
        grid_9 = '<div class="grid-9">'
        for j in t9: grid_9 += f'<div class="item-diamond">{j}</div>'
        grid_9 += '</div>'
        st.markdown(grid_9, unsafe_allow_html=True)

    # --- HISTORY ---
    st.divider()
    st.subheader("📜 10-Shift Backtest History")
    hist = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        h36, h16, h9, _ = calculate_v52(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 DIAMOND"
            elif rv in h16: status = "✅ STABLE"
            elif rv in h36: status = "🟡 BASE"
        hist.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist))
        
