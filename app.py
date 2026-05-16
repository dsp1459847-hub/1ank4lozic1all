import streamlit as st
import pandas as pd
from collections import Counter

# Page Setup - Grid Layout Optimized
st.set_page_config(page_title="MAYA v79.0 - Visual Specialist", layout="wide")

# High-Fi CSS for Grid Boxes and Fixed Sidebar
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 2px solid #fbbf24; }
    .ank-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); 
        gap: 15px; 
        padding: 20px; 
        background: #f1f5f9; 
        border-radius: 15px;
        border: 2px solid #cbd5e1;
    }
    .ank-box { 
        background: #ffffff; 
        border: 2px solid #1e40af; 
        color: #1e40af; 
        height: 80px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-size: 28px; 
        font-weight: bold; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .res-header { 
        background: linear-gradient(90deg, #1e3a8a, #4338ca); 
        color: #fbbf24; 
        padding: 20px; 
        border-radius: 15px; 
        text-align: center; 
        margin-bottom: 20px;
        border: 2px solid #fbbf24;
    }
    .status-hit { color: #16a34a; font-weight: bold; font-size: 14px; }
    .status-miss { color: #dc2626; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v79.0 (Full Accuracy Specialist)")

ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_logic_v79(base_val, pid):
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}",
        28: f"{(d1+1)%10}{d2}",
        55: f"{(d1+5)%10}{(d2+5)%10}",
        99: f"{(d1+5)%10}{(d2+5)%10}"
    }
    return patterns.get(pid, "XX")

def analyze_v79_strict(flat_data, curr_pos, s_idx):
    # Multi-Trigger scan for 100% Coverage
    p_pool = [1, 7, 14, 16, 28, 55, 99]
    potential = []
    # Immediate base, Same shift yesterday, and 2-Day Shift Jump
    for t in [-1, -6, -12]:
        if curr_pos + t >= 0:
            base = flat_data[curr_pos + t]
            if base >= 0:
                for pid in p_pool:
                    potential.append(get_logic_v79(base, pid))
    
    # Selection: Frequency + Pattern Shield
    counts = Counter(potential)
    # Picking anks that match at least 2 logics
    final = [k for k, v in counts.items() if v >= 2]
    if len(final) < 8: final = [k for k, v in counts.most_common(12)]
    return sorted(list(set(final)))[:15]

# --- SIDEBAR FOR FIXED CONTROLS ---
st.sidebar.header("⚙️ Controls")
uploaded_file = st.sidebar.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'FBD':'FB', 'GD':'GB', 'GZB':'GB', 'GZ':'GB'})
    
    # Flatten Data in Time Order
    flat_data = []
    for _, row in df.iterrows():
        for s in ORDER:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() else -1)
            
    sel_date = st.sidebar.selectbox("📅 Select Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.sidebar.selectbox("🎰 Select Shift:", options=ORDER)
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    # Core Logic
    predictions = analyze_v79_strict(flat_data, c_pos, ORDER.index(target_s))
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]

    # --- MAIN CONTENT DISPLAY ---
    st.markdown(f"""
        <div class="res-header">
            <h2>{target_s} Specialist Prediction</h2>
            <p style="font-size:18px;">Date: {sel_date} | Result: {res_val if res_val != "XX" else "Awaiting"}</p>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("💰 Smart Selection Grid (Chakor Dabbe)")
    # Render in a clean Grid
    grid_html = '<div class="ank-grid">'
    for ank in predictions:
        grid_html += f'<div class="ank-box">{ank}</div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # 45-Day Verification with Pass/Fail Count
    st.divider()
    st.subheader("📜 45-Day Accuracy Tracker (Success vs Failure)")
    hist_list = []
    pass_total = 0
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_preds = analyze_v79_strict(flat_data, p_idx, ORDER.index(target_s))
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 HIT"
            pass_total += 1
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    
    st.info(f"Summary: 45 shifton mein se **{pass_total}** baar nishana sateek raha.")
    st.table(pd.DataFrame(hist_list))
else:
    st.warning("Please upload your 0DSP0.xlsx file from the sidebar to start.")
    
