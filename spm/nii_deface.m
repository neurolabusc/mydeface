function names = nii_deface(job, overwrite)
% extends nii_deface to remove excess neck and face details
% Face strip images
% FORMAT names = spm_deface(job)
% job.images   - cell array of NIfTI file names
%
% names        - cell array of de-faced images
%
% This is a little routine for attempting to strip the face from images,
% so individuals are more difficult to identify from surface renderings.
%__________________________________________________________________________

% John Ashburner
% Copyright (C) 2013-2022 Wellcome Centre for Human Neuroimaging


if ~nargin
    [P, sts] = spm_select(Inf,'image','Select images to strip the face from');
    if ~sts, return; end
elseif isstruct(job)
    P = job.images;
else
    P = job;
end
if ~exist('overwrite','var') 
    overwrite = false;
end
P = cellstr(P);
names = cell(size(P));
tpm = spm_load_priors8(spm_vol(fullfile(spm('Dir'),'tpm','TPM.nii')));
for i=1:numel(P)
    names{i} = deface(P{i},tpm, overwrite);
end

function fname = deface(P,tpm, overwrite)
M       = spm_maff8(P,4,20,tpm,[],'mni');
Nii     = nifti(P);
d       = [size(Nii.dat) 1];
[i,j,k] = ndgrid(1:d(1),1:d(2),1:d(3));
nul     = [0 -1.1 0.98 115];
nul1    = nul*M*Nii.mat;
msk     = nul1(1)*i + nul1(2)*j + nul1(3)*k + nul1(4) < 0;
% add a second plane to remove excess neck
nul     = [0 0 1 90];
nul1    = nul*M*Nii.mat;
msk2     = nul1(1)*i + nul1(2)*j + nul1(3)*k + nul1(4) < 0;
msk = max(msk, msk2);
% add a third plane to remove left ear
nul     = [1 0 0 80];
nul1    = nul*M*Nii.mat;
msk2     = nul1(1)*i + nul1(2)*j + nul1(3)*k + nul1(4) < 0;
msk = max(msk, msk2);
% add a fourth plane to remove right ear
nul     = [-1 0 0 80];
nul1    = nul*M*Nii.mat;
msk2     = nul1(1)*i + nul1(2)*j + nul1(3)*k + nul1(4) < 0;
msk = max(msk, msk2);
% create two masks to remove jaw
% msk inferior removes signal near feet
nul     = [0 -0.2 1 50];
nul1    = nul*M*Nii.mat;
mskInferior     = nul1(1)*i + nul1(2)*j + nul1(3)*k + nul1(4) < 0;
% msk anterior removes signal near the nose
nul     = [0 -1.0 0.8 75];
nul1    = nul*M*Nii.mat;
mskAnterior     = nul1(1)*i + nul1(2)*j + nul1(3)*k + nul1(4) < 0;
% remove intersection of foot and nose removal
msk2 = min(mskInferior, mskAnterior);
% combine compound jaw mask to others:
msk = max(msk, msk2);
% next masks are optional, but remove phantom face signal and excess neck
% add a plane to rem
% ove posterior
nul     = [0 1 0 120];
nul1    = nul*M*Nii.mat;
msk2     = nul1(1)*i + nul1(2)*j + nul1(3)*k + nul1(4) < 0;
msk = max(msk, msk2);
% add a plane to remove superior to head
nul     = [0 0 1 105];
nul1    = nul*M*Nii.mat;
msk2     = nul1(1)*i + nul1(2)*j + nul1(3)*k + nul1(4) < 0;
msk = max(msk, msk2);

% Ensure anything that may reveal identity is not included in the face-stripped
% version. This includes hidden fields, extensions etc that may contain strings.

%fname   = Nii.dat.fname;
%fname   = spm_file(Nii.dat.fname,'prefix','anon_');
fname   = spm_file(Nii.dat.fname,'prefix','anon_');

%Noo    = Nii; % This was unsafe because Nii may contain hidden strings
Noo             = nifti;
Noo.dat         = file_array(fname, Nii.dat.dim, Nii.dat.dtype, 0, ...
                             Nii.dat.scl_slope, Nii.dat.scl_inter);
Noo.dat.fname   = fname;
Noo.diminfo     = Nii.diminfo;
Noo.mat         = Nii.mat;
Noo.mat_intent  = Nii.mat_intent;
Noo.mat0        = Nii.mat0;
Noo.mat0_intent = Nii.mat0_intent;
Noo.descrip     = 'SPM anonymised'; % Unsafe to copy string
Noo.intent      = Nii.intent;
Noo.cal         = Nii.cal;

create(Noo);
for k=1:size(Noo.dat,6)
    for j=1:size(Noo.dat,5)
        for i=1:size(Noo.dat,4)
            F       = Nii.dat(:,:,:,i,j,k);
            F(msk)  = NaN;
            Noo.dat(:,:,:) = F;
        end
    end
end
if overwrite
    [p,n,x] = fileparts(Nii.dat.fname);
    movefile(Nii.dat.fname,fullfile(p,['_',n,x]));
    movefile(fullfile(p,['anon_',n,x]), Nii.dat.fname);
end

