"""
SISTEMA DE GESTIÓN DE BACKUPS
==============================
Script para crear, listar, restaurar y gestionar backups de la base de datos.

USO:
  python gestionar_backups.py                    # Menú interactivo
  python gestionar_backups.py --crear            # Crear backup
  python gestionar_backups.py --listar           # Listar backups
  python gestionar_backups.py --restaurar N      # Restaurar backup N
  python gestionar_backups.py --exportar         # Exportar a Excel
  python gestionar_backups.py --limpiar          # Limpiar backups antiguos
"""

import sqlite3
import pandas as pd
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import sys

# Configuración
DB_FILE = "inventario.db"
BACKUP_DIR = Path("backups")
EXPORTS_DIR = Path("exports")

# Crear directorios
BACKUP_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

class GestorBackups:
    def __init__(self):
        self.db_file = DB_FILE
        self.backup_dir = BACKUP_DIR
        self.exports_dir = EXPORTS_DIR
    
    def crear_backup(self, tipo="manual"):
        """Crea un backup de la base de datos"""
        try:
            if not Path(self.db_file).exists():
                print(f"❌ No se encontró la base de datos: {self.db_file}")
                return None
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"inventario_{tipo}_{timestamp}.db"
            backup_path = self.backup_dir / backup_name
            
            # Copiar archivo de base de datos
            shutil.copy2(self.db_file, backup_path)
            
            # Obtener tamaño del archivo
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            
            print(f"✅ Backup creado exitosamente:")
            print(f"   📁 Archivo: {backup_name}")
            print(f"   📊 Tamaño: {size_mb:.2f} MB")
            print(f"   📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            return backup_path
            
        except Exception as e:
            print(f"❌ Error al crear backup: {str(e)}")
            return None
    
    def listar_backups(self, detallado=False):
        """Lista todos los backups disponibles"""
        backups = sorted(self.backup_dir.glob("inventario_*.db"), reverse=True)
        
        if not backups:
            print("📦 No hay backups disponibles")
            return []
        
        print(f"\n📦 BACKUPS DISPONIBLES ({len(backups)}):")
        print("=" * 80)
        
        backups_info = []
        for i, backup in enumerate(backups, 1):
            # Obtener información del archivo
            stat = backup.stat()
            size_mb = stat.st_size / (1024 * 1024)
            fecha_modificacion = datetime.fromtimestamp(stat.st_mtime)
            antiguedad = datetime.now() - fecha_modificacion
            
            # Tipo de backup
            if "manual" in backup.name:
                tipo = "📌 Manual"
            elif "auto" in backup.name:
                tipo = "🤖 Auto"
            else:
                tipo = "❓ Desconocido"
            
            info = {
                'numero': i,
                'nombre': backup.name,
                'path': backup,
                'tipo': tipo,
                'fecha': fecha_modificacion,
                'size': size_mb,
                'antiguedad_dias': antiguedad.days
            }
            backups_info.append(info)
            
            # Mostrar información
            print(f"{i:3}. {tipo} | {backup.name}")
            print(f"     📅 Fecha: {fecha_modificacion.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"     📊 Tamaño: {size_mb:.2f} MB")
            print(f"     ⏰ Antigüedad: {antiguedad.days} días, {antiguedad.seconds // 3600} horas")
            
            if detallado:
                # Mostrar contenido del backup
                try:
                    conn = sqlite3.connect(backup)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM entradas")
                    entradas = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM salidas")
                    salidas = cursor.fetchone()[0]
                    conn.close()
                    print(f"     📦 Contenido: {entradas} entradas, {salidas} salidas")
                except:
                    print(f"     ⚠️  No se pudo leer el contenido")
            
            print("-" * 80)
        
        return backups_info
    
    def restaurar_backup(self, numero_backup):
        """Restaura un backup específico"""
        backups = sorted(self.backup_dir.glob("inventario_*.db"), reverse=True)
        
        if not backups:
            print("❌ No hay backups disponibles para restaurar")
            return False
        
        if numero_backup < 1 or numero_backup > len(backups):
            print(f"❌ Número de backup inválido. Debe ser entre 1 y {len(backups)}")
            return False
        
        backup_seleccionado = backups[numero_backup - 1]
        
        print(f"\n⚠️  ADVERTENCIA: Vas a restaurar el siguiente backup:")
        print(f"   📁 {backup_seleccionado.name}")
        print(f"   📅 {datetime.fromtimestamp(backup_seleccionado.stat().st_mtime).strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"\n   Esto SOBRESCRIBIRÁ la base de datos actual.")
        
        respuesta = input("\n¿Estás seguro? Escribe 'SI' para confirmar: ")
        
        if respuesta.upper() != 'SI':
            print("❌ Restauración cancelada")
            return False
        
        try:
            # Crear backup de seguridad antes de restaurar
            print("\n📦 Creando backup de seguridad de la BD actual...")
            backup_seguridad = self.crear_backup(tipo="pre_restauracion")
            
            if backup_seguridad:
                # Restaurar el backup seleccionado
                print(f"\n🔄 Restaurando backup...")
                shutil.copy2(backup_seleccionado, self.db_file)
                
                print(f"\n✅ Backup restaurado exitosamente")
                print(f"   📁 Base de datos actualizada: {self.db_file}")
                print(f"   💾 Backup de seguridad guardado: {backup_seguridad.name}")
                
                # Mostrar contenido restaurado
                self.mostrar_estadisticas()
                
                return True
            else:
                print("❌ No se pudo crear backup de seguridad. Restauración cancelada.")
                return False
                
        except Exception as e:
            print(f"❌ Error al restaurar backup: {str(e)}")
            return False
    
    def exportar_excel(self):
        """Exporta la base de datos a Excel"""
        try:
            if not Path(self.db_file).exists():
                print(f"❌ No se encontró la base de datos: {self.db_file}")
                return None
            
            print("\n📥 Exportando a Excel...")
            
            conn = sqlite3.connect(self.db_file)
            entradas = pd.read_sql_query("SELECT * FROM entradas", conn)
            salidas = pd.read_sql_query("SELECT * FROM salidas", conn)
            conn.close()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.exports_dir / f"inventario_completo_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Exportar entradas (sin columnas internas)
                columnas_entradas = [
                    'orden_compra', 'fecha', 'codigo', 'producto', 'cantidad', 'um', 
                    'sistema', 'almacen_salida', 'fecha_envio', 'responsable_envio',
                    'almacen_recepcion', 'fecha_recepcion', 'responsable_recepcion'
                ]
                df_entradas = entradas[[col for col in columnas_entradas if col in entradas.columns]]
                df_entradas.to_excel(writer, sheet_name='Entradas', index=False)
                
                # Exportar salidas (sin columnas internas)
                columnas_salidas = [
                    'nro_guia', 'nro_tarea', 'fecha', 'cod_sitio', 'sitio', 
                    'departamento', 'codigo', 'producto', 'code_indra', 'descripcion',
                    'cantidad', 'um', 'sistema'
                ]
                df_salidas = salidas[[col for col in columnas_salidas if col in salidas.columns]]
                df_salidas.to_excel(writer, sheet_name='Salidas', index=False)
            
            size_mb = filename.stat().st_size / (1024 * 1024)
            
            print(f"✅ Excel exportado exitosamente:")
            print(f"   📁 Archivo: {filename.name}")
            print(f"   📊 Tamaño: {size_mb:.2f} MB")
            print(f"   📥 Entradas: {len(entradas)} registros")
            print(f"   📤 Salidas: {len(salidas)} registros")
            
            return filename
            
        except Exception as e:
            print(f"❌ Error al exportar: {str(e)}")
            return None
    
    def limpiar_backups_antiguos(self, dias=30, mantener_minimo=10):
        """Elimina backups más antiguos que X días, manteniendo al menos Y backups"""
        backups = sorted(self.backup_dir.glob("inventario_*.db"), reverse=True)
        
        if not backups:
            print("📦 No hay backups para limpiar")
            return 0
        
        print(f"\n🧹 Limpiando backups antiguos...")
        print(f"   Criterio: Más de {dias} días de antigüedad")
        print(f"   Mantener al menos: {mantener_minimo} backups")
        
        fecha_limite = datetime.now() - timedelta(days=dias)
        eliminados = 0
        
        # Mantener al menos los N backups más recientes
        backups_a_revisar = backups[mantener_minimo:]
        
        for backup in backups_a_revisar:
            fecha_backup = datetime.fromtimestamp(backup.stat().st_mtime)
            
            if fecha_backup < fecha_limite:
                print(f"   🗑️  Eliminando: {backup.name} ({fecha_backup.strftime('%d/%m/%Y')})")
                backup.unlink()
                eliminados += 1
        
        if eliminados > 0:
            print(f"\n✅ Se eliminaron {eliminados} backups antiguos")
            print(f"   Backups restantes: {len(backups) - eliminados}")
        else:
            print(f"\n✅ No hay backups antiguos para eliminar")
        
        return eliminados
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas de la base de datos actual"""
        try:
            if not Path(self.db_file).exists():
                print(f"❌ No se encontró la base de datos: {self.db_file}")
                return
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM entradas")
            total_entradas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM salidas")
            total_salidas = cursor.fetchone()[0]
            
            # Obtener últimos registros
            cursor.execute("SELECT fecha_creacion FROM entradas ORDER BY id DESC LIMIT 1")
            ultima_entrada = cursor.fetchone()
            
            cursor.execute("SELECT fecha_creacion FROM salidas ORDER BY id DESC LIMIT 1")
            ultima_salida = cursor.fetchone()
            
            conn.close()
            
            print("\n" + "=" * 60)
            print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
            print("=" * 60)
            print(f"📁 Archivo: {self.db_file}")
            print(f"📊 Tamaño: {Path(self.db_file).stat().st_size / (1024 * 1024):.2f} MB")
            print(f"\n📥 Entradas: {total_entradas} registros")
            if ultima_entrada:
                print(f"   Última entrada: {ultima_entrada[0]}")
            print(f"\n📤 Salidas: {total_salidas} registros")
            if ultima_salida:
                print(f"   Última salida: {ultima_salida[0]}")
            print(f"\n📦 Total: {total_entradas + total_salidas} registros")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error al mostrar estadísticas: {str(e)}")

def menu_interactivo():
    """Menú interactivo para gestionar backups"""
    gestor = GestorBackups()
    
    while True:
        print("\n" + "=" * 60)
        print("💾 SISTEMA DE GESTIÓN DE BACKUPS")
        print("=" * 60)
        print("\n1. 📊 Ver estadísticas de la base de datos")
        print("2. 💾 Crear backup manual")
        print("3. 📋 Listar backups disponibles")
        print("4. 🔄 Restaurar backup")
        print("5. 📥 Exportar a Excel")
        print("6. 🧹 Limpiar backups antiguos")
        print("0. ❌ Salir")
        
        try:
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == "1":
                gestor.mostrar_estadisticas()
            
            elif opcion == "2":
                gestor.crear_backup("manual")
            
            elif opcion == "3":
                detallado = input("\n¿Mostrar información detallada? (s/n): ").lower() == 's'
                gestor.listar_backups(detallado)
            
            elif opcion == "4":
                backups_info = gestor.listar_backups()
                if backups_info:
                    try:
                        numero = int(input("\nIngresa el número del backup a restaurar: "))
                        gestor.restaurar_backup(numero)
                    except ValueError:
                        print("❌ Número inválido")
            
            elif opcion == "5":
                gestor.exportar_excel()
            
            elif opcion == "6":
                try:
                    dias = int(input("\nEliminar backups más antiguos que (días) [30]: ") or "30")
                    mantener = int(input("Mantener al menos (backups) [10]: ") or "10")
                    gestor.limpiar_backups_antiguos(dias, mantener)
                except ValueError:
                    print("❌ Valores inválidos")
            
            elif opcion == "0":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("❌ Opción inválida")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Operación cancelada")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

def main():
    """Función principal con soporte para argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Sistema de Gestión de Backups')
    parser.add_argument('--crear', action='store_true', help='Crear backup manual')
    parser.add_argument('--listar', action='store_true', help='Listar backups disponibles')
    parser.add_argument('--restaurar', type=int, metavar='N', help='Restaurar backup número N')
    parser.add_argument('--exportar', action='store_true', help='Exportar a Excel')
    parser.add_argument('--limpiar', action='store_true', help='Limpiar backups antiguos')
    parser.add_argument('--estadisticas', action='store_true', help='Mostrar estadísticas')
    parser.add_argument('--detallado', action='store_true', help='Información detallada (con --listar)')
    
    args = parser.parse_args()
    gestor = GestorBackups()
    
    # Si no hay argumentos, mostrar menú interactivo
    if len(sys.argv) == 1:
        menu_interactivo()
        return
    
    # Procesar argumentos
    if args.crear:
        gestor.crear_backup("manual")
    
    if args.listar:
        gestor.listar_backups(args.detallado)
    
    if args.restaurar:
        gestor.restaurar_backup(args.restaurar)
    
    if args.exportar:
        gestor.exportar_excel()
    
    if args.limpiar:
        gestor.limpiar_backups_antiguos()
    
    if args.estadisticas:
        gestor.mostrar_estadisticas()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
