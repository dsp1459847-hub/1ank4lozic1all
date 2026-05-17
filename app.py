import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

st.set_page_config(page_title="Strict History Rule Miner", layout="wide")

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
def load_excel(uploaded_file):
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

def feature_rows(df, idx, target):
    row = df.iloc[idx]
    feats = []
    if idx - 1 >= 0:
        prev = df.iloc[idx - 1]
        prev2 = df.iloc[idx - 2] if idx - 2 >= 0 else None

        for c in SHIFT_COLS:
            if c != target and pd.notna(prev.get(c)):
                feats.append(("L1_" + c, int(prev[c])))
            if prev2 is not None and c != target and pd.notna(prev2.get(c)):
                feats.append(("L2_" + c, int(prev2[c])))

        if pd.notna(prev.get("DS")) and pd.notna(prev.get("FD")):
            feats.append(("P_DS_FD", f"{int(prev['DS'])}_{int(prev['FD'])}"))
        if pd.notna(prev.get("GD")) and pd.notna(prev.get("GL")):
            feats.append(("P_GD_GL", f"{int(prev['GD'])}_{int(prev['GL'])}"))
        if pd.notna(prev.get("DB")) and pd.notna(prev.get("SG")):
            feats.append(("P_DB_SG", f"{int(prev['DB'])}_{int(prev['SG'])}"))

        d = row["DATE"]
        feats.append(("WEEKDAY", int(d.weekday())))
        feats.append(("MONTHDAY", int(d.day)))
    return feats

def build_rule_bank(train_df, target, min_support=6):
    bank = defaultdict(lambda: Counter())
    meta = defaultdict(lambda: {"support": 0, "hits": 0})

    for i in range(2, len(train_df)):
        row_feats = feature_rows(train_df, i, target)
        actual = train_df.iloc[i][target]
        if pd.isna(actual):
            continue
        actual = int(actual)
        for k, v in row_feats:
            bank[(k, v)][actual] += 1
            meta[(k, v)]["support"] += 1

    rules = []
    for key, ctr in bank.items():
        support = sum(ctr.values())
        if support < min_support:
            continue
        pred, hits = ctr.most_common(1)[0]
        prob = hits / support
        if prob >= 0.20:
            rules.append({
                "feature": key[0],
                "value": key[1],
                "pred": int(pred),
                "support": int(support),
                "hits": int(hits),
                "prob": float(prob)
            })
    return pd.DataFrame(rules)

def predict_row(train_df, row, target, rules_df):
    votes = defaultdict(float)
    used = []
    if rules_df.empty:
        return np.nan, 0.0, "No rules"

    feats = []
    if len(train_df) >= 2:
        prev = train_df.iloc[-1]
        prev2 = train_df.iloc[-2] if len(train_df) >= 2 else None

        for c in SHIFT_COLS:
            if c != target and pd.notna(prev.get(c)):
                feats.append(("L1_" + c, int(prev[c])))
            if prev2 is not None and c != target and pd.notna(prev2.get(c)):
                feats.append(("L2_" + c, int(prev2[c])))

        if pd.notna(prev.get("DS")) and pd.notna(prev.get("FD")):
            feats.append(("P_DS_FD", f"{int(prev['DS'])}_{int(prev['FD'])}"))
        if pd.notna(prev.get("GD")) and pd.notna(prev.get("GL")):
            feats.append(("P_GD_GL", f"{int(prev['GD'])}_{int(prev['GL'])}"))
        if pd.notna(prev.get("DB")) and pd.notna(prev.get("SG")):
            feats.append(("P_DB_SG", f"{int(prev['DB'])}_{int(prev['SG'])}"))

    feats.append(("WEEKDAY", int(row["DATE"].weekday())))
    feats.append(("MONTHDAY", int(row["DATE"].day)))

    for f, v in feats:
        hit = rules_df[(rules_df["feature"] == f) & (rules_df["value"] == v)]
        if hit.empty:
            continue
        for _, r in hit.iterrows():
            w = r["support"] * r["prob"]
            if f.startswith("L1_"):
                w *= 1.3
            elif f.startswith("L2_"):
                w *= 1.1
            elif f.startswith("P_"):
                w *= 1.4
            elif f in ["WEEKDAY", "MONTHDAY"]:
                w *= 1.05
            votes[int(r["pred"])] += w
            used.append(f"{f}={v}->{int(r['pred'])}")

    if not votes:
        return np.nan, 0.0, "No match"

    pred = max(votes, key=votes.get)
    total = sum(votes.values())
    conf = votes[pred] / total if total > 0 else 0.0
    return pred, float(conf), "; ".join(used[:5])

def sym(a, p):
    if pd.isna(a) or pd.isna(p):
        return "❌"
    return "✅" if int(a) == int(p) else "❌"

st.title("Strict History Rule Miner")

uploaded = st.file_uploader("Upload Excel", type=["xlsx"])
if not uploaded:
    st.stop()

df = load_excel(uploaded)
st.write(f"Rows loaded: {len(df)}")

with st.sidebar:
    target = st.selectbox("Target shift", SHIFT_COLS, index=0)
    min_support = st.slider("Min support", 2, 40, 6)
    prob_cut = st.slider("Min rule probability", 0.05, 0.60, 0.20, 0.01)
    history_days = st.slider("Training window days", 30, 3650, 365)

results = []
rule_stats = []
start_idx = max(2, len(df) - 21)

for i in range(start_idx, len(df) - 1):
    cutoff = df.iloc[:i+1].copy()
    if history_days < len(cutoff):
        cutoff = cutoff.iloc[-history_days:].copy()

    rules = build_rule_bank(cutoff, target, min_support=min_support)
    if not rules.empty:
        rules = rules[rules["prob"] >= prob_cut].copy()

    actual_row = df.iloc[i+1]
    pred, conf, src = predict_row(cutoff, actual_row, target, rules)

    results.append({
        "TRAIN_TILL": df.iloc[i]["DATE"].date(),
        "PRED_FOR": actual_row["DATE"].date(),
        "ACTUAL": actual_row[target],
        "PRED": pred,
        "CONF": round(conf, 3),
        "RESULT": sym(actual_row[target], pred),
        "SRC": src
    })

    if not rules.empty:
        rule_stats.append(rules)

res = pd.DataFrame(results)
st.subheader("Last 20 Backtest")
st.dataframe(res.tail(20), use_container_width=True)

if not res.empty:
    acc = (res["RESULT"] == "✅").mean() * 100
    st.metric("Backtest Accuracy", f"{acc:.2f}%")
    st.metric("Total Tested", len(res))
    st.metric("Hits", int((res["RESULT"] == "✅").sum()))

if rule_stats:
    all_rules = pd.concat(rule_stats, ignore_index=True)
    top_rules = all_rules.groupby(["feature", "value", "pred"], as_index=False).agg(
        support=("support", "sum"),
        hits=("hits", "sum"),
        prob=("prob", "mean")
    ).sort_values(["prob", "support"], ascending=False)
    st.subheader("Top Rules")
    st.dataframe(top_rules.head(50), use_container_width=True)
