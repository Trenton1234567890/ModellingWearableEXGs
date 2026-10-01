# Model Assumptions Log

Every assumption the architecture model makes, however small. The newest changes are listed first. When an assumption changes, it moves to **Superseded** together with its replacement and the date. IDs never change, so papers, notes and code can refer to them.

Status tags: **[decision]** agreed design choice · **[standard]** from a standard · **[lit]** from a paper or measurement · **[derived]** computed from other entries · **[assumed]** placeholder that still needs a citation or check · **[TBD]** open; must be filled before the stage that uses it.

The parameter values live in `ecg_arch_model/params.py`; this log records the reasoning and the history.

---

## Recent changes (newest first)

| Date | ID | Change |
|---|---|---|
| 2026-10-01 | A-10, A-11 | Added a lossless buffer-compression knob r (default 1, swept 1–3). Added the closed-form regime rule; it matches 220 of 220 sweep cells. |
| 2026-10-01 | A-01 – A-09 | **On-garment processing added (user request).** Every architecture now uses the same export policy (raw, compressed or onbody). Whether a given orchestrator can do the analysis depends on per-chiplet SRAM (32 kB) and clock (4 MHz) caps; if it can't, that head falls back to compressed streaming. Lead assignment uses a WCT broadcast to area heads. Retained-SRAM leakage is added to every orchestrator floor. Two continuous schedules were added. |
| 2026-10-01 | A-08 | **Bug fix.** Compressed and raw capture streams were previously transmitted during the 15 s warm-up as well as the capture, which inflated TX about 2.5× for captures. Battery TX in the default schedule drops from 87 to 62 µW; Stage 3 numbers were re-run. |
| 2026-10-01 | X-06 | Superseded by A-01: export is now a policy shared by all architectures, not fixed per mode. |
| 2026-10-01 | Q-09 – Q-20 | **Stage 4 signal-quality model built.** CM conversion at each lead is computed from lead weights, per-electrode CM transfer (electrode Z, line-to-body and line-to-ground C, AFE input impedance), and per-node gain and skew errors. The realistic case is Monte Carlo at the 5th percentile. Sync is a 3-level knob. The R-R target is 60 dB. |
| 2026-10-01 | Q-03 | **Resolved.** Line capacitance is split: 80 pF/m line-to-body (in parallel with the electrode) and 25 pF/m line-to-ground (from the ground yarn running alongside), with 0 meaning a guarded line. |
| 2026-10-01 | Q-04 | Gain mismatch is now the maximum pairwise difference between nodes, with ε ~ U(−g/2, g/2). The range is widened to 0.01–2% to cover calibration. |
| 2026-10-01 | V-02 | Validation result: the textbook divider is reproduced exactly. Dabbaghian is over-predicted by 3–5 dB (8–10 dB against < 5 dB reported). |
| 2026-10-01 | Q-07 | Updated from the model: cross-node 12-lead needs skew ≲ 10 µs and gain matching ≲ 0.35% (with 40 dB DRL, a 2 pF AFE and dry electrodes). |
| 2026-09-30 | H-10 – H-14 | **Stage 3 power model built.** Channels are counted differentially per node: (k − 1) per node, plus 1 anchor channel when leads span nodes (user decision). Sensor chiplets stream raw data to their head. Leads within one area are formed at its head; leads spanning areas, including the 12-lead and BSPM, are formed at the root. Spares stay off. |
| 2026-09-30 | P-20 – P-30 | Stage 3 parameters added: AFE grades (5 µW/ch diagnostic, 1 µW/ch monitor); ADS1292R at 335 µW/ch as the COTS reference; sensor-node overhead 10 µW, router 2 µW, off-state 0.5 µW; per-hop energy 90 pJ; 38 pJ per SoC cycle; 20k cycles/s per lead; BLE at 200 nJ/b plus a 20 µW connection floor. |
| 2026-09-30 | X-06 – X-08 | Export rates: features at 48 b per beat per lead, and 4:1 compression. Schedule: a 12-lead capture every hour and one BSPM capture per day, each with 15 s of warm-up. A 10 µW orchestrator floor is used for illustration only. |
| 2026-09-30 | V-01 | Validation restated: a predictive check (Warchall's UWB TX), accounting checks (Warchall, Kuang, Dabbaghian), and a plausibility check (SeisMote). The original wording is superseded (S-08). |
| 2026-09-30 | Q-04 | Gain-mismatch range now has a literature anchor: the ADS1292R datasheet gives 0.2% gain match between channels. |
| 2026-09-30 | B-01, B-02 | **Correction.** The 0.5 mW budget is the average draw at the battery. It is derated for usable capacity only. PMU efficiency (B-02) is applied separately, so delivered power ≈ 0.7 × 0.5 = 350 µW. Earlier wording had derated for regulator losses twice. |
| 2026-09-30 | P-10 – P-13 | The THReaD SoC as built has no characterized sleep mode. Lab observations: about 1.2 mA at clocked idle and about 4 mA with everything active (clock and rail still to confirm). The static floor sits between 100 and 225 µW. The sleep floor becomes a chip-spec output. |
| 2026-09-30 | P-09 | THReaD SoC at 1 MHz with all links active is 0.25 mA at 1.2 V, about 300 µW (T. Elliott). A two-point fit gives P ≈ 225 µW + 75 µW/MHz. |
| 2026-09-30 | P-05, B-02 | Yarn C set to 80 pF/m (range 30–150) from an analytical estimate. PMU efficiency set to 0.7 (range 0.5–0.85). |
| 2026-09-30 | P-06, P-07, P-08 | Added: 16-bit raw samples, data-line activity 0.5, and the clock line toggling on every bit, all on a 1.2 V link rail. |
| 2026-09-30 | H-01 – H-09 | The architecture is now a THReaD-style hierarchy: sensor node (m electrodes per ADC) → area (n nodes, SoC orchestrator) → root orchestrator. This replaces the single k knob (superseded S-01). |
| 2026-09-30 | G-09 | Spares are a parameter: 1 per 12-lead site by default, each 1.5 cm away. This replaces "spares = nearest grid site" (superseded S-02). The 64-electrode figure is now the grid, not a cap on the total. |
| 2026-09-30 | G-02 | Two sleeve cylinders were added (30 cm around, 25 cm long). |

---

## Active assumptions

### M — Method and scope
| ID | Assumption | Status |
|---|---|---|
| M-01 | First-order only. A term is included only if it could change which architecture wins for at least one application class. | [decision] |
| M-02 | Motion artifacts are modelled as electrode availability, not as a signal. Each site gets a level (low/med/high) for each activity state (rest, walking, arm movement). A lead is usable only when both of its electrodes are at or below the application's tolerated level. Motion counts as a transient fault. | [decision] |
| M-03 | Mains pickup on analog yarn is handled as a design rule (a maximum analog run length), not as a model term. | [decision] |
| M-04 | Wires are insulated and may cross, as close to perpendicular as possible. Crosstalk at crossings is ignored. | [decision] |
| M-05 | Excluded: clock-distribution power, energy harvesting, wash durability, detection-accuracy mapping. Duty cycling appears only as the SoC sleep floor (P-12) and the mode schedule (X-02). | [decision] |
| M-06 | Deferred (second-order): partial cancellation of correlated motion artifacts in short local leads; noise summing in shared FDM/TDM paths; mode-switch transients beyond one warm-up time (X-04). | [decision] |
| M-07 | Faults: single faults only, counted deterministically (no probabilities for now). Fault probabilities can come from the MWSCAS Fallback Protocols paper, which isn't in the project yet. | [decision] |
| M-08 | Mains frequency is 60 Hz for every calculation that depends on frequency. | [assumed] |
| M-09 | Model tooling is a Python notebook plus modules, with every parameter in one table (`params.py`). | [decision] |

### R — Requirements by application class
| ID | Assumption | Status |
|---|---|---|
| R-01 | Three application classes: R-R rhythm, 12-lead morphology/ST, and BSPM. All three are in the first pass. | [decision] |
| R-02 | R-R: basis is IEC 60601-2-27 (monitoring); bandwidth 0.67–40 Hz. | [standard] |
| R-03 | R-R noise ≈ 25 µVp-p over 0.5–40 Hz. This comes from ADI monitor-grade guidance and still needs checking against IEC 60601-2-27/-47. | [assumed] |
| R-04 | R-R: sampling ≥ 250 Hz; at least one usable lead; tolerates a medium motion-artifact level. | [decision] |
| R-05 | 12-lead: basis is IEC 60601-2-25; bandwidth 0.05–150 Hz. | [standard] |
| R-06 | 12-lead noise ≤ 30 µV peak-to-valley over 10 s, referred to input (cl. 201.12.4.106.1). | [standard] |
| R-07 | 12-lead common-mode rejection: 10 Vrms at mains through 200 pF, with 51 kΩ ∥ 47 nF on each electrode, must give ≤ 1 mV p-v at the output (≈ 89 dB) (cl. 201.12.4.105.1). | [standard] |
| R-08 | 12-lead input impedance ≥ 2.5 MΩ over a ±300 mV DC offset (cl. 201.12.4.103). | [standard] |
| R-09 | 12-lead: sampling ≥ 500 Hz. | [decision] |
| R-10 | 12-lead fault policy: losing any lead is a failure, because the clinical format is standardized. Spares within tolerance may substitute. | [decision] |
| R-11 | 12-lead tolerates only a low motion-artifact level. | [decision] |
| R-12 | BSPM uses the same electrical requirements as 12-lead, with simultaneous sampling. It tolerates losing ≤ 5% of electrodes, recovered by interpolation. The 5% is arbitrary for now. | [decision] |
| R-13 | The IEC 60601-2-47 (ambulatory) numerical clauses are not yet verified; they need the full text via UVA. | [TBD] |
| R-14 | Garment 12-lead uses Mason-Likar torso placement. The resulting axis shift against a standard 12-lead is noted as a limitation. | [decision] |

### B — Energy budget and power delivery
| ID | Assumption | Status |
|---|---|---|
| B-01 | 7 days of wear on a ~1 g Li-ion cell. Energy is 0.1–0.15 Wh (about 100–150 Wh/kg). Over 168 h that is 0.6–0.9 mW; ×0.85 for usable capacity gives about 0.5–0.75 mW. **The budget is 0.5 mW average at the battery**, swept 0.25–1 mW. This is deliberately tighter than the ExG Needs ceiling of ~113 g. | [derived] |
| B-02 | PMU (SCVR + LDO from 3 V) light-load efficiency is 0.7, swept 0.5–0.85. It is one factor applied to all on-body loads, so to first order it doesn't change the ranking of architectures. | [assumed] |
| B-03 | A single 3 V supply feeds distributed PMU chiplets, as in THReaD. The supply bus is a single point of failure common to all architectures, so it doesn't differentiate them. Per-node energy storage is out of scope. | [decision] |

### Q — Signal quality
| ID | Assumption | Status |
|---|---|---|
| Q-01 | Lead residual ≈ V_cm / (1 + G_supp) × (ΔZ_e/Z_cm + ΔG/G + ωΔt) + IRN. The mismatch terms add in the worst case, and the skew term applies only to leads formed across nodes. | [decision] |
| Q-02 | Two electrode-imbalance cases. Compliance: ΔZ_e = the IEC value of 37.8 kΩ at 60 Hz. Realistic: dry/textile mismatch in the MΩ range (value still to find). | [decision] / [TBD] |
| Q-03 | Analog line capacitance is split in two. Line-to-body is 80 pF/m (the yarn_C estimate) and sits in parallel with the electrode impedance. Line-to-ground is 25 pF/m (range 0–80), from a ground yarn about 1 mm away: πε/acosh(s/2a) with εr ≈ 2. It adds to the AFE input C and lowers Z_cm; 0 means a guarded or driven-shield line. | [derived] |
| Q-04 | Gain mismatch g is the maximum pairwise gain difference between nodes, with ε_n ~ U(−g/2, g/2). Default is 1% (range 0.01–2%). Dabbaghian '24 gives 40 dB for 1%; the ADS1292R gives 0.2% between channels on one chip; calibration can go lower. | [assumed] / [lit] |
| Q-05 | CM suppression (DRL or shared CM) is 40 dB (range 26.5–40), from Dabbaghian '24 and Kuang '25. | [lit] |
| Q-06 | Leads formed across nodes always use digital subtraction. | [decision] |
| Q-07 | Sample alignment for cross-node 12-lead: the model gives ≲ 10 µs, with gain matching ≲ 0.35% (at 40 dB DRL, a 2 pF AFE input and dry electrodes). THReaD provides no network time sync, so timestamp sync with interpolation is a chip-spec requirement. | [derived] |
| Q-08 | Not needed. The requirement is expressed as system rejection (DRL credit + conversion) against the IEC-equivalent 89 dB, so the absolute V_cm cancels out. | [decision] |
| Q-09 | Each lead is a weight vector over electrodes. 12-lead uses standard Einthoven, Goldberger and WCT weights; BSPM is each measuring electrode against the WCT; R-R uses the H-13 pairs. | [decision] |
| Q-10 | CM transfer per electrode: h = Z_cm/(Z_src + Z_cm). Z_src = Z_e ∥ line-to-body C × L. Z_cm = R_in ∥ (C_in + line-to-ground C × L). L is the analog run from the electrode to its node's AFE, using Manhattan distance. | [decision] |
| Q-11 | Conversion: c = \|Σ w·(1+ε)·e^(−jωτ)·h\| + 1/CMRR_amp, with a worst-case add of the amplifier term. Electrodes on one node share ε and τ. | [decision] |
| Q-12 | Dry/textile electrodes are modelled as R ∥ C, with R lognormal (median 2 MΩ, range 0.5–8) and C lognormal (median 2.2 nF, range 0.5–10), each with σ_ln = 0.7. That gives a median \|Z\| of about 1 MΩ at 60 Hz. Anchors: 1 MΩ mismatch in Dabbaghian '24, 800 kΩ in Xu '15. | [assumed] |
| Q-13 | Compliance case: the IEC 51 kΩ ∥ 47 nF imbalance is placed on each electrode of a lead in turn, with the others ideal, and the worst case is kept. | [decision] |
| Q-14 | AFE CM input impedance: R_in = 5 GΩ (range 1–1000), C_in = 5 pF baseline (range 2–20; the ADS1292R is 20 pF). 2 pF is used as the "spec AFE" scenario. | [assumed] |
| Q-15 | The intrinsic CMRR of the differential amplifier is 100 dB (range 80–120; the ADS1292R is 105–120). | [lit] |
| Q-16 | Sync levels: none, with τ ~ U(0, 1/fs); timestamp + interpolation, ±2.5 µs (5 µs pairwise); hardware strobe, ±0.25 µs (0.5 µs pairwise). | [assumed] |
| Q-17 | Targets: 89 dB system rejection for 12-lead and BSPM, which is the IEC 60601-2-25 CMR-test equivalent including DRL. R-R uses 60 dB, a placeholder until IEC 60601-2-27/-47 is checked. | [standard] / [assumed] |
| Q-18 | Pass metrics, each at the 5th percentile over 400 Monte Carlo trials (so 95% of garments pass): 12-lead uses the worst lead; BSPM requires ≥ 95% of leads to pass; R-R uses the best of its leads. | [decision] |
| Q-19 | Mains is a single 60 Hz tone. The DRL credit is a flat 40 dB in every architecture, assuming one global DRL loop. Its latency and stability in distributed systems are not modelled. | [assumed] |
| Q-20 | Noise check: channel IRN is 1 µVrms (diagnostic) and 2 µVrms (monitor). Lead noise = 6.6 × IRN × √(Σw²) p-p. | [assumed] |

### G — Garment geometry and layout
| ID | Assumption | Status |
|---|---|---|
| G-01 | The torso is an unwrapped cylinder, 100 cm around (80–120) and 50 cm tall (40–60). x = 0 at the sternum, +x toward the patient's left; y = 0 at the waist/iliac level. | [assumed] |
| G-02 | Sleeves are cylinders 30 cm around (25–35) and 25 cm long (15–35). They join the torso at the point (±C/4, H) ↔ (u = 0, v = 0). | [assumed] |
| G-03 | Routing is Manhattan along each surface (warp and weft, like THReaD's XY routing), wrapping around at the back seam. Sleeve routes pass through the shoulder junction. Shoulder-to-shoulder is C/2 = 50 cm across the front. | [decision] |
| G-04 | 12-lead coordinates (cm), all approximate landmarks: RA (−12, 45), LA (12, 45), LL (12, 5), RL (−12, 5), V1 (−2.5, 34), V2 (2.5, 34), V3 (5.75, 32), V4 (9.5, 30), V5 (17, 30), V6 (25, 30). | [assumed] |
| G-05 | Sleeve variant: RA and LA are at the mid upper arm, anterior (u = 0, v = 12 cm). LL and RL stay on the torso in both variants. | [decision] |
| G-06 | Front grid: a 7 × 6 candidate grid (x −21…21, y 6…44), minus the 4 points nearest the 12-lead sites, leaving 38. Back grid: 4 × 4 centred on the back midline (x = C/2 ± 6, ± 18; y 8…42), 16 sites. Pitch is about 7 cm. The grid is identical across variants and spare counts. | [decision] |
| G-07 | Precordial placement tolerance is 2 cm (the error that visibly alters morphology). A citation is still needed. | [assumed] |
| G-08 | Minimum spacing for a usable local bipolar R-R lead is 5 cm (range 3–10). | [assumed] |
| G-09 | Spares: 1 per 12-lead site by default (range 0–4), offset 1.5 cm, lateral first and then vertical, all inside the tolerance. | [decision] |
| G-10 | Electrodes are passive. The AFE sits at the sensor node, except at m = 1, which is an active electrode. | [decision] |

### H — Architecture hierarchy
| ID | Assumption | Status |
|---|---|---|
| H-01 | A sensor node is an ExG chiplet: AFE + ADC for m electrodes plus a 2DSPI router. It sits at the medoid electrode site of its cluster. m ∈ {1, 2, 3, 4, 8, 16, N}; the region of interest is 3–4. | [decision] |
| H-02 | Electrodes are grouped into nodes by capacitated k-medoids on the surface metric, with pairwise swap refinement for m ≤ 8. There are ⌈N/m⌉ nodes of ≤ m electrodes each. | [decision] |
| H-03 | An area (compute neighbourhood) is a THReaD sub-mesh of ≤ n sensor nodes with one SoC orchestrator. The SoC is co-located with the area's medoid node. n ∈ {1, 2, 4, 8, all}. | [decision] |
| H-04 | Orchestrators work in a hierarchy. Area heads form leads within their area and run local analysis and quality checks. The root fuses across areas, forms leads that span areas (including the 12-lead's WCT), and decides what to transmit. | [decision] |
| H-05 | The root is the area head nearest the reference hub point, the L1-median of all sites: (0, 29) with 0 spares, (3, 29) with 1 spare. The root hosts the off-body TX. The hub position is swept as a sensitivity check. | [decision] |
| H-06 | Node-to-head topology is star, multidrop bus, or mesh. Head-to-root topology is star or mesh. | [decision] |
| H-07 | Mesh graph: MST plus nearest neighbours, up to 4 ports per node (THReaD N/E/S/W). Routes take the shortest path by length. | [decision] |
| H-08 | Bus: a greedy nearest-neighbour chain from the sink. It is multidrop, so every bit charges the whole bus length. | [decision] |
| H-09 | Special-case comparison points: an analog link with the ADC at the gateway (Warchall); per-node radios as a link with only a fixed cost per bit (SeisMote). | [decision] |
| H-10 | **Channel counting is differential per node.** A node with k measuring electrodes has k − 1 differential channels, plus 1 anchor channel referenced to the body/DRL when the mode's leads span more than one node. A centralized 12-lead has 8 channels. The RL (DRL) driver counts as one AFE channel-equivalent. At m = 1, each active electrode is one single-ended channel against a shared reference. | [decision] |
| H-11 | Sensor chiplets have no processor. Each active node streams raw samples to its area head. A lead is formed at the head when all its electrodes are in one area, and at the root otherwise, with the heads forwarding raw data. | [decision] |
| H-12 | In 12-lead and BSPM modes, all leads are formed at the root, unless every active node sits in a single area, in which case they are formed at that area's head. | [decision] |
| H-13 | R-R mode activates `rr_leads` (default 2) local leads, on the nodes nearest the root whose electrodes are ≥ 5 cm apart. If no node can form a local lead (m = 1), it uses pairs of active-electrode nodes nearest the root that are ≥ 5 cm apart. Each local lead is one differential channel. | [decision] |
| H-14 | Spares are powered off (counted at off-state power) unless substituting. Substitution events are not yet modelled in the power model. | [decision] |

### P — Power parameters
| ID | Assumption | Status |
|---|---|---|
| P-01 | Link energy per useful bit per hop = E_hop + E'·L. | [decision] |
| P-02 | THReaD bench link energy ≈ 90 pJ per useful bit at 1.2 V, from (3.97 − 1.88) mW / 22.8 Mbps. It reflects bench loading, not yarn. | [derived] |
| P-03 | Protocol overhead is 2.2–2.7 link clocks per useful bit: a 57-bit packet carrying a 32-bit payload, plus arbitration deadtime; block transfer is the lower end. | [derived] |
| P-04 | The network has plenty of bandwidth for ECG (≤ 0.8 Mbps raw for the whole garment, versus 9.3 Mbps per link). Link power is set by energy per bit and idle floors, not by throughput. | [derived] |
| P-05 | Yarn C = 80 pF/m (range 30–150), from treating each wire as a line over a skin plane: 2πε/acosh(h/a) with h = 0.3–0.5 mm, a = 0.1–0.15 mm, εr ≈ 2. It still needs an LCR measurement on 1 m of yarn over a phantom. | [derived] |
| P-06 | Link swing is 1.2 V (THReaD's communication rail). | [lit] |
| P-07 | Data-line activity is 0.5, and the clock line toggles every bit. That gives about 58 pJ/bit/m on the data line and 115 pJ/bit/m on the clock line at 80 pF/m. | [assumed] |
| P-08 | Raw samples are 16-bit words on the network (range 12–24). | [assumed] |
| P-09 | THReaD SoC measured at 0.25 mA, 1.2 V, 1 MHz, all links active: about 300 µW (T. Elliott). | [lit] |
| P-10 | THReaD SoC power ≈ 225 µW + 75 µW/MHz × f, from a two-point linear fit of the all-links data (1 MHz and 50 MHz). This fit is fragile. | [derived] |
| P-11 | Lab observations: about 1.2 mA at clocked idle and about 4 mA with everything active. Clock and rail are unconfirmed (probably 50 MHz, 1.2 V; the paper gives 1.57 mA and 3.3 mA). | [lit] |
| P-12 | As built, the SoC has no characterized sleep mode. The static floor band is 100–225 µW until a low-clock sweep (100 kHz, 250 kHz, 1 MHz, links idle) separates it. In the spec case, the sleep floor and wake energy are model outputs. | [assumed] / [TBD] |
| P-13 | THReaD SoC at 50 MHz, 1.2 V, no links: 1.88 mW, about 38 µW/MHz. | [lit] |
| P-14 | ADC figure of merit is 48.6 fJ/conversion-step (Ji '26 SAR). That puts conversion at about 0.1 µW for 12 bits at 500 S/s, so per-ADC cost is dominated by overhead (reference, bias, clock, serializer), not by conversion. | [derived] |
| P-15 | AFE power per channel ranges 0.45–212 µW across the literature. Baselines are set in P-20 and P-21. | [lit] |
| P-16 | On-node processing energy is anchored to Ji '26 at 0.19 µJ per beat inference. | [lit] |
| P-17 | Superseded by P-24. | — |
| P-18 | Off-body TX: UWB is 88 pJ/b (Warchall '19). BLE is 200 nJ/b (range 50–1250). That is the best case from Siekkinen '12 on the CC2540 (100–600 kB/J, or 0.21–1.25 µJ/bit); modern SoCs are likely lower. | [lit] |
| P-19 | Raw 12-lead traffic to the root is about 80 kbps (10 channels × 500 S/s × 16 bits). | [derived] |
| P-20 | Diagnostic-grade AFE is 5 µW per channel (range 0.5–20), anchored to the 4.6 µW two-electrode AFE (JSSC '25). It is used for 12-lead and BSPM. | [assumed] |
| P-21 | Monitor-grade AFE is 1 µW per channel (range 0.5–20). It is used for R-R. | [assumed] |
| P-22 | COTS reference: the ADS1292R datasheet gives 335 µW per channel at 3 V and 500 SPS, including its ADC and digital. It is used only as a comparison point. | [lit] |
| P-23 | ADC ENOB is 11 bits, used for the FoM-based conversion power (about 0.05 µW/ch at 500 S/s). | [assumed] |
| P-24 | Sensor chiplet: active fixed overhead 10 µW (range 1–50), from Dabbaghian's 17.5 µW/AE total, which implies about 10 µW that is not AFE. Router idle/wake 2 µW (range 0.5–20), assuming a router designed for ECG rates rather than THReaD's 50 MHz SoC router. Off-state 0.5 µW (range 0.1–5). A single-node architecture has no router. In the spec case, these limits are model outputs. | [assumed] |
| P-25 | Per-hop router and pad energy is 90 pJ per useful bit (P-02; bench wiring included, so slightly conservative). Yarn energy is added separately, at 467 pJ per useful bit per metre (overhead × (0.5·CV² + CV²) at 80 pF/m and 1.2 V). | [derived] |
| P-26 | SoC compute energy is 38 pJ/cycle (P-13; an upper bound because it includes a share of the floor). | [derived] |
| P-27 | Workload: 20k cycles/s per lead processed (range 5k–100k; filtering, QRS detection, quality) plus 20k cycles/s of root fusion. | [assumed] |
| P-28 | As-built orchestrators run at the 225 µW floor continuously in every mode, with no sleep. In the spec case the floor per SoC is the unknown solved for. | [decision] |
| P-29 | BLE connection-maintenance floor is 20 µW (range 5–100), independent of payload. | [assumed] |
| P-30 | Off-body TX happens only at the root. | [decision] |

### X — Modes and schedule
| ID | Assumption | Status |
|---|---|---|
| X-01 | One superset garment serves every application class through modes. Each mode is an active electrode subset plus an export level. | [decision] |
| X-02 | Example schedule: R-R continuous using the best available pair; a 10 s 12-lead capture triggered by rest, a symptom or a timer; BSPM on demand. Average power is the time-weighted sum over modes. | [decision] |
| X-03 | Off-state power per node is not yet set. | [TBD] |
| X-04 | Warm-up per mode switch is about 15 s: a 0.05 Hz first-order high-pass takes 4.6τ to settle to 1%, unless the front end has fast-settle. | [derived] |
| X-05 | The interconnect and hub must be sized for the largest mode. | [decision] |
| X-06 | Export levels: R-R sends one fused feature stream at 48 b per beat (heart rate 1.2 Hz, range 0.8–3). 12-lead streams the 8 independent leads, compressed 4:1, during the capture. BSPM streams all measuring channels, compressed 4:1. | [decision] / [assumed] |
| X-07 | Schedule: 24 12-lead captures a day (range 1–96) of 10 s each plus 15 s of warm-up; 1 BSPM capture a day of 10 s plus 15 s of warm-up; R-R the rest of the time (99.28%). R-R is not counted separately during captures. | [assumed] |
| X-08 | A 10 µW orchestrator floor is used only to illustrate the breakdown and the tornado plot. It is not a measured value. | [assumed] |

### A — On-garment analysis and export
| ID | Assumption | Status |
|---|---|---|
| A-01 | Export policy is the same for every architecture. raw: stream everything unprocessed (the prior-work baseline). compressed: R-R features plus 4:1 capture streams. onbody (default): R-R features, plus capture analysis wherever capacity allows. | [decision] |
| A-02 | On-body analysis of a capture outputs, per orchestrator that fits: 12-lead, 512 b of features per lead reported; BSPM, a beat-averaged template per lead (0.6 s × fs × 16 b). Abnormal captures are additionally sent in full (compressed). An orchestrator that doesn't fit streams its leads compressed instead (per-head fallback). | [decision] / [assumed] |
| A-03 | Every orchestrator chiplet, including the centralized one, has an SRAM cap of 32 kB (THReaD class; swept 8–256 kB). A puck-sized hub with no cap is not allowed, following the CCI proposal's form factor. | [decision] |
| A-04 | Every orchestrator chiplet has a 4 MHz clock cap (range 1–50) for low-power operation. In practice memory binds first. | [assumed] |
| A-05 | Analysis memory is 10 kB per independent lead (a 10 s window × 500 S/s × 16 b, which matches the standard 12-lead record length) plus 8 kB base for program, state and fusion. The window is swept 2–10 s. | [decision] |
| A-06 | Abnormal-capture fraction p_abnormal = 5% (range 1–50%). | [decision] |
| A-07 | Retained SRAM leakage is 0.1 µW/kB (range 0.02–1), added to every orchestrator floor as leakage × SRAM cap (3.2 µW at 32 kB). This value needs a citation. | [assumed] |
| A-08 | Lead assignment for on-body analysis. Each independent lead goes to the head of the area holding its electrode. The 12-lead limb group (I and II buffered, the others derived) goes to the head holding RA. Heads other than RA's receive a WCT broadcast of RA, LA and LL (3 × fs × 16 b) over the inter-area links. Streams are counted only during the capture, not the warm-up. | [decision] |
| A-10 | The analysis buffer can be compressed losslessly by r (default 1, range 1–3). Lossless ECG coders reach about 2–3×; this needs a citation. | [assumed] |
| A-11 | Closed-form regime rule. A head holding L independent leads fits if M_base + L·T/r ≤ S. The winner is the fewest-SoC architecture whose largest per-head load L_max fits. If none fits but M_base + T/r ≤ S, the finest architecture wins by fitting partially. Otherwise everything streams and centralized wins. Checked against 220 of 220 cells for continuous 12-lead. | [derived] |
| A-09 | Schedules. default: as in X-07. cont12L: 12-lead continuously, as back-to-back 10 s windows with no warm-up. contBSPM: BSPM continuously. | [decision] |

### V — Validation and publication
| ID | Assumption | Status |
|---|---|---|
| V-01 | Power-model validation has three parts. Predictive: Warchall's UWB TX increment computed from the ADC rate × 88 pJ/b (result: +0.6%). Accounting: Warchall without UWB, Kuang and Dabbaghian (within 0.3%). Plausibility: SeisMote (150 mAh / 9.4 mA = 16 h; radio is 10–59% of 34.8 mW). | [decision] |
| V-02 | Signal-quality validation. The model reproduces the textbook divider result \|ΔZ\|/\|Z_cm\| exactly. For Dabbaghian '24 (82.2 dB intrinsic, 1 MΩ mismatch, Z_in = 5.5 GΩ at 60 Hz) it predicts 8–10 dB of degradation against < 5 dB reported, so it is conservative by 3–5 dB. The test conditions still need checking. | [decision] |
| V-03 | The target venue is ISCAS 2027 (about 4 pages). The deadline is set aside for now, on the expectation that it will be extended. | [decision] |

---

## Superseded

| ID | Was | Replaced by | Date |
|---|---|---|---|
| S-01 | A single knob k (electrodes per node) with power-of-two recursive bisection. | H-01 – H-03: an (m, n) hierarchy with capacitated clustering. | 2026-09-30 |
| S-02 | Spares were the nearest grid sites (3.7–6 cm away, outside tolerance). | G-09: dedicated spares at 1.5 cm. | 2026-09-30 |
| S-03 | 64 electrodes as a cap on the total. | G-06 / G-09: 54 grid + 10 12-lead sites + spares. | 2026-09-30 |
| S-04 | Hub at the "centre of the torso", fixed. | H-05: root chosen by the L1-median, with the position swept. | 2026-09-30 |
| S-05 | "0.5 mW after derating for usable capacity **and** regulator losses", with η then applied again. | B-01 / B-02: the budget is at the battery and η is applied once. | 2026-09-30 |
| S-06 | THReaD SoC floor treated as about 38 µW/MHz with no static term. | P-10 / P-12: 225 µW + 75 µW/MHz fit, with a floor band of 100–225 µW. | 2026-09-30 |
| S-07 | Motion artifacts assumed the same across architectures (out of scope). | M-02: availability by site and activity. | 2026-09-30 |
| S-08 | V-01 as "reproduce Warchall, Dabbaghian and Kuang to within ~20% using only the terms each reported" (partly circular). | V-01: predictive + accounting + plausibility. | 2026-09-30 |
| S-09 | P-17: sensor-node overhead and router power were TBD. | P-24: set values, with spec-case limits as outputs. | 2026-09-30 |
| S-10 | Q-03: yarn coupling to the body vs. to ground was unresolved. | Q-03: split into line-to-body and line-to-ground C. | 2026-10-01 |
| S-11 | Q-08: realistic V_cm was TBD. | Q-08: not needed (rejection-ratio formulation). | 2026-10-01 |
| S-12 | Q-07: "≤ ~9 µs with 40 dB" from a back-of-envelope estimate. | Q-07: ≲ 10 µs and ≲ 0.35% gain, from the model. | 2026-10-01 |
| S-13 | X-06: export rates fixed per mode, identical for all architectures, with captures streamed during warm-up. | A-01 – A-09: an export policy limited by chiplet capacity; streaming counted only during the capture. | 2026-10-01 |
