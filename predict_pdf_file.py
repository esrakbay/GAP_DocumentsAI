import torch
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2
from PIL import Image
from pdf2image import convert_from_path
import os

# === Ayarlar ===
image_size = 512
model_path = "model_mobilenetv2.pt"
data_dir = "dataset_augmented_512"
pdf_folder = "data"  # Taranacak klasör

# === Sınıf İsimleri Otomatik ===
class_names = sorted(os.listdir(data_dir))

# === Modeli Yükleme ===
model = mobilenet_v2(weights=None)
model.classifier[1] = torch.nn.Linear(model.last_channel, len(class_names))
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
model.eval()

# === Görsel Dönüştürme (Val transform) ===
transform = transforms.Compose([
    #Görüntüyü yeniden boyutlandır
    transforms.Resize((image_size, image_size)),
    #Görüntüyü PyTorch veri yapısına çevirir
    transforms.ToTensor()
])

def predict_pdf_type(pdf_path, poppler_path):
    try:
        #görüntünün ilk sayfasını pdf'e çevirme
        images = convert_from_path(pdf_path, first_page=1, last_page=1, poppler_path=poppler_path)
        image = images[0]
        #görüntüyü modelin beklediği formata dönüştürme
        image = transform(image).unsqueeze(0)  # batch dimension

        #image tensörünün en yüksek olasılıklı sınıf tahminlemesi ve olasılık yüzdesi
        with torch.no_grad():
            output = model(image)
            probs = torch.nn.functional.softmax(output, dim=1)
            confidence, predicted = torch.max(probs, 1)

        predicted_class = class_names[predicted.item()]
        confidence_percent = confidence.item() * 100
        return predicted_class, confidence_percent

    except Exception as e:
        print(f"Hata oluştu: {pdf_path} → {e}")
        return None, None

# === Klasördeki tüm PDF'leri tara ===
if __name__ == "__main__":
    print(f"Klasör taranıyor: {pdf_folder}\n")
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            file_path = os.path.join(pdf_folder, filename)
            predicted_class, confidence = predict_pdf_type(file_path)
            if predicted_class:
                print(f"{filename} → Tahmin: {predicted_class} (%{confidence:.2f})")
            else:
                print(f"{filename} → Tahmin yapılamadı")