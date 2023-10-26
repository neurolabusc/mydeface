## About

Sharing data allows reproducibility and reuse. However, medical images can expose facial features that allow identification. This is a defacing utility for MRI images inspired by [pydeface](https://github.com/poldracklab/pydeface). Both tools use FSL's [FLIRT](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT) to mask regions outside the skull. mydeface differs in a minor ways:

  - The `normmi` normalized mutual information cost function is a bit more robust.
  - While pydeface strips regions around the nose and eyes, mydeface expands this and strips all signal outside a narrowly defined scalp. This influences recognition of ear shape. Further, as excess neck and scalp fat are removed this can aid subsequent analyses. Further, ghosting images of facial features are removed from the air. However, since all these external features are set to zero, this can impact some segmentation tools that use the variability in the air signal to estimate noise variance (e.g. Gaussian mixture models for earlier versions of SPM). Likewise, this may impact the performance of homogeneity biased intensity correction. Tools should use implicit zero masking.

## Requirements

This script requires FSL and its default datasets are installed.

## Usage

Simply provide the name of the image to be masked. The masked image replaces the original, with the original renamed with an underscore prefix (e.g. `T1.nii.gz` -> `_T1.nii.gz`). The intention is that the original is removed after visual inspection to ensure accurate defacing.

```
python mydeface.py FLAIR.nii.gz
```

## Limitations and Solutions

FSL's FLIRT uses the center of brightness as its starting estimate. Therefore, it can be disrupted by too much neck signal. The bonus included Matlab/SPM script extends SPM's `spm_deface` script to remove both facial features and signal from the shoulders and thoracic spine. For the rare images where mydeface fails, you can run nii_deface followed by mydeface for a thorough and robust anonymization. The disadvantage is that this requires SPM and Matlab to be installed.