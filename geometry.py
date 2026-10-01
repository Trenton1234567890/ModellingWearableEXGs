"""
Stage 2 geometry for the garment ECG architecture model.

Hierarchy (THReaD-style):
  electrode --analog--> sensor node (AFE+ADC for m electrodes, 2DSPI router)
  sensor nodes --digital--> area head (SoC orchestrator; one per area of n sensor nodes)
  area heads --digital--> root orchestrator (one head, nearest the garment centre; hosts off-body TX)

Surfaces (all unwrapped, units = cm):
  'T'  torso cylinder : x in (-C/2, C/2], 0 = sternum midline, + = patient's left
                        y in [0, H], 0 = waist/iliac level, H = shoulder line
  'SL' / 'SR' sleeves : u in (-Cs/2, Cs/2], 0 = anterior; v in [0, Ls], 0 = shoulder

Routing is Manhattan along each surface (textile yarn follows warp/weft; THReaD
routes XY dimension-ordered inside an area). Torso <-> sleeve routes pass through
the shoulder junction: torso (+/-C/4, H) <-> sleeve (0, 0). Wires may cross
(insulated, perpendicular); crossing crosstalk is out of scope.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree, dijkstra, connected_components


# --------------------------------------------------------------------------- #
# Garment, sites, distances
# --------------------------------------------------------------------------- #
@dataclass
class Garment:
    C: float = 100.0   # torso circumference [cm]
    H: float = 50.0    # torso height [cm]
    Cs: float = 30.0   # sleeve circumference [cm]
    Ls: float = 25.0   # sleeve length [cm]

    def junction(self, side: str):
        return (self.C / 4, self.H) if side == "SL" else (-self.C / 4, self.H)


@dataclass
class Site:
    name: str
    surface: str          # 'T', 'SL', 'SR'
    a: float              # x (torso) or u (sleeve)
    b: float              # y (torso) or v (sleeve)
    role: str = "grid"    # '12lead', 'spare', 'grid'
    parent: str = ""      # for spares: the 12-lead site they back up


def _wrap(d, period):
    d = abs(d) % period
    return min(d, period - d)


def surface_dist(g: Garment, p: Site, q: Site) -> float:
    """Manhattan routing distance along the garment surface [cm]."""
    if p.surface == q.surface:
        per = g.C if p.surface == "T" else g.Cs
        return _wrap(p.a - q.a, per) + abs(p.b - q.b)

    def to_junction(s: Site, side: str) -> float:
        if s.surface == "T":
            jx, jy = g.junction(side)
            return _wrap(s.a - jx, g.C) + abs(s.b - jy)
        return _wrap(s.a, g.Cs) + s.b

    surfaces = {p.surface, q.surface}
    if "T" in surfaces:
        side = (surfaces - {"T"}).pop()
        return to_junction(p, side) + to_junction(q, side)
    jl, jr = g.junction("SL"), g.junction("SR")
    return to_junction(p, p.surface) + _wrap(jl[0] - jr[0], g.C) + to_junction(q, q.surface)


def dist_matrix(g: Garment, sites: list[Site]) -> np.ndarray:
    n = len(sites)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            D[i, j] = D[j, i] = surface_dist(g, sites[i], sites[j])
    return D


# --------------------------------------------------------------------------- #
# Superset layout: 10 12-lead sites + spares + grid
# --------------------------------------------------------------------------- #
TWELVE_LEAD_TORSO = {
    "RA": (-12.0, 45.0), "LA": (12.0, 45.0),      # Mason-Likar infraclavicular
    "LL": (12.0, 5.0), "RL": (-12.0, 5.0),        # lower abdomen (RL = reference / DRL)
    "V1": (-2.5, 34.0), "V2": (2.5, 34.0), "V3": (5.75, 32.0),
    "V4": (9.5, 30.0), "V5": (17.0, 30.0), "V6": (25.0, 30.0),
}
SLEEVE_ARM_SITES = {"RA": ("SR", 0.0, 12.0), "LA": ("SL", 0.0, 12.0)}
# Spare offsets inside the placement tolerance (cm): lateral first, then vertical
SPARE_OFFSETS = [(1.5, 0.0), (-1.5, 0.0), (0.0, 1.5), (0.0, -1.5)]


def build_layout(g: Garment, variant: str = "ML", spares_per_site: int = 0,
                 n_front_grid: int = 38, n_back_grid: int = 16,
                 grid_pitch: float | None = None) -> list[Site]:
    """
    variant 'ML' : Mason-Likar torso placement for RA/LA
    variant 'SLV': RA/LA on the sleeves (mid upper arm)
    spares_per_site: dedicated spares per 12-lead site, placed 1.5 cm away (inside 2 cm tolerance).
    Grid sites are identical across variants and spare counts, so results are comparable.
    """
    explicit = []
    for name, (x, y) in TWELVE_LEAD_TORSO.items():
        if variant == "SLV" and name in SLEEVE_ARM_SITES:
            surf, u, v = SLEEVE_ARM_SITES[name]
            explicit.append(Site(name, surf, u, v, "12lead"))
        else:
            explicit.append(Site(name, "T", x, y, "12lead"))

    spare_sites = []
    for e in explicit:
        for j in range(spares_per_site):
            dx, dy = SPARE_OFFSETS[j % len(SPARE_OFFSETS)]
            spare_sites.append(Site(f"{e.name}s{j+1}", e.surface, e.a + dx, e.b + dy, "spare", e.name))

    ml_pts = [Site(n, "T", x, y) for n, (x, y) in TWELVE_LEAD_TORSO.items()]
    if grid_pitch is not None:
        # G-11: lead-count scaling. Regular grid at the given pitch over the same front/back regions,
        # dropping grid points closer than half a pitch (min 2 cm) to any 12-lead site.
        excl = max(grid_pitch / 2, 2.0)
        fx = np.arange(-21, 21 + 1e-9, grid_pitch); fy = np.arange(6, 44 + 1e-9, grid_pitch)
        front = [Site("", "T", x, y) for y in fy for x in fx
                 if min(surface_dist(g, Site("", "T", x, y), e) for e in ml_pts) >= excl]
        back = []
        for y in np.arange(8, 42 + 1e-9, grid_pitch):
            for dx in np.arange(-18, 18 + 1e-9, grid_pitch):
                x = g.C / 2 + dx
                back.append(Site("", "T", x - g.C if x > g.C / 2 else x, y))
        grid = front + back
        for i, s_ in enumerate(grid):
            s_.name, s_.role = f"G{i:03d}", "grid"
        return explicit + spare_sites + grid
    cand = [Site("", "T", x, y) for y in np.linspace(6, 44, 6) for x in np.linspace(-21, 21, 7)]
    dmin = [min(surface_dist(g, c, e) for e in ml_pts) for c in cand]
    keep = np.argsort(dmin)[len(cand) - n_front_grid:]
    front = [cand[i] for i in sorted(keep)]
    back = []
    for y in np.linspace(8, 42, 4):
        for dx in (-18, -6, 6, 18):
            x = g.C / 2 + dx
            back.append(Site("", "T", x - g.C if x > g.C / 2 else x, y))
    grid = front + back[:n_back_grid]
    for i, s in enumerate(grid):
        s.name, s.role = f"G{i:02d}", "grid"
    return explicit + spare_sites + grid


# --------------------------------------------------------------------------- #
# Leads
# --------------------------------------------------------------------------- #
WCT = ("RA", "LA", "LL")
TWELVE_LEADS = {
    "I": ("LA", "RA"), "II": ("LL", "RA"), "III": ("LL", "LA"),
    "aVR": ("RA", "LA", "LL"), "aVL": ("LA", "RA", "LL"), "aVF": ("LL", "RA", "LA"),
    **{f"V{i}": (f"V{i}",) + WCT for i in range(1, 7)},
}


def nearest_substitute(g: Garment, sites: list[Site]) -> dict[str, tuple[str, float]]:
    """Closest non-12-lead site (spare if present, else grid) for each 12-lead site."""
    out = {}
    others = [s for s in sites if s.role != "12lead"]
    for s in sites:
        if s.role != "12lead":
            continue
        d = [surface_dist(g, s, q) for q in others]
        j = int(np.argmin(d))
        out[s.name] = (others[j].name, float(d[j]))
    return out


# --------------------------------------------------------------------------- #
# Hub reference point (L1 median) - used to pick the root orchestrator
# --------------------------------------------------------------------------- #
def torso_point_dists(g: Garment, sites: list[Site], x: float, y: float) -> np.ndarray:
    p = Site("hub", "T", x, y)
    return np.array([surface_dist(g, p, s) for s in sites])


def central_hub(g: Garment, sites: list[Site], step: float = 1.0) -> tuple[float, float]:
    best, arg = np.inf, (0.0, g.H / 2)
    for x in np.arange(-g.C / 2 + step, g.C / 2 + 1e-9, step):
        for y in np.arange(0, g.H + 1e-9, step):
            tot = torso_point_dists(g, sites, x, y).sum()
            if tot < best:
                best, arg = tot, (float(x), float(y))
    return arg


# --------------------------------------------------------------------------- #
# Capacitated clustering on the surface metric (any cluster size)
# --------------------------------------------------------------------------- #
def capacitated_clusters(D: np.ndarray, cap: int, iters: int = 20) -> tuple[list[list[int]], list[int]]:
    """
    Split points into ceil(N/cap) clusters of at most `cap` members, minimizing
    total member-to-medoid routing distance. Farthest-point seeding, then
    alternating capacitated assignment (Hungarian on replicated medoids) and
    medoid update. Returns (clusters, medoids) as indices into D.
    """
    n = D.shape[0]
    if cap >= n:
        return [list(range(n))], [int(np.argmin(D.sum(axis=1)))]
    if cap == 1:
        return [[i] for i in range(n)], list(range(n))
    k = int(np.ceil(n / cap))
    med = [int(np.argmax(D.sum(axis=1)))]
    while len(med) < k:
        med.append(int(np.argmax(D[:, med].min(axis=1))))
    for _ in range(iters):
        cols = np.repeat(np.arange(k), cap)                     # each medoid offers `cap` slots
        cost = D[:, [med[c] for c in cols]]
        rows, cidx = linear_sum_assignment(cost)
        lab = np.empty(n, int)
        lab[rows] = cols[cidx]
        new = []
        for c in range(k):
            mem = np.where(lab == c)[0]
            if len(mem) == 0:
                new.append(med[c])
                continue
            sub = D[np.ix_(mem, mem)]
            new.append(int(mem[np.argmin(sub.sum(axis=1))]))
        if new == med:
            break
        med = new
    clusters = [[int(i) for i in np.where(lab == c)[0]] for c in range(k)]
    clusters = [c for c in clusters if c]
    if cap <= 8:
        clusters = _swap_refine(D, clusters)
    meds = [c[int(np.argmin(D[np.ix_(c, c)].sum(axis=1)))] for c in clusters]
    return clusters, meds


def _swap_refine(D: np.ndarray, clusters: list[list[int]], passes: int = 4) -> list[list[int]]:
    """Pairwise member swaps between clusters that lower total member-to-medoid distance."""
    def cost(c):
        sub = D[np.ix_(c, c)]
        return sub.sum(axis=1).min()
    cl = [list(c) for c in clusters]
    cs = [cost(c) for c in cl]
    for _ in range(passes):
        improved = False
        for a in range(len(cl)):
            for b in range(a + 1, len(cl)):
                for i in range(len(cl[a])):
                    for j in range(len(cl[b])):
                        A, B = cl[a][:], cl[b][:]
                        A[i], B[j] = B[j], A[i]
                        ca, cb = cost(A), cost(B)
                        if ca + cb < cs[a] + cs[b] - 1e-9:
                            cl[a], cl[b], cs[a], cs[b] = A, B, ca, cb
                            improved = True
        if not improved:
            break
    return cl


# --------------------------------------------------------------------------- #
# Link graphs: star, bus (multidrop chain), mesh (THReaD-like 4-port neighbour mesh)
# --------------------------------------------------------------------------- #
def _mesh_edges(Dsub: np.ndarray, ports: int = 4) -> np.ndarray:
    """Symmetric neighbour graph: MST (connectivity) + each node's nearest neighbours up to `ports`."""
    m = Dsub.shape[0]
    A = np.zeros_like(Dsub)
    if m < 2:
        return A
    mst = minimum_spanning_tree(csr_matrix(Dsub)).toarray()
    A[mst > 0] = Dsub[mst > 0]
    A = np.maximum(A, A.T)
    for i in range(m):
        for j in np.argsort(Dsub[i])[1:]:
            if (A[i] > 0).sum() >= ports:
                break
            if (A[j] > 0).sum() < ports and A[i, j] == 0:
                A[i, j] = A[j, i] = Dsub[i, j]
    return A


