"""Generate the Paper 1 graphical abstract.

The abstract is intentionally schematic and data-light: it summarizes the
posterior-certificate workflow without duplicating Fig. 2. Outputs are written
as SVG, PDF, and high-resolution PNG for manuscript portals and slide reuse.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphical_abstract"
FIG_WIDTH = 14
FIG_HEIGHT = 6.6
X_ASPECT_COMP = FIG_HEIGHT / FIG_WIDTH


COLORS = {
    "blue": "#005493",  # UVic blue
    "gold": "#F5AA1C",
    "ink": "#17202A",
    "muted": "#5B6770",
    "pale_blue": "#E8F2FA",
    "pale_gold": "#FFF4D8",
    "green": "#2C8C5A",
    "amber": "#D89000",
    "red": "#C44545",
    "grey": "#EEF1F4",
    "dark_grey": "#B7C0C8",
    "purple": "#6F4A8E",
    "component_blue": "#3B6EA8",
    "component_teal": "#4C8FA3",
    "component_indigo": "#6B6FAE",
    "component_slate": "#6F7F91",
}


def rounded_box(ax, xy, w, h, fc, ec="#CBD3DA", lw=1.4, radius=0.025, z=1):
    box = patches.FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle=patches.BoxStyle("Round", pad=0.012, rounding_size=radius),
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        zorder=z,
    )
    ax.add_patch(box)
    return box


def arrow(ax, start, end, color=None, lw=2.2, z=4):
    if color is None:
        color = COLORS["blue"]
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=lw,
            color=color,
            shrinkA=0,
            shrinkB=0,
        ),
        zorder=z,
    )


def atom_sphere(ax, xy, r, fc, ec="white", lw=0.6, z=6):
    """Small shaded atom marker for schematic crystal drawings."""
    width = 2 * r * X_ASPECT_COMP
    height = 2 * r
    ax.add_patch(patches.Ellipse(xy, width, height, fc=fc, ec=ec, lw=lw, zorder=z))
    ax.add_patch(
        patches.Ellipse(
            (xy[0] - 0.15 * r, xy[1] + 0.35 * r),
            0.55 * r * X_ASPECT_COMP,
            0.55 * r,
            fc="white",
            ec="none",
            alpha=0.35,
            zorder=z + 1,
        )
    )


def draw_orbitals(ax, center, s):
    """Subtle schematic Ti-centered orbital lobes."""
    cx, cy = center
    orbital_color = "#7FB6D6"
    for angle in [0, 90]:
        ax.add_patch(
            patches.Ellipse(
                (cx, cy),
                0.30 * s * X_ASPECT_COMP,
                0.090 * s,
                angle=angle,
                fc=orbital_color,
                ec=COLORS["blue"],
                lw=0.6,
                alpha=0.27,
                zorder=7,
            )
        )
    for dx, dy in [(0.055 * s, 0.040 * s), (-0.055 * s, -0.040 * s)]:
        atom_sphere(ax, (cx + dx, cy + dy), 0.025 * s, "#BFD7E8", ec="#EAF3F8", lw=0.4, z=7)


def draw_unit_cell(ax, cx, cy, s, show_orbitals=False):
    """Stylized BaTiO3 perovskite cell."""
    # Back and front near-cubic tetragonal rectangles, linked as a simple pseudo-3D cell.
    # Room-temperature BaTiO3 has only slight tetragonality, so keep the icon close to cubic.
    c_over_a = 1.012
    a_x = s * X_ASPECT_COMP
    c_y = s * c_over_a
    dx, dy = 0.26 * s * X_ASPECT_COMP, 0.20 * s
    def project(u, v, z):
        return np.array([cx + (u - 0.5) * a_x + z * dx, cy + (v - 0.5) * c_y + z * dy])

    front = np.array(
        [
            project(0, 0, 0),
            project(1, 0, 0),
            project(1, 1, 0),
            project(0, 1, 0),
        ]
    )
    back = np.array(
        [
            project(0, 0, 1),
            project(1, 0, 1),
            project(1, 1, 1),
            project(0, 1, 1),
        ]
    )
    for p, q in zip(front, back):
        ax.plot([p[0], q[0]], [p[1], q[1]], color=COLORS["muted"], lw=1.2, zorder=3)
    ax.add_patch(patches.Polygon(back, fill=False, ec=COLORS["muted"], lw=1.2, zorder=3))
    ax.add_patch(patches.Polygon(front, fill=False, ec=COLORS["ink"], lw=1.5, zorder=4))

    # BaTiO3 perovskite motif: large Ba at cube corners, O at face centers,
    # and a smaller Ti displaced from the body center.
    for p in list(front) + list(back):
        atom_sphere(ax, p, 0.070 * s, COLORS["green"], z=6)

    oxygen_face_centers = [
        project(0.5, 0.5, 0),  # front face
        project(0.5, 0.5, 1),  # back face
        project(0.5, 0, 0.5),  # bottom face
        project(0.5, 1, 0.5),  # top face
        project(0, 0.5, 0.5),  # left face
        project(1, 0.5, 0.5),  # right face
    ]
    for p in oxygen_face_centers:
        atom_sphere(ax, p, 0.056 * s, COLORS["red"], z=7)

    ti_center = project(0.56, 0.54, 0.55)
    if show_orbitals:
        draw_orbitals(ax, ti_center, s)
    atom_sphere(ax, ti_center, 0.038 * s, COLORS["blue"], lw=0.8, z=8)
    ax.annotate(
        "",
        xy=(ti_center[0], ti_center[1] + 0.14 * s),
        xytext=(ti_center[0], ti_center[1] + 0.035 * s),
        arrowprops=dict(arrowstyle="-|>", mutation_scale=11, lw=1.2, color=COLORS["blue"]),
        zorder=9,
    )
    ax.text(ti_center[0] + 0.025 * s, ti_center[1] + 0.135 * s, r"$P$", fontsize=10, color=COLORS["blue"], weight="bold")

    # Minimal atom key, inside the DFT panel and separated from the crystal drawing.
    legend_x = cx + 0.42 * s
    legend_y = cy + 0.23 * s
    for i, (name, col) in enumerate([("Ba", COLORS["green"]), ("Ti", COLORS["blue"]), ("O", COLORS["red"])]):
        lx = legend_x
        ly = legend_y - i * 0.17 * s
        legend_r = {"Ba": 0.026 * s, "Ti": 0.017 * s, "O": 0.022 * s}[name]
        atom_sphere(ax, (lx, ly), legend_r, col, z=9)
        ax.text(lx + 0.022 * s, ly, name, fontsize=7.3, va="center", ha="left", color=COLORS["muted"], zorder=10)


def draw_soft_mode(ax, x0, y0, w, h):
    ax.text(x0 + 0.50 * w, y0 + 0.82 * h, "soft-mode bottleneck", ha="center", va="center", fontsize=13, weight="bold", color=COLORS["ink"])
    ax.text(
        x0 + 0.50 * w,
        y0 + 0.66 * h,
        r"$r_{33}\ \propto\ Z^{*2}/(\varepsilon_\infty\,\omega_\mathrm{soft}^{2})$",
        ha="center",
        va="center",
        fontsize=12.3,
        color=COLORS["ink"],
    )

    # Nonlinear propagation sketch: a narrow input band on omega maps through
    # a curved inverse-square response into a broader output band in r33.
    gx0, gy0 = x0 + 0.13 * w, y0 + 0.26 * h
    gw, gh = 0.74 * w, 0.30 * h
    ax.plot([gx0, gx0 + gw], [gy0, gy0], color="#CAD2DA", lw=1.0, zorder=4)
    ax.plot([gx0, gx0], [gy0, gy0 + gh], color="#CAD2DA", lw=1.0, zorder=4)
    xs = np.linspace(0.16, 0.92, 180)
    curve = 1.0 / (xs + 0.22) ** 2
    curve = (curve - curve.min()) / (curve.max() - curve.min())
    px = gx0 + xs * gw
    py = gy0 + (0.10 + 0.78 * curve) * gh
    ax.plot(px, py, color=COLORS["blue"], lw=2.0, zorder=6)

    input_x = gx0 + 0.56 * gw
    input_band = 0.055 * gw
    output_y_mid = np.interp(input_x, px, py)
    output_band = 0.22 * gh
    ax.add_patch(
        patches.Rectangle(
            (input_x - input_band / 2, gy0),
            input_band,
            gh,
            fc=COLORS["purple"],
            ec="none",
            alpha=0.13,
            zorder=5,
        )
    )
    ax.add_patch(
        patches.Rectangle(
            (gx0 + gw - 0.045 * gw, output_y_mid - output_band / 2),
            0.045 * gw,
            output_band,
            fc=COLORS["red"],
            ec="none",
            alpha=0.18,
            zorder=5,
        )
    )
    for offset in [-0.5, 0.0, 0.5]:
        xi = input_x + offset * input_band
        yi = np.interp(xi, px, py)
        ax.plot([xi, gx0 + gw - 0.045 * gw], [yi, yi], color=COLORS["red"], lw=0.9, alpha=0.5, zorder=5)
        ax.add_patch(patches.Circle((xi, yi), 0.0065, fc=COLORS["purple"], ec="white", lw=0.4, zorder=7))
        ax.add_patch(patches.Circle((gx0 + gw - 0.045 * gw, yi), 0.0065, fc=COLORS["red"], ec="white", lw=0.4, zorder=7))
    ax.text(gx0 + 0.54 * gw, gy0 - 0.035 * h, r"$\omega_\mathrm{soft}$", ha="center", va="center", fontsize=8.8, color=COLORS["muted"])
    ax.text(gx0 + gw + 0.015 * w, output_y_mid, r"$r_{33}$", ha="left", va="center", fontsize=9.0, color=COLORS["muted"])

    ax.text(
        x0 + 0.50 * w,
        y0 + 0.145 * h,
        r"$5\%$ in $\omega_\mathrm{soft}$  $\rightarrow$  $10\%$ in $r_{33}$",
        ha="center",
        va="center",
        fontsize=10.6,
        color=COLORS["red"],
        weight="bold",
    )
    ax.text(
        x0 + 0.50 * w,
        y0 + 0.055 * h,
        "curvature expands uncertainty",
        ha="center",
        va="center",
        fontsize=9.2,
        color=COLORS["muted"],
    )


def draw_certificate_card(ax, x, y, w, h):
    rounded_box(ax, (x, y), w, h, "#FFFFFF", ec="#C7CED6", lw=1.2, radius=0.018, z=4)
    ax.text(
        x + 0.05 * w,
        y + 0.88 * h,
        "posterior certificate",
        fontsize=13.2,
        weight="bold",
        color=COLORS["ink"],
        zorder=7,
    )
    ax.text(
        x + 0.05 * w,
        y + 0.765 * h,
        "typed observable\nuncertainty budget",
        fontsize=8.7,
        color=COLORS["muted"],
        va="top",
        linespacing=1.08,
        zorder=7,
    )

    labels = [r"$\sigma_\mathrm{conv}$", r"$\sigma_\mathrm{method}$", r"$\sigma_\mathrm{DFT}$", r"$\sigma_\mathrm{model}$"]
    vals = [0.23, 0.40, 0.25, 0.62]
    # Cool/neutral component colors are intentionally distinct from Green/Amber/Red tier semantics.
    cols = [
        COLORS["component_blue"],
        COLORS["component_teal"],
        COLORS["component_indigo"],
        COLORS["component_slate"],
    ]
    y0 = y + 0.535 * h
    for i, (lab, val, col) in enumerate(zip(labels, vals, cols)):
        yy = y0 - i * 0.096 * h
        ax.text(x + 0.06 * w, yy + 0.012, lab, fontsize=10.5, color=COLORS["ink"], va="center", zorder=7)
        ax.add_patch(patches.Rectangle((x + 0.39 * w, yy - 0.010), 0.50 * w, 0.021, fc=COLORS["grey"], ec="none", zorder=5))
        ax.add_patch(patches.Rectangle((x + 0.39 * w, yy - 0.010), 0.50 * w * val, 0.021, fc=col, ec="none", zorder=6))

    tiers = [("Green", COLORS["green"]), ("Amber", COLORS["amber"]), ("Red", COLORS["red"])]
    ax.text(x + 0.06 * w, y + 0.150 * h, "quality tier", fontsize=8.8, color=COLORS["muted"], va="center")
    for i, (name, col) in enumerate(tiers):
        tx = x + (0.305 + i * 0.215) * w
        ax.add_patch(patches.FancyBboxPatch((tx, y + 0.095 * h), 0.185 * w, 0.075 * h, boxstyle="round,pad=0.005,rounding_size=0.010", fc=col, ec="none", zorder=6))
        ax.text(tx + 0.0925 * w, y + 0.132 * h, name, ha="center", va="center", fontsize=8.3, color="white", weight="bold", zorder=7)


def draw_fusion_panel(ax, x, y, w, h):
    rounded_box(ax, (x, y), w, h, COLORS["pale_gold"], ec="#D8B65A", lw=1.2, radius=0.018, z=2)
    ax.text(x + 0.06 * w, y + 0.83 * h, "phase-aware fusion", fontsize=13.5, weight="bold", color=COLORS["ink"])
    ax.text(x + 0.13 * w, y + 0.66 * h, "library", ha="center", fontsize=8.7, color=COLORS["muted"], weight="bold")
    ax.text(x + 0.48 * w, y + 0.66 * h, "typed\nfilter", ha="center", va="center", fontsize=8.2, color=COLORS["muted"], linespacing=1.0, weight="bold")
    ax.text(x + 0.80 * w, y + 0.66 * h, "posterior", ha="center", fontsize=8.7, color=COLORS["muted"], weight="bold")

    # Library entries.
    rng = np.random.default_rng(7)
    for i in range(19):
        px = x + (0.07 + 0.18 * rng.random()) * w
        py = y + (0.31 + 0.25 * rng.random()) * h
        r = (0.009 + 0.007 * rng.random()) * w
        col = [COLORS["green"], COLORS["amber"], COLORS["red"]][i % 3]
        ax.add_patch(patches.Circle((px, py), r, fc=col, ec="white", lw=0.6, alpha=0.85, zorder=5))

    # Explicit filter stage.
    ax.add_patch(
        patches.FancyBboxPatch(
            (x + 0.38 * w, y + 0.34 * h),
            0.20 * w,
            0.20 * h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            fc="#FFFFFF",
            ec="#D8B65A",
            lw=1.0,
            zorder=6,
        )
    )
    ax.text(x + 0.48 * w, y + 0.480 * h, "phase", ha="center", va="center", fontsize=7.6, color=COLORS["ink"], zorder=7)
    ax.text(x + 0.48 * w, y + 0.430 * h, "+", ha="center", va="center", fontsize=8.0, color=COLORS["muted"], zorder=7)
    ax.text(x + 0.48 * w, y + 0.380 * h, "component", ha="center", va="center", fontsize=7.0, color=COLORS["ink"], zorder=7)

    # Posterior estimate as a separated value card.
    ax.add_patch(
        patches.FancyBboxPatch(
            (x + 0.66 * w, y + 0.31 * h),
            0.29 * w,
            0.26 * h,
            boxstyle="round,pad=0.006,rounding_size=0.014",
            fc="#FFFFFF",
            ec="#E2C46E",
            lw=1.0,
            zorder=6,
        )
    )
    ax.text(x + 0.805 * w, y + 0.515 * h, r"$r_{33}$", ha="center", va="center", fontsize=14.5, color=COLORS["blue"], weight="bold", zorder=8)
    ax.text(x + 0.805 * w, y + 0.425 * h, r"$108 \pm 25$", ha="center", va="center", fontsize=9.8, color=COLORS["ink"], weight="bold", zorder=8)
    ax.text(x + 0.805 * w, y + 0.350 * h, r"pm/V, $\sim24\%$", ha="center", va="center", fontsize=8.2, color=COLORS["muted"], zorder=8)

    for start, end in [
        ((x + 0.29 * w, y + 0.44 * h), (x + 0.36 * w, y + 0.44 * h)),
        ((x + 0.60 * w, y + 0.44 * h), (x + 0.64 * w, y + 0.44 * h)),
    ]:
        ax.annotate(
            "",
            xy=end,
            xytext=start,
            arrowprops=dict(arrowstyle="-|>", mutation_scale=10, linewidth=1.3, color=COLORS["blue"]),
            zorder=8,
        )


def draw_json_strip(ax, x, y, w, h):
    rounded_box(ax, (x, y), w, h, "#F8FAFC", ec="#D8DEE6", lw=1.1, radius=0.012, z=2)
    lines = [
        '{ "property": "r33_iso",',
        '  "value": "108 pm/V",',
        '  "sigma_rel": "28.4%",',
        '  "components":',
        '    ["conv", "method",',
        '     "DFT", "model"],',
        '  "quality_tier": "Red"',
        '}',
    ]
    ax.text(x + 0.05 * w, y + 0.86 * h, "machine-readable record", fontsize=10.8, weight="bold", color=COLORS["ink"])
    for i, line in enumerate(lines):
        color = COLORS["red"] if "Red" in line else COLORS["ink"]
        ax.text(x + 0.06 * w, y + (0.69 - i * 0.080) * h, line, fontsize=7.2, family="DejaVu Sans Mono", color=color)


def render_graphical_abstract(show_orbitals=False, suffix="") -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "dejavusans",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )

    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Soft background.
    ax.add_patch(patches.Rectangle((0, 0), 1, 1, fc="#FBFCFE", ec="none", zorder=0))
    ax.add_patch(patches.Rectangle((0, 0.905), 1, 0.095, fc=COLORS["blue"], ec="none", zorder=1))
    ax.text(
        0.035,
        0.952,
        "Posterior error certificates for DFT",
        fontsize=22,
        color="white",
        weight="bold",
        va="center",
    )
    ax.text(
        0.965,
        0.952,
        r"BaTiO$_3$ soft-mode electro-optics",
        fontsize=13.5,
        color="white",
        ha="right",
        va="center",
    )

    # Main panels.
    y_main, h_main = 0.34, 0.50
    panels = [
        (0.035, y_main, 0.205, h_main, COLORS["pale_blue"], "DFT/DFPT calculation"),
        (0.285, y_main, 0.205, h_main, "#FFFFFF", "nonlinear propagation"),
        (0.535, y_main, 0.205, h_main, "#FFFFFF", "certificate object"),
        (0.785, y_main, 0.180, h_main, COLORS["pale_gold"], "library posterior"),
    ]
    for x, y, w, h, fc, title in panels:
        rounded_box(ax, (x, y), w, h, fc, ec="#C6D1DA", lw=1.3, radius=0.02)
        ax.text(x + 0.04 * w, y + 0.90 * h, title, fontsize=12.5, weight="bold", color=COLORS["ink"], zorder=4)

    draw_unit_cell(ax, 0.118, 0.585, 0.150, show_orbitals=show_orbitals)
    ax.text(0.138, 0.462, r"$E_\mathrm{cut}$, $k$-mesh, SCF", ha="center", fontsize=10.6, color=COLORS["ink"])
    ax.text(0.138, 0.421, r"$Z^*$, $\varepsilon_\infty$, $\omega_\mathrm{soft}$", ha="center", fontsize=11.6, color=COLORS["blue"], weight="bold")
    ax.text(0.138, 0.388, "observable-specific\nconvergence evidence", ha="center", va="top", fontsize=9.2, color=COLORS["muted"], linespacing=1.05)

    draw_soft_mode(ax, 0.315, 0.405, 0.145, 0.285)
    draw_certificate_card(ax, 0.552, 0.375, 0.170, 0.370)
    draw_fusion_panel(ax, 0.797, 0.375, 0.155, 0.370)

    arrow(ax, (0.250, 0.590), (0.278, 0.590))
    arrow(ax, (0.500, 0.590), (0.528, 0.590))
    arrow(ax, (0.750, 0.590), (0.778, 0.590))

    # Bottom row: claims and outputs.
    rounded_box(ax, (0.035, 0.105), 0.305, 0.165, "#FFFFFF", ec="#D8DEE6", lw=1.1, radius=0.018)
    ax.text(0.055, 0.228, "What travels with each value", fontsize=13.2, weight="bold", color=COLORS["ink"])
    ax.text(0.055, 0.184, "source labels", fontsize=10.6, color=COLORS["muted"])
    ax.text(0.055, 0.144, "quality tier", fontsize=10.6, color=COLORS["muted"])
    ax.text(0.188, 0.184, "observable type", fontsize=10.6, color=COLORS["muted"])
    ax.text(0.188, 0.144, "propagation rule", fontsize=10.6, color=COLORS["muted"])

    draw_json_strip(ax, 0.370, 0.105, 0.245, 0.165)

    rounded_box(ax, (0.645, 0.105), 0.320, 0.165, "#FFFFFF", ec="#D8DEE6", lw=1.1, radius=0.018)
    ax.text(0.665, 0.228, "Outcome for reusable materials data", fontsize=13.2, weight="bold", color=COLORS["ink"])
    ax.text(0.665, 0.185, r"single calculation: $28.4\%$ Red-tier response", fontsize=10.2, color=COLORS["red"], weight="bold")
    ax.text(0.665, 0.150, r"phase-filtered fusion: $108\pm25$ pm/V", fontsize=10.2, color=COLORS["blue"], weight="bold")
    ax.text(0.665, 0.118, r"floor-limited uncertainty: $\sim24\%$ toward $\sim22\%$", fontsize=9.7, color=COLORS["muted"])

    ax.text(
        0.5,
        0.047,
        "Core idea: DFT values should travel with calibrated uncertainty, provenance, and validity scope.",
        ha="center",
        va="center",
        fontsize=13,
        color=COLORS["ink"],
        weight="bold",
    )

    for ext in ["svg", "pdf", "png"]:
        out = OUT / f"paper1_graphical_abstract{suffix}.{ext}"
        fig.savefig(out, bbox_inches="tight", pad_inches=0.02, dpi=300)
        print(out)
    plt.close(fig)


def main() -> None:
    render_graphical_abstract(show_orbitals=False, suffix="")
    render_graphical_abstract(show_orbitals=False, suffix="_no_orbitals")
    render_graphical_abstract(show_orbitals=True, suffix="_orbitals")


if __name__ == "__main__":
    main()
