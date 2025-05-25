import torch
import yaml
from pathlib import Path
import shutil
import os
import sys

# Çalışma dizinini al
WORKSPACE_DIR = os.path.abspath(os.path.dirname(__file__))

# YOLOv5'u klonla
if not os.path.exists('yolov5'):
    os.system('git clone https://github.com/ultralytics/yolov5.git')
    os.system('pip install -r yolov5/requirements.txt')

# YOLOv5'u Python path'ine ekle
sys.path.append(os.path.join(WORKSPACE_DIR, 'yolov5'))

# Veri setlerini birleştir
def merge_datasets():
    # Hedef klasörleri oluştur
    merged_dir = os.path.join(WORKSPACE_DIR, 'merged_dataset')
    os.makedirs(os.path.join(merged_dir, 'train/images'), exist_ok=True)
    os.makedirs(os.path.join(merged_dir, 'train/labels'), exist_ok=True)
    os.makedirs(os.path.join(merged_dir, 'valid/images'), exist_ok=True)
    os.makedirs(os.path.join(merged_dir, 'valid/labels'), exist_ok=True)
    
    # Kamyon veri setini kopyala
    for split in ['train', 'valid']:
        src_img = os.path.join(WORKSPACE_DIR, f'Yolo Truck.v1i.yolov5pytorch/{split}/images')
        src_lbl = os.path.join(WORKSPACE_DIR, f'Yolo Truck.v1i.yolov5pytorch/{split}/labels')
        dst_img = os.path.join(merged_dir, f'{split}/images')
        dst_lbl = os.path.join(merged_dir, f'{split}/labels')
        
        if os.path.exists(src_img):
            for file in os.listdir(src_img):
                shutil.copy2(os.path.join(src_img, file), os.path.join(dst_img, file))
        if os.path.exists(src_lbl):
            for file in os.listdir(src_lbl):
                shutil.copy2(os.path.join(src_lbl, file), os.path.join(dst_lbl, file))
    
    # Araba veri setini kopyala
    for split in ['train', 'valid']:
        src_img = os.path.join(WORKSPACE_DIR, f'DeteksiMobil.v1i.yolov5pytorch/{split}/images')
        src_lbl = os.path.join(WORKSPACE_DIR, f'DeteksiMobil.v1i.yolov5pytorch/{split}/labels')
        dst_img = os.path.join(merged_dir, f'{split}/images')
        dst_lbl = os.path.join(merged_dir, f'{split}/labels')
        
        if os.path.exists(src_img):
            for file in os.listdir(src_img):
                shutil.copy2(os.path.join(src_img, file), os.path.join(dst_img, file))
        if os.path.exists(src_lbl):
            for file in os.listdir(src_lbl):
                shutil.copy2(os.path.join(src_lbl, file), os.path.join(dst_lbl, file))

# data.yaml dosyasını oluştur
def create_data_yaml():
    data = {
        'train': os.path.join(WORKSPACE_DIR, 'merged_dataset/train/images'),
        'val': os.path.join(WORKSPACE_DIR, 'merged_dataset/valid/images'),
        'nc': 2,  # sınıf sayısı
        'names': ['truck', 'car']  # sınıf isimleri
    }
    
    yaml_path = os.path.join(WORKSPACE_DIR, 'merged_dataset/data.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f)

# Veri setlerini birleştir
merge_datasets()
create_data_yaml()

# Bellek optimizasyonları için ortam değişkenlerini ayarla
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# Eğitim komutunu oluştur ve çalıştır
train_command = f"""
python yolov5/train.py \
    --img 416 \
    --batch 4 \
    --epochs 100 \
    --data {os.path.join(WORKSPACE_DIR, 'merged_dataset/data.yaml')} \
    --weights yolov5s.pt \
    --device 0 \
    --workers 2 \
    --cache \
    --exist-ok \
    --project runs/train \
    --name exp
"""

print("Veri seti yolları:")
print(f"Train: {os.path.join(WORKSPACE_DIR, 'merged_dataset/train/images')}")
print(f"Valid: {os.path.join(WORKSPACE_DIR, 'merged_dataset/valid/images')}")

os.system(train_command) 