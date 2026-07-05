import os
from pathlib import Path

# Central path configuration for the measure pipeline (repo copy).
#
# Henry's pipeline and all textual/GPT data live in the Dropbox project folder
# under Henry_updated/; this Code copy is the version-controlled mirror. The
# scripts here chdir to HENRY_ROOT at startup so Henry's relative paths
# ("data/...", "graphs/...") resolve unchanged.
#
# Override NEWSGEORISK_DROPBOX if Dropbox lives elsewhere (e.g. Windows).

DROPBOX_PROJECT = Path(os.environ.get(
    "NEWSGEORISK_DROPBOX",
    str(Path.home() / "Library/CloudStorage/Dropbox/News-based Geoeconomic Risk")))

HENRY_ROOT = DROPBOX_PROJECT / "Henry_updated"
DATA_ROOT = HENRY_ROOT / "data"
MEASURE_DIR = DATA_ROOT / "measures"   # rolling_30d_df / month_by_month_df / quarter_to_quarter_df
