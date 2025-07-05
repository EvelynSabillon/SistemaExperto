#!/usr/bin/env python3
"""
Instalador Automático de Dependencias
Factory I/O Controller System

Este script instala automáticamente todas las dependencias necesarias
para el sistema de control Factory I/O con autenticación facial.
"""

import subprocess
import sys
import os

# Lista de dependencias requeridas
REQUIRED_PACKAGES = [
    "opencv-python>=4.5.0",
    "opencv-contrib-python>=4.5.0", 
    "numpy>=1.19.0",
    "PyQt5>=5.15.0",
    "google-generativeai>=0.3.0",
    "pymodbus>=3.0.0",
    "pickle-mixin",
    "face_recognition>=1.3.0",
]

def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    if sys.version_info < (3, 7):
        print("❌ Error: Se requiere Python 3.7 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Compatible")
        return True

def check_pip():
    """Verifica que pip esté disponible"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip está disponible")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error: pip no está disponible")
        return False

def install_package(package):
    """Instala un paquete específico"""
    try:
        print(f"📦 Instalando {package}...")
        
        # Comando de instalación
        cmd = [sys.executable, "-m", "pip", "install", package, "--upgrade"]
        
        # Ejecutar instalación
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print(f"✅ {package} instalado correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando {package}:")
        print(f"   {e.stderr}")
        return False

def check_installation():
    """Verifica que todas las dependencias estén instaladas correctamente"""
    print("\n🔍 Verificando instalación...")
    
    failed_imports = []
    
    # Verificar cada dependencia
    dependencies = {
        "cv2": "OpenCV",
        "numpy": "NumPy", 
        "PyQt5": "PyQt5",
        "google.generativeai": "Google Generative AI",
        "pymodbus": "PyModbus"
    }
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name} - OK")
        except ImportError:
            print(f"❌ {name} - FALLO")
            failed_imports.append(name)
    
    return len(failed_imports) == 0

def create_requirements_txt():
    """Crea un archivo requirements.txt para referencia futura"""
    try:
        with open("requirements.txt", "w") as f:
            f.write("# Factory I/O Controller System - Dependencias\n")
            f.write("# Generado automáticamente\n\n")
            for package in REQUIRED_PACKAGES:
                f.write(f"{package}\n")
        
        print("📝 Archivo requirements.txt creado")
        return True
        
    except Exception as e:
        print(f"⚠️ Error creando requirements.txt: {e}")
        return False

def show_post_install_info():
    """Muestra información post-instalación"""
    info = """
🎉 INSTALACIÓN COMPLETADA 🎉

Todas las dependencias han sido instaladas correctamente.

Para ejecutar el sistema:
  python main.py

Archivos del sistema:
  • main.py         - Lanzador principal
  • login.py        - Sistema de autenticación facial
  • main2.py        - Aplicación principal
  • requirements.txt - Lista de dependencias

Comandos útiles:
  • python main.py           - Ejecutar sistema completo
  • python login.py          - Solo sistema de login
  • python main2.py          - Solo aplicación principal (sin auth)

Si encuentras problemas:
  1. Verifica que la cámara esté conectada
  2. Asegúrate de tener permisos de cámara
  3. Revisa que Factory I/O esté ejecutándose (para Modbus)

¡Disfruta del sistema Factory I/O Controller! 🏭
    """
    print(info)

def main():
    """Función principal del instalador"""
    print("🚀 INSTALADOR DE DEPENDENCIAS")
    print("Factory I/O Controller System v2.0")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        input("Presiona Enter para salir...")
        sys.exit(1)
    
    # Verificar pip
    if not check_pip():
        print("\n💡 Solución:")
        print("   Instala pip ejecutando: python -m ensurepip --upgrade")
        input("Presiona Enter para salir...")
        sys.exit(1)
    
    print(f"\n📋 Instalando {len(REQUIRED_PACKAGES)} dependencias...")
    print("-" * 50)
    
    # Instalar cada paquete
    failed_packages = []
    for package in REQUIRED_PACKAGES:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n" + "=" * 50)
    
    # Verificar instalación
    if check_installation():
        print("\n🎉 ¡Todas las dependencias instaladas correctamente!")
        
        # Crear requirements.txt
        create_requirements_txt()
        
        # Mostrar información post-instalación
        show_post_install_info()
        
    else:
        print(f"\n❌ Algunas dependencias fallaron:")
        for package in failed_packages:
            print(f"   • {package}")
        
        print("\n💡 Soluciones:")
        print("   1. Ejecuta: pip install --upgrade pip")
        print("   2. Reinstala Python desde python.org")
        print("   3. Usa un entorno virtual: python -m venv venv")
        
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()