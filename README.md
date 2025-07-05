# 🏭 Factory I/O Controller System v2.0

Sistema de control industrial con autenticación facial avanzada, diseñado para trabajar con Factory I/O y comunicación Modbus.

## 🌟 Características Principales

- **🔐 Autenticación Facial**: Sistema de login seguro con reconocimiento facial
- **⚡ Control Modbus**: Comunicación directa con Factory I/O
- **🤖 Asistente IA**: Integrado con Google Gemini para soporte técnico
- **🎨 Interfaz Moderna**: Diseño profesional con modo claro/oscuro
- **📊 Monitoreo en Tiempo Real**: Visualización de sensores y actuadores
- **👥 Gestión de Usuarios**: Registro, eliminación y respaldo de usuarios
- **🔗 Integración Mejorada**: Sistema de autenticación conectado con aplicación principal

## 📋 Estructura del Proyecto

```
Factory-IO-Controller/
├── main.py                 # 🚀 Lanzador principal
├── login.py               # 🔐 Sistema de autenticación facial  
├── main2.py               # 🏭 Aplicación principal de control
├── launcher.py            # 🚀 Launcher completo del sistema
├── integration_example.py # 📝 Ejemplo de integración
├── install_requirements.py # 📦 Instalador de dependencias
├── requirements.txt       # 📝 Lista de dependencias
├── README.md             # 📖 Esta documentación
├── faces_data.pkl        # 💾 Datos de usuarios (se genera automáticamente)
└── face_model.xml        # 🧠 Modelo de reconocimiento (se genera automáticamente)
```

## 🛠️ Instalación

### Paso 1: Verificar Requisitos del Sistema

- **Python**: 3.7 o superior
- **Cámara Web**: Para reconocimiento facial
- **Factory I/O**: Para comunicación Modbus (opcional para testing)

### Paso 2: Instalación Automática

```bash
# Opción 1: Instalación automática (recomendada)
python install_requirements.py

# Opción 2: Instalación manual
pip install -r requirements.txt

# Opción 3: Instalación individual
pip install opencv-python opencv-contrib-python numpy PyQt5 google-generativeai pymodbus
```

### Paso 3: Verificar Instalación

## 🚀 Uso del Sistema

### Opción 1: Launcher Completo (Recomendado)
```bash
python launcher.py
```

### Opción 2: Solo Sistema de Login
```bash
python login.py
```

### Opción 3: Integración Personalizada
Ver `integration_example.py` para ejemplos de integración

## 🔐 Flujo de Autenticación

1. **Registro**: Captura 30 muestras faciales del usuario
2. **Autenticación**: Reconoce usuarios en tiempo real
3. **Aplicación Principal**: Lanza automáticamente después de autenticación exitosa

## 🔧 Integración con tu Código

### Modificaciones Necesarias en tu Código:

```python
# ANTES (código original)
self.login_window.launch_main_application = self.launch_main_application
self.login_window.closeEvent = self.on_login_closed

# DESPUÉS (código actualizado)
self.login_window.set_external_launcher(self.launch_main_application)
self.login_window.login_closed.connect(self.on_login_closed)
```

### Ejemplo Completo de Integración:

```python
def launch_login_system(self):
    """Inicia el sistema de login con reconocimiento facial"""
    try:
        import login
        
        self.login_window = login.LoginWindow()
        
        # ✅ Configurar launcher externo
        self.login_window.set_external_launcher(self.launch_main_application)
        
        # ✅ Conectar señal de cierre
        self.login_window.login_closed.connect(self.on_login_closed)
        
        self.login_window.show()
        
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error iniciando sistema de login:\n{str(e)}")
        sys.exit(1)

def launch_main_application(self):
    """Lanza la aplicación principal después de autenticación exitosa"""
    try:
        # Cerrar ventana de login
        if self.login_window:
            self.login_window.close()
        
        # Importar y crear aplicación principal
        import main2
        
        self.main_window = main2.FactoryIOController()
        self.main_window.show()
        
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error lanzando aplicación principal:\n{str(e)}")
        sys.exit(1)

def on_login_closed(self):
    """Maneja el evento de cierre de la ventana de login"""
    # Si se cierra el login sin autenticación, salir de la aplicación
    if not self.main_window:
        self.app.quit()
```

```bash
python main.py
```

## 🚀 Uso del Sistema

### Ejecución Principal

```bash
python main.py
```

Este comando ejecutará el flujo completo:
1. Verificación de dependencias
2. Sistema de login con reconocimiento facial
3. Una vez autenticado, lanza la aplicación principal

### Ejecución Individual de Módulos

```bash
# Solo sistema de login
python login.py

# Solo aplicación principal (sin autenticación)
python main2.py
```

## 🔐 Sistema de Autenticación

### Primera Vez - Registro de Usuario

1. Ejecuta `python main.py`
2. Ve a la pestaña **"👤 Registro"**
3. Ingresa tu nombre de usuario
4. Haz clic en **"🎯 Iniciar Registro"**
5. Mantente frente a la cámara hasta completar 30 capturas
6. El sistema entrenará automáticamente el modelo

### Login Posterior

1. Ejecuta `python main.py`
2. En la pestaña **"🔐 Autenticación"**
3. Haz clic en **"📷 Iniciar Cámara"**
4. Posiciónate frente a la cámara
5. El sistema te reconocerá automáticamente

### Gestión de Usuarios

En la pestaña **"⚙️ Gestión"** puedes:
- Ver lista de usuarios registrados
- Eliminar usuarios existentes
- Crear respaldos de datos
- Actualizar la lista de usuarios

