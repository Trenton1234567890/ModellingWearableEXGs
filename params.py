"""
Single parameter table for the model.

status:
  'decision'  - agreed design choice (Stage 1/2 specs)
  'standard'  - from a standard (clause cited)
  'derived'   - computed from other entries (formula in source column)
  'lit'       - literature anchor(s); baseline value still to be chosen
  'assumed'   - placeholder assumption; needs a citation or check
  'TBD'       - must be measured or researched before the stage that uses it
"""
import pandas as pd

ROWS = [
    # name, value, low, high, unit, stage, status, source / note
    # ---- Stage 1: requirements & budget -----------------------------------
    ("wear_days", 7, None, None, "days", 1, "decision", "Stage 1 spec"),
    ("battery_mass", 1, None, None, "g", 1, "decision", "Stage 1 spec (ExG Needs allows up to ~113 g)"),
    ("P_budget", 0.5, 0.25, 1.0, "mW", 1, "derived", "average draw at the battery: 0.1-0.15 Wh (1 g Li-ion) / 168 h = 0.6-0.9 mW, x~0.85 usable capacity, rounded down; PMU efficiency applied separately (eta_pmu)"),
    ("noise_diag", 30, None, None, "uVp-v", 1, "standard", "IEC 60601-2-25 cl. 201.12.4.106.1 (10 s, RTI)"),
    ("noise_monitor", 25, None, None, "uVp-p", 1, "assumed", "ADI monitor-grade guidance, 0.5-40 Hz; verify vs IEC 60601-2-27/-47"),
    ("cmr_test_Vcm", 10, None, None, "Vrms", 1, "standard", "IEC 60601-2-25 cl. 201.12.4.105.1 (200 pF source)"),
    ("cmr_test_maxout", 1.0, None, None, "mVp-v", 1, "standard", "10 mm at 10 mm/mV; implies ~89 dB"),
    ("dZe_compliance", 37.8, None, None, "kOhm", 1, "derived", "|51 kOhm || 47 nF| at 60 Hz"),
    ("Zin_min", 2.5, None, None, "MOhm", 1, "standard", "IEC 60601-2-25 cl. 201.12.4.103, +/-300 mV DC offset"),
    ("fs_rr", 250, None, None, "Hz", 1, "decision", "Stage 1 spec"),
    ("fs_diag", 500, None, None, "Hz", 1, "decision", "Stage 1 spec; AHA 2007 recommends >=500 S/s"),
    ("bspm_loss_max", 5, None, None, "%", 1, "decision", "Stage 1 spec (arbitrary for now)"),
    ("t_warmup_hpf", 15, None, None, "s", 1, "derived", "0.05 Hz 1st-order HPF, 4.6*tau to 1%"),
    # ---- Stage 2: geometry --------------------------------------------------
    ("torso_circ", 100, 80, 120, "cm", 2, "assumed", "adult chest circumference; sweep for sensitivity"),
    ("torso_height", 50, 40, 60, "cm", 2, "assumed", "waist/iliac to shoulder line"),
    ("sleeve_circ", 30, 25, 35, "cm", 2, "assumed", "upper arm"),
    ("sleeve_len", 25, 15, 35, "cm", 2, "assumed", "short/mid sleeve"),
    ("n_electrodes", 64, 12, 64, "-", 2, "decision", "Stage 2 spec (upper limit)"),
    ("grid_pitch", 7, None, None, "cm", 2, "derived", "front 7x6 grid over 42x38 cm"),
    ("precordial_tol", 2, None, None, "cm", 2, "assumed", "placement error that visibly alters morphology; find citation"),
    ("spares_per_site", 1, 0, 4, "-", 2, "decision", "dedicated spares per 12-lead site, 1.5 cm offset (inside tolerance)"),
    ("m_electrodes_per_adc", None, 1, 64, "-", 2, "decision", "sweep: 1, 2, 3, 4, 8, 16, N; region of interest 3-4"),
    ("n_nodes_per_area", None, 1, 64, "-", 2, "decision", "sweep: 1, 2, 4, 8, all; area = THReaD sub-mesh with one SoC orchestrator"),
    ("min_lead_spacing", 5, 3, 10, "cm", 2, "assumed", "min bipolar spacing for a usable local R-R lead; QRS amplitude grows with spacing"),
    ("chiplet_io_pads", 9, 8, 32, "-", 2, "lit", "usable IO pads per chiplet (THReaD: 8-9 IO; rest power/ground); a spec knob for future chiplets (H-15)"),
    ("router_ports", 4, None, None, "-", 2, "lit", "THReaD CICC'26: N/E/S/W 2DSPI controllers"),
    # ---- Stage 3: power (literature anchors; baselines chosen in Stage 3) ---
    ("P_afe_ch", None, 0.45, 212, "uW/ch", 3, "lit",
     "Zou'09 0.45; 2-electrode AFE'25 4.6; Dabbaghian'24 17.5 (incl. ADC+digital); Kuang'25 30.9 (excl. FPGA/XO); 44 uW ASIC'25; Warchall'19 212"),
    ("adc_fom", 48.6, None, None, "fJ/conv-step", 3, "derived", "Ji'26 SAR: 0.051 uW at 1024 S/s, ~10 ENOB"),
    ("E_tx_uwb", 88, None, None, "pJ/b", 3, "lit", "Warchall'19 UWB TX"),
    ("sample_bits", 16, 12, 24, "bit", 3, "assumed", "raw sample word on the network"),
    ("activity_data", 0.5, None, None, "-", 3, "assumed", "data-line toggle probability per bit; clock line toggles every bit"),
    ("E_tx_ble", 200, 3, 200, "nJ/b", 3, "lit", "effective radio energy per bit, swept 3-200 nJ/b: ~3 nJ/b for best-case modern low-power radios at high packing, ~200 nJ/b for Siekkinen'12 CC2540 best case (0.21-1.25 uJ/b) (P-18)"),
    ("P_tx_floor", 20, 5, 100, "uW", 3, "assumed", "BLE connection maintenance at ~1 s interval, independent of payload"),
    ("P_afe_diag", 5, 0.5, 20, "uW/ch", 3, "assumed", "diagnostic-grade channel; anchored to 4.6 uW two-electrode AFE (JSSC'25)"),
    ("P_afe_mon", 1, 0.5, 20, "uW/ch", 3, "assumed", "monitor-grade channel (R-R)"),
    ("P_afe_cots", 335, None, None, "uW/ch", 3, "lit", "ADS1292R datasheet: 335 uW/ch, 3 V, 500 SPS (reference point only)"),
    ("adc_enob", 11, None, None, "bit", 3, "assumed", "for FoM-based conversion power"),
    ("P_node_fixed", 10, 1, 50, "uW", 3, "assumed", "sensor chiplet bias/reference/clock/control when active; Dabbaghian'24 17.5 uW/AE total suggests ~10 uW non-AFE; spec case solves for it"),
    ("P_router_node", 2, 0.5, 20, "uW", 3, "assumed", "sensor-chiplet 2DSPI router idle/wake, ECG-rate design; not THReaD's 50 MHz SoC router"),
    ("P_node_off", 0.5, 0.1, 5, "uW", 3, "assumed", "gated sensor chiplet (leakage + wake logic)"),
    ("E_hop", 90, None, None, "pJ/useful bit/hop", 3, "derived", "THReaD bench link energy (P-02) used as per-hop router+pad cost; bench wiring included, slightly conservative"),
    ("E_cycle", 38, None, None, "pJ/cycle", 3, "derived", "THReaD SoC 1.88 mW / 50 MHz, no links; upper bound (includes floor share)"),
    ("W_lead", 20000, 5000, 100000, "cycles/s per lead", 3, "assumed", "filtering + QRS detection + quality per lead on an M0+-class core"),
    ("W_root", 20000, 5000, 100000, "cycles/s", 3, "assumed", "root fusion / export decision"),
    ("hr_hz", 1.2, 0.8, 3.0, "beats/s", 3, "assumed", "72 bpm"),
    ("feat_bits_beat", 48, 32, 128, "bit/beat/lead", 3, "decision", "timestamp + class + quality"),
    ("compress_ratio", 4, 2, 8, "-", 3, "decision", "ADPCM-like (SeisMote uses ADPCM)"),
    ("rr_leads", 2, 1, 4, "-", 3, "assumed", "R-R mode keeps 2 leads active for redundancy"),
    ("T_win_rr", 2, 1, 5, "s", 3, "decision", "R-R analysis window; R-R intervals 0.6-1.2 s (A-05)"),
    ("T_win_12L", 10, 2, 30, "s", 3, "decision", "12-lead capture/analysis window; 10 s standard clinical record (Cleveland Clinic) (A-05)"),
    ("n_12lead_per_day", 24, 1, 96, "1/day", 3, "assumed", "one capture per hour (plus symptom-triggered)"),
    ("T_win_bspm", 10, 10, 600, "s", 3, "decision", "BSPM capture/analysis window; <1 min ideal, up to 10 min (overnight sleep shirt) (A-05)"),
    ("bspm_analysis", "store", None, None, "-", 3, "decision", "store (buffer the whole window) | stream (beat-averaged running state) (A-14)"),
    ("stream_mem_kB_lead", 1.5, 0.5, 4, "kB/lead", 3, "assumed", "streaming state per lead: ~1 beat template + running sums (A-14)"),
    ("n_bspm_per_day", 1, 0, 4, "1/day", 3, "assumed", "on demand"),
    ("schedule", "default", None, None, "-", 3, "decision", "default (R-R + hourly 12-lead + daily BSPM) | cont12L | contBSPM | sleepBSPM (BSPM back-to-back for sleep_hours, R-R otherwise) (A-09)"),
    ("sleep_hours", 8, 4, 10, "h/day", 3, "assumed", "overnight BSPM duration for the sleepBSPM schedule (A-09)"),
    ("export", "onbody", None, None, "-", 3, "decision", "export policy for every architecture: raw | compressed | onbody (A-01)"),
    ("sram_cap_kB", 32, 8, 256, "kB", 3, "decision", "per-chiplet SRAM cap for every orchestrator incl. centralized; THReaD-class 32 kB (A-03)"),
    ("f_cap_MHz", 4, 1, 50, "MHz", 3, "assumed", "per-chiplet clock cap for low-power operation (A-04)"),
    ("analysis_mem_base_kB", 8, 4, 16, "kB", 3, "assumed", "program + state + fusion (A-05)"),
    ("buf_ratio", 1.0, 1.0, 3.0, "-", 3, "assumed", "lossless compression of the analysis buffer; lossless ECG coders reach ~2-3x (citation needed) (A-10)"),
    ("diag_lossless", False, None, None, "-", 3, "decision", "True: 12-lead buffer AND exported captures are lossless at lossless_ratio (A-13)"),
    ("lossless_ratio", 2.5, 1.5, 3.0, "-", 3, "assumed", "lossless ECG compression ratio; citation needed (A-13)"),
    ("p_abnormal", 0.05, 0.01, 0.5, "-", 3, "decision", "fraction of captures flagged abnormal and sent in full (compressed) (A-06)"),
    ("p_abnormal_bspm", 0.05, 0.0, 0.5, "-", 3, "assumed", "fraction of BSPM windows also sent in full (compressed); 0 = templates only (A-06)"),
    ("feat_bits_lead_12L", 512, 256, 2048, "bit/lead/capture", 3, "assumed", "32 measurements x 16 b per lead per 12-lead capture (A-06)"),
    ("template_s_bspm", 0.6, 0.4, 1.0, "s", 3, "assumed", "beat-averaged template length per BSPM lead (A-06)"),
    ("sram_leak_uW_kB", 0.1, 0.02, 1.0, "uW/kB", 3, "assumed", "retained SRAM leakage, 65 nm low-voltage retention; needs a citation (A-07)"),
    ("P_orch_sleep_spec", None, None, None, "uW", 3, "TBD", "spec-case orchestrator sleep floor: model output"),
    ("E_proc_beat", 0.19, None, None, "uJ/inference", 3, "lit", "Ji'26 single-beat multi-task inference"),
    ("thread_link_clk", 25, None, None, "MHz", 3, "lit", "THReaD CICC'26: 2DSPI link rate at 50 MHz chip clock"),
    ("thread_eff_rate", 9.3, 9.3, 11.4, "Mbps/link", 3, "lit", "THReaD CICC'26: normal / block transfer"),
    ("pkt_overhead", 2.7, 2.2, 2.7, "clk per useful bit", 3, "derived", "25 MHz / 9.3-11.4 Mbps (57-bit packet, 32-bit payload, arbitration deadtime)"),
    ("E_link_bit", 90, None, None, "pJ/useful bit", 3, "derived", "THReaD: (3.97-1.88) mW / 22.8 Mbps, 1.2 V, bench loading (not yarn); split into fixed + per-m once yarn C is known"),
    ("P_soc_per_MHz", 38, None, None, "uW/MHz", 3, "derived", "THReaD SoC: 1.88 mW at 50 MHz, 1.2 V, 65 nm, no links"),
    ("P_soc_1MHz_links", 300, None, None, "uW", 3, "lit", "THReaD SoC measured (T. Elliott): 0.25 mA at 1.2 V, 1 MHz, all links active"),
    ("P_soc_floor_asbuilt", 225, None, None, "uW", 3, "derived", "linear fit of all-links points (1 MHz, 0.30 mW) and (50 MHz, 3.97 mW): P = 225 uW + 75 uW/MHz * f"),
    ("P_soc_slope_links", 75, None, None, "uW/MHz", 3, "derived", "same fit; includes core, router and pad switching"),
    ("I_soc_idle_lab", 1.2, None, None, "mA", 3, "lit", "T. Elliott lab obs.: clocked idle, no links; clock and rail to confirm (likely 50 MHz, 1.2 V; paper gives 1.57 mA)"),
    ("I_soc_active_lab", 4.0, None, None, "mA", 3, "lit", "T. Elliott lab obs.: everything active; paper gives 3.3 mA at 50 MHz, 1.2 V, all links"),
    ("P_soc_sleep", None, None, None, "uW", 3, "TBD", "no sleep/retention mode characterized in THReaD as built; this becomes a chip-spec output (required floor)"),
    ("eta_pmu", 0.7, 0.5, 0.85, "-", 3, "assumed", "SCVR+LDO light-load efficiency from 3 V; scales all architectures equally to first order"),
    ("yarn_R", None, None, None, "Ohm/m", 3, "TBD", "measure conductive yarn"),
    ("yarn_C", 80, 30, 150, "pF/m", 3, "derived", "analytical: wire over skin plane, 2*pi*eps/acosh(h/a), h=0.3-0.5 mm, a=0.1-0.15 mm, eps_r~2; measure with LCR meter on 1 m yarn over a phantom"),
    ("V_link", 1.2, None, None, "V", 3, "lit", "THReaD 1.2 V communication rail"),
    # ---- Stage 4: signal quality ------------------------------------------
    ("Zcm_required_iec", 1.1, None, None, "GOhm", 4, "derived", "dZe_compliance * (28.3 Vpp / 1 mV), no DRL"),
    ("Zcm_afe", None, 0.181, 5.5, "GOhm", 4, "lit", "Kuang'25 181 MOhm@50 Hz; TDM 8-ch'22 2.29 GOhm; Dabbaghian'24 5.5 GOhm@60 Hz"),
    ("gain_mismatch", 1.0, 0.01, 2.0, "%", 4, "assumed", "max pairwise gain difference between nodes (eps ~ U(-g/2, g/2)); Dabbaghian'24: 1% -> 40 dB; ADS1292R 0.2% on-chip; calibration can go lower"),
    ("cm_suppression_drl", 40, 26.5, 40, "dB", 4, "lit", "Dabbaghian'24 DRL gain 100; Kuang'25 26.45 dB"),
    ("Ze_R_med", 2.0, 0.5, 8.0, "MOhm", 4, "assumed", "dry/textile electrode R (R||C model), lognormal median; anchors: Dabbaghian'24 1 MOhm mismatch, Xu'15 800 kOhm"),
    ("Ze_C_med", 2.2, 0.5, 10, "nF", 4, "assumed", "dry/textile electrode C, lognormal median; R||C median |Z| ~1 MOhm at 60 Hz"),
    ("Ze_sigma_ln", 0.7, 0.3, 1.0, "-", 4, "assumed", "lognormal spread (~2x) for R and C independently"),
    ("Zin_R", 5.0, 1.0, 1000, "GOhm", 4, "assumed", "AFE common-mode input resistance"),
    ("Zin_C", 5.0, 2.0, 20.0, "pF", 4, "assumed", "AFE common-mode input capacitance incl. pad/ESD (ADS1292R: 20 pF)"),
    ("C_line_body", 80, 30, 150, "pF/m", 4, "derived", "analog line to skin (= yarn_C); parallel to electrode impedance"),
    ("C_line_gnd", 25, 0, 80, "pF/m", 4, "derived", "analog line to accompanying ground yarn ~1 mm away: pi*eps/acosh(s/2a), eps_r~2; 0 = guarded/driven shield"),
    ("cmrr_amp", 100, 80, 120, "dB", 4, "lit", "intrinsic differential-amp CMRR (ADS1292R 105-120 dB)"),
    ("skew_ts", 5.0, 1.0, 20.0, "us", 4, "assumed", "timestamp + interpolation residual (pairwise max)"),
    ("skew_hw", 0.5, 0.05, 2.0, "us", 4, "assumed", "hardware sample strobe over the mesh (pairwise max)"),
    ("rej_target_diag", 89, None, None, "dB", 4, "standard", "IEC 60601-2-25 CMR test equivalent, system level incl. DRL"),
    ("rej_target_rr", 60, 40, 89, "dB", 4, "assumed", "R-R mode; verify vs IEC 60601-2-27/-47"),
    ("irn_ch_diag", 1.0, 0.4, 3.0, "uVrms", 4, "assumed", "diagnostic channel IRN, 0.05-150 Hz"),
    ("irn_ch_mon", 2.0, 0.5, 5.0, "uVrms", 4, "assumed", "monitor channel IRN, 0.67-40 Hz"),
    ("mc_trials", 400, None, None, "-", 4, "decision", "Monte Carlo trials; report 5th-percentile rejection (95% of garments pass)"),
]

COLUMNS = ["name", "value", "low", "high", "unit", "stage", "status", "source"]


def table() -> pd.DataFrame:
    return pd.DataFrame(ROWS, columns=COLUMNS).set_index("name")


def get(name):
    return table().loc[name, "value"]
