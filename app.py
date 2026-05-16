import streamlit as st
import pandas as pd
from collections import Counter

# Page Config & Visual Setup
st.set_page_config(page_title="MAYA v85.0 - Structural Relation", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #020617; border-right: 3px solid #fbbf24; }
    .master-header { 
        background: linear-gradient(135deg, #1e3a8a, #000000); 
        color: #fbbf24; padding: 25px; border-radius: 15px; 
        text-align: center; border: 3px solid #fbbf24; margin-bottom: 25px;
    }
    .ank-grid { 
        display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); 
        gap: 12px; padding: 20px; background: #ffffff; border-radius: 15px; border: 2px solid #fbbf24;
    }
    .ank-box { 
        background: #f8fafc; border: 2px solid #1e3a8a; color: #1e3a8a; 
        height: 80px; display: flex; align-items: center; justify-content: center; 
        font-size: 32px; font-weight: bold; border-radius: 12px;
    }
    .logic-note { background: #fffbeb; border-left: 5px solid #f59e0b; padding: 10px; margin-bottom: 20px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v85.0 (Cross-Shift Structural Matrix)")

ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_pattern_32(val, pid):
    """32 patterns and odd-even logic integration"""
    if val < 0: return "XX"
    d1, d2 = val // 10, val % 10
    
    # Structural Theory Rules
    logics = {
        1: f"{(d1+1)%10}{(d2+1)%10}", # Step 1
        16: f"{(d1+1)%10}{(d2+6)%10}", # Power 16
        55: f"{(d1+5)%10}{(d2+5)%10}", # Mirror 55
        28: f"{(d1+2)%10}{(d2+8)%10}", # Cross 28
        11: f"{(d1)%10}{(d2+1)%10}",    # Same-Digit Slide
        22: f"{(d1+2)%10}{(d2)%10}",    # Jump Slide
        'OE': f"{(d1+1)%10 if d1%2==0 else (d1+5)%10}{d2}" # Odd-Even Switch
    }
    return logics.get(pid, "XX")

def analyze_structural_relation(flat_data, curr_pos, s_idx):
    """Deep Relation Analysis (Shift-to-Shift & Pattern-to-Pattern)"""
    p_pool = [1, 16, 55, 28, 11, 22, 'OE']
    potential = []
    
    # 1. RELATION CHECK: Pichli shift ka structural impact
    prev_val = flat_data[curr_pos - 1]
    if prev_val >= 0:
        # Check if Double Ank (e.g. 22) or Same Odd-Even
        is_double = (prev_val // 10 == prev_val % 10)
        is_same_oe = (prev_val // 10 % 2 == prev_val % 10 % 2)
        
        # Apply specific logic based on structure
        if is_double:
            potential.append(get_pattern_32(prev_val, 55)) # Double follows Mirror
            potential.append(get_pattern_32(prev_val, 11))
        if is_same_oe:
            potential.append(get_pattern_32(prev_val, 'OE'))
            
    # 2. SEQUENCE CHECK: Pattern Triplet (What follows 2 patterns?)
    for t_offset in [-1, -6, -12]:
        base = flat_data[curr_pos + t_offset]
        if base >= 0:
            for p in p_pool:
                potential.append(get_pattern_32(base, p))

    counts = Counter(potential)
    # Picking anks with high structural probability
    final = [k for k, v in counts.items() if v >= 2]
    if len(final) < 10:
        final = [k for k, v in counts.most_common(12)]
    return sorted(list(set(final)))[:15]

# --- SIDEBAR (THE NOTE MAKER) ---
st.sidebar.header("📊 Shift Relation Notes")
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
            
    sel_date = st.sidebar.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.sidebar.selectbox("🎰 Shift:", options=ORDER)
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    # Prediction & Relation logic
    final_anks = analyze_structural_relation(flat_data, c_pos, ORDER.index(target_s))
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]

    # --- UI DISPLAY ---
    st.markdown(f"""
        <div class="master-header">
            <h1>{target_s} Structural Analysis</h1>
            <p>Relation Sequence Active | Date: {sel_date} | Result: {res_val}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""<div class="logic-note">
    <b>Relation Note:</b> Analyzing {target_s} based on its link with pichli shift aur pichle 3 dinon ke structural pattern sequence se.
    </div>""", unsafe_allow_html=True)

    st.subheader("💎 Structural Selection Grid")
    grid_html = '<div class="ank-grid">'
    for ank in final_anks:
        grid_html += f'<div class="ank-box">{ank}</div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # 45-Day Structural Backtest
    st.divider()
    st.subheader(f"📜 Structural Accuracy Backtest ({target_s})")
    hist_list = []
    pass_total = 0
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_preds = analyze_structural_relation(flat_data, p_idx, ORDER.index(target_s))
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 STRUCTURAL HIT"
            pass_total += 1
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    
    st.info(f"Summary: 45 shifton mein se **{pass_total}** baar Structural HIT mila.")
    st.table(pd.DataFrame(hist_list))
    
