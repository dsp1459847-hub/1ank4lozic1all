import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

st.set_page_config(page_title="History Backtest Predictor", layout="wide")

SHIFT_COLS = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]

def clean_val(x):
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
def load_data(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(uploaded_file, sheet_name=xls.sheet_names[0])
    df.columns = [str(c).strip().upper().replace(".", "").replace(" ", "_") for c in df.columns]

    rename = {}
    for c in df.columns:
        if c in ["S_NUMBER", "SNUMBER", "S_NUMBER_"]:
            rename[c] = "S_NUMBER"
        elif c == "DATE":
            rename[c] = "DATE"
        elif c in SHIFT_COLS:
            rename[c] = c
    df = df.rename(columns=rename)

    if "DATE" not in df.columns:
        raise ValueError("DATE column not found")

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    for c in SHIFT_COLS:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = df[c].apply(clean_val)

    df = df.dropna(subset=["DATE"]).sort_values("DATE").reset_index(drop=True)
    return df

def make_rule_bank(train_df, target, min_support=8):
    rows = []
    cols = [c for c in SHIFT_COLS if c != target]

    for feat in cols:
        tmp = train_df[[feat, target]].dropna().copy()
        if len(tmp) < min_support:
            continue

        tmp[feat] = tmp[feat].astype(int)
        tmp[target] = tmp[target].astype(int)

        grp = tmp.groupby(feat)[target].agg(list)
        for cond, vals in grp.items():
            ctr = Counter(vals)
            pred, hits = ctr.most_common(1)[0]
            support = len(vals)
            prob = hits / support
            if support >= min_support and prob >= 0.18:
                rows.append({
                    "feat": feat,
                    "cond": int(cond),
                    "pred": int(pred),
                    "support": int(support),
                    "hits": int(hits),
                    "prob": float(prob)
                })

    return pd.DataFrame(rows)

def predict_next(train_df, row, target, min_support=8):
    bank = make_rule_bank(train_df, target, min_support=min_support)
    if bank.empty:
        return np.nan, 0.0, "No rule"

    votes = defaultdict(float)
    sources = defaultdict(list)
    feat_order = [c for c in SHIFT_COLS if c != target]

    for feat in feat_order:
        val = row.get(feat, np.nan)
        if pd.isna(val):
            continue
        hit = bank[(bank["feat"] == feat) & (bank["cond"] == int(val))]
        if hit.empty:
            continue

        for _, r in hit.iterrows():
            weight = r["support"] * r["prob"]
            if feat in ["DS", "FD"]:
                weight *= 1.15
            if feat in ["GD", "GL"]:
                weight *= 1.05
            votes[int(r["pred"])] += weight
            sources[int(r["pred"])].append(f"{feat}={int(val)}")

    if not votes:
        return np.nan, 0.0, "No match"

    pred = max(votes, key=votes.get)
    total = sum(votes.values())
    conf = votes[pred] / total if total > 0 else 0.0
    src = "; ".join(sources[pred][:4])
    return pred, conf, src

def symbol(a, p):
    if pd.isna(a) or pd.isna(p):
        return "❌"
    return "✅" if int(a) == int(p) else "❌"

st.title("History Backtest Predictor")

uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
if not uploaded:
    st.stop()

df = load_data(uploaded)
st.write(f"Rows loaded: {len(df)}")

with st.sidebar:
    target = st.selectbox("Target shift", SHIFT_COLS, index=0)
    min_support = st.slider("Min support", 3, 30, 8)
    mode = st.selectbox("Backtest mode", ["Full history", "Last 20", "Custom start"], index=0)

dates = df["DATE"].dt.date.tolist()

if mode == "Full history":
    start_idx = 0
elif mode == "Last 20":
    start_idx = max(0, len(df) - 21)
else:
    start_date = st.date_input("Custom start date", value=dates[max(0, len(dates)-30)])
    start_idx = df.index[df["DATE"].dt.date >= start_date][0] if any(df["DATE"].dt.date >= start_date) else 0

results = []
for i in range(start_idx, len(df) - 1):
    train = df.iloc[:i+1].copy()
    actual_row = df.iloc[i+1]
    pred, conf, src = predict_next(train, actual_row, target, min_support=min_support)
    results.append({
        "TRAIN_TILL": df.iloc[i]["DATE"].date(),
        "PRED_FOR": actual_row["DATE"].date(),
        "ACTUAL": actual_row[target],
        "PRED": pred,
        "CONF": round(conf, 3),
        "RESULT": symbol(actual_row[target], pred),
        "SRC": src
    })

res = pd.DataFrame(results)
st.subheader("Backtest Results")
st.dataframe(res.tail(20), use_container_width=True)

if not res.empty:
    acc = (res["RESULT"] == "✅").mean() * 100
    st.metric("Accuracy", f"{acc:.2f}%")
    st.metric("Total Tested", len(res))
    st.metric("Hits", int((res["RESULT"] == "✅").sum()))
