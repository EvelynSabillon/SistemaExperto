#!/usr/bin/env python3
"""
Factory I/O Controller - Sistema Principal con Autenticación
Autor: Sistema de Automatización Industrial
Versión: 2.0

Este archivo maneja el flujo completo:
1. Verifica dependencias
2. Ejecuta sistema de login con reconocimiento facial
3. Una vez autenticado, lanza la aplicación principal (main2.py)
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

class ApplicationLauncher:
    def __init__(self):
        self.app = None
        self.login_window = None
        self.main_window = None
        
    def check_dependencies(self):
        """Verifica que todas las dependencias estén instaladas"""
        missing_packages = []
        
        try:
            import cv2
        except ImportError:
            missing_packages.append("opencv-python")
            
        try:
            import numpy
        except ImportError:
            missing_packages.append("numpy")
            
        try:
            import PyQt5
        except ImportError:
            missing_packages.append("PyQt5")
            
        try:
            import google.generativeai
        except ImportError:
            missing_packages.append("google-generativeai")
            
        try:
            import pymodbus
        except ImportError:
            missing_packages.append("pymodbus")
            
        if missing_packages:
            self.show_dependency_error(missing_packages)
            return False
            
        return True
    
    def show_dependency_error(self, missing_packages):
        """Muestra error de dependencias faltantes"""
        packages_str = '\n'.join([f"  • {pkg}" for pkg in missing_packages])
        
        error_msg = f"""
        ⚠️ DEPENDENCIAS FALTANTES ⚠️

        Los siguientes paquetes Python no están instalados:

        {packages_str}

        Para instalar todas las dependencias, ejecuta:

        pip install opencv-python opencv-contrib-python numpy PyQt5 google-generativeai pymodbus

        O ejecuta el archivo 'install_requirements.py' incluido en el proyecto.
                """
        # Mostrar mensaje de error        
        if self.app:
            QMessageBox.critical(None, "Error de Dependencias", error_msg)
        else:
            print(error_msg)
    
    def check_files(self):
        """Verifica que los archivos necesarios existan"""
        required_files = ['login.py', 'main2.py']
        missing_files = []
        
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            files_str = '\n'.join([f"  • {file}" for file in missing_files])
            error_msg = f"""
            ⚠️ ARCHIVOS FALTANTES ⚠️

            Los siguientes archivos del sistema no se encontraron:

            {files_str}

            Asegúrate de que todos los archivos del proyecto estén en la misma carpeta.
                        """
            
            if self.app:
                QMessageBox.critical(None, "Archivos Faltantes", error_msg)
            else:
                print(error_msg)
            return False
            
        return True
    
    def launch_login_system(self):
        """Inicia el sistema de login con reconocimiento facial"""
        try:
            import login
            
            self.login_window = login.LoginWindow()
            
            # ✅ NUEVO: Configurar launcher externo (reemplaza la modificación directa)
            self.login_window.set_external_launcher(self.launch_main_application)
            
            # ✅ NUEVO: Conectar señal de cierre (más limpio que modificar closeEvent)
            self.login_window.login_closed.connect(self.on_login_closed)
            
            self.login_window.show()
            
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error iniciando sistema de login:\n{str(e)}")
            sys.exit(1)
    
    def launch_main_application(self):
        """Lanza la aplicación principal después de autenticación exitosa"""
        try:
            # Cerrar ventana de login (ya se cierra automáticamente)
            if self.login_window:
                self.login_window.close()
            
            # Importar y crear aplicación principal
            import main2
            
            self.main_window = main2.FactoryIOController()
            self.main_window.show()
            
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error lanzando aplicación principal:\n{str(e)}")
            sys.exit(1)
    
    def on_login_closed(self, event):
        """Maneja el evento de cierre de la ventana de login"""
        # Si se cierra el login sin autenticación, salir de la aplicación
        if not hasattr(self, 'main_window') or not self.main_window:
            self.app.quit()
    
    def run(self):
        """Ejecuta el flujo completo de la aplicación"""
        # Crear aplicación Qt
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Factory I/O Controller System")
        self.app.setOrganizationName("Industrial Automation")
        self.app.setStyle('Fusion')

        # Inicializar variables
        self.main_window = None
        self.login_window = None
        
        # Verificar dependencias
        if not self.check_dependencies():
            sys.exit(1)
        
        # Verificar archivos
        if not self.check_files():
            sys.exit(1)
        
        # Mostrar mensaje de bienvenida
        self.show_welcome_message()
        
        # Iniciar sistema de login
        self.launch_login_system()
        
        # Ejecutar aplicación
        sys.exit(self.app.exec_())
    
    def show_welcome_message(self):
        """Muestra mensaje de bienvenida"""
        welcome_msg = """
        🏭 Factory I/O Controller System v2.0

        Sistema de Control Industrial con Autenticación Facial

        • Sistema de login con reconocimiento facial
        • Control de dispositivos Modbus
        • Interfaz moderna y intuitiva
        • Asistente IA integrado

        Desarrollado por: Grupo 4 SistemasExpertos
                """
        
        QMessageBox.information(None, "Bienvenido", welcome_msg)

def main():
    """Función principal del sistema"""
    launcher = ApplicationLauncher()
    launcher.run()

if __name__ == "__main__":
    main()