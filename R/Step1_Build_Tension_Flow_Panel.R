# Step 1: Build the tension x bilateral-flow analysis panel.
#
# Merges (i) Henry's quarterly slant-gap measure, (ii) bilateral US-China fund
# flows from FlowIntSpillover, (iii) MSCI China A-share inclusion controls.
# Output: Output/TensionFlow/tension_flow_panel.csv, one row per cell x quarter.
#
# Quarter key convention here: integer YYYYQQ (e.g. 201801 = 2018Q1), the format
# used by bilateral_country_flows_quarterly.csv (verified: last two digits 1-4).

library(data.table)
source("R/config.R")

qtr_add <- function(q, k = 1L) {  # shift YYYYQQ by k quarters
  i <- (q %/% 100L) * 4L + (q %% 100L - 1L) + k
  (i %/% 4L) * 100L + (i %% 4L) + 1L
}
qtr_end_date <- function(q) as.Date(sprintf("%d-%02d-01", q %/% 100L, (q %% 100L) * 3L)) + 32L -
  as.integer(format(as.Date(sprintf("%d-%02d-01", q %/% 100L, (q %% 100L) * 3L)) + 32L, "%d"))

## 1. Tension measure (quarterly), 2018Q1-2024Q4 -------------------------------
meas <- fread(file.path(MEASURE_DIR, "quarter_to_quarter_df.csv"))
meas[, qtr := as.integer(paste0(substr(quarter, 1, 4), "0", substr(quarter, 6, 6)))]
stopifnot(meas$qtr %% 100L %in% 1:4, !anyDuplicated(meas$qtr))
meas <- meas[, .(qtr, n_articles, gap_abs_scaled, tone_gap_scaled,
                 en_tone_bias_scaled, cn_tone_bias_scaled)]
range(meas$qtr)  # 201801 202404

## 2. Bilateral flows (quarterly), 2000Q1-2025Q1 -------------------------------
flow <- fread(BILATERAL_CSV)
stopifnot(flow$quarter %% 100L %in% 1:4, sort(unique(flow$cell)) == c("China->US", "US->China"))
setnames(flow, "quarter", "qtr")
flow[, `:=`(flow_bn = flow_dollar / 1e9, endinv_bn = end_investor_dollar / 1e9,
            rebal_bn = rebalancing_dollar / 1e9, aum_lag_bn = aum_lag / 1e9)]
flow[!is.finite(pw_total_rate), c("pw_total_rate", "pw_endinv_rate", "pw_rebal_rate") := NA_real_]

## 3. MSCI China A-share weight in ACWI ----------------------------------------
# A-shares are the ISO=="CN" & currency=="CNH" securities. Benchmark-revision
# events are read off the data as changes in the modal standard inclusion factor
# (std_IIF) of A-shares: 0 -> 2.5% (Jun 2018), 5% (Sep 2018), 10% (May 2019),
# 15% (Aug 2019), 20% (Nov 2019, mid-caps added); no further steps through Feb 2025.
msci <- fread(MSCI_CSV, select = c("calc_date", "ISO", "ISO_currency_symbol", "weight", "std_IIF"))
modal <- function(x) if (!length(x)) 0 else as.numeric(names(sort(table(x), decreasing = TRUE))[1])
ashare_m <- msci[, .(msci_cn_wt = sum(weight[ISO == "CN" & ISO_currency_symbol == "CNH"],
                                      na.rm = TRUE),
                     ashare_iif = modal(std_IIF[ISO == "CN" & ISO_currency_symbol == "CNH"])),
                 by = calc_date]
ashare_m[, qtr := (calc_date %/% 10000L) * 100L + (calc_date %/% 100L %% 100L + 2L) %/% 3L]
# last available month within each quarter (= quarter-end month except the terminal
# quarter, where MSCI coverage ends mid-quarter: 2025Q1 uses Feb 2025)
ashare_q <- ashare_m[order(calc_date), .(msci_cn_wt = msci_cn_wt[.N], ashare_iif = ashare_iif[.N]),
                     by = qtr][order(qtr)]
