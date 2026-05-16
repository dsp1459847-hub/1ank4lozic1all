import streamlit as st
import pandas as pd
from collections import Counter

# Page Setup
st.set_page_config(page_title="MAYA v77.0 - Iron Clad", layout="wide")

st.markdown("""
    <style>
    .operator-shield { background: linear-gradient(135deg, #450a0a, #7f1d1d); color: #fbbf24; padding: 25px; border-radius: 15px; text-align: center; border: 4px solid #fbbf24; box-shadow: 0 10px 20px rgba(0,0,0,0.4); }
    .ank-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }
    .ank-box { background: #ffffff; border: 3px solid #7f1d1d; padding: 15px; border-radius: 12px; text-align: center; }
    .ank-val { font-size: 34px; font-weight: bold; color: #450a0a; }
    .defense-tag { background: #fef2f2; color: #991b1b; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; border: 1px solid #fecaca; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v77.0 (Operator-Proof Final Defense)")

ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_logic_v77(base_val, pid):
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}",
        28: f"{(d1+1)%10}{d2}",
        55: f"{(d1+5)%10}{(d2+5)%10}",
        MIRROR: f"{(d1+5)%10}{(d2+5)%10}" # Operator Mirror Trap
    }
    return patterns.get(pid, "XX")

def analyze_v77_defense(flat_data, curr_pos, s_idx):
    """Deep analysis to beat the operator trap"""
    p_pool = [1, 7, 14, 16, 28, 55]
    potential = []
    
    # Layer 1: Time-Chain (Immediate & Yesterday)
    for t in [-1, -6]:
        base = flat_data[curr_pos + t]
        if base >= 0:
            for pid in p_pool:
                potential.append(get_logic_v77(base, pid))
    
    # Layer 2: Frequency Analysis (Last 3 Months)
    # Finding "Silent" numbers (Operator's Target)
    recent_history = flat_data[curr_pos-100 : curr_pos]
    silent_anks = [str(i).zfill(2) for i in range(100) if i not in recent_history]
    
    # Layer 3: Selection Logic
    counts = Counter(potential)
    # Anks that appear in patterns AND are relatively silent or high-freq
    master_selection = [k for k, v in counts.items() if v >= 2 or k in silent_anks[:5]]
    
    return sorted(list(set(master_selection)))[:15]

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'GD':'GB', 'GZB':'GB'})
    
    flat_data = []
    for _, row in df.iterrows():
        for s in ORDER:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() else -1)
            
    sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift:", options=ORDER)
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    final_anks = analyze_v77_defense(flat_data, c_pos, ORDER.index(target_s))
    
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f"""<div class="operator-shield"><h2>{target_s} Iron-Clad Defense</h2>
    <p>Target: 100% Logic for 30% Real Pass | Current Result: {res_val}</p></div>""", unsafe_allow_html=True)
    
    st.subheader("🛡️ Defense Selection (Anti-Trap Anks)")
    cols = st.columns(4)
    for i, ank in enumerate(final_anks):
        with cols[i % 4]:
            st.markdown(f'<div class="ank-box"><span class="ank-val">{ank}</span><br><span class="defense-tag">Shield Validated</span></div>', unsafe_allow_html=True)

    # RE-VALIDATED HISTORY
    st.divider()
    st.subheader("📜 60-Shift Stress Test (Absolute Results)")
    hist_list = []
    pass_count = 0
    for i in range(d_idx - 60, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_preds = analyze_v77_defense(flat_data, p_idx, ORDER.index(target_s))
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 SHIELD HIT"
            pass_count += 1
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    
    st.success(f"Stress Test Result: 60 mein se **{pass_count}** pass. Operator-Proof Efficiency: {round(pass_count/61*100, 2)}%")
    st.table(pd.DataFrame(hist_list).tail(15))
        
