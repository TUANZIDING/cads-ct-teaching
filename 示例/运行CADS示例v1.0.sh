#!/usr/bin/env bash
# 运行 CADS 示例 v1.0 —— 命令摘自官方 README（https://github.com/murong-xu/CADS），仅作教学示范。
# 使用权重即表示接受其许可：research = CC BY-NC-SA 4.0；open = CC BY-SA 4.0；reference = CADS 定制许可。
set -euo pipefail
git clone https://github.com/murong-xu/CADS.git
conda create -n CADS_env python=3.11 -y
conda activate CADS_env
# 按自己的系统/CUDA 安装 PyTorch（torch>=2.1.2），以下为官方示例（Linux + CUDA 12.4）
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
cd CADS && pip install -e .
# 单个任务（例：554 躯干肌肉与骨盆），无 GPU 时加 --cpu
python cads/scripts/predict_images.py -in /path/to/ct_images -out /path/to/output -task 554 -license research
# 全部 9 个任务
python cads/scripts/predict_images.py -in /path/to/ct_images -out /path/to/output -task all -license research
