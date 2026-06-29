#!/usr/bin/env python3
"""Self-contained extraction case study for the APECs support repository.

The manuscript describes a retrospective extraction workflow that merges
curated DFPT literature, public database-style records, a production Quantum
ESPRESSO calculation, and experimental calibration/check targets. This script
does not require any external development package. It reads the public
``data/bto_literature_library.json`` file and emits a compact audit summary of
the source classes, weighted tetragonal averages, phase/tensor partitions, and
experimental check targets used in the paper.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "bto_literature_library.json"
OUT_PATH = ROOT / "outputs" / "extraction_case_study_summary.json"

R_REF_PM_PER_V = 105.0
W_REF_CM = 180.0
Z_REF_E = 7.16
EPS_REF = 6.5


def load_library() -> dict[str, Any]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def iter_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prop, phases in payload["database"].items():
        for phase, entries in phases.items():
            for entry in entries:
                row = dict(entry)
                row["property"] = prop
                row["phase"] = phase
                row["component"] = row.get("component", "isotropic_or_unspecified")
                rows.append(row)
    return rows


def source_class(entry: dict[str, Any]) -> str:
    source = entry.get("source", "")
    functional = entry.get("functional", "")
    if functional.lower() in {"expt", "experiment", "experimental"}:
        return "experimental_reference"
    if "This work" in source:
        return "production_qe"
    if "PhononDB" in source:
        return "phonondb"
    if "Materials Project" in source or source.startswith("mp-"):
        return "materials_project"
    return "curated_literature"


def inverse_variance_average(entries: list[dict[str, Any]]) -> dict[str, float] | None:
    usable = [entry for entry in entries if entry.get("sigma") not in (None, 0)]
    if not usable:
        return None
    weights = [1.0 / float(entry["sigma"]) ** 2 for entry in usable]
    values = [float(entry["value"]) for entry in usable]
    weight_sum = sum(weights)
    mean = sum(w * v for w, v in zip(weights, values)) / weight_sum
    sigma = math.sqrt(1.0 / weight_sum)
    return {"mean": mean, "sigma": sigma, "n": len(usable)}


def soft_mode_r33(omega_cm: float, z_star: float, eps_inf: float) -> float:
    return (
        R_REF_PM_PER_V
        * (W_REF_CM / omega_cm) ** 2
        * (z_star / Z_REF_E) ** 2
        * (EPS_REF / eps_inf)
    )


def weighted_tetragonal_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for prop in ["omega_soft", "Z_star_Ti", "epsilon_inf", "P_s", "lattice_a"]:
        prop_rows = [
            row
            for row in rows
            if row["property"] == prop
            and row["phase"] == "tetragonal"
            and source_class(row) != "experimental_reference"
        ]
        by_component: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in prop_rows:
            by_component[row["component"]].append(row)
        summary[prop] = {
            component: inverse_variance_average(component_rows)
            for component, component_rows in sorted(by_component.items())
        }
    return summary


def phase_partition_rows() -> list[dict[str, Any]]:
    cases = [
        ("unpartitioned_library", 176.0, 7.29, 6.51),
        ("tetragonal_isotropic_avg", 172.0, 6.85, 6.31),
        ("tetragonal_zz_only", 172.0, 6.20, 5.96),
        ("single_calc_zz", 172.0, 6.20, 5.96),
        ("single_calc_iso", 172.0, 6.85, 6.32),
    ]
    return [
        {
            "case": name,
            "omega_soft_cm-1": omega,
            "Z_star_Ti": z_star,
            "epsilon_inf": eps,
            "r33_pm_per_V": round(soft_mode_r33(omega, z_star, eps), 3),
        }
        for name, omega, z_star, eps in cases
    ]


def build_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = iter_entries(payload)
    counts_by_source_class: dict[str, int] = defaultdict(int)
    counts_by_property: dict[str, int] = defaultdict(int)
    for row in rows:
        counts_by_source_class[source_class(row)] += 1
        counts_by_property[row["property"]] += 1

    return {
        "metadata": payload.get("metadata", {}),
        "n_database_entries": len(rows),
        "counts_by_source_class": dict(sorted(counts_by_source_class.items())),
        "counts_by_property": dict(sorted(counts_by_property.items())),
        "weighted_tetragonal_summary": weighted_tetragonal_summary(rows),
        "phase_partition_r33_rows": phase_partition_rows(),
        "experimental_references": payload.get("experimental_references", []),
        "source_policy": {
            "curated_literature": "quantitative fusion input when phase/component typed",
            "production_qe": "certificate generation input and library cross-check",
            "phonondb": "typed literature/database support",
            "materials_project": "retrospective extraction stress test unless fully typed",
            "experimental_reference": "calibration/check target, not a DFT fusion row",
        },
    }


def main() -> None:
    payload = load_library()
    summary = build_summary(payload)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Extraction case study summary")
    print("=" * 78)
    print(f"Database entries: {summary['n_database_entries']}")
    print("Source classes:")
    for name, count in summary["counts_by_source_class"].items():
        print(f"  {name}: {count}")
    print()
    print("Phase/tensor r33 checks:")
    for row in summary["phase_partition_r33_rows"]:
        print(f"  {row['case']}: r33 = {row['r33_pm_per_V']:.1f} pm/V")
    print()
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