ashare_q[, d_msci_cn_wt := msci_cn_wt - shift(msci_cn_wt)]
ashare_q[, d_ashare_iif := ashare_iif - shift(ashare_iif, fill = 0)]  # revision magnitude
ashare_q[, msci_step := as.integer(d_ashare_iif > 0)]                 # revision-event dummy
stopifnot(ashare_q[msci_step == 1, qtr] == c(201802L, 201803L, 201902L, 201903L, 201904L))

## 4. Henry's macro/market controls (data_master_file/fund_flow, key = end-month yyyymm)
yyyymm_to_qtr <- function(m) (m %/% 100L) * 100L + (m %% 100L) %/% 3L
ctrl_spec <- list(  # file -> columns to keep
  us_real_gdp          = c("GDP_growth_yoy"),
  cn_real_gdp          = c("GDP_growth_yoy_CN"),
  usd_cny_qoq          = c("EX_qoq"),
  IR_diff              = c("IR_diff_CNUS"),
  quarterly_csi300     = c("CSI300_ret"),
  quarterly_csi300_vol = c("CSI300_vol"))
ctrl <- Reduce(function(a, b) merge(a, b, by = "qtr", all = TRUE), lapply(names(ctrl_spec), function(f) {
  d <- fread(file.path(HENRY_CTRL_DIR, paste0(f, ".csv")))
  d <- d[!is.na(YYYYMM), c("YYYYMM", ctrl_spec[[f]]), with = FALSE]  # cn_real_gdp has a source-note footer row
  stopifnot(as.integer(d$YYYYMM) %% 100L %in% c(3L, 6L, 9L, 12L))    # yyyymm_to_qtr assumes quarter-end months
  d[, qtr := yyyymm_to_qtr(as.integer(YYYYMM))][, YYYYMM := NULL]
  stopifnot(!anyDuplicated(d$qtr))
  d
}))
# Henry's usd_cny_qoq 2025Q1 row uses the Jan-31 rate as quarter end (his raw
# monthly series stops there), so EX_qoq is a partial-quarter change: drop it
ctrl[qtr == 202501L, EX_qoq := NA_real_]
ctrl_l1 <- copy(ctrl)[, qtr := qtr_add(qtr, 1L)][, .(qtr, CSI300_ret_l1 = CSI300_ret)]

## 5. Merge: flows + lagged tension + MSCI + Henry's controls ------------------
meas_l1 <- copy(meas)[, qtr := qtr_add(qtr, 1L)]                    # measure at t-1 joined to flow at t
setnames(meas_l1, setdiff(names(meas_l1), "qtr"), paste0(setdiff(names(meas_l1), "qtr"), "_l1"))

panel <- merge(flow, meas,    by = "qtr", all.x = TRUE)             # contemporaneous (descriptives)
panel <- merge(panel, meas_l1, by = "qtr", all.x = TRUE)            # lagged (regressions)
panel <- merge(panel, ashare_q, by = "qtr", all.x = TRUE)
# ashare_q covers every quarter 2005Q1-2025Q1 (weight 0 pre-inclusion); quarters
# before MSCI coverage (pre-2005) stay NA and lie outside the regression sample
panel <- merge(panel, ctrl,    by = "qtr", all.x = TRUE)
panel <- merge(panel, ctrl_l1, by = "qtr", all.x = TRUE)
panel[, date := qtr_end_date(qtr)]
panel[, in_reg_sample := !is.na(gap_abs_scaled_l1) & !is.na(pw_total_rate)]
setorder(panel, cell, qtr)

## 6. Checks and save -----------------------------------------------------------
panel[in_reg_sample == TRUE, .N, by = cell]                          # expect 28 per cell (2018Q2-2025Q1)
stopifnot(panel[in_reg_sample == TRUE, .N, by = cell]$N == c(28L, 28L))
panel[qtr %in% c(201802L, 201903L, 201904L) & cell == "US->China",
      .(qtr, msci_cn_wt, d_msci_cn_wt, msci_step, flow_bn, gap_abs_scaled_l1)]

fwrite(panel, file.path(OUTPUT_ROOT, "tension_flow_panel.csv"))
fwrite(ashare_m[, .(calc_date, msci_cn_wt, ashare_iif)],
       file.path(OUTPUT_ROOT, "msci_ashare_monthly.csv"))
cat("Panel written:", nrow(panel), "rows,",
    panel[, uniqueN(qtr)], "quarters x", panel[, uniqueN(cell)], "cells\n")
