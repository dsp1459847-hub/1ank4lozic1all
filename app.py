import streamlit as st
import pandas as pd

# Page Setup
st.set_page_config(page_title="MAYA v50.0 - Recovery Engine", layout="wide")

# High-Visibility UI
st.markdown("""
    <style>
    .live-res { background: #1e293b; color: #fbbf24; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid #fbbf24; margin-bottom: 20px;}
    .grid-64 { display: grid; grid-template-columns: repeat(8, 1fr); gap: 5px; margin-bottom: 20px; }
    .grid-16 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; max-width: 400px; margin: 0 auto; }
    .item-target { background: #f0fdf4; color: #166534; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; border: 1px solid #bbf7d0; font-size: 18px; }
    .item-64 { background: #f8fafc; color: #475569; padding: 5px; border-radius: 4px; text-align: center; font-size: 12px; border: 1px solid #e2e8f0; }
    .status-hit { color: #16a34a; font-weight: bold; }
    .status-fail { color: #dc2626; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v50.0 (All-Shift 64-Ank Recovery)")

def get_flat_data(df):
    shifts = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat = []
    for _, row in df.iterrows():
        for s in shifts:
            v = str(row.get(s, "XX")).split('.')[0]
            flat.append(int(v) if v.isdigit() else -1)
    return flat

def calculate_v50_logic(df, date_idx, target_s):
    flat_data = get_flat_data(df)
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # 1. Finding Pure Base (Like v47.0)
    base_val = -1
    for i in range(1, 20):
        if curr_pos - i >= 0 and flat_data[curr_pos - i] > 0:
            base_val = flat_data[curr_pos - i]
            break
    if base_val == -1: base_val = 14

    d1, d2 = base_val // 10, base_val % 10
    pa = (d1 + 1) % 10 if d1 != d2 else (d1 + 5) % 10
    pb = (d2 + 1) % 10
    ra, rb = (pa + 5) % 10, (pb + 5) % 10
    
    # 2. Level 1: Generate 64 Eliminated Jodis (Blocking)
    blocked_64 = set()
    for a in {pa, ra}:
        for i in range(10): blocked_64.add(f"{a}{i}")
    for b in {pb, rb}:
        for i in range(10): blocked_64.add(f"{i}{b}")
    
    # 3. Level 2: Target Jodis (36 Anks) - v47 Style
    target_36 = [str(i).zfill(2) for i in range(100) if str(i).zfill(2) not in blocked_64]
    
    # 4. Reverse Filter (Removing Worst Gaps from these 36)
    # Scanning All-Shift Chain for failures
    final_16 = []
    extra_hatao = set()
    for g in [6, 12]: # Gaps in All-Shift chain (1 and 2 full rounds)
        if curr_pos - g >= 0:
            v = flat_data[curr_pos - g]
            if v != -1:
                for i in range(10):
                    extra_hatao.add(f"{v//10}{i}")
                    extra_hatao.add(f"{i}{v%10}")
    
    final_16 = [j for j in target_36 if j not in extra_hatao]
    return target_36, final_16[:16]

uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    
    # --- LIVE RESULT ---
    res_val = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-res">LIVE RESULT: <span style="font-size:35px; font-weight:bold;">{res_val}</span></div>', unsafe_allow_html=True)

    # Calculate
    t36, t16 = calculate_v50_logic(df, idx, target_s)

    # --- 64 ANK VERIFICATION (The Foundation) ---
    st.subheader("📋 Step 1: 36-Ank Target Base (Eliminated 64)")
    grid_64_html = '<div class="grid-64">'
    for j in t36: grid_64_html += f'<div class="item-64">{j}</div>'
    grid_64_html += '</div>'
    st.markdown(grid_64_html, unsafe_allow_html=True)

    st.divider()

    # --- FINAL 16 ANK (The Square Box) ---
    st.subheader("💎 Step 2: Final 16 Specialist Anks")
    grid_16_html = '<div class="grid-16">'
    for j in t16: grid_16_html += f'<div class="item-target">{j}</div>'
    grid_16_html += '</div>'
    st.markdown(grid_16_html, unsafe_allow_html=True)

    # --- HISTORY ---
    st.divider()
    st.subheader("📜 Backtest History (Check 8-13 May Accuracy)")
    hist = []
    flat_data = get_flat_data(df)
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    
    for p in range(curr_pos - 10, curr_pos + 1):
        if p < 0: continue
        d_idx = p // 6
        s_name = shifts_order[p % 6]
        h36, h16 = calculate_v50_logic(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h16: status = "✅ STABLE HIT"
            elif rv in h36: status = "🟡 BASE HIT"
            
        hist.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    
    st.table(pd.DataFrame(hist))
    
