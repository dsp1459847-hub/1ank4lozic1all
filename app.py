import streamlit as st
import pandas as pd

st.set_page_config(page_title="MAYA v72.0 - Theory Re-Aligned", layout="wide")

st.markdown("""
    <style>
    .theory-header { background: linear-gradient(90deg, #1e1b4b, #4338ca); color: #fbbf24; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #fbbf24; }
    .logic-card { background: #f8fafc; border-left: 6px solid #4f46e5; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    .ank-val { font-size: 34px; font-weight: bold; color: #1e1b4b; text-align: center; display: block; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v72.0 (Corrected Logic Chain)")

# --- CORRECT TIME ORDER ---
# 1. DB (15:15) | 2. SG (16:30) | 3. FB (18:00) | 4. GB (20:45) | 5. GL (23:45) | 6. DS (05:00)
ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def apply_theory_logic(base_val, pid):
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    
    # Theory Patterns - Re-aligned to Time Sequence
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}", # Fixed +16 Theory
        28: f"{(d1+1)%10}{d2}",
        55: f"{(d1+5)%10}{(d2+5)%10}", # Fixed +55 Theory
        99: f"{(d1+9)%10}{(d2+9)%10}"
    }
    return patterns.get(pid, f"{(d1+2)%10}{(d2+2)%10}")

def analyze_theory_accuracy(flat_data, curr_pos, s_idx):
    p_pool = [1, 7, 14, 16, 28, 55, 99]
    scores = {p: 0 for p in p_pool}
    
    # Scan history strictly using the new Time-Chain
    for i in range(curr_pos - 300, curr_pos):
        if i < 30: continue
        if (i % 6) == s_idx:
            actual = str(flat_data[i]).zfill(2)
            # Yahan par 'i-1' ab waqai sahi pichli shift hogi time ke hisab se
            base = flat_data[i-1] 
            if base >= 0:
                for p in p_pool:
                    if apply_theory_logic(base, p) == actual:
                        scores[p] += 1
    return sorted(scores, key=scores.get, reverse=True)[:4]

uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'GD':'GB', 'GZB':'GB', 'GZ':'GB'})
    
    # Build data in Chronological Time Flow
    flat_data = []
    for _, row in df.iterrows():
        for s in ORDER:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() else -1)
            
    sel_date = st.selectbox("📅 Selection Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Selection Shift:", options=ORDER)
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    # Analyze best patterns based on corrected chain
    best_pids = analyze_theory_accuracy(flat_data, c_pos, ORDER.index(target_s))
    
    # UI Output
    st.markdown(f"""<div class="theory-header"><h2>{target_s} Logic Specialist</h2>
    <p>Theory re-aligned to Time Sequence: DB > SG > FB > GB > GL > DS</p></div>""", unsafe_allow_html=True)
    
    st.subheader("💎 Theory-Corrected Anks (Strong Hits)")
    base_trigger = flat_data[c_pos - 1] # Now correctly linked!
    
    cols = st.columns(4)
    for i, pid in enumerate(best_pids):
        ank = apply_theory_logic(base_trigger, pid)
        with cols[i]:
            st.markdown(f"""<div class="logic-card"><p style="color:gray;font-size:12px;">Rule {pid}</p>
            <span class="ank-val">{ank}</span></div>""", unsafe_allow_html=True)

    # Re-testing History with corrected sequence
    st.divider()
    st.subheader("📜 Backtest (Time-Synchronized Success)")
    hist_list = []
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_pids = analyze_theory_accuracy(flat_data, p_idx, ORDER.index(target_s))
        h_base = flat_data[p_idx - 1]
        h_preds = [apply_theory_logic(h_base, hp) for hp in h_pids]
        
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds: status = "🔥 THEORY HIT"
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
    
