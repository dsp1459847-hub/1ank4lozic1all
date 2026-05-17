import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter, defaultdict

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

def build_rule_bank(train_df, target_shift, min_support=10):
    rules = []
    feat_cols = [c for c in SHIFT_COLS if c != target_shift]

    for feat in feat_cols:
        tmp = train_df[[feat, target_shift]].dropna().copy()
        if tmp.empty:
            continue
        tmp[feat] = tmp[feat].astype(int)
        tmp[target_shift] = tmp[target_shift].astype(int)

        grp = tmp.groupby(feat)[target_shift].agg(["count", lambda x: x.value_counts().idxmax(), lambda x: x.value_counts().max()])
        grp.columns = ["support", "pred", "hits"]
        grp["prob"] = grp["hits"] / grp["support"]
        grp = grp[grp["support"] >= min_support].reset_index()

        for _, r in grp.iterrows():
            rules.append({
                "feat": feat,
                "cond": int(r[feat]),
                "pred": int(r["pred"]),
                "support": int(r["support"]),
                "prob": float(r["prob"])
            })

    return pd.DataFrame(rules)

def predict_next(train_df, row, target_shift, min_support=10):
    bank = build_rule_bank(train_df, target_shift, min_support=min_support)
    if bank.empty:
        return np.nan, 0.0, "No rule"

    cand = bank[bank["cond"].isin([int(row[c]) for c in SHIFT_COLS if c != target_shift and pd.notna(row.get(c))])].copy()
    if cand.empty:
        return np.nan, 0.0, "No match"

    cand["weight"] = cand["support"] * cand["prob"]
    score = cand.groupby("pred")["weight"].sum().sort_values(ascending=False)

    pred = int(score.index[0])
    conf = float(score.iloc[0] / score.sum()) if score.sum() > 0 else 0.0

    top_rules = cand[cand["pred"] == pred].sort_values(["weight", "prob", "support"], ascending=False)
    src = ", ".join(top_rules["feat"].head(3).tolist())

    return pred, conf, src

def mark_symbol(actual, pred):
    if pd.isna(actual) or pd.isna(pred):
        return "❌"
    return "✅" if int(actual) == int(pred) else "❌"

st.title("Shift Predictor Lite")

uploaded = st.file_uploader("Excel file upload करें", type=["xlsx"])
if not uploaded:
    st.info("Excel file upload करें.")
    st.stop()

try:
    df = load_excel(uploaded)
    st.success(f"Loaded rows: {len(df)}")

    with st.sidebar:
        target_shift = st.selectbox("Target shift", SHIFT_COLS, index=0)
        min_support = st.slider("Min support", 3, 50, 10)
        mode = st.selectbox("Mode", ["Select cutoff date", "Latest date"], index=0)

    valid_dates = sorted(df["DATE"].dropna().dt.date.unique().tolist())
    if len(valid_dates) < 2:
        st.error("Not enough dates.")
        st.stop()

    cutoff_date = st.date_input(
        "Cutoff date चुनें",
        value=valid_dates[-2] if mode == "Select cutoff date" else valid_dates[-2],
        min_value=valid_dates[0],
        max_value=valid_dates[-2]
    )

    cutoff_rows = df[df["DATE"].dt.date == cutoff_date]
    if cutoff_rows.empty:
        st.warning("Cutoff date not found.")
        st.stop()

    cutoff_idx = cutoff_rows.index[0]
    if cutoff_idx + 1 >= len(df):
        st.warning("Next day data not available.")
        st.stop()

    train_df = df.iloc[:cutoff_idx + 1].copy()
    next_row = df.iloc[cutoff_idx + 1]
    next_date = next_row["DATE"].date()

    pred, conf, src = predict_next(train_df, next_row, target_shift, min_support=min_support)

    st.subheader("Prediction")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cutoff Date", str(cutoff_date))
    c2.metric("Prediction For", str(next_date))
    c3.metric("Predicted Number", "NA" if pd.isna(pred) else int(pred))
    st.write(f"Source: {src}")
    st.write(f"Confidence: {conf:.2f}")

    st.subheader("Backtest History (Last 20 Days)")
    rows = []
    start_idx = max(0, len(df) - 21)

    for i in range(start_idx, len(df) - 1):
        tr = df.iloc[:i + 1].copy()
        actual_row = df.iloc[i + 1]
        p, c, s = predict_next(tr, actual_row, target_shift, min_support=min_support)
        rows.append({
            "CUTOFF_DATE": df.iloc[i]["DATE"].date(),
            "PRED_FOR": actual_row["DATE"].date(),
            "ACTUAL": actual_row[target_shift],
            "PRED": p,
            "RESULT": mark_symbol(actual_row[target_shift], p),
            "SRC": s
        })

    hist = pd.DataFrame(rows).tail(20)
    st.dataframe(hist, use_container_width=True)

    acc = (hist["RESULT"] == "✅").mean() * 100 if not hist.empty else 0
    st.metric("Backtest Accuracy", f"{acc:.2f}%")

except Exception as e:
    st.error(f"Error: {e}")
