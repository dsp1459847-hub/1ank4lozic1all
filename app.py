import streamlit as st
import pandas as pd

st.set_page_config(page_title="MAYA v74.0 - Auto-Switch", layout="wide")

st.markdown("""
    <style>
    .auto-header { background: linear-gradient(90deg, #1e293b, #334155); color: #fbbf24; padding: 25px; border-radius: 15px; text-align: center; border: 3px solid #fbbf24; }
    .pattern-card { background: #f1f5f9; border-left: 5px solid #0f172a; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .ank-val { font-size: 36px; font-weight: bold; color: #1e293b; }
    .status-active { color: #16a34a; font-weight: bold; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v74.0 (Automatic Pattern Switcher)")

# CORRECT TIME ORDER
ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_logic_v74(base_val, pid):
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
    return patterns.get(pid, f"{(d1+2)%10}{(d2+2)%10}")

def get_best_active_patterns(flat_data, curr_pos, s_idx):
    """Automatic scan to find which patterns are currently working"""
    p_pool = [1, 7, 14, 16, 28, 55, 99]
    performance = {p: 0 for p in p_pool}
    
    # Scanning only last 15 days for 'HOT' patterns (Fresh Trends)
    for i in range(curr_pos - 90, curr_pos):
        if i < 12: continue
        if (i % 6) == s_idx:
            actual = str(flat_data[i]).zfill(2)
            # Checking immediate base trigger
            base = flat_data[i-1]
            if base >= 0:
                for p in p_pool:
                    if get_logic_v74(base, p) == actual:
                        performance[p] += 1
    
    # Sort patterns by recent performance
    sorted_patterns = sorted(performance, key=performance.get, reverse=True)
    return sorted_patterns[:4], performance

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
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
    
    # AUTOMATIC SELECTION
    active_pids, all_perf = get_best_active_patterns(flat_data, c_pos, ORDER.index(target_s))
    
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f"""<div class="auto-header"><h2>{target_s} - Auto-Adaptive Engine</h2>
    <p>Live Scanning Active Patterns... Result: {res_val}</p></div>""", unsafe_allow_html=True)
    
    st.subheader("🔥 Current Working Patterns (Auto-Selected)")
    base_trigger = flat_data[c_pos - 1]
    
    cols = st.columns(4)
    for i, pid in enumerate(active_pids):
        ank = get_logic_v74(base_trigger, pid)
        with cols[i]:
            st.markdown(f"""<div class="pattern-card">
            <span class="status-active">● Active Trend</span><br>
            <p style="color:gray;font-size:12px;">Rule {pid} (Hits: {all_perf[pid]})</p>
            <span class="ank-val">{ank}</span></div>""", unsafe_allow_html=True)

    # Historical Accuracy with Auto-Switching
    st.divider()
    st.subheader("📜 Backtest with Auto-Switching (45 Days)")
    hist_list = []
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        # For each date, code finds what was working 'then'
        h_pids, _ = get_best_active_patterns(flat_data, p_idx, ORDER.index(target_s))
        h_base = flat_data[p_idx - 1]
        h_preds = [get_logic_v74(h_base, hp) for hp in h_pids]
        
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds: status = "✅ AUTO-HIT"
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
                
