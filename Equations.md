# Model Equations Reference

These are the equations the architecture model actually uses, grouped by stage. Bracketed IDs point to `Assumptions.md`; the code module is given for each stage.

---

## 1. Energy budget (Stage 1, `params.py`)

| # | Equation | Meaning |
|---|---|---|
| 1.1 | E_batt ≈ 0.10–0.15 Wh | 1 g Li-ion at ~100–150 Wh/kg [B-01] |
| 1.2 | P_budget = 0.85 · E_batt / (7 d × 24 h) ≈ 0.5 mW | average battery draw, derated for usable capacity [B-01] |
| 1.3 | P_delivered = η · P_battery, with η = 0.7 | PMU conversion loss, applied once [B-02] |
| 1.4 | t_warm = 4.6 / (2π · f_HP) ≈ 15 s at 0.05 Hz | settling of a first-order high-pass to 1% [X-04] |

---

## 2. Geometry and wiring (Stage 2, `geometry.py`)

| # | Equation | Meaning |
|---|---|---|
| 2.1 | d(p, q) = min(\|Δx\|, C − \|Δx\|) + \|Δy\| | Manhattan routing on the unwrapped torso, wrapping at the back seam [G-03] |
| 2.2 | d_torso↔sleeve = d(p, J) + (\|u\| + v) | routes between the torso and a sleeve pass through the shoulder junction J [G-02] |
| 2.3 | min Σᵢ d(i, medoid(cᵢ)) subject to \|c\| ≤ m | capacitated k-medoids grouping of electrodes into sensor nodes, then of nodes into areas [H-02] |
| 2.4 | path and hop count per source, from Dijkstra on a 4-port mesh (MST + nearest neighbours), a star, or a multidrop chain | inputs to the link-energy term [H-06 – H-08] |

---

## 3. Power (Stage 3, `power.py`)

**3.1 Battery power, averaged over the schedule**

  P_batt = (1/η) · Σ_modes d_mode · P_mode

with mode duty d_12L = n_12L/day · (t_cap + t_warm) / 86400, and similarly for BSPM. R-R takes the rest of the time [X-07, A-09].

**3.2 Power in one mode**

  P_mode = Σ_active nodes [P_fixed + P_router + ch·(P_AFE + P_ADC)] + Σ_off nodes P_off + P_links + Σ_SoCs P_SoC + P_TX

**3.3 Channels per node (differential)**

  ch = (k − 1) + a, where a = 1 when the mode's leads span more than one node [H-10]

**3.4 ADC conversion power**

  P_ADC = FoM · fs · 2^ENOB  (48.6 fJ/step × 500 S/s × 2¹¹ ≈ 0.05 µW) [P-14]

**3.5 Link energy per useful bit**

  E_link = h·E_hop + L·E_yarn, with E_yarn = κ·(α·C′·V² + C′·V²) [P-01, P-25]

- κ = 2.7 is protocol overhead in link clocks per useful bit [P-03].
- α = 0.5 is the data-line activity; the clock line toggles every bit [P-07].
- The result is about 467 pJ per bit per metre at 80 pF/m and 1.2 V.

  P_links = Σ_sources R_bits · E_link

**3.6 Yarn capacitance (analytical estimates)**

  C′_line→skin = 2πε / acosh(h/a)   (h = height above skin, a = yarn radius) [P-05]
  C′_line→ground yarn = πε / acosh(s/2a)   (s = spacing to the ground yarn) [Q-03]

**3.7 Orchestrator SoC**

  P_SoC = P_floor + P_leak·S + E_cycle·W

- As built: P_floor = 225 µW, from the two-point fit P = 225 µW + 75 µW/MHz · f [P-10].
- Spec case: P_floor is the unknown being solved for.
- P_leak·S is retained SRAM leakage, S being the SRAM size [A-07].
- E_cycle·W is compute: 38 pJ/cycle × cycles/s [P-26, P-27].

**3.8 Radio**

  P_TX = P_TX,floor + E_bit · R_TX  (20 µW + 200 nJ/b × rate) [P-18, P-29]

**3.9 Spec inversion: largest core floor per SoC that fits the budget**

  P_floor,max = (P_budget − A) · η / n_SoC, where A is battery power with a zero floor

---

## 4. On-garment analysis and export (`power.py`)

**4.1 Memory an orchestrator needs**

  M_need = M_base + M_lead · L / r

- M_lead = T · fs · b ≈ T kB at 500 S/s and 16 b [A-05].
- L is the number of independent leads this head analyses.
- r is the lossless buffer-compression ratio [A-10].

**4.2 Fit test**

  fits ⇔ M_need ≤ S_cap and W ≤ f_cap [A-03, A-04]

**4.3 Bits sent per capture, per head**

  fits:  N_rep · b_feat + p_abn · L · B_comp
  doesn't fit:  L · B_comp, where B_comp = fs · b · T_cap / ρ (ρ = 4) [A-02]

**4.3b Per-mode memory per lead**

  store-then-decide: M_lead = T_win · fs · b (≈ T_win kB), divided by the buffer ratio, or by the lossless ratio when diag_lossless is on
  streaming (BSPM): M_lead = M_stream ≈ 1.5 kB, independent of T_win [A-05, A-13, A-14]

**4.4 Regime boundaries**

  Centralized fits:  S ≥ M_base + L_max · T / r
  Partial fit:  S ≥ M_base + T / r

The winner is the architecture with the fewest SoCs whose L_max fits. This reproduces 220 of 220 sweep cells [A-11].

**4.5 Breakeven: distribution beats a centralized design that has to stream**

  (n_SoC − 1) · (P_floor + P_leak·S) < E_bit · (R_stream − R_onbody)

For continuous 12-lead this is about 19 µW per SoC against about 4.2 mW saved, so breakeven is around 220 extra SoCs.

---

## 4b. IO pads per chiplet (`geometry.py`) [H-15]

  sensor chiplet:  P_IO = k_electrodes + 2 · (p_dedicated + min(p_mesh, 4))
  orchestrator:    P_IO = 2 · (p_dedicated + min(p_mesh, 4))
  centralized:     P_IO = N + 2, so it grows linearly with electrode count
  feasible ⇔ P_IO ≤ chiplet_io_pads (THReaD ≈ 9)

---

## 5. Signal quality (Stage 4, `sigq.py`)

**5.1 Lead definition**

  lead = Σᵢ wᵢ · vᵢ, with Σ wᵢ = 0
  Example: V1 = v_V1 − (v_RA + v_LA + v_LL)/3 [Q-09]

**5.2 Fraction of the common mode reaching each input**

  hᵢ = Z_cm,i / (Z_src,i + Z_cm,i)

- Z_src = Z_e ∥ 1/(jω·C′_line→skin·L)
- Z_cm = R_in ∥ 1/(jω·(C_in + C′_line→ground·L)) [Q-10]

**5.3 Common-mode-to-differential conversion**

  c = \|Σᵢ wᵢ · (1 + εₙ) · e^(−jωτₙ) · hᵢ\| + 1/CMRR_amp [Q-11]

- εₙ is node n's gain error and τₙ its sample-time offset; they are shared within a node.

**5.4 Small-error approximations (useful intuition)**

  electrode mismatch ≈ ΔZ_e / Z_cm
  gain mismatch ≈ ΔG/G
  sample skew ≈ ω·Δt

**5.5 System rejection and requirement**

  Rej = G_DRL − 20·log₁₀(c) ≥ 89 dB for 12-lead/BSPM, ≥ 60 dB for R-R [Q-17]

**5.6 Where the IEC number comes from**

  20·log₁₀(28.3 Vpp / 1 mV) ≈ 89 dB
  Z_cm,required = ΔZ_IEC · 28,300 ≈ 37.8 kΩ × 28,300 ≈ 1.1 GΩ (no DRL)
  ΔZ_IEC = \|51 kΩ ∥ 47 nF\| at 60 Hz

**5.7 Dry-electrode model**

  Z_e = R ∥ C, with R and C lognormal (medians 2 MΩ and 2.2 nF, σ_ln = 0.7) [Q-12]
  Results are reported at the 5th percentile of 400 Monte Carlo trials [Q-18].

**5.8 Noise check**

  v_pp ≈ 6.6 · σ_ch · √(Σwᵢ²) [Q-20]
