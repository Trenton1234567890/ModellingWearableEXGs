"""
Stage 3 power model.

For one architecture point (geometry.Point) and one operating mode, sum:
  sensor nodes : active -> P_node_fixed + P_router + ch*(P_afe + P_adc) [+ DRL drive]
                 inactive -> P_node_off
  intra links  : per active node, raw bits * (hops*E_hop + path*E_yarn)
  inter links  : per area head, (features or raw) bits * (hops*E_hop + path*E_yarn)
  orchestrators: per SoC, floor + E_cycle * workload   (floor = as-built THReaD, or spec unknown)
  off-body TX  : P_tx_floor + E_tx * export rate
Average over the mode schedule, then divide by PMU efficiency to get battery power.

Assumption IDs in comments refer to ASSUMPTIONS.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import params as prm
import geometry as geo

MODES = ("RR", "12L", "BSPM")
CATS = ("afe_adc", "node_fixed", "node_off", "link_intra", "link_inter",
        "orch_floor", "orch_compute", "tx")


def P(**overrides) -> dict:
    """Parameter values as a dict, with overrides."""
    t = prm.table()
    d = {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in t["value"].items()}
    d.update(overrides)
    return d


def e_yarn_per_m(p) -> float:
    """Energy per useful bit per metre of 2-wire link [J] (P-03, P-05, P-06, P-07)."""
    C = p["yarn_C"] * 1e-12
    V = p["V_link"]
    return p["pkt_overhead"] * (p["activity_data"] * C * V**2 + C * V**2)


def p_adc_ch(p, fs) -> float:
    """FoM-based conversion power per channel [W] (P-14)."""
    return p["adc_fom"] * 1e-15 * fs * 2 ** p["adc_enob"]


# --------------------------------------------------------------------------- #
# Which electrodes / channels / leads are active in each mode
# --------------------------------------------------------------------------- #
@dataclass
class ModeLoad:
    mode: str
    fs: float
    afe_w: float                                   # per-channel AFE power [W]
    ch: dict = field(default_factory=dict)         # node index -> channels
    drl: dict = field(default_factory=dict)        # node index -> DRL drivers
    leads_at: dict = field(default_factory=dict)   # SoC site index -> leads processed
    inter_raw_nodes: set = field(default_factory=set)   # nodes whose raw must reach the root
    feat_leads_at_head: dict = field(default_factory=dict)  # head site -> feature leads sent to root
    tx_bps: float = 0.0
    inter_extra_bps: dict = field(default_factory=dict)  # head site -> extra inter-area bps (features, abnormal captures, WCT)
    head_mem_kB: dict = field(default_factory=dict)      # head site -> SRAM needed for on-body analysis
    head_fits: dict = field(default_factory=dict)        # head site -> analysis fits SRAM and clock caps
    onbody_frac: float = 0.0                             # fraction of leads analysed on-body


def _maps(pt: geo.Point):
    node_of = {i: c for c, mem in enumerate(pt.node_clusters) for i in mem}
    area_of_node = {c: a for a, mem in enumerate(pt.areas) for c in mem}
    return node_of, area_of_node


def mode_load(sites, D, pt: geo.Point, mode: str, p) -> ModeLoad:
    node_of, area_of_node = _maps(pt)
    head_of_node = {c: pt.heads[area_of_node[c]] for c in range(pt.n_nodes)}
    name_idx = {s.name: i for i, s in enumerate(sites)}
    usable = [i for i, s in enumerate(sites) if s.role != "spare"]          # spares off unless substituting

    if mode == "RR":                                                        # R-04, X-02, P rr_leads
        L = ModeLoad("RR", p["fs_rr"], p["P_afe_mon"] * 1e-6)
        k = int(p["rr_leads"])
        sp = p["min_lead_spacing"]
        by_root = sorted(range(pt.n_nodes), key=lambda c: D[pt.node_sites[c], pt.root])
        leads = []                                                          # (node_a, node_b)
        if pt.n_nodes == 1:
            leads = [(0, 0)] * k
        else:
            local = [c for c in by_root
                     if len([i for i in pt.node_clusters[c] if i in usable]) > 1
                     and D[np.ix_(pt.node_clusters[c], pt.node_clusters[c])].max() >= sp]
            if len(local) >= k:
                leads = [(c, c) for c in local[:k]]
            else:                                                           # active electrodes (m = 1)
                used = set()
                for a in by_root:
                    if len(leads) == k:
                        break
                    if a in used:
                        continue
                    for b in by_root:
                        if b != a and b not in used and D[pt.node_sites[a], pt.node_sites[b]] >= sp:
                            leads.append((a, b)); used |= {a, b}; break
        for a, b in leads:
            if a == b:
                L.ch[a] = L.ch.get(a, 0) + 1                                # differential, on-node
                soc = head_of_node[a]
            else:
                L.ch[a] = L.ch.get(a, 0) + 1                                # single-ended vs shared ref
                L.ch[b] = L.ch.get(b, 0) + 1
                if area_of_node[a] == area_of_node[b]:
                    soc = head_of_node[a]
                else:
                    soc = pt.root
                    L.inter_raw_nodes |= {a, b}
            L.leads_at[soc] = L.leads_at.get(soc, 0) + 1
            if soc != pt.root:
                L.feat_leads_at_head[soc] = L.feat_leads_at_head.get(soc, 0) + 1
        pol = p.get("export", "onbody")
        if pol == "raw":                                                    # no on-body processing at all
            L.tx_bps = sum(L.ch.values()) * L.fs * p["sample_bits"]
        else:                                                               # streaming R-R detection is cheap
            L.tx_bps = p["feat_bits_beat"] * p["hr_hz"]                     # one fused R-R stream
        return L

    # 12-lead and BSPM: differential per node + one anchor channel when leads span nodes
    L = ModeLoad(mode, p["fs_diag"], p["P_afe_diag"] * 1e-6)
    if mode == "12L":
        meas = [name_idx[n] for n in ("RA", "LA", "LL", "V1", "V2", "V3", "V4", "V5", "V6")]
        n_leads, n_export = 12, 8
    else:
        meas = [i for i in usable if sites[i].name != "RL"]
        n_leads = n_export = len(meas)
    drl = name_idx["RL"]
    per_node = {}
    for i in meas:
        per_node.setdefault(node_of[i], []).append(i)
    anchor = 1 if len(per_node) > 1 else 0                                  # H: differential choice
    for c, els in per_node.items():
        L.ch[c] = (len(els) - 1) + anchor
    L.drl[node_of[drl]] = 1
    pol = p.get("export", "onbody")
    t_cap = p["t_12lead_capture"] if mode == "12L" else p["t_bspm_capture"]
    cont = p.get("schedule", "default") == ("cont12L" if mode == "12L" else "contBSPM")
    t_mode = t_cap + (0.0 if cont else p["t_warmup_hpf"])                # A-09: continuous = back-to-back windows
    bits = p["sample_bits"]
    comp_bits_lead = L.fs * bits * t_cap / p["compress_ratio"]           # one compressed lead, one capture

    if pol in ("raw", "compressed"):
        # Leads formed at the root (or the single area head); root streams the capture off-body
        areas_used = {area_of_node[c] for c in list(per_node) + [node_of[drl]]}
        soc = pt.heads[areas_used.pop()] if len(areas_used) == 1 else pt.root
        L.leads_at[soc] = n_leads
        if soc == pt.root:
            L.inter_raw_nodes |= {c for c in per_node if head_of_node[c] != pt.root}
        div = 1 if pol == "raw" else p["compress_ratio"]
        L.tx_bps = n_export * L.fs * bits / div * t_cap / t_mode            # stream only during the capture (fix, A-08)
        return L

    # ---- on-body analysis, capacity-limited (A-01 .. A-08) ----
    # Assign each independent lead to an orchestrator: leads stay in the area that holds their electrode;
    # the limb group (I, II; others derived) sits with RA. WCT samples (RA, LA, LL) are broadcast to other heads.
    idx = name_idx
    limb_head = head_of_node[node_of[idx["RA"]]]
    assign = {}                                                             # head -> [n_independent, n_reported]
    if mode == "12L":
        assign[limb_head] = [2, 6]
        for k in range(1, 7):
            h = head_of_node[node_of[idx[f"V{k}"]]]
            a = assign.setdefault(h, [0, 0]); a[0] += 1; a[1] += 1
    else:
        for i in meas:
            if sites[i].name in ("RA", "LA", "LL"):
                continue
            h = head_of_node[node_of[i]]
            a = assign.setdefault(h, [0, 0]); a[0] += 1; a[1] += 1
    cap_kB, fcap = p["sram_cap_kB"], p["f_cap_MHz"] * 1e6
    mem_lead = p["analysis_mem_kB_lead"]
    lead_out_bits = p["feat_bits_lead_12L"] if mode == "12L" else p["template_s_bspm"] * L.fs * bits
    n_onbody = n_total = 0
    tx_bits = 0.0
    for h, (n_ind, n_rep) in assign.items():
        need = p["analysis_mem_base_kB"] + mem_lead * n_ind
        cyc = p["W_lead"] * n_rep + (p["W_root"] if h == pt.root else 0)
        fits = (need <= cap_kB) and (cyc <= fcap)
        L.head_mem_kB[h], L.head_fits[h] = need, fits
        L.leads_at[h] = L.leads_at.get(h, 0) + n_rep
        n_total += n_ind
        if fits:
            n_onbody += n_ind
            out_bits = n_rep * lead_out_bits + p["p_abnormal"] * n_ind * comp_bits_lead
        else:
            out_bits = n_ind * comp_bits_lead                                # per-head fallback: stream compressed
        tx_bits += out_bits
        if h != pt.root:
            L.inter_extra_bps[h] = L.inter_extra_bps.get(h, 0) + out_bits / t_mode
            if h != limb_head:                                              # WCT broadcast into this area
                L.inter_extra_bps[h] = L.inter_extra_bps.get(h, 0) + 3 * L.fs * bits
    L.onbody_frac = n_onbody / max(n_total, 1)
    L.tx_bps = tx_bits / t_mode
    return L


# --------------------------------------------------------------------------- #
# Power for one mode
# --------------------------------------------------------------------------- #
def mode_power(sites, D, pt: geo.Point, mode: str, p, case: str = "asbuilt",
               orch_floor_w: float | None = None) -> dict:
    """Returns per-category power [W] for one mode (before PMU efficiency)."""
    L = mode_load(sites, D, pt, mode, p)
    out = dict.fromkeys(CATS, 0.0)
    ey = e_yarn_per_m(p)
    eh = p["E_hop"] * 1e-12
    bits = p["sample_bits"]
    has_links = pt.n_nodes > 1

    # Sensor nodes
    for c in range(pt.n_nodes):
        ch, dr = L.ch.get(c, 0), L.drl.get(c, 0)
        if ch or dr:
            out["afe_adc"] += ch * (L.afe_w + p_adc_ch(p, L.fs)) + dr * L.afe_w
            out["node_fixed"] += (p["P_node_fixed"] + (p["P_router_node"] if has_links else 0)) * 1e-6
        else:
            out["node_off"] += p["P_node_off"] * 1e-6

    # Intra-area links: every active node streams raw to its head
    for c, ch in L.ch.items():
        s = pt.node_sites[c]
        if ch and s in pt.intra_lv.per_src:
            path_cm, hops = pt.intra_lv.per_src[s]
            out["link_intra"] += ch * L.fs * bits * (hops * eh + path_cm / 100 * ey)

    # Inter-area links: features from heads, raw forwarded for leads formed at the root
    head_of_node = {c: pt.heads[a] for a, mem in enumerate(pt.areas) for c in mem}
    inter_bps = {}
    for h, nl in L.feat_leads_at_head.items():
        inter_bps[h] = inter_bps.get(h, 0) + nl * p["feat_bits_beat"] * p["hr_hz"]
    for c in L.inter_raw_nodes:
        h = head_of_node[c]
        inter_bps[h] = inter_bps.get(h, 0) + L.ch.get(c, 0) * L.fs * bits
    for h, bps in L.inter_extra_bps.items():
        inter_bps[h] = inter_bps.get(h, 0) + bps
    for h, bps in inter_bps.items():
        if h in pt.inter_lv.per_src:
            path_cm, hops = pt.inter_lv.per_src[h]
            out["link_inter"] += bps * (hops * eh + path_cm / 100 * ey)

    # Orchestrators (one SoC per area)
    floor = (p["P_soc_floor_asbuilt"] * 1e-6 if case == "asbuilt"
             else (orch_floor_w if orch_floor_w is not None else 0.0)
                  + p["sram_leak_uW_kB"] * 1e-6 * p["sram_cap_kB"])          # A-07: retained SRAM leakage
    for h in pt.heads:
        w = L.leads_at.get(h, 0) * p["W_lead"] + (p["W_root"] if h == pt.root else 0)
        out["orch_floor"] += floor
        out["orch_compute"] += p["E_cycle"] * 1e-12 * w

    # Off-body TX at the root
    out["tx"] = p["P_tx_floor"] * 1e-6 + p["E_tx_ble"] * 1e-9 * L.tx_bps
    return out


def duty(p) -> dict:
    """Time fraction per mode, including warm-up (X-02, X-04). schedule: default | cont12L | contBSPM (A-09)."""
    sch = p.get("schedule", "default")
    if sch == "cont12L":
        return {"RR": 0.0, "12L": 1.0, "BSPM": 0.0}
    if sch == "contBSPM":
        return {"RR": 0.0, "12L": 0.0, "BSPM": 1.0}
    d12 = p["n_12lead_per_day"] * (p["t_12lead_capture"] + p["t_warmup_hpf"]) / 86400
    db = p["n_bspm_per_day"] * (p["t_bspm_capture"] + p["t_warmup_hpf"]) / 86400
    return {"RR": 1 - d12 - db, "12L": d12, "BSPM": db}


def average_power(sites, D, pt, p, case="asbuilt", orch_floor_w=None) -> dict:
    """Schedule-weighted breakdown at the battery [W] (B-02). Adds 'total' and per-mode totals."""
    dt = duty(p)
    avg = dict.fromkeys(CATS, 0.0)
    per_mode = {}
    for m in MODES:
        mp = mode_power(sites, D, pt, m, p, case, orch_floor_w)
        per_mode[m] = sum(mp.values()) / p["eta_pmu"]
        for k in CATS:
            avg[k] += dt[m] * mp[k] / p["eta_pmu"]
    avg["total"] = sum(avg[k] for k in CATS)
    avg.update({f"mode_{m}": v for m, v in per_mode.items()})
    return avg


# --------------------------------------------------------------------------- #
# Spec case: what orchestrator floor fits the budget?
# --------------------------------------------------------------------------- #
def max_orch_floor(sites, D, pt, p) -> float:
    """
    Largest per-SoC idle floor [W] such that battery power <= P_budget,
    with all other parameters at their values. Negative => infeasible even at 0 W.
    Battery power is linear in the floor: P = A + n_areas * floor / eta.
    The floor here is the core floor; SRAM leakage (A-07) is added on top inside mode_power.
    """
    A = average_power(sites, D, pt, p, "spec", 0.0)["total"]
    B = p["P_budget"] * 1e-3
    return (B - A) * p["eta_pmu"] / pt.n_areas


def max_node_fixed(sites, D, pt, p, orch_floor_w: float) -> float:
    """Largest sensor-node fixed overhead [W] that fits the budget at a given orchestrator floor."""
    p0 = dict(p, P_node_fixed=0.0)
    p1 = dict(p, P_node_fixed=1.0)          # 1 uW probe (linear)
    A0 = average_power(sites, D, pt, p0, "spec", orch_floor_w)["total"]
    A1 = average_power(sites, D, pt, p1, "spec", orch_floor_w)["total"]
    slope = (A1 - A0) / 1e-6                # W at battery per W of node overhead
    B = p["P_budget"] * 1e-3
    return (B - A0) / slope if slope > 0 else np.inf