## 🏭 Control Factory I/O

### Configuración de Conexión

1. Abre Factory I/O
2. Configura el servidor Modbus TCP (por defecto: 127.0.0.1:502)
3. En la aplicación, ingresa la IP y puerto
4. Haz clic en **"🔌 Conectar"**

### Dispositivos Soportados

**Sensores (Inputs):**
- Start Button 1
- Stop Button 1
- Diffuse Sensor 1, 2, 3
- Reset Button 1

**Actuadores (Coils):**
- Motor
- Luces de botones
- Stack Light (Verde, Amarillo, Rojo)
- Emitter 1
- Remover 1

### Control de Actuadores

- **Pestaña Control**: Botones ON/OFF para cada actuador
- **Pestaña Monitoreo**: Vista de solo lectura del estado actual

## 🤖 Asistente IA

El sistema incluye un asistente IA integrado que puede ayudar con:

- **Troubleshooting**: Diagnóstico de problemas
- **Consultas Técnicas**: Información sobre dispositivos
- **Guía de Uso**: Ayuda con la operación del sistema
- **Análisis de Estados**: Interpretación de datos de sensores

### Uso del Asistente

1. En la pestaña **"🔧 Control"**
2. Escribe tu consulta en el campo de texto
3. Haz clic en **"📤 Enviar"** o presiona Enter
4. Recibe respuesta instantánea del asistente

## ⚙️ Configuración Avanzada

### Archivos de Configuración

- **faces_data.pkl**: Datos de entrenamiento facial
- **face_model.xml**: Modelo entrenado de reconocimiento
- **Configuración Qt**: Se guarda automáticamente (tema, preferencias)

### Parámetros de Reconocimiento Facial

```python
# En login.py, puedes ajustar:
max_captures = 30          # Número de capturas para registro
confidence_threshold = 50  # Umbral de confianza (menor = más estricto)
```

### Configuración Modbus

```python
# En main2.py, configuración por defecto:
host = "127.0.0.1"        # IP del servidor Modbus
port = 502                # Puerto Modbus TCP
unit_id = 1               # ID de unidad Modbus
```

## 🔧 Troubleshooting

### Problemas Comunes

**Error: "No se pudo acceder a la cámara"**
- Verifica que la cámara esté conectada
- Cierra otras aplicaciones que usen la cámara
- Verifica permisos de cámara del sistema

**Error: "Conexión fallida" (Modbus)**
- Verifica que Factory I/O esté ejecutándose
- Confirma la configuración IP:Puerto
- Asegúrate de que el servidor Modbus esté habilitado

**Error: "Falta instalar dependencias"**
- Ejecuta: `python install_requirements.py`
- O instala manualmente: `pip install opencv-python opencv-contrib-python`

**Reconocimiento facial impreciso**
- Re-registra el usuario con mejor iluminación
- Asegúrate de estar solo en el encuadre
- Ajusta el umbral de confianza en el código

### Logs y Debugging

- Los logs se muestran en tiempo real en la pestaña Control
- Errores detallados aparecen en ventanas emergentes
- Para debugging avanzado, ejecuta desde terminal

## 📊 Especificaciones Técnicas

### Requisitos de Hardware

- **Procesador**: Intel i3 o AMD equivalente (mínimo)
- **RAM**: 4GB (8GB recomendado)
- **Cámara**: Resolución mínima 640x480
- **Espacio**: 100MB libres en disco

### Dependencias de Software

- **Python**: 3.7+
- **OpenCV**: 4.5.0+
- **PyQt5**: 5.15.0+
- **NumPy**: 1.19.0+
- **PyModbus**: 3.0.0+
- **Google Generative AI**: 0.3.0+

### Protocolos Soportados

- **Modbus TCP**: Comunicación con PLCs y Factory I/O
- **HTTP/HTTPS**: Para consultas IA
- **Webcam APIs**: Para captura de video

## 🔒 Seguridad y Privacidad

### Datos Faciales

- Los datos se almacenan **localmente** en archivos pickle
- **No se envían** datos faciales a servidores externos
- Los modelos se entrenan en tu máquina
- Puedes eliminar usuarios y datos en cualquier momento

### Respaldos

- Usa la función **"💾 Crear Respaldo"** regularmente
- Los respaldos incluyen datos de usuarios y modelos
- Almacena respaldos en ubicación segura

## 🤝 Contribución

Este proyecto es de código abierto. Contribuciones bienvenidas:

1. Fork del repositorio
2. Crea una rama para tu feature
3. Commit de cambios
4. Push a la rama
5. Crea Pull Request

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles

## 🆘 Soporte

Para soporte técnico:

1. **Asistente IA Integrado**: Úsalo para consultas rápidas
2. **Issues**: Crea un issue en el repositorio
3. **Documentación**: Consulta esta documentación
4. **Community**: Únete a las discusiones del proyecto

## 🔄 Changelog

### v2.0.0 (Actual)
- ✅ Sistema de autenticación facial
- ✅ Interfaz de login completa
- ✅ Gestión avanzada de usuarios
- ✅ Instalador automático de dependencias
- ✅ Documentación completa

### v1.0.0 (main2.py original)
- ✅ Control Modbus básico
- ✅ Interfaz de monitoreo
- ✅ Asistente IA
- ✅ Temas claro/oscuro

---

**Desarrollado con ❤️ para la automatización industrial**

🏭 **Factory I/O Controller System** - Llevando la seguridad y eficiencia al siguiente nivel