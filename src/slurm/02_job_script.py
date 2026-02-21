#!/usr/bin/env python3
"""
ANTPD Processing Script (positional args, no argparse)

Usage:
  python antpd_process.py [file_index] [optional_rootdir]
  python antpd_process.py sub-XXXX [optional_rootdir]
"""

from __future__ import annotations

import glob
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import ants
import antspyt1w
import antspymm


# -----------------------------
# Config / constants
# -----------------------------

DEFAULT_FILEINDEX = 9
DEFAULT_THREAD_COUNT = 24

DEFAULT_BASEDIR_CANDIDATES = [
    "/mnt/cluster/data/ANTPD/",
    "/workspace/ANTPD_antspymm/data/ANTPD/",
    "./data/ANTPD/",
]

TEMPLATE_DIR = Path.home() / ".antspymm"
TEMPLATE_IMAGE = TEMPLATE_DIR / "PPMI_template0.nii.gz"
TEMPLATE_MASK = TEMPLATE_DIR / "PPMI_template0_brainmask.nii.gz"


@dataclass(frozen=True)
class RunPaths:
    base_directory: Path
    bids_root: Path
    outdir: Path
    csvoutdir: Path


# -----------------------------
# Utility helpers
# -----------------------------

def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def info(msg: str) -> None:
    print(msg, flush=True)


def set_thread_env(num_threads: int) -> None:
    os.environ.setdefault("TF_NUM_INTEROP_THREADS", str(num_threads))
    os.environ.setdefault("TF_NUM_INTRAOP_THREADS", str(num_threads))
    os.environ.setdefault("ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS", str(num_threads))


def parse_args(argv: List[str]) -> Tuple[Optional[int], Optional[str], Optional[Path]]:
    fileindex: Optional[int] = None
    subject_id: Optional[str] = None
    rootdir: Optional[Path] = None

    if len(argv) > 1:
        arg1 = argv[1]

        if arg1.startswith("sub-"):
            subject_id = arg1
        else:
            try:
                fileindex = int(arg1)
            except ValueError:
                die("First argument must be an integer file index or subject ID (sub-XXXX).", 2)

    if len(argv) > 2:
        rootdir = Path(argv[2]).expanduser().resolve()

    if len(argv) > 3:
        die("Too many arguments. Usage: script.py [index|sub-XXXX] [rootdir]", 2)

    return fileindex, subject_id, rootdir


def resolve_paths(user_rootdir: Optional[Path]) -> RunPaths:
    if user_rootdir is not None:
        if (user_rootdir / "bids").exists():
            base = user_rootdir
            bids_root = user_rootdir / "bids"
        elif user_rootdir.name == "bids" and user_rootdir.exists():
            bids_root = user_rootdir
            base = user_rootdir.parent
        else:
            cur = user_rootdir
            found = None
            for _ in range(5):
                if (cur / "bids").exists():
                    found = cur
                    break
                if cur.parent == cur:
                    break
                cur = cur.parent
            if found is None:
                die(f"Provided rootdir does not contain a 'bids' directory: {user_rootdir}")
            base = found
            bids_root = found / "bids"
    else:
        base = None
        bids_root = None
        for candidate in DEFAULT_BASEDIR_CANDIDATES:
            cbase = Path(candidate).expanduser().resolve()
            cbids = cbase / "bids"
            if cbids.exists():
                base = cbase
                bids_root = cbids
                break
        if base is None or bids_root is None:
            die("No valid default rootdir found. Please pass as second argument.")

    outdir = base / "antpd_antspymm"
    csvoutdir = base / "studycsvs"
    outdir.mkdir(parents=True, exist_ok=True)
    csvoutdir.mkdir(parents=True, exist_ok=True)

    return RunPaths(base, bids_root, outdir, csvoutdir)


def ensure_template() -> ants.ANTsImage:
    if not TEMPLATE_IMAGE.exists() or not TEMPLATE_MASK.exists():
        info("Template or mask not found. Downloading default templates...")
        antspyt1w.get_data(force_download=True)
        antspymm.get_data(force_download=True)

    if not TEMPLATE_IMAGE.exists():
        die(f"Template still missing after download: {TEMPLATE_IMAGE}")
    if not TEMPLATE_MASK.exists():
        die(f"Brain mask still missing after download: {TEMPLATE_MASK}")

    template = ants.image_read(str(TEMPLATE_IMAGE))
    brain_mask = ants.image_read(str(TEMPLATE_MASK))

    if template.shape != brain_mask.shape:
        die("Template/mask shape mismatch.")

    template = template * brain_mask
    template = ants.crop_image(template, ants.iMath(brain_mask, "MD", 12))

    return template


