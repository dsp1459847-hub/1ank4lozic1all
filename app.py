import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter, defaultdict

st.set_page_config(page_title="Excel History Predictor", layout="wide")

SHIFT_COLS = ["DS", "FD", "GD", "GL", "DB", "SG", "ZA"]

def to_num(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().upper()
    if s in ["XX", "X", "", "NAN", "NONE", "-"]:
        return np.nan
    try:
        return int(float(s))
    except:
        return np.nan

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df.columns = [str(c).strip().upper().replace(".", "").replace(" ", "_") for c in df.columns]
    if "DATE" not in df.columns:
        raise ValueError("DATE column not found")

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    for c in SHIFT_COLS:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = df[c].apply(to_num)

    df = df.dropna(subset=["DATE"]).sort_values("DATE").reset_index(drop=True)
    return df

def build_features(df, idx, target):
    row = df.iloc[idx]
    feats = []

    if idx - 1 >= 0:
        prev = df.iloc[idx - 1]
        for c in SHIFT_COLS:
            if c != target and pd.notna(prev[c]):
                feats.append((f"L1_{c}", int(prev[c])))

    if idx - 2 >= 0:
        prev2 = df.iloc[idx - 2]
        for c in SHIFT_COLS:
            if c != target and pd.notna(prev2[c]):
                feats.append((f"L2_{c}", int(prev2[c])))

    if idx - 7 >= 0:
        prev7 = df.iloc[idx - 7]
        if pd.notna(prev7[target]):
            feats.append(("L7_SELF", int(prev7[target])))

    feats.append(("WEEKDAY", int(row["DATE"].weekday())))
    feats.append(("MONTHDAY", int(row["DATE"].day)))

    return feats

def train_rule_bank(train_df, target, min_support=5):
    rules = defaultdict(Counter)

    for i in range(2, len(train_df)):
        actual = train_df.iloc[i][target]
        if pd.isna(actual):
            continue
        actual = int(actual)
        feats = build_features(train_df, i, target)
        for f in feats:
            rules[f][actual] += 1

    rows = []
    for key, ctr in rules.items():
        support = sum(ctr.values())
        if support < min_support:
            continue
        pred, hit = ctr.most_common(1)[0]
        prob = hit / support
        rows.append({
            "feature": key[0],
            "value": key[1],
            "pred": int(pred),
            "support": int(support),
            "hits": int(hit),
            "prob": round(prob, 4)
        })

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["prob", "support"], ascending=False).reset_index(drop=True)
    return out

def predict_with_rules(train_df, current_row, target, rules_df):
    votes = defaultdict(float)
    feats = []

    if len(train_df) >= 1:
        prev = train_df.iloc[-1]
        for c in SHIFT_COLS:
            if c != target and pd.notna(prev[c]):
                feats.append((f"L1_{c}", int(prev[c])))

    if len(train_df) >= 2:
        prev2 = train_df.iloc[-2]
        for c in SHIFT_COLS:
            if c != target and pd.notna(prev2[c]):
                feats.append((f"L2_{c}", int(prev2[c])))

    if len(train_df) >= 7:
        prev7 = train_df.iloc[-7]
        if pd.notna(prev7[target]):
            feats.append(("L7_SELF", int(prev7[target])))

    feats.append(("WEEKDAY", int(current_row["DATE"].weekday())))
    feats.append(("MONTHDAY", int(current_row["DATE"].day)))

    used = []
    for f, v in feats:
        hit = rules_df[(rules_df["feature"] == f) & (rules_df["value"] == v)]
        if hit.empty:
            continue
        for _, r in hit.iterrows():
            w = r["support"] * r["prob"]
            if f.startswith("L1_"):
                w *= 1.4
            elif f.startswith("L2_"):
                w *= 1.2
            elif f == "L7_SELF":
                w *= 1.6
            elif f in ["WEEKDAY", "MONTHDAY"]:
                w *= 1.05
            votes[int(r["pred"])] += w
            used.append(f"{f}={v} -> {int(r['pred'])}")

    if not votes:
        return [], np.nan, 0.0, "No matching rule"

    ranked = sorted(votes.items(), key=lambda x: x[1], reverse=True)
    total = sum(votes.values())
    top1 = ranked[0][0]
    conf = ranked[0][1] / total if total > 0 else 0.0
    top10 = [n for n, _ in ranked[:10]]
    return top10, int(top1), round(conf, 4), "; ".join(used[:8])

def backtest(df, target, window=180, min_support=5):
    rows = []
    start = max(10, len(df) - window - 1)

    for i in range(start, len(df) - 1):
        train = df.iloc[:i+1].copy()
        if len(train) > window:
            train = train.iloc[-window:].copy()

        rules = train_rule_bank(train, target, min_support=min_support)
        current_row = df.iloc[i+1]
        top10, top1, conf, src = predict_with_rules(train, current_row, target, rules)
        actual = current_row[target]

        hit1 = int(pd.notna(actual) and top1 == int(actual))
        hit10 = int(pd.notna(actual) and int(actual) in top10)

        rows.append({
            "train_till": train.iloc[-1]["DATE"].date(),
            "predict_for": current_row["DATE"].date(),
            "actual": None if pd.isna(actual) else int(actual),
            "top1": top1,
            "top10": top10,
            "conf": conf,
            "hit_top1": hit1,
            "hit_top10": hit10,
            "source": src
        })

    res = pd.DataFrame(rows)
    return res

st.title("Excel History Predictor")

uploaded = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded is None:
    st.stop()

df = load_data(uploaded)

with st.sidebar:
    target = st.selectbox("Target shift", SHIFT_COLS, index=0)
    window = st.slider("Rolling history window", 30, 1000, 180)
    min_support = st.slider("Min rule support", 2, 30, 5)

st.write("Loaded rows:", len(df))
st.write(df.head(10))

rules = train_rule_bank(df, target, min_support=min_support)
st.subheader(f"Top rules for {target}")
st.dataframe(rules.head(50), use_container_width=True)

bt = backtest(df, target, window=window, min_support=min_support)
st.subheader("Backtest results")
st.dataframe(bt.tail(30), use_container_width=True)

if not bt.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Top1 Accuracy", f"{bt['hit_top1'].mean()*100:.2f}%")
    col2.metric("Top10 Hit Rate", f"{bt['hit_top10'].mean()*100:.2f}%")
    col3.metric("Tests", f"{len(bt)}")

st.subheader("Next day prediction")
latest_train = df.copy()
if len(latest_train) > window:
    latest_train = latest_train.iloc[-window:].copy()

latest_rules = train_rule_bank(latest_train, target, min_support=min_support)
next_date = latest_train.iloc[-1]["DATE"] + pd.Timedelta(days=1)
next_row = pd.DataFrame([{"DATE": next_date}])
top10, top1, conf, src = predict_with_rules(latest_train, next_row.iloc[0], target, latest_rules)

st.write("Top 1:", top1)
st.write("Confidence:", conf)
st.write("Top 10:", top10)
st.write("Rule source:", src)

if top10:
    st.success(f"Best prediction for {target}: {top1}")
    st.info(f"Top 10 candidates: {top10}")
