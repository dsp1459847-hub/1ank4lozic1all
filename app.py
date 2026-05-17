import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import timedelta
from sklearn.metrics import accuracy_score
from collections import Counter, defaultdict

st.set_page_config(page_title="Shift Data Analyzer", layout="wide")

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

def load_excel(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(uploaded_file, sheet_name=xls.sheet_names[0])
    df.columns = [str(c).strip().upper().replace("S. NUMBER", "S_NUMBER").replace(".", "").replace(" ", "_") for c in df.columns]

    rename_map = {}
    for c in df.columns:
        if c in ["S_NUMBER", "S_NUMBER_", "SNUMBER"]:
            rename_map[c] = "S_NUMBER"
        elif c == "DATE":
            rename_map[c] = "DATE"
        elif c in [x.upper() for x in SHIFT_COLS]:
            rename_map[c] = c
    df = df.rename(columns=rename_map)

    if "DATE" not in df.columns:
        raise ValueError("DATE column not found in Excel sheet.")
    if "S_NUMBER" not in df.columns and "S NUMBER" in df.columns:
        df = df.rename(columns={"S NUMBER": "S_NUMBER"})

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    for c in SHIFT_COLS:
        if c in df.columns:
            df[c] = df[c].apply(clean_num)
        else:
            df[c] = np.nan

    df = df.sort_values("DATE").reset_index(drop=True)
    return df

def build_features(df, target_shift, lookbacks=(1, 2, 3, 5, 7, 10)):
    d = df.copy()
    d["TARGET"] = d[target_shift]
    d["DAYOFWEEK"] = d["DATE"].dt.dayofweek
    d["MONTH"] = d["DATE"].dt.month
    d["DAY"] = d["DATE"].dt.day
    d["IS_MONTH_START"] = (d["DAY"] <= 3).astype(int)
    d["IS_MONTH_END"] = (d["DATE"] + pd.offsets.MonthEnd(0) == d["DATE"]).astype(int)

    for c in SHIFT_COLS:
        if c not in d.columns:
            d[c] = np.nan
        d[f"{c}_UNIT"] = d[c] % 10
        d[f"{c}_TENS"] = (d[c] // 10).astype("float")

    for c in SHIFT_COLS:
        for lb in lookbacks:
            d[f"{c}_LAG{lb}"] = d[c].shift(lb)
            d[f"{c}_UNIT_LAG{lb}"] = d[f"{c}_UNIT"].shift(lb)
            d[f"{c}_DIFF{lb}"] = d[c] - d[c].shift(lb)

    for c in SHIFT_COLS:
        d[f"{c}_ROLL3_MEAN"] = d[c].shift(1).rolling(3).mean()
        d[f"{c}_ROLL5_MEAN"] = d[c].shift(1).rolling(5).mean()
        d[f"{c}_ROLL10_MEAN"] = d[c].shift(1).rolling(10).mean()
        d[f"{c}_ROLL3_MODE"] = d[c].shift(1).rolling(3).apply(lambda x: pd.Series(x).mode().iloc[0] if len(pd.Series(x).mode()) else np.nan, raw=False)

    d["TARGET_LAG1"] = d[target_shift].shift(1)
    d["TARGET_LAG2"] = d[target_shift].shift(2)
    d["TARGET_LAG3"] = d[target_shift].shift(3)
    d["TARGET_LAG5"] = d[target_shift].shift(5)
    d["TARGET_LAG7"] = d[target_shift].shift(7)
    d["TARGET_ROLL3_MEAN"] = d[target_shift].shift(1).rolling(3).mean()
    d["TARGET_ROLL5_MEAN"] = d[target_shift].shift(1).rolling(5).mean()
    d["TARGET_ROLL10_MEAN"] = d[target_shift].shift(1).rolling(10).mean()
    d["TARGET_UNIT_LAG1"] = d[f"{target_shift}_UNIT"].shift(1)
    d["TARGET_UNIT_LAG2"] = d[f"{target_shift}_UNIT"].shift(2)
    d["TARGET_UNIT_LAG3"] = d[f"{target_shift}_UNIT"].shift(3)

    feature_cols = [c for c in d.columns if c not in ["DATE", "S_NUMBER", "TARGET"]]
    d = d.dropna(subset=["TARGET"])
    return d, feature_cols

def match_rule_score(train_df, target_shift, feature_shift, min_support=8):
    pairs = defaultdict(Counter)
    vals = train_df[[feature_shift, target_shift]].dropna()
    vals[feature_shift] = vals[feature_shift].astype(int)
    vals[target_shift] = vals[target_shift].astype(int)
    for a, b in zip(vals[feature_shift], vals[target_shift]):
        pairs[a][b] += 1

    rules = []
    for a, cnt in pairs.items():
        total = sum(cnt.values())
        best_val, best_count = cnt.most_common(1)[0]
        prob = best_count / total
        if total >= min_support:
            rules.append({
                "condition_value": a,
                "pred": best_val,
                "support": total,
                "prob": prob
            })
    return pd.DataFrame(rules).sort_values(["prob", "support"], ascending=False)

def generate_prediction_rules(df):
    all_rules = {}
    for target in SHIFT_COLS:
        for feat in SHIFT_COLS:
            if feat == target:
                continue
            rule_df = match_rule_score(df, target, feat)
            if not rule_df.empty:
                all_rules[(feat, target)] = rule_df
    return all_rules

def pick_best_threshold(df, target_shift):
    candidates = [0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30, 0.35, 0.40]
    results = []
    for th in candidates:
        preds = []
        actuals = []
        for i in range(20, len(df)-1):
            tr = df.iloc[:i].copy()
            row = df.iloc[i]
            next_row = df.iloc[i+1]
            best_pred = None
            best_score = -1
            for feat in SHIFT_COLS:
                if feat == target_shift:
                    continue
                if pd.isna(row.get(feat)):
                    continue
                rules = match_rule_score(tr, target_shift, feat, min_support=8)
                if rules.empty:
                    continue
                hit = rules[rules["condition_value"] == int(row[feat])]
                if hit.empty:
                    continue
                hit = hit.iloc[0]
                if hit["prob"] >= th and hit["prob"] > best_score:
                    best_score = hit["prob"]
                    best_pred = int(hit["pred"])
            if best_pred is not None and not pd.isna(next_row[target_shift]):
                preds.append(best_pred)
                actuals.append(int(next_row[target_shift]))
        acc = accuracy_score(actuals, preds) if preds else 0.0
        results.append((th, acc, len(preds)))
    res = pd.DataFrame(results, columns=["threshold", "accuracy", "pred_count"])
    best = res.sort_values(["accuracy", "pred_count"], ascending=False).iloc[0]
    return float(best["threshold"]), res

def rolling_backtest(df, target_shift, window_days=10):
    df = df.sort_values("DATE").reset_index(drop=True)
    rows = []
    for i in range(window_days, len(df)-1):
        train = df.iloc[:i].copy()
        test_row = df.iloc[i]
        next_actual = df.iloc[i+1][target_shift]
        best_pred = np.nan
        best_prob = -1
        for feat in SHIFT_COLS:
            if feat == target_shift:
                continue
            if pd.isna(test_row[feat]) or pd.isna(next_actual):
                continue
            rules = match_rule_score(train, target_shift, feat, min_support=8)
            if rules.empty:
                continue
            hit = rules[rules["condition_value"] == int(test_row[feat])]
            if hit.empty:
                continue
            hit = hit.iloc[0]
            if hit["prob"] > best_prob:
                best_prob = hit["prob"]
                best_pred = int(hit["pred"])
        rows.append({
            "date": df.iloc[i+1]["DATE"],
            "actual": next_actual,
            "pred": best_pred,
            "hit": int(not pd.isna(best_pred) and int(best_pred) == int(next_actual)) if not pd.isna(next_actual) else 0
        })
    out = pd.DataFrame(rows)
    return out

def last_n_history(df, n=20):
    return df.tail(n).copy()

def status_mark(actual, pred):
    if pd.isna(actual) or pd.isna(pred):
        return "—"
    return "✅" if int(actual) == int(pred) else "❌"

st.title("Shift Data Analyzer & Predictor")

uploaded = st.file_uploader("Excel file upload करें", type=["xlsx"])

if uploaded:
    try:
        df = load_excel(uploaded)
        st.success(f"Loaded rows: {len(df)}")

        st.subheader("Raw History")
        st.dataframe(df, use_container_width=True)

        st.subheader("Analysis Settings")
        target_shift = st.selectbox("Target shift चुनें", SHIFT_COLS, index=0)

        cleaned = df.copy()
        for c in SHIFT_COLS:
            cleaned[f"{c}_UNIT"] = cleaned[c] % 10

        threshold, th_table = pick_best_threshold(cleaned, target_shift)
        st.write(f"Auto-selected threshold: {threshold:.2f}")
        st.dataframe(th_table, use_container_width=True)

        bt = rolling_backtest(cleaned, target_shift, window_days=10)
        st.subheader("Backtest Result")
        if not bt.empty:
            acc = bt["hit"].mean()
            st.write(f"Backtest accuracy: {acc:.4f}")
            st.dataframe(bt.tail(30), use_container_width=True)
        else:
            st.write("Not enough data for backtest.")

        st.subheader("Last 20 Days History with Result Mark")
        hist = last_n_history(cleaned, 20)
        hist = hist[["DATE"] + [c for c in SHIFT_COLS if c in hist.columns]].copy()

        rules = {}
        for feat in SHIFT_COLS:
            if feat != target_shift:
                r = match_rule_score(cleaned.iloc[:-1], target_shift, feat, min_support=8)
                if not r.empty:
                    rules[feat] = r

        preds = []
        for _, row in hist.iterrows():
            pred = np.nan
            best_prob = -1
            matched_from = ""
            for feat in SHIFT_COLS:
                if feat == target_shift:
                    continue
                if feat not in row or pd.isna(row[feat]):
                    continue
                if feat in rules:
                    hit = rules[feat][rules[feat]["condition_value"] == int(row[feat])]
                    if not hit.empty:
                        hit = hit.iloc[0]
                        if hit["prob"] >= threshold and hit["prob"] > best_prob:
                            pred = int(hit["pred"])
                            best_prob = float(hit["prob"])
                            matched_from = feat
            preds.append((pred, best_prob, matched_from))

        hist["PRED"] = [x[0] for x in preds]
        hist["CONF"] = [round(x[1], 3) if x[1] >= 0 else np.nan for x in preds]
        hist["FROM"] = [x[2] for x in preds]
        if target_shift in df.columns:
            hist["ACTUAL"] = hist[target_shift]
            hist["RESULT"] = [status_mark(a, p) for a, p in zip(hist["ACTUAL"], hist["PRED"])]
        st.dataframe(hist, use_container_width=True)

        st.subheader("Latest Prediction")
        latest = cleaned.iloc[-1]
        pred = np.nan
        best_prob = -1
        best_from = ""
        for feat in SHIFT_COLS:
            if feat == target_shift:
                continue
            if pd.isna(latest[feat]):
                continue
            if feat in rules:
                hit = rules[feat][rules[feat]["condition_value"] == int(latest[feat])]
                if not hit.empty:
                    hit = hit.iloc[0]
                    if hit["prob"] >= threshold and hit["prob"] > best_prob:
                        pred = int(hit["pred"])
                        best_prob = float(hit["prob"])
                        best_from = feat

        c1, c2, c3 = st.columns(3)
        c1.metric("Target Shift", target_shift)
        c2.metric("Predicted Number", "NA" if pd.isna(pred) else int(pred))
        c3.metric("Confidence", "NA" if best_prob < 0 else f"{best_prob:.3f}")
        st.write(f"Rule source shift: {best_from if best_from else 'None'}")

        st.subheader("Shift Relations")
        rel_rows = []
        for feat in SHIFT_COLS:
            if feat == target_shift:
                continue
            r = match_rule_score(cleaned, target_shift, feat, min_support=8)
            if not r.empty:
                top = r.iloc[0]
                rel_rows.append({
                    "FROM": feat,
                    "TO": target_shift,
                    "COND_VALUE": int(top["condition_value"]),
                    "PRED": int(top["pred"]),
                    "SUPPORT": int(top["support"]),
                    "PROB": round(float(top["prob"]), 4)
                })
        rel_df = pd.DataFrame(rel_rows).sort_values(["PROB", "SUPPORT"], ascending=False) if rel_rows else pd.DataFrame()
        st.dataframe(rel_df, use_container_width=True)

        st.subheader("Monthly Accuracy")
        if not bt.empty:
            bt2 = bt.copy()
            bt2["month"] = bt2["date"].dt.to_period("M").astype(str)
            monthly = bt2.groupby("month")["hit"].mean().reset_index(name="accuracy")
            st.dataframe(monthly, use_container_width=True)

        st.subheader("How to use")
        st.write("1. Select target shift.")
        st.write("2. Upload your Excel.")
        st.write("3. Auto threshold will be chosen from history.")
        st.write("4. History will show tick/cross in RESULT column.")

    except Exception as e:
        st.error(str(e))
else:
    st.info("Excel file upload करें. आपकी sheet के हिसाब से app built है.")
