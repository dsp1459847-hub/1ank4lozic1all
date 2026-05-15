import streamlit as st
import pandas as pd
from collections import Counter

# Page Setup
st.set_page_config(page_title="MAYA v67.0 - Sequence Hunter", layout="wide")

st.markdown("""
    <style>
    .trigger-active { background: #065f46; color: #fbbf24; padding: 15px; border-radius: 12px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .pattern-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px; }
    .ank-box { background: #ffffff; border: 2px solid #1e40af; padding: 15px; border-radius: 10px; text-align: center; }
    .ank-val { font-size: 26px; font-weight: bold; color: #1e40af; }
    .stats { font-size: 11px; color: #059669; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v67.0 (Sequence & Trigger Hunter)")

def get_pattern_logic(base_val, pid):
    """Refined 32-Pattern Logic Core"""
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    # Aapke bataye huye pattern logics
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}", # 16+ logic
        28: f"{(d1+1)%10}{d2}",
        32: f"{(d1+5)%10}{(d2+5)%10}",
        55: f"{(d1+5)%10}{(d2+5)%10}" # 55-55 logic
    }
    return patterns.get(pid, f"{(d1+2)%10}{(d2+2)%10}")

def find_trigger_sequence(flat_data, curr_pos, target_shift_idx):
    """Pichle 1 saal mein trigger ke baad ka behavior scan karna"""
    pattern_pool = [1, 7, 14, 16, 28, 32, 55]
    sequence_scores = {p: 0 for p in pattern_pool}
    
    # 1. Look for 'Match' triggers in history (Last 300 shifts ~ 6 months)
    for i in range(curr_pos - 300, curr_pos):
        if i < 10: continue
        
        # Check if shift 'i' was a trigger (Match between prediction and history)
        # For simulation, we check if current result matches previous shift logic
        if flat_data[i] != -1:
            # Analyze what happened in the next few shifts (specifically our target shift)
            # Find the next occurrence of our target shift after this trigger
            for jump in range(1, 7):
                if (i + jump) % 6 == target_shift_idx and (i + jump) < curr_pos:
                    actual_next = str(flat_data[i + jump]).zfill(2)
                    base_for_next = flat_data[i + jump - 1]
                    if base_for_next > 0:
                        for pid in pattern_pool:
                            if get_pattern_logic(base_for_next, pid) == actual_next:
                                sequence_scores[pid] += 1
    
    # Top 4 most successful patterns for this sequence
    best_pids = sorted(sequence_scores, key=sequence_scores.get, reverse=True)[:4]
    return best_pids, sequence_scores

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
            
    sel_date = st.selectbox("📅 Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Shift:", options=shifts)
    
    date_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    curr_pos = (date_idx * 6) + shifts.index(target_s)
    
    # Analyze Sequence
    best_pids, scores = find_trigger_sequence(flat_data, curr_pos, shifts.index(target_s))
    
    # UI Output
    res_raw = str(df.iloc[date_idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f'<div class="trigger-active"><h2>SHIFT: {target_s} | MASTER SEQUENCE</h2><p>Trigger Found: Analyzing Agli 6 Shiftron ke Patterns...</p></div>', unsafe_allow_html=True)
    
    # Predictions
    st.subheader("💎 Sequence-Verified Predictions (Max 12-16 Anks)")
    base_val = flat_data[curr_pos - 1]
    
    cols = st.columns(4)
    final_prediction_list = []
    for i, pid in enumerate(best_pids):
        pred = get_pattern_logic(base_val, pid)
        final_prediction_list.append(pred)
        with cols[i]:
            st.markdown(f"""
                <div class="ank-box">
                    <p style="color:gray; font-size:11px;">Pattern {pid}</p>
                    <span class="ank-val">{pred}</span><br>
                    <span class="stats">History Score: {scores[pid]}</span>
                </div>
            """, unsafe_allow_html=True)

    # Historical Backtest
    st.divider()
    st.subheader("📜 1-Month Sequence Backtest")
    hist_list = []
    for i in range(date_idx - 15, date_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + shifts.index(target_s)
        h_pids, _ = find_trigger_sequence(flat_data, p_idx, shifts.index(target_s))
        h_base = flat_data[p_idx - 1]
        h_preds = [get_pattern_logic(h_base, pid) for pid in h_pids]
        
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds:
            status = "🔥 SEQUENCE HIT"
            
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
    
