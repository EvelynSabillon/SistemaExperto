import sys
import socket
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTextEdit, QFrame, QSplitter, QGroupBox, QGridLayout,
                            QTabWidget, QScrollArea, QCheckBox, QSlider)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt, QSettings
from PyQt5.QtGui import QFont, QIcon
import google.generativeai as genai
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

class ModbusWorker(QThread):
    connection_status = pyqtSignal(bool)
    error_message = pyqtSignal(str)
    sensor_data = pyqtSignal(dict)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.client = None
        self.running = False


    def run(self):
        try:
            self.client = ModbusTcpClient(self.host, port=self.port)
            connection = self.client.connect()
            if connection:
                self.connection_status.emit(True)
                self.running = True
                while self.running:
                    self.read_sensors()
                    self.msleep(500)
            else:
                self.connection_status.emit(False)
                self.error_message.emit("Conexión fallida")
        except Exception as e:
            self.connection_status.emit(False)
            self.error_message.emit(f"Error: {str(e)}")

    def read_sensors(self):
        if self.client:
            try:
                # Leer inputs (sensores) - VERSIÓN CORREGIDA
                sensor_data = {}
                
                # Opción 1: Para pymodbus >= 3.0 (sintaxis con argumentos nombrados)
                try:
                    inputs = self.client.read_discrete_inputs(address=0, count=7)
                    if not inputs.isError():
                        sensor_data['inputs'] = inputs.bits[:7]
                except TypeError:
                    # Opción 2: Para pymodbus < 3.0 (sintaxis antigua)
                    inputs = self.client.read_discrete_inputs(0, 7, unit=1)
                    if not inputs.isError():
                        sensor_data['inputs'] = inputs.bits[:7]
                
                # Leer coils (actuadores) - VERSIÓN CORREGIDA
                try:
                    coils = self.client.read_coils(address=0, count=9)
                    if not coils.isError():
                        sensor_data['coils'] = coils.bits[:9]
                except TypeError:
                    # Para versiones antiguas
                    coils = self.client.read_coils(0, 7, unit=1)
                    if not coils.isError():
                        sensor_data['coils'] = coils.bits[:7]
                
                self.sensor_data.emit(sensor_data)
            except Exception as e:
                self.error_message.emit(f"Error leyendo datos: {str(e)}")

    def stop(self):
        self.running = False
        if self.client:
            self.client.close()
        self.quit()
        self.wait()

class ThemeManager:
    @staticmethod
    def get_light_theme():
        return """
            QMainWindow {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QWidget {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #34495e;
                background-color: #ffffff;
            }
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            QTextEdit {
                border: 1px solid #ecf0f1;
                border-radius: 6px;
                padding: 8px;
                background-color: #f8f9fa;
                color: #2c3e50;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #7f8c8d;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """

    @staticmethod
    def get_dark_theme():
        return """
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #2d2d2d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #ffffff;
                background-color: #1e1e1e;
            }
            QLineEdit {
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #0078d4;
                outline: none;
            }
            QTextEdit {
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 8px;
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
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: white;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """

