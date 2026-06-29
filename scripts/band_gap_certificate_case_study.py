#!/usr/bin/env python3
"""Generate the Paper 1 band-gap certificate case study artifacts.

The case study deliberately keeps the target observable explicit. Semilocal
Kohn-Sham gaps are useful evidence about a calculation, but they are not
exchangeable with optical or quasiparticle gaps without a calibrated reduction
map. The generated artifacts expose that distinction rather than hiding it in a
single inverse-variance average.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "bto_literature_library.json"
OUT_DIR = ROOT / "outputs" / "band_gap_certificate"
FIG_DIR = ROOT / "figures"


@dataclass(frozen=True)
class GapEvidence:
    record_id: str
    value: float
    sigma: float
    unit: str
    target_observable: str
    method_class: str
    functional: str
    source: str
    doi: str
    phase: str
    exchangeability_group: str
    physical_gap_evidence: bool
    notes: str


def _quality_tier(relative_uncertainty: float) -> str:
    if relative_uncertainty < 0.05:
        return "Green"
    if relative_uncertainty < 0.15:
        return "Amber"
    return "Red"


def _total_percent(components: dict[str, float]) -> float:
    return math.sqrt(sum(float(value) ** 2 for value in components.values()))


def _load_gap_evidence() -> list[GapEvidence]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    raw_entries = payload["database"]["E_gap"]["tetragonal"]
    evidence: list[GapEvidence] = []
    for raw in raw_entries:
        evidence.append(
            GapEvidence(
                record_id=str(raw["record_id"]),
                value=float(raw["value"]),
                sigma=float(raw["sigma"]),
                unit=str(raw.get("unit", "eV")),
                target_observable=str(raw["target_observable"]),
                method_class=str(raw["method_class"]),
                functional=str(raw["functional"]),
                source=str(raw["source"]),
                doi=str(raw.get("doi", "")),
                phase="tetragonal",
                exchangeability_group=str(raw["exchangeability_group"]),
                physical_gap_evidence=bool(raw.get("physical_gap_evidence", False)),
                notes=str(raw.get("notes", "")),
            )
        )
    return evidence


def _component_model(entry: GapEvidence) -> dict[str, float]:
    """Return Paper-1-style relative-percent uncertainty components."""

    convergence = abs(entry.sigma / entry.value) * 100.0
    if entry.method_class == "semilocal_ks":
        # SC40 benchmark-scale semilocal bias plus the DFT derivative
        # discontinuity/observable-mismatch floor.
        method = 42.0 if entry.functional == "LDA" else 38.0
        intrinsic = 25.0
        model = 0.0
    elif entry.method_class == "tb_mbj_proxy":
        method = 15.0
        intrinsic = 10.0
        model = 6.0
    elif entry.method_class == "hybrid_ks_proxy":
        # Generic HSE06 is closer to the physical gap, but until Julien's
        # calibrated HSE parameter study is imported it remains a proxy.
        method = 15.0
        intrinsic = 8.0
        model = 8.0
    elif entry.method_class == "optical_experiment":
        method = 0.0
        intrinsic = 0.0
        model = 0.0
    else:
        method = 25.0
        intrinsic = 15.0
        model = 10.0
    return {
        "convergence": convergence,
        "methodological": method,
        "intrinsic_dft": intrinsic,
        "model_form": model,
    }


def _certificate_for_entry(entry: GapEvidence, optical_reference: GapEvidence) -> dict[str, Any]:
    components = _component_model(entry)
    total_percent = _total_percent(components)
    rel_to_optical = (entry.value - optical_reference.value) / optical_reference.value
    return {
        "parameter": f"E_gap_{entry.record_id}",
        "value": entry.value,
        "unit": entry.unit,
        "uncertainties": {
            **{key: round(value, 3) for key, value in components.items()},
            "total": round(total_percent, 3),
        },
        "quality_tier": _quality_tier(total_percent / 100.0),
        "target_observable": entry.target_observable,
        "phase": entry.phase,
        "exchangeability_group": entry.exchangeability_group,
        "physical_gap_evidence": entry.physical_gap_evidence,
        "relative_offset_from_optical_reference_percent": round(rel_to_optical * 100.0, 3),
        "provenance": {
            "functional": entry.functional,
            "method_class": entry.method_class,
            "source": entry.source,
            "doi": entry.doi,
            "notes": entry.notes,
        },
    }


def _naive_fusion(entries: list[GapEvidence]) -> dict[str, float]:
    values = np.array([entry.value for entry in entries], dtype=float)
    sigmas = np.array([entry.sigma for entry in entries], dtype=float)
    weights = 1.0 / sigmas**2
    mean = float(np.sum(weights * values) / np.sum(weights))
    sigma = float(math.sqrt(1.0 / np.sum(weights)))
    spread = float(np.std(values, ddof=0))
    return {
        "mean_eV": mean,
        "formal_sigma_eV": sigma,
        "method_spread_eV": spread,
        "total_sigma_eV": math.sqrt(sigma**2 + spread**2),
    }


def build_case_study() -> dict[str, Any]:
    entries = _load_gap_evidence()
    optical_refs = [entry for entry in entries if entry.method_class == "optical_experiment"]
    if len(optical_refs) != 1:
        raise SystemExit("Expected exactly one optical experimental reference in E_gap data.")
    optical_reference = optical_refs[0]

    certificates = [_certificate_for_entry(entry, optical_reference) for entry in entries]
    semilocal = [entry for entry in entries if entry.method_class == "semilocal_ks"]
    physical = [entry for entry in entries if entry.physical_gap_evidence]

    physical_fusion = _naive_fusion(physical)
    all_naive_fusion = _naive_fusion(entries)
    formal_gap_certificate = {
        "parameter": "E_gap_optical_typed",
        "value": round(physical_fusion["mean_eV"], 3),
        "unit": "eV",
        "uncertainties": {
            "convergence": 3.125,
            "methodological": 15.0,
            "intrinsic_dft": 8.0,
            "model_form": 8.0,
            "total": round(_total_percent(
                {
                    "convergence": 3.125,
                    "methodological": 15.0,
                    "intrinsic_dft": 8.0,
                    "model_form": 8.0,
                }
            ), 3),
        },
        "quality_tier": "Red",
        "target_observable": "room-temperature optical band gap",
        "phase": "tetragonal",
        "exchangeability_group": "physical optical-gap evidence only",
        "non_exchangeability_rule": (
            "Semilocal Kohn-Sham gaps are retained as Red-tier evidence but "
            "excluded from optical-gap fusion unless a calibrated reduction "
            "map is supplied."
        ),
        "provenance": {
            "physical_evidence_record_ids": [entry.record_id for entry in physical],
            "excluded_semilocal_record_ids": [entry.record_id for entry in semilocal],
            "pending_calibration": (
                "Import Julien's HSE06 exact-exchange calibration study before "
                "using a calibrated-hybrid certificate as an Amber/Green prior."
            ),
        },
    }

    return {
        "metadata": {
            "schema": "qff.paper1.band_gap_certificate_case_study.v1",
            "n_evidence_records": len(entries),
            "n_method_certificates": len(certificates),
            "target_material": "tetragonal BaTiO3",
            "purpose": (
                "Promoted Paper 1 case study showing that posterior "
                "certificates preserve target-observable typing for band gaps."
            ),
        },
        "optical_reference": {
            "record_id": optical_reference.record_id,
            "value": optical_reference.value,
            "sigma": optical_reference.sigma,
            "source": optical_reference.source,
        },
        "method_certificates": certificates,
        "formal_band_gap_certificate": formal_gap_certificate,
        "diagnostics": {
            "physical_gap_fusion": physical_fusion,
            "naive_all_evidence_fusion_disallowed": all_naive_fusion,
            "naive_fusion_warning": (
                "The all-evidence fusion is intentionally reported only as a "
                "diagnostic anti-example because it mixes non-exchangeable "
                "Kohn-Sham, proxy, and optical target observables."
            ),
        },
    }


def write_csv(case_study: dict[str, Any]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "band_gap_certificate_case_study.csv"
    rows = []
    for cert in case_study["method_certificates"]:
        uncertainties = cert["uncertainties"]
        provenance = cert["provenance"]
        rows.append(
            {
                "parameter": cert["parameter"],
                "value_eV": cert["value"],
                "sigma_total_percent": uncertainties["total"],
                "quality_tier": cert["quality_tier"],
                "target_observable": cert["target_observable"],
                "method_class": provenance["method_class"],
                "functional": provenance["functional"],
                "exchangeability_group": cert["exchangeability_group"],
                "physical_gap_evidence": cert["physical_gap_evidence"],
                "relative_offset_from_optical_reference_percent": cert[
                    "relative_offset_from_optical_reference_percent"
                ],
                "source": provenance["source"],
                "doi": provenance["doi"],
            }
        )

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def plot_case_study(case_study: dict[str, Any]) -> tuple[Path, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    certs = case_study["method_certificates"]
    labels = [
        cert["provenance"]["functional"].replace("Experiment", "Optical exp.")
        for cert in certs
    ]
    values = np.array([cert["value"] for cert in certs], dtype=float)
    sigma = np.array(
        [
            cert["value"] * cert["uncertainties"]["convergence"] / 100.0
            for cert in certs
        ],
        dtype=float,
    )
    totals = np.array([cert["uncertainties"]["total"] for cert in certs], dtype=float)
    method = np.array([cert["uncertainties"]["methodological"] for cert in certs], dtype=float)
    intrinsic = np.array([cert["uncertainties"]["intrinsic_dft"] for cert in certs], dtype=float)
    model = np.array([cert["uncertainties"]["model_form"] for cert in certs], dtype=float)
    convergence = np.array([cert["uncertainties"]["convergence"] for cert in certs], dtype=float)
    x = np.arange(len(certs))

    colors = []
    for cert in certs:
        method_class = cert["provenance"]["method_class"]
        if method_class == "semilocal_ks":
            colors.append("#C44E52")
        elif method_class == "optical_experiment":
            colors.append("#55A868")
        else:
            colors.append("#4C72B0")

    fig, axes = plt.subplots(2, 1, figsize=(9.2, 7.2), gridspec_kw={"height_ratios": [1.05, 1]})
    optical_ref = case_study["optical_reference"]["value"]

    axes[0].bar(x, values, yerr=sigma, color=colors, alpha=0.86, edgecolor="#222222", linewidth=0.5)
    axes[0].axhspan(optical_ref - 0.1, optical_ref + 0.1, color="#55A868", alpha=0.14, label="optical reference")
    axes[0].axhline(optical_ref, color="#2F6F46", lw=1.2)
    axes[0].set_ylabel("gap (eV)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=20, ha="right")
    axes[0].set_title("a) Band-gap evidence is target-observable typed", loc="left", fontweight="bold")
    bar_h = 0.18
    y = np.arange(len(certs))
    axes[1].barh(y - 1.5 * bar_h, convergence, height=bar_h, color="#4477AA", label="convergence")
    axes[1].barh(y - 0.5 * bar_h, method, height=bar_h, color="#CC6677", label="methodological")
    axes[1].barh(y + 0.5 * bar_h, intrinsic, height=bar_h, color="#666666", hatch="///", label="intrinsic DFT")
    axes[1].barh(y + 1.5 * bar_h, model, height=bar_h, color="#DDAA33", hatch="...", label="model-form")
    axes[1].scatter(totals, y, color="#111111", s=24, zorder=4, label="quadrature total")
    axes[1].axvline(5, color="#2E8B57", linestyle="--", linewidth=1.0)
    axes[1].axvline(15, color="#CC3333", linestyle="--", linewidth=1.0)
    axes[1].set_yticks(y)
    axes[1].set_yticklabels(labels)
    axes[1].set_xlabel("relative uncertainty (%)")
    axes[1].set_title("b) Physical-gap certificates expose method-form risk", loc="left", fontweight="bold")
    axes[1].legend(frameon=False, ncol=3, fontsize=8)
    axes[1].set_xlim(0, max(52, float(np.max(totals)) + 5))
    axes[1].invert_yaxis()

    fig.tight_layout()
    pdf_path = FIG_DIR / "figS_band_gap_certificate.pdf"
    png_path = FIG_DIR / "figS_band_gap_certificate.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return pdf_path, png_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    case_study = build_case_study()
    json_path = OUT_DIR / "band_gap_certificate_case_study.json"
    json_path.write_text(json.dumps(case_study, indent=2), encoding="utf-8")
    csv_path = write_csv(case_study)
    pdf_path, png_path = plot_case_study(case_study)

    formal = case_study["formal_band_gap_certificate"]
    print("Band-gap certificate case study complete")
    print(
        "  formal optical-gap certificate: "
        f"{formal['value']} eV, tier {formal['quality_tier']}, "
        f"total sigma {formal['uncertainties']['total']}%"
    )
    print(f"  wrote: {json_path}")
    print(f"  wrote: {csv_path}")
    print(f"  wrote: {pdf_path}")
    print(f"  wrote: {png_path}")


if __name__ == "__main__":
    main()
