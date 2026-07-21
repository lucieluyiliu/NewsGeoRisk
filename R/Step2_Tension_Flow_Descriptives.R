# Step 2: Summary statistics and descriptive plots, tension vs bilateral flows.
#
# Input: Output/TensionFlow/tension_flow_panel.csv (Step 1).
# Output: Output/TensionFlow/Tables/{summary_stats_flows,summary_stats_tension,
#         correlations_tension_flow}.csv and Figures/fig{1,2,3}_*.png.
# Plot style follows FlowIntSpillover Step3B (theme_bw, endinv blue / rebal orange).

library(data.table)
library(ggplot2)
library(patchwork)
library(scales)
source("R/config.R")

panel <- fread(file.path(OUTPUT_ROOT, "tension_flow_panel.csv"))
panel[, date := as.Date(date)]
meas_m <- fread(file.path(MEASURE_DIR, "month_by_month_df.csv"))
meas_m[, date := as.Date(paste0(month, "-15"))]

COL_ENDINV <- "#4C72B0"; COL_REBAL <- "#DD8452"

# quarterly tension series (one row per quarter) and MSCI-step shading rectangles
qmeas <- unique(panel[!is.na(gap_abs_scaled),
                      .(qtr, date, gap_abs_scaled, tone_gap_scaled,
                        en_tone_bias_scaled, cn_tone_bias_scaled, n_articles)])
msci_rect <- unique(panel[msci_step == 1, .(qtr, xmax = date)])
msci_rect[, xmin := as.Date(sprintf("%d-%02d-01", qtr %/% 100L, (qtr %% 100L - 1L) * 3L + 1L))]
events <- data.table(
  date  = as.Date(c("2018-07-06", "2019-05-10", "2020-01-15", "2022-08-02", "2023-02-04")),
  label = c("First tariffs", "Tariff escalation", "Phase-one deal",
            "Pelosi Taiwan visit", "Balloon incident"))

## 1. Summary statistics --------------------------------------------------------
flow_vars <- c("pw_total_rate", "pw_endinv_rate", "pw_rebal_rate",
               "ew_total_rate", "ew_endinv_rate", "ew_rebal_rate",
               "flow_bn", "endinv_bn", "rebal_bn", "aum_lag_bn", "n_funds")
ss_flow <- melt(panel[in_reg_sample == TRUE], id.vars = "cell", measure.vars = flow_vars)[
  , .(N = sum(is.finite(value)), Mean = mean(value, na.rm = TRUE), SD = sd(value, na.rm = TRUE),
      Min = min(value, na.rm = TRUE), P25 = quantile(value, .25, na.rm = TRUE),
      Median = median(value, na.rm = TRUE), P75 = quantile(value, .75, na.rm = TRUE),
      Max = max(value, na.rm = TRUE)), by = .(cell, variable)]
tension_vars <- c("gap_abs_scaled", "tone_gap_scaled", "en_tone_bias_scaled",
                  "cn_tone_bias_scaled", "n_articles")
ss_tens <- melt(qmeas, id.vars = "qtr", measure.vars = tension_vars)[
  , .(N = .N, Mean = mean(value), SD = sd(value), Min = min(value),
      P25 = quantile(value, .25), Median = median(value),
      P75 = quantile(value, .75), Max = max(value)), by = variable]
print(ss_flow, digits = 3); print(ss_tens, digits = 3)
fwrite(ss_flow, file.path(TAB_DIR, "summary_stats_flows.csv"))
fwrite(ss_tens, file.path(TAB_DIR, "summary_stats_tension.csv"))

## 2. Correlations: tension (t and t-1) vs flow components ----------------------
rate_vars <- flow_vars[1:6]
cor_dt <- panel[in_reg_sample == TRUE, rbindlist(lapply(rate_vars, function(v) data.table(
  flow_var    = v,
  cor_contemp = cor(get(v), gap_abs_scaled,    use = "pairwise.complete.obs"),
  cor_lag1    = cor(get(v), gap_abs_scaled_l1, use = "pairwise.complete.obs")))),
  by = cell]
print(cor_dt, digits = 2)
fwrite(cor_dt, file.path(TAB_DIR, "correlations_tension_flow.csv"))

## 3. Fig 1: tension measure with MSCI steps and tension episodes ---------------
ymax <- max(meas_m$gap_abs_scaled)
p1 <- ggplot() +
  geom_rect(data = msci_rect, aes(xmin = xmin, xmax = xmax, ymin = -Inf, ymax = Inf),
            fill = "grey85", alpha = .7) +
  geom_line(data = meas_m, aes(date, gap_abs_scaled, colour = "Monthly"), linewidth = .35) +
  geom_line(data = qmeas, aes(date, gap_abs_scaled, colour = "Quarterly"), linewidth = .8) +
  geom_point(data = qmeas, aes(date, gap_abs_scaled, colour = "Quarterly"), size = 1.2) +
  geom_vline(data = events, aes(xintercept = date), linetype = "dashed",
             colour = "grey40", linewidth = .3) +
  geom_text(data = events, aes(date, ymax * .99, label = label), angle = 90,
            hjust = 1, vjust = -.35, size = 2.7, colour = "grey30") +
  scale_colour_manual(NULL, values = c(Monthly = "grey60", Quarterly = COL_ENDINV)) +
  scale_x_date(date_breaks = "1 year", date_labels = "%Y") +
  labs(x = NULL, y = "Absolute CN-EN slant gap (scaled)",
       title = "US-China tension: Reuters slant-gap measure",
       caption = "Grey bands: MSCI China A-share inclusion step quarters (2018Q2, 2018Q3, 2019Q2-Q4).") +
  theme_bw(base_size = 11) + theme(legend.position = "top")
ggsave(file.path(FIG_DIR, "fig1_tension_series.png"), p1, width = 9, height = 5, dpi = 150)

## 4. Fig 2: bilateral flows (stacked components + total) under the tension series
xlim2 <- as.Date(c("2016-01-01", "2025-06-30"))
bars <- melt(panel[date >= xlim2[1],
                   .(cell, date, `End-investor` = endinv_bn, Rebalancing = rebal_bn)],
             id.vars = c("cell", "date"), variable.name = "component", value.name = "usd_bn")
p_tens <- ggplot(qmeas, aes(date, gap_abs_scaled)) +
  geom_rect(data = msci_rect, aes(xmin = xmin, xmax = xmax, ymin = -Inf, ymax = Inf),
            fill = "grey85", alpha = .7, inherit.aes = FALSE) +
  geom_line(colour = COL_ENDINV, linewidth = .7) + geom_point(colour = COL_ENDINV, size = 1) +
  coord_cartesian(xlim = xlim2) +
  scale_x_date(date_breaks = "1 year", date_labels = "%Y") +
  labs(x = NULL, y = "Slant gap", title = "Tension measure and bilateral fund flows") +
  theme_bw(base_size = 11)
p_flow <- ggplot(bars, aes(date, usd_bn)) +
  geom_rect(data = msci_rect, aes(xmin = xmin, xmax = xmax, ymin = -Inf, ymax = Inf),
            fill = "grey85", alpha = .7, inherit.aes = FALSE) +
  geom_col(aes(fill = component), width = 70, colour = "white", linewidth = .15) +
  geom_hline(yintercept = 0, linewidth = .3) +
  geom_line(data = panel[date >= xlim2[1]], aes(date, flow_bn, colour = "Total net flow"),
            linewidth = .45) +
  geom_point(data = panel[date >= xlim2[1]], aes(date, flow_bn, colour = "Total net flow"),
             size = .7) +
  facet_wrap(~cell, ncol = 1, scales = "free_y") +
  scale_fill_manual(NULL, values = c(`End-investor` = COL_ENDINV, Rebalancing = COL_REBAL)) +
  scale_colour_manual(NULL, values = c(`Total net flow` = "black")) +
  coord_cartesian(xlim = xlim2) +
  scale_x_date(date_breaks = "1 year", date_labels = "%Y") +
  labs(x = NULL, y = "Quarterly flow (USD bn)",
       caption = "Grey bands: MSCI A-share inclusion steps.") +
  theme_bw(base_size = 11) + theme(legend.position = "top")
