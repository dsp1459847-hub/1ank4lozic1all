import streamlit as st
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(page_title="MAYA v57.0 - Strict Logic", layout="wide")

st.markdown("""
    <style>
    .live-res { background: #0f172a; color: #fbbf24; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; }
    .grid-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; max-width: 400px; margin: 0 auto; }
    .grid-9 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 300px; margin: 0 auto; }
    .item-box { background: #ffffff; color: #1e40af; padding: 15px; border-radius: 10px; font-size: 20px; font-weight: bold; text-align: center; border: 2px solid #bfdbfe; }
    .item-diamond { background: #fffbeb; color: #9a3412; padding: 18px; border-radius: 10px; font-size: 24px; font-weight: bold; text-align: center; border: 3px solid #f97316; }
    .eff-meter { background: #f0fdf4; border-left: 5px solid #22c55e; padding: 10px; margin-top: 10px; color: #166534; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v57.0 (Strict Difference Engine)")

def get_step_jump_val(flat_list, current_pos, step):
    # Strictly implements your jump rule: Skip 'step' records
    idx = current_pos - (step + 1)
    return flat_list[idx] if idx >= 0 else -1

def scan_zero_efficiency_jumps(flat_list, current_pos):
    """Scan 1-90 jumps and verify 0% success in last 25 records"""
    valid_zero_steps = []
    for step in range(0, 91):
        test_matches = 0
        i = current_pos - 1
        # Check consistency for last 25 shifts
        for _ in range(25):
            if i < 1: break
            prev_pos = i - (step + 1)
            if prev_pos >= 0:
                if flat_list[i] == flat_list[prev_pos] and flat_list[i] != -1:
                    test_matches += 1
            i -= 1
        
        if test_matches == 0:
            valid_zero_steps.append(step)
            if len(valid_zero_steps) >= 5: break
    return valid_zero_steps

def calculate_v57_strict(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Base 36 Logic (Foundation)
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
    
    # 2. Strict Zero-Efficiency Filtering
    worst_steps = scan_zero_efficiency_jumps(flat_data, curr_pos)
    
    # Logic Choice: Strictly using the most frequent bad digits from zero-acc jumps
    bad_a, bad_b = [], []
    for s in worst_steps:
        fv = get_step_jump_val(flat_data, curr_pos, s)
        if fv > 0:
            bad_a.append(fv // 10)
            bad_b.append(fv % 10)
            
    extra_elim = set()
    if bad_a:
        # We eliminate the common digits found across multiple zero-acc steps
        common_a = max(set(bad_a), key=bad_a.count)
        common_b = max(set(bad_b), key=bad_b.count)
        for i in range(10):
            extra_elim.add(f"{common_a}{i}")
            extra_elim.add(f"{i}{common_b}")

    final_target = [j for j in t36_base if j not in extra_elim]
    
    # Final Difference Check: Ensure result isn't same as previous shift
    prev_res = str(flat_data[curr_pos-1]).zfill(2)
    if final_target and final_target[0] == prev_res:
        final_target = final_target[1:] # Force a change

    return t36_base, final_target[:16], final_target[:9], worst_steps

uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    sel_date = st.selectbox("📅 Selection Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Selection Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    t36, t16, t9, steps = calculate_v57_strict(df, idx, target_s)
    
    # Live Result Display
    res_raw = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-res">LIVE RESULT: <span style="font-size:35px;">{res_raw}</span></div>', unsafe_allow_html=True)

    # --- EFFICIENCY METER ---
    st.markdown(f'<div class="eff-meter">Logic Applied: Zero-Efficiency Hunter | Active Gaps: {steps[:3]}</div>', unsafe_allow_html=True)

    st.divider()
    
    # Display in 4x4 and 3x3 Squares
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✅ Stable (Square 16)")
        grid_16 = '<div class="grid-container">'
        for j in t16: grid_16 += f'<div class="item-box">{j}</div>'
        grid_16 += '</div>'
        st.markdown(grid_16, unsafe_allow_html=True)
        
    with col2:
        st.subheader("💎 Diamond (Square 9)")
        grid_9 = '<div class="grid-9">'
        for j in t9: grid_9 += f'<div class="item-diamond">{j}</div>'
        grid_9 += '</div>'
        st.markdown(grid_9, unsafe_allow_html=True)

    # --- HISTORICAL VERIFICATION ---
    st.divider()
    st.subheader("📜 Efficiency Backtest (Last 10 Shifts)")
    hist_list = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        _, h16, h9, _ = calculate_v57_strict(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 DIAMOND HIT"
            elif rv in h16: status = "✅ STABLE HIT"
        hist_list.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
        
