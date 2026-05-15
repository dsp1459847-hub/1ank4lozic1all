import streamlit as st
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(page_title="MAYA v49.0 - All Shifts Scanner", layout="wide")

# Custom CSS for Mobile-Friendly Square UI
st.markdown("""
    <style>
    .live-res-box { 
        background: #1e293b; color: #fbbf24; padding: 15px; 
        border-radius: 12px; text-align: center; margin-bottom: 15px;
        border: 2px solid #fbbf24;
    }
    .grid-container { 
        display: grid; grid-template-columns: repeat(4, 1fr); 
        gap: 8px; max-width: 400px; margin: 10px auto; 
    }
    .grid-item { 
        background-color: #ffffff; color: #1e40af; padding: 12px; 
        border-radius: 8px; font-size: 20px; font-weight: bold; 
        text-align: center; border: 2px solid #bfdbfe;
    }
    .worst-tag { 
        background: #fee2e2; color: #b91c1c; padding: 3px 8px; 
        border-radius: 5px; font-size: 11px; margin-right: 5px; border: 1px solid #fecaca;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v49.0 (All-Shifts Deep Scanner)")

def get_all_shifts_data(df):
    """Sari shifton ko ek sequence mein lagana (DS -> FB -> GB -> GL -> DB -> SG)"""
    shifts = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    all_data = []
    for _, row in df.iterrows():
        for s in shifts:
            val = str(row.get(s, "XX")).split('.')[0]
            if val.isdigit():
                all_data.append(int(val))
            else:
                all_data.append(-1) # Placeholder for missing
    return all_data

def find_worst_gaps_all(data_list, current_idx):
    """90-gap scanning on combined shifts data"""
    gap_scores = {}
    for g in range(1, 91):
        if current_idx - g - 20 < 0: continue
        fails = 0
        for check in range(current_idx - 20, current_idx):
            if check - g < 0: continue
            if data_list[check-g] == data_list[check] and data_list[check] != -1:
                fails += 1
        gap_scores[g] = fails
    
    worst_gaps = sorted(gap_scores, key=gap_scores.get)[:5]
    
    bad_a, bad_b = [], []
    for wg in worst_gaps:
        val = data_list[current_idx - wg]
        if val != -1:
            bad_a.append(val // 10)
            bad_b.append(val % 10)
    
    final_a = max(set(bad_a), key=bad_a.count) if bad_a else 0
    final_b = max(set(bad_b), key=bad_b.count) if bad_b else 5
    return final_a, final_b, worst_gaps

def calculate_v49_logic(df, date_idx, target_shift):
    # Combine data
    all_vals = get_all_shifts_data(df)
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    # Current position in flat list
    current_pos = (date_idx * 6) + shifts_order.index(target_shift)
    
    # 1. Base Logic (Previous Value in Sequence)
    base_val = -1
    for i in range(1, 15):
        if current_pos - i >= 0:
            if all_vals[current_pos - i] != -1:
                base_val = all_vals[current_pos - i]
                break
    
    if base_val == -1: base_val = 0
    d1, d2 = base_val // 10, base_val % 10
    pa = (d1 + 1) % 10 if d1 != d2 else (d1 + 5) % 10
    pb = (d2 + 1) % 10
    ra, rb = (pa + 5) % 10, (pb + 5) % 10
    
    blocked_64 = set()
    for a in {pa, ra}:
        for i in range(10): blocked_64.add(f"{a}{i}")
    for b in {pb, rb}:
        for i in range(10): blocked_64.add(f"{i}{b}")
    
    target_36 = [str(i).zfill(2) for i in range(100) if str(i).zfill(2) not in blocked_64]
    
    # 2. Deep Scanner
    wa, wb, wgaps = find_worst_gaps_all(all_vals, current_pos)
    
    extra_hatao = set()
    for i in range(10):
        extra_hatao.add(f"{wa}{i}")
        extra_hatao.add(f"{i}{wb}")
        
    final_list = [j for j in target_36 if j not in extra_hatao]
    return final_list[:16], final_list[:9], wgaps

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD': 'FB', 'GD': 'GB', 'FBD': 'FB', 'GZB': 'GB'})
    
    c1, c2 = st.columns(2)
    with c1: sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    with c2: target_s = st.selectbox("🎰 Shift:", options=['DS', 'FB', 'GB', 'GL', 'DB', 'SG'])
    
    idx = df[df['DATE'].astype(str) == sel_date].index[0]
    
    # --- LIVE RESULT ---
    res_val = str(df.iloc[idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f"""
        <div class="live-res-box">
            <span style="font-size:14px;">ALL-SHIFTS LIVE RESULT</span><br>
            <span style="font-size:32px; font-weight:bold;">{res_val}</span>
        </div>
    """, unsafe_allow_html=True)

    # --- CALCULATION ---
    t16, t9, wgaps = calculate_v49_logic(df, idx, target_s)

    st.write("🔍 **Worst Gaps (All-Shifts):** " + "".join([f'<span class="worst-tag">G-{g}</span>' for g in wgaps]), unsafe_allow_html=True)

    # --- TARGET BOXES ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**✅ Stable (Square 16)**")
        grid_html = '<div class="grid-container">'
        for j in t16: grid_html += f'<div class="grid-item">{j}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

    with col_b:
        st.write("**💎 Super Hit (Square 9)**")
        grid_html = '<div class="grid-container" style="grid-template-columns: repeat(3, 1fr);">'
        for j in t9: grid_html += f'<div class="grid-item" style="background:#fff7ed; border-color:#fed7aa; color:#9a3412;">{j}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

    # --- HISTORY ---
    st.divider()
    st.subheader("📜 10-Shift Backtest History")
    hist = []
    # Test last 10 shifts sequence
    all_vals = get_all_shifts_data(df)
    shifts_order = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    current_pos = (idx * 6) + shifts_order.index(target_s)
    
    for p in range(current_pos - 10, current_pos + 1):
        if p < 0: continue
        # Reverse map position to date/shift
        d_idx = p // 6
        s_name = shifts_order[p % 6]
        
        h16, h9, _ = calculate_v49_logic(df, d_idx, s_name)
        actual = str(df.iloc[d_idx].get(s_name, "XX")).split('.')[0]
        
        status = "❌"
        if actual.isdigit():
            rv = str(int(actual)).zfill(2)
            if rv in h9: status = "💎 SUPER"
            elif rv in h16: status = "✅ HIT"
            
        hist.append({"Shift": f"{df.iloc[d_idx]['DATE']} {s_name}", "Result": actual, "Status": status})
    
    st.table(pd.DataFrame(hist))
  
