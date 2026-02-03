#!/usr/bin/env python3
"""
SCRIPT DE MIGRACIÓN URGENTE
===========================
Migra del sistema viejo (sin persistencia) al nuevo (con persistencia automática)

USO:
    python migrar_sistema.py
"""

import shutil
import os
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 80)
    print("🚨 MIGRACIÓN URGENTE AL SISTEMA CON PERSISTENCIA AUTOMÁTICA")
    print("=" * 80)
    print()
    
    # Verificar archivos
    app_viejo = Path("app.py")
    app_mejorado = Path("app_mejorado.py")
    
    if not app_viejo.exists():
        print("⚠️  No se encontró app.py - ¿Estás en el directorio correcto?")
        return
    
    if not app_mejorado.exists():
        print("❌ No se encontró app_mejorado.py")
        print("   Copia el archivo app_mejorado.py a este directorio primero")
        return
    
    print("✅ Archivos encontrados")
    print()
    
    # Confirmar migración
    print("⚠️  ADVERTENCIA:")
    print("   Esta migración reemplazará tu app.py actual")
    print("   Se creará un backup en: app_backup_<timestamp>.py")
    print()
    
    respuesta = input("¿Continuar con la migración? (SI/no): ")
    if respuesta.upper() != "SI":
        print("❌ Migración cancelada")
        return
    
    print()
    print("🔄 Iniciando migración...")
    print()
    
    # 1. Crear backup del app.py anterior
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"app_backup_{timestamp}.py"
    
    print(f"1️⃣  Creando backup: {backup_name}")
    shutil.copy2(app_viejo, backup_name)
    print("   ✅ Backup creado")
    print()
    
    # 2. Reemplazar app.py
    print("2️⃣  Reemplazando app.py con la versión mejorada")
    shutil.copy2(app_mejorado, app_viejo)
    print("   ✅ app.py actualizado")
    print()
    
    # 3. Crear carpeta data si no existe
    print("3️⃣  Creando carpeta 'data/' para persistencia")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Crear .gitkeep para que Git trackee la carpeta
    gitkeep = data_dir / ".gitkeep"
    gitkeep.touch(exist_ok=True)
    print("   ✅ Carpeta data/ creada")
    print()
    
    # 4. Crear/actualizar .gitignore
    print("4️⃣  Configurando .gitignore")
    gitignore = Path(".gitignore")
    
    gitignore_content = """
# Base de datos temporal (no persistir en GitHub)
inventario.db
*.db
!data/*.db

# Pero SÍ incluir archivos de data/
!data/*.json
!data/*.xlsx
!data/.gitkeep

# Backups locales temporales
backups/
!backups/.gitkeep

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Logs
*.log

# OS
.DS_Store
Thumbs.db
"""
    
    with open(gitignore, 'w') as f:
        f.write(gitignore_content.strip())
    
    print("   ✅ .gitignore actualizado")
    print()
    
    # 5. Instrucciones de Git
    print("=" * 80)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 80)
    print()
    print("📋 PRÓXIMOS PASOS:")
    print()
    print("1️⃣  Hacer commit de los cambios:")
    print("    git add .")
    print(f"    git commit -m 'Migración urgente: Sistema con persistencia automática'")
    print()
    print("2️⃣  Subir a GitHub:")
    print("    git push origin main")
    print()
    print("3️⃣  Esperar que Streamlit Cloud redeploy (~1-2 minutos)")
    print()
    print("4️⃣  Verificar que funciona:")
    print("    - Abre la app en Streamlit Cloud")
    print("    - Agrega un dato de prueba")
    print("    - Ve a GitHub → carpeta data/")
    print("    - Verifica que aparecen archivos .json")
    print()
    print("5️⃣  Informar a todos los usuarios:")
    print("    - Nuevo protocolo de exportación diaria")
    print("    - Sistema ahora guarda automáticamente")
    print()
    print("=" * 80)
    print("📁 ARCHIVOS CREADOS/MODIFICADOS:")
    print(f"   - app.py (actualizado)")
    print(f"   - {backup_name} (backup del anterior)")
    print(f"   - data/ (nueva carpeta)")
    print(f"   - data/.gitkeep")
    print(f"   - .gitignore (actualizado)")
    print("=" * 80)
    print()
    print("⚠️  IMPORTANTE:")
    print("   - El backup del sistema viejo está en: " + backup_name)
    print("   - NO lo elimines hasta confirmar que todo funciona")
    print("   - Lee RECUPERACION_EMERGENCIA.md para más detalles")
    print()
    print("🎉 ¡Listo para deploy!")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migración cancelada por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante la migración: {str(e)}")
        print("   Por favor, revisa y vuelve a intentar")
