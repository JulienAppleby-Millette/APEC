**QE BTO TEST ARRAY: PAPER 1**
Filename structure: ${func}_${ecut}_${kmesh}_scf.out
includes:
   PBE:
      ecut: 30, 40, 50, 60, 70, 80, 90
         kmesh: 4x4x4, 6x6x6, 8x8x8, 10x10x10
   PBEsol:
      ecut: 40, 60, 80
         kmesh: 4x4x4, 6x6x6, 8x8x8
37 total output files

***Generic input files included below:***
**SMEAR:**
&CONTROL
    calculation = 'scf'
    prefix = 'NAME'
    outdir = './tmp'
    pseudo_dir = '/path/to/pseuds'
    tprnfor = .true.
    tstress = .true.
    etot_conv_thr = 1.0d-4  ! Ry
    forc_conv_thr = 1.0d-3  ! Ry/au
    nstep = 500
    restart_mode = 'from_scratch'
/
&SYSTEM
    ibrav = 6
    celldm(1) = 15.0876 ! in bohr, = 7.984 A
    celldm(3) = 1.01102  ! c/a ratio
    nat = 40
    ntyp = 3
    ecutwfc = ECUT
    ecutrho = 8 * ECUT
    occupations = 'smearing'
    smearing = 'mv'
    degauss = 0.005
    input_dft = 'FUNC'
    nbnd = 200
/
&ELECTRONS
  conv_thr = 1.0d-8
  mixing_beta = 0.3
  mixing_mode = 'plain'
  mixing_ndim = 16
  electron_maxstep = 200
  diagonalization = 'david'
/
ATOMIC_SPECIES
    Ba  137.327  Ba.pbe-spn-kjpaw_psl.1.0.0.UPF
    Ti  47.867   Ti.pbe-spn-kjpaw_psl.1.0.0.UPF
    O   15.999   O.pbe-n-kjpaw_psl.1.0.0.UPF

ATOMIC_POSITIONS crystal
{optimized atomic positions}

K_POINTS automatic
    KMESH KMESH KMESH 0 0 0


**FIXED:**
&CONTROL
    calculation = 'scf'
    prefix = 'NAME'
    outdir = './tmp'
    pseudo_dir = '/path/to/pseuds'
    tprnfor = .true.
    tstress = .true.
    etot_conv_thr = 1.0d-4  ! Ry
    forc_conv_thr = 1.0d-3  ! Ry/au
    nstep = 500
    restart_mode = 'from_scratch'
/
&SYSTEM
    ibrav = 6
    celldm(1) = 15.0876 ! in bohr, = 7.984 A
    celldm(3) = 1.01102  ! c/a ratio
    nat = 40
    ntyp = 3
    ecutwfc = ECUT
    ecutrho = 8 * ECUT
    occupations = 'fixed'
    input_dft = 'FUNC'
    nbnd = 200
/
&ELECTRONS
  conv_thr = 1.0d-10
  mixing_beta = 0.3
  mixing_mode = 'plain'
  mixing_ndim = 16
  electron_maxstep = 200
  diagonalization = 'david'
  startingwfc = 'file'
  startingpot = 'file'
/
ATOMIC_SPECIES
    Ba  137.327  Ba.pbe-spn-kjpaw_psl.1.0.0.UPF
    Ti  47.867   Ti.pbe-spn-kjpaw_psl.1.0.0.UPF
    O   15.999   O.pbe-n-kjpaw_psl.1.0.0.UPF

ATOMIC_POSITIONS crystal
{optimized atomic positions}

K_POINTS automatic
    KMESH KMESH KMESH 0 0 0