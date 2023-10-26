#!/usr/bin/env python

# Convert each directory in the root directory to a tgz file

from pathlib import Path
import shutil
import sys
import os
import tarfile
import os.path
import ctypes
import csv
from datetime import datetime
import glob
import shutil

if __name__ == "__main__":
    """Remove facial features from MRI scans
    Parameters
    ----------
    niftiInput : str
                 NIfTI image to deface
    """
    if len(sys.argv) < 2:
        sys.exit("No input filename provided")
    niftiInput = sys.argv[1]
    if (not os.path.isfile(niftiInput)) and (os.path.isfile(os.path.join(os.getcwd(), niftiInput))):
        niftiInput = os.path.join(os.getcwd(), niftiInput)
    if not os.path.isfile(niftiInput):
        sys.exit("Unable to find "+niftiInput)
    #rename input file with "_"
    niftiDiscard = os.path.join(os.path.dirname(niftiInput),"_"+ os.path.basename(niftiInput))
    if os.path.isfile(niftiDiscard):
        sys.exit("Discard already exists "+niftiDiscard)

    scalpmask = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "mniMask.nii.gz")
    if not os.path.isfile(scalpmask):
        sys.exit("Unable to find "+scalpmask)
    fsldir = os.getenv('FSLDIR')
    template =  os.path.join(fsldir, "data", "standard", "MNI152_T1_2mm.nii.gz")
    if not os.path.isfile(template):
        sys.exit("Unable to find "+template)
    if not shutil.which("flirt"):
        sys.exit("Unable to find flirt")
    if not shutil.which("fslmaths"):
        sys.exit("Unable to find fslmaths")
    #create temporary folder
    tmp = os.path.join(os.getcwd(), 'temp')
    Path(tmp).mkdir(parents=True, exist_ok=True)
    mat = os.path.join(tmp, 'm.mat')
    #step 1: coregister template to image to deface
    cmd = "flirt -in " + template + " -ref " + niftiInput + " -omat " + mat + " -bins 256 -cost normmi -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12"
    os.system(cmd)
    #step 2: warp scalp mask to native space
    mas = os.path.join(tmp, 'mask.nii.gz')
    cmd = "flirt -in " + scalpmask +  " -ref " + niftiInput + " -out " + mas +" -applyxfm -init " + mat + " -interp nearestneighbour"
    os.system(cmd)
    os.rename(niftiInput, niftiDiscard);
    #step 3: mask image
    cmd = "fslmaths " + niftiDiscard + " -mas " + mas +" " + niftiInput + " -odt input"
    os.system(cmd)
    #remove temporary directory
    #os.system(cmd)
    #shutil.rmtree(tmp)
    sys.exit(0)
