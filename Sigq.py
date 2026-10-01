"""
Stage 4 signal-quality model: common-mode residual at each lead.

A lead is a weight vector w over electrodes (sum w = 0). The common-mode-to-
differential conversion at the lead is

    c = | sum_i  w_i * (1 + eps_n(i)) * exp(-j*omega*tau_n(i)) * h_i |  +  1/CMRR_amp

    h_i   = Z_cm,i / (Z_src,i + Z_cm,i)
    Z_src = Z_e,i || 1/(j*omega*C_line_body*L_i)      (electrode, with the analog line's coupling to skin)
    Z_cm  = Z_in   || 1/(j*omega*C_line_gnd*L_i)      (AFE input CM impedance, with line-to-ground C)
    L_i   = analog run from electrode i to its sensor node's AFE

eps_n and tau_n are the gain error and sample-time offset of sensor node n; electrodes on the
same node share them, so they cancel within a node (differential channels, H-10).
System rejection = 20*log10(1 + A_DRL) - 20*log10(c), compared against the IEC-equivalent
target (Q-09 .. Q-16 in ASSUMPTIONS.md).
"""
from __future__ import annotations

import numpy as np
import geometry as geo

W60 = 2 * np.pi * 60.0


# --------------------------------------------------------------------------- #
# Lead weight matrices
# --------------------------------------------------------------------------- #
def _w(sites, terms):
    idx = {s.name: i for i, s in enumerate(sites)}
    w = np.zeros(len(sites))
    for name, c in terms:
        w[idx[name]] += c
    return w


def twelve_lead_weights(sites):
    W = {
        "I": [("LA", 1), ("RA", -1)], "II": [("LL", 1), ("RA", -1)], "III": [("LL", 1), ("LA", -1)],
        "aVR": [("RA", 1), ("LA", -.5), ("LL", -.5)], "aVL": [("LA", 1), ("RA", -.5), ("LL", -.5)],
        "aVF": [("LL", 1), ("RA", -.5), ("LA", -.5)],
    }
    for k in range(1, 7):
        W[f"V{k}"] = [(f"V{k}", 1), ("RA", -1/3), ("LA", -1/3), ("LL", -1/3)]
    names = list(W)
    return names, np.array([_w(sites, W[n]) for n in names])


def bspm_weights(sites):
    idx = {s.name: i for i, s in enumerate(sites)}
    meas = [i for i, s in enumerate(sites) if s.role != "spare" and s.name not in ("RL", "RA", "LA", "LL")]
    Wm = np.zeros((len(meas), len(sites)))
    for r, i in enumerate(meas):
        Wm[r, i] = 1
        for e in ("RA", "LA", "LL"):
            Wm[r, idx[e]] -= 1/3
    return [sites[i].name for i in meas], Wm


def rr_pairs(sites, D, pt: geo.Point, p):
    """Electrode pairs used in R-R mode (same selection rule as power.mode_load, H-13)."""
    k, sp = int(p["rr_leads"]), p["min_lead_spacing"]
    usable = {i for i, s in enumerate(sites) if s.role != "spare"}
    if pt.n_nodes == 1:
        idx = {s.name: i for i, s in enumerate(sites)}
        return [(idx["LA"], idx["RA"]), (idx["LL"], idx["RA"])][:k]
    by_root = sorted(range(pt.n_nodes), key=lambda c: D[pt.node_sites[c], pt.root])
    pairs = []
    for c in by_root:
        mem = [i for i in pt.node_clusters[c] if i in usable]
        if len(mem) < 2:
            continue
        sub = D[np.ix_(mem, mem)]
        a, b = np.unravel_index(np.argmax(sub), sub.shape)
        if sub[a, b] >= sp:
            pairs.append((mem[a], mem[b]))
        if len(pairs) == k:
            return pairs
    pairs, used = [], set()                              # active electrodes (m = 1)
    for a in by_root:
        if len(pairs) == k:
            break
        if a in used:
            continue
        for b in by_root:
            if b != a and b not in used and D[pt.node_sites[a], pt.node_sites[b]] >= sp:
                pairs.append((pt.node_clusters[a][0], pt.node_clusters[b][0])); used |= {a, b}; break
    return pairs


def rr_weights(sites, D, pt, p):
    pr = rr_pairs(sites, D, pt, p)
    W = np.zeros((len(pr), len(sites)))
    for r, (a, b) in enumerate(pr):
        W[r, a], W[r, b] = 1, -1
    return [f"{sites[a].name}-{sites[b].name}" for a, b in pr], W


# --------------------------------------------------------------------------- #
# Per-electrode CM transfer
# --------------------------------------------------------------------------- #
def analog_runs_m(D, pt: geo.Point) -> np.ndarray:
    L = np.zeros(D.shape[0])
    for c, mem in enumerate(pt.node_clusters):
        for i in mem:
            L[i] = D[i, pt.node_sites[c]] / 100
    return L


