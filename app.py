import streamlit as st
import pandas as pd

# Page Setup
st.set_page_config(page_title="MAYA v51.0 - Unique Engine", layout="wide")

# High-Visibility UI Styling
st.markdown("""
    <style>
    .live-card { background: #1e293b; color: #fbbf24; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .grid-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; max-width: 400px; margin: 10px auto; }
    .super-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 300px; margin: 10px auto; }
    .grid-item { background: #ffffff; color: #1e40af; padding: 12px; border-radius: 8px; font-size: 20px; font-weight: bold; text-align: center; border: 2px solid #bfdbfe; }
    .super-item { background: #fffbeb; color: #92400e; padding: 15px; border-radius: 8px; font-size: 22px; font-weight: bold; text-align: center; border: 2px solid #fde68a; }
    .status-hit { color: #16a34a; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v51.0 (Automatic Time-Frame Jump)")

# --- DYNAMIC DIVERSITY SEARCH ---
def get_unique_base_logic(df, date_idx, shift_col):
    """Data na hone par piche jump maarna jab tak 4 unique digits na mil jayein"""
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    current_flat_pos = (date_idx * 6) + shifts_order.index(shift_col)
    
    # All-shift flattening for jump
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)

    # Jump search (1 to 120 positions back)
    for jump in range(1, 120):
        pos = current_flat_pos - jump
        if pos < 0: break
        
        base_val = flat_data[pos]
        if base_val != -1:
            d1, d2 = base_val // 10, base_val % 10
            pa = (d1 + 1) % 10 if d1 != d2 else (d1 + 5) % 10
            pb = (d2 + 1) % 10
            ra, rb = (pa + 5) % 10, (pb + 5) % 10
            
            # Agar charon ank alag hain, toh hi return karo
            if len({pa, ra, pb, rb}) == 4:
                return pa, ra, pb, rb, jump
                
    return 1, 6, 2, 7, 0 # Fallback

def calculate_v51(df, idx, target_s):
    # 1. Get 4 Unique Digits using Timeframe Jump
    pa, ra, pb, rb, used_jump = get_unique_base_logic(df, idx, target_s)
    
    # 2. Level 1: Generate 36 Target Jodis (Eliminating 64)
    blocked_64 = set()
    for a in {pa, ra}:
        for i in range(10): blocked_64.add(f"{a}{i}")
    for b in {pb, rb}:
        for i in range(10): blocked_64.add(f"{i}{b}")
    
    target_36 = [str(i).zfill(2) for i in range(100) if str(i).zfill(2) not in blocked_64]
    
    # 3. Level 2: Eliminate Worst Gaps (5-5 ank filter)
    # Using a secondary jump for extra elimination
    w_pa, w_ra, w_pb, w_rb, _ = get_unique_base_logic(df, idx-5, target_s) # 5 days shifted search
    
    extra_hatao = set()
    for a in {w_pa, w_ra}:
        for i in range(10): extra_hatao.add(f"{a}{i}")
    for b in {w_pb, w_rb}:
        for i in range(10): extra_hatao.add(f"{i}{b}")
        
    final_16 = [j for j in target_36 if j not in extra_hatao]
    return final_16[:16], final_16[:9], used_jump

uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    c1, c2 = st.columns(2)
    with c1: sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    with c2: target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    
    # Calculate with Jump Logic
    t16, t9, jump_val = calculate_v51(df, idx, target_s)
    
    # --- LIVE DISPLAY ---
    res_raw = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-card"><span style="font-size:14px;">LIVE RESULT</span><br><span style="font-size:35px; font-weight:bold;">{res_raw}</span><br><span style="font-size:12px;">Used Timeframe Jump: {jump_val} Shifts</span></div>', unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**✅ Stable Target (Square 16)**")
        grid_html = '<div class="grid-container">'
        for j in t16: grid_html += f'<div class="grid-item">{j}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

    with col_r:
        st.write("**💎 Super Diamond (Square 9)**")
        grid_html = '<div class="super-grid">'
        for j in t9: grid_html += f'<div class="super-item">{j}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

    # --- HISTORY ---
    st.divider()
    st.subheader("📜 Backtest History (Jump-Logic Verification)")
    hist = []
    for i in range(idx - 10, idx + 1):
        if i < 0: continue
        h16, h9, _ = calculate_v51(df, i, target_s)
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 DIAMOND"
            elif rv in h16: status = "✅ HIT"
        hist.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist))
                                                      
