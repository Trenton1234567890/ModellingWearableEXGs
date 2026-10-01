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
    ("P_budget", 0.5, 0.25, 1.0, "mW", 1, "derived", "0.1-0.15 Wh (1 g Li-ion) / 168 h, derated for usable capacity + regulator"),
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
    ("router_ports", 4, None, None, "-", 2, "lit", "THReaD CICC'26: N/E/S/W 2DSPI controllers"),
    # ---- Stage 3: power (literature anchors; baselines chosen in Stage 3) ---
    ("P_afe_ch", None, 0.45, 212, "uW/ch", 3, "lit",
     "Zou'09 0.45; 2-electrode AFE'25 4.6; Dabbaghian'24 17.5 (incl. ADC+digital); Kuang'25 30.9 (excl. FPGA/XO); 44 uW ASIC'25; Warchall'19 212"),
    ("adc_fom", 48.6, None, None, "fJ/conv-step", 3, "derived", "Ji'26 SAR: 0.051 uW at 1024 S/s, ~10 ENOB"),
    ("E_tx_uwb", 88, None, None, "pJ/b", 3, "lit", "Warchall'19 UWB TX"),
    ("E_tx_ble", None, None, None, "nJ/b", 3, "TBD", "effective BLE energy/bit incl. connection overhead"),
    ("E_proc_beat", 0.19, None, None, "uJ/inference", 3, "lit", "Ji'26 single-beat multi-task inference"),
    ("thread_link_clk", 25, None, None, "MHz", 3, "lit", "THReaD CICC'26: 2DSPI link rate at 50 MHz chip clock"),
    ("thread_eff_rate", 9.3, 9.3, 11.4, "Mbps/link", 3, "lit", "THReaD CICC'26: normal / block transfer"),
    ("pkt_overhead", 2.7, 2.2, 2.7, "clk per useful bit", 3, "derived", "25 MHz / 9.3-11.4 Mbps (57-bit packet, 32-bit payload, arbitration deadtime)"),
    ("E_link_bit", 90, None, None, "pJ/useful bit", 3, "derived", "THReaD: (3.97-1.88) mW / 22.8 Mbps, 1.2 V, bench loading (not yarn); split into fixed + per-m once yarn C is known"),
    ("P_soc_per_MHz", 38, None, None, "uW/MHz", 3, "derived", "THReaD SoC: 1.88 mW at 50 MHz, 1.2 V, 65 nm, no links; leakage floor from Fig. 6a TBD"),
    ("P_router_idle", None, None, None, "uW", 3, "TBD", "2DSPI router idle/wake power; first-order because links run at <0.5% duty for ECG"),
    ("eta_pmu", None, None, None, "-", 3, "TBD", "SCVR+LDO efficiency from 3 V; THReaD: 4.2x lower input power vs LDO-only"),
    ("yarn_R", None, None, None, "Ohm/m", 3, "TBD", "measure conductive yarn"),
    ("yarn_C", None, None, None, "pF/m", 3, "TBD", "measure; also decide coupling to body vs ground"),
    ("V_link", None, None, None, "V", 3, "TBD", "digital link swing"),
    ("P_node_off", None, None, None, "uW", 3, "TBD", "gated node leakage + retention"),
    ("P_node_fixed", None, None, None, "uW", 3, "TBD", "per-node overhead: bias, clock, control"),
    # ---- Stage 4: signal quality ------------------------------------------
    ("Zcm_required_iec", 1.1, None, None, "GOhm", 4, "derived", "dZe_compliance * (28.3 Vpp / 1 mV), no DRL"),
    ("Zcm_afe", None, 0.181, 5.5, "GOhm", 4, "lit", "Kuang'25 181 MOhm@50 Hz; TDM 8-ch'22 2.29 GOhm; Dabbaghian'24 5.5 GOhm@60 Hz"),
    ("dZe_realistic", None, None, None, "MOhm", 4, "TBD", "dry/textile electrode mismatch, multi-day"),
    ("gain_mismatch", 1.0, 0.1, 1.0, "%", 4, "assumed", "Dabbaghian'24: 1% -> 40 dB for digital subtraction"),
    ("skew", None, None, None, "us", 4, "TBD", "depends on sync scheme; <=94 ns needed for 89 dB with no suppression"),
    ("cm_suppression_drl", 40, 26.5, 40, "dB", 4, "lit", "Dabbaghian'24 DRL gain 100; Kuang'25 26.45 dB"),
    ("Vcm_realistic", None, None, None, "Vrms", 4, "TBD", "body CM from mains in daily wear"),
]

COLUMNS = ["name", "value", "low", "high", "unit", "stage", "status", "source"]


def table() -> pd.DataFrame:
    return pd.DataFrame(ROWS, columns=COLUMNS).set_index("name")


def get(name):
    return table().loc[name, "value"]