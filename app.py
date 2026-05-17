import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

st.set_page_config(page_title="Shift Predictor", layout="wide")

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
    candidates = [0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.28, 0.30]
    base = df.reset_index(drop=True)
    best_th = 0.20
    best_score = -1

    for th in candidates:
        hits = 0
        total = 0
        for i in range(30, len(base) - 1):
            train = base.iloc[:i].copy()
            row = base.iloc[i]
            actual = base.iloc[i + 1][target_shift]

            best_pred = np.nan
            best_prob = -1
            for feat in SHIFT_COLS:
                if feat == target_shift or pd.isna(row[feat]):
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
                total += 1
                if int(best_pred) == int(actual):
                    hits += 1

        score = hits / total if total else 0
        if score > best_score:
            best_score = score
            best_th = th

    return best_th

def predict_row(train_df, row, target_shift, threshold):
    best_pred = np.nan
    best_prob = -1.0
    best_from = ""

    for feat in SHIFT_COLS:
        if feat == target_shift or pd.isna(row[feat]):
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

def get_selected_rows(df, selected_date):
    selected = df[df["DATE"].dt.date == selected_date]
    if selected.empty:
        return None, None
    idx = selected.index[0]
    train_df = df.iloc[:idx].copy()
    row = df.iloc[idx]
    return train_df, row

def result_mark(actual, pred):
    if pd.isna(actual) or pd.isna(pred):
        return "❌"
    return "✅" if int(actual) == int(pred) else "❌"

def colored_result(actual, pred):
    if pd.isna(actual) or pd.isna(pred):
        return "<span style='color:red;font-weight:bold'>❌</span>"
    if int(actual) == int(pred):
        return "<span style='color:green;font-weight:bold'>✅</span>"
    return "<span style='color:red;font-weight:bold'>❌</span>"

st.title("Shift Predictor")

uploaded = st.file_uploader("Excel file upload करें", type=["xlsx"])

if not uploaded:
    st.info("Excel file upload करें.")
    st.stop()

try:
    df = load_excel(uploaded)
    st.success(f"Loaded rows: {len(df)}")

    with st.sidebar:
        st.header("Settings")
        target_shift = st.selectbox("Target shift", SHIFT_COLS, index=0)
        mode = st.selectbox("Mode", ["Select single date", "Latest date"], index=0)
        fast_mode = st.checkbox("Fast mode", value=True)

    valid_dates = sorted(df["DATE"].dropna().dt.date.unique().tolist())
    if not valid_dates:
        st.error("No valid dates found.")
        st.stop()

    threshold = auto_threshold(df, target_shift)

    st.subheader("Selected Date")
    if mode == "Select single date":
        selected_date = st.date_input(
            "Date चुनें",
            value=valid_dates[-1],
            min_value=valid_dates[0],
            max_value=valid_dates[-1]
        )
        prediction_label = "This date prediction"
    else:
        selected_date = valid_dates[-1]
        st.write(f"Latest available date: **{selected_date}**")
        prediction_label = "Latest date prediction"

    st.subheader("Prediction")
    train_df, row = get_selected_rows(df, selected_date)

    if row is None:
        st.warning("Selected date data not found.")
        st.stop()

    pred, conf, frm = predict_row(train_df, row, target_shift, threshold)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected Date", str(selected_date))
    c2.metric("Target Shift", target_shift)
    c3.metric("Predicted Number", "NA" if pd.isna(pred) else int(pred))
    c4.metric("Confidence", "NA" if conf < 0 else f"{conf:.3f}")

    st.write(f"Prediction type: **{prediction_label}**")
    st.write(f"Source shift: **{frm if frm else 'None'}**")

    st.subheader("Latest History")
    hist_rows = []
    start_idx = max(30, len(df) - 20)

    for i in range(start_idx, len(df)):
        cur = df.iloc[i]
        train = df.iloc[:i].copy()
        actual = cur[target_shift]
        p, c, f = predict_row(train, cur, target_shift, threshold)
        hist_rows.append({
            "DATE": cur["DATE"].date(),
            "ACTUAL": actual,
            "PRED": p,
            "FROM": f,
            "CONF": None if c < 0 else round(c, 3),
            "RESULT": colored_result(actual, p)
        })

    hist = pd.DataFrame(hist_rows)

    if hist.empty:
        st.warning("History not available.")
    else:
        st.markdown(
            """
            <style>
            .result-green { color: green; font-weight: bold; }
            .result-red { color: red; font-weight: bold; }
            </style>
            """,
            unsafe_allow_html=True
        )

        def style_result(val):
            if "green" in str(val):
                return "color: green; font-weight: bold;"
            return "color: red; font-weight: bold;"

        show = hist.copy()
        st.dataframe(show, use_container_width=True)

        st.markdown("### Tick / Cross View")
        for _, r in show.iterrows():
            mark = "✅" if r["RESULT"] == "<span style='color:green;font-weight:bold'>✅</span>" else "❌"
            color = "green" if mark == "✅" else "red"
            st.markdown(
                f"<div style='padding:6px 0;color:{color};font-weight:bold'>"
                f"{r['DATE']} | Actual: {r['ACTUAL']} | Pred: {r['PRED']} | {mark}"
                f"</div>",
                unsafe_allow_html=True
            )

    st.subheader("Note")
    st.write("ऊपर की prediction selected date या latest date के लिए है.")
    st.write("History में green tick सही prediction को दिखाता है, red cross गलत prediction को.")

except Exception as e:
    st.error(f"Error: {e}")