def electrode_Z(n_el, trials, p, case, rng):
    """Complex electrode impedance at 60 Hz, shape (trials, n_el)."""
    if case == "compliance":
        return None                                    # handled by imbalance sweep
    s = p["Ze_sigma_ln"]
    R = p["Ze_R_med"] * 1e6 * np.exp(rng.normal(0, s, (trials, n_el)))
    C = p["Ze_C_med"] * 1e-9 * np.exp(rng.normal(0, s, (trials, n_el)))
    return R / (1 + 1j * W60 * R * C)


def h_transfer(Ze, L, p):
    Zlb = 1 / (1j * W60 * p["C_line_body"] * 1e-12 * np.maximum(L, 1e-9))
    Zsrc = np.where(L > 0, Ze * Zlb / (Ze + Zlb), Ze)
    Yin = 1 / (p["Zin_R"] * 1e9) + 1j * W60 * (p["Zin_C"] * 1e-12 + p["C_line_gnd"] * 1e-12 * L)
    Zcm = 1 / Yin
    return Zcm / (Zsrc + Zcm)


def node_errors(pt, trials, p, sync, fs, rng):
    """Per-node gain error and time offset, shape (trials, n_nodes)."""
    nn = pt.n_nodes
    g = p["gain_mismatch"] / 100
    eps = rng.uniform(-g / 2, g / 2, (trials, nn))
    if sync == "none":
        tau = rng.uniform(0, 1 / fs, (trials, nn))
    elif sync == "ts":
        tau = rng.uniform(-p["skew_ts"] / 2, p["skew_ts"] / 2, (trials, nn)) * 1e-6
    elif sync == "hw":
        tau = rng.uniform(-p["skew_hw"] / 2, p["skew_hw"] / 2, (trials, nn)) * 1e-6
    else:
        raise ValueError(sync)
    return (1 + eps) * np.exp(-1j * W60 * tau)


# --------------------------------------------------------------------------- #
# Rejection per lead
# --------------------------------------------------------------------------- #
def lead_rejection(sites, D, pt, mode, p, case="realistic", sync="hw", trials=None, seed=0):
    """
    Returns (lead_names, rej_dB) with rej_dB shape (trials, leads): system-level rejection
    including DRL credit. Compliance case: the IEC 51k||47n imbalance is placed on each
    electrode of the lead in turn (others ideal) and the worst is kept.
    """
    rng = np.random.default_rng(seed)
    trials = int(trials or p["mc_trials"])
    if mode == "12L":
        names, W = twelve_lead_weights(sites); fs = p["fs_diag"]
    elif mode == "BSPM":
        names, W = bspm_weights(sites); fs = p["fs_diag"]
    else:
        names, W = rr_weights(sites, D, pt, p); fs = p["fs_rr"]
    L = analog_runs_m(D, pt)
    node_of = np.empty(len(sites), int)
    for c, mem in enumerate(pt.node_clusters):
        node_of[mem] = c
    G = node_errors(pt, trials, p, sync, fs, rng)[:, node_of]          # (trials, N)
    amp = 10 ** (-p["cmrr_amp"] / 20)
    drl = p["cm_suppression_drl"]                                   # 20*log10(1 + A_DRL)

    if case == "realistic":
        h = h_transfer(electrode_Z(len(sites), trials, p, case, rng), L, p)
        conv = np.abs((G * h) @ W.T) + amp
    else:
        z_imb = 51e3 / (1 + 1j * W60 * 51e3 * 47e-9)
        conv = np.zeros((trials, W.shape[0]))
        for r in range(W.shape[0]):
            worst = np.zeros(trials)
            for i in np.nonzero(W[r])[0]:
                Ze = np.full(len(sites), 1e-3 + 0j)
                Ze[i] = z_imb
                h = h_transfer(Ze, L, p)
                worst = np.maximum(worst, np.abs((G * h) @ W[r]) + amp)
            conv[:, r] = worst
    return names, drl - 20 * np.log10(conv)


def mode_metric(rej, mode, p, q=5):
    """
    Pass metric per mode, at the q-th percentile across trials (95% of garments):
      12L : worst lead           >= rej_target_diag
      BSPM: fraction of leads    >= rej_target_diag  (pass if >= 95%)
      RR  : best lead            >= rej_target_rr
    Returns (value, passed).
    """
    if mode == "12L":
        v = np.percentile(rej.min(axis=1), q)
        return v, v >= p["rej_target_diag"]
    if mode == "BSPM":
        frac = (rej >= p["rej_target_diag"]).mean(axis=1)
        v = np.percentile(frac, q)
        return v, v >= 0.95
    v = np.percentile(rej.max(axis=1), q)
    return v, v >= p["rej_target_rr"]


def lead_noise_uvpp(W, p, mode):
    """First-order lead IRN (p-p over ~6.6 sigma), treating each weighted electrode term as one channel's noise."""
    irn = p["irn_ch_diag"] if mode != "RR" else p["irn_ch_mon"]
    return 6.6 * irn * np.sqrt((W ** 2).sum(axis=1))
