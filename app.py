import streamlit as st
import pandas as pd
from collections import Counter

# Page Setup
st.set_page_config(page_title="MAYA v98.0 - Raw Logic", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #020617; border-right: 3px solid #fbbf24; }
    .header-box { background: #1e293b; color: #fbbf24; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #fbbf24; }
    .ank-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(85px, 1fr)); gap: 10px; padding: 15px; }
    .ank-box { background: #ffffff; border: 2px solid #1e293b; height: 70px; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v98.0 (Final Logic - No Nonsense)")

ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_raw_logic(val, pid):
    if val < 0: return "XX"
    d1, d2 = val // 10, val % 10
    r = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
    rules = {
        1: f"{r[d1]}{r[d2]}",         # Mirror
        2: f"{d2}{d1}",               # Reverse
        3: f"{(d1+1)%10}{(d2+5)%10}", # Power 15
        4: f"{(d1+5)%10}{(d2+6)%10}"  # Power 56
    }
    return rules.get(pid, "XX")

def analyze_v98_raw(flat_data, curr_pos):
    potential = []
    # Targeted triggers from our 20-day discussion
    for t in [-1, -6, -12, -18, -24]:
        if curr_pos + t >= 0:
            base = flat_data[curr_pos + t]
            if base >= 0:
                for rid in [1, 2, 3, 4]:
                    res = get_raw_logic(base, rid)
                    if res != "XX": potential.append(res)
    
    counts = Counter(potential)
    # Strict verification: Ank must appear in multiple logic paths
    final = [k for k, v in counts.items() if v >= 2]
    if len(final) < 8: final = [k for k, v in counts.most_common(12)]
    return sorted(list(set(final)))[:12]

# --- SIDEBAR ---
uploaded_file = st.sidebar.file_uploader("📂 Upload 0DSP0.xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'GD':'GB', 'GZB':'GB'})
    
    flat_data = []
    for _, row in df.iterrows():
        for s in ORDER:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() else -1)
            
    sel_date = st.sidebar.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.sidebar.selectbox("🎰 Shift:", options=ORDER)
    
    s_idx = ORDER.index(target_s)
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + s_idx
    
    final_anks = analyze_v98_raw(flat_data, c_pos)
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]

    st.markdown(f'<div class="header-box"><h1>{target_s} Raw Analysis</h1><p>Result: {res_val}</p></div>', unsafe_allow_html=True)

    # 45-DAY BACKTEST TABLE (SABSE PEHLE)
    st.subheader(f"📜 45-Day Proof ({target_s})")
    hist_list = []
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + s_idx
        h_preds = analyze_v98_raw(flat_data, p_idx)
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds: status = "✅ HIT"
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list).tail(15))

    st.subheader("💰 Selection Grid")
    grid_html = '<div class="ank-grid">'
    for ank in final_anks:
        grid_html += f'<div class="ank-box">{ank}</div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)
else:
    st.info("File upload karo aur asli history dekho.")
    
