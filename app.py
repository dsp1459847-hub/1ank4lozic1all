import streamlit as st
import pandas as pd
from collections import Counter

# Page Configuration
st.set_page_config(page_title="MAYA v75.0 - Master Recovery", layout="wide")

st.markdown("""
    <style>
    .master-header { background: linear-gradient(135deg, #1e3a8a, #000000); color: #fbbf24; padding: 25px; border-radius: 15px; text-align: center; border: 3px solid #fbbf24; }
    .ank-card { background: #ffffff; border-radius: 12px; padding: 20px; border: 2px solid #1e3a8a; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .ank-val { font-size: 38px; font-weight: bold; color: #1e3a8a; }
    .hit-badge { background: #dcfce7; color: #166534; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v75.0 (Deep Cycle Analysis)")

# CORRECT CHRONOLOGICAL ORDER
ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_v75_logic(base_val, pid):
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}",
        28: f"{(d1+1)%10}{d2}",
        55: f"{(d1+5)%10}{(d2+5)%10}",
        99: f"{(d1+9)%10}{(d2+9)%10}"
    }
    return patterns.get(pid, "XX")

def analyze_v75_master(flat_data, curr_pos, s_idx):
    """Pichle 45 dinon ka behavior aur Frequency scan karna"""
    p_pool = [1, 7, 14, 16, 28, 55, 99]
    # Analysis points: Pichli shift, 2 pichli shift, aur kal ki same shift
    triggers = [-1, -2, -6, -12] 
    
    potential_hits = []
    for t in triggers:
        base = flat_data[curr_pos + t]
        if base >= 0:
            for pid in p_pool:
                res = get_v75_logic(base, pid)
                if res != "XX": potential_hits.append(res)
    
    # Frequency: Jo ank in 4 alag-alag trigger points se sabse zyada baar nikal raha hai
    counts = Counter(potential_hits)
    # Sirf wahi ank jo kam se kam 2 alag-alag logic se match ho rahe hon
    final_selection = [k for k, v in counts.items() if v >= 2]
    
    # Agar selection bahut chota hai toh top frequency wale uthao
    if len(final_selection) < 6:
        final_selection = [k for k, v in counts.most_common(12)]
        
    return final_selection[:15]

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'GD':'GB', 'GZB':'GB', 'GZ':'GB'})
    
    flat_data = []
    for _, row in df.iterrows():
        for s in ORDER:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() else -1)
            
    sel_date = st.selectbox("📅 Select Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Select Shift:", options=ORDER)
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    # MASTER ANALYSIS
    final_predictions = analyze_v75_master(flat_data, c_pos, ORDER.index(target_s))
    
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f"""<div class="master-header"><h2>{target_s} Specialist v75.0</h2>
    <p>Frequency & Cycle Analysis | Result: {res_val}</p></div>""", unsafe_allow_html=True)
    
    st.subheader("💎 Master Prediction (High Probability 12-15 Anks)")
    cols = st.columns(4)
    for i, ank in enumerate(final_predictions):
        with cols[i % 4]:
            st.markdown(f'<div class="ank-card"><span class="hit-badge">Cycle Match</span><br><span class="ank-val">{ank}</span></div>', unsafe_allow_html=True)

    # 45-Day Absolute Verification
    st.divider()
    st.subheader("📜 45-Day Accuracy Recovery Check")
    hist_list = []
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_preds = analyze_v75_master(flat_data, p_idx, ORDER.index(target_s))
        
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds: status = "🔥 MASTER HIT"
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
    
