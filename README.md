# Araç ve Plaka Tespit Sistemi

Bu proje, kamera ile araç ve plaka tespiti yapıp Arduino ile kapı kontrolü sağlayan bir Flask web uygulamasıdır. Sistem, sadece veritabanında kayıtlı plakalara izin vermektedir.

📺 Demo Video: https://www.youtube.com/watch?v=0sVUL57W0PM

## 🚀 Özellikler

- 🚗 Araç tespiti (Araba/Kamyon)
- 🔍 Plaka tanıma ve doğrulama
- 🚪 Arduino ile otomatik kapı kontrolü
- 📊 Gerçek zamanlı web arayüzü
- 👥 Admin paneli ile plaka yönetimi
- 📝 Giriş kayıtları ve loglama
- 📸 Görsel ve video yükleme desteği
- ⏯️ Video kontrolü (oynat/durdur/ileri/geri)
- 🔄 Otomatik Arduino bağlantı yönetimi
- 🔔 Araç tespitinde ses uyarısı
- 🔒 Güvenli admin oturum yönetimi

## 🛠️ Teknik Altyapı

- **Web Framework:** Flask
- **Nesne Tespiti:** YOLOv5
- **Plaka Tanıma:** Tesseract OCR
- **Veritabanı:** MySQL
- **Gerçek Zamanlı İletişim:** Socket.IO
- **Donanım Kontrolü:** Arduino (CH340/USB Serial)
- **Görüntü İşleme:** OpenCV

## 📋 Gereksinimler

- Python 3.8+
- MySQL (Port: 3309)
- Tesseract OCR
- Arduino (CH340 veya USB Serial)
- Web kamerası
- PyTorch (CPU versiyonu)

## 🔧 Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. MySQL veritabanını oluşturun:
```bash
mysql -u root -p < veritabani.sql
```

3. Tesseract OCR'ı yükleyin:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt install tesseract-ocr`

4. YOLOv5 modellerini ana dizine kopyalayın:
- Araç modeli: `vehicle_model.pt`
- Plaka modeli: `plate_model.pt`

## 🚀 Çalıştırma

```bash
python app.py
```

Uygulama varsayılan olarak http://localhost:5000 adresinde çalışacaktır.

## 📱 Kullanım

### Ana Sayfa
- Canlı kamera görüntüsü
- Görsel/video yükleme
- Gerçek zamanlı tespit sonuçları
- Video kontrolü (oynat/durdur/ileri/geri)

### Admin Paneli (/admin)
- Plaka ekleme/düzenleme/silme
- Giriş kayıtlarını görüntüleme
- Plaka erişim kontrolü
- Oturum yönetimi

## 🔒 Güvenlik Özellikleri

- Admin oturum yönetimi ve şifreleme
- Güvenli dosya yükleme kontrolleri
- Plaka doğrulama sistemi
- Oturum bazlı yetkilendirme
- Maksimum dosya boyutu sınırlaması

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakınız.

## 🤝 Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/yeniOzellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik: X'`)
4. Branch'inizi push edin (`git push origin feature/yeniOzellik`)
5. Bir Pull Request oluşturun 