def _bridges(A: np.ndarray) -> int:
    """Number of links whose single failure disconnects the graph."""
    edges = [(i, j) for i in range(A.shape[0]) for j in range(i + 1, A.shape[0]) if A[i, j] > 0]
    count = 0
    for i, j in edges:
        B = A.copy()
        B[i, j] = B[j, i] = 0
        if connected_components(csr_matrix(B > 0), directed=False)[0] > 1:
            count += 1
    return count


@dataclass
class LinkLevel:
    """Wiring between a set of endpoints and their sink (area head or root)."""
    yarn_cm: float = 0.0          # installed digital yarn (per link pair of wires, counted once)
    bitm_cm: float = 0.0          # sum over sources of routed path length to the sink
    hops: int = 0                 # sum over sources of router hops to the sink
    max_path_cm: float = 0.0
    bridges: int = 0              # single-link faults that disconnect something
    links: int = 0
    per_src: dict = field(default_factory=dict)   # source site index -> (path_cm, hops)
    degree: dict = field(default_factory=dict)    # vertex site index -> number of link ports used


def link_level(D: np.ndarray, members: list[int], sink: int, topo: str) -> LinkLevel:
    """members/sink are indices into D (site indices). sink must be in members."""
    idx = list(members)
    s = idx.index(sink)
    Dsub = D[np.ix_(idx, idx)]
    m = len(idx)
    if m < 2:
        return LinkLevel()
    if topo == "star":
        d = Dsub[s]
        ps = {idx[t]: (float(d[t]), 1) for t in range(m) if t != s}
        deg = {idx[t]: (m - 1 if t == s else 1) for t in range(m)}
        return LinkLevel(float(d.sum()), float(d.sum()), m - 1, float(d.max()), m - 1, m - 1, ps, deg)
    if topo == "bus":
        # multidrop chain from the sink; every bit charges the whole bus
        rem = [i for i in range(m) if i != s]
        cur, length, order = s, 0.0, [s]
        while rem:
            j = min(rem, key=lambda r: Dsub[cur, r])
            length += Dsub[cur, j]
            cur = j
            rem.remove(j)
            order.append(j)
        ps = {idx[t]: (float(length), 1) for t in range(m) if t != s}   # multidrop: whole bus per bit
        deg = {idx[t]: (1 if t in (order[0], order[-1]) else 2) for t in range(m)}   # daisy-chained bus
        return LinkLevel(length, length * (m - 1), m - 1, length, 1, m - 1, ps, deg)
    if topo == "mesh":
        A = _mesh_edges(Dsub)
        dist, pred = dijkstra(csr_matrix(A), directed=False, indices=s, return_predecessors=True)
        hops, ps = 0, {}
        for t in range(m):
            v, h = t, 0
            while v != s and v >= 0:
                v = pred[v]
                h += 1
            hops += h
            if t != s:
                ps[idx[t]] = (float(dist[t]), h)
        deg = {idx[t]: int((A[t] > 0).sum()) for t in range(m)}
        return LinkLevel(float(A.sum() / 2), float(dist.sum()), hops, float(dist.max()),
                         _bridges(A), int((A > 0).sum() // 2), ps, deg)
    raise ValueError(topo)


# --------------------------------------------------------------------------- #
# One architecture point: (m, n, intra-area topology, inter-area topology)
# --------------------------------------------------------------------------- #
@dataclass
class Point:
    m: int                         # electrodes per sensor node (ADC)
    n: int                         # sensor nodes per area (per SoC orchestrator)
    intra: str                     # sensor node -> head: star | bus | mesh
    inter: str                     # head -> root: star | mesh
    n_nodes: int
    n_areas: int
    analog_total_cm: float
    analog_max_cm: float
    intra_lv: LinkLevel
    inter_lv: LinkLevel
    leads_in_node: int             # 12-lead leads formed in analog on one sensor node
    leads_in_area: int             # formed by digital subtraction at one area head
    leads_cross_area: int          # need data from >1 area (root or WCT broadcast)
    nodes_local_lead: int          # sensor nodes that can form >=1 local bipolar lead >= min spacing
    node_clusters: list = field(repr=False, default_factory=list)
    node_sites: list = field(repr=False, default_factory=list)
    areas: list = field(repr=False, default_factory=list)       # lists of node indices
    heads: list = field(repr=False, default_factory=list)       # site index of each head
    root: int = -1                                              # site index of root head
    node_pads: list = field(default_factory=list)               # IO pads per sensor chiplet (H-15)
    soc_pads: list = field(default_factory=list)                # IO pads per orchestrator chiplet (H-15)


def build_point(g: Garment, sites: list[Site], D: np.ndarray, m: int, n: int,
                intra: str = "mesh", inter: str = "mesh", hub_xy=None,
                min_lead_spacing_cm: float = 5.0, ports_cap: int = 4) -> Point:
    N = len(sites)
    hub_xy = hub_xy or central_hub(g, sites)
    node_cl, node_site = capacitated_clusters(D, m)
    analog = np.array([D[i, node_site[c]] for c, mem in enumerate(node_cl) for i in mem])

    # Areas: cluster sensor nodes (by their site positions) into groups of <= n nodes
    Dn = D[np.ix_(node_site, node_site)]
    area_cl, area_med = capacitated_clusters(Dn, n)
    heads = [node_site[a] for a in area_med]                 # SoC sits beside its area's medoid node
    hub_d = torso_point_dists(g, sites, *hub_xy)
    root = min(heads, key=lambda h: hub_d[h])

    # Intra-area links: sensor nodes -> head (summed over areas)
    intra_tot = LinkLevel()
    intra_deg = {}
    for a, mem in enumerate(area_cl):
        lv = link_level(D, [node_site[i] for i in mem], heads[a], intra)
        intra_deg[a] = lv.degree
        for f in ("yarn_cm", "bitm_cm", "hops", "bridges", "links"):
            setattr(intra_tot, f, getattr(intra_tot, f) + getattr(lv, f))
        intra_tot.max_path_cm = max(intra_tot.max_path_cm, lv.max_path_cm)
        intra_tot.per_src.update(lv.per_src)
    inter_lv = link_level(D, heads, root, inter)

    # Lead locality
    names = [s.name for s in sites]
    node_of = {names[i]: c for c, mem in enumerate(node_cl) for i in mem}
    area_of_node = {i: a for a, mem in enumerate(area_cl) for i in mem}
    in_node = in_area = cross = 0
    for els in TWELVE_LEADS.values():
        nodes = {node_of[e] for e in els}
        areas = {area_of_node[x] for x in nodes}
        if len(nodes) == 1:
            in_node += 1
        elif len(areas) == 1:
            in_area += 1
        else:
            cross += 1

    local = sum(1 for mem in node_cl
                if len(mem) > 1 and D[np.ix_(mem, mem)].max() >= min_lead_spacing_cm)

    # IO pads (H-15): electrode inputs + 2 pads (SCLK, SDIO) per link port.
    # Star and bus links need dedicated ports. Mesh links share one router whose ports are capped
    # at ports_cap (THReaD: N/E/S/W); extra mesh adjacency is reached by forwarding through neighbours.
    # A sensor node co-located with its head uses one local port to the SoC.
    def ports(dedicated, mesh):
        return dedicated + min(mesh, ports_cap)
    node_pads, soc_pads = [], []
    area_of = {c: a for a, mem in enumerate(area_cl) for c in mem}
    for c, mem in enumerate(node_cl):
        a = area_of[c]
        site = node_site[c]
        if site == heads[a] or len(area_cl[a]) == 1:
            pr = 1
        else:
            d = intra_deg[a].get(site, 1)
            pr = ports(0, d) if intra == "mesh" else d
        node_pads.append(len(mem) + 2 * pr)
    for a, h in enumerate(heads):
        d_in = intra_deg[a].get(h, 0) if len(area_cl[a]) > 1 else 0
        d_out = inter_lv.degree.get(h, 0) if len(heads) > 1 else 0
        ded, mesh_ports = 0, 0
        if intra == "mesh":
            mesh_ports += d_in + 1                                # local node joins the router's port pool
        else:
            ded += d_in + 1                                       # local port to the co-located node
        if inter == "mesh":
            mesh_ports += d_out
        else:
            ded += d_out
        soc_pads.append(2 * ports(ded, mesh_ports))

    return Point(m, n, intra, inter, len(node_cl), len(area_cl),
                 float(analog.sum()), float(analog.max()), intra_tot, inter_lv,
                 in_node, in_area, cross, local, node_cl, node_site, area_cl, heads, root,
                 node_pads, soc_pads)
