# News-based Geoeconomic Risk

Research project constructing a geoeconomic risk measure from the slant of Reuters
macro news coverage toward Chinese versus Western audiences, and studying its effect
on economic outcomes, in particular US-China cross-border fund flows.

**Author:** Henry Dongyihai Peng (dongyihai.peng@student.unimelb.edu.au)

## Repository scope

This repo holds code only:

- `Python/measure/` -- Henry's measure-construction pipeline (versioned mirror; his
  working copy and all data live in the Dropbox project folder under `Henry_updated/`)
- `R/` -- Lucie's flow analysis (end-investor vs manager-reallocation components; to come)

Data, notes, literature, and outputs live in the Dropbox project folder
`News-based Geoeconomic Risk/`, reached via per-machine paths (see below).

## Setup on a new machine

1. Clone: `git clone git@github.com:lucieluyiliu/NewsGeoRisk.git ~/Projects/NewsGeoRisk`
2. Symlinks (Mac; adjust `DB` if Dropbox lives elsewhere):
   ```bash
   cd ~/Projects/NewsGeoRisk
   DB="$HOME/Library/CloudStorage/Dropbox"
   for d in Data Notes Literature Output; do
     ln -s "$DB/News-based Geoeconomic Risk/$d" "$d"
   done
   ```
3. If Dropbox is elsewhere, set `NEWSGEORISK_DROPBOX` to the Dropbox project folder
   in your shell profile; `Python/measure/config.py` (and later `config.R`) read it.

## Measure pipeline (`Python/measure/`)

| Script | Purpose |
|--------|---------|
| `001_filter_macro_and_cnen_news.py` | Filter Reuters macro news via subject/suffix tags and headline word filter; pool CN/EN records |
| `002_embed_headlines_and_match.py`  | Clean and embed headlines; match EN-CN article pairs by cosine similarity |
| `003_clean_match_headlines.py`      | Set match threshold, merge article bodies back, translate bodies (GPT) |
| `004_check_macro_sentence_classify.py` | GPT prompts: confirm macro news; classify judgemental language of bloc A about bloc B |
| `005_construct_measure.py`          | Construct the slant measure and time-series graphs; outputs to `Henry_updated/data/measures/` |

`utility/` holds shared functions, parameters, and the manually labelled subject-code
filter lists. The final measure files are `rolling_30d_df.csv`, `month_by_month_df.csv`,
and `quarter_to_quarter_df.csv`.

### Path design

Each pipeline script starts with a 3-line bootstrap (see `Python/measure/config.py`)
that chdirs to `Henry_updated/`, so Henry's relative paths (`data/...`, `graphs/...`)
run unchanged and all reads/writes stay in his data folders. Below the header the
files are byte-identical to his originals. Running a script therefore WRITES into
`Henry_updated/data/`; there is one data home by design, so do not run the pipeline
casually.

### Syncing with Henry's updates

Henry keeps working in `Henry_updated/` (status quo). When he revises a script,
refresh the mirror and re-add the 4-line header. Check from `Python/measure/`:

```bash
diff <(tail -n +5 001_filter_macro_and_cnen_news.py) \
     "$DB/News-based Geoeconomic Risk/Henry_updated/001_filter_macro_and_cnen_news.py"
```

## Flow analysis (`R/`)

To be added: quarterly US-China cross-border fund flows decomposed into the
end-investor flow component and the manager active-reallocation component,
regressed on the slant measure. Supersedes Henry's exploratory regressions in
`Henry_updated/data/data_master_file/fund_flow/` (kept there as his record).
