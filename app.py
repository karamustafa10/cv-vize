from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
import cv2
import torch
import pytesseract
import numpy as np
import serial
import time
import pygame
from threading import Thread
import serial.tools.list_ports
from flask_socketio import SocketIO
import os
from werkzeug.utils import secure_filename
import mysql.connector
from datetime import datetime
from functools import wraps

# Flask uygulamasının oluşturulması ve temel ayarların yapılandırılması
flask_app = Flask(__name__)
flask_app.config['SECRET_KEY'] = 'gizli_anahtar123'
flask_app.config['UPLOAD_FOLDER'] = 'uploads'  # Yüklenen dosyaların kaydedileceği klasör
flask_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Maksimum dosya boyutu: 16MB
ALLOWED_FILE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov'}  # İzin verilen dosya uzantıları
socket_io = SocketIO(flask_app, cors_allowed_origins="*", async_mode='threading')

# Veritabanı bağlantı ayarları
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'arac_takip',
    'port': 3309
}

# Admin yetkisi gerektiren sayfalar için decorator fonksiyonu
def admin_required(route_function):
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return route_function(*args, **kwargs)
    return decorated_function

# Veritabanı bağlantısını oluşturan fonksiyon
def get_database_connection():
    try:
        return mysql.connector.connect(**DATABASE_CONFIG)
    except Exception as error:
        print(f"Veritabanı bağlantı hatası: {str(error)}")
        return None

