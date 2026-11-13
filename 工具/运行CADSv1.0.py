"""运行CADS v1.0 / Run CADS-model-research task 554 on a cropped TotalSegmentator v2.0.1 CT (s0423) on CPU.
Deviation from the official pipeline (documented): patch size reduced 192^3 -> 128^3 to fit ~2.5 GB free RAM;
no test-time mirroring (trainer is NoMirroring anyway); CADS TPTBox post-processing not applied.
Usage: CADS_W=<model dir> CADS_CT=<ct.nii.gz> python3 工具/运行CADSv1.0.py <z0> <z1> [patch]
Code: PolyForm Noncommercial 1.0.0. Weights are NOT included (CC BY-NC-SA 4.0, download from github.com/murong-xu/CADS/releases)."""
import os, sys, time, json
import numpy as np, nibabel as nib, torch
torch.set_num_threads(2)
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
# 权重目录与输入 CT 用环境变量指定 / set paths via environment variables
W=os.environ.get('CADS_W','weights/research/Dataset554_Totalseg254/nnUNetTrainerNoMirroring__nnUNetResEncUNetLPlans__3d_fullres')
src=os.environ.get('CADS_CT','s0423/ct.nii.gz')
z0,z1=int(sys.argv[1]),int(sys.argv[2]); patch=int(sys.argv[3]) if len(sys.argv)>3 else 128
X0,X1,Y0,Y1=24,252,36,196  # crop to the trunk (bbox of TS reference trunk muscles/pelvis + margin)
img=nib.load(src); a=img.get_fdata(dtype=np.float32)[X0:X1,Y0:Y1,z0:z1]
p=nnUNetPredictor(tile_step_size=0.5,use_gaussian=True,use_mirroring=False,perform_everything_on_device=False,device=torch.device('cpu'),verbose=False,allow_tqdm=True)
p.initialize_from_trained_model_folder(W,use_folds=('all',),checkpoint_name='checkpoint_final.pth')
p.configuration_manager.configuration['patch_size']=[patch]*3
print('patch',p.configuration_manager.patch_size,flush=True)
# nnU-Net expects (c, z, y, x) with spacing ordered accordingly; SimpleITK-like ordering = reverse of nibabel axes
arr=np.transpose(a,(2,1,0))[None]
props={'spacing':[1.5,1.5,1.5]}
t=time.time()
seg=p.predict_single_npy_array(arr,props,None,None,False)
print('seconds',time.time()-t,flush=True)
seg=np.transpose(seg,(2,1,0)).astype(np.uint8)
full=np.zeros(img.shape,np.uint8); full[X0:X1,Y0:Y1,z0:z1]=seg
nib.save(nib.Nifti1Image(full,img.affine),f'cads554-s0423-z{z0}-{z1}.nii.gz')
json.dump({'crop_xyz':[X0,X1,Y0,Y1,z0,z1],'z0':z0,'z1':z1,'patch':patch,'seconds':time.time()-t,'labels':p.dataset_json['labels']},open(f'cads554-s0423-z{z0}-{z1}.json','w'),ensure_ascii=False,indent=1)
print('saved')
