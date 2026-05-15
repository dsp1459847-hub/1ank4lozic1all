import streamlit as st
import pandas as pd
import numpy as np

# Page Configuration for high-accuracy tracking
st.set_page_config(page_title="MAYA v69.0 - Final Correction", layout="wide")

st.markdown("""
    <style>
    .header-box { background: linear-gradient(135deg, #1e1b4b, #312e81); color: #fbbf24; padding: 25px; border-radius: 15px; text-align: center; border: 3px solid #fbbf24; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .grid-diamond { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; max-width: 600px; margin: 20px auto; }
    .ank-card { background: #ffffff; border: 2px solid #312e81; padding: 20px; border-radius: 15px; text-align: center; transition: 0.3s; }
    .ank-card:hover { transform: translateY(-5px); border-color: #fbbf24; }
    .ank-val { font-size: 38px; font-weight: bold; color: #1e1b4b; }
    .status-badge { background: #dcfce7; color: #166534; padding: 3px 12px; border-radius: 20px; font-size: 13px; font-weight: bold; border: 1px solid #166534; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v69.0 (45-Day Accuracy Recovery)")

def get_logic_v69(base_val, pid):
    """Refined Pattern Logic with Dynamic Adjustments"""
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    
    # Strictly applying 16/55 and Mirror rules with Shift Corrections
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}",
        28: f"{(d1+1)%10}{d2}",
        55: f"{(d1+5)%10}{(d2+5)%10}",
        99: f"{(d1+9)%10}{(d2+9)%10}" # High-end jump
    }
    return patterns.get(pid, f"{(d1+2)%10}{(d2+2)%10}")

def analyze_history_v69(flat_data, curr_pos, shift_idx):
    """Pichle 45 dinon ka failure analyze karke best selection karna"""
    p_pool = [1, 7, 14, 16, 28, 55, 99]
    scores = {p: 0 for p in p_pool}
    
    # 45 Days = ~270 shifts. Scan strictly.
    for i in range(curr_pos - 270, curr_pos):
        if i < 30: continue
        if (i % 6) == shift_idx:
            actual = str(flat_data[i]).zfill(2)
            # Checking multiple base points for same result
            bases = [flat_data[i-1], flat_data[i-6], flat_data[i-12]]
            
            for b_idx, base in enumerate(bases):
                if base > 0:
                    for pid in p_pool:
                        p_val = get_logic_v69(base, pid)
                        if p_val == actual:
                            scores[pid] += (3 - b_idx) # Higher weight to recent base
                            
    best_pids = sorted(scores, key=scores.get, reverse=True)[:4]
    return best_pids

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    shifts = ['DS', 'FB', 'GB', 'GL', 'DB', 'SG']
    flat_data = []
    for _, row in df.iterrows():
        for s in shifts:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() and int(v) >= 0 else -1)
            
    sel_date = st.selectbox("📅 Selection Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Selection Shift:", options=shifts)
    
    date_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    curr_pos = (date_idx * 6) + shifts.index(target_s)
    
    # Run Matrix Analysis
    best_pids = analyze_history_v69(flat_data, curr_pos, shifts.index(target_s))
    
    # UI Header
    res_val = str(df.iloc[date_idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f"""
        <div class="header-box">
            <h1>MAYA v69.0: {target_s} SPECIALIST</h1>
            <p style="font-size:18px;">Deep Memory Analysis | Result: {res_raw if res_raw != "XX" else "Awaiting"}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # PREDICTIONS
    st.subheader("💎 Master Diamond Predictions (Max 12-16 Anks)")
    bases = [flat_data[curr_pos - 1], flat_data[curr_pos - 6]]
    
    final_anks = []
    for b in bases:
        if b > 0:
            for pid in best_pids:
                final_anks.append(get_logic_v69(b, pid))
    
    final_anks = sorted(list(set([a for a in final_anks if a != "XX"])))

    cols = st.columns(4)
    for i, ank in enumerate(final_anks[:16]):
        with cols[i % 4]:
            st.markdown(f"""
                <div class="ank-card">
                    <span class="status-badge">High Conf</span><br>
                    <span class="ank-val">{ank}</span>
                </div>
            """, unsafe_allow_html=True)

    # 45-Day Backtest History
    st.divider()
    st.subheader("📜 45-Day Absolute Accuracy Backtest")
    hist_list = []
    for i in range(date_idx - 45, date_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + shifts.index(target_s)
        h_pids = analyze_history_v69(flat_data, p_idx, shifts.index(target_s))
        h_bases = [flat_data[p_idx - 1], flat_data[p_idx - 6]]
        h_preds = []
        for hb in h_bases:
            if hb > 0:
                for hp in h_pids: h_preds.append(get_logic_v69(hb, hp))
        
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 SUCCESS HIT"
            
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    
    st.table(pd.DataFrame(hist_list))
    
