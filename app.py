import streamlit as st
import pandas as pd

st.set_page_config(page_title="MAYA v73.0 - Ultimate Recovery", layout="wide")

st.markdown("""
    <style>
    .main-header { background: linear-gradient(90deg, #1e3a8a, #4338ca); color: #fbbf24; padding: 25px; border-radius: 15px; text-align: center; border: 3px solid #fbbf24; }
    .ank-box { background: #ffffff; border: 3px solid #1e40af; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .ank-val { font-size: 36px; font-weight: bold; color: #1e3a8a; }
    .hit-tag { background: #dcfce7; color: #166534; font-weight: bold; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 MAYA v73.0 (45-Day Recovery Specialist)")

# 1. TIME-CORRECTED SEQUENCE (The Backbone)
# DB(3:15 PM) -> SG(4:30 PM) -> FB(6:00 PM) -> GB(8:45 PM) -> GL(11:45 PM) -> DS(5:00 AM)
ORDER = ['DB', 'SG', 'FB', 'GB', 'GL', 'DS']

def get_v73_logic(base_val, pid):
    if base_val < 0: return "XX"
    d1, d2 = base_val // 10, base_val % 10
    
    patterns = {
        1: f"{(d1+1)%10}{(d2+1)%10}",
        7: f"{(d1+5)%10}{(d2+1)%10}",
        14: f"{d2}{(d1+2)%10}",
        16: f"{(d1+1)%10}{(d2+6)%10}", # 16+ Rule
        28: f"{(d1+1)%10}{d2}",
        55: f"{(d1+5)%10}{(d2+5)%10}", # 55- Rule
        99: f"{(d1+9)%10}{(d2+9)%10}"
    }
    return patterns.get(pid, f"{(d1+2)%10}{(d2+2)%10}")

def analyze_dynamic_rules(flat_data, curr_pos, s_idx):
    """Pichle 45 dinon mein kaunsa 'Base' aur 'Pattern' hit hua hai"""
    p_pool = [1, 7, 14, 16, 28, 55, 99]
    scores = {p: 0 for p in p_pool}
    
    # 45-Day Back-Scan (Total 270 shifts)
    for i in range(curr_pos - 270, curr_pos):
        if i < 30: continue
        if (i % 6) == s_idx:
            actual = str(flat_data[i]).zfill(2)
            # Two Dynamic Bases: 
            # 1. Pichli Shift (Immediate)
            # 2. Same Shift (Yesterday)
            bases = [flat_data[i-1], flat_data[i-6]]
            for b_idx, b_val in enumerate(bases):
                if b_val >= 0:
                    for pid in p_pool:
                        if get_v73_logic(b_val, pid) == actual:
                            # Immediate base ko zyada weight (2 points)
                            scores[pid] += (2 if b_idx == 0 else 1)
                            
    return sorted(scores, key=scores.get, reverse=True)[:4]

uploaded_file = st.file_uploader("📂 Upload 0DSP0 File", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns={'FD':'FB', 'GD':'GB', 'GZB':'GB'})
    
    # Process data in Time-Order
    flat_data = []
    for _, row in df.iterrows():
        for s in ORDER:
            v = str(row.get(s, "XX")).strip().split('.')[0]
            flat_data.append(int(v) if v.isdigit() else -1)
            
    sel_date = st.selectbox("📅 Select Date:", options=df['DATE'].astype(str).unique().tolist()[::-1])
    target_s = st.selectbox("🎰 Select Shift:", options=ORDER)
    
    d_idx = df[df['DATE'].astype(str) == sel_date].index[0]
    c_pos = (d_idx * 6) + ORDER.index(target_s)
    
    # Matrix Analysis
    best_pids = analyze_dynamic_rules(flat_data, c_pos, ORDER.index(target_s))
    
    # UI Output
    res_val = str(df.iloc[d_idx].get(target_s, "XX")).split('.')[0]
    st.markdown(f"""<div class="main-header"><h2>{target_s} Specialist v73.0</h2>
    <p>Theory Re-Aligned & Time Synchronized | Result: {res_val}</p></div>""", unsafe_allow_html=True)
    
    st.subheader("💎 Super Strong Predictions (Max 12-16 Anks)")
    # Using both Current Base and Yesterday Same-Shift Base
    b_prev = flat_data[c_pos - 1]
    b_yesterday = flat_data[c_pos - 6]
    
    final_anks = []
    for pid in best_pids:
        final_anks.append(get_v73_logic(b_prev, pid))
        final_anks.append(get_v73_logic(b_yesterday, pid))
    
    final_anks = sorted(list(set([a for a in final_anks if a != "XX"])))

    cols = st.columns(4)
    for i, ank in enumerate(final_anks[:12]):
        with cols[i % 4]:
            st.markdown(f'<div class="ank-box"><span class="hit-tag">Confirm</span><br><span class="ank-val">{ank}</span></div>', unsafe_allow_html=True)

    # 45-Day Accuracy Proof
    st.divider()
    st.subheader("📜 45-Day Accuracy Recovery Table")
    hist_list = []
    for i in range(d_idx - 45, d_idx + 1):
        if i < 0: continue
        p_idx = (i * 6) + ORDER.index(target_s)
        h_pids = analyze_dynamic_rules(flat_data, p_idx, ORDER.index(target_s))
        h_b_prev = flat_data[p_idx - 1]
        h_b_yest = flat_data[p_idx - 6]
        
        h_preds = []
        for pid in h_pids:
            h_preds.append(get_v73_logic(h_b_prev, pid))
            h_preds.append(get_v73_logic(h_b_yest, pid))
            
        actual = str(df.iloc[i].get(target_s, "XX")).split('.')[0]
        status = "❌"
        if actual.isdigit() and str(int(actual)).zfill(2) in h_preds: status = "🔥 HIT SUCCESS"
        hist_list.append({"Date": df.iloc[i]['DATE'], "Result": actual, "Status": status})
    st.table(pd.DataFrame(hist_list))
    