fig2 <- p_tens / p_flow + plot_layout(heights = c(1, 2.6))
ggsave(file.path(FIG_DIR, "fig2_flows_vs_tension.png"), fig2, width = 9, height = 9, dpi = 150)

## 5. Fig 3: flow rate (t) vs tension (t-1) scatter -----------------------------
sc <- melt(panel[in_reg_sample == TRUE,
                 .(cell, qtr, gap_abs_scaled_l1, msci = factor(msci_step),
                   `Position-weighted` = pw_total_rate, `Equal-weighted` = ew_total_rate)],
           id.vars = c("cell", "qtr", "gap_abs_scaled_l1", "msci"),
           variable.name = "weighting", value.name = "rate")
p3 <- ggplot(sc, aes(gap_abs_scaled_l1, rate)) +
  geom_hline(yintercept = 0, linewidth = .3, colour = "grey70") +
  geom_smooth(method = "lm", se = TRUE, colour = "grey30", linewidth = .6, fill = "grey88") +
  geom_point(aes(colour = msci, shape = msci), size = 1.9) +
  scale_colour_manual(NULL, values = c(`0` = COL_ENDINV, `1` = COL_REBAL),
                      labels = c("Other quarters", "MSCI inclusion step")) +
  scale_shape_manual(NULL, values = c(`0` = 16, `1` = 17),
                     labels = c("Other quarters", "MSCI inclusion step")) +
  scale_y_continuous(labels = percent_format(accuracy = 1)) +
  facet_grid(weighting ~ cell, scales = "free_y") +
  labs(x = "Slant gap, t-1 (gap_abs_scaled)", y = "Total flow rate, t",
       title = "Bilateral flow rates vs lagged tension, 2018Q2-2025Q1") +
  theme_bw(base_size = 11) + theme(legend.position = "top")
ggsave(file.path(FIG_DIR, "fig3_scatter_tension_flow.png"), p3, width = 9, height = 7, dpi = 150)

## 6. Fig 4: MSCI benchmark revisions (A-share inclusion path) ------------------
ash <- fread(file.path(OUTPUT_ROOT, "msci_ashare_monthly.csv"))
ash[, date := as.Date(sprintf("%08d", calc_date), "%Y%m%d")]
rev_m <- ash[ashare_iif != shift(ashare_iif, fill = 0)]              # revision months
p_iif <- ggplot(ash, aes(date, ashare_iif)) +
  geom_step(colour = COL_REBAL, linewidth = .7) +
  geom_point(data = rev_m, colour = COL_REBAL, size = 1.8) +
  geom_text(data = rev_m, aes(label = percent(ashare_iif, accuracy = .1)),
            vjust = -.8, size = 2.8, colour = "grey30") +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, .24)) +
  scale_x_date(date_breaks = "1 year", date_labels = "%Y", limits = range(ash$date)) +
  labs(x = NULL, y = "A-share inclusion factor",
       title = "MSCI benchmark revisions: China A-share inclusion",
       subtitle = "Modal standard inclusion factor of A-shares in ACWI (revision events marked)") +
  theme_bw(base_size = 11)
p_wt <- ggplot(ash, aes(date, msci_cn_wt)) +
  geom_line(colour = COL_ENDINV, linewidth = .7) +
  geom_vline(data = rev_m, aes(xintercept = date), linetype = "dashed",
             colour = "grey40", linewidth = .3) +
  scale_y_continuous(labels = percent_format(accuracy = .1)) +
  scale_x_date(date_breaks = "1 year", date_labels = "%Y", limits = range(ash$date)) +
  labs(x = NULL, y = "A-share weight in ACWI",
       caption = "Dashed lines: revision months. Weight moves with prices between revisions.") +
  theme_bw(base_size = 11)
fig4 <- p_iif / p_wt + plot_layout(heights = c(1, 1))
ggsave(file.path(FIG_DIR, "fig4_msci_benchmark_revisions.png"), fig4, width = 9, height = 6.5, dpi = 150)

cat("Figures written to", FIG_DIR, "\nTables written to", TAB_DIR, "\n")
