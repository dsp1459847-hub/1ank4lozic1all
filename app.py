import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="MAYA v56.0 - Adaptive Engine", layout="wide")

# High-Fi UI Styling
st.markdown("""
    <style>
    .live-res-box { background: #0f172a; color: #fbbf24; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .grid-36 { display: grid; grid-template-columns: repeat(9, 1fr); gap: 4px; background: #f8fafc; padding: 8px; border-radius: 8px; }
    .item-36 { background: #fff; color: #94a3b8; padding: 4px; border-radius: 4px; text-align: center; font-size: 10px; border: 1px solid #e2e8f0; }
    .grid-16 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; max-width: 400px; margin: 10px auto; }
    .grid-9 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 300px; margin: 10px auto; }
    .item-stable { background: #f0fdf4; color: #166534; padding: 12px; border-radius: 10px; font-size: 22px; font-weight: bold; text-align: center; border: 2px solid #bbf7d0; }
    .item-diamond { background: #fffbeb; color: #92400e; padding: 15px; border-radius: 10px; font-size: 26px; font-weight: bold; text-align: center; border: 3px solid #fde68a; }
    .logic-badge { background: #e0f2fe; color: #0369a1; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; border: 1px solid #bae6fd; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v56.0 (Adaptive Zero-Scanner)")

def get_step_jump_val(flat_list, current_pos, step):
    idx = current_pos - (step + 1)
    return flat_list[idx] if idx >= 0 else -1

def scan_worst_jumps(flat_list, current_pos):
    """Scan 1-90 jumps for absolute zero accuracy"""
    worst_jumps = []
    for step in range(0, 91):
        matches = 0
        i = current_pos - 1
        count = 0
        while i >= 1 and count < 20:
            prev = i - (step + 1)
            if prev >= 0 and flat_list[i] == flat_list[prev] and flat_list[i] != -1:
                matches += 1
            i -= 1
            count += 1
        if matches == 0:
            worst_jumps.append(step)
            if len(worst_jumps) >= 5: break
    return worst_jumps

def get_elimination_set(flat_list, current_pos, worst_steps, mode='common'):
    bad_a, bad_b = [], []
    for s in worst_steps:
        fv = get_step_jump_val(flat_list, current_pos, s)
        if fv != -1:
            bad_a.append(fv // 10)
            bad_b.append(fv % 10)
    
    elim = set()
    if mode == 'common' and bad_a:
        # Picking most frequent (common) bad digits
        ca = max(set(bad_a), key=bad_a.count)
        cb = max(set(bad_b), key=bad_b.count)
        for i in range(10): 
            elim.add(f"{ca}{i}"); elim.add(f"{i}{cb}")
    else:
        # Unique elimination (All bad digits found)
        for a in set(bad_a):
            for i in range(10): elim.add(f"{a}{i}")
        for b in set(bad_b):
            for i in range(10): elim.add(f"{i}{b}")
    return elim

def calculate_v56(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Base Logic (v54 Strong Foundation)
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
    
    # 2. AUTO-ENGINE: Testing Logic A vs B
    worst_steps = scan_worst_jumps(flat_data, curr_pos)
    
    def test_logic(mode):
        score = 0
        for p in range(curr_pos - 10, curr_pos):
            e_set = get_elimination_set(flat_data, p, worst_steps, mode)
            res = flat_data[p]
            if res != -1 and str(res).zfill(2) not in e_set:
                score += 1
        return score

    score_common = test_logic('common')
    score_unique = test_logic('unique')
    
    best_mode = 'common' if score_common >= score_unique else 'unique'
    final_elim = get_elimination_set(flat_data, curr_pos, worst_steps, best_mode)
    
    final_target = [j for j in t36_base if j not in final_elim]
    if len(final_target) < 9: final_target = t36_base # Fallback
    
    return t36_base, final_target[:16], final_target[:9], best_mode, worst_steps

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    c1, c2 = st.columns(2)
    with c1: sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    with c2: target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    t36, t16, t9, mode_used, steps = calculate_v56(df, idx, target_s)
    
    # Live Display
    res_val = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-res-box"><span style="font-size:14px;">LIVE RESULT: {res_val}</span><br><span class="logic-badge">Engine Mode: {mode_used.upper()}</span><br><span style="font-size:12px;">Worst Steps: {steps[:3]}</span></div>', unsafe_allow_html=True)

    # UI Table Levels
    st.subheader("📋 Level 1: Foundation (36 Jodis)")
    grid_36 = '<div class="grid-36">'
    for j in t36: grid_36 += f'<div class="item-36">{j}</div>'
    grid_36 += '</div>'
    st.markdown(grid_36, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Level 2: Stable (16 Jodis)")
        grid_16 = '<div class="grid-16">'
        for j in t16: grid_16 += f'<div class="item-stable">{j}</div>'
        grid_16 += '</div>'
        st.markdown(grid_16, unsafe_allow_html=True)

    with col2:
        st.subheader("💎 Level 3: Diamond (9 Jodis)")
        grid_9 = '<div class="grid-9">'
        for j in t9: grid_9 += f'<div class="item-diamond">{j}</div>'
        grid_9 += '</div>'
        st.markdown(grid_9, unsafe_allow_html=True)

    # History Table
    st.divider()
    st.subheader("📜 Backtest History (Adaptive Verification)")
    hist_list = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        h36, h16, h9, _, _ = calculate_v56(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 DIAMOND"
            elif rv in h16: status = "✅ STABLE"
            elif rv in h36: status = "🟡 BASE"
        hist_list.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
            
