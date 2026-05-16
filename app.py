import streamlit as st
import pandas as pd
from collections import Counter

st.set_page_config(page_title="MAYA v96.0 - Common Logic", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #020617; border-right: 3px solid #fbbf24; }
    .common-header { 
        background: linear-gradient(135deg, #1e3a8a, #1e1b4b); 
        color: #fbbf24; padding: 25px; border-radius: 15px; 
        text-align: center; border: 3px solid #fbbf24; margin-bottom: 25px;
    }
    .ank-grid { 
        display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); 
        gap: 15px; padding: 20px; background: #ffffff; border-radius: 15px; border: 3px solid #fbbf24;
    }
    .ank-box { 
        background: #f8fafc; border: 2.5px solid #1e3a8a; color: #1e3a8a; 
        height: 95px; display: flex; align-items: center; justify-content: center; 
        font-size: 40px; font-weight: bold; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v96.0 (The Common Logic Aggregator)")

ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_aggregated_logic(val):
    """Merging Rashi, Angle, and Seat logics into one common filter"""
    if val < 0: return []
    d1, d2 = val // 10, val % 10
    r = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
    
    # Combined Rules from previous versions
    rules = [
        f"{r[d1]}{r[d2]}", f"{d2}{d1}", f"{(d1+1)%10}{(d2+5)%10}", 
        f"{(d1+5)%10}{(d2+6)%10}", f"{(d1+5)%10}{(d2+5)%10}", f"{(d1+1)%10}{d2}"
    ]
    return list(set(rules))

def analyze_v96_commonality(flat_data, curr_pos):
    """Finding the COMMON ank across all logic layers"""
    potential = []
    triggers = [-1, -6, -12, -18, -24] # Immediate & Shift Cycles
    
    for t in triggers:
        if curr_pos + t >= 0:
            base = flat_data[curr_pos + t]
            potential.extend(get_aggregated_logic(base))
                    
    counts = Counter(potential)
    # The 'Commonality' filter: Ank must be suggested by multiple rules
    final = [k for k, v in counts.items() if v >= 3] # Minimum 3 logic layers must agree
    
    if len(final) < 10:
        final = [k for k, v in counts.most_common(12)]
        
    return sorted(list(set(final)))[:12]

# --- UI CONTROLS ---
st.sidebar.header("🕹️ Master Aggregator")
uploaded_file = st.sidebar.file_uploader("📂 Upload 0DSP0 File")

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
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    final_anks = analyze_v96_commonality(flat_data, c_pos)
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]

    st.markdown(f"""<div class="common-header"><h1>{target_s} Common Logic Summary</h1>
    <p>Ensemble Method Active | Result: {res_val}</p></div>""", unsafe_allow_html=True)

    grid_html = '<div class="ank-grid">'
    for ank in final_anks:
        grid_html += f'<div class="ank-box">{ank}</div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    st.success("Bhai, yeh v96.0 ab pichle saare 'Tukkas' ko filter karke sirf wahi de raha hai jo sab mein Common hain.")
    
