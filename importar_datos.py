"""
SCRIPT DE IMPORTACIÓN DE DATOS A SQLite
========================================
Este script importa tus datos existentes de Excel a la base de datos SQLite.

INSTRUCCIONES DE USO:
1. Asegúrate de tener tus archivos Excel actuales en la carpeta 'data/'
2. Ejecuta: python importar_datos.py
3. Verifica que los datos se importaron correctamente

IMPORTANTE: Guarda un backup de tus archivos Excel antes de ejecutar este script.
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil

# Configuración
DB_FILE = "inventario.db"
DATA_DIR = Path("data")
BACKUP_DIR = Path("backups_importacion")
ENTRADAS_FILE = DATA_DIR / "entradas.xlsx"
SALIDAS_FILE = DATA_DIR / "salidas.xlsx"

def crear_backup_excel():
    """Crea un backup de los archivos Excel antes de importar"""
    print("\n📦 Creando backup de seguridad de archivos Excel...")
    
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = BACKUP_DIR / f"backup_antes_importacion_{timestamp}"
    backup_folder.mkdir(exist_ok=True)
    
    archivos_respaldados = []
    
    if ENTRADAS_FILE.exists():
        destino = backup_folder / "entradas.xlsx"
        shutil.copy2(ENTRADAS_FILE, destino)
        archivos_respaldados.append("entradas.xlsx")
        print(f"  ✅ Respaldado: entradas.xlsx")
    
    if SALIDAS_FILE.exists():
        destino = backup_folder / "salidas.xlsx"
        shutil.copy2(SALIDAS_FILE, destino)
        archivos_respaldados.append("salidas.xlsx")
        print(f"  ✅ Respaldado: salidas.xlsx")
    
    if archivos_respaldados:
        print(f"\n✅ Backup creado en: {backup_folder}")
        print(f"   Archivos respaldados: {len(archivos_respaldados)}")
        return backup_folder
    else:
        print("⚠️  No se encontraron archivos Excel para respaldar")
        return None

def inicializar_base_datos():
    """Inicializa la base de datos SQLite con las tablas necesarias"""
    print("\n🔧 Inicializando base de datos SQLite...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tabla de ENTRADAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_compra TEXT,
            fecha TEXT,
            codigo TEXT,
            producto TEXT,
            cantidad REAL,
            um TEXT,
            sistema TEXT,
            almacen_salida TEXT,
            fecha_envio TEXT,
            responsable_envio TEXT,
            almacen_recepcion TEXT,
            fecha_recepcion TEXT,
            responsable_recepcion TEXT,
            creado_por TEXT,
            fecha_creacion TEXT
        )
    ''')
    
    # Tabla de SALIDAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nro_guia TEXT,
            nro_tarea TEXT,
            fecha TEXT,
            cod_sitio TEXT,
            sitio TEXT,
            departamento TEXT,
            codigo TEXT,
            producto TEXT,
            code_indra TEXT,
            descripcion TEXT,
            cantidad REAL,
            um TEXT,
            sistema TEXT,
            creado_por TEXT,
            fecha_creacion TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Base de datos inicializada correctamente")

def importar_entradas():
    """Importa entradas desde Excel a SQLite"""
    print("\n📥 Importando ENTRADAS...")
    
    if not ENTRADAS_FILE.exists():
        print(f"⚠️  No se encontró el archivo: {ENTRADAS_FILE}")
        print("   Creando tabla vacía...")
        return 0
    
    try:
        # Leer Excel
        df = pd.read_excel(ENTRADAS_FILE)
        print(f"  📊 Registros encontrados en Excel: {len(df)}")
        
        # Mapear columnas (ajustar según tu estructura)
        columnas_requeridas = [
            'orden_compra', 'fecha', 'codigo', 'producto', 'cantidad', 'um', 
            'sistema', 'almacen_salida', 'fecha_envio', 'responsable_envio',
            'almacen_recepcion', 'fecha_recepcion', 'responsable_recepcion'
        ]
        
        # Asegurar que todas las columnas existan
        for col in columnas_requeridas:
            if col not in df.columns:
                df[col] = ''
        
        # Agregar metadatos si no existen
        if 'creado_por' not in df.columns:
            df['creado_por'] = 'Importado'
        if 'fecha_creacion' not in df.columns:
            df['fecha_creacion'] = datetime.now().strftime('%d/%m/%Y %I:%M %p')
        
        # Remover la columna 'id' si existe (se autogenerará)
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
        
        # Importar a SQLite
        conn = sqlite3.connect(DB_FILE)
        
        # Verificar si ya hay datos
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM entradas")
        count_existente = cursor.fetchone()[0]
        
        if count_existente > 0:
            print(f"  ⚠️  La tabla ya tiene {count_existente} registros")
            respuesta = input("  ¿Deseas agregar los nuevos registros? (s/n): ")
            if respuesta.lower() != 's':
                conn.close()
                print("  ❌ Importación de entradas cancelada")
                return 0
        
        # Importar datos
        registros_antes = count_existente
        df.to_sql('entradas', conn, if_exists='append', index=False)
        
        # Verificar importación
        cursor.execute("SELECT COUNT(*) FROM entradas")
        registros_despues = cursor.fetchone()[0]
        
        conn.close()
        
        registros_importados = registros_despues - registros_antes
        print(f"  ✅ Entradas importadas: {registros_importados}")
        return registros_importados
        
    except Exception as e:
        print(f"  ❌ Error al importar entradas: {str(e)}")
        return 0

def importar_salidas():
    """Importa salidas desde Excel a SQLite"""
    print("\n📤 Importando SALIDAS...")
    
    if not SALIDAS_FILE.exists():
        print(f"⚠️  No se encontró el archivo: {SALIDAS_FILE}")
        print("   Creando tabla vacía...")
        return 0
    
    try:
        # Leer Excel
        df = pd.read_excel(SALIDAS_FILE)
        print(f"  📊 Registros encontrados en Excel: {len(df)}")
        
        # Mapear columnas
        columnas_requeridas = [
            'nro_guia', 'nro_tarea', 'fecha', 'cod_sitio', 'sitio', 
            'departamento', 'codigo', 'producto', 'code_indra', 'descripcion',
            'cantidad', 'um', 'sistema'
        ]
        
        # Asegurar que todas las columnas existan
        for col in columnas_requeridas:
            if col not in df.columns:
                df[col] = ''
        
        # Agregar metadatos
        if 'creado_por' not in df.columns:
            df['creado_por'] = 'Importado'
        if 'fecha_creacion' not in df.columns:
            df['fecha_creacion'] = datetime.now().strftime('%d/%m/%Y %I:%M %p')
        
        # Remover la columna 'id' si existe
        if 'id' in df.columns:
            df = df.drop('id', axis=1)
        
        # Importar a SQLite
        conn = sqlite3.connect(DB_FILE)
        
        # Verificar si ya hay datos
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM salidas")
        count_existente = cursor.fetchone()[0]
        
        if count_existente > 0:
            print(f"  ⚠️  La tabla ya tiene {count_existente} registros")
            respuesta = input("  ¿Deseas agregar los nuevos registros? (s/n): ")
            if respuesta.lower() != 's':
                conn.close()
                print("  ❌ Importación de salidas cancelada")
                return 0
        
        # Importar datos
        registros_antes = count_existente
        df.to_sql('salidas', conn, if_exists='append', index=False)
        
        # Verificar importación
        cursor.execute("SELECT COUNT(*) FROM salidas")
        registros_despues = cursor.fetchone()[0]
        
        conn.close()
        
        registros_importados = registros_despues - registros_antes
        print(f"  ✅ Salidas importadas: {registros_importados}")
        return registros_importados
        
    except Exception as e:
        print(f"  ❌ Error al importar salidas: {str(e)}")
        return 0

def verificar_importacion():
    """Verifica que los datos se importaron correctamente"""
    print("\n🔍 Verificando importación...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Contar entradas
        cursor.execute("SELECT COUNT(*) FROM entradas")
        total_entradas = cursor.fetchone()[0]
        
        # Contar salidas
        cursor.execute("SELECT COUNT(*) FROM salidas")
        total_salidas = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 RESUMEN DE IMPORTACIÓN:")
        print(f"  📥 Entradas en BD: {total_entradas}")
        print(f"  📤 Salidas en BD: {total_salidas}")
        print(f"  📦 Total registros: {total_entradas + total_salidas}")
        
        return total_entradas, total_salidas
        
    except Exception as e:
        print(f"  ❌ Error al verificar: {str(e)}")
        return 0, 0

def mostrar_ejemplos():
    """Muestra algunos ejemplos de los datos importados"""
    print("\n📋 Ejemplos de datos importados:")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        
        print("\n  📥 ÚLTIMAS 3 ENTRADAS:")
        entradas = pd.read_sql_query("SELECT orden_compra, fecha, producto, cantidad, um FROM entradas ORDER BY id DESC LIMIT 3", conn)
        if not entradas.empty:
            for idx, row in entradas.iterrows():
                print(f"    • OC: {row['orden_compra']} | {row['producto']} | {row['cantidad']} {row['um']}")
        else:
            print("    (Sin registros)")
        
        print("\n  📤 ÚLTIMAS 3 SALIDAS:")
        salidas = pd.read_sql_query("SELECT nro_guia, fecha, producto, cantidad, sitio FROM salidas ORDER BY id DESC LIMIT 3", conn)
        if not salidas.empty:
            for idx, row in salidas.iterrows():
                print(f"    • Guía: {row['nro_guia']} | {row['producto']} | {row['cantidad']} | {row['sitio']}")
        else:
            print("    (Sin registros)")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Error al mostrar ejemplos: {str(e)}")

def main():
    """Función principal de importación"""
    print("=" * 70)
    print("  SCRIPT DE IMPORTACIÓN DE DATOS A SQLite")
    print("  Sistema de Gestión de Consumibles y Stock")
    print("=" * 70)
    
    # Crear backup de seguridad
    backup_folder = crear_backup_excel()
    
    # Inicializar base de datos
    inicializar_base_datos()
    
    # Importar datos
    entradas_importadas = importar_entradas()
    salidas_importadas = importar_salidas()
    
    # Verificar
    total_entradas, total_salidas = verificar_importacion()
    
    # Mostrar ejemplos
    if total_entradas > 0 or total_salidas > 0:
        mostrar_ejemplos()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("=" * 70)
    print(f"\n📁 Base de datos creada: {DB_FILE}")
    print(f"📊 Total de registros importados: {entradas_importadas + salidas_importadas}")
    
    if backup_folder:
        print(f"\n💾 Backup de seguridad guardado en:")
        print(f"   {backup_folder}")
    
    print("\n📌 PRÓXIMOS PASOS:")
    print("   1. Verifica que los datos se importaron correctamente")
    print("   2. Ejecuta tu aplicación: streamlit run app.py")
    print("   3. Si todo funciona bien, puedes eliminar los archivos Excel antiguos")
    print("\n⚠️  IMPORTANTE: Guarda el backup antes de eliminar los archivos Excel")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Importación cancelada por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error general: {str(e)}")
        print("   Por favor, revisa los archivos y vuelve a intentar")
