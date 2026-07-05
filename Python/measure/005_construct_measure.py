# Repo copy of Henry_updated pipeline. Data stays in Henry_updated/data; paths
# below are relative, so switch the working directory there (see config.py).
import os as _os; from config import HENRY_ROOT as _HR; _os.chdir(_HR)

# constructs and graphs the measure

import pandas as pd
import re, json, ast
import pandas as pd

import json, re
import pandas as pd
from ast import literal_eval


cn_matched_filtered_translated= pd.read_csv('data/pooled_cnen_news/matched_headline/cn_matched_filtered_translated_cleaned.csv.gz')
cn_classified_p1 = pd.read_csv('data/sentence_classification/cn_matched_part1.csv')
cn_classified_p2 = pd.read_csv('data/sentence_classification/cn_matched_part2.csv')
cn_classified = pd.concat([cn_classified_p1,cn_classified_p2])



cn_classified = cn_classified.drop(columns=['index','body_org','cn_body_translated_org','en_body_embed','cn_body_embed','cos_sim'])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# clean json results
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

CODE_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*([\s\S]*?)\s*```\s*$",
    re.IGNORECASE
)


def _strip_code_fences(s: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences if present."""
    m = CODE_FENCE_RE.match(s)
    return m.group(1) if m else s


def _clean_json_string(s: str) -> str:
    """Normalize CSV-embedded JSON strings to be JSON-loadable."""
    s = str(s).lstrip("\ufeff").strip()
    s = _strip_code_fences(s)

    # Fix common invalid escapes from CSV / LLM outputs
    s = s.replace(r"\'", "'")
    s = re.sub(r'\\(?!["\\/bfnrtu])', "", s)

    return s


def parse_messy_json(x):
    """
    Parse messy JSON-like strings.
    Returns {} if unparseable.
    Normalizes [dict] -> dict.
    """
    if pd.isna(x):
        return {}

    s = _clean_json_string(x)

    for parser in (json.loads, literal_eval):
        try:
            data = parser(s)

            # Handle double-stringified JSON
            if isinstance(data, str) and data.strip().startswith(("{", "[")):
                data = json.loads(data)

            if isinstance(data, list):
                return data[0] if data and isinstance(data[0], dict) else {}

            if isinstance(data, dict):
                return data

        except Exception:
            continue

    return {}


def expand_json_column(
    df: pd.DataFrame,
    col_name: str,
    prefix: str | None = None
) -> pd.DataFrame:
    """
    Expand one messy JSON column into normal dataframe columns.
    """
    parsed = df[col_name].apply(parse_messy_json)
    expanded = pd.json_normalize(parsed)

    if prefix is None:
        prefix = col_name

    expanded.columns = [
        f"{prefix}_{c}".replace(" ", "_")
        for c in expanded.columns
    ]

    return pd.concat([df.reset_index(drop=True), expanded.reset_index(drop=True)], axis=1)


def prepare_macro_verification_flags(
    df: pd.DataFrame,
    cn_col: str = "cn_macro_verify",
    en_col: str = "en_macro_verify",
    flag_name: str = "macro_level_international_news",
    drop_null: bool = False,
    return_inconsistent: bool = True
):
    """
    Expand CN and EN macro verification JSON columns, extract macro-level flags,
    convert them to numeric 1/0, and optionally return inconsistent rows.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    cn_col : str
        Column containing Chinese-side JSON verification result.
    en_col : str
        Column containing English-side JSON verification result.
    flag_name : str
        Name of the flag inside the parsed JSON.
    drop_null : bool
        If True, drop rows where either CN or EN flag is missing.
    return_inconsistent : bool
        If True, return both cleaned dataframe and inconsistent dataframe.

    Returns
    -------
    If return_inconsistent=True:
        df_expanded, df_inconsistent

    If return_inconsistent=False:
        df_expanded
    """

    df_expanded = df.copy()

    df_expanded = expand_json_column(df_expanded, cn_col)
    df_expanded = expand_json_column(df_expanded, en_col)

    cn_flag_col = f"{cn_col}_{flag_name}"
    en_flag_col = f"{en_col}_{flag_name}"

    if cn_flag_col not in df_expanded.columns:
        raise KeyError(f"Missing expanded column: {cn_flag_col}")

    if en_flag_col not in df_expanded.columns:
        raise KeyError(f"Missing expanded column: {en_flag_col}")

    df_inconsistent = df_expanded[
        df_expanded[cn_flag_col] != df_expanded[en_flag_col]
    ].copy()

    if drop_null:
        df_expanded = df_expanded[
            df_expanded[cn_flag_col].notna()
            & df_expanded[en_flag_col].notna()
        ].copy()

    df_expanded["cn_macro_flag"] = (
        df_expanded[cn_flag_col]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"true": 1, "false": 0})
    )

    df_expanded["en_macro_flag"] = (
        df_expanded[en_flag_col]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"true": 1, "false": 0})
    )

    if return_inconsistent:
        return df_expanded, df_inconsistent

    return df_expanded

def prepare_true_international_news(
    df,
    parse_func,
    cn_macro_col="cn_macro_verify_macro_level_international_news",
    en_macro_col="en_macro_verify_macro_level_international_news",
    cn_bloc_col="cn_bloc_result",
    en_bloc_col="en_bloc_result",
    cn_json_col="cn_bloc_result_json",
    en_json_col="en_bloc_result_json"
):
    """
    Keep observations that:
    1. are macro-level international news in both CN and EN checks;
    2. have non-missing CN and EN bloc extraction results;
    3. have successfully parsed CN and EN bloc JSON results.
    """

    df = df.copy()

    # Check required columns
    required_cols = [cn_macro_col, en_macro_col, cn_bloc_col, en_bloc_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    # Treat string 'False', boolean False, missing, and empty string as invalid
    def valid_macro_flag(s):
        return (
            s.notna()
            & ~s.astype(str).str.strip().str.lower().isin(["false", "nan", "none", ""])
        )

    macro_mask = (
        valid_macro_flag(df[cn_macro_col])
        & valid_macro_flag(df[en_macro_col])
    )

    bloc_mask = (
        df[cn_bloc_col].notna()
        & df[en_bloc_col].notna()
    )

    df_true = df.loc[macro_mask & bloc_mask].copy()

    # Parse messy JSON
    df_true[en_json_col] = df_true[en_bloc_col].apply(parse_func)
    df_true[cn_json_col] = df_true[cn_bloc_col].apply(parse_func)

    # Keep only successfully parsed results
    df_true = df_true.loc[
        df_true[en_json_col].notna()
        & df_true[cn_json_col].notna()
    ].copy()

    return df_true


# Clean for cn matched news
cn_classified, cn_classified_inconsistent = prepare_macro_verification_flags(
    cn_classified,
    cn_col="cn_macro_verify",
    en_col="en_macro_verify"
)

# Keep true international macro news and parse bloc JSON
cn_classified_international_news = prepare_true_international_news(
    cn_classified,
    parse_func=parse_messy_json
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# clean sentence classifications
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


import pandas as pd
import re

_WORD_RE = re.compile(r"\b\w+\b", flags=re.UNICODE)
def _wc(s): return len(_WORD_RE.findall(s)) if isinstance(s, str) else 0

def _norm_bloc(x):
    if not isinstance(x, str): return None
    x = x.strip().lower()
    if x.startswith("east"): return "East"
    if x.startswith("west"): return "West"
    return None

def _norm_tone(x):
    if not isinstance(x, str): return None
    x = x.strip().lower()
    if x.startswith("pos"): return "Positive"
    if x.startswith("neg"): return "Negative"
    return None

def _row_buckets(obj):
    """Return dict of 8 bloc-tone word counts for one cell (dict)."""
    buckets = {
        "East_East_Positive": 0,
        "East_East_Negative": 0,
        "East_West_Positive": 0,
        "East_West_Negative": 0,
        "West_West_Positive": 0,
        "West_West_Negative": 0,
        "West_East_Positive": 0,
        "West_East_Negative": 0,
    }
    if not isinstance(obj, dict):
        return buckets

    sents = obj.get("extracted_sentences", [])
    if not isinstance(sents, list):
        return buckets

    for item in sents:
        if not isinstance(item, dict):
            continue
        fr = _norm_bloc(item.get("framer_bloc"))
        tg = _norm_bloc(item.get("target_bloc"))
        tn = _norm_tone(item.get("tone"))
        if fr and tg and tn:
            key = f"{fr}_{tg}_{tn}"
            if key in buckets:
                buckets[key] += _wc(item.get("sentence"))
    return buckets

def add_bloc_tone_columns(df, json_col, source_label):
    """
    Adds 8 columns for (framer_bloc, target_bloc, tone) word counts.
    Column names are prefixed with the source label ('en'/'cn').
    """
    # Generate one dict per row
    counts_series = df[json_col].apply(_row_buckets)
    # Expand into columns
    expanded = pd.DataFrame(counts_series.tolist(), index=df.index)
    expanded.columns = [f"{source_label}_{c}" for c in expanded.columns]
    # Merge back
    return pd.concat([df, expanded], axis=1)



# Clean for cn matched news
cn_expanded = cn_classified_international_news.copy()

# add columns for English and Chinese results
cn_expanded = add_bloc_tone_columns(cn_expanded, "en_bloc_result_json", "en")
cn_expanded = add_bloc_tone_columns(cn_expanded, "cn_bloc_result_json", "cn")




# construct 3 measures, one is month to month, one is rolling quarter to quarter, one is rolling 30d
# ============================================================
# 0. Start from existing variable
# ============================================================

df_measure = cn_expanded.copy()

date_col = "timestamp_dt"
en_body_col = "body"
cn_body_col = "cn_body_translated"

bucket_suffixes = [
    "East_East_Positive",
    "East_East_Negative",
    "East_West_Positive",
    "East_West_Negative",
    "West_West_Positive",
    "West_West_Negative",
    "West_East_Positive",
    "West_East_Negative",
]

en_bucket_cols = [f"en_{x}" for x in bucket_suffixes]
cn_bucket_cols = [f"cn_{x}" for x in bucket_suffixes]
all_bucket_cols = en_bucket_cols + cn_bucket_cols


# ============================================================
# 1. Prepare dates, bucket counts, and article word counts
# ============================================================

df_measure[date_col] = pd.to_datetime(df_measure[date_col], errors="coerce")
df_measure = df_measure[df_measure[date_col].notna()].copy()

for col in all_bucket_cols:
    df_measure[col] = pd.to_numeric(df_measure[col], errors="coerce").fillna(0)

df_measure["en_total_article_words"] = df_measure[en_body_col].apply(_wc)
df_measure["cn_total_article_words"] = df_measure[cn_body_col].apply(_wc)
# calculates total classified words (not used in measure construction)
df_measure["en_classified_bucket_words"] = df_measure[en_bucket_cols].sum(axis=1)
df_measure["cn_classified_bucket_words"] = df_measure[cn_bucket_cols].sum(axis=1)

df_measure["classified_bucket_words_total"] = (
    df_measure["en_classified_bucket_words"]
    + df_measure["cn_classified_bucket_words"]
)


# ============================================================
# 2. Article-level raw tone bias
# ============================================================

df_measure["en_tone_bias_raw"] = (
    (
        df_measure["en_West_West_Positive"]
        - df_measure["en_West_West_Negative"]
        + df_measure["en_East_West_Positive"]
        - df_measure["en_East_West_Negative"]
    )
    -
    (
        df_measure["en_West_East_Positive"]
        - df_measure["en_West_East_Negative"]
        + df_measure["en_East_East_Positive"]
        - df_measure["en_East_East_Negative"]
    )
)

df_measure["cn_tone_bias_raw"] = (
    (
        df_measure["cn_West_West_Positive"]
        - df_measure["cn_West_West_Negative"]
        + df_measure["cn_East_West_Positive"]
        - df_measure["cn_East_West_Negative"]
    )
    -
    (
        df_measure["cn_West_East_Positive"]
        - df_measure["cn_West_East_Negative"]
        + df_measure["cn_East_East_Positive"]
        - df_measure["cn_East_East_Negative"]
    )
)


# ============================================================
# 3. Helper functions
# ============================================================
import numpy as np
def _safe_divide(num, den):
    return np.where(den > 0, num / den, np.nan)


def _add_scaled_tone_gap(df):
    """
    Scale by total words in the pooled full articles.
    """
    df = df.copy()

    df["en_tone_bias_scaled"] = _safe_divide(
        df["en_tone_bias_raw"],
        df["en_total_article_words"]
    )

    df["cn_tone_bias_scaled"] = _safe_divide(
        df["cn_tone_bias_raw"],
        df["cn_total_article_words"]
    )

    df["tone_gap_scaled"] = (
        df["en_tone_bias_scaled"]
        - df["cn_tone_bias_scaled"]
    )

    df["gap_abs_scaled"] = df["tone_gap_scaled"].abs()

    return df


def _aggregate_pooled_articles(df, group_col):
    """
    Treat all articles in each period as one pooled article.
    """
    sum_cols = (
        all_bucket_cols
        + [
            "en_classified_bucket_words",
            "cn_classified_bucket_words",
            "classified_bucket_words_total",
            "en_total_article_words",
            "cn_total_article_words",
            "en_tone_bias_raw",
            "cn_tone_bias_raw",
        ]
    )

    out = (
        df
        .groupby(group_col, as_index=False)
        .agg(
            n_articles=(date_col, "size"),
            period_start=(date_col, "min"),
            period_end=(date_col, "max"),
            **{col: (col, "sum") for col in sum_cols}
        )
    )

    out["pooled_total_article_words"] = (
        out["en_total_article_words"]
        + out["cn_total_article_words"]
    )

    out = _add_scaled_tone_gap(out)

    return out


# ============================================================
# 4. Month-by-month dataframe
# ============================================================

df_measure["month"] = df_measure[date_col].dt.to_period("M")

month_by_month_df = _aggregate_pooled_articles(
    df_measure,
    group_col="month"
)

month_by_month_df["month"] = month_by_month_df["month"].astype(str)


# ============================================================
# 5. Quarter-to-quarter dataframe
# ============================================================

df_measure["quarter"] = df_measure[date_col].dt.to_period("Q")

quarter_to_quarter_df = _aggregate_pooled_articles(
    df_measure,
    group_col="quarter"
)

quarter_to_quarter_df["quarter"] = quarter_to_quarter_df["quarter"].astype(str)


# ============================================================
# 6. 30-day rolling dataframe
# ============================================================

df_measure["date_day"] = df_measure[date_col].dt.floor("D")

daily_sum_cols = (
    all_bucket_cols
    + [
        "en_classified_bucket_words",
        "cn_classified_bucket_words",
        "classified_bucket_words_total",
        "en_total_article_words",
        "cn_total_article_words",
        "en_tone_bias_raw",
        "cn_tone_bias_raw",
    ]
)

daily_df = (
    df_measure
    .groupby("date_day", as_index=False)
    .agg(
        n_articles=("date_day", "size"),
        **{col: (col, "sum") for col in daily_sum_cols}
    )
)

daily_df = daily_df.set_index("date_day").sort_index()

full_daily_index = pd.date_range(
    start=daily_df.index.min(),
    end=daily_df.index.max(),
    freq="D"
)

daily_df = daily_df.reindex(full_daily_index)
daily_df.index.name = "date_day"

for col in ["n_articles"] + daily_sum_cols:
    daily_df[col] = daily_df[col].fillna(0)

rolling_30d_df = (
    daily_df[["n_articles"] + daily_sum_cols]
    .rolling(window=30, min_periods=1)
    .sum()
    .reset_index()
)

rolling_30d_df = rolling_30d_df.rename(columns={"date_day": "window_end"})
rolling_30d_df["window_start"] = rolling_30d_df["window_end"] - pd.Timedelta(days=29)

rolling_30d_df["pooled_total_article_words"] = (
    rolling_30d_df["en_total_article_words"]
    + rolling_30d_df["cn_total_article_words"]
)

rolling_30d_df = _add_scaled_tone_gap(rolling_30d_df)


# ============================================================
# 7. Reorder columns
# ============================================================

key_cols_month = [
    "month",
    "period_start",
    "period_end",
    "n_articles",
    "en_classified_bucket_words",
    "cn_classified_bucket_words",
    "classified_bucket_words_total",
    "en_total_article_words",
    "cn_total_article_words",
    "pooled_total_article_words",
    "en_tone_bias_raw",
    "cn_tone_bias_raw",
    "en_tone_bias_scaled",
    "cn_tone_bias_scaled",
    "tone_gap_scaled",
    "gap_abs_scaled",
]

key_cols_quarter = [
    "quarter",
    "period_start",
    "period_end",
    "n_articles",
    "en_classified_bucket_words",
    "cn_classified_bucket_words",
    "classified_bucket_words_total",
    "en_total_article_words",
    "cn_total_article_words",
    "pooled_total_article_words",
    "en_tone_bias_raw",
    "cn_tone_bias_raw",
    "en_tone_bias_scaled",
    "cn_tone_bias_scaled",
    "tone_gap_scaled",
    "gap_abs_scaled",
]

key_cols_rolling = [
    "window_start",
    "window_end",
    "n_articles",
    "en_classified_bucket_words",
    "cn_classified_bucket_words",
    "classified_bucket_words_total",
    "en_total_article_words",
    "cn_total_article_words",
    "pooled_total_article_words",
    "en_tone_bias_raw",
    "cn_tone_bias_raw",
    "en_tone_bias_scaled",
    "cn_tone_bias_scaled",
    "tone_gap_scaled",
    "gap_abs_scaled",
]

month_by_month_df = month_by_month_df[
    key_cols_month
    + [c for c in month_by_month_df.columns if c not in key_cols_month]
]

quarter_to_quarter_df = quarter_to_quarter_df[
    key_cols_quarter
    + [c for c in quarter_to_quarter_df.columns if c not in key_cols_quarter]
]

rolling_30d_df = rolling_30d_df[
    key_cols_rolling
    + [c for c in rolling_30d_df.columns if c not in key_cols_rolling]
]


# ============================================================
# 1. Prepare x-axis date columns
# ============================================================

import os
import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import pandas as pd

SAVE_FIG_PATH = "graphs/measure_TS"
os.makedirs(SAVE_FIG_PATH, exist_ok=True)

month_plot_df = month_by_month_df.copy()
quarter_plot_df = quarter_to_quarter_df.copy()
rolling_plot_df = rolling_30d_df.copy()

month_plot_df["month_date"] = pd.to_datetime(month_plot_df["month"])

quarter_plot_df["quarter_date"] = pd.PeriodIndex(
    quarter_plot_df["quarter"], freq="Q"
).to_timestamp()

rolling_plot_df["window_end"] = pd.to_datetime(rolling_plot_df["window_end"])


# ============================================================
# 2. Helper graph function
# ============================================================

def plot_time_series(df, x_col, y_col, title, xlabel, ylabel, filename):
    plot_df = df[[x_col, y_col]].dropna().copy()
    plot_df = plot_df.sort_values(x_col)

    plt.figure(figsize=(12, 5))
    plt.plot(plot_df[x_col], plot_df[y_col], linewidth=1.8)
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    save_path = os.path.join(SAVE_FIG_PATH, filename)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()
    print(f"Saved: {save_path}")


# ============================================================
# 3. Main tone_gap_scaled graphs
# ============================================================

plot_time_series(
    month_plot_df,
    x_col="month_date",
    y_col="tone_gap_scaled",
    title="Monthly EN-CN Scaled Tone Gap",
    xlabel="Month",
    ylabel="Tone gap scaled",
    filename="monthly_tone_gap_scaled.png"
)

plot_time_series(
    quarter_plot_df,
    x_col="quarter_date",
    y_col="tone_gap_scaled",
    title="Quarterly EN-CN Scaled Tone Gap",
    xlabel="Quarter",
    ylabel="Tone gap scaled",
    filename="quarterly_tone_gap_scaled.png"
)

plot_time_series(
    rolling_plot_df,
    x_col="window_end",
    y_col="tone_gap_scaled",
    title="30-Day Rolling EN-CN Scaled Tone Gap",
    xlabel="Window end date",
    ylabel="Tone gap scaled",
    filename="rolling_30d_tone_gap_scaled.png"
)


# ============================================================
# 4. Absolute gap graphs
# ============================================================

plot_time_series(
    month_plot_df,
    x_col="month_date",
    y_col="gap_abs_scaled",
    title="Monthly Absolute Scaled Tone Gap",
    xlabel="Month",
    ylabel="Absolute tone gap scaled",
    filename="monthly_gap_abs_scaled.png"
)

plot_time_series(
    quarter_plot_df,
    x_col="quarter_date",
    y_col="gap_abs_scaled",
    title="Quarterly Absolute Scaled Tone Gap",
    xlabel="Quarter",
    ylabel="Absolute tone gap scaled",
    filename="quarterly_gap_abs_scaled.png"
)

plot_time_series(
    rolling_plot_df,
    x_col="window_end",
    y_col="gap_abs_scaled",
    title="30-Day Rolling Absolute Scaled Tone Gap",
    xlabel="Window end date",
    ylabel="Absolute tone gap scaled",
    filename="rolling_30d_gap_abs_scaled.png"
)


# ============================================================
# 5. Monthly-sampled 30-day rolling dataframe
# ============================================================

rolling_plot_df = rolling_30d_df.copy()
rolling_plot_df["window_end"] = pd.to_datetime(rolling_plot_df["window_end"])

rolling_plot_df_monthly = (
    rolling_plot_df
    .sort_values("window_end")
    .set_index("window_end")
    .resample("ME")
    .last()
    .reset_index()
)

rolling_plot_df_monthly["month"] = (
    rolling_plot_df_monthly["window_end"]
    .dt.to_period("M")
    .astype(str)
)


# ============================================================
# 6. Monthly-sampled 30-day rolling graphs
# ============================================================

plot_time_series(
    rolling_plot_df_monthly,
    x_col="window_end",
    y_col="tone_gap_scaled",
    title="Monthly Sampled 30-Day Rolling EN-CN Scaled Tone Gap",
    xlabel="Month",
    ylabel="Tone gap scaled",
    filename="rolling_30d_monthly_tone_gap_scaled.png"
)

plot_time_series(
    rolling_plot_df_monthly,
    x_col="window_end",
    y_col="gap_abs_scaled",
    title="Monthly Sampled 30-Day Rolling Absolute Scaled Tone Gap",
    xlabel="Month",
    ylabel="Absolute tone gap scaled",
    filename="rolling_30d_monthly_gap_abs_scaled.png"
)






# save the measures

from pathlib import Path

# Create output folder if it does not exist
SAVE_DIR = Path("data/measures")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Save three measure dataframes
month_by_month_df.to_csv(SAVE_DIR / "month_by_month_df.csv", index=False)
quarter_to_quarter_df.to_csv(SAVE_DIR / "quarter_to_quarter_df.csv", index=False)
rolling_30d_df.to_csv(SAVE_DIR / "rolling_30d_df.csv", index=False)