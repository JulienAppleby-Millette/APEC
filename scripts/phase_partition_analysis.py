#!/usr/bin/env python3
"""Reproduce the phase/tensor partitioning analysis for the APECs case study.

The script evaluates the soft-mode model for the five input conventions shown
in the main text and applies the same floor-aware uncertainty policy used for
Table II. It is intentionally self-contained so that the repository can run
without any external development package.
"""

from __future__ import annotations

import math


R_REF_PM_PER_V = 105.0
W_REF_CM = 180.0
Z_REF_E = 7.16
EPS_REF = 6.5
SIGMA_CONV_PCT = 6.5
SIGMA_METHOD_PCT = 17.8
SIGMA_DFT_PCT = 11.2
SIGMA_MODEL_PCT = 17.9
FUSED_EFFECTIVE_SAMPLE_SIZE = 5.0


def soft_mode_r33(omega_cm: float, z_star: float, eps_inf: float) -> float:
    """Return r33 in pm/V from the calibrated soft-mode expression."""
    return (
        R_REF_PM_PER_V
        * (W_REF_CM / omega_cm) ** 2
        * (z_star / Z_REF_E) ** 2
        * (EPS_REF / eps_inf)
    )


def r33_uncertainty_pct(kind: str) -> float:
    """Return the manuscript uncertainty policy for one r33 convention."""
    if kind == "single_calc":
        sigma_method = SIGMA_METHOD_PCT
    elif kind == "fused":
        sigma_method = SIGMA_METHOD_PCT / math.sqrt(FUSED_EFFECTIVE_SAMPLE_SIZE)
    else:
        raise ValueError(f"unknown uncertainty kind: {kind}")
    return math.sqrt(
        SIGMA_CONV_PCT**2
        + sigma_method**2
        + SIGMA_DFT_PCT**2
        + SIGMA_MODEL_PCT**2
    )


def main() -> None:
    conventions = [
        {
            "name": "Unpartitioned library",
            "kind": "fused",
            "omega": 176.0,
            "z_star": 7.29,
            "eps_inf": 6.51,
        },
        {
            "name": "Tetragonal, isotropic avg",
            "kind": "fused",
            "omega": 172.0,
            "z_star": 6.85,
            "eps_inf": 6.31,
        },
        {
            "name": "Tetragonal, zz only",
            "kind": "fused",
            "omega": 172.0,
            "z_star": 6.20,
            "eps_inf": 5.96,
        },
        {
            "name": "Single calc, zz",
            "kind": "single_calc",
            "omega": 172.0,
            "z_star": 6.20,
            "eps_inf": 5.96,
        },
        {
            "name": "Single calc, iso",
            "kind": "single_calc",
            "omega": 172.0,
            "z_star": 6.85,
            "eps_inf": 6.32,
        },
    ]

    print("=" * 78)
    print("Phase partition analysis: effect on derived r33")
    print("=" * 78)
    print(
        f"Reference values: r_ref={R_REF_PM_PER_V} pm/V, "
        f"omega_ref={W_REF_CM} cm^-1, Z_ref={Z_REF_E} e, eps_ref={EPS_REF}"
    )
    print(
        "Uncertainty policy: conv=6.5%, method=17.8%, intrinsic DFT=11.2%, "
        "model=17.9%; method averages down only for fused rows"
    )
    print()
    print(
        f"{'Convention':<30s} {'Z*':>7s} {'eps':>7s} {'omega':>7s} "
        f"{'r33':>8s} {'sigma':>8s} {'abs':>8s}"
    )
    print("-" * 78)

    for row in conventions:
        r33 = soft_mode_r33(row["omega"], row["z_star"], row["eps_inf"])
        sigma_pct = r33_uncertainty_pct(row["kind"])
        abs_unc = r33 * sigma_pct / 100.0
        print(
            f"{row['name']:<30s} {row['z_star']:7.2f} {row['eps_inf']:7.2f} "
            f"{row['omega']:7.0f} {r33:8.0f} {sigma_pct:7.1f}% {abs_unc:8.0f}"
        )

    print("-" * 78)
    print(f"{'Experiment (bulk, 300 K)':<30s} {'---':>7s} {'---':>7s} "
          f"{'---':>7s} {105:8.0f} {'---':>8s} {15:8.0f}")
    print()
    print("Key findings:")
    print("  1. The unpartitioned library inflates r33 because cubic-reference Z* enters.")
    print("  2. Phase-filtered isotropic inputs give 108 pm/V, matching the calibrated bulk scale.")
    print("  3. Single-calculation values match the library when tensor convention is fixed.")
    print("  4. The 94 vs 108 pm/V spread quantifies tensor-averaging sensitivity.")


if __name__ == "__main__":
    main()
