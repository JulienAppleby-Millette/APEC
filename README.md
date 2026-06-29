# APECs BaTiO3 Support Repository

This repository supports the manuscript:

**A Posteriori Error Certificates (APECs): Certifying Uncertainty Through the Soft-Mode Bottleneck in BaTiO3**

Authors: Julien Appleby-Millette, Kyla Younger, Thomas Baker, and Irina Paci  
Department of Chemistry, University of Victoria

## Scope

The repository contains the curated data, figure-generation and validation scripts, calibration outputs, and manuscript source needed to reproduce the BaTiO3 APECs case study. It is intentionally limited to the posterior-certificate analysis and is self-contained.

The case study attaches decomposed uncertainty estimates to DFT-computed BaTiO3 properties, assigns Green/Amber/Red quality tiers, and propagates uncertainty through the soft-mode expression for the electro-optic coefficient r33. It also includes a typed band-gap certificate case study and Kyla Younger's independent SCF convergence study for a 40-atom BaTiO3 supercell.

## Key Results

- 12 posterior certificates extracted from a production PBE/PAW DFPT calculation using Quantum ESPRESSO 7.5.
- 1 typed band-gap certificate case study showing why Kohn-Sham, proxy, and optical gaps must be kept non-exchangeable unless calibrated reduction maps are supplied.
- Phase-aware partitioning resolves cubic/tetragonal conflation in prior Born effective charge data.
- Library-fused isotropic r33 = 108 +/- 25 pm/V for tetragonal bulk BaTiO3; agreement with the bulk reference scale is treated as a calibrated internal consistency check, not an independent validation of the absolute electro-optic response.
- Library fusion reduces relative uncertainty from 28% for the single-calculation certificate to approximately 24% for the fused estimate, bounded by a model-form-dominated floor of about 22%.
- Leave-one-out calibration gives RMS z = 1.05 across 15 exchangeable library residuals.
- The SCF convergence campaign confirms cutoff-dominated total-energy convergence for the 40-atom BaTiO3 supercell.

## Repository Structure

```text
data/
  posterior_certificates.json        # DFPT certificates plus typed band-gap record
  bto_literature_library.json        # Phase- and observable-typed literature library

scripts/
  phase_partition_analysis.py        # Phase/tensor partition table for r33
  extraction_case_study.py           # Self-contained literature-extraction audit summary
  gen_fig1_convergence.py            # Figure 1: soft-mode uncertainty propagation
  gen_fig2_composite.py              # Figure 2: canonical asset validation + optional preview
  calibration_check.py               # Figure 3: leave-one-out calibration
  analyze_kyla_scf_convergence.py    # Figure 4: SCF convergence campaign
  band_gap_certificate_case_study.py # Typed band-gap artifacts and supplemental figure

figures/
  fig1_omega_convergence.pdf/png
  fig2_composite.pdf/png
  fig3_calibration_check.pdf/png
  fig4_scf_convergence.pdf/png
  figS_band_gap_certificate.pdf/png

outputs/
  calibration/                       # Leave-one-out calibration JSON/CSV
  band_gap_certificate/              # Typed band-gap JSON/CSV artifacts
  extraction_case_study_summary.json # Support-repository extraction summary

convergence_study/
  kyla_younger_scf_20260525/         # Raw and processed SCF convergence study

manuscript/
  paper1_main.tex                    # Current canonical manuscript source
  paper1_supplemental.tex            # Current canonical Supplemental Material
  references_merged.bib              # Bibliography used by main text and SI
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python scripts/phase_partition_analysis.py
python scripts/extraction_case_study.py
python scripts/gen_fig1_convergence.py
python scripts/gen_fig2_composite.py
python scripts/calibration_check.py
python scripts/analyze_kyla_scf_convergence.py
python scripts/band_gap_certificate_case_study.py
```

The scripts are self-contained and do not require any external development package.

## Generated Artifacts

`figures/fig2_composite.pdf` and `figures/fig2_composite.png` are the canonical
Overleaf Figure 2 assets. `scripts/gen_fig2_composite.py` validates these assets
by default and does not overwrite them. To create a non-authoritative diagnostic
preview from the JSON data, run `python scripts/gen_fig2_composite.py
--regenerate-preview`.

`scripts/calibration_check.py` regenerates `outputs/calibration/certificate_library_calibration.json`, `outputs/calibration/certificate_library_leave_one_out.csv`, and `figures/fig3_calibration_check.*`.

`scripts/analyze_kyla_scf_convergence.py` regenerates the convergence summaries under `convergence_study/kyla_younger_scf_20260525/processed/` and `figures/fig4_scf_convergence.*`.

`scripts/band_gap_certificate_case_study.py` regenerates the typed band-gap outputs under `outputs/band_gap_certificate/` and `figures/figS_band_gap_certificate.*`.

## Notes on Exchangeability

The library calibration script excludes the typed band-gap records from the leave-one-out exchangeability check. Band gaps are retained in the certificate audit trail, but semilocal Kohn-Sham gaps, proxy gaps, and optical gaps are not fused as physical optical-gap evidence unless an explicit calibrated reduction map is supplied.

The SCF convergence records are convergence-model diagnostics, not independent response-property certificates.

## License

Data, scripts, and generated figures are released under CC-BY 4.0. Manuscript text remains copyright the authors and is included for review and reproducibility.
