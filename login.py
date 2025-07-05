import sys
import cv2
import numpy as np
import pickle
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QFrame, QMessageBox, QProgressBar, QTabWidget,
                            QGridLayout, QFileDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon, QImage
from PyQt5.QtCore import QSettings

class FaceRecognitionThread(QThread):
    authentication_result = pyqtSignal(bool, str)
    frame_ready = pyqtSignal(np.ndarray)
    
    def __init__(self, mode="authenticate", username=None):
        super().__init__()
        self.mode = mode  # "authenticate", "register", "capture"
        self.username = username
        self.running = False
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.faces_data_file = "faces_data.pkl"
        self.model_file = "face_model.xml"
        self.capture_count = 0
        self.max_captures = 30
        self.model_loaded = False
        
        # Configuración mejorada del reconocedor
        self.face_recognizer.setThreshold(100.0)  # Aumentar el umbral para ser menos restrictivo
        
        # Cargar modelo si existe y estamos en modo authenticate
        if mode == "authenticate":
            self.load_model()
        
    def run(self):
        self.running = True
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            self.authentication_result.emit(False, "No se pudo acceder a la cámara")
            return
            
        captured_faces = []
        auth_attempts = 0
        max_auth_attempts = 10  # Múltiples intentos de autenticación
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Voltear horizontalmente para efecto espejo
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Mejorar la detección de rostros
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,  # Más sensible
                minNeighbors=4,   # Menos restrictivo
                minSize=(80, 80)  # Tamaño mínimo de cara
            )
            
            for (x, y, w, h) in faces:
                # Dibujar rectángulo alrededor de la cara
                color = (0, 255, 0) if self.mode == "authenticate" else (255, 0, 0)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                
                if self.mode == "register" and len(faces) == 1:
                    # Capturar cara para registro con preprocesamiento
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = self.preprocess_face(face_roi)
                    captured_faces.append(face_roi)
                    self.capture_count += 1
                    
                    # Mostrar progreso
                    cv2.putText(frame, f"Capturando: {self.capture_count}/{self.max_captures}", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    if self.capture_count >= self.max_captures:
                        self.save_face_data(captured_faces)
                        self.running = False
                        break
                        
                elif self.mode == "authenticate" and len(faces) == 1:
                    # Autenticar cara solo si el modelo está entrenado
                    if self.model_loaded and os.path.exists(self.model_file):
                        face_roi = gray[y:y+h, x:x+w]
                        face_roi = self.preprocess_face(face_roi)
                        
                        try:
                            # Realizar predicción
                            label, confidence = self.face_recognizer.predict(face_roi)
                            
                            # Debug info
                            print(f"Predicción - Label: {label}, Confianza: {confidence}")
                            
                            # Umbral de confianza ajustado (menor valor = mayor confianza)
                            # LBPH típicamente da valores entre 0-100, donde 0 es match perfecto
                            if confidence < 80:  # Umbral más permisivo
                                username = self.get_username_by_label(label)
                                if username != "Desconocido":
                                    cv2.putText(frame, f"Bienvenido {username} ({confidence:.1f})", 
                                              (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                                    auth_attempts += 1
                                    
                                    # Requiere múltiples detecciones consecutivas para mayor seguridad
                                    if auth_attempts >= 3:
                                        self.authentication_result.emit(True, username)
                                        self.running = False
                                        break
                                else:
                                    cv2.putText(frame, "Usuario no encontrado", (x, y-10), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
                            else:
                                cv2.putText(frame, f"No reconocido ({confidence:.1f})", (x, y-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                                auth_attempts = 0  # Reset counter
                        except Exception as e:
                            cv2.putText(frame, "Error reconocimiento", (x, y-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                            print(f"Error en predicción: {str(e)}")
                    else:
                        cv2.putText(frame, "Sin usuarios registrados", (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            else:
                # No se detectó cara, reset counter
                auth_attempts = 0
            
            # Agregar instrucciones en pantalla
            if self.mode == "authenticate":
                cv2.putText(frame, "Posicionate frente a la camara para autenticarte", 
                          (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            elif self.mode == "register":
                cv2.putText(frame, "Mantente frente a la camara para registro", 
                          (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                          
            self.frame_ready.emit(frame)
            self.msleep(30)  # Reducir delay para mejor respuesta
            
        cap.release()
    
    def preprocess_face(self, face):
        """Preprocesa la imagen de la cara para mejorar el reconocimiento"""
        # Redimensionar a tamaño estándar
        face = cv2.resize(face, (100, 100))
        
        # Aplicar ecualización de histograma para mejorar el contraste
        face = cv2.equalizeHist(face)
        
        # Aplicar filtro gaussiano para reducir ruido
        face = cv2.GaussianBlur(face, (5, 5), 0)
        
        return face
        
    def save_face_data(self, faces):
        try:
            # Cargar datos existentes
            if os.path.exists(self.faces_data_file):
                with open(self.faces_data_file, 'rb') as f:
                    data = pickle.load(f)
                    all_faces = data['faces']
                    all_labels = data['labels']
                    usernames = data['usernames']
            else:
                all_faces = []
                all_labels = []
                usernames = {}
            
            # Agregar nuevas caras
            new_label = len(usernames)
            usernames[new_label] = self.username
            
            for face in faces:
                all_faces.append(face)
                all_labels.append(new_label)
            
            # Guardar datos actualizados
            data = {
                'faces': all_faces,
                'labels': all_labels,
                'usernames': usernames
            }
            
            with open(self.faces_data_file, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"✅ Datos guardados: {len(faces)} caras para usuario {self.username}")
            
            # Entrenar modelo
            self.train_model(all_faces, all_labels)
            self.authentication_result.emit(True, f"Usuario {self.username} registrado exitosamente")
            
        except Exception as e:
            self.authentication_result.emit(False, f"Error al guardar datos: {str(e)}")
    
    def train_model(self, faces, labels):
        try:
            # Verificar que hay suficientes datos
            if len(faces) == 0 or len(labels) == 0:
                print("❌ No hay datos para entrenar")
                return
                
            # Convertir labels a numpy array
            labels_array = np.array(labels)
            
            print(f"🔄 Entrenando modelo con {len(faces)} caras...")
            
            # Entrenar el modelo
            self.face_recognizer.train(faces, labels_array)
            
            # Guardar el modelo
            self.face_recognizer.save(self.model_file)
            
            print("✅ Modelo entrenado y guardado exitosamente")
            
        except Exception as e:
            print(f"❌ Error entrenando modelo: {str(e)}")
    
    def get_username_by_label(self, label):
        try:
            if os.path.exists(self.faces_data_file):
                with open(self.faces_data_file, 'rb') as f:
                    data = pickle.load(f)
                    username = data['usernames'].get(label, "Desconocido")
                    print(f"Label {label} corresponde a usuario: {username}")
                    return username
        except Exception as e:
            print(f"Error obteniendo username: {str(e)}")
            return "Desconocido"
        return "Desconocido"
    
    def stop(self):
        self.running = False
        self.quit()
        self.wait()
    
    def load_model(self):
        """Carga el modelo de reconocimiento facial si existe"""
        try:
            if os.path.exists(self.model_file) and os.path.exists(self.faces_data_file):
                # Verificar que el archivo de datos tenga contenido
                with open(self.faces_data_file, 'rb') as f:
                    data = pickle.load(f)
                    faces = data.get('faces', [])
                    labels = data.get('labels', [])
                    usernames = data.get('usernames', {})
                    
                    if faces and labels:
                        # Cargar el modelo existente
                        self.face_recognizer.read(self.model_file)
                        self.model_loaded = True
                        print(f"✅ Modelo cargado con {len(usernames)} usuarios")
                        print(f"   Usuarios: {list(usernames.values())}")
                        return True
                    else:
                        print("⚠️ Archivo de datos vacío")
            else:
                print("⚠️ No hay modelo o datos guardados")
            
            self.model_loaded = False
            return False
            
        except Exception as e:
            print(f"❌ Error cargando modelo: {str(e)}")
            self.model_loaded = False
            return False

class LoginWindow(QMainWindow):
    # Agregar señal para manejar el cierre desde el exterior
    login_closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('FactoryIO', 'LoginSystem')
        self.dark_mode = self.settings.value('dark_mode', False, type=bool)
        
        self.setWindowTitle("Factory I/O - Sistema de Autenticación")
        self.setGeometry(200, 200, 900, 600)
        self.setFixedSize(1000, 700)
        
        self.face_thread = None
        self.camera_active = False
        self.external_launcher = None  # Para launcher externo
        
        self.init_ui()
        self.apply_theme()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Login
        login_tab = self.create_login_tab()
        self.tab_widget.addTab(login_tab, "🔐 Autenticación")
        
        # Tab 2: Registro
        register_tab = self.create_register_tab()
        self.tab_widget.addTab(register_tab, "👤 Registro")
        
        # Tab 3: Gestión
        management_tab = self.create_management_tab()
        self.tab_widget.addTab(management_tab, "⚙️ Gestión")
        
        main_layout.addWidget(self.tab_widget)


        
    def create_header(self):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        
        # Título
        title = QLabel("🏭 Factory I/O - Sistema de Autenticación")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #3498db; margin-bottom: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Toggle tema
        theme_label = QLabel("Modo Oscuro:")
        self.dark_mode_toggle = QPushButton("🌙" if not self.dark_mode else "☀️")
        self.dark_mode_toggle.setFixedSize(40, 30)
        self.dark_mode_toggle.clicked.connect(self.toggle_theme)
        
        header_layout.addWidget(theme_label)
        header_layout.addWidget(self.dark_mode_toggle)
        
        return header_widget
    
    def create_login_tab(self):
        login_widget = QWidget()
        layout = QHBoxLayout(login_widget)
        layout.setSpacing(20)
        
        # Panel izquierdo - Información
        info_panel = QFrame()
        info_panel.setFrameStyle(QFrame.Box)
        info_layout = QVBoxLayout(info_panel)
        
        info_title = QLabel("💡 Instrucciones")
        info_title.setFont(QFont("Arial", 10, QFont.Bold))
        info_layout.addWidget(info_title)
        
        instructions = QLabel("""
• Haz clic en "Iniciar Cámara" para activar el reconocimiento
• Posicionese frente a la cámara y espere
• Mantenga el rostro estable por unos segundos
• Si no está registrado, vaya a "Registro"
• Una vez autenticado, accederás al sistema
        """)
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Arial", 9))
        info_layout.addWidget(instructions)
        
        info_layout.addStretch()
        
        # Estado del sistema
        status_label = QLabel("📊 Estado del Sistema")
        status_label.setFont(QFont("Arial", 10, QFont.Bold))
        info_layout.addWidget(status_label)
        
        self.status_text = QLabel()
        self.update_system_status()
        info_layout.addWidget(self.status_text)
        
        # Botón de debug
        self.btn_debug = QPushButton("🔧 Ver Logs")
        self.btn_debug.setStyleSheet(self.get_button_style("#95a5a6", "#7f8c8d"))
        self.btn_debug.clicked.connect(self.show_debug_info)
        info_layout.addWidget(self.btn_debug)
        
        layout.addWidget(info_panel, 1)
        
        # Panel derecho - Cámara y controles
        camera_panel = QFrame()
        camera_panel.setFrameStyle(QFrame.Box)
        camera_layout = QVBoxLayout(camera_panel)
        
        # Área de cámara
        self.camera_label = QLabel("📷 Cámara Desactivada")
        self.camera_label.setMinimumHeight(300)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)
        camera_layout.addWidget(self.camera_label)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.btn_start_camera = QPushButton("📷 Iniciar Cámara")
        self.btn_start_camera.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        self.btn_start_camera.clicked.connect(self.start_authentication)
        
        self.btn_stop_camera = QPushButton("⏹️ Detener")
        self.btn_stop_camera.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
        self.btn_stop_camera.clicked.connect(self.stop_camera)
        self.btn_stop_camera.setEnabled(False)
        
        controls_layout.addWidget(self.btn_start_camera)
        controls_layout.addWidget(self.btn_stop_camera)
        camera_layout.addLayout(controls_layout)
        
        layout.addWidget(camera_panel, 2)
        
        return login_widget
    
    def create_register_tab(self):
        register_widget = QWidget()
        layout = QVBoxLayout(register_widget)
        layout.setSpacing(20)
        
        # Formulario de registro
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Box)
        form_layout = QVBoxLayout(form_frame)
        
        form_title = QLabel("👤 Registro de Nuevo Usuario")
        form_title.setFont(QFont("Arial", 16, QFont.Bold))
        form_title.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(form_title)
        
        # Campo nombre de usuario
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Nombre de Usuario:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingresa tu nombre de usuario")
        username_layout.addWidget(self.username_input)
        form_layout.addLayout(username_layout)
        
        # Área de cámara para registro
        self.register_camera_label = QLabel("📷 Cámara para Registro")
        self.register_camera_label.setMinimumHeight(250)
        self.register_camera_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.register_camera_label.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self.register_camera_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        form_layout.addWidget(self.progress_bar)
        
        # Botones de registro
        register_controls = QHBoxLayout()
        
        self.btn_start_register = QPushButton("🎯 Iniciar Registro")
        self.btn_start_register.setStyleSheet(self.get_button_style("#27ae60", "#229954"))
        self.btn_start_register.clicked.connect(self.start_registration)
        
        self.btn_cancel_register = QPushButton("❌ Cancelar")
        self.btn_cancel_register.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
        self.btn_cancel_register.clicked.connect(self.stop_camera)
        self.btn_cancel_register.setEnabled(False)
        
        register_controls.addWidget(self.btn_start_register)
        register_controls.addWidget(self.btn_cancel_register)
        form_layout.addLayout(register_controls)
        
        layout.addWidget(form_frame)
        
        return register_widget
    
    def create_management_tab(self):
        management_widget = QWidget()
        layout = QVBoxLayout(management_widget)
        
        # Título
        title = QLabel("⚙️ Gestión de Usuarios")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Lista de usuarios
        self.users_list = QListWidget()
        self.load_users_list()
        layout.addWidget(self.users_list)
        
        # Botones de gestión
        management_controls = QHBoxLayout()
        
        btn_refresh = QPushButton("🔄 Actualizar Lista")
        btn_refresh.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        btn_refresh.clicked.connect(self.load_users_list)
        
        btn_delete_user = QPushButton("🗑️ Eliminar Usuario")
        btn_delete_user.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
        btn_delete_user.clicked.connect(self.delete_user)
        
        btn_backup = QPushButton("💾 Crear Respaldo")
        btn_backup.setStyleSheet(self.get_button_style("#f39c12", "#e67e22"))
        btn_backup.clicked.connect(self.create_backup)
        
        btn_rebuild = QPushButton("🔨 Reconstruir Modelo")
        btn_rebuild.setStyleSheet(self.get_button_style("#9b59b6", "#8e44ad"))
        btn_rebuild.clicked.connect(self.rebuild_model)
        
        management_controls.addWidget(btn_refresh)
        management_controls.addWidget(btn_delete_user)
        management_controls.addWidget(btn_backup)
        management_controls.addWidget(btn_rebuild)
        
        layout.addLayout(management_controls)
        
        return management_widget
    
    def get_button_style(self, color, hover_color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: bold;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """
    
    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(self.get_dark_theme())
        else:
            self.setStyleSheet(self.get_light_theme())
    
    def get_light_theme(self):
        return """
            QMainWindow {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QWidget {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #7f8c8d;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 6px;
            }
        """
    
    def get_dark_theme(self):
        return """
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 15px;
            }
            QLineEdit {
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1e1e1e;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget {
                border: 1px solid #404040;
                border-radius: 6px;
                background-color: #2d2d2d;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 6px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 6px;
            }
        """
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.settings.setValue('dark_mode', self.dark_mode)
        self.dark_mode_toggle.setText("☀️" if self.dark_mode else "🌙")
        self.apply_theme()
    
    def start_authentication(self):
        # Verificar si hay usuarios registrados
        if not self.check_users_exist():
            QMessageBox.warning(self, "Sin Usuarios", 
                              "No hay usuarios registrados en el sistema.\n\n"
                              "Ve a la pestaña 'Registro' para registrar el primer usuario.")
            return
            
        self.start_camera_process("authenticate")
        
    def start_registration(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Error", "Por favor ingresa un nombre de usuario")
            return
        
        # Verificar si el usuario ya existe
        if self.user_exists(username):
            QMessageBox.warning(self, "Error", f"El usuario '{username}' ya existe")
            return
            
        self.start_camera_process("register", username)
        
    def start_camera_process(self, mode, username=None):
        if self.face_thread and self.face_thread.isRunning():
            self.face_thread.stop()
            
        self.face_thread = FaceRecognitionThread(mode, username)
        self.face_thread.authentication_result.connect(self.on_authentication_result)
        self.face_thread.frame_ready.connect(self.update_camera_display)
        self.face_thread.start()
        
        self.camera_active = True
        self.update_camera_controls()
        
        if mode == "register":
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
    def stop_camera(self):
        if self.face_thread:
            self.face_thread.stop()
            
        self.camera_active = False
        self.update_camera_controls()
        
        # Reset camera displays
        self.camera_label.setText("📷 Cámara Desactivada")
        self.register_camera_label.setText("📷 Cámara para Registro")
        self.progress_bar.setVisible(False)
        
    def update_camera_controls(self):
        # Controles de autenticación
        self.btn_start_camera.setEnabled(not self.camera_active)
        self.btn_stop_camera.setEnabled(self.camera_active)
        
        # Controles de registro
        self.btn_start_register.setEnabled(not self.camera_active)
        self.btn_cancel_register.setEnabled(self.camera_active)
        
    def update_camera_display(self, frame):
        try:
            # Convertir frame de BGR a RGB
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # Crear QImage desde array numpy
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Convertir QImage a QPixmap
            pixmap = QPixmap.fromImage(qt_image)
            
            # Escalar imagen según el modo
            if hasattr(self.face_thread, 'mode'):
                if self.face_thread.mode == "authenticate":
                    scaled_pixmap = pixmap.scaled(
                        self.camera_label.size(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.camera_label.setPixmap(scaled_pixmap)
                elif self.face_thread.mode == "register":
                    scaled_pixmap = pixmap.scaled(
                        self.register_camera_label.size(), 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.register_camera_label.setPixmap(scaled_pixmap)
                    
                    # Actualizar progress bar
                    if hasattr(self.face_thread, 'capture_count'):
                        progress = (self.face_thread.capture_count / self.face_thread.max_captures) * 100
                        self.progress_bar.setValue(int(progress))
                        
        except Exception as e:
            print(f"Error actualizando display de cámara: {str(e)}")
            # En caso de error, mostrar mensaje en el label
            if hasattr(self.face_thread, 'mode'):
                if self.face_thread.mode == "authenticate":
                    self.camera_label.setText("❌ Error en cámara")
                elif self.face_thread.mode == "register":
                    self.register_camera_label.setText("❌ Error en cámara")
    
    def on_authentication_result(self, success, message):
        self.stop_camera()
        
        if success:
            if "registrado" in message:
                QMessageBox.information(self, "Éxito", message)
                self.username_input.clear()
                self.load_users_list()
                self.update_system_status()  # Actualizar estado del sistema
            else:
                # Autenticación exitosa - lanzar aplicación principal
                QMessageBox.information(self, "Autenticación Exitosa", f"Bienvenido {message}")
                self.launch_main_application()
        else:
            QMessageBox.warning(self, "Error", message)

    def set_external_launcher(self, launcher_function):
        """Configura una función externa para lanzar la aplicación principal"""
        self.external_launcher = launcher_function
            
    def launch_main_application(self):
        try:
            # Cerrar ventana de login
            self.close()
            
            # Verificar si hay un launcher personalizado
            if self.external_launcher:
                # Usar el launcher externo
                self.external_launcher()
            else:
                # Comportamiento por defecto - lanzar main2 directamente
                try:
                    import main2
                    main_app = main2.FactoryIOController()
                    main_app.show()
                except ImportError:
                    # Si main2 no existe, mostrar mensaje
                    QMessageBox.information(None, "Sistema Principal", 
                                          "Aquí se abriría la aplicación principal de Factory I/O")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar aplicación principal: {str(e)}")

    def user_exists(self, username):
        try:
            if os.path.exists("faces_data.pkl"):
                with open("faces_data.pkl", 'rb') as f:
                    data = pickle.load(f)
                    usernames = data.get('usernames', {})
                    return username in usernames.values()
        except:
            pass
        return False
    
    def check_users_exist(self):
        """Verifica si hay usuarios registrados en el sistema"""
        try:
            if os.path.exists("faces_data.pkl") and os.path.exists("face_model.xml"):
                with open("faces_data.pkl", 'rb') as f:
                    data = pickle.load(f)
                    usernames = data.get('usernames', {})
                    faces = data.get('faces', [])
                    return len(usernames) > 0 and len(faces) > 0
        except:
            pass
        return False
    
    def update_system_status(self):
        """Actualiza el estado del sistema en la interfaz"""
        if self.check_users_exist():
            try:
                with open("faces_data.pkl", 'rb') as f:
                    data = pickle.load(f)
                    num_users = len(data.get('usernames', {}))
                    self.status_text.setText(f"✅ Sistema listo\n{num_users} usuario(s) registrado(s)")
                    self.status_text.setStyleSheet("color: #27ae60; font-weight: bold;")
            except:
                self.status_text.setText("✅ Sistema listo para autenticación")
                self.status_text.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.status_text.setText("⚠️ Sin usuarios registrados\nVe a 'Registro'")
            self.status_text.setStyleSheet("color: #f39c12; font-weight: bold;")
    
    def load_users_list(self):
        self.users_list.clear()
        try:
            if os.path.exists("faces_data.pkl"):
                with open("faces_data.pkl", 'rb') as f:
                    data = pickle.load(f)
                    usernames = data.get('usernames', {})
                    
                    for label, username in usernames.items():
                        item = QListWidgetItem(f"👤 {username} (ID: {label})")
                        self.users_list.addItem(item)
                        
                    if not usernames:
                        self.users_list.addItem(QListWidgetItem("No hay usuarios registrados"))
            else:
                self.users_list.addItem(QListWidgetItem("No hay datos de usuarios"))
        except Exception as e:
            self.users_list.addItem(QListWidgetItem(f"Error cargando usuarios: {str(e)}"))
    
    def delete_user(self):
        current_item = self.users_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Selecciona un usuario para eliminar")
            return
            
        # Extraer ID del usuario del texto del item
        item_text = current_item.text()
        if "ID:" in item_text:
            try:
                user_id = int(item_text.split("ID: ")[1].split(")")[0])
                username = item_text.split("👤 ")[1].split(" (ID:")[0]
                
                reply = QMessageBox.question(self, "Confirmar", 
                                           f"¿Eliminar usuario '{username}'?",
                                           QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.remove_user_data(user_id)
                    self.load_users_list()
                    self.update_system_status()
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error eliminando usuario: {str(e)}")
    
    def remove_user_data(self, user_id):
        try:
            if os.path.exists("faces_data.pkl"):
                with open("faces_data.pkl", 'rb') as f:
                    data = pickle.load(f)
                
                # Remover datos del usuario específico
                faces = data.get('faces', [])
                labels = data.get('labels', [])
                usernames = data.get('usernames', {})
                
                # Filtrar datos
                new_faces = []
                new_labels = []
                for i, label in enumerate(labels):
                    if label != user_id:
                        new_faces.append(faces[i])
                        new_labels.append(label)
                
                # Remover username
                if user_id in usernames:
                    del usernames[user_id]
                
                # Guardar datos actualizados
                updated_data = {
                    'faces': new_faces,
                    'labels': new_labels,
                    'usernames': usernames
                }
                
                with open("faces_data.pkl", 'wb') as f:
                    pickle.dump(updated_data, f)
                
                # Re-entrenar modelo si hay datos
                if new_faces:
                    recognizer = cv2.face.LBPHFaceRecognizer_create()
                    recognizer.train(new_faces, np.array(new_labels))
                    recognizer.save("face_model.xml")
                else:
                    # Si no hay usuarios, eliminar modelo
                    if os.path.exists("face_model.xml"):
                        os.remove("face_model.xml")
                
                QMessageBox.information(self, "Éxito", "Usuario eliminado correctamente")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error eliminando usuario: {str(e)}")
    
    def create_backup(self):
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            backup_dir = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para respaldo")
            if backup_dir:
                import shutil
                
                # Copiar archivos de datos
                if os.path.exists("faces_data.pkl"):
                    shutil.copy2("faces_data.pkl", f"{backup_dir}/faces_data_backup_{timestamp}.pkl")
                
                if os.path.exists("face_model.xml"):
                    shutil.copy2("face_model.xml", f"{backup_dir}/face_model_backup_{timestamp}.xml")
                
                QMessageBox.information(self, "Éxito", f"Respaldo creado en:\n{backup_dir}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error creando respaldo: {str(e)}")
    
    def rebuild_model(self):
        """Reconstruir el modelo desde los datos guardados"""
        try:
            if not os.path.exists("faces_data.pkl"):
                QMessageBox.warning(self, "Error", "No hay datos de usuarios guardados")
                return
                
            reply = QMessageBox.question(self, "Confirmar", 
                                       "¿Reconstruir el modelo de reconocimiento?\n\n"
                                       "Esto puede ayudar si hay problemas de reconocimiento.",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                with open("faces_data.pkl", 'rb') as f:
                    data = pickle.load(f)
                    faces = data.get('faces', [])
                    labels = data.get('labels', [])
                    
                if faces and labels:
                    # Crear nuevo reconocedor
                    recognizer = cv2.face.LBPHFaceRecognizer_create()
                    recognizer.setThreshold(100.0)
                    
                    # Entrenar con todos los datos
                    recognizer.train(faces, np.array(labels))
                    
                    # Guardar modelo
                    recognizer.save("face_model.xml")
                    
                    QMessageBox.information(self, "Éxito", 
                                          "Modelo reconstruido exitosamente.\n\n"
                                          "Prueba la autenticación nuevamente.")
                else:
                    QMessageBox.warning(self, "Error", "No hay datos suficientes para entrenar")
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error reconstruyendo modelo: {str(e)}")
    
    def show_debug_info(self):
        """Muestra información de debug del sistema"""
        debug_info = "🔧 Información de Debug\n" + "="*30 + "\n\n"
        
        try:
            # Verificar archivos
            debug_info += "📁 Archivos del sistema:\n"
            debug_info += f"- faces_data.pkl: {'✅ Existe' if os.path.exists('faces_data.pkl') else '❌ No existe'}\n"
            debug_info += f"- face_model.xml: {'✅ Existe' if os.path.exists('face_model.xml') else '❌ No existe'}\n\n"
            
            # Información de datos
            if os.path.exists("faces_data.pkl"):
                with open("faces_data.pkl", 'rb') as f:
                    data = pickle.load(f)
                    usernames = data.get('usernames', {})
                    faces = data.get('faces', [])
                    labels = data.get('labels', [])
                    
                    debug_info += "👥 Usuarios registrados:\n"
                    for label, username in usernames.items():
                        face_count = labels.count(label)
                        debug_info += f"   - {username} (ID: {label}) - {face_count} muestras\n"
                    
                    debug_info += f"\n📊 Total de caras: {len(faces)}\n"
                    debug_info += f"📊 Total de etiquetas: {len(labels)}\n"
            
            # Mostrar en un diálogo
            msg = QMessageBox()
            msg.setWindowTitle("Debug del Sistema")
            msg.setText(debug_info)
            msg.setIcon(QMessageBox.Information)
            msg.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error obteniendo información: {str(e)}")
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana"""
        if self.face_thread:
            self.face_thread.stop()
        
        # Emitir señal de cierre
        self.login_closed.emit()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Factory I/O Login System")
    app.setOrganizationName("Industrial Automation")
    app.setStyle('Fusion')
    
    # Verificar dependencias
    try:
        import cv2
        import numpy as np
        import pickle
        
        # Verificar que opencv-contrib-python está instalado
        if not hasattr(cv2.face, 'LBPHFaceRecognizer_create'):
            QMessageBox.critical(None, "Error de Dependencias", 
                               "opencv-contrib-python no está instalado correctamente.\n\n"
                               "Ejecuta: pip install opencv-contrib-python")
            sys.exit(1)
            
    except ImportError as e:
        QMessageBox.critical(None, "Error de Dependencias", 
                           f"Falta instalar dependencias:\n{str(e)}\n\n"
                           "Ejecuta: pip install opencv-python opencv-contrib-python numpy PyQt5")
        sys.exit(1)
    
    window = LoginWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()