# Admin girişi kontrolü yapan fonksiyon
def verify_admin_credentials(username, password):
    db_connection = get_database_connection()
    if not db_connection:
        return False
    
    try:
        db_cursor = db_connection.cursor(dictionary=True)
        db_cursor.execute("""
            SELECT * FROM admin_kullanicilar 
            WHERE kullanici_adi = %s AND sifre = %s
        """, (username, password))
        
        admin_user = db_cursor.fetchone()
        if admin_user:
            db_cursor.execute("""
                UPDATE admin_kullanicilar 
                SET son_giris = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (admin_user['id'],))
            db_connection.commit()
            return True
        return False
    finally:
        db_cursor.close()
        db_connection.close()

# Admin giriş sayfası route'u
@flask_app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        input_username = request.form.get('username')
        input_password = request.form.get('password')
        
        if verify_admin_credentials(input_username, input_password):
            session['admin_logged_in'] = True
            session['username'] = input_username
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Geçersiz kullanıcı adı veya şifre')
    
    return render_template('admin_login.html')

# Admin çıkış işlemi route'u
@flask_app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('username', None)
    return redirect(url_for('index'))

# Admin paneli route'u
@flask_app.route('/admin')
@admin_required
def admin_panel():
    db_connection = get_database_connection()
    if not db_connection:
        return "Veritabanı bağlantı hatası", 500
    
    try:
        db_cursor = db_connection.cursor(dictionary=True)
        db_cursor.execute("SELECT * FROM kayitli_plakalar ORDER BY kayit_tarihi DESC")
        registered_plates = db_cursor.fetchall()
        return render_template('admin_panel.html', plakalar=registered_plates)
    finally:
        db_cursor.close()
        db_connection.close()

@flask_app.route('/admin/plaka/ekle', methods=['POST'])
@admin_required
def plaka_ekle():
    plaka = request.form.get('plaka')
    arac_sahibi = request.form.get('arac_sahibi')
    arac_turu = request.form.get('arac_turu')
    
    conn = get_database_connection()
    if not conn:
        return jsonify({'error': 'Veritabanı bağlantı hatası'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO kayitli_plakalar (plaka, arac_sahibi, arac_turu)
            VALUES (%s, %s, %s)
        """, (plaka, arac_sahibi, arac_turu))
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@flask_app.route('/admin/plaka/sil/<int:id>')
@admin_required
def plaka_sil(id):
    conn = get_database_connection()
    if not conn:
        return jsonify({'error': 'Veritabanı bağlantı hatası'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kayitli_plakalar WHERE id = %s", (id,))
        conn.commit()
        return redirect(url_for('admin_panel'))
    finally:
        cursor.close()
        conn.close()

@flask_app.route('/admin/plaka/guncelle', methods=['POST'])
@admin_required
def plaka_guncelle():
    id = request.form.get('id')
    plaka = request.form.get('plaka')
    arac_sahibi = request.form.get('arac_sahibi')
    arac_turu = request.form.get('arac_turu')
    aktif = request.form.get('aktif') == 'true'
    
    conn = get_database_connection()
    if not conn:
        return jsonify({'error': 'Veritabanı bağlantı hatası'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE kayitli_plakalar 
            SET plaka = %s, arac_sahibi = %s, arac_turu = %s, aktif = %s
            WHERE id = %s
        """, (plaka, arac_sahibi, arac_turu, aktif, id))
        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Plaka erişim kontrolü yapan fonksiyon
def check_plate_access(plate_number):
    db_connection = get_database_connection()
    if not db_connection:
        return False, None
    
    try:
        db_cursor = db_connection.cursor(dictionary=True)
        # Tüm aktif plakaları getir
        db_cursor.execute("""
            SELECT id, plaka, arac_sahibi, aktif 
            FROM kayitli_plakalar 
            WHERE aktif = TRUE
        """)
        
        active_plates = db_cursor.fetchall()
        
        # Okunan plaka metnini temizle ve büyük harfe çevir
        cleaned_detected_plate = ''.join(c for c in plate_number if c.isalnum()).upper()
        
        for plate_record in active_plates:
            # Veritabanındaki plakayı da temizle ve büyük harfe çevir
            cleaned_db_plate = ''.join(c for c in plate_record['plaka'] if c.isalnum()).upper()
            
            # Eğer veritabanındaki plaka, okunan plaka metninin içinde birebir geçiyorsa
            if cleaned_db_plate in cleaned_detected_plate:
                # Giriş kaydı oluştur
                db_cursor.execute("""
                    INSERT INTO giris_kayitlari (plaka_id, basarili, okunan_plaka) 
                    VALUES (%s, TRUE, %s)
                """, (plate_record['id'], plate_number))
                
                # Son giriş tarihini güncelle
                db_cursor.execute("""
                    UPDATE kayitli_plakalar 
                    SET son_giris_tarihi = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (plate_record['id'],))
                
                db_connection.commit()
                return True, plate_record
        
        # Eşleşme bulunamadıysa
        return False, None
        
    except Exception as error:
        print(f"Plaka kontrol hatası: {str(error)}")
        return False, None
    finally:
        db_cursor.close()
        db_connection.close()

# Yükleme klasörünü oluştur
if not os.path.exists(flask_app.config['UPLOAD_FOLDER']):
    os.makedirs(flask_app.config['UPLOAD_FOLDER'])

# Global değişkenler
video_camera = None
arduino_controller = None
vehicle_detection_model = None
plate_detection_model = None
current_frame_source = 'camera'
current_image = None
is_video_paused = False
current_video_frame = None
is_detection_active = True  # Tespit işlemlerini kontrol eden yeni değişken

# Arduino portunu bulan fonksiyon
def find_arduino_port():
    available_ports = list(serial.tools.list_ports.comports())
    for port in available_ports:
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB Serial' in port.description:
            return port.device
    return 'COM3'

# Arduino bağlantısını kuran fonksiyon
def connect_arduino():
    global arduino_controller
    try:
        if arduino_controller is not None:
            arduino_controller.close()
        
        port = find_arduino_port()
        print(f"Arduino port: {port}")
        arduino_controller = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)
        print("Arduino bağlantısı başarılı!")
        socket_io.emit('arduino_status', {'status': 'connected', 'port': port})
        return True
    except Exception as error:
        print(f"Arduino bağlantı hatası: {str(error)}")
        arduino_controller = None
        socket_io.emit('arduino_status', {'status': 'disconnected', 'error': str(error)})
        return False

# Sistem başlatma fonksiyonu
def initialize_system():
    global vehicle_detection_model, plate_detection_model, video_camera
    
    connect_arduino()
    pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    
    try:
        vehicle_detection_model = torch.hub.load('ultralytics/yolov5', 'custom', path='vehicle_model.pt')
        vehicle_detection_model.names = ['car', 'truck']
        vehicle_detection_model.conf = 0.5

        plate_detection_model = torch.hub.load('ultralytics/yolov5', 'custom', path='plate_model.pt')
        plate_detection_model.conf = 0.4
    except Exception as error:
        print(f"Model yükleme hatası: {str(error)}")
        
    try:
        video_camera = cv2.VideoCapture(0)
    except Exception as error:
        print(f"Kamera başlatma hatası: {str(error)}")

# Socket.IO bağlantı olayı
@socket_io.on('connect')
def handle_connect():
    print('Client connected')
    socket_io.emit('arduino_status', {'status': 'connected' if arduino_controller else 'disconnected'})

# Görüntü işleme fonksiyonu
def process_frame(frame):
    if frame is None:
        return frame

    if not is_detection_active:  # Tespit aktif değilse sadece frame'i döndür
        return frame

    try:
        detection_results = vehicle_detection_model(frame)
        for detection in detection_results.xyxy[0]:
            x1, y1, x2, y2, confidence, class_id = detection.cpu().numpy()
            if confidence > vehicle_detection_model.conf:
                if int(class_id) == 1:  # Kamyon
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    truck_image = frame[y1:y2, x1:x2].copy()
                    if truck_image.size > 0:
                        plate_results = plate_detection_model(truck_image)
                        plate_detected = False
                        for plate_detection in plate_results.xyxy[0]:
                            px1, py1, px2, py2, plate_conf, plate_cls = plate_detection.cpu().numpy()
                            if plate_conf > plate_detection_model.conf:
                                px1, py1, px2, py2 = map(int, [px1, py1, px2, py2])
                                plate_image = truck_image[py1:py2, px1:px2]
                                if plate_image.size > 0:
                                    try:
                                        gray_image = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
                                        _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                                        plate_text = pytesseract.image_to_string(binary_image, config='--psm 7').strip()
                                        
                                        # Plaka kontrolü
                                        has_access, plate_info = check_plate_access(plate_text)
                                        
                                        cv2.rectangle(truck_image, (px1, py1), (px2, py2), 
                                                    (0, 255, 0) if has_access else (0, 0, 255), 2)
                                        cv2.putText(truck_image, plate_text, (px1, py1 - 10),
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                                  (0, 255, 0) if has_access else (0, 0, 255), 2)
                                        
                                        if plate_text and arduino_controller and has_access:
                                            try:
                                                arduino_controller.write(b'OPEN\n')
                                                print(f"Arduino'ya OPEN komutu gönderildi. Plaka: {plate_text}")
                                                socket_io.emit('plate_detected', {
                                                    'plate': plate_text,
                                                    'type': 'truck',
                                                    'confidence': float(confidence),
                                                    'access': True,
                                                    'owner': plate_info['arac_sahibi'] if plate_info else None
                                                })
                                            except:
                                                print("Arduino bağlantısı koptu, yeniden bağlanmaya çalışılıyor...")
                                                connect_arduino()
                                        else:
                                            socket_io.emit('plate_detected', {
                                                'plate': plate_text,
                                                'type': 'truck',
                                                'confidence': float(confidence),
                                                'access': False
                                            })
                                        plate_detected = True
                                    except Exception as error:
                                        print(f"Plaka işleme hatası: {str(error)}")
                                        continue
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, "Kamyon", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        frame[y1:y2, x1:x2] = truck_image
                else:  # Araba
                    try:
                        pygame.mixer.init()
                        pygame.mixer.music.load('araba-sesi.mp3')
                        pygame.mixer.music.play()
                    except Exception as error:
                        print(f"Ses çalma hatası: {str(error)}")
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
                    cv2.putText(frame, "Araba", (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    socket_io.emit('vehicle_detected', {
                        'type': 'car',
                        'confidence': float(confidence)
                    })
    except Exception as error:
        print(f"Frame işleme hatası: {str(error)}")

    return frame

# Dosya uzantısı kontrolü
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS

# Ana sayfa route'u
@flask_app.route('/')
def index():
    return render_template('index.html')

# Video akışı route'u
@flask_app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Dosya yükleme route'u
@flask_app.route('/upload', methods=['POST'])
def upload_file():
    global current_frame_source, current_image, video_camera, is_video_paused, current_video_frame
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya seçilmedi'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_ext = filename.rsplit('.', 1)[1].lower()
        if file_ext in ['mp4', 'avi', 'mov']:  # Video dosyası
            current_frame_source = 'video'
            is_video_paused = False
            current_video_frame = None
            if video_camera is not None:
                video_camera.release()
            video_camera = cv2.VideoCapture(filepath)
            return jsonify({'success': True, 'message': 'Video başarıyla yüklendi', 'type': 'video'})
        else:  # Resim dosyası
            current_frame_source = 'image'
            current_image = cv2.imread(filepath)
            if current_image is None:
                return jsonify({'error': 'Görüntü yüklenemedi'}), 400
            return jsonify({'success': True, 'message': 'Resim başarıyla yüklendi', 'type': 'image'})
    
    return jsonify({'error': 'İzin verilmeyen dosya türü'}), 400

# Video kontrol route'u
@flask_app.route('/video_control', methods=['POST'])
def video_control():
    global is_video_paused, video_camera, current_video_frame
    
    if not video_camera or current_frame_source != 'video':
        return jsonify({'error': 'Video yüklü değil'}), 400
    
    data = request.get_json()
    action = data.get('action')
    
    if action == 'pause':
        is_video_paused = True
        ret, current_video_frame = video_camera.read()  # Mevcut kareyi sakla
        return jsonify({'success': True})
    
    elif action == 'play':
        is_video_paused = False
        current_video_frame = None
        return jsonify({'success': True})
    
    elif action == 'prev':
        current_pos = video_camera.get(cv2.CAP_PROP_POS_FRAMES)
        new_pos = max(0, current_pos - 300)  # 10 saniye geri (30fps varsayarak)
        video_camera.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
        return jsonify({'success': True})
    
    elif action == 'next':
        current_pos = video_camera.get(cv2.CAP_PROP_POS_FRAMES)
        total_frames = video_camera.get(cv2.CAP_PROP_FRAME_COUNT)
        new_pos = min(total_frames - 1, current_pos + 300)  # 10 saniye ileri
        video_camera.set(cv2.CAP_PROP_POS_FRAMES, new_pos)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Geçersiz işlem'}), 400

# Video karelerini oluşturan fonksiyon
def generate_frames():
    global video_camera, current_frame_source, current_image, is_video_paused, current_video_frame
    
    while True:
        if current_frame_source == 'camera' and video_camera is not None:
            success, frame = video_camera.read()
            if not success:
                break
        elif current_frame_source == 'video' and video_camera is not None:
            if is_video_paused and current_video_frame is not None:
                frame = current_video_frame.copy()
            else:
                success, frame = video_camera.read()
                if not success:
                    video_camera.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Videoyu başa sar
                    continue
        elif current_frame_source == 'image' and current_image is not None:
            frame = current_image.copy()
        else:
            continue

        processed_frame = process_frame(frame)
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Kameraya geçiş route'u
@flask_app.route('/switch_to_camera')
def switch_to_camera():
    global current_frame_source
    current_frame_source = 'camera'
    return jsonify({'success': True})

# Tespit işlemlerini kontrol eden route
@flask_app.route('/toggle_detection', methods=['POST'])
def toggle_detection():
    global is_detection_active
    is_detection_active = not is_detection_active
    return jsonify({'success': True, 'detection_active': is_detection_active})

# Sayfa yenilendiğinde kamera/tespit alanını sıfırlayan route
@flask_app.route('/reset_view')
def reset_view():
    global current_frame_source, current_image, video_camera, is_video_paused, current_video_frame, is_detection_active
    
    try:
        # Mevcut video kamerasını kapat
        if video_camera is not None:
            video_camera.release()
        
        # Tüm değişkenleri başlangıç değerlerine sıfırla
        current_frame_source = 'camera'
        current_image = None
        is_video_paused = False
        current_video_frame = None
        is_detection_active = True
        
        # Yeni kamera bağlantısı kur
        video_camera = cv2.VideoCapture(0)
        if not video_camera.isOpened():
            return jsonify({'success': False, 'error': 'Kamera başlatılamadı'}), 500
            
        # Socket.IO üzerinden durumu bildir
        socket_io.emit('view_reset', {
            'success': True,
            'message': 'Görüntü başarıyla sıfırlandı',
            'detection_active': True,
            'frame_source': 'camera'
        })
        
        return jsonify({
            'success': True, 
            'message': 'Görüntü başarıyla sıfırlandı',
            'detection_active': True,
            'frame_source': 'camera'
        })
    except Exception as e:
        print(f"Görüntü sıfırlama hatası: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Uygulama başlatma
if __name__ == '__main__':
    initialize_system()
    socket_io.run(flask_app, debug=False, host='0.0.0.0', port=5000)