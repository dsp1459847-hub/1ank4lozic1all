import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="MAYA v53.0 - Zero Efficiency Hunter", layout="wide")

# High-Fi UI Styling
st.markdown("""
    <style>
    .live-res-box { background: #0f172a; color: #fbbf24; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .grid-64 { display: grid; grid-template-columns: repeat(8, 1fr); gap: 4px; background: #f8fafc; padding: 10px; border-radius: 8px; }
    .item-64 { background: #fff; color: #94a3b8; padding: 4px; border-radius: 4px; text-align: center; font-size: 10px; border: 1px solid #e2e8f0; }
    .grid-16 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; max-width: 450px; margin: 15px auto; }
    .grid-9 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; max-width: 350px; margin: 15px auto; }
    .item-stable { background: #f0fdf4; color: #166534; padding: 15px; border-radius: 12px; font-size: 24px; font-weight: bold; text-align: center; border: 2px solid #bbf7d0; }
    .item-diamond { background: #fffbeb; color: #92400e; padding: 20px; border-radius: 12px; font-size: 28px; font-weight: bold; text-align: center; border: 3px solid #fde68a; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .status-diamond { color: #d97706; font-weight: bold; font-size: 14px; }
    .gap-marker { background: #fee2e2; color: #b91c1c; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-right: 4px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v53.0 (Zero-Accuracy Elimination)")

def get_zero_accuracy_gaps(all_vals, current_pos):
    """Scan 90 gaps to find timeframes with absolute 0% success in last 20 shifts"""
    zero_gaps = []
    for g in range(1, 91):
        if current_pos - g - 20 < 0: continue
        matches = 0
        for check in range(current_pos - 20, current_pos):
            if check - g >= 0 and all_vals[check-g] == all_vals[check] and all_vals[check] != -1:
                matches += 1
        if matches == 0: # Absolute Zero Efficiency
            zero_gaps.append(g)
    return zero_gaps[:5] # Return top 5 worst gaps

def calculate_v53(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Base 64 Logic (Original Strength)
    base_val = -1
    for i in range(1, 15):
        if curr_pos - i >= 0 and flat_data[curr_pos - i] > 0:
            base_val = flat_data[curr_pos - i]; break
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
    
    # 2. Hunting Zero-Accuracy Gaps for Diamond Extraction
    z_gaps = get_zero_accuracy_gaps(flat_data, curr_pos)
    extra_elimination = set()
    for zg in z_gaps:
        val = flat_data[curr_pos - zg]
        if val > 0:
            # We eliminate sets of these zero-performing numbers
            for i in range(10):
                extra_elimination.add(f"{val//10}{i}")
                extra_elimination.add(f"{i}{val%10}")
    
    final_target = [j for j in t36_base if j not in extra_elimination]
    
    # If filtration is too heavy, we fallback to maintain min counts
    if len(final_target) < 9: final_target = t36_base[:16]
    
    return t36_base, final_target[:16], final_target[:9], z_gaps

uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    sel_date = st.selectbox("📅 Selection Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Selection Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    t36, t16, t9, zgaps = calculate_v53(df, idx, target_s)
    
    # Live Result
    res_raw = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-res-box"><span style="font-size:16px;">LIVE RESULT</span><br><span style="font-size:42px; font-weight:bold;">{res_raw}</span><br><span>Zero-Accuracy Gaps: ' + "".join([f'<span class="gap-marker">G-{g}</span>' for g in zgaps]) + '</span></div>', unsafe_allow_html=True)

    # UI Levels
    st.subheader("📋 Level 1: Foundation (36 Jodis)")
    grid_64 = '<div class="grid-64">'
    for j in t36: grid_64 += f'<div class="item-64">{j}</div>'
    grid_64 += '</div>'
    st.markdown(grid_64, unsafe_allow_html=True)

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

    # History Backtest
    st.divider()
    st.subheader("📜 10-Shift Backtest (Zero-Accuracy Filter)")
    hist = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        h36, h16, h9, _ = calculate_v53(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 DIAMOND HIT"
            elif rv in h16: status = "✅ STABLE HIT"
            elif rv in h36: status = "🟡 BASE HIT"
        hist.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist))
        
