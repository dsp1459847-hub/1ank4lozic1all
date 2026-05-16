import streamlit as st
import pandas as pd
from collections import Counter

# Page Configuration - Grid & Sidebar Optimized
st.set_page_config(page_title="MAYA v80.0 - Quad Recovery", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 3px solid #fbbf24; }
    .st-res-header { 
        background: linear-gradient(90deg, #1e3a8a, #1e40af); 
        color: #fbbf24; padding: 25px; border-radius: 15px; 
        text-align: center; border: 2px solid #fbbf24; margin-bottom: 25px;
    }
    .ank-grid { 
        display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); 
        gap: 15px; padding: 20px; background: #f8fafc; border-radius: 15px; border: 1px solid #cbd5e1;
    }
    .ank-box { 
        background: #ffffff; border: 3px solid #1e40af; color: #1e40af; 
        height: 80px; display: flex; align-items: center; justify-content: center; 
        font-size: 32px; font-weight: bold; border-radius: 12px;
    }
    .hit-tag { color: #16a34a; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v80.0 (The 4-Shift Success Engine)")

# STRICT TIME ORDER
ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_logic_v80(base_val, pid):
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}",
        28: f"{(d1+1)%10}{d2}",
        55: f"{(d1+5)%10}{(d2+5)%10}",
        100: f"{(d1+5)%10}{(d2+5)%10}" # Fixed Mirror
    }
    return patterns.get(pid, "XX")

def analyze_v80_recovery(flat_data, curr_pos, s_idx):
    p_pool = [1, 7, 14, 16, 28, 55, 100]
    potential = []
    
    # Adaptive Trigger: For weak shifts, we scan deeper history
    # 1. Immediate Base | 2. Same Shift Yesterday | 3. Same Shift Day Before Yesterday
    triggers = [-1, -6, -12]
    
    for t in triggers:
        if curr_pos + t >= 0:
            base = flat_data[curr_pos + t]
            if base >= 0:
                for pid in p_pool:
                    res = get_logic_v80(base, pid)
                    if res != "XX": potential.append(res)
    
    counts = Counter(potential)
    # Selection: Anks that match at least 2 different time-triggers
    final = [k for k, v in counts.items() if v >= 2]
    
    # If recovery is weak, fallback to top probability
    if len(final) < 8:
        final = [k for k, v in counts.most_common(12)]
        
    return sorted(list(set(final)))[:15]

# --- SIDEBAR CONTROLS ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1532/1532514.png", width=100)
st.sidebar.header("⚙️ Final Settings")
uploaded_file = st.sidebar.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'FBD':'FB', 'GD':'GB', 'GZB':'GB', 'GZ':'GB'})
    
    # Chronological Data Link
    flat_data = []
    for _, row in df.iterrows():
        for s in ORDER:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() else -1)
            
    sel_date = st.sidebar.selectbox("📅 Select Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.sidebar.selectbox("🎰 Select Shift:", options=ORDER)
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    # Run Logic
    final_predictions = analyze_v80_recovery(flat_data, c_pos, ORDER.index(target_s))
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]

    # --- MAIN UI DISPLAY ---
    st.markdown(f"""
        <div class="st-res-header">
            <h1>{target_s} Specialist Prediction</h1>
            <p style="font-size:18px;">4-Shift Recovery Mode Active | Date: {sel_date} | Result: {res_val}</p>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("💰 Strong Prediction Grid (Chakor Dabbe)")
    grid_html = '<div class="ank-grid">'
    for ank in final_predictions:
        grid_html += f'<div class="ank-box">{ank}</div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # 45-Day Accuracy Tracker
    st.divider()
    st.subheader(f"📜 45-Day Accuracy Proof ({target_s})")
    hist_list = []
    pass_total = 0
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_preds = analyze_v80_recovery(flat_data, p_idx, ORDER.index(target_s))
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "✅ HIT"
            pass_total += 1
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    
    st.success(f"Recovery Analysis: 45 shifton mein se **{pass_total}** baar nishana sahi laga.")
    st.table(pd.DataFrame(hist_list))
else:
    st.warning("Please upload your 0DSP0.xlsx file from the sidebar to activate the recovery logic.")
    
