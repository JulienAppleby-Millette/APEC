#!/usr/bin/env python3
"""
Calibration check for the BaTiO3 posterior-certificate literature library.

This script implements the first lightweight version of the validation test
suggested during manuscript review:

1. Partition literature entries by property, phase, and tensor component.
2. For every subset with at least three computational entries, perform
   leave-one-out inverse-variance fusion.
3. Report standardized residuals against the held-out entry:

       z_i = (P_i - P_LOO) / sqrt(sigma_i^2 + sigma_LOO^2)

If the certificate sigmas are calibrated and the entries are approximately
exchangeable within each subset, these z-scores should follow N(0, 1).

The current library is intentionally small, so this should be read as a
calibration smoke test rather than a definitive validation campaign.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "bto_literature_library.json"
OUT_DIR = ROOT / "outputs" / "calibration"
FIG_DIR = ROOT / "figures"


@dataclass(frozen=True)
class Entry:
    property: str
    phase: str
    component: str
    value: float
    sigma: float
    functional: str
    source: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.property, self.phase, self.component)


def load_entries() -> tuple[list[Entry], list[dict]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    entries: list[Entry] = []
    for prop, phases in payload["database"].items():
        for phase, raw_entries in phases.items():
            for raw in raw_entries:
                sigma = raw.get("sigma")
                if sigma is None:
                    continue
                entries.append(
                    Entry(
                        property=prop,
                        phase=phase,
                        component=raw.get("component", "isotropic_or_unspecified"),
                        value=float(raw["value"]),
                        sigma=float(sigma),
                        functional=raw.get("functional", "unknown"),
                        source=raw.get("source", "unknown"),
                    )
                )
    return entries, payload.get("experimental_references", [])


def ivw(entries: list[Entry]) -> tuple[float, float]:
    weights = np.array([1.0 / (entry.sigma**2) for entry in entries], dtype=float)
    values = np.array([entry.value for entry in entries], dtype=float)
    mean = float(np.sum(weights * values) / np.sum(weights))
    sigma = float(math.sqrt(1.0 / np.sum(weights)))
    return mean, sigma


def leave_one_out_rows(entries: list[Entry], min_group_size: int = 3) -> list[dict]:
    groups: dict[tuple[str, str, str], list[Entry]] = defaultdict(list)
    for entry in entries:
        if entry.functional.lower() in {"expt", "experiment", "experimental"}:
            continue
        if entry.property == "E_gap":
            # Band-gap records intentionally mix non-exchangeable target types
            # (Kohn-Sham, proxy, and optical). They are audited separately in
            # the typed band-gap case study and are not part of this library
            # calibration smoke test.
            continue
        groups[entry.key].append(entry)

    rows: list[dict] = []
    for key, group in sorted(groups.items()):
        if len(group) < min_group_size:
            continue
        group_mean, group_sigma = ivw(group)
        group_chi2 = sum(((entry.value - group_mean) / entry.sigma) ** 2 for entry in group)
        group_dof = max(len(group) - 1, 1)
        for i, held_out in enumerate(group):
            train = group[:i] + group[i + 1 :]
            pred, pred_sigma = ivw(train)
            denom = math.sqrt(held_out.sigma**2 + pred_sigma**2)
            z = (held_out.value - pred) / denom
            rows.append(
                {
                    "property": key[0],
                    "phase": key[1],
                    "component": key[2],
                    "n_group": len(group),
                    "held_out_value": held_out.value,
                    "held_out_sigma": held_out.sigma,
                    "held_out_functional": held_out.functional,
                    "held_out_source": held_out.source,
                    "loo_prediction": pred,
                    "loo_sigma": pred_sigma,
                    "z_score": z,
                    "abs_z": abs(z),
                    "full_group_mean": group_mean,
                    "full_group_sigma": group_sigma,
                    "full_group_reduced_chi2": group_chi2 / group_dof,
                }
            )
    return rows


def summarize(rows: list[dict], experimental_refs: list[dict]) -> dict:
    z = np.array([row["z_score"] for row in rows], dtype=float)
    abs_z = np.abs(z)
    normal = NormalDist()

    group_summary: dict[str, dict] = {}
    for key in sorted({(r["property"], r["phase"], r["component"]) for r in rows}):
        group_rows = [r for r in rows if (r["property"], r["phase"], r["component"]) == key]
        gz = np.array([r["z_score"] for r in group_rows], dtype=float)
        group_summary["|".join(key)] = {
            "n": len(group_rows),
            "mean_z": float(np.mean(gz)),
            "rms_z": float(math.sqrt(np.mean(gz**2))),
            "max_abs_z": float(np.max(np.abs(gz))),
            "mean_reduced_chi2": float(np.mean([r["full_group_reduced_chi2"] for r in group_rows])),
        }

    # This validation point is the bulk room-temperature comparison reported in
    # the manuscript's Table 5. Thin-film values are deliberately excluded here:
    # they include domain, strain, and device effects outside the bulk model.
    bulk_r33_prediction = {"value": 108.0, "sigma": 22.0, "label": "library_fused_bulk_r33_iso"}
    bulk_refs = [
        ref
        for ref in experimental_refs
        if ref.get("parameter") == "r_33" and "bulk" in ref.get("conditions", "").lower()
    ]
    validation = []
    for ref in bulk_refs:
        denom = math.sqrt(bulk_r33_prediction["sigma"] ** 2 + ref["uncertainty"] ** 2)
        validation.append(
            {
                "prediction": bulk_r33_prediction["label"],
                "predicted_value": bulk_r33_prediction["value"],
                "predicted_sigma": bulk_r33_prediction["sigma"],
                "experimental_value": ref["value"],
                "experimental_sigma": ref["uncertainty"],
                "source": ref["source"],
                "z_score": (bulk_r33_prediction["value"] - ref["value"]) / denom,
            }
        )

    return {
        "n_leave_one_out": int(len(rows)),
        "n_groups": int(len(group_summary)),
        "mean_z": float(np.mean(z)) if len(z) else None,
        "rms_z": float(math.sqrt(np.mean(z**2))) if len(z) else None,
        "reduced_chi2_pooled": float(np.mean(z**2)) if len(z) else None,
        "coverage_abs_z_lt_1": float(np.mean(abs_z < 1.0)) if len(z) else None,
        "coverage_abs_z_lt_1p96": float(np.mean(abs_z < 1.96)) if len(z) else None,
        "expected_abs_z_lt_1": normal.cdf(1.0) - normal.cdf(-1.0),
        "expected_abs_z_lt_1p96": normal.cdf(1.96) - normal.cdf(-1.96),
        "max_abs_z": float(np.max(abs_z)) if len(z) else None,
        "groups": group_summary,
        "experimental_validation": validation,
    }


def write_outputs(rows: list[dict], summary: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    (OUT_DIR / "certificate_library_calibration.json").write_text(
        json.dumps({"summary": summary, "leave_one_out": rows}, indent=2),
        encoding="utf-8",
    )

    with (OUT_DIR / "certificate_library_leave_one_out.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    plot_calibration(rows, summary)


def plot_calibration(rows: list[dict], summary: dict) -> None:
    z = np.array([row["z_score"] for row in rows], dtype=float)
    abs_z = np.sort(np.abs(z))
    normal = NormalDist()

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))

    axes[0].hist(z, bins=np.linspace(-3, 3, 13), density=True, alpha=0.7, color="#4C72B0")
    xs = np.linspace(-3, 3, 300)
    axes[0].plot(xs, [math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi) for x in xs],
                 color="#222222", lw=1.5, label="N(0,1)")
    axes[0].axvline(0, color="#777777", lw=0.8)
    axes[0].set_xlabel("leave-one-out z-score")
    axes[0].set_ylabel("density")
    axes[0].set_title("Signed residuals")
    axes[0].legend(frameon=False)

    empirical_y = np.arange(1, len(abs_z) + 1) / len(abs_z)
    expected_x = np.linspace(0, max(3.0, float(abs_z[-1]) + 0.2), 300)
    expected_y = [normal.cdf(x) - normal.cdf(-x) for x in expected_x]
    axes[1].step(abs_z, empirical_y, where="post", color="#55A868", lw=2.0,
                 label="empirical |z|")
    axes[1].plot(expected_x, expected_y, color="#222222", lw=1.5, label="N(0,1)")
    axes[1].axvline(1.0, color="#777777", ls="--", lw=0.8)
    axes[1].axvline(1.96, color="#777777", ls=":", lw=0.8)
    axes[1].set_xlabel("|z|")
    axes[1].set_ylabel("cumulative fraction")
    axes[1].set_title("Coverage check")
    axes[1].legend(frameon=False)

    fig.suptitle(
        "BaTiO3 certificate-library calibration "
        f"(n={summary['n_leave_one_out']}, rms z={summary['rms_z']:.2f})",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_calibration_check.pdf", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig3_calibration_check.png", bbox_inches="tight", dpi=300)
    plt.close(fig)


def main() -> None:
    entries, experimental_refs = load_entries()
    rows = leave_one_out_rows(entries)
    if not rows:
        raise SystemExit("No leave-one-out groups available.")
    summary = summarize(rows, experimental_refs)
    write_outputs(rows, summary)

    print("Calibration check complete")
    print(f"  leave-one-out residuals: {summary['n_leave_one_out']}")
    print(f"  groups: {summary['n_groups']}")
    print(f"  mean z: {summary['mean_z']:.3f}")
    print(f"  rms z / reduced chi2^0.5: {summary['rms_z']:.3f}")
    print(
        "  coverage |z|<1: "
        f"{summary['coverage_abs_z_lt_1']:.3f} "
        f"(expected {summary['expected_abs_z_lt_1']:.3f})"
    )
    print(
        "  coverage |z|<1.96: "
        f"{summary['coverage_abs_z_lt_1p96']:.3f} "
        f"(expected {summary['expected_abs_z_lt_1p96']:.3f})"
    )
    for validation in summary["experimental_validation"]:
        print(
            "  bulk r33 validation z: "
            f"{validation['z_score']:.3f} vs {validation['source']}"
        )
    print(f"  wrote: {OUT_DIR / 'certificate_library_calibration.json'}")
    print(f"  wrote: {FIG_DIR / 'fig3_calibration_check.pdf'}")


if __name__ == "__main__":
    main()
