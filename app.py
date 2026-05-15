import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="MAYA v58.0 - Reverse Logic", layout="wide")

st.markdown("""
    <style>
    .live-res-box { background: #1e293b; color: #fbbf24; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .grid-64 { display: grid; grid-template-columns: repeat(8, 1fr); gap: 4px; background: #f8fafc; padding: 8px; border-radius: 8px; }
    .item-64 { background: #fff; color: #94a3b8; padding: 4px; border-radius: 4px; text-align: center; font-size: 10px; border: 1px solid #e2e8f0; }
    .grid-stable { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; max-width: 500px; margin: 10px auto; }
    .grid-diamond { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 300px; margin: 10px auto; }
    .box-stable { background: #fff1f2; color: #9f1239; padding: 12px; border-radius: 10px; font-size: 20px; font-weight: bold; text-align: center; border: 2px solid #fecdd3; }
    .box-diamond { background: #fdf2f8; color: #9d174d; padding: 15px; border-radius: 10px; font-size: 24px; font-weight: bold; text-align: center; border: 2px solid #fbcfe8; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .status-hit { color: #e11d48; font-weight: bold; }
    .info-text { font-size: 12px; color: #64748b; font-style: italic; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v58.0 (Mirror/Reverse Logic)")

def calculate_v58_reverse(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Base 64 Foundation (Target 36) - Keeping it strong
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

    # 2. THE REVERSE JUMP - Finding the "Failing" digits to use as Diamond
    # We scan for 3 gaps that have 0 accuracy and use THEM as our target
    reverse_target = []
    for step in range(0, 60):
        idx = curr_pos - (step + 1)
        if idx >= 0 and flat_data[idx] > 0:
            v = flat_data[idx]
            jodi = str(v).zfill(2)
            # Agar ye jodi hamare 36 base mein hai, toh ise 'Super Hit' mano (Reverse Logic)
            if jodi in t36_base and jodi not in reverse_target:
                reverse_target.append(jodi)
            if len(reverse_target) >= 25: break

    # If reverse target is weak, fallback to shuffle
    if not reverse_target: reverse_target = t36_base[::-1]

    return t36_base, reverse_target[:25], reverse_target[:9]

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    t36, t25, t9 = calculate_v58_reverse(df, idx, target_s)
    
    # Live Result
    res_raw = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-res-box"><span style="font-size:14px;">LIVE RESULT</span><br><span style="font-size:35px; font-weight:bold;">{res_raw}</span></div>', unsafe_allow_html=True)

    # UI Table Levels
    st.subheader("📋 Level 1: 36-Jodi Base (The Foundation)")
    grid_64 = '<div class="grid-64">'
    for j in t36: grid_64 += f'<div class="item-64">{j}</div>'
    grid_64 += '</div>'
    st.markdown(grid_64, unsafe_allow_html=True)

    st.divider()

    # REVERSE TARGETS
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🔄 Level 2: Reverse Stable (25 Jodis)")
        st.markdown('<p class="info-text">Ye wo ank hain jo pehle eliminate hote the, ab target hain</p>', unsafe_allow_html=True)
        grid_stable = '<div class="grid-stable">'
        for j in t25: grid_stable += f'<div class="box-stable">{j}</div>'
        grid_stable += '</div>'
        st.markdown(grid_stable, unsafe_allow_html=True)

    with col_r:
        st.subheader("💎 Level 3: Reverse Diamond (9 Jodis)")
        st.markdown('<p class="info-text">Sabse zyada fail hone wale gaps se nikale gaye Diamond</p>', unsafe_allow_html=True)
        grid_diamond = '<div class="grid-diamond">'
        for j in t9: grid_diamond += f'<div class="box-diamond">{j}</div>'
        grid_diamond += '</div>'
        st.markdown(grid_diamond, unsafe_allow_html=True)

    # History Table
    st.divider()
    st.subheader("📜 Backtest History (Reverse Logic Verification)")
    hist_list = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        h36, h25, h9 = calculate_v58_reverse(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 REV-DIAMOND"
            elif rv in h25: status = "✅ REV-STABLE"
            elif rv in h36: status = "🟡 BASE HIT"
        hist_list.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
            
