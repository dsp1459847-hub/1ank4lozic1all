import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from sklearn.metrics import accuracy_score
from datetime import date

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
    if "S_NUMBER" not in df.columns and "S NUMBER" in df.columns:
        df = df.rename(columns={"S NUMBER": "S_NUMBER"})

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

def predict_row(train_df, row, target_shift, threshold):
    best_pred = np.nan
    best_prob = -1.0
    best_from = ""

    for feat in SHIFT_COLS:
        if feat == target_shift:
            continue
        if pd.isna(row[feat]):
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

def rolling_backtest(df, target_shift, threshold):
    base = df.copy().reset_index(drop=True)
    rows = []
    for i in range(30, len(base) - 1):
        train = base.iloc[:i].copy()
        row = base.iloc[i]
        actual = base.iloc[i + 1][target_shift]
        pred, prob, frm = predict_row(train, row, target_shift, threshold)
        rows.append({
            "TRAIN_UPTO_DATE": base.iloc[i]["DATE"],
            "PRED_FOR_DATE": base.iloc[i + 1]["DATE"],
            "ACTUAL": actual,
            "PRED": pred,
            "FROM": frm,
            "CONF": prob if prob >= 0 else np.nan,
            "HIT": int((not pd.isna(pred)) and (not pd.isna(actual)) and int(pred) == int(actual))
        })
    return pd.DataFrame(rows)

def monthly_accuracy(history_df):
    if history_df.empty:
        return pd.DataFrame(columns=["MONTH", "ACCURACY", "TOTAL"])
    x = history_df.copy()
    x["MONTH"] = x["PRED_FOR_DATE"].dt.to_period("M").astype(str)
    out = x.groupby("MONTH").agg(
        ACCURACY=("HIT", "mean"),
        TOTAL=("HIT", "count")
    ).reset_index()
    return out

def status_mark(actual, pred):
    if pd.isna(actual) or pd.isna(pred):
        return "—"
    return "✅" if int(actual) == int(pred) else "❌"

def history_table(df, target_shift, threshold, upto_date=None, limit=20):
    base = df.copy().reset_index(drop=True)
    rows = []
    for i in range(30, len(base)):
        pred_date = base.iloc[i]["DATE"]
        if upto_date is not None and pred_date.date() > upto_date:
            continue
        train = base.iloc[:i].copy()
        row = base.iloc[i]
        actual = row[target_shift]
        pred, prob, frm = predict_row(train, row, target_shift, threshold)
        rows.append({
            "DATE": pred_date,
            "ACTUAL": actual,
            "PRED": pred,
            "FROM": frm,
            "CONF": prob if prob >= 0 else np.nan,
            "RESULT": status_mark(actual, pred)
        })
    return pd.DataFrame(rows).tail(limit)

st.title("Shift Data Analyzer & Predictor")

uploaded = st.file_uploader("Excel file upload करें", type=["xlsx"])

if not uploaded:
    st.info("Excel file upload करें.")
    st.stop()

