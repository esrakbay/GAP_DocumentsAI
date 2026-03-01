import os
import torch
import torchvision
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader, random_split
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

# ==== Ayarlar ====
data_dir = 'dataset_augmented_512'
image_size = 512
batch_size = 8
num_epochs = 20
learning_rate = 0.0002

# ==== Transformlar ====
train_transform = transforms.Compose([
    transforms.Resize((image_size, image_size)),
    transforms.RandomRotation(5),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.RandomPerspective(distortion_scale=0.1, p=0.5),
    transforms.ToTensor()
])

val_transform = transforms.Compose([
    transforms.Resize((image_size, image_size)),
    transforms.ToTensor()
])

# ==== Dataset yükleme (önce tümü) ====
full_dataset = ImageFolder(root=data_dir)
class_names = full_dataset.classes
num_classes = len(class_names)

# ==== Split ====
val_size = int(0.2 * len(full_dataset))
train_size = len(full_dataset) - val_size
train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

# Split sonrası transformları set et
train_dataset.dataset.transform = train_transform
val_dataset.dataset.transform = val_transform

# ==== DataLoader ====
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size)

# ==== Model tanımı ====
from torchvision.models import mobilenet_v2
model = mobilenet_v2(weights=None)  # SSL problemi varsa weights=None
model.classifier[1] = nn.Linear(model.last_channel, num_classes)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# ==== Loss + Optimizasyon ====
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# ==== Eğitim Döngüsü ====
train_acc, val_acc = [], []

for epoch in range(num_epochs):
    model.train()
    correct, total = 0, 0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    train_accuracy = 100 * correct / total
    train_acc.append(train_accuracy)

    # ==== Doğrulama ====
    model.eval()
    val_correct, val_total = 0, 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    val_accuracy = 100 * val_correct / val_total
    val_acc.append(val_accuracy)

    print(f"Epoch {epoch+1}/{num_epochs} - Train Acc: {train_accuracy:.2f}% | Val Acc: {val_accuracy:.2f}%")

# ==== Accuracy Grafiği(Eğitim ve doğrulama sonuçları görselleştirme) ====
plt.plot(train_acc, label='Train Acc')
plt.plot(val_acc, label='Val Acc')
plt.legend()
plt.title('Accuracy over Epochs')
plt.show()

# ==== Modeli kaydet ====
torch.save(model.state_dict(), "model_mobilenetv2.pt")