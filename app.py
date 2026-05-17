import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

st.set_page_config(page_title="Shift Predictor Lite", layout="wide")

SHIFT_COLS = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]

def clean_num(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().upper()
    if s in ["XX", "X", "", "NAN", "NONE", "-"]:
        return np.nan
    try:
        return int(float(s))
    except:
        return np.nan

@st.cache_data(show_spinner=False)
def load_excel(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(uploaded_file, sheet_name=xls.sheet_names[0])
    df.columns = [str(c).strip().upper().replace(".", "").replace(" ", "_") for c in df.columns]
    rename_map = {}
    for c in df.columns:
        if c in ["S_NUMBER", "SNUMBER", "S_NUMBER_"]:
            rename_map[c] = "S_NUMBER"
        elif c == "DATE":
            rename_map[c] = "DATE"
        elif c in SHIFT_COLS:
            rename_map[c] = c
    df = df.rename(columns=rename_map)
    if "DATE" not in df.columns:
        raise ValueError("DATE column not found.")
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    for c in SHIFT_COLS:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = df[c].apply(clean_num)
    df = df.dropna(subset=["DATE"]).sort_values("DATE").reset_index(drop=True)
    return df

def shift_rules(train_df, target_shift, feature_shift, min_support=8):
    data = train_df[[feature_shift, target_shift]].dropna().copy()
    if data.empty:
        return pd.DataFrame(columns=["cond", "pred", "support", "prob"])
    data[feature_shift] = data[feature_shift].astype(int)
    data[target_shift] = data[target_shift].astype(int)

    counts = defaultdict(Counter)
    for a, b in zip(data[feature_shift], data[target_shift]):
        counts[a][b] += 1

    rows = []
    for cond_val, ctr in counts.items():
        total = sum(ctr.values())
        pred, sup = ctr.most_common(1)[0]
        if total >= min_support:
            rows.append({"cond": int(cond_val), "pred": int(pred), "support": int(total), "prob": float(sup / total)})
    if not rows:
        return pd.DataFrame(columns=["cond", "pred", "support", "prob"])
    return pd.DataFrame(rows).sort_values(["prob", "support"], ascending=False).reset_index(drop=True)

def predict_row(train_df, row, target_shift, threshold):
    best_pred = np.nan
    best_prob = -1.0
    best_from = ""
    for feat in SHIFT_COLS:
        if feat == target_shift or pd.isna(row.get(feat)):
            continue
        rules = shift_rules(train_df, target_shift, feat, min_support=8)
        if rules.empty:
            continue
        hit = rules[rules["cond"] == int(row[feat])]
        if hit.empty:
            continue
        hit = hit.iloc[0]
        if hit["prob"] >= threshold and hit["prob"] > best_prob:
            best_prob = float(hit["prob"])
            best_pred = int(hit["pred"])
            best_from = feat
    return best_pred, best_prob, best_from

def auto_threshold(df, target_shift):
    candidates = [0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.28, 0.30]
    base = df.reset_index(drop=True)
    best_th = 0.20
    best_acc = -1

    for th in candidates:
        hits = 0
        total = 0
        for i in range(30, len(base) - 1):
            train = base.iloc[:i].copy()
            row = base.iloc[i]
            actual = base.iloc[i + 1][target_shift]
            pred, _, _ = predict_row(train, row, target_shift, th)
            if not pd.isna(pred) and not pd.isna(actual):
                total += 1
                if int(pred) == int(actual):
                    hits += 1
        acc = hits / total if total else 0
        if acc > best_acc:
            best_acc = acc
            best_th = th
    return best_th

def mark_html(actual, pred):
    if pd.isna(actual) or pd.isna(pred):
        return "<span style='color:red;font-weight:bold'>❌</span>"
    return "<span style='color:green;font-weight:bold'>✅</span>" if int(actual) == int(pred) else "<span style='color:red;font-weight:bold'>❌</span>"

st.title("Shift Predictor Lite")

uploaded = st.file_uploader("Excel file upload करें", type=["xlsx"])
if not uploaded:
    st.info("Excel file upload करें.")
    st.stop()

try:
    df = load_excel(uploaded)

    with st.sidebar:
        target_shift = st.selectbox("Target shift", SHIFT_COLS, index=0)
        mode = st.selectbox("Mode", ["Select date", "Latest date"], index=0)

    valid_dates = sorted(df["DATE"].dropna().dt.date.unique().tolist())
    if not valid_dates:
        st.error("No valid dates found.")
        st.stop()

    threshold = auto_threshold(df, target_shift)

    if mode == "Select date":
        selected_date = st.date_input(
            "Date चुनें",
            value=valid_dates[-1],
            min_value=valid_dates[0],
            max_value=valid_dates[-1]
        )
    else:
        selected_date = valid_dates[-1]
        st.write(f"Latest date: **{selected_date}**")

    sel = df[df["DATE"].dt.date == selected_date]
    if sel.empty:
        st.warning("Selected date not found.")
        st.stop()

    idx = sel.index[0]
    train_df = df.iloc[:idx].copy()
    row = df.iloc[idx]

    pred, conf, frm = predict_row(train_df, row, target_shift, threshold)

    st.subheader("Prediction")
    c1, c2, c3 = st.columns(3)
    c1.metric("Selected Date", str(selected_date))
    c2.metric("Target Shift", target_shift)
    c3.metric("Predicted Number", "NA" if pd.isna(pred) else int(pred))
    st.write(f"Prediction is for **{selected_date}**.")
    st.write(f"Source shift: **{frm if frm else 'None'}**")

    st.subheader("Latest 20 History")
    rows = []
    start_idx = max(0, len(df) - 20)
    for i in range(start_idx, len(df)):
        cur = df.iloc[i]
        train = df.iloc[:i].copy()
        p, c, f = predict_row(train, cur, target_shift, threshold)
        rows.append({
            "DATE": cur["DATE"].date(),
            "ACTUAL": cur[target_shift],
            "PRED": p,
            "RESULT": mark_html(cur[target_shift], p)
        })
    hist = pd.DataFrame(rows)
    st.dataframe(hist, use_container_width=True)

    st.markdown("### Tick / Cross")
    for _, r in hist.iterrows():
        color = "green" if "green" in str(r["RESULT"]) else "red"
        mark = "✅" if color == "green" else "❌"
        st.markdown(
            f"<div style='color:{color};font-weight:bold'>{r['DATE']} | Actual: {r['ACTUAL']} | Pred: {r['PRED']} | {mark}</div>",
            unsafe_allow_html=True
        )

except Exception as e:
    st.error(f"Error: {e}")
