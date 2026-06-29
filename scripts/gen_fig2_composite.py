#!/usr/bin/env python3
"""Validate the canonical Figure 2 assets.

Figure 2 in the manuscript is the curated Overleaf composition containing the
certificate decomposition panel and an example JSON certificate panel. A later
experimental generator produced an over-wide variant by mixing the main-text
certificate figure with the supplemental band-gap example. To prevent that
regression, this script validates the checked-in canonical assets by default.

Use ``--regenerate-preview`` only to create a non-authoritative diagnostic
preview under ``outputs/fig2_regeneration_preview.*``. The preview is useful for
checking the data pipeline but does not overwrite the canonical manuscript
figure.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "posterior_certificates.json"
FIG_DIR = ROOT / "figures"
OUT_DIR = ROOT / "outputs"

CANONICAL_PDF = FIG_DIR / "fig2_composite.pdf"
CANONICAL_PNG = FIG_DIR / "fig2_composite.png"
EXPECTED_ASPECT = 1.69
ASPECT_TOLERANCE = 0.08


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
}


def _aspect_ok(aspect: float) -> bool:
    return abs(aspect - EXPECTED_ASPECT) <= ASPECT_TOLERANCE


def _pdf_page_aspect(path: Path) -> float:
    data = path.read_bytes()
    matches = re.findall(rb"/(?:MediaBox|CropBox)\s*\[([^\]]+)\]", data)
    if not matches:
        raise ValueError(f"Could not locate PDF page box in {path}")
    values = [float(item) for item in matches[0].split()]
    if len(values) != 4:
        raise ValueError(f"Unexpected PDF page box in {path}: {matches[0]!r}")
    width = abs(values[2] - values[0])
    height = abs(values[3] - values[1])
    return width / height


def _png_page_aspect(path: Path) -> float:
    with path.open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"{path} is not a PNG file")
        _chunk_len = handle.read(4)
        chunk_type = handle.read(4)
        if chunk_type != b"IHDR":
            raise ValueError(f"{path} does not start with a PNG IHDR chunk")
        width, height = struct.unpack(">II", handle.read(8))
    return width / height


def validate_canonical_assets() -> None:
    missing = [path for path in (CANONICAL_PDF, CANONICAL_PNG) if not path.exists()]
    if missing:
        raise SystemExit(
            "Missing canonical Figure 2 asset(s): "
            + ", ".join(str(path) for path in missing)
        )

    pdf_aspect = _pdf_page_aspect(CANONICAL_PDF)
    png_aspect = _png_page_aspect(CANONICAL_PNG)
    print("Canonical Figure 2 validation")
    print(f"  PDF: {CANONICAL_PDF}")
    print(f"  PDF aspect: {pdf_aspect:.3f}")
    print(f"  PNG: {CANONICAL_PNG}")
    print(f"  PNG aspect: {png_aspect:.3f}")

    if not _aspect_ok(pdf_aspect) or not _aspect_ok(png_aspect):
        raise SystemExit(
            "Figure 2 assets do not match the expected Overleaf aspect ratio. "
            "Do not overwrite the canonical figure with a regenerated preview."
        )

    print("  status: OK")


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
    if parameter == "c_over_a":
        return f"{value:.3f}"
    if unit == "dimensionless":
        return f"{value:.2f}"
    return f"{value:.3g} {unit}"


def _example_certificate(certificate: dict) -> dict:
    provenance = certificate.get("provenance", {})
    return {
        "parameter": certificate["parameter"],
        "value": certificate["value"],
        "unit": certificate["unit"],
        "uncertainties": certificate["uncertainties"],
        "quality_tier": certificate["quality_tier"],
        "provenance": {
            "code": provenance.get("code"),
            "version": provenance.get("version"),
            "functional": provenance.get("functional"),
            "pseudopotential": provenance.get("pseudopotential"),
            "phase": provenance.get("phase"),
            "tensor_component": certificate.get("convention"),
            "energy_cutoff_Ry": provenance.get("energy_cutoff_Ry"),
            "kpoint_mesh": provenance.get("kpoint_mesh"),
            "supercell": provenance.get("supercell"),
            "n_atoms": provenance.get("n_atoms"),
        },
        "calibration": {
            "Z_ref_e": provenance.get("Z_star_ref"),
            "epsilon_ref": provenance.get("eps_inf_ref"),
            "model": "soft-mode r33",
        },
        "schema_version": "posterior-certificate-v1",
    }


def regenerate_preview() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    certificates = [
        cert
        for cert in payload["certificates"]
        if cert["parameter"] in LABELS
    ]
    example = next(cert for cert in certificates if cert["parameter"] == "r_33_iso")

    plt.rcParams.update(
        {
            "font.size": 8,
            "font.family": "serif",
            "axes.labelsize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "figure.dpi": 300,
        }
    )

    fig = plt.figure(figsize=(9.2, 5.45))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.75, 1.0], wspace=0.25)
    ax = fig.add_subplot(grid[0, 0])
    ax_json = fig.add_subplot(grid[0, 1])

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
        [float(cert["uncertainties"].get("total", 0.0)) for cert in certificates]
    )

    ax.barh(y_pos, sigma_total, height=0.65, color="#E8E8E8", edgecolor="#CCCCCC")
    bar_h = 0.14
    offsets = [-1.5 * bar_h, -0.5 * bar_h, 0.5 * bar_h, 1.5 * bar_h]
    ax.barh(y_pos + offsets[0], sigma_conv, height=bar_h, color="#4477AA", label=r"$\sigma_{\mathrm{conv}}$")
    ax.barh(y_pos + offsets[1], sigma_meth, height=bar_h, color="#CC6677", label=r"$\sigma_{\mathrm{method}}$")
    ax.barh(
        y_pos + offsets[2],
        sigma_dft,
        height=bar_h,
        color="#666666",
        hatch="///",
        edgecolor="#444444",
        linewidth=0.3,
        label=r"$\sigma_{\mathrm{DFT}}$",
    )
    model_vals = np.where(sigma_model > 0, sigma_model, np.nan)
    ax.barh(
        y_pos + offsets[3],
        model_vals,
        height=bar_h,
        color="#DDAA33",
        hatch="...",
        edgecolor="#AA7700",
        linewidth=0.3,
        label=r"$\sigma_{\mathrm{model}}$",
    )

    ax.axvline(x=5, color="#2E8B57", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.axvline(x=15, color="#CC3333", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.text(2.5, -1.25, "Green", ha="center", fontsize=8, color="#2E8B57", fontweight="bold")
    ax.text(10, -1.25, "Amber", ha="center", fontsize=8, color="#CC8800", fontweight="bold")
    ax.text(23, -1.25, "Red", ha="center", fontsize=8, color="#CC3333", fontweight="bold")

    for i, st in enumerate(sigma_total):
        label = f"{st:.1f}%" if st >= 10 else f"{st:.2f}%"
        ax.text(st + 0.35, i, label, va="center", fontsize=6, color="#333333")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        [
            f"{LABELS[cert['parameter']]}  =  {_format_value(cert)}"
            for cert in certificates
        ],
        fontsize=6.7,
    )
    ax.set_xlabel(r"Relative uncertainty, $\sigma/|P|$ (%)")
    ax.set_xlim(0, 35)
    ax.set_ylim(len(certificates) - 0.5, -1.9)
    ax.legend(loc="center right", framealpha=0.95, ncol=2)
    ax.set_title("a) Certificate uncertainty decomposition", loc="left", fontweight="bold")

    ax_json.axis("off")
    ax_json.set_title("b) Example JSON certificate", loc="left", fontweight="bold")
    ax_json.text(
        0.03,
        0.97,
        json.dumps(_example_certificate(example), indent=2),
        va="top",
        ha="left",
        family="DejaVu Sans Mono",
        fontsize=4.8,
        color="#111111",
        transform=ax_json.transAxes,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "#F7F7F2",
            "edgecolor": "#CCCCCC",
            "linewidth": 0.6,
        },
    )
    ax_json.text(
        0.03,
        0.05,
        "All uncertainty components are relative percentages.\n"
        "The full table contains one record per certified property.",
        va="bottom",
        ha="left",
        fontsize=6,
        color="#444444",
        transform=ax_json.transAxes,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT_DIR / "fig2_regeneration_preview.pdf"
    png_path = OUT_DIR / "fig2_regeneration_preview.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("Wrote non-authoritative Figure 2 preview:")
    print(f"  {pdf_path}")
    print(f"  {png_path}")
    print("Canonical manuscript assets were not overwritten.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--regenerate-preview",
        action="store_true",
        help="write a diagnostic preview under outputs/ without overwriting canonical assets",
    )
    args = parser.parse_args()

    validate_canonical_assets()
    if args.regenerate_preview:
        regenerate_preview()


if __name__ == "__main__":
    main()
