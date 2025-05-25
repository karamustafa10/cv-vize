-- Veritabanını oluştur
CREATE DATABASE IF NOT EXISTS arac_takip;

-- Veritabanını kullan
USE arac_takip;

-- Admin tablosu
CREATE TABLE IF NOT EXISTS admin_kullanicilar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_adi VARCHAR(50) NOT NULL UNIQUE,
    sifre VARCHAR(255) NOT NULL,
    ad_soyad VARCHAR(100),
    son_giris TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Örnek admin kullanıcısı (şifre: admin123)
INSERT INTO admin_kullanicilar (kullanici_adi, sifre, ad_soyad) VALUES
('admin', 'admin123', 'Sistem Yöneticisi');

-- Kayıtlı plakalar tablosu
CREATE TABLE IF NOT EXISTS kayitli_plakalar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plaka VARCHAR(20) NOT NULL UNIQUE,
    arac_sahibi VARCHAR(100),
    arac_turu ENUM('Kamyon', 'Araba') NOT NULL,
    kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    son_giris_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    aktif BOOLEAN DEFAULT TRUE
);

-- Giriş kayıtları tablosu
CREATE TABLE IF NOT EXISTS giris_kayitlari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plaka_id INT,
    giris_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    basarili BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (plaka_id) REFERENCES kayitli_plakalar(id)
);

-- Örnek kayıtlı plakalar
INSERT INTO kayitli_plakalar (plaka, arac_sahibi, arac_turu) VALUES
('34ABC123', 'Ahmet Yılmaz', 'Kamyon'),
('06XYZ789', 'Mehmet Demir', 'Kamyon'),
('35DEF456', 'Ayşe Kaya', 'Kamyon'); 