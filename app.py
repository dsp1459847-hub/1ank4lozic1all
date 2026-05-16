import streamlit as st
import pandas as pd
from collections import Counter

# Page Setup - Sidebar and Grid optimization
st.set_page_config(page_title="MAYA v81.0 - Pattern Decoder", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 2px solid #fbbf24; color: white; }
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
    .status-tag { color: #16a34a; font-weight: bold; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v81.0 (Pattern-Shift Decoder)")

# TIME-SYNCHRONIZED ORDER
ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_pattern_logic(base_val, pid):
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}",
        28: f"{(d1+1)%10}{d2}",
        55: f"{(d1+5)%10}{(d2+5)%10}",
        99: f"{(d1+5)%10}{(d2+5)%10}" # Mirror Trap
    }
    return patterns.get(pid, "XX")

def analyze_dynamic_shift(flat_data, curr_pos, s_idx):
    """Detects which pattern the operator is currently using for THIS shift"""
    p_pool = [1, 7, 14, 16, 28, 55, 99]
    active_patterns = {p: 0 for p in p_pool}
    
    # Scan recent 30 shifts (approx 5 days) to find the 'LIVE' pattern
    for i in range(curr_pos - 30, curr_pos):
        if (i % 6) == s_idx and i >= 6:
            actual = str(flat_data[i]).zfill(2)
            # Check which base/pattern combination actually worked recently
            for base_offset in [-1, -6, -12]:
                base = flat_data[i + base_offset]
                if base >= 0:
                    for pid in p_pool:
                        if get_pattern_logic(base, pid) == actual:
                            active_patterns[pid] += 2 # Higher weight to recent success
                            
    # Pick top 3 patterns that worked in the last 5 days
    best_pids = sorted(active_patterns, key=active_patterns.get, reverse=True)[:3]
    return best_pids

def generate_v81_prediction(flat_data, curr_pos, s_idx):
    best_pids = analyze_dynamic_shift(flat_data, curr_pos, s_idx)
    potential = []
    
    # Apply these LIVE patterns to current triggers
    for t in [-1, -6, -12]:
        base = flat_data[curr_pos + t]
        if base >= 0:
            for pid in best_pids:
                res = get_pattern_logic(base, pid)
                if res != "XX": potential.append(res)
    
    return sorted(list(set(potential)))[:15]

# --- SIDEBAR FOR FIXED SELECTION ---
st.sidebar.header("⚙️ Dynamic Settings")
uploaded_file = st.sidebar.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'FBD':'FB', 'GD':'GB', 'GZB':'GB', 'GZ':'GB'})
    
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
    final_anks = generate_v81_prediction(flat_data, c_pos, ORDER.index(target_s))
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]

    # --- MAIN UI ---
    st.markdown(f"""
        <div class="st-res-header">
            <h1>{target_s} Dynamic Prediction</h1>
            <p style="font-size:18px;">Operator Pattern Switcher Active | Date: {sel_date} | Result: {res_val}</p>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("💰 Live Pattern Selection (Chakor Dabbe)")
    grid_html = '<div class="ank-grid">'
    for ank in final_anks:
        grid_html += f'<div class="ank-box">{ank}</div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # Historical Accuracy Proof
    st.divider()
    st.subheader(f"📜 Accuracy Backtest (Detecting Pattern Shifts)")
    hist_list = []
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_preds = generate_v81_prediction(flat_data, p_idx, ORDER.index(target_s))
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds: status = "✅ HIT"
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    
    st.table(pd.DataFrame(hist_list))
else:
    st.warning("Sidebar se 0DSP0.xlsx file upload karein.")
    
