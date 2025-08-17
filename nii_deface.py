#!/usr/bin/env python3
"""
nii_deface.py  —  mask+crop a 3D NIfTI with an MNI-space face mask

Usage:
  python nii_deface.py /path/to/img.nii.gz

Requirements:
  - antspyx, nibabel, numpy
  - The files "MNI152_T1_2mm.nii.gz" and "mniMask.nii.gz" must be in the same
    folder as this script (used as moving image and mask in MNI space).
"""

import sys
import os
from pathlib import Path
import numpy as np
import nibabel as nib

try:
    import ants
except ImportError:
    print("ERROR: antspyx is required (pip install antspyx).", file=sys.stderr)
    sys.exit(1)


def _ensure_3d_nifti(p: Path) -> nib.Nifti1Image:
    if not p.exists():
        print(f"ERROR: Input file not found: {p}", file=sys.stderr)
        sys.exit(1)
    img = nib.load(str(p))
    if img.ndim != 3:
        print(f"ERROR: Input must be 3D (got shape {img.shape}).", file=sys.stderr)
        sys.exit(1)
    return img


def _find_resources(script_dir: Path):
    tmpl = script_dir / "MNI152_T1_2mm.nii.gz"
    msk  = script_dir / "mniMask.nii.gz"
    missing = [str(x) for x in (tmpl, msk) if not x.exists()]
    if missing:
        print("ERROR: Required files not found next to script:\n  " + "\n  ".join(missing), file=sys.stderr)
        sys.exit(1)
    return tmpl, msk


def _mask_and_crop_preserve_affine(data: np.ndarray, affine: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Zero-voxel crop with ≤1-voxel padding and affine translation preserved.

    Adapted from user's crop script (preserve origin shift when cropping). :contentReference[oaicite:0]{index=0}
    """
    # ensure 3D array
    if data.ndim != 3:
        raise ValueError(f"Expected 3D data, got shape {data.shape}")

    X, Y, Z = data.shape
    mask = (data != 0)

    if not np.any(mask):
        # Entire volume zero; nothing to crop — keep as-is.
        return data, affine

    coords = np.array(np.nonzero(mask))
    xmin, ymin, zmin = coords.min(axis=1)
    xmax, ymax, zmax = coords.max(axis=1) + 1  # exclusive

    pad = 1
    xmin_p = max(xmin - pad, 0)
    xmax_p = min(xmax + pad, X)
    ymin_p = max(ymin - pad, 0)
    ymax_p = min(ymax + pad, Y)
    zmin_p = max(zmin - pad, 0)
    zmax_p = min(zmax + pad, Z)

    cropped = data[xmin_p:xmax_p, ymin_p:ymax_p, zmin_p:zmax_p]

    # shift affine by voxel offset
    offset_voxel = np.array([xmin_p, ymin_p, zmin_p, 1])
    new_affine = affine.copy()
    new_affine[:3, 3] = (affine @ offset_voxel)[:3]

    return cropped, new_affine


def main():
    if len(sys.argv) != 2:
        print("Usage: python nii_deface.py /path/to/img.nii[.gz]", file=sys.stderr)
        sys.exit(1)

    in_path = Path(sys.argv[1]).resolve()
    script_dir = Path(__file__).resolve().parent

    # Check inputs/resources
    src_img = _ensure_3d_nifti(in_path)
    tmpl_path, mask_path = _find_resources(script_dir)

    # Read with ANTs for registration
    fixed = ants.image_read(str(in_path))               # subject (fixed)
    moving = ants.image_read(str(tmpl_path))            # MNI template (moving)
    moving_mask = ants.image_read(str(mask_path))       # MNI-space mask

    # Rigid+Affine+SyN registration is robust but can be slow; if you prefer quicker,
    # swap to type_of_transform="Affine" or "Rigid".
    print("Registering MNI template to input (this may take a bit)...")
    reg = ants.registration(
        fixed=fixed,
        moving=moving,
        type_of_transform="SyN",   # change to "Affine" for speed if desired
        verbose=False
    )

    # Apply transform to mask (moving->fixed). Use nearest-neighbor to keep binary mask.
    print("Resampling mask to input space...")
    mask_in_fixed = ants.apply_transforms(
        fixed=fixed,
        moving=moving_mask,
        transformlist=reg["fwdtransforms"],
        interpolator="nearestNeighbor"  # preserves labels
    )

    # Create a hard binary mask (in case the warp produced non-binary values)
    mask_np = (mask_in_fixed.numpy() > 0.5).astype(np.uint8)

    # Load original with nibabel to preserve dtype & affine on save
    orig_dtype = src_img.get_data_dtype()
    orig_affine = src_img.affine
    subj_np = src_img.get_fdata(dtype=np.float32)  # float for safe masking math

    # Mask out voxels outside brain/face mask
    # Ensure shape alignment (should already match)
    if subj_np.shape != mask_np.shape:
        print(f"ERROR: Masked shape {mask_np.shape} does not match input {subj_np.shape}.", file=sys.stderr)
        sys.exit(1)

    subj_np[mask_np == 0] = 0

    # Crop zeros (≤1-voxel pad) while preserving affine translation
    cropped_np, new_affine = _mask_and_crop_preserve_affine(subj_np, orig_affine)

    # Save back, overwriting the original file, preserving original dtype
    print(f"Overwriting input with masked, cropped image: {in_path}")
    out_img = nib.Nifti1Image(cropped_np.astype(orig_dtype), new_affine)
    out_img.set_data_dtype(orig_dtype)
    nib.save(out_img, str(in_path))

    print("Done.")
    sys.exit(0)


if __name__ == "__main__":
    main()