class FactoryIOController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('FactoryIO', 'Controller')
        self.dark_mode = self.settings.value('dark_mode', False, type=bool)
        
        self.setWindowTitle("Factory I/O Controller Pro")
        self.setGeometry(100, 100, 1200, 800)
        
        self.modbus_client = None
        self.worker_thread = None
        self.is_connected = False

        self.host = "127.0.0.1"
        self.port = 502

        # Mapeo de dispositivos según la imagen
        self.device_mapping = {
            'inputs': {
                0: 'Start Button 1',
                1: 'Stop Button 1', 
                2: 'Diffuse Sensor 1',
                3: 'Diffuse Sensor 2',
                4: 'Diffuse Sensor 3',
                5: 'Reset Button 1',
            },
            'coils': {
                0: 'Motor',
                1: 'Start Button 1 (Light)',
                2: 'Stop Button 1 (Light)', 
                3: 'Stack Light 1 (Green)',
                4: 'Stack Light 1 (Yellow)',
                5: 'Stack Light 1 (Red)',
                6: 'Reset Button 1 (Light)',
                7: 'Emitter 1 (Emit)',
                8: 'Remover 1 (Remove)',
            }
        }

        self.sensor_states = {}
        self.actuator_states = {}

        self.init_ui()
        self.setup_timer()
        self.apply_theme()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # HEADER - Estado de conexión y toggle modo oscuro
        header_widget = self.create_header_widget()
        main_layout.addWidget(header_widget)

        # Línea separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ecf0f1; max-height: 1px;")
        main_layout.addWidget(separator)

        # CONTENIDO PRINCIPAL - Solo 2 tabs ahora
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget::pane { margin: 0px; }")

        # Tab 1: Conexión y Control (incluye actuadores y IA)
        control_tab = self.create_control_tab()
        self.tab_widget.addTab(control_tab, "🔧 Control")

        # Tab 2: Monitoreo
        monitor_tab = self.create_monitor_tab()
        self.tab_widget.addTab(monitor_tab, "📊 Monitoreo")

        main_layout.addWidget(self.tab_widget)

    def create_header_widget(self):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setSpacing(20)

        # Lado izquierdo - Título y estado
        left_section = QWidget()
        left_layout = QVBoxLayout(left_section)
        left_layout.setSpacing(5)

        title = QLabel("Factory I/O Controller Pro")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #3498db; margin-bottom: 5px;")
        left_layout.addWidget(title)

        # Estado de conexión
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 14))
        self.status_indicator.setStyleSheet("color: #e74c3c;")
        
        self.status_text = QLabel("Desconectado")
        self.status_text.setFont(QFont("Arial", 12, QFont.Medium))
        self.status_text.setStyleSheet("color: #7f8c8d; margin-left: 8px;")

        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        left_layout.addWidget(status_widget)
        header_layout.addWidget(left_section)

        # Lado derecho - Toggle modo oscuro
        header_layout.addStretch()
        
        theme_widget = QWidget()
        theme_layout = QHBoxLayout(theme_widget)
        theme_layout.setContentsMargins(0, 0, 0, 0)

        theme_label = QLabel("Modo Oscuro")
        theme_label.setFont(QFont("Arial", 10))
        
        self.dark_mode_toggle = QCheckBox()
        self.dark_mode_toggle.setChecked(self.dark_mode)
        self.dark_mode_toggle.stateChanged.connect(self.toggle_theme)
        self.dark_mode_toggle.setStyleSheet("""
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
                border-radius: 10px;
                background-color: #bdc3c7;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
            }
        """)

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.dark_mode_toggle)
        header_layout.addWidget(theme_widget)

        return header_widget


    # Modificar on_connection_status para habilitar/deshabilitar modo automático
    def on_connection_status_modified(self, connected):
        self.is_connected = connected
        if connected:
            self.status_indicator.setStyleSheet("color: #27ae60;")
            self.status_text.setText("Conectado")
            self.status_text.setStyleSheet("color: #27ae60; margin-left: 8px; font-weight: 600;")
            self.btn_connect.setText("🔌 Desconectar")

            # HABILITAR CONTROLES DE ACTUADORES AL CONECTAR
            for address, controls in self.actuator_states.items():
                controls['btn_on'].setEnabled(True)
                controls['btn_off'].setEnabled(True)
            
            self.clear_all_states()

            self.log_message("✅ Conectado exitosamente")
            self.modbus_client = self.worker_thread.client
        else:
            self.status_indicator.setStyleSheet("color: #e74c3c;")
            self.status_text.setText("Desconectado")
            self.status_text.setStyleSheet("color: #e74c3c; margin-left: 8px; font-weight: 600;")
            self.btn_connect.setText("🔌 Conectar")
            
            # Deshabilitar controles
            for address, controls in self.actuator_states.items():
                controls['btn_on'].setEnabled(False)
                controls['btn_off'].setEnabled(False)
            
            
            self.clear_all_states()
            self.log_message("❌ Desconectado")

        self.btn_connect.setEnabled(True)

    def create_control_tab(self):
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)  # Cambio a QHBoxLayout para disposición horizontal
        control_layout.setSpacing(15)

        # Panel izquierdo - Conexión y Control de Actuadores
        connection_group = QGroupBox("🔌 Conexión y Control")
        connection_layout = QVBoxLayout(connection_group)
        connection_layout.setSpacing(15)

        # Sección de conexión
        connection_section = QWidget()
        connection_section_layout = QVBoxLayout(connection_section)
        
        # Inputs de conexión
        connection_inputs = QHBoxLayout()
        
        self.ip_input = QLineEdit(self.host)
        self.ip_input.setPlaceholderText("Dirección IP")
        
        self.port_input = QLineEdit(str(self.port))
        self.port_input.setPlaceholderText("Puerto")
        self.port_input.setMaximumWidth(100)

        connection_inputs.addWidget(QLabel("IP:"))
        connection_inputs.addWidget(self.ip_input)
        connection_inputs.addWidget(QLabel("Puerto:"))
        connection_inputs.addWidget(self.port_input)
        connection_inputs.addStretch()
        connection_section_layout.addLayout(connection_inputs)

        # Botón conectar
        self.btn_connect = QPushButton("🔌 Conectar")
        self.btn_connect.setStyleSheet(self.get_button_style("#3498db", "#2980b9"))
        self.btn_connect.setMaximumWidth(150)
        self.btn_connect.clicked.connect(self.toggle_connection)
        connection_section_layout.addWidget(self.btn_connect)

        
        
        connection_layout.addWidget(connection_section)

        # Línea separadora dentro del grupo
        separator_internal = QFrame()
        separator_internal.setFrameShape(QFrame.HLine)
        separator_internal.setStyleSheet("background-color: #bdc3c7; max-height: 1px; margin: 10px 0;")
        connection_layout.addWidget(separator_internal)

        # Sección de control de actuadores
        actuators_label = QLabel("⚡ Control de Actuadores")
        actuators_label.setFont(QFont("Arial", 12, QFont.Bold))
        connection_layout.addWidget(actuators_label)

        # Scroll area para actuadores
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)  # Aumentado para mejor uso del espacio vertical
        
        actuators_widget = QWidget()
        self.actuators_grid = QGridLayout(actuators_widget)
        
        self.create_actuator_controls()
        
        scroll_area.setWidget(actuators_widget)
        connection_layout.addWidget(scroll_area)

        # Agregar el panel izquierdo al layout principal
        control_layout.addWidget(connection_group)

        # Panel derecho - Log de actividades y IA
        log_ia_group = QGroupBox("📋 Log de Actividades y Asistente IA")
        log_ia_layout = QVBoxLayout(log_ia_group)
        log_ia_layout.setSpacing(10)

        # Log de actividades
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)  # Ajustado para el nuevo layout
        self.log_text.setFont(QFont("Courier New", 9))
        log_ia_layout.addWidget(self.log_text)

        # Línea separadora
        separator_log_ia = QFrame()
        separator_log_ia.setFrameShape(QFrame.HLine)
        separator_log_ia.setStyleSheet("background-color: #bdc3c7; max-height: 1px; margin: 5px 0;")
        log_ia_layout.addWidget(separator_log_ia)

        # Sección IA
        ia_label = QLabel("🤖 Asistente de IA")
        ia_label.setFont(QFont("Arial", 11, QFont.Bold))
        log_ia_layout.addWidget(ia_label)

        # Input para prompt en una línea horizontal
        prompt_layout = QHBoxLayout()
        
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Pregunta sobre el sistema, troubleshooting, etc...")
        self.prompt_input.returnPressed.connect(self.send_prompt_to_ai)

        self.btn_send_prompt = QPushButton("📤 Enviar")
        self.btn_send_prompt.setStyleSheet(self.get_button_style("#9b59b6", "#8e44ad"))
        self.btn_send_prompt.setMaximumWidth(100)
        self.btn_send_prompt.clicked.connect(self.send_prompt_to_ai)

        prompt_layout.addWidget(self.prompt_input)
        prompt_layout.addWidget(self.btn_send_prompt)
        log_ia_layout.addLayout(prompt_layout)

        # Área de respuesta IA
        self.ia_response_text = QTextEdit()
        self.ia_response_text.setFont(QFont("Arial", 10))
        self.ia_response_text.setMaximumHeight(180)  # Ajustado para el nuevo layout
        log_ia_layout.addWidget(self.ia_response_text)

        # Botón limpiar IA
        clear_btn = QPushButton("🗑️ Limpiar Chat IA")
        clear_btn.setStyleSheet(self.get_button_style("#7f8c8d", "#95a5a6"))
        clear_btn.setMaximumWidth(150)
        clear_btn.clicked.connect(lambda: self.ia_response_text.clear())
        log_ia_layout.addWidget(clear_btn)

        # Agregar el panel derecho al layout principal
        control_layout.addWidget(log_ia_group)
        
        # Establecer proporciones: panel izquierdo (45%), panel derecho (55%)
        control_layout.setStretchFactor(connection_group, 45)
        control_layout.setStretchFactor(log_ia_group, 55)

        return control_widget

    def create_monitor_tab(self):
        monitor_widget = QWidget()
        monitor_layout = QHBoxLayout(monitor_widget)
        monitor_layout.setSpacing(15)

        # Panel de sensores
        sensors_group = QGroupBox("📡 Estado de Sensores")
        sensors_layout = QVBoxLayout(sensors_group)

        # Scroll area para sensores
        sensors_scroll = QScrollArea()
        sensors_scroll.setWidgetResizable(True)
        sensors_scroll.setMaximumHeight(300)
        
        sensors_widget = QWidget()
        self.sensors_grid = QGridLayout(sensors_widget)
        
        self.create_sensor_displays()
        
        sensors_scroll.setWidget(sensors_widget)
        sensors_layout.addWidget(sensors_scroll)
        monitor_layout.addWidget(sensors_group)

        # Panel de actuadores (solo lectura)
        actuators_status_group = QGroupBox("⚡ Estado de Actuadores")
        actuators_status_layout = QVBoxLayout(actuators_status_group)

        actuators_status_scroll = QScrollArea()
        actuators_status_scroll.setWidgetResizable(True)
        actuators_status_scroll.setMaximumHeight(300)
        
        actuators_status_widget = QWidget()
        self.actuators_status_grid = QGridLayout(actuators_status_widget)
        
        self.create_actuator_displays()
        
        actuators_status_scroll.setWidget(actuators_status_widget)
        actuators_status_layout.addWidget(actuators_status_scroll)
        monitor_layout.addWidget(actuators_status_group)

        return monitor_widget

    def create_actuator_controls(self):
        row = 0
        for address, name in self.device_mapping['coils'].items():
            # Label del actuador
            label = QLabel(f"{name}:")
            label.setFont(QFont("Arial", 10, QFont.Medium))
            
            # Botón ON
            btn_on = QPushButton("ON")
            btn_on.setStyleSheet(self.get_button_style("#27ae60", "#229954"))
            btn_on.setMaximumWidth(60)
            btn_on.clicked.connect(lambda checked, addr=address: self.control_actuator(addr, True))
            btn_on.setEnabled(False)
            
            # Botón OFF
            btn_off = QPushButton("OFF")
            btn_off.setStyleSheet(self.get_button_style("#e74c3c", "#c0392b"))
            btn_off.setMaximumWidth(60)
            btn_off.clicked.connect(lambda checked, addr=address: self.control_actuator(addr, False))
            btn_off.setEnabled(False)
            
            # Estado
            status_label = QLabel("●")
            status_label.setFont(QFont("Arial", 12))
            status_label.setStyleSheet("color: #bdc3c7;")
            
            self.actuator_states[address] = {
                'btn_on': btn_on,
                'btn_off': btn_off,
                'status': status_label
            }
            
            self.actuators_grid.addWidget(label, row, 0)
            self.actuators_grid.addWidget(btn_on, row, 1)
            self.actuators_grid.addWidget(btn_off, row, 2)
            self.actuators_grid.addWidget(status_label, row, 3)
            row += 1

    def create_sensor_displays(self):
        row = 0
        for address, name in self.device_mapping['inputs'].items():
            label = QLabel(f"{name}:")
            label.setFont(QFont("Arial", 10, QFont.Medium))
            
            status_label = QLabel("●")
            status_label.setFont(QFont("Arial", 14))
            status_label.setStyleSheet("color: #bdc3c7;")
            
            value_label = QLabel("INACTIVO")
            value_label.setFont(QFont("Arial", 10, QFont.Bold))
            value_label.setStyleSheet("color: #7f8c8d;")
            
            self.sensor_states[address] = {
                'status': status_label,
                'value': value_label
            }
            
            self.sensors_grid.addWidget(label, row, 0)
            self.sensors_grid.addWidget(status_label, row, 1)
            self.sensors_grid.addWidget(value_label, row, 2)
            row += 1

    def create_actuator_displays(self):
        row = 0
        for address, name in self.device_mapping['coils'].items():
            if address not in self.actuator_states:
                continue
                
            label = QLabel(f"{name}:")
            label.setFont(QFont("Arial", 10, QFont.Medium))
            
            status_label = QLabel("●")
            status_label.setFont(QFont("Arial", 14))
            status_label.setStyleSheet("color: #bdc3c7;")
            
            value_label = QLabel("OFF")
            value_label.setFont(QFont("Arial", 10, QFont.Bold))
            value_label.setStyleSheet("color: #7f8c8d;")
            
            # Agregar referencia para actualización
            self.actuator_states[address]['monitor_status'] = status_label
            self.actuator_states[address]['monitor_value'] = value_label
            
            self.actuators_status_grid.addWidget(label, row, 0)
            self.actuators_status_grid.addWidget(status_label, row, 1)
            self.actuators_status_grid.addWidget(value_label, row, 2)
            row += 1

    def get_button_style(self, color, hover_color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """

    def setup_timer(self):
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(5000)

    def toggle_theme(self):
        self.dark_mode = self.dark_mode_toggle.isChecked()
        self.settings.setValue('dark_mode', self.dark_mode)
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(ThemeManager.get_dark_theme())
        else:
            self.setStyleSheet(ThemeManager.get_light_theme())

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_to_factory_io()
        else:
            self.disconnect_from_factory_io()

    def connect_to_factory_io(self):
        try:
            self.host = self.ip_input.text()
            self.port = int(self.port_input.text())

            self.worker_thread = ModbusWorker(self.host, self.port)
            self.worker_thread.connection_status.connect(self.on_connection_status)
            self.worker_thread.error_message.connect(self.on_connection_error)
            self.worker_thread.sensor_data.connect(self.update_sensor_data)
            self.worker_thread.start()

            self.btn_connect.setText("🔄 Conectando...")
            self.btn_connect.setEnabled(False)

        except ValueError:
            self.log_message("❌ Puerto inválido")
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")

    def clear_all_states(self):
        """Limpia el estado visual de todos los sensores y actuadores"""
        # Limpiar estado de sensores
        for address, sensor in self.sensor_states.items():
            sensor['status'].setStyleSheet("color: #bdc3c7;")
            sensor['value'].setText("INACTIVO")
            sensor['value'].setStyleSheet("color: #7f8c8d; font-weight: bold;")
        
        # Limpiar estado de actuadores
        for address, controls in self.actuator_states.items():
            controls['status'].setStyleSheet("color: #bdc3c7;")
            if 'monitor_status' in controls:
                controls['monitor_status'].setStyleSheet("color: #bdc3c7;")
                controls['monitor_value'].setText("OFF")
                controls['monitor_value'].setStyleSheet("color: #7f8c8d; font-weight: bold;")

    def on_connection_status(self, connected):
        self.is_connected = connected
        if connected:
            self.status_indicator.setStyleSheet("color: #27ae60;")
            self.status_text.setText("Conectado")
            self.status_text.setStyleSheet("color: #27ae60; margin-left: 8px; font-weight: 600;")
            self.btn_connect.setText("🔌 Desconectar")

            # HABILITAR CONTROLES DE ACTUADORES AL CONECTAR
            for address, controls in self.actuator_states.items():
                controls['btn_on'].setEnabled(True)
                controls['btn_off'].setEnabled(True)
            
            # Limpiar estados al conectar
            self.clear_all_states()
                
            self.log_message("✅ Conectado exitosamente")
            self.modbus_client = self.worker_thread.client
        else:
            self.status_indicator.setStyleSheet("color: #e74c3c;")
            self.status_text.setText("Desconectado")
            self.status_text.setStyleSheet("color: #e74c3c; margin-left: 8px; font-weight: 600;")
            self.btn_connect.setText("🔌 Conectar")
            
            # Deshabilitar controles de actuadores
            for address, controls in self.actuator_states.items():
                controls['btn_on'].setEnabled(False)
                controls['btn_off'].setEnabled(False)

            # Limpiar estados al desconectar
            self.clear_all_states()
                
            self.log_message("❌ Desconectado")

        self.btn_connect.setEnabled(True)

    def on_connection_error(self, error_msg):
        self.log_message(f"❌ Error: {error_msg}")
        self.btn_connect.setText("🔌 Conectar")
        self.btn_connect.setEnabled(True)

    def disconnect_from_factory_io(self):
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread = None
        
        # Actualizar estado de conexión
        self.is_connected = False
        self.modbus_client = None
        
        # Actualizar interfaz de usuario
        self.status_indicator.setStyleSheet("color: #e74c3c;")
        self.status_text.setText("Desconectado")
        self.status_text.setStyleSheet("color: #e74c3c; margin-left: 8px; font-weight: 600;")
        self.btn_connect.setText("🔌 Conectar")
        self.btn_connect.setEnabled(True)
        
        # Deshabilitar controles de actuadores
        for address, controls in self.actuator_states.items():
            controls['btn_on'].setEnabled(False)
            controls['btn_off'].setEnabled(False)
        
        # Limpiar todos los estados
        self.clear_all_states()
        
        # Registrar en el log
        self.log_message("❌ Desconectado manualmente")
        
    def control_actuator(self, address, state):
        if self.is_connected and self.modbus_client:
            try:
                # Corregir sintaxis según versión de pymodbus
                try:
                    result = self.modbus_client.write_coil(address=address, value=state)
                except TypeError:
                    result = self.modbus_client.write_coil(address, state, unit=1)
                    
                if not result.isError():
                    device_name = self.device_mapping['coils'].get(address, f"Coil {address}")
                    state_text = "ON" if state else "OFF"
                    self.log_message(f"✅ {device_name}: {state_text}")
                else:
                    self.log_message(f"❌ Error controlando dispositivo en dirección {address}")
            except Exception as e:
                self.log_message(f"❌ Error: {str(e)}")

    def update_sensor_data(self, data):
        # Actualizar sensores
        if 'inputs' in data:
            for i, state in enumerate(data['inputs']):
                if i in self.sensor_states:
                    if state:
                        self.sensor_states[i]['status'].setStyleSheet("color: #27ae60;")
                        self.sensor_states[i]['value'].setText("ACTIVO")
                        self.sensor_states[i]['value'].setStyleSheet("color: #27ae60; font-weight: bold;")
                    else:
                        self.sensor_states[i]['status'].setStyleSheet("color: #bdc3c7;")
                        self.sensor_states[i]['value'].setText("INACTIVO")
                        self.sensor_states[i]['value'].setStyleSheet("color: #7f8c8d; font-weight: bold;")

        # Actualizar estado de actuadores
        if 'coils' in data:
            for i, state in enumerate(data['coils']):
                if i in self.actuator_states:
                    if state:
                        self.actuator_states[i]['status'].setStyleSheet("color: #27ae60;")
                        if 'monitor_status' in self.actuator_states[i]:
                            self.actuator_states[i]['monitor_status'].setStyleSheet("color: #27ae60;")
                            self.actuator_states[i]['monitor_value'].setText("ON")
                            self.actuator_states[i]['monitor_value'].setStyleSheet("color: #27ae60; font-weight: bold;")
                    else:
                        self.actuator_states[i]['status'].setStyleSheet("color: #bdc3c7;")
                        if 'monitor_status' in self.actuator_states[i]:
                            self.actuator_states[i]['monitor_status'].setStyleSheet("color: #bdc3c7;")
                            self.actuator_states[i]['monitor_value'].setText("OFF")
                            self.actuator_states[i]['monitor_value'].setStyleSheet("color: #7f8c8d; font-weight: bold;")

    def check_connection(self):
        if self.is_connected and self.modbus_client:
            try:
                # Usar sintaxis corregida
                try:
                    result = self.modbus_client.read_coils(address=0, count=1)
                except TypeError:
                    result = self.modbus_client.read_coils(0, 1, unit=1)
                    
                if result.isError():
                    self.log_message("⚠️ Conexión inestable")
            except Exception as e:
                self.log_message(f"⚠️ Problema de conexión: {str(e)}")

    def send_prompt_to_ai(self):
        prompt = self.prompt_input.text().strip()
        if not prompt:
            return
        
        self.prompt_input.clear()
        self.ia_response_text.append(f"🤔 Pregunta: {prompt}")
        self.ia_response_text.append("⏳ Procesando...")
        
        # Agregar contexto del sistema
        system_context = f"""
        Sistema Factory I/O Controller:
        - Estado de conexión: {'Conectado' if self.is_connected else 'Desconectado'}
        - Host: {self.host}:{self.port}
        - Dispositivos disponibles:
          Sensores: {list(self.device_mapping['inputs'].values())}
          Actuadores: {list(self.device_mapping['coils'].values())}
        """
        
        full_prompt = f"{system_context}\n\nPregunta del usuario: {prompt}"
        
        try:
            import google.generativeai as genai
            API_KEY = "AIzaSyB4hptdAfmMwWHRgm6bNLTpu5uKAFyecV8"
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            response = model.generate_content(full_prompt)
            
            # Limpiar la línea de "Procesando..."
            text = self.ia_response_text.toPlainText()
            lines = text.split('\n')
            if lines and "⏳ Procesando..." in lines[-1]:
                lines = lines[:-1]
                self.ia_response_text.clear()
                self.ia_response_text.append('\n'.join(lines))
            
            self.ia_response_text.append(f"🤖 Respuesta: {response.text}\n")
            self.ia_response_text.append("─" * 30 + "\n")
            
        except Exception as e:
            # Limpiar la línea de "Procesando..."
            text = self.ia_response_text.toPlainText()
            lines = text.split('\n')
            if lines and "⏳ Procesando..." in lines[-1]:
                lines = lines[:-1]
                self.ia_response_text.clear()
                self.ia_response_text.append('\n'.join(lines))
            
            self.ia_response_text.append(f"❌ Error al consultar IA: {str(e)}\n")
            self.ia_response_text.append("─" * 30 + "\n")

    def log_message(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto scroll al final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        if self.worker_thread:
            self.worker_thread.stop()
        event.accept()

def main():
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("Factory I/O Controller Pro")
    app.setOrganizationName("Industrial Automation")
    
    # Configurar estilo base
    app.setStyle('Fusion')
    
    window = FactoryIOController()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()