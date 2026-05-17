import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="Shift Analyzer", layout="wide")

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
        if c == "DATE":
            rename_map[c] = "DATE"
        if c in SHIFT_COLS:
            rename_map[c] = c
    df = df.rename(columns=rename_map)

    if "DATE" not in df.columns:
        raise ValueError("DATE column not found.")
    if "S_NUMBER" not in df.columns:
        for alt in ["S_NUMBER", "SNUMBER", "S NUMBER"]:
            if alt in df.columns:
                df = df.rename(columns={alt: "S_NUMBER"})
                break

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    for c in SHIFT_COLS:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = df[c].apply(clean_num)

    df = df.dropna(subset=["DATE"]).sort_values("DATE").reset_index(drop=True)
    return df

def add_units(df):
    out = df.copy()
    for c in SHIFT_COLS:
        out[f"{c}_UNIT"] = out[c] % 10
    return out

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
            rows.append({
                "cond": int(cond_val),
                "pred": int(pred),
                "support": int(total),
                "prob": float(sup / total)
            })
    if not rows:
        return pd.DataFrame(columns=["cond", "pred", "support", "prob"])
    return pd.DataFrame(rows).sort_values(["prob", "support"], ascending=False).reset_index(drop=True)

def auto_threshold(df, target_shift):
    candidates = [0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.28, 0.30, 0.35, 0.40]
    results = []
    base = df.copy().reset_index(drop=True)

    for th in candidates:
        preds, actuals = [], []
        for i in range(30, len(base) - 1):
            train = base.iloc[:i].copy()
            row = base.iloc[i]
            actual = base.iloc[i + 1][target_shift]
            best_pred = np.nan
            best_prob = -1.0

            for feat in SHIFT_COLS:
                if feat == target_shift:
                    continue
                if pd.isna(row[feat]):
                    continue
                rules = shift_rules(train, target_shift, feat, min_support=8)
                if rules.empty:
                    continue
                hit = rules[rules["cond"] == int(row[feat])]
                if hit.empty:
                    continue
                hit = hit.iloc[0]
                if hit["prob"] >= th and hit["prob"] > best_prob:
                    best_prob = float(hit["prob"])
                    best_pred = int(hit["pred"])

            if not pd.isna(best_pred) and not pd.isna(actual):
                preds.append(int(best_pred))
                actuals.append(int(actual))

        acc = accuracy_score(actuals, preds) if preds else 0.0
        results.append({"threshold": th, "accuracy": acc, "pred_count": len(preds)})

    res = pd.DataFrame(results)
    best = res.sort_values(["accuracy", "pred_count"], ascending=False).iloc[0]
    return float(best["threshold"]), res

def rolling_backtest(df, target_shift, threshold):
    base = df.copy().reset_index(drop=True)
    rows = []

    for i in range(30, len(base) - 1):
        train = base.iloc[:i].copy()
        row = base.iloc[i]
        actual = base.iloc[i + 1][target_shift]

        best_pred = np.nan
        best_prob = -1.0
        best_from = ""

        for feat in SHIFT_COLS:
            if feat == target_shift:
                continue
            if pd.isna(row[feat]):
                continue

            rules = shift_rules(train, target_shift, feat, min_support=8)
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

        rows.append({
            "DATE": base.iloc[i + 1]["DATE"],
            "ACTUAL": actual,
            "PRED": best_pred,
            "FROM": best_from,
            "CONF": best_prob if best_prob >= 0 else np.nan,
            "HIT": int((not pd.isna(best_pred)) and (not pd.isna(actual)) and int(best_pred) == int(actual))
        })

    return pd.DataFrame(rows)

def predict_latest(df, target_shift, threshold):
    base = df.copy().reset_index(drop=True)
    if len(base) < 2:
        return np.nan, np.nan, ""

    latest = base.iloc[-1]
    train = base.iloc[:-1].copy()

    best_pred = np.nan
    best_prob = -1.0
    best_from = ""

    for feat in SHIFT_COLS:
        if feat == target_shift:
            continue
        if pd.isna(latest[feat]):
            continue

        rules = shift_rules(train, target_shift, feat, min_support=8)
        if rules.empty:
            continue

        hit = rules[rules["cond"] == int(latest[feat])]
        if hit.empty:
            continue

        hit = hit.iloc[0]
        if hit["prob"] >= threshold and hit["prob"] > best_prob:
            best_prob = float(hit["prob"])
            best_pred = int(hit["pred"])
            best_from = feat

    return best_pred, best_prob, best_from

def make_history_table(df, target_shift, threshold):
    base = df.copy().reset_index(drop=True)
    rows = []

    for i in range(30, len(base)):
        train = base.iloc[:i].copy()
        cur = base.iloc[i]
        actual = cur[target_shift]

        pred = np.nan
        prob = -1.0
        from_shift = ""

        for feat in SHIFT_COLS:
            if feat == target_shift:
                continue
            if pd.isna(cur[feat]):
                continue

            rules = shift_rules(train, target_shift, feat, min_support=8)
            if rules.empty:
                continue

            hit = rules[rules["cond"] == int(cur[feat])]
            if hit.empty:
                continue

            hit = hit.iloc[0]
            if hit["prob"] >= threshold and hit["prob"] > prob:
                prob = float(hit["prob"])
                pred = int(hit["pred"])
                from_shift = feat

        rows.append({
            "DATE": cur["DATE"],
            "ACTUAL": actual,
            "PRED": pred,
            "FROM": from_shift,
            "CONF": prob if prob >= 0 else np.nan,
            "RESULT": "✅" if (not pd.isna(pred) and not pd.isna(actual) and int(pred) == int(actual)) else "❌"
        })

    return pd.DataFrame(rows)

def monthly_accuracy(history_df):
    if history_df.empty:
        return pd.DataFrame(columns=["MONTH", "ACCURACY", "TOTAL"])
    x = history_df.copy()
    x["MONTH"] = x["DATE"].dt.to_period("M").astype(str)
    out = x.groupby("MONTH").agg(ACCURACY=("RESULT", lambda s: (s == "✅").mean()), TOTAL=("RESULT", "count")).reset_index()
    return out

def last_n_accuracy(history_df, n):
    if history_df.empty:
        return 0.0
    x = history_df.tail(n)
    if x.empty:
        return 0.0
    return float((x["RESULT"] == "✅").mean())

st.title("Shift Data Analyzer & Prediction App")

uploaded = st.file_uploader("Excel file upload करें", type=["xlsx"])

if uploaded is None:
    st.info("0DSP0.xlsx upload करें.")
    st.stop()

try:
    df = load_excel(uploaded)
    df = add_units(df)

    st.success(f"File loaded: {len(df)} rows")

    with st.sidebar:
        st.header("Settings")
        target_shift = st.selectbox("Target shift", SHIFT_COLS, index=0)
        min_rows = st.slider("Backtest start row", 10, 100, 30)
        show_raw = st.toggle("Show raw data", value=True)

    if show_raw:
        st.subheader("Raw Data")
        st.dataframe(df, use_container_width=True)

    st.subheader("Auto Threshold Selection")
    th, th_table = auto_threshold(df, target_shift)
    st.write(f"Selected threshold: **{th:.2f}**")
    st.dataframe(th_table, use_container_width=True)

    st.subheader("Rolling Backtest")
    bt = rolling_backtest(df, target_shift, th)

    if bt.empty:
        st.warning("Backtest ke liye data kam hai.")
    else:
        st.metric("Overall Backtest Accuracy", f"{bt['HIT'].mean():.4f}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Last 10 Days Accuracy", f"{last_n_accuracy(bt, 10):.4f}")
        c2.metric("Last 20 Days Accuracy", f"{last_n_accuracy(bt, 20):.4f}")
        c3.metric("Last 60 Days Accuracy", f"{last_n_accuracy(bt, 60):.4f}")

        st.dataframe(bt.tail(100), use_container_width=True)

        m = monthly_accuracy(bt)
        st.subheader("Monthly Accuracy")
        st.dataframe(m, use_container_width=True)

        st.subheader("Backtest History with Tick/Cross")
        view = bt.copy()
        st.dataframe(view, use_container_width=True)

        csv = view.to_csv(index=False).encode("utf-8")
        st.download_button("Download backtest CSV", csv, "backtest_history.csv", "text/csv")

    st.subheader("Latest Prediction")
    pred, conf, frm = predict_latest(df, target_shift, th)

    c1, c2, c3 = st.columns(3)
    c1.metric("Target Shift", target_shift)
    c2.metric("Predicted Number", "NA" if pd.isna(pred) else int(pred))
    c3.metric("Confidence", "NA" if pd.isna(conf) else f"{conf:.3f}")
    st.write(f"Source shift: **{frm if frm else 'None'}**")

    st.subheader("History with Result Mark")
    hist = make_history_table(df, target_shift, th)
    st.dataframe(hist.tail(20), use_container_width=True)

    st.subheader("Shift-wise Rules")
    rule_rows = []
    train_all = df.iloc[:-1].copy() if len(df) > 1 else df.copy()
    for feat in SHIFT_COLS:
        if feat == target_shift:
            continue
        r = shift_rules(train_all, target_shift, feat, min_support=8)
        if not r.empty:
            top = r.iloc[0]
            rule_rows.append({
                "FROM": feat,
                "TO": target_shift,
                "COND": int(top["cond"]),
                "PRED": int(top["pred"]),
                "SUPPORT": int(top["support"]),
                "PROB": round(float(top["prob"]), 4)
            })
    rules_df = pd.DataFrame(rule_rows)
    st.dataframe(rules_df, use_container_width=True)

    st.subheader("How to use")
    st.write("1. Upload Excel.")
    st.write("2. Select target shift.")
    st.write("3. App auto-selects threshold from history.")
    st.write("4. Backtest accuracy, monthly accuracy, and tick/cross history show on same page.")

except Exception as e:
    st.error(f"Error: {e}")
