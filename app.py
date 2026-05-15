import streamlit as st
import pandas as pd

# Page Setup
st.set_page_config(page_title="MAYA v55.0 - Triple Confirmation", layout="wide")

# High-Fi UI Styling
st.markdown("""
    <style>
    .live-res-box { background: #0f172a; color: #fbbf24; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .grid-36 { display: grid; grid-template-columns: repeat(9, 1fr); gap: 4px; background: #f8fafc; padding: 10px; border-radius: 8px; }
    .item-36 { background: #fff; color: #94a3b8; padding: 4px; border-radius: 4px; text-align: center; font-size: 10px; border: 1px solid #e2e8f0; }
    .grid-16 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; max-width: 450px; margin: 15px auto; }
    .grid-9 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; max-width: 350px; margin: 15px auto; }
    .item-stable { background: #f0fdf4; color: #166534; padding: 15px; border-radius: 12px; font-size: 24px; font-weight: bold; text-align: center; border: 2px solid #bbf7d0; }
    .item-diamond { background: #fffbeb; color: #92400e; padding: 20px; border-radius: 12px; font-size: 28px; font-weight: bold; text-align: center; border: 3px solid #fde68a; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .confirmation-badge { background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 5px; border: 1px solid #bbf7d0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v55.0 (Triple Confirmation Engine)")

def get_step_jump_val(flat_list, current_pos, step):
    idx = current_pos - (step + 1)
    return flat_list[idx] if idx >= 0 else -1

def get_triple_confirmed_gaps(flat_list, current_pos):
    """Sari shifton mein scan karke 3 sabse bekar zero gaps nikalna"""
    gap_failures = {}
    for step in range(0, 91):
        # Scan last 20 records for this specific step-jump
        matches = 0
        i = current_pos - 1
        count = 0
        while i >= 1 and count < 20:
            prev_val = i - (step + 1)
            if prev_val >= 0 and flat_list[i] == flat_list[prev_val] and flat_list[i] != -1:
                matches += 1
            i -= 1
            count += 1
        gap_failures[step] = matches
    
    # Picking top 3 gaps with zero or minimum matches
    worst_3_steps = sorted(gap_failures, key=gap_failures.get)[:3]
    return worst_3_steps

def calculate_v55(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Base 64 Foundation (Original Power)
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
    
    # 2. Triple Confirmation Elimination
    worst_steps = get_triple_confirmed_gaps(flat_data, curr_pos)
    
    # Extracting common failing elements from these 3 gaps
    common_bad_a = []
    common_bad_b = []
    for step in worst_steps:
        fv = get_step_jump_val(flat_data, curr_pos, step)
        if fv != -1:
            common_bad_a.append(fv // 10)
            common_bad_b.append(fv % 10)
            
    extra_elim = set()
    for a in set(common_bad_a):
        for i in range(10): extra_elim.add(f"{a}{i}")
    for b in set(common_bad_b):
        for i in range(10): extra_elim.add(f"{i}{b}")

    final_list = [j for j in t36_base if j not in extra_elim]
    
    # Security check to ensure we don't empty the list
    if len(final_list) < 9: final_list = t36_base
    
    return t36_base, final_list[:16], final_list[:9], worst_steps

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    c1, c2 = st.columns(2)
    with c1: sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    with c2: target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    t36, t16, t9, steps = calculate_v55(df, idx, target_s)
    
    # Live Display
    res_val = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-res-box"><span style="font-size:16px;">LIVE RESULT</span><br><span style="font-size:42px; font-weight:bold;">{res_val}</span><br><span>Triple Confirmed Zero Gaps: ' + "".join([f'<span class="confirmation-badge">Step-{s}</span>' for s in steps]) + '</span></div>', unsafe_allow_html=True)

    # UI Levels
    st.subheader("📋 Level 1: Strong Foundation (36 Jodis)")
    grid_36 = '<div class="grid-36">'
    for j in t36: grid_36 += f'<div class="item-36">{j}</div>'
    grid_36 += '</div>'
    st.markdown(grid_36, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Level 2: Confirmed Stable (16 Jodis)")
        grid_16 = '<div class="grid-16">'
        for j in t16: grid_16 += f'<div class="item-stable">{j}</div>'
        grid_16 += '</div>'
        st.markdown(grid_16, unsafe_allow_html=True)

    with col2:
        st.subheader("💎 Level 3: Triple Diamond (9 Jodis)")
        grid_9 = '<div class="grid-9">'
        for j in t9: grid_9 += f'<div class="item-diamond">{j}</div>'
        grid_9 += '</div>'
        st.markdown(grid_9, unsafe_allow_html=True)

    # History Table
    st.divider()
    st.subheader("📜 10-Shift Backtest (Triple Confirmation Accuracy)")
    hist_list = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        h36, h16, h9, _ = calculate_v55(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 TRIPLE DIAMOND"
            elif rv in h16: status = "✅ STABLE HIT"
            elif rv in h36: status = "🟡 BASE HIT"
        hist_list.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
        
