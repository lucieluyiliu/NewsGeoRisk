# NewsGeoRisk - News-based Geoeconomic Risk

## Ground Rules

1. **Never delete data or code.** Do not remove files, drop tables, or delete code unless
   explicitly told to do so. Never delete notes.
2. **`Henry_updated/` is strictly read-only.** It is Henry's (PhD student) working area:
   his pipeline originals and ALL project data live there. Never edit, move, or write
   anything in it. The measure code in `Python/measure/` is a versioned mirror of his
   scripts; when he updates, refresh the mirror (see README), never the reverse.
3. Stay within this repository and the Dropbox project folder
   (`~/Library/CloudStorage/Dropbox/News-based Geoeconomic Risk/`). Within it:
   - **Read-only**: `Henry_updated/`, `Literature/`, `MeetingNotes/`, `Benchmarks/`,
     legacy folders (`codes/`, `Henry/`, `Economic outcomes/`).
   - **Read/write**: `Notes/` for project notes (update existing notes in place; only
     create new files when the user asks) and `Output/` for generated results.
   - `Data/` is read-only unless the task is explicitly data construction.
4. **Obsidian vault** (`~/Library/CloudStorage/Dropbox/Obsidian/research-vault/`): this
   project's notes will appear there as a `Projects/` symlink to `Notes/`. Write only
   project-related notes; never touch `Private/` or `.obsidian/`.
5. **Two-machine sync discipline.** Lucie works on this repo from two Macs; GitHub is
   the only sync channel. At the START of every session, run `git status` and
   `git fetch` (or `git pull`): report any uncommitted changes, unpushed commits, or
   commits behind origin BEFORE doing other work, and do not edit over a dirty or
   stale tree without flagging it. At the END of every session (and before any large
   edit), remind Lucie to commit and push; never leave work uncommitted at session end
   without saying so explicitly.

## Project Layout

This repo lives OUTSIDE Dropbox (default `~/Projects/NewsGeoRisk`; GitHub
`lucieluyiliu/NewsGeoRisk`). The Dropbox project folder holds data, notes, and outputs,
reached via gitignored per-machine symlinks (`Data`, `Notes`, `Literature`, `Output`;
see README) or via the `NEWSGEORISK_DROPBOX` environment variable.

- Repo (git tracked): `Python/`, `R/`, `README.md`, `CLAUDE.md`
- Division of labor: Henry constructs the measure (in `Henry_updated/`); Lucie analyzes
  economic outcomes, starting with US-China fund flows (in `R/`).

**Output convention**: all generated output (figures, tables, html renders, intermediate
files) goes to `Output/` (`Output/Figures/`, `Output/Tables/`, or a task subfolder).
Do NOT write outputs into the repo, and do NOT write into `Henry_updated/`.

## Coding Style

- Research code, not production code: concise, no defensive try/catch unless necessary.
- Write interactive code that can be evaluated line by line.
- Edit existing scripts; do NOT create `_V2`/`_new` copies (git history holds versions).
- Never hardcode machine-specific paths. Python uses `Python/measure/config.py`
  (`NEWSGEORISK_DROPBOX` env var override); R will use a `config.R` with the same
  pattern once the flow analysis starts.
- Exception: the five `Python/measure/00x_*.py` scripts mirror Henry's code. Below
  their 4-line bootstrap header they must stay byte-identical to his originals; do not
  restyle or refactor them.

## Pipeline

### Measure construction (`Python/measure/`, Henry's, mirrored)

| Step | Script | Purpose |
|------|--------|---------|
| 001 | `001_filter_macro_and_cnen_news.py` | Filter Reuters macro news (subject/suffix tags, headline filter); pool CN/EN records |
| 002 | `002_embed_headlines_and_match.py` | Embed headlines; match EN-CN article pairs by cosine similarity |
| 003 | `003_clean_match_headlines.py` | Threshold matches, merge bodies, GPT-translate |
| 004 | `004_check_macro_sentence_classify.py` | GPT: confirm macro news; classify bloc-A-about-bloc-B judgemental language |
| 005 | `005_construct_measure.py` | Construct slant measure -> `Henry_updated/data/measures/` |

Final measure files: `rolling_30d_df.csv`, `month_by_month_df.csv`,
`quarter_to_quarter_df.csv`. Key variables: `gap_abs_scaled` (absolute CN-EN slant gap),
`en_tone_bias_scaled`, `cn_tone_bias_scaled`.

### Flow analysis (`R/`, Lucie's, to come)

US-China cross-border fund flows decomposed into end-investor flows and manager active
reallocation, regressed on the slant measure. Henry's exploratory regressions in
`Henry_updated/data/data_master_file/fund_flow/` are superseded and stay untouched as
his record.

## Data Conventions

- **Quarter format:** quarters map to end-month `yyyymm` integers (e.g. Q4 2024 = `202412`).
- **Flow definition:** `flow = flow_num / aum_lag` from FactSet-based country flows;
  a valid observation needs non-missing `flow_num`, `aum_lag > 0`, fund history > 1 quarter.
- **Measure timing:** the measure enters regressions lagged one period; prefer explicit
  date joins over positional `shift()` when building new analysis.
- **Winsorization:** follow the FlowIntSpillover convention (flow variables 1%/99% by
  quarter) in new R work.
- GPT caches in `Henry_updated/data/gpt_results/` are expensive to regenerate; never
  touch them.

## Session Logs

At the end of each session (or after completing a piece of analysis), write a working
journal entry to `Notes/WorkingJournal/YYYY-MM-DD-Lucie-[Description].md` using the
`work-summary` skill conventions: frontmatter with date, project, `git_commit` (full
hash), `git_message`; factual and objective, no speculation or recommendations unless
asked; every claim cited to code/output/note paths.

## Literature

Citekey-named notes in `Notes/Literature/` (snake_case `author_year`, matching pinned
Zotero Better BibTeX keys). Zotero MCP is configured in `.mcp.json` (keys in
`Notes/.env`); the `zotero-paper-reader` skill fetches papers, full texts go to
`Notes/PaperInMarkdown/<citekey>_fulltext.md`.
