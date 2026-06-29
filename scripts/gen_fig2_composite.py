#!/usr/bin/env python3
"""Generate Figure 2: certificate decomposition plus example JSON record."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "posterior_certificates.json"
FIG_DIR = ROOT / "figures"

plt.rcParams.update(
    {
        "font.size": 11,
        "font.family": "serif",
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9,
        "figure.dpi": 300,
    }
)


LABELS = {
    "Z_star_Ti_mean": r"$Z^*_{\mathrm{Ti}}$ (mean)",
    "Z_star_Ti_zz": r"$Z^*_{\mathrm{Ti},zz}$",
    "Z_star_O_zz_axial": r"$Z^*_{\mathrm{O},zz}$ (axial)",
    "Z_star_Ba_mean": r"$Z^*_{\mathrm{Ba}}$ (mean)",
    "epsilon_inf_xx": r"$\varepsilon^\infty_{xx}$",
    "epsilon_inf_zz": r"$\varepsilon^\infty_{zz}$",
    "omega_soft": r"$\omega_{\mathrm{soft}}$",
    "omega_soft_z": r"$\omega_{\mathrm{soft},z}$",
    "c_over_a": r"$c/a$ ratio",
    "a_lattice": r"$a$ (lattice)",
    "r_33_zz": r"$r_{33}$ ($zz$)",
    "r_33_iso": r"$r_{33}$ (iso)",
    "E_gap_optical_typed": r"$E_g$ optical (typed)",
}


def _format_value(certificate: dict) -> str:
    value = float(certificate["value"])
    unit = str(certificate["unit"])
    parameter = str(certificate["parameter"])
    if unit == "e":
        return f"{value:.2f} $e$"
    if unit == "angstrom":
        return f"{value:.3f} $\\AA$"
    if unit == "cm-1":
        return f"{value:.0f} cm$^{{-1}}$"
    if unit == "pm/V":
        return f"{value:.0f} pm/V"
    if unit == "eV":
        return f"{value:.2f} eV"
    if parameter == "c_over_a":
        return f"{value:.3f}"
    if unit == "dimensionless":
        return f"{value:.2f}"
    return f"{value:.3g} {unit}"


def load_certificates() -> tuple[list[dict], dict]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return list(payload["certificates"]), dict(payload["metadata"])


def _example_certificate(certificate: dict) -> dict:
    provenance = dict(certificate.get("provenance", {}))
    if certificate["parameter"] == "E_gap_optical_typed":
        return {
            "parameter": certificate["parameter"],
            "value": certificate["value"],
            "unit": certificate["unit"],
            "target_observable": certificate["target_observable"],
            "quality_tier": certificate["quality_tier"],
            "uncertainties": certificate["uncertainties"],
            "non_exchangeability_rule": certificate["non_exchangeability_rule"],
            "provenance": {
                "phase": provenance.get("phase"),
                "physical_evidence": provenance.get("physical_evidence_record_ids"),
                "excluded_evidence": provenance.get("excluded_semilocal_record_ids"),
                "calibration_status": provenance.get("calibration_status"),
            },
            "schema_version": "posterior-certificate-v1",
        }
    return certificate


def draw_certificate_bars(ax: plt.Axes, certificates: list[dict]) -> None:
    y_pos = np.arange(len(certificates))
    sigma_conv = np.array(
        [float(cert["uncertainties"].get("convergence", 0.0)) for cert in certificates]
    )
    sigma_meth = np.array(
        [float(cert["uncertainties"].get("methodological", 0.0)) for cert in certificates]
    )
    sigma_dft = np.array(
        [float(cert["uncertainties"].get("intrinsic_dft", 0.0)) for cert in certificates]
    )
    sigma_model = np.array(
        [float(cert["uncertainties"].get("model_form", 0.0)) for cert in certificates]
    )
    sigma_total = np.array(
        [
            float(
                cert["uncertainties"].get(
                    "total",
                    np.sqrt(
                        sigma_conv[i] ** 2
                        + sigma_meth[i] ** 2
                        + sigma_dft[i] ** 2
                        + sigma_model[i] ** 2
                    ),
                )
            )
            for i, cert in enumerate(certificates)
        ]
    )

    ax.barh(
        y_pos,
        sigma_total,
        height=0.65,
        color="#E8E8E8",
        edgecolor="#CCCCCC",
        linewidth=0.5,
        zorder=1,
    )

    bar_h = 0.14
    offsets = [-1.5 * bar_h, -0.5 * bar_h, 0.5 * bar_h, 1.5 * bar_h]

    ax.barh(
        y_pos + offsets[0],
        sigma_conv,
        height=bar_h,
        color="#4477AA",
        alpha=0.9,
        label=r"$\sigma_{\mathrm{conv}}$",
        zorder=2,
    )
    ax.barh(
        y_pos + offsets[1],
        sigma_meth,
        height=bar_h,
        color="#CC6677",
        alpha=0.9,
        label=r"$\sigma_{\mathrm{method}}$",
        zorder=2,
    )
    ax.barh(
        y_pos + offsets[2],
        sigma_dft,
        height=bar_h,
        color="#666666",
        alpha=0.9,
        hatch="///",
        edgecolor="#444444",
        linewidth=0.3,
        label=r"$\sigma_{\mathrm{DFT}}$",
        zorder=2,
    )

    model_vals = np.where(sigma_model > 0, sigma_model, np.nan)
    ax.barh(
        y_pos + offsets[3],
        model_vals,
        height=bar_h,
        color="#DDAA33",
        alpha=0.9,
        hatch="...",
        edgecolor="#AA7700",
        linewidth=0.3,
        label=r"$\sigma_{\mathrm{model}}$",
        zorder=2,
    )

    ax.axvline(x=5, color="#2E8B57", linestyle="--", linewidth=1.2, alpha=0.75, zorder=3)
    ax.axvline(x=15, color="#CC3333", linestyle="--", linewidth=1.2, alpha=0.75, zorder=3)

    ax.text(2.5, -1.25, "Green", ha="center", fontsize=11, color="#2E8B57", fontweight="bold")
    ax.text(10, -1.25, "Amber", ha="center", fontsize=11, color="#CC8800", fontweight="bold")
    ax.text(32, -1.25, "Red", ha="center", fontsize=11, color="#CC3333", fontweight="bold")

    for i, st in enumerate(sigma_total):
        label = f"{st:.1f}%" if st >= 10 else f"{st:.2f}%"
        ax.text(st + 0.35, i, label, va="center", fontsize=9, color="#333333")

    ax.axhline(y=9.5, xmin=0, xmax=1, color="#CCCCCC", linewidth=0.5, linestyle=":", zorder=0)
    ax.axhline(y=11.5, xmin=0, xmax=1, color="#CCCCCC", linewidth=0.5, linestyle=":", zorder=0)

    ylabels = [
        f"{LABELS.get(cert['parameter'], cert['parameter'])}  =  {_format_value(cert)}"
        for cert in certificates
    ]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(ylabels, fontsize=9, color="#222222")
    ax.set_xlabel(r"Relative uncertainty, $\sigma/|P|$ (%)")
    ax.set_xlim(0, max(32.0, float(np.max(sigma_total)) + 4.0))
    ax.set_ylim(len(certificates) - 0.5, -1.9)
    ax.legend(loc="upper right", framealpha=0.95, ncol=2, bbox_to_anchor=(0.99, 0.93))
    ax.set_title("a) Certificate uncertainty decomposition", loc="left", fontweight="bold")


def draw_json_panel(ax: plt.Axes, certificates: list[dict]) -> None:
    ax.axis("off")
    ax.set_title("b) Typed band-gap JSON certificate", loc="left", fontweight="bold", pad=10)

    band_gap = next(
        cert for cert in certificates if cert["parameter"] == "E_gap_optical_typed"
    )
    code = json.dumps(_example_certificate(band_gap), indent=2)
    ax.text(
        0.03,
        0.97,
        code,
        va="top",
        ha="left",
        family="DejaVu Sans Mono",
        fontsize=7.25,
        color="#111111",
        transform=ax.transAxes,
        bbox={
            "boxstyle": "round,pad=0.55",
            "facecolor": "#F7F7F2",
            "edgecolor": "#CCCCCC",
            "linewidth": 0.8,
        },
    )
    ax.text(
        0.03,
        0.05,
        "All uncertainty components are relative percentages.\n"
        "The band-gap record demonstrates target-observable typing.",
        va="bottom",
        ha="left",
        fontsize=8.5,
        color="#444444",
        transform=ax.transAxes,
    )


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    certificates, _metadata = load_certificates()
    fig = plt.figure(figsize=(14.6, 9.2))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.9, 1.15], wspace=0.24)
    ax_bars = fig.add_subplot(grid[0, 0])
    ax_json = fig.add_subplot(grid[0, 1])

    draw_certificate_bars(ax_bars, certificates)
    draw_json_panel(ax_json, certificates)

    fig.savefig(FIG_DIR / "fig2_composite.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig2_composite.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Figure saved: fig2_composite.pdf and fig2_composite.png")


if __name__ == "__main__":
    main()
