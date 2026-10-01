# Garment-Scale ECG Architecture Model

A first-order analytical model of architectures for garment-integrated ECG. It compares centralized, distributed and hierarchical (THReaD-style) designs on three things:

- **power:** sensing, routing, on-garment processing and off-body transmission;
- **signal quality:** common-mode rejection at each lead, under the IEC 60601-2-25 test and with dry electrodes;
- **on-garment compute capacity:** what each chiplet's memory allows it to analyse.

The question it answers: **for a given application, chiplet and radio, does distributing acquisition and compute across the garment beat a centralized design, and by how much?**

The model is deliberately first-order. Every number and modelling choice is logged with a status (decision / standard / literature / derived / assumed / TBD) in [`ASSUMPTIONS.md`](ASSUMPTIONS.md), and the equations are collected in [`EQUATIONS.md`](EQUATIONS.md).

---

## Architecture space

```
electrode ──analog──► sensor node (AFE+ADC for m electrodes, 2DSPI router)
sensor nodes ──digital──► area head (SoC orchestrator; one per n sensor nodes)
area heads ──digital──► root orchestrator (fusion, export decision, off-body BLE)
```

| Knob | Values |
|---|---|
| m, electrodes per ADC | 1 (active electrode), 2, 3, 4, 8, 16, N (centralized) |
| n, sensor nodes per orchestrator area | 1, 2, 4, 8, all |
| Topology | star, multidrop bus, or mesh (sensor node → head); star or mesh (head → root) |
| Layout | Mason-Likar torso or sleeve limb leads; 10 12-lead sites + spares + a 54-site grid on a torso + sleeves cylinder model |
| Export policy | raw, compressed, or on-body analysis (limited by chiplet SRAM and clock) |
| Schedule | default (R-R plus hourly 12-lead plus daily BSPM), continuous 12-lead, continuous BSPM |

---

## Repository layout

| File | Contents |
|---|---|
| `params.py` | Single parameter table: value, range, unit, stage, status and source for every parameter |
| `geometry.py` | Garment surfaces, Manhattan routing, 64+ site layout, capacitated clustering, star/bus/mesh link graphs, lead locality |
| `power.py` | Power model: mode loads, channel counting, links, orchestrators (as-built vs. spec), BLE, schedule averaging, export policies, capacity-limited on-body analysis, spec inversion |
| `sigq.py` | Signal-quality model: lead weights, per-electrode CM transfer, node gain/skew errors, Monte Carlo, IEC compliance case |
| `01_geometry_layout.ipynb` | Stage 2: layout, hierarchy, wiring primitives, hub sensitivity |
| `02_power_model.ipynb` | Stage 3: validation, power sweep, design map, breakdown, sensitivity |
| `03_signal_quality.ipynb` | Stage 4: CMR validation, gain/skew spec map, input-capacitance and guarding requirements |
| `04_onbody_processing.ipynb` | On-garment processing vs. distribution, SRAM crossover |
| `05_regime_map.ipynb` | Regime map (SRAM × analysis window) and closed-form check |
| `ASSUMPTIONS.md` | Assumptions log; newest changes first, with superseded entries kept |
| `EQUATIONS.md` | Every equation the model uses, with assumption IDs |
| `*.csv`, `*.png` | Outputs written by the notebooks |

---

## Running it

```bash
pip install -r requirements.txt
jupyter notebook          # run 01 → 05 in order; each notebook is self-contained
```

To run everything headless:

```bash
for nb in 0*.ipynb; do jupyter nbconvert --to notebook --execute --inplace "$nb"; done
```

Or use the modules directly:

```python
import geometry as geo, power as pw, sigq as sq
p = pw.P(export="onbody", schedule="cont12L", sram_cap_kB=32)     # any parameter can be overridden
g = geo.Garment(); sites = geo.build_layout(g, "ML", spares_per_site=1)
D = geo.dist_matrix(g, sites)
pt = geo.build_point(g, sites, D, m=4, n=4, intra="mesh", inter="mesh")
print(pw.average_power(sites, D, pt, p, case="spec", orch_floor_w=10e-6)["total"] * 1e6, "uW")
names, rej = sq.lead_rejection(sites, D, pt, "12L", p, case="realistic", sync="ts")
print(sq.mode_metric(rej, "12L", p))
```

---

## Headline results (first pass; see each notebook's Findings)

1. **Validation.**
   - Power: reproduces Warchall '19's UWB transmit power to +0.6% (predictive check) and Kuang/Dabbaghian accounting to within 0.3%.
   - Signal quality: reproduces the textbook potential-divider result exactly; conservative by 3–5 dB against Dabbaghian '24.
2. **Power (default schedule).**
   - Textile interconnect is negligible (≤ 6 µW) unless high-channel raw data streams continuously.
   - Fixed per-chiplet floors decide the ranking: centralized needs about 102 µW, against about 205 µW for m = 4 with 5 SoCs at a 10 µW orchestrator floor.
   - THReaD as built (225 µW floor) fits the 0.5 mW budget only as a single SoC.
3. **Signal quality (dry electrodes).**
   - A centralized design needs guarded analog lines to meet 89 dB.
   - Distributed designs need ≤ ~3 pF AFE input capacitance, ≤ 0.35% node gain matching and ≤ ~10 µs timestamp sync. m = 4 is the lowest-power distributed design that passes.
4. **On-garment processing is the dominant lever.**
   - For continuous 12-lead: raw streaming is 18.4 mW, compressed streaming 4.7 mW, and on-body analysis 0.55–1.1 mW.
5. **Regime map: distribution wins when no single chiplet can hold the analysis.**
   - A head with L leads fits if M_base + L·T/r ≤ S. The winner is the fewest-SoC architecture that fits; this matches 220 of 220 sweep cells.
   - At 32 kB with a 10 s window, m = 4, n = 1 needs 1.07 mW against 4.7 mW centralized (4.4×).
   - At ≥ 96 kB, centralized wins again.

### Known weak points
- SRAM retention leakage per kB and lossless ECG compression ratios are uncited (A-07, A-10).
- The analysis window per application is not yet tied to clinical requirements.
- The AFE power model is not coupled to the input-capacitance requirement.
- Sync, calibration and guard-driver power are not modelled.
- Motion artifacts are scoped out.
- The R-R rejection target (60 dB) is a placeholder.

---

## Key references for parameters
- Chen et al., "THReaD: A 22.8 Mbps/node Two-dimensional Hierarchical Reconfigurable and Distributed Network for E-textiles," IEEE CICC 2026.
- Warchall et al., distributed FM-ADC ExG platform, ISSCC 2019.
- Dabbaghian et al., 17.5 µW/ch active electrode with in-channel CMRR boost, IEEE TBCAS 2024.
- Kuang et al., multi-channel CD-FDM direct-digital front-end, IEEE TCAS-II 2025.
- Ji et al., single-lead ECG SoC with 1.04 s latency, IEEE JSSC 2026.
- Rossi et al., SeisMote, Sensors 2020.
- Siekkinen et al., "How Low Energy is Bluetooth Low Energy?", 2012.
- IEC 60601-2-25:2011; Texas Instruments ADS1292R datasheet.
