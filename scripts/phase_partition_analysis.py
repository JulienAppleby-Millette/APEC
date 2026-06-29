#!/usr/bin/env python3
"""Reproduce the phase/tensor partitioning analysis for Paper 1.

The script evaluates the soft-mode model for the five input conventions shown
in the main text. It is intentionally self-contained so that the public support
repository can run without the broader QFF package.
"""

from __future__ import annotations

import math


R_REF_PM_PER_V = 105.0
W_REF_CM = 180.0
Z_REF_E = 7.16
EPS_REF = 6.5
SIGMA_MODEL_PCT = 17.9


def soft_mode_r33(omega_cm: float, z_star: float, eps_inf: float) -> float:
    """Return r33 in pm/V from the calibrated soft-mode expression."""
    return (
        R_REF_PM_PER_V
        * (W_REF_CM / omega_cm) ** 2
        * (z_star / Z_REF_E) ** 2
        * (EPS_REF / eps_inf)
    )


def propagated_uncertainty_pct(
    sigma_omega_pct: float, sigma_z_pct: float, sigma_eps_pct: float
) -> float:
    """Propagate relative input uncertainties and add model form in quadrature."""
    sigma_prop = math.sqrt(
        (2.0 * sigma_omega_pct) ** 2
        + (2.0 * sigma_z_pct) ** 2
        + sigma_eps_pct**2
    )
    return math.sqrt(sigma_prop**2 + SIGMA_MODEL_PCT**2)


def main() -> None:
    conventions = [
        {
            "name": "Unpartitioned library",
            "omega": 176.0,
            "sigma_omega": 3.4,
            "z_star": 7.29,
            "sigma_z": 3.8,
            "eps_inf": 6.51,
            "sigma_eps": 6.1,
        },
        {
            "name": "Tetragonal, isotropic avg",
            "omega": 172.0,
            "sigma_omega": 3.5,
            "z_star": 6.85,
            "sigma_z": 2.9,
            "eps_inf": 6.31,
            "sigma_eps": 4.0,
        },
        {
            "name": "Tetragonal, zz only",
            "omega": 172.0,
            "sigma_omega": 3.5,
            "z_star": 6.20,
            "sigma_z": 3.2,
            "eps_inf": 5.96,
            "sigma_eps": 3.0,
        },
        {
            "name": "Single calc, zz",
            "omega": 172.0,
            "sigma_omega": 3.0,
            "z_star": 6.20,
            "sigma_z": 1.0,
            "eps_inf": 5.96,
            "sigma_eps": 1.5,
        },
        {
            "name": "Single calc, iso",
            "omega": 172.0,
            "sigma_omega": 3.0,
            "z_star": 6.85,
            "sigma_z": 1.0,
            "eps_inf": 6.32,
            "sigma_eps": 1.5,
        },
    ]

    print("=" * 78)
    print("Phase partition analysis: effect on derived r33")
    print("=" * 78)
    print(
        f"Reference values: r_ref={R_REF_PM_PER_V} pm/V, "
        f"omega_ref={W_REF_CM} cm^-1, Z_ref={Z_REF_E} e, eps_ref={EPS_REF}"
    )
    print(f"Model-form uncertainty: {SIGMA_MODEL_PCT}%")
    print()
    print(
        f"{'Convention':<30s} {'Z*':>7s} {'eps':>7s} {'omega':>7s} "
        f"{'r33':>8s} {'sigma':>8s} {'abs':>8s}"
    )
    print("-" * 78)

    for row in conventions:
        r33 = soft_mode_r33(row["omega"], row["z_star"], row["eps_inf"])
        sigma_pct = propagated_uncertainty_pct(
            row["sigma_omega"], row["sigma_z"], row["sigma_eps"]
        )
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
    print("  1. The unpartitioned library inflates r33 because cubic Z* enters.")
    print("  2. Phase-filtered isotropic inputs give 108 pm/V, matching the calibrated bulk scale.")
    print("  3. Single-calculation values match the library when tensor convention is fixed.")
    print("  4. The 94 vs 108 pm/V spread quantifies tensor-averaging sensitivity.")


if __name__ == "__main__":
    main()