def list_t1_files(bids_root: Path) -> List[Path]:
    pattern = str(bids_root / "*" / "*" / "anat" / "*T1w.nii.gz")
    return sorted(Path(p).resolve() for p in glob.glob(pattern))


def parse_subject_session_from_t1(t1_path: Path) -> Tuple[str, str]:
    parts = t1_path.name.split("_")
    if len(parts) < 2:
        die(f"Unexpected T1 filename: {t1_path.name}")
    return parts[0], parts[1]


def pick_first_sorted(matches: List[Path]) -> List[str]:
    if not matches:
        return []
    return [str(sorted(matches)[0])]


def find_optional_modalities(bids_root: Path, subject_id: str, subdate: str) -> Tuple[List[str], List[str]]:
    dwi_dir = bids_root / subject_id / subdate / "dwi"
    dwi_matches = sorted(dwi_dir.glob("*dwi.nii.gz")) if dwi_dir.exists() else []
    dtfn = pick_first_sorted(dwi_matches)

    func_dir = bids_root / subject_id / subdate / "func"
    func_matches = sorted(func_dir.glob("*rest_bold.nii.gz")) if func_dir.exists() else []
    rsfn = pick_first_sorted(func_matches)

    return dtfn, rsfn


def run_pipeline(paths: RunPaths, fileindex: Optional[int], subject_id: Optional[str], template: ants.ANTsImage) -> None:
    t1_files = list_t1_files(paths.bids_root)
    if not t1_files:
        die(f"No T1w files found under: {paths.bids_root}")

    if subject_id:
        subject_matches = [p for p in t1_files if p.name.startswith(subject_id)]
        if not subject_matches:
            die(f"No T1w files found for subject: {subject_id}")
        t1fn = sorted(subject_matches)[0]
        info(f"Selected first T1 for subject {subject_id}: {t1fn}")
    else:
        if fileindex is None:
            fileindex = DEFAULT_FILEINDEX
        if fileindex < 0 or fileindex >= len(t1_files):
            die(f"File index out of range: {fileindex}")
        t1fn = t1_files[fileindex]
        info(f"Selected T1 file [{fileindex}]: {t1fn}")

    subject_id, subdate = parse_subject_session_from_t1(t1fn)

    dtfn, rsfn = find_optional_modalities(paths.bids_root, subject_id, subdate)

    studycsv = antspymm.generate_mm_dataframe(
        projectID="ANTPD",
        subjectID=subject_id,
        date=subdate,
        imageUniqueID="000",
        modality="T1w",
        source_image_directory=str(paths.bids_root),
        output_image_directory=str(paths.outdir),
        t1_filename=str(t1fn),
        dti_filenames=dtfn,
        rsf_filenames=rsfn,
    )

    csv_filename = paths.csvoutdir / f"{subject_id}_{subdate}.csv"
    studycsv.to_csv(str(csv_filename), index=False)
    info(f"Wrote study CSV: {csv_filename}")

    studycsv_clean = studycsv.dropna(axis=1)

    antspymm.mm_csv(
        studycsv_clean,
        dti_motion_correct="SyN",
        dti_denoise=True,
        normalization_template=template,
        normalization_template_output="ppmi",
        normalization_template_transform_type="antsRegistrationSyNQuickRepro[s]",
        normalization_template_spacing=[1, 1, 1],
        mysep="_",
    )

    info("Multimodal processing complete.")


def main(argv: List[str]) -> None:
    fileindex, subject_id, user_rootdir = parse_args(argv)

    num_threads = int(os.environ.get("ANTPD_NUM_THREADS", str(DEFAULT_THREAD_COUNT)))
    set_thread_env(num_threads)

    paths = resolve_paths(user_rootdir)
    info(f"Using base_directory: {paths.base_directory}")
    info(f"Using bids_root: {paths.bids_root}")

    template = ensure_template()

    run_pipeline(paths, fileindex, subject_id, template)


if __name__ == "__main__":
    main(sys.argv)
