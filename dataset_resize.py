from PIL import Image
import os
import random
import numpy as np
from torchvision import transforms

# 📁 Klasör ayarları
input_root = "dataset"
output_root = "dataset_augmented_512"
target_size = (512, 512)
min_samples = 10

# 🎨 Augment transformları
augmentation_transforms = transforms.Compose([
    transforms.RandomRotation(degrees=5),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.ToPILImage()
])

os.makedirs(output_root, exist_ok=True)

# 🔁 Her sınıf klasörünü işle
for folder in os.listdir(input_root):
    input_folder = os.path.join(input_root, folder)
    if not os.path.isdir(input_folder) or not folder.startswith("type_"):
        continue

    class_num = folder.split("_")[1]
    output_folder = os.path.join(output_root, folder)
    os.makedirs(output_folder, exist_ok=True)

    # 📸 Orijinal görselleri al
    original_images = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    image_count = 0

    # 🔁 Orijinalleri resize edip kaydet
    for img_file in original_images:
        img_path = os.path.join(input_folder, img_file)
        img = Image.open(img_path).convert("RGB").resize(target_size)
        new_name = f"itu_type{class_num}_{str(image_count+1).zfill(2)}.jpg"
        img.save(os.path.join(output_folder, new_name))
        image_count += 1

    # 🔁 Eksik varsa augment ederek tamamla
    while image_count < min_samples:
        img_file = random.choice(original_images)
        img_path = os.path.join(input_folder, img_file)
        img = Image.open(img_path).convert("RGB").resize(target_size)
        aug_img = augmentation_transforms(img)
        new_name = f"itu_type{class_num}_{str(image_count+1).zfill(2)}.jpg"
        aug_img.save(os.path.join(output_folder, new_name))
        image_count += 1

print("✅ Tüm sınıflar resize + augment + yeniden isimlendirme ile hazırlandı.")
