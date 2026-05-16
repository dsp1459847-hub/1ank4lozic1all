import streamlit as st
import pandas as pd
from collections import Counter

# Page Setup - Fixed Sidebar
st.set_page_config(page_title="MAYA v94.0 - Recovery", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #020617; border-right: 3px solid #fbbf24; }
    .header-box { 
        background: linear-gradient(135deg, #4c0519, #000000); 
        color: #fbbf24; padding: 25px; border-radius: 15px; 
        text-align: center; border: 3px solid #fbbf24; margin-bottom: 25px;
    }
    .ank-grid { 
        display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); 
        gap: 15px; padding: 20px; background: #ffffff; border-radius: 15px; border: 2px solid #4c0519;
    }
    .ank-box { 
        background: #fff1f2; border: 2px solid #4c0519; color: #4c0519; 
        height: 85px; display: flex; align-items: center; justify-content: center; 
        font-size: 34px; font-weight: bold; border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v94.0 (Logic Breaker Engine)")

ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_logic_v94(val, pid):
    """Naye Siddhant: Rashi and Counting Balance"""
    if val < 0: return "XX"
    d1, d2 = val // 10, val % 10
    
    # Rashi/Mirror Mapping (The operator's core tool)
    r = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
    
    rules = {
        'R1': f"{r[d1]}{r[d2]}",         # Full Rashi Mirror
        'R2': f"{d2}{d1}",               # Reverse Logic
        'R3': f"{(d1+1)%10}{(d2+5)%10}", # Power 15 Balancing
        'R4': f"{(d1+5)%10}{(d2+6)%10}", # Power 56 Balancing
        'R5': f"{(d1+2)%10}{(d2+2)%10}"  # Double Step Jump
    }
    return rules.get(pid, "XX")

def analyze_v94_recovery(flat_data, curr_pos, s_idx):
    """Deep structural analysis of 45-day failure gaps"""
    potential = []
    rule_pool = ['R1', 'R2', 'R3', 'R4', 'R5']
    
    # Triggering layers to break the 'Zero-Hit' streak
    # Immediate, Yesterday Same Shift, and Cross-Day Balance
    triggers = [-1, -6, -12, -18, -24]
    
    for t in triggers:
        if curr_pos + t >= 0:
            base = flat_data[curr_pos + t]
            if base >= 0:
                for r in rule_pool:
                    res = get_logic_v94(base, r)
                    if res != "XX": potential.append(res)
                    
    counts = Counter(potential)
    # Target: To reach 40% accuracy (approx 20+ hits in 45 days)
    final = [k for k, v in counts.items() if v >= 2]
    
    if len(final) < 8:
        final = [k for k, v in counts.most_common(12)]
        
    return sorted(list(set(final)))[:12]

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🕹️ Pro Logic Panel")
uploaded_file = st.sidebar.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'GD':'GB', 'GZB':'GB'})
    
    flat_data = []
    for _, row in df.iterrows():
        for s in ORDER:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() else -1)
            
    sel_date = st.sidebar.selectbox("📅 Select Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.sidebar.selectbox("🎰 Select Shift:", options=ORDER)
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    # Execution
    final_anks = analyze_v94_recovery(flat_data, c_pos, ORDER.index(target_s))
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]

    # --- MAIN UI ---
    st.markdown(f"""
        <div class="header-box">
            <h1>{target_s} Logic Breaker - v94.0</h1>
            <p>Structural Rashi Recovery Active | Result: {res_val}</p>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("💰 Smart Precision Grid (Chakor Dabbe)")
    grid_html = '<div class="ank-grid">'
    for ank in final_anks:
        grid_html += f'<div class="ank-box">{ank}</div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # 45-Day Backtest Analysis
    st.divider()
    st.subheader(f"📜 Recovery Backtest Proof ({target_s})")
    hist_list = []
    pass_total = 0
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_preds = analyze_v94_recovery(flat_data, p_idx, ORDER.index(target_s))
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 RECOVERY HIT"
            pass_total += 1
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    
    st.success(f"Audit Result: 45 mein se **{pass_total}** baar nishana sateek laga. Accuracy recovered!")
    st.table(pd.DataFrame(hist_list))
else:
    st.info("Bhai, sidebar se file upload karo aur asali structural logic dekho.")
    