try:
    df = load_excel(uploaded)
    df = add_units(df)

    st.success(f"Loaded rows: {len(df)}")

    with st.sidebar:
        st.header("Settings")
        target_shift = st.selectbox("Target shift", SHIFT_COLS, index=0)
        mode = st.selectbox("Mode", ["Latest available date", "Select practice date", "Select date range"], index=0)

    st.subheader("Raw History")
    st.dataframe(df, use_container_width=True)

    st.subheader("Auto Threshold Selection")
    threshold, threshold_table = auto_threshold(df, target_shift)
    st.write(f"Selected threshold: **{threshold:.2f}**")
    st.dataframe(threshold_table, use_container_width=True)

    valid_dates = sorted(df["DATE"].dropna().dt.date.unique().tolist())
    practice_date = None
    start_date = None
    end_date = None

    if mode == "Select practice date":
        practice_date = st.date_input(
            "Select date",
            value=valid_dates[-1],
            min_value=valid_dates[0],
            max_value=valid_dates[-1],
            key="practice_date"
        )

    elif mode == "Select date range":
        start_date, end_date = st.date_input(
            "Select date range",
            value=(valid_dates[max(0, len(valid_dates) - 20)], valid_dates[-1]),
            min_value=valid_dates[0],
            max_value=valid_dates[-1],
            key="date_range"
        )

    st.subheader("Backtest Result")
    bt = rolling_backtest(df, target_shift, threshold)
    if bt.empty:
        st.warning("Backtest के लिए data कम है.")
    else:
        st.metric("Overall Accuracy", f"{bt['HIT'].mean():.4f}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Last 10 Days Accuracy", f"{bt.tail(10)['HIT'].mean():.4f}")
        c2.metric("Last 20 Days Accuracy", f"{bt.tail(20)['HIT'].mean():.4f}")
        c3.metric("Last 60 Days Accuracy", f"{bt.tail(60)['HIT'].mean():.4f}")
        st.dataframe(bt.tail(100), use_container_width=True)

        m = monthly_accuracy(bt)
        st.subheader("Monthly Accuracy")
        st.dataframe(m, use_container_width=True)

        st.download_button(
            "Download Backtest CSV",
            bt.to_csv(index=False).encode("utf-8"),
            "backtest.csv",
            "text/csv"
        )

    st.subheader("Selected Date / Range Practice")

    if mode == "Latest available date":
        latest_idx = len(df) - 1
        train_df = df.iloc[:latest_idx].copy()
        row = df.iloc[latest_idx]
        pred, conf, frm = predict_row(train_df, row, target_shift, threshold)

        c1, c2, c3 = st.columns(3)
        c1.metric("Selected Date", str(row["DATE"].date()))
        c2.metric("Prediction For", f"{target_shift} on selected date")
        c3.metric("Predicted Number", "NA" if pd.isna(pred) else int(pred))
        st.write(f"Source shift: **{frm if frm else 'None'}**")
        st.write(f"यह prediction **selected date** का है, next day का नहीं.")

    elif mode == "Select practice date":
        sel = df[df["DATE"].dt.date == practice_date]
        if sel.empty:
            st.warning("Selected date data नहीं मिला.")
        else:
            idx = sel.index[0]
            train_df = df.iloc[:idx].copy()
            row = df.iloc[idx]
            pred, conf, frm = predict_row(train_df, row, target_shift, threshold)

            c1, c2, c3 = st.columns(3)
            c1.metric("Selected Date", str(practice_date))
            c2.metric("Prediction For", f"{target_shift} on selected date")
            c3.metric("Predicted Number", "NA" if pd.isna(pred) else int(pred))
            st.write(f"Source shift: **{frm if frm else 'None'}**")
            st.write(f"यह prediction **selected date** का है.")

            hist = history_table(df, target_shift, threshold, upto_date=practice_date, limit=20)
            st.subheader("History up to Selected Date")
            if not hist.empty:
                st.dataframe(hist, use_container_width=True)
            else:
                st.warning("No practice history available.")

    else:
        if isinstance(start_date, tuple) or start_date is None or end_date is None:
            st.warning("Valid date range चुनें.")
        else:
            if start_date > end_date:
                st.warning("Start date end date से पहले होना चाहिए.")
            else:
                range_hist = []
                for i in range(30, len(df)):
                    cur_date = df.iloc[i]["DATE"].date()
                    if cur_date < start_date or cur_date > end_date:
                        continue
                    train_df = df.iloc[:i].copy()
                    row = df.iloc[i]
                    pred, conf, frm = predict_row(train_df, row, target_shift, threshold)
                    range_hist.append({
                        "DATE": row["DATE"],
                        "ACTUAL": row[target_shift],
                        "PRED": pred,
                        "FROM": frm,
                        "CONF": conf if conf >= 0 else np.nan,
                        "RESULT": status_mark(row[target_shift], pred)
                    })

                rh = pd.DataFrame(range_hist)
                st.write(f"यह prediction range **{start_date}** से **{end_date}** तक का है.")
                if not rh.empty:
                    st.dataframe(rh, use_container_width=True)
                    st.write(f"Range Accuracy: {(rh['RESULT'] == '✅').mean():.4f}")
                else:
                    st.warning("No rows found in selected range.")

    st.subheader("Last 20 Predictions")
    hist20 = history_table(df, target_shift, threshold, upto_date=None, limit=20)
    if not hist20.empty:
        st.dataframe(hist20, use_container_width=True)

    st.subheader("Shift Relations")
    rel_rows = []
    train_all = df.iloc[:-1].copy() if len(df) > 1 else df.copy()
    for feat in SHIFT_COLS:
        if feat == target_shift:
            continue
        r = shift_rules(train_all, target_shift, feat, min_support=8)
        if not r.empty:
            top = r.iloc[0]
            rel_rows.append({
                "FROM": feat,
                "TO": target_shift,
                "COND_VALUE": int(top["cond"]),
                "PRED": int(top["pred"]),
                "SUPPORT": int(top["support"]),
                "PROB": round(float(top["prob"]), 4)
            })
    rel_df = pd.DataFrame(rel_rows)
    st.dataframe(rel_df, use_container_width=True)

    st.subheader("Usage Notes")
    st.write("1. Target shift select करें.")
    st.write("2. Mode select करें.")
    st.write("3. Selected date का prediction उसी date के लिए होगा.")
    st.write("4. Date range mode में selected dates के बीच history output आएगा.")
    st.write("5. Below history में RESULT column tick/cross दिखाएगा.")

except Exception as e:
    st.error(f"Error: {e}")
