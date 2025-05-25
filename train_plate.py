import os
import sys

# YOLOv5 klasörü yoksa klonla
if not os.path.exists('yolov5'):
    os.system('git clone https://github.com/ultralytics/yolov5.git')
    os.system('pip install -r yolov5/requirements.txt')

# Eğitim komutunu oluştur
train_command = (
    'python yolov5/train.py '
    '--img 416 '
    '--batch 4 '
    '--epochs 100 '
    '--data "Turkish Number Plates.v1i.yolov5pytorch/data.yaml" '
    '--weights yolov5s.pt '
    '--device 0 '
    '--project runs/train_plate '
    '--name exp '
    '--exist-ok'
)

os.system(train_command) 