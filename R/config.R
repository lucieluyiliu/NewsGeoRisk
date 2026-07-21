# Central path configuration for the flow analysis (mirrors Python/measure/config.py).
#
# All data is read in place from Dropbox; all generated output goes to
# Output/TensionFlow/. Override the env vars if Dropbox lives elsewhere:
#   NEWSGEORISK_DROPBOX  -> the "News-based Geoeconomic Risk" project folder
#   FLOWINT_DROPBOX      -> the "FlowIntSpillover" project folder
#   MSCI_DIR             -> the MSCI ACWI constituents folder

.dropbox_root <- function() {
  for (p in path.expand(c("~/Dropbox", "~/Library/CloudStorage/Dropbox"))) {
    if (dir.exists(p)) return(p)
  }
  stop("Dropbox root not found; set NEWSGEORISK_DROPBOX / FLOWINT_DROPBOX / MSCI_DIR")
}

DROPBOX_PROJECT <- Sys.getenv("NEWSGEORISK_DROPBOX",
  file.path(.dropbox_root(), "News-based Geoeconomic Risk"))
FLOWINT_PROJECT <- Sys.getenv("FLOWINT_DROPBOX",
  file.path(.dropbox_root(), "FlowIntSpillover"))
MSCI_DIR <- Sys.getenv("MSCI_DIR",
  file.path(.dropbox_root(), "MSCI_Index", "ACWI"))

# Inputs (read-only)
MEASURE_DIR   <- file.path(DROPBOX_PROJECT, "Henry_updated", "data", "measures")
HENRY_CTRL_DIR <- file.path(DROPBOX_PROJECT, "Henry_updated", "data", "data_master_file", "fund_flow")
FLOWINT_DATA  <- file.path(FLOWINT_PROJECT, "Data")
BILATERAL_CSV <- file.path(FLOWINT_DATA, "bilateral_country_flows_quarterly.csv")
MSCI_CSV      <- file.path(MSCI_DIR, "ACWIInclusion.csv")

# Outputs
OUTPUT_ROOT <- file.path(DROPBOX_PROJECT, "Output", "TensionFlow")
FIG_DIR     <- file.path(OUTPUT_ROOT, "Figures")
TAB_DIR     <- file.path(OUTPUT_ROOT, "Tables")
for (d in c(FIG_DIR, TAB_DIR)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
