#!/usr/bin/env python3
"""
Analyze Kyla Younger's BaTiO3 Quantum ESPRESSO SCF convergence campaign.

The raw outputs are single-point SCF calculations on a 40-atom tetragonal
BaTiO3 supercell. They are intended to certify the total-energy/basis/k-mesh
part of the Paper 1 convergence story, not to replace DFPT response-property
convergence for soft modes and electro-optic tensors.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


RY_TO_EV = 13.605693122994
N_ATOMS = 40

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = ROOT / "convergence_study" / "kyla_younger_scf_20260525" / "raw"
DEFAULT_OUT_DIR = ROOT / "convergence_study" / "kyla_younger_scf_20260525" / "processed"
DEFAULT_FIG_DIR = ROOT / "figures"

FILENAME_RE = re.compile(r"^(PBEsol|PBE)_(?P<ecut>\d+)_(?P<kmesh>\d+)_scf\.out$")


@dataclass(frozen=True)
class ScfRun:
    functional: str
    ecut_ry: int
    kmesh: int
    total_energy_ry: float
    scf_accuracy_ry: float | None
    scf_iterations: int | None
    cpu_time_s: float | None
    wall_time_s: float | None
    converged: bool
    job_done: bool
    source_file: str


def _last_float(pattern: str, text: str) -> float | None:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    return float(matches[-1]) if matches else None


def _first_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def parse_scf_output(path: Path) -> ScfRun:
    match = FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(f"Unexpected SCF filename: {path.name}")

    text = path.read_text(encoding="utf-8", errors="replace")
    total_energy = _last_float(r"!\s+total energy\s+=\s+([-0-9.]+)\s+Ry", text)
    if total_energy is None:
        raise ValueError(f"No final total energy found in {path}")

    scf_accuracy = _last_float(r"estimated scf accuracy\s+<\s+([0-9.Ee+-]+)\s+Ry", text)
    scf_iterations = _first_int(r"convergence has been achieved in\s+(\d+)\s+iterations", text)

    timing_match = re.search(
        r"PWSCF\s+:\s+([0-9.]+)s CPU\s+([0-9.]+)s WALL", text, flags=re.MULTILINE
    )
    cpu_time = float(timing_match.group(1)) if timing_match else None
    wall_time = float(timing_match.group(2)) if timing_match else None

    return ScfRun(
        functional=match.group(1),
        ecut_ry=int(match.group("ecut")),
        kmesh=int(match.group("kmesh")),
        total_energy_ry=total_energy,
        scf_accuracy_ry=scf_accuracy,
        scf_iterations=scf_iterations,
        cpu_time_s=cpu_time,
        wall_time_s=wall_time,
        converged="convergence has been achieved" in text,
        job_done="JOB DONE" in text,
        source_file=path.name,
    )


def load_runs(raw_dir: Path) -> list[ScfRun]:
    runs = [parse_scf_output(path) for path in sorted(raw_dir.glob("*_scf.out"))]
    if not runs:
        raise SystemExit(f"No *_scf.out files found in {raw_dir}")
    return runs


def best_by_functional(runs: list[ScfRun]) -> dict[str, ScfRun]:
    best: dict[str, ScfRun] = {}
    for functional in sorted({run.functional for run in runs}):
        subset = [run for run in runs if run.functional == functional]
        best[functional] = max(subset, key=lambda run: (run.ecut_ry, run.kmesh))
    return best


def row_with_delta(run: ScfRun, reference: ScfRun) -> dict[str, object]:
    delta_ry_cell = run.total_energy_ry - reference.total_energy_ry
    delta_ev_cell = delta_ry_cell * RY_TO_EV
    delta_mev_atom = delta_ev_cell * 1000.0 / N_ATOMS
    return {
        **asdict(run),
        "total_energy_ev_per_atom": run.total_energy_ry * RY_TO_EV / N_ATOMS,
        "delta_to_best_ev_cell": delta_ev_cell,
        "delta_to_best_mev_atom": delta_mev_atom,
        "abs_delta_to_best_mev_atom": abs(delta_mev_atom),
        "reference_file": reference.source_file,
    }


def build_rows(runs: list[ScfRun]) -> list[dict[str, object]]:
    references = best_by_functional(runs)
    rows = [row_with_delta(run, references[run.functional]) for run in runs]
    return sorted(rows, key=lambda row: (str(row["functional"]), int(row["ecut_ry"]), int(row["kmesh"])))


def first_cutoff_below(rows: list[dict[str, object]], functional: str, threshold_mev_atom: float) -> int | None:
    by_cutoff = sorted({int(row["ecut_ry"]) for row in rows if row["functional"] == functional})
    for ecut in by_cutoff:
        subset = [
            row
            for row in rows
            if row["functional"] == functional and int(row["ecut_ry"]) == ecut
        ]
        if subset and max(float(row["abs_delta_to_best_mev_atom"]) for row in subset) <= threshold_mev_atom:
            return ecut
    return None


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    summary: dict[str, object] = {"n_atoms": N_ATOMS, "n_runs": len(rows), "functionals": {}}
    for functional in sorted({str(row["functional"]) for row in rows}):
        subset = [row for row in rows if row["functional"] == functional]
        max_ecut = max(int(row["ecut_ry"]) for row in subset)
        at_max = [row for row in subset if int(row["ecut_ry"]) == max_ecut]
        kmesh_span = (
            max(float(row["delta_to_best_mev_atom"]) for row in at_max)
            - min(float(row["delta_to_best_mev_atom"]) for row in at_max)
        )
        production_like = [
            row
            for row in subset
            if int(row["ecut_ry"]) == 60 and int(row["kmesh"]) == 6
        ]
        summary["functionals"][functional] = {
            "n_runs": len(subset),
            "ecut_ry_values": sorted({int(row["ecut_ry"]) for row in subset}),
            "kmesh_values": sorted({int(row["kmesh"]) for row in subset}),
            "reference_file": next(
                row["source_file"]
                for row in subset
                if int(row["ecut_ry"]) == max_ecut
                and int(row["kmesh"]) == max(int(r["kmesh"]) for r in subset)
            ),
            "first_cutoff_all_k_below_10_mev_atom": first_cutoff_below(rows, functional, 10.0),
            "first_cutoff_all_k_below_1_mev_atom": first_cutoff_below(rows, functional, 1.0),
            "kmesh_span_at_max_cutoff_mev_atom": kmesh_span,
            "production_60ry_6_delta_mev_atom": (
                float(production_like[0]["delta_to_best_mev_atom"]) if production_like else None
            ),
            "max_scf_accuracy_ry": max(
                float(row["scf_accuracy_ry"])
                for row in subset
                if row["scf_accuracy_ry"] is not None
            ),
            "all_converged": all(bool(row["converged"]) and bool(row["job_done"]) for row in subset),
        }
    return summary


def write_csv(rows: list[dict[str, object]], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "scf_convergence_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def scf_energy_tier(total_abs_mev_atom: float) -> str:
    """Assign a diagnostic tier for absolute total-energy convergence.

    These thresholds are intentionally not the relative property tiers used for
    tensor certificates. They summarize numerical total-energy convergence only.
    """

    if total_abs_mev_atom <= 1.0:
        return "Green"
    if total_abs_mev_atom <= 15.0:
        return "Amber"
    return "Red"


def build_scf_energy_certificates(rows: list[dict[str, object]]) -> dict[str, object]:
    certificates: list[dict[str, object]] = []
    for row in rows:
        value_ev_atom = float(row["total_energy_ev_per_atom"])
        convergence_mev_atom = float(row["abs_delta_to_best_mev_atom"])
        scf_accuracy_ry = row["scf_accuracy_ry"]
        scf_residual_mev_atom = (
            abs(float(scf_accuracy_ry)) * RY_TO_EV * 1000.0 / N_ATOMS
            if scf_accuracy_ry is not None
            else None
        )
        total_abs_mev_atom = math.sqrt(
            convergence_mev_atom**2 + (scf_residual_mev_atom or 0.0) ** 2
        )
        relative_percent = total_abs_mev_atom / 1000.0 / abs(value_ev_atom) * 100.0
        certificates.append(
            {
                "parameter": "total_energy_per_atom",
                "value": value_ev_atom,
                "unit": "eV/atom",
                "uncertainties": {
                    "convergence_abs_mev_per_atom": convergence_mev_atom,
                    "scf_residual_abs_mev_per_atom": scf_residual_mev_atom,
                    "total_abs_mev_per_atom": total_abs_mev_atom,
                    "relative_percent": relative_percent,
                },
                "quality_tier": scf_energy_tier(total_abs_mev_atom),
                "tier_basis": {
                    "quantity": "absolute total-energy convergence",
                    "green_abs_mev_per_atom_max": 1.0,
                    "amber_abs_mev_per_atom_max": 15.0,
                    "note": (
                        "Diagnostic SCF energy tiers are not interchangeable "
                        "with relative Green/Amber/Red tensor-property tiers."
                    ),
                },
                "scope": (
                    "SCF total-energy numerical convergence only; does not "
                    "certify DFPT phonons, Born charges, dielectric tensors, "
                    "or electro-optic response properties."
                ),
                "provenance": {
                    "code": "Quantum ESPRESSO",
                    "functional": row["functional"],
                    "ecut_ry": int(row["ecut_ry"]),
                    "kpoint_mesh": [int(row["kmesh"])] * 3,
                    "n_atoms": N_ATOMS,
                    "source_file": row["source_file"],
                    "reference_file": row["reference_file"],
                    "converged": bool(row["converged"]),
                    "job_done": bool(row["job_done"]),
                },
            }
        )
    return {
        "metadata": {
            "schema": "qff.paper1.scf_energy_certificate_set.v1",
            "n_certificates": len(certificates),
            "n_atoms": N_ATOMS,
            "description": (
                "SCF total-energy convergence certificates derived from "
                "Kyla Younger's BaTiO3 convergence campaign."
            ),
            "fusion_warning": (
                "Do not inverse-variance-fuse different cutoffs or k-meshes as "
                "independent estimates of the same property; these records are "
                "intended for convergence-model calibration and SI diagnostics."
            ),
        },
        "certificates": certificates,
    }


def write_scf_energy_certificates(rows: list[dict[str, object]], out_dir: Path) -> tuple[Path, Path]:
    certificate_set = build_scf_energy_certificates(rows)
    json_path = out_dir / "scf_energy_certificates.json"
    json_path.write_text(json.dumps(certificate_set, indent=2), encoding="utf-8")

    csv_path = out_dir / "scf_energy_certificates.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "functional",
            "ecut_ry",
            "kmesh",
            "value_ev_atom",
            "convergence_abs_mev_per_atom",
            "scf_residual_abs_mev_per_atom",
            "total_abs_mev_per_atom",
            "relative_percent",
            "quality_tier",
            "source_file",
            "reference_file",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for cert in certificate_set["certificates"]:
            uncertainty = cert["uncertainties"]
            provenance = cert["provenance"]
            writer.writerow(
                {
                    "functional": provenance["functional"],
                    "ecut_ry": provenance["ecut_ry"],
                    "kmesh": provenance["kpoint_mesh"][0],
                    "value_ev_atom": cert["value"],
                    "convergence_abs_mev_per_atom": uncertainty[
                        "convergence_abs_mev_per_atom"
                    ],
                    "scf_residual_abs_mev_per_atom": uncertainty[
                        "scf_residual_abs_mev_per_atom"
                    ],
                    "total_abs_mev_per_atom": uncertainty["total_abs_mev_per_atom"],
                    "relative_percent": uncertainty["relative_percent"],
                    "quality_tier": cert["quality_tier"],
                    "source_file": provenance["source_file"],
                    "reference_file": provenance["reference_file"],
                }
            )
    return json_path, csv_path


def plot_convergence(rows: list[dict[str, object]], fig_dir: Path) -> tuple[Path, Path]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), sharey=True)
    colors = {4: "#4C72B0", 6: "#55A868", 8: "#C44E52", 10: "#8172B2"}

    for ax, functional in zip(axes, ["PBE", "PBEsol"], strict=True):
        subset = [row for row in rows if row["functional"] == functional]
        for kmesh in sorted({int(row["kmesh"]) for row in subset}):
            line = sorted(
                [row for row in subset if int(row["kmesh"]) == kmesh],
                key=lambda row: int(row["ecut_ry"]),
            )
            xs = [int(row["ecut_ry"]) for row in line]
            ys = [max(float(row["abs_delta_to_best_mev_atom"]), 1e-4) for row in line]
            ax.plot(xs, ys, marker="o", lw=1.8, color=colors.get(kmesh), label=f"{kmesh}x{kmesh}x{kmesh}")

        ax.axhline(10.0, color="#666666", ls="--", lw=0.9)
        ax.axhline(1.0, color="#999999", ls=":", lw=0.9)
        ax.set_title(functional)
        ax.set_xlabel("plane-wave cutoff (Ry)")
        ax.set_yscale("log")
        ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.5)
        ax.legend(frameon=False, fontsize=8)

    axes[0].set_ylabel(r"$|\Delta E|$ vs highest-grid reference (meV/atom)")
    fig.suptitle("BaTiO3 40-atom SCF convergence campaign (K. Younger)")
    fig.tight_layout()

    pdf_path = fig_dir / "fig4_scf_convergence.pdf"
    png_path = fig_dir / "fig4_scf_convergence.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return pdf_path, png_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    args = parser.parse_args()

    runs = load_runs(args.raw_dir)
    rows = build_rows(runs)
    summary = summarize(rows)

    csv_path = write_csv(rows, args.out_dir)
    json_path = args.out_dir / "scf_convergence_summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    certificate_json_path, certificate_csv_path = write_scf_energy_certificates(
        rows, args.out_dir
    )
    pdf_path, png_path = plot_convergence(rows, args.fig_dir)

    print("Kyla Younger SCF convergence analysis complete")
    print(f"  runs: {summary['n_runs']}")
    for functional, fs in summary["functionals"].items():
        print(
            f"  {functional}: first <=1 meV/atom cutoff = "
            f"{fs['first_cutoff_all_k_below_1_mev_atom']} Ry; "
            f"k-span at max cutoff = {fs['kmesh_span_at_max_cutoff_mev_atom']:.4g} meV/atom; "
            f"60 Ry/6^3 delta = {fs['production_60ry_6_delta_mev_atom']}"
        )
    print(f"  wrote: {csv_path}")
    print(f"  wrote: {json_path}")
    print(f"  wrote: {certificate_json_path}")
    print(f"  wrote: {certificate_csv_path}")
    print(f"  wrote: {pdf_path}")
    print(f"  wrote: {png_path}")


if __name__ == "__main__":
    main()
