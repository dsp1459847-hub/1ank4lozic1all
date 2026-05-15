import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="MAYA v54.0 - Step Jump Engine", layout="wide")

# High-Visibility UI
st.markdown("""
    <style>
    .main-box { background: #0f172a; color: #fbbf24; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 25px; }
    .grid-36 { display: grid; grid-template-columns: repeat(9, 1fr); gap: 4px; background: #f1f5f9; padding: 10px; border-radius: 8px; }
    .item-36 { background: #fff; color: #64748b; padding: 4px; border-radius: 4px; text-align: center; font-size: 11px; border: 1px solid #e2e8f0; }
    .grid-16 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; max-width: 450px; margin: 15px auto; }
    .grid-9 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; max-width: 350px; margin: 15px auto; }
    .box-stable { background: #f0fdf4; color: #166534; padding: 15px; border-radius: 12px; font-size: 24px; font-weight: bold; text-align: center; border: 2px solid #bbf7d0; }
    .box-diamond { background: #fffbeb; color: #92400e; padding: 20px; border-radius: 12px; font-size: 28px; font-weight: bold; text-align: center; border: 3px solid #fde68a; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .jump-tag { background: #fee2e2; color: #b91c1c; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin: 2px; border: 1px solid #fecaca; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v54.0 (Step-Jump Zero Scanner)")

def get_step_jump_data(flat_list, current_pos, step):
    """Aapke niyam ke hisaab se jump maarkar data nikalna"""
    jumped_data = []
    # step 0 means every record, step 1 means skip 1, etc.
    i = current_pos - 1
    while i >= 0 and len(jumped_data) < 30:
        if flat_list[i] != -1:
            jumped_data.append(flat_list[i])
        i -= (step + 1)
    return jumped_data

def scan_worst_step_jumps(flat_list, current_pos):
    """1 se 90 step-jumps scan karke absolute zero accuracy dhoondhna"""
    worst_jump_configs = []
    for step in range(0, 91):
        test_data = get_step_jump_data(flat_list, current_pos, step)
        if len(test_data) < 15: continue
        
        # Check last 15 jumps accuracy
        matches = 0
        for idx in range(len(test_data)-1):
            if test_data[idx] == test_data[idx+1]:
                matches += 1
        
        if matches == 0: # Absolute Zero Efficiency found
            worst_jump_configs.append(step)
            if len(worst_jump_configs) >= 4: break
    return worst_jump_configs

def calculate_v54(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Level 1 Base (64 Eliminated -> 36 Target)
    # Using previous valid result as base
    base_val = -1
    for i in range(1, 20):
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
    
    # 2. Level 2 & 3: Step-Jump Elimination
    worst_steps = scan_worst_step_jumps(flat_data, curr_pos)
    
    # If no zero accuracy in current shift, check relation with neighbor shift
    if not worst_steps:
        neighbor_pos = curr_pos - 1 # Relation with previous shift
        worst_steps = scan_worst_step_jumps(flat_data, neighbor_pos)

    extra_elim = set()
    for step in worst_steps:
        # Get the first value in that zero-accuracy step jump
        fail_val_list = get_step_jump_data(flat_data, curr_pos, step)
        if fail_val_list:
            fv = fail_val_list[0]
            for i in range(10):
                extra_elim.add(f"{fv//10}{i}")
                extra_elim.add(f"{i}{fv%10}")
                
    final_target = [j for j in t36_base if j not in extra_elim]
    if len(final_target) < 9: final_target = t36_base # Fallback to base
    
    return t36_base, final_target[:16], final_target[:9], worst_steps

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    sel_date = st.selectbox("📅 Date Select:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift Select:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    t36, t16, t9, steps = calculate_v54(df, idx, target_s)
    
    # Live Result
    res_val = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="main-box"><span style="font-size:14px;">LIVE RESULT</span><br><span style="font-size:42px; font-weight:bold;">{res_val}</span><br><span>Zero-Acc Jumps: ' + "".join([f'<span class="jump-tag">Step-{s}</span>' for s in steps]) + '</span></div>', unsafe_allow_html=True)

    # UI Levels
    st.subheader("📋 Step 1: Base Target (36 Jodis)")
    grid_36 = '<div class="grid-36">'
    for j in t36: grid_36 += f'<div class="item-36">{j}</div>'
    grid_36 += '</div>'
    st.markdown(grid_36, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Step 2: Stable (16 Jodis)")
        grid_16 = '<div class="grid-16">'
        for j in t16: grid_16 += f'<div class="box-stable">{j}</div>'
        grid_16 += '</div>'
        st.markdown(grid_16, unsafe_allow_html=True)

    with col2:
        st.subheader("💎 Step 3: Diamond (9 Jodis)")
        grid_9 = '<div class="grid-9">'
        for j in t9: grid_9 += f'<div class="box-diamond">{j}</div>'
        grid_9 += '</div>'
        st.markdown(grid_9, unsafe_allow_html=True)

    # Backtest History
    st.divider()
    st.subheader("📜 10-Shift Backtest (Step-Jump Verification)")
    hist_data = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        h36, h16, h9, _ = calculate_v54(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 DIAMOND HIT"
            elif rv in h16: status = "✅ STABLE HIT"
            elif rv in h36: status = "🟡 BASE HIT"
        hist_data.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_data))
            
