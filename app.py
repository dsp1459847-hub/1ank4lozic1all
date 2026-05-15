import streamlit as st
import pandas as pd
from collections import Counter

# Page Setup
st.set_page_config(page_title="MAYA v59.0 - History Validator", layout="wide")

st.markdown("""
    <style>
    .live-res { background: #1e293b; color: #fbbf24; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .compare-box { background: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
    .grid-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
    .grid-9 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
    .item-stable { background: #f0fdf4; color: #166534; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; border: 1px solid #bbf7d0; font-size: 18px; }
    .item-diamond { background: #fffbeb; color: #92400e; padding: 12px; border-radius: 8px; font-weight: bold; text-align: center; border: 2px solid #fde68a; font-size: 20px; }
    .unique-badge { background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v59.0 (History & Unique Comparison)")

def get_unique_freq_digits(df, target_s, months=3):
    """Pichle 3 mahine ke results se sabse zyada aane wale unique ank nikalna"""
    # Assuming 1 month = 30 rows approx
    history_data = df[target_s].tail(months * 30).dropna().astype(str)
    all_digits = "".join([d.split('.')[0].zfill(2) for d in history_data if d.split('.')[0].isdigit()])
    counts = Counter([all_digits[i:i+2] for i in range(0, len(all_digits), 2)])
    return [k for k, v in counts.most_common(20)] # Top 20 unique frequent jodis

def calculate_v59(df, date_idx, target_s):
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts_order:
            v = str(row.get(s, "XX")).split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) > 0 else -1)
    
    curr_pos = (date_idx * 6) + shifts_order.index(target_s)
    
    # Base 36 Logic (Reverse Pattern for Strength)
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
    
    # Step-Jump Reverse Elimination
    reverse_target = []
    for step in range(0, 60):
        idx = curr_pos - (step + 1)
        if idx >= 0 and flat_data[idx] > 0:
            jodi = str(flat_data[idx]).zfill(2)
            if jodi in t36_base and jodi not in reverse_target:
                reverse_target.append(jodi)
            if len(reverse_target) >= 16: break
            
    return t36_base, reverse_target[:16], reverse_target[:9]

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    sel_date = st.selectbox("📅 Date Select:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift Select:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    
    # Predictions
    t36, t16, t9 = calculate_v59(df, idx, target_s)
    hist_unique = get_unique_freq_digits(df, target_s)

    # UI: TOP LIVE
    res_raw = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="live-res">LIVE RESULT: <span style="font-size:35px;">{res_raw}</span></div>', unsafe_allow_html=True)

    # --- COMPARISON LAYOUT ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Current Logic (16 Stable)")
        grid_html = '<div class="grid-container">'
        for j in t16: grid_html += f'<div class="item-stable">{j}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)
        
        st.subheader("💎 Current Diamond (9 Jodis)")
        grid_9 = '<div class="grid-9">'
        for j in t9: grid_9 += f'<div class="item-diamond">{j}</div>'
        grid_9 += '</div>'
        st.markdown(grid_9, unsafe_allow_html=True)

    with col2:
        st.subheader("📊 3-Month Unique Freq (Top 16)")
        st.info("Ye ank pichle 3 mahine mein sabse zyada baar aaye hain.")
        grid_u = '<div class="grid-container">'
        for j in hist_unique[:16]:
            color = "#eff6ff" if j in t16 else "#ffffff"
            st.markdown(f'<div class="item-stable" style="background:{color};">{j}<div class="unique-badge">Match: {"Yes" if j in t16 else "No"}</div></div>', unsafe_allow_html=True)
        grid_u += '</div>'

    # --- 1 MONTH HISTORY ---
    st.divider()
    st.subheader("📜 30-Day Deep History Backtest")
    hist_list = []
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    curr_pos = (idx * 6) + shifts_order.index(target_s)
    
    for p in range(curr_pos - 30, curr_pos + 1):
        if p < 0: continue
        d_idx, s_name = p // 6, shifts_order[p % 6]
        _, h16, h9 = calculate_v59(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 DIAMOND"
            elif rv in h16: status = "✅ STABLE"
        hist_list.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    
    st.table(pd.DataFrame(hist_list))
    
