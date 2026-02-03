import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import shutil
import base64
import requests
import json
import os

# ==================== CONFIGURACIÓN Y PERSISTENCIA ====================
# Configuración de directorios
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Archivos de persistencia
ENTRADAS_PERSIST = DATA_DIR / "entradas_persist.json"
SALIDAS_PERSIST = DATA_DIR / "salidas_persist.json"

# Funciones de persistencia
def guardar_a_json(df, archivo):
    """Guarda DataFrame a JSON para persistencia en GitHub"""
    try:
        data = df.to_dict('records')
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error al guardar JSON: {e}")
        return False

def cargar_desde_json(archivo):
    """Carga DataFrame desde JSON"""
    try:
        if Path(archivo).exists():
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data:
                return pd.DataFrame(data)
    except Exception as e:
        print(f"Error al cargar JSON: {e}")
    return pd.DataFrame()

def auto_backup_excel():
    """Crea backup automático en Excel"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = DATA_DIR / f"backup_auto_{timestamp}.xlsx"
        
        entradas = cargar_entradas_db()
        salidas = cargar_salidas_db()
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            entradas.to_excel(writer, sheet_name='Entradas', index=False)
            salidas.to_excel(writer, sheet_name='Salidas', index=False)
        
        # Mantener solo los últimos 5 backups
        backups = sorted(DATA_DIR.glob("backup_auto_*.xlsx"))
        if len(backups) > 5:
            for old_backup in backups[:-5]:
                old_backup.unlink()
        
        return True
    except Exception as e:
        print(f"Error en auto-backup: {e}")
        return False

def sincronizar_datos():
    """Sincroniza datos entre SQLite, JSON local y GitHub"""
    try:
        # Guardar localmente
        entradas = cargar_entradas_db()
        salidas = cargar_salidas_db()
        
        guardar_a_json(entradas, ENTRADAS_PERSIST)
        guardar_a_json(salidas, SALIDAS_PERSIST)
        
        # Sincronizar con GitHub
        sincronizar_github()
        
        return True
    except Exception as e:
        print(f"Error en sincronización: {e}")
        return False

# ==================== CONFIGURACIÓN DE BASE DE DATOS SQLite ====================
DB_FILE = "inventario.db"
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

def init_database():
    """Inicializa la base de datos SQLite con las tablas necesarias"""
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
    
    # RESTAURACIÓN AUTOMÁTICA desde JSON
    try:
        cursor.execute("SELECT COUNT(*) FROM entradas")
        count_entradas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM salidas")
        count_salidas = cursor.fetchone()[0]
        
        if count_entradas == 0 and ENTRADAS_PERSIST.exists():
            df_entradas = cargar_desde_json(ENTRADAS_PERSIST)
            if not df_entradas.empty:
                df_entradas.to_sql('entradas', conn, if_exists='replace', index=False)
                print(f"✅ Restauradas {len(df_entradas)} entradas desde JSON")
        
        if count_salidas == 0 and SALIDAS_PERSIST.exists():
            df_salidas = cargar_desde_json(SALIDAS_PERSIST)
            if not df_salidas.empty:
                df_salidas.to_sql('salidas', conn, if_exists='replace', index=False)
                print(f"✅ Restauradas {len(df_salidas)} salidas desde JSON")
    except Exception as e:
        print(f"Error en restauración: {e}")
    finally:
        conn.close()

def cargar_entradas_db():
    """Carga entradas desde la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM entradas ORDER BY id DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error al cargar entradas: {e}")
        return pd.DataFrame()

def cargar_salidas_db():
    """Carga salidas desde la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM salidas ORDER BY id DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error al cargar salidas: {e}")
        return pd.DataFrame()

def guardar_entrada_db(datos):
    """Guarda una entrada en la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO entradas (
                orden_compra, fecha, codigo, producto, cantidad, um, sistema,
                almacen_salida, fecha_envio, responsable_envio,
                almacen_recepcion, fecha_recepcion, responsable_recepcion,
                creado_por, fecha_creacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datos.get('orden_compra', ''),
            datos.get('fecha', ''),
            datos.get('codigo', ''),
            datos.get('producto', ''),
            datos.get('cantidad', 0),
            datos.get('um', ''),
            datos.get('sistema', ''),
            datos.get('almacen_salida', ''),
            datos.get('fecha_envio', ''),
            datos.get('responsable_envio', ''),
            datos.get('almacen_recepcion', ''),
            datos.get('fecha_recepcion', ''),
            datos.get('responsable_recepcion', ''),
            datos.get('creado_por', 'Usuario'),
            obtener_hora_peru()
        ))
        
        conn.commit()
        conn.close()
        
        # Backup automático
        backup_automatico()
        
        # SINCRONIZAR CON GITHUB
        sincronizar_datos()
        return True
    except Exception as e:
        st.error(f"Error al guardar entrada: {e}")
        return False

def guardar_salida_db(datos):
    """Guarda una salida en la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO salidas (
                nro_guia, nro_tarea, fecha, cod_sitio, sitio, departamento,
                codigo, producto, code_indra, descripcion, cantidad, um, sistema,
                creado_por, fecha_creacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datos.get('nro_guia', ''),
            datos.get('nro_tarea', ''),
            datos.get('fecha', ''),
            datos.get('cod_sitio', ''),
            datos.get('sitio', ''),
            datos.get('departamento', ''),
            datos.get('codigo', ''),
            datos.get('producto', ''),
            datos.get('code_indra', ''),
            datos.get('descripcion', ''),
            datos.get('cantidad', 0),
            datos.get('um', ''),
            datos.get('sistema', ''),
            datos.get('creado_por', 'Usuario'),
            obtener_hora_peru()
        ))
        
        conn.commit()
        conn.close()
        
        # Backup automático
        backup_automatico()
        
        # SINCRONIZAR CON GITHUB
        sincronizar_datos()
        return True
    except Exception as e:
        st.error(f"Error al guardar salida: {e}")
        return False

def eliminar_entrada_db(entrada_id):
    """Elimina una entrada de la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entradas WHERE id = ?", (entrada_id,))
        conn.commit()
        conn.close()
        backup_automatico()
        
        # SINCRONIZAR CON GITHUB
        sincronizar_datos()
        return True
    except Exception as e:
        st.error(f"Error al eliminar entrada: {e}")
        return False

def eliminar_salida_db(salida_id):
    """Elimina una salida de la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM salidas WHERE id = ?", (salida_id,))
        conn.commit()
        conn.close()
        backup_automatico()
        
        # SINCRONIZAR CON GITHUB
        sincronizar_datos()
        return True
    except Exception as e:
        st.error(f"Error al eliminar salida: {e}")
        return False

def backup_automatico():
    """Crea backup automático del archivo de base de datos"""
    try:
        # Solo crear backup cada hora para no saturar
        ultimo_backup = st.session_state.get('ultimo_backup_timestamp', 0)
        ahora = datetime.now().timestamp()
        
        # Si pasó más de 1 hora desde el último backup
        if ahora - ultimo_backup > 3600:  # 3600 segundos = 1 hora
            fecha = datetime.now().strftime('%Y%m%d_%H%M')
            backup_file = BACKUP_DIR / f"inventario_auto_{fecha}.db"
            shutil.copy2(DB_FILE, backup_file)
            st.session_state.ultimo_backup_timestamp = ahora
            
            # Limpiar backups antiguos (mantener últimos 50)
            backups = sorted(BACKUP_DIR.glob("inventario_auto_*.db"))
            if len(backups) > 50:
                for old_backup in backups[:-50]:
                    old_backup.unlink()
    except Exception as e:
        pass  # Silencioso para no molestar al usuario

def backup_manual():
    """Crea backup manual"""
    try:
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = BACKUP_DIR / f"inventario_manual_{fecha}.db"
        shutil.copy2(DB_FILE, backup_file)
        return backup_file
    except Exception as e:
        st.error(f"Error al crear backup: {e}")
        return None

def exportar_excel_completo():
    """Exporta entradas y salidas en un solo Excel con 2 hojas"""
    try:
        conn = sqlite3.connect(DB_FILE)
        entradas = pd.read_sql_query("SELECT * FROM entradas", conn)
        salidas = pd.read_sql_query("SELECT * FROM salidas", conn)
        conn.close()
        
        EXPORTS_DIR = Path("exports")
        EXPORTS_DIR.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = EXPORTS_DIR / f"inventario_completo_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Hoja de Entradas
            columnas_entradas = [
                'orden_compra', 'fecha', 'codigo', 'producto', 'cantidad', 'um', 
                'sistema', 'almacen_salida', 'fecha_envio', 'responsable_envio',
                'almacen_recepcion', 'fecha_recepcion', 'responsable_recepcion'
            ]
            df_entradas = entradas[[col for col in columnas_entradas if col in entradas.columns]]
            df_entradas.to_excel(writer, sheet_name='Entradas', index=False)
            
            # Hoja de Salidas
            columnas_salidas = [
                'nro_guia', 'nro_tarea', 'fecha', 'cod_sitio', 'sitio', 
                'departamento', 'codigo', 'producto', 'code_indra', 'descripcion',
                'cantidad', 'um', 'sistema'
            ]
            df_salidas = salidas[[col for col in columnas_salidas if col in salidas.columns]]
            df_salidas.to_excel(writer, sheet_name='Salidas', index=False)
        
        return filename
    except Exception as e:
        st.error(f"Error al exportar: {e}")
        return None

# ==================== FUNCIONES ORIGINALES ====================

def obtener_hora_peru():
    """Obtiene la hora actual de Perú (UTC-5)"""
    utc_now = datetime.utcnow()
    peru_time = utc_now - timedelta(hours=5)
    return peru_time.strftime('%d/%m/%Y %I:%M %p')

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Consumibles y Stock",
    page_icon="📦",
    layout="wide"
)

# Inicializar base de datos
init_database()

# Rutas de archivos
DATA_DIR = Path("data")
EXPORTS_DIR = Path("exports")
SITES_FILE = DATA_DIR / "SITES.xlsx"
STOCK_FILE = DATA_DIR / "Stock.xlsx"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Cargar datos desde DB
if 'entradas' not in st.session_state:
    st.session_state.entradas = cargar_entradas_db()

if 'salidas' not in st.session_state:
    st.session_state.salidas = cargar_salidas_db()

# Cargar datos de SITES
if 'sites_data' not in st.session_state:
    if SITES_FILE.exists():
        try:
            st.session_state.sites_data = pd.read_excel(SITES_FILE, sheet_name='Site POP')
        except ValueError:
            st.session_state.sites_data = pd.read_excel(SITES_FILE, sheet_name=0)
            st.warning("⚠️ No se encontró la hoja 'Site POP'. Se cargó la primera hoja.")
    else:
        st.session_state.sites_data = pd.DataFrame()
        st.error("❌ No se encontró el archivo SITES.xlsx en la carpeta data/")

# Cargar datos de STOCK
if 'stock_data' not in st.session_state:
    if STOCK_FILE.exists():
        st.session_state.stock_data = pd.read_excel(STOCK_FILE)
    else:
        st.session_state.stock_data = pd.DataFrame()
        st.error("❌ No se encontró el archivo Stock.xlsx en la carpeta data/")

def obtener_datos_producto(codigo_o_producto):
    """Obtiene datos del producto desde Stock.xlsx"""
    if st.session_state.stock_data.empty:
        return {}
    
    try:
        producto = st.session_state.stock_data[
            (st.session_state.stock_data['Codigo'].astype(str).str.upper() == str(codigo_o_producto).upper()) |
            (st.session_state.stock_data['Producto'].astype(str).str.upper() == str(codigo_o_producto).upper())
        ]
        
        if not producto.empty:
            producto = producto.iloc[0]
            return {
                'codigo': str(producto.get('Codigo', '')),
                'producto': str(producto.get('Producto', '')),
                'um': str(producto.get('UM', '')),
                'sistema': str(producto.get('SISTEMA', '')),
                'stock_inicial': float(producto.get('Stock inicial', 0))
            }
    except Exception as e:
        st.error(f"❌ Error al buscar producto: {str(e)}")
    
    return {}

def obtener_datos_site(nombre_site):
    """Obtiene datos del site desde SITES.xlsx"""
    if st.session_state.sites_data.empty:
        return {}
    
    try:
        site = st.session_state.sites_data[
            (st.session_state.sites_data['Código'].astype(str).str.upper() == nombre_site.upper()) |
            (st.session_state.sites_data['Nombre'].astype(str).str.upper() == nombre_site.upper())
        ]
        
        if not site.empty:
            site = site.iloc[0]
            return {
                'cod_sitio': str(site.get('Código', '')),
                'sitio': str(site.get('Nombre', '')),
                'departamento': str(site.get('Departamento', ''))
            }
    except Exception as e:
        st.error(f"❌ Error al buscar site: {str(e)}")
    
    return {}

def calcular_stock_actual():
    """Calcula el stock actual de todos los productos"""
    if st.session_state.stock_data.empty:
        return pd.DataFrame()
    
    stock_df = st.session_state.stock_data.copy()
    
    # Calcular total de entradas por producto
    if not st.session_state.entradas.empty:
        entradas_sum = st.session_state.entradas.groupby('codigo')['cantidad'].sum().reset_index()
        entradas_sum.columns = ['Codigo', 'total_entradas']
        stock_df = stock_df.merge(entradas_sum, on='Codigo', how='left')
        stock_df['total_entradas'] = stock_df['total_entradas'].fillna(0)
    else:
        stock_df['total_entradas'] = 0
    
    # Calcular total de salidas por producto
    if not st.session_state.salidas.empty:
        salidas_sum = st.session_state.salidas.groupby('codigo')['cantidad'].sum().reset_index()
        salidas_sum.columns = ['Codigo', 'total_salidas']
        stock_df = stock_df.merge(salidas_sum, on='Codigo', how='left')
        stock_df['total_salidas'] = stock_df['total_salidas'].fillna(0)
    else:
        stock_df['total_salidas'] = 0
    
    # Calcular stock actual
    stock_df['stock_actual'] = stock_df['Stock inicial'] + stock_df['total_entradas'] - stock_df['total_salidas']
    stock_df['variacion_stock'] = stock_df['stock_actual'] - stock_df['Stock inicial']
    stock_df['variacion_porcentaje'] = (stock_df['variacion_stock'] / stock_df['Stock inicial'] * 100).round(2)
    
    # Rotación de inventario (salidas / stock promedio)
    stock_df['stock_promedio'] = (stock_df['Stock inicial'] + stock_df['stock_actual']) / 2
    stock_df['rotacion_inventario'] = (stock_df['total_salidas'] / stock_df['stock_promedio']).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)
    
    return stock_df

def crear_entrada(datos):
    """Crea un nuevo registro de entrada"""
    if guardar_entrada_db(datos):
        st.session_state.entradas = cargar_entradas_db()
        return True
    return False

def crear_salida(datos):
    """Crea un nuevo registro de salida"""
    if guardar_salida_db(datos):
        st.session_state.salidas = cargar_salidas_db()
        return True
    return False

def eliminar_entrada(entrada_id):
    """Elimina un registro de entrada"""
    if eliminar_entrada_db(entrada_id):
        st.session_state.entradas = cargar_entradas_db()

def eliminar_salida(salida_id):
    """Elimina un registro de salida"""
    if eliminar_salida_db(salida_id):
        st.session_state.salidas = cargar_salidas_db()

def mostrar_dashboard():
    """Muestra el dashboard con gráficos y análisis"""
    st.header("📊 Dashboard de Análisis de Stock")
    
    stock_actual_df = calcular_stock_actual()
    
    if stock_actual_df.empty:
        st.info("No hay datos de stock para mostrar.")
        return
    
    # Selector de producto individual
    st.subheader("🔍 Análisis por Producto Individual")
    productos_lista = stock_actual_df['Producto'].tolist()
    producto_seleccionado = st.selectbox("Selecciona un producto:", productos_lista)
    
    if producto_seleccionado:
        prod_data = stock_actual_df[stock_actual_df['Producto'] == producto_seleccionado].iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Stock Inicial", f"{prod_data['Stock inicial']:.2f} {prod_data['UM']}")
        with col2:
            st.metric("Total Entradas", f"{prod_data['total_entradas']:.2f} {prod_data['UM']}")
        with col3:
            st.metric("Total Salidas", f"{prod_data['total_salidas']:.2f} {prod_data['UM']}")
        with col4:
            st.metric("Stock Actual", f"{prod_data['stock_actual']:.2f} {prod_data['UM']}", 
                     delta=f"{prod_data['variacion_porcentaje']:.2f}%")
        
        # Gráfico de evolución del producto seleccionado
        fig_prod = go.Figure()
        fig_prod.add_trace(go.Bar(
            name='Stock Inicial',
            x=['Stock'],
            y=[prod_data['Stock inicial']],
            marker_color='lightblue'
        ))
        fig_prod.add_trace(go.Bar(
            name='Entradas',
            x=['Stock'],
            y=[prod_data['total_entradas']],
            marker_color='green'
        ))
        fig_prod.add_trace(go.Bar(
            name='Salidas',
            x=['Stock'],
            y=[prod_data['total_salidas']],
            marker_color='red'
        ))
        fig_prod.add_trace(go.Bar(
            name='Stock Actual',
            x=['Stock'],
            y=[prod_data['stock_actual']],
            marker_color='darkblue'
        ))
        fig_prod.update_layout(
            title=f"Evolución de {producto_seleccionado}",
            barmode='group',
            yaxis_title=f"Cantidad ({prod_data['UM']})"
        )
        st.plotly_chart(fig_prod, use_container_width=True)
    
    st.markdown("---")
    
    # Gráficos generales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 TOP 10 Productos con Más Stock")
        top_stock = stock_actual_df.nlargest(10, 'stock_actual')
        fig1 = px.bar(
            top_stock,
            x='stock_actual',
            y='Producto',
            orientation='h',
            title="TOP 10 Stock Actual",
            labels={'stock_actual': 'Cantidad', 'Producto': 'Producto'},
            color='stock_actual',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("📉 TOP 10 Productos con Más Salidas")
        top_salidas = stock_actual_df.nlargest(10, 'total_salidas')
        fig2 = px.bar(
            top_salidas,
            x='total_salidas',
            y='Producto',
            orientation='h',
            title="TOP 10 Salidas",
            labels={'total_salidas': 'Cantidad', 'Producto': 'Producto'},
            color='total_salidas',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("⚠️ Stock Crítico (Menor a 100)")
        stock_critico = stock_actual_df[stock_actual_df['stock_actual'] < 100].nsmallest(10, 'stock_actual')
        if not stock_critico.empty:
            fig3 = px.bar(
                stock_critico,
                x='stock_actual',
                y='Producto',
                orientation='h',
                title="Productos con Stock Crítico",
                labels={'stock_actual': 'Cantidad', 'Producto': 'Producto'},
                color='stock_actual',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.success("✅ No hay productos con stock crítico")
    
    with col4:
        st.subheader("🔄 TOP 10 Rotación de Inventario")
        top_rotacion = stock_actual_df.nlargest(10, 'rotacion_inventario')
        fig4 = px.bar(
            top_rotacion,
            x='rotacion_inventario',
            y='Producto',
            orientation='h',
            title="Mayor Rotación",
            labels={'rotacion_inventario': 'Índice de Rotación', 'Producto': 'Producto'},
            color='rotacion_inventario',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    # Stock Inicial vs Stock Actual
    st.subheader("📊 Stock Inicial vs Stock Actual por Producto")
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(
        name='Stock Inicial',
        x=stock_actual_df['Producto'].head(15),
        y=stock_actual_df['Stock inicial'].head(15),
        marker_color='lightblue'
    ))
    fig5.add_trace(go.Bar(
        name='Stock Actual',
        x=stock_actual_df['Producto'].head(15),
        y=stock_actual_df['stock_actual'].head(15),
        marker_color='darkblue'
    ))
    fig5.update_layout(
        title="Comparación Stock Inicial vs Actual (Top 15 productos)",
        barmode='group',
        xaxis_title="Producto",
        yaxis_title="Cantidad",
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig5, use_container_width=True)
    
    # Variación de Stock
    st.subheader("📉 Variación de Stock por Producto")
    stock_actual_df_sorted = stock_actual_df.sort_values('variacion_stock', ascending=False).head(15)
    fig6 = px.bar(
        stock_actual_df_sorted,
        x='Producto',
        y='variacion_stock',
        title="Variación de Stock (Top 15)",
        labels={'variacion_stock': 'Variación', 'Producto': 'Producto'},
        color='variacion_stock',
        color_continuous_scale='RdYlGn'
    )
    fig6.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig6, use_container_width=True)
    
    # Distribución por Sistema
    st.subheader("🗂️ Distribución por Sistema")
    sistema_counts = stock_actual_df.groupby('SISTEMA')['stock_actual'].sum().reset_index()
    fig7 = px.pie(
        sistema_counts,
        values='stock_actual',
        names='SISTEMA',
        title="Stock Actual por Sistema"
    )
    st.plotly_chart(fig7, use_container_width=True)

def main():
    # Título principal
    st.title("📦 Sistema de Gestión de Consumibles y Stock")
    st.caption("")
    
    # Sidebar para navegación
    st.sidebar.title("📋 Navegación")
    pagina = st.sidebar.radio(
        "Selecciona una página:",
        ["🏠 Panel Principal", "📊 Dashboard", "📥 Entradas", "📤 Salidas"]
    )
    
    # Sistema de Backups en sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Sistema de Backups")
    
    # Información de backups
    total_entradas = len(st.session_state.entradas)
    total_salidas = len(st.session_state.salidas)
    st.sidebar.info(f"📊 **Registros actuales:**\n- Entradas: {total_entradas}\n- Salidas: {total_salidas}")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("💾 Backup DB", use_container_width=True):
            backup_file = backup_manual()
            if backup_file:
                st.sidebar.success(f"✅ Backup creado:\n{backup_file.name}")
    
    with col2:
        if st.button("📥 Export Excel", use_container_width=True):
            with st.spinner("Exportando..."):
                archivo = exportar_excel_completo()
                if archivo:
                    with open(archivo, 'rb') as f:
                        st.sidebar.download_button(
                            label="⬇️ Descargar",
                            data=f,
                            file_name=archivo.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    st.sidebar.success(f"✅ Excel generado")
    
    # Botón de exportación completa
    st.sidebar.markdown("---")
    if st.sidebar.button("📥 Exportar TODO a Excel", type="primary", use_container_width=True):
        try:
            archivo = exportar_excel_completo()
            if archivo:
                with open(archivo, 'rb') as f:
                    st.sidebar.download_button(
                        label="⬇️ Descargar Excel Completo",
                        data=f,
                        file_name=archivo.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                total_registros = total_entradas + total_salidas
                st.sidebar.success(f"✅ Excel con {total_registros} registros")
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
    
    # Panel Principal
    if pagina == "🏠 Panel Principal":
        st.header("📊 Resumen General")
        
        # Calcular métricas
        stock_actual_df = calcular_stock_actual()
        total_entradas_cant = st.session_state.entradas['cantidad'].sum() if not st.session_state.entradas.empty else 0
        total_salidas_cant = st.session_state.salidas['cantidad'].sum() if not st.session_state.salidas.empty else 0
        stock_total_inicial = stock_actual_df['Stock inicial'].sum() if not stock_actual_df.empty else 0
        stock_total_actual = stock_actual_df['stock_actual'].sum() if not stock_actual_df.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Stock Inicial Total", f"{stock_total_inicial:,.2f}")
        with col2:
            st.metric("📥 Total Entradas", f"{total_entradas_cant:,.2f}")
        with col3:
            st.metric("📤 Total Salidas", f"{total_salidas_cant:,.2f}")
        with col4:
            variacion = stock_total_actual - stock_total_inicial
            st.metric("📊 Stock Actual Total", f"{stock_total_actual:,.2f}", 
                     delta=f"{variacion:,.2f}")
        
        st.markdown("---")
        
        # Vista rápida de últimos movimientos
        col_ent, col_sal = st.columns(2)
        
        with col_ent:
            st.subheader("📥 Últimas Entradas")
            if not st.session_state.entradas.empty:
                ultimas_entradas = st.session_state.entradas.head(5)[['fecha', 'producto', 'cantidad', 'orden_compra']]
                st.dataframe(ultimas_entradas, use_container_width=True, hide_index=True)
            else:
                st.info("No hay entradas registradas")
        
        with col_sal:
            st.subheader("📤 Últimas Salidas")
            if not st.session_state.salidas.empty:
                ultimas_salidas = st.session_state.salidas.head(5)[['fecha', 'producto', 'cantidad', 'sitio']]
                st.dataframe(ultimas_salidas, use_container_width=True, hide_index=True)
            else:
                st.info("No hay salidas registradas")
    
    # Dashboard
    elif pagina == "📊 Dashboard":
        mostrar_dashboard()
    
    # Página de Entradas
    elif pagina == "📥 Entradas":
        st.header("📥 Gestión de Entradas")
        
        tab1, tab2 = st.tabs(["➕ Nueva Entrada", "📋 Lista de Entradas"])
        
        with tab1:
            st.subheader("Registrar Nueva Entrada")
            
            col1, col2 = st.columns(2)
            
            # Usar contador para forzar limpieza completa
            form_key = st.session_state.get('entrada_form_counter', 0)
            
            with col1:
                orden_compra = st.text_input("Orden de Compra *", placeholder="Ej: OC-2006", key=f"entrada_orden_compra_{form_key}")
                fecha_entrada = st.date_input("Fecha *", key=f"entrada_fecha_{form_key}")
                
                # Selector de Código Producto
                opciones_productos = [""] + st.session_state.stock_data['Codigo'].tolist() if not st.session_state.stock_data.empty else [""]
                codigo_seleccionado = st.selectbox("Código Producto *", opciones_productos, key=f"entrada_codigo_{form_key}")
                
                if codigo_seleccionado:
                    datos_prod = obtener_datos_producto(codigo_seleccionado)
                    producto_auto = datos_prod.get('producto', '')
                    um_auto = datos_prod.get('um', '')
                    sistema_auto = datos_prod.get('sistema', '')
                else:
                    producto_auto = ''
                    um_auto = ''
                    sistema_auto = ''
                
                # Producto - Campo de solo lectura visible
                st.markdown("**Producto** *")
                if producto_auto:
                    st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #262730;">{producto_auto}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #999;">Selecciona un código primero</div>', unsafe_allow_html=True)
                
                cantidad = st.number_input("Cantidad *", min_value=0.0, step=1.0, key=f"entrada_cantidad_{form_key}")
                
                # UM - Campo de solo lectura visible
                st.markdown("**UM** *")
                if um_auto:
                    st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #262730;">{um_auto}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #999;">Selecciona un código primero</div>', unsafe_allow_html=True)
                
                # Sistema - Campo de solo lectura visible
                st.markdown("**Sistema**")
                if sistema_auto:
                    st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #262730;">{sistema_auto}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #999;">Selecciona un código primero</div>', unsafe_allow_html=True)
            
            with col2:
                almacen_salida = st.text_input("Almacén de Salida", placeholder="Ej: Chorrillos", key=f"entrada_almacen_salida_{form_key}")
                fecha_envio = st.date_input("Fecha de Envío", key=f"entrada_fecha_envio_{form_key}")
                responsable_envio = st.text_input("Responsable de Envío", key=f"entrada_responsable_envio_{form_key}")
                almacen_recepcion = st.text_input("Almacén de Recepción", placeholder="Ej: Ica", key=f"entrada_almacen_recepcion_{form_key}")
                fecha_recepcion = st.date_input("Fecha de Recepción", key=f"entrada_fecha_recepcion_{form_key}")
                responsable_recepcion = st.text_input("Responsable de Recepción", key=f"entrada_responsable_recepcion_{form_key}")
            
            if st.button("✅ Registrar Entrada", type="primary"):
                if not all([orden_compra, codigo_seleccionado, cantidad]):
                    st.error("❌ Por favor completa todos los campos obligatorios (*)")
                else:
                    datos = {
                        'orden_compra': orden_compra,
                        'fecha': str(fecha_entrada),
                        'codigo': codigo_seleccionado,
                        'producto': producto_auto,
                        'cantidad': cantidad,
                        'um': um_auto,
                        'sistema': sistema_auto,
                        'almacen_salida': almacen_salida,
                        'fecha_envio': str(fecha_envio),
                        'responsable_envio': responsable_envio,
                        'almacen_recepcion': almacen_recepcion,
                        'fecha_recepcion': str(fecha_recepcion),
                        'responsable_recepcion': responsable_recepcion
                    }
                    if crear_entrada(datos):
                        st.success("✅ Entrada registrada correctamente")
                        st.info("🔄 Datos sincronizados automáticamente")
                        # Incrementar contador para limpiar formulario
                        st.session_state['entrada_form_counter'] = st.session_state.get('entrada_form_counter', 0) + 1
                        st.rerun()
        
        with tab2:
            st.subheader("📋 Lista de Entradas Registradas")
            
            if st.session_state.entradas.empty:
                st.info("No hay entradas registradas aún.")
            else:
                for idx, entrada in st.session_state.entradas.iterrows():
                    with st.expander(f"📦 OC: {entrada['orden_compra']} - {entrada['producto']} - Cantidad: {entrada['cantidad']} {entrada['um']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Fecha:** {entrada.get('fecha', 'N/A')}")
                            st.write(f"**Código:** {entrada.get('codigo', 'N/A')}")
                            st.write(f"**Producto:** {entrada.get('producto', 'N/A')}")
                            st.write(f"**Cantidad:** {entrada.get('cantidad', 'N/A')} {entrada.get('um', '')}")
                        
                        with col2:
                            st.write(f"**Sistema:** {entrada.get('sistema', 'N/A')}")
                            st.write(f"**Almacén Salida:** {entrada.get('almacen_salida', 'N/A')}")
                            st.write(f"**Fecha Envío:** {entrada.get('fecha_envio', 'N/A')}")
                            st.write(f"**Responsable Envío:** {entrada.get('responsable_envio', 'N/A')}")
                        
                        with col3:
                            st.write(f"**Almacén Recepción:** {entrada.get('almacen_recepcion', 'N/A')}")
                            st.write(f"**Fecha Recepción:** {entrada.get('fecha_recepcion', 'N/A')}")
                            st.write(f"**Responsable Recepción:** {entrada.get('responsable_recepcion', 'N/A')}")
                        
                        # Clave única con idx y fecha para evitar duplicados
                        if st.button(f"🗑️ Eliminar", key=f"del_ent_{entrada['id']}_{idx}_{entrada.get('fecha', '')}"):
                            eliminar_entrada(entrada['id'])
                            st.success("✅ Entrada eliminada")
                            st.info("🔄 Datos sincronizados")
                            st.rerun()
    
    # Página de Salidas
    elif pagina == "📤 Salidas":
        st.header("📤 Gestión de Salidas")
        
        tab1, tab2 = st.tabs(["➕ Nueva Salida", "📋 Lista de Salidas"])
        
        with tab1:
            st.subheader("Registrar Nueva Salida")
            
            col1, col2 = st.columns(2)
            
            # Usar contador para forzar limpieza completa
            form_key = st.session_state.get('salida_form_counter', 0)
            
            with col1:
                nro_guia = st.text_input("N° Guía de Salida *", placeholder="Ej: A123", key=f"salida_nro_guia_{form_key}")
                nro_tarea = st.text_input("N° Tarea", placeholder="Ej: cm-00312", key=f"salida_nro_tarea_{form_key}")
                fecha_salida = st.date_input("Fecha *", key=f"salida_fecha_{form_key}")
                
                # Selector de Site
                opciones_sites = [""] + st.session_state.sites_data['Nombre'].tolist() if not st.session_state.sites_data.empty else [""]
                sitio_seleccionado = st.selectbox("Sitio *", opciones_sites, key=f"salida_sitio_{form_key}")
                
                if sitio_seleccionado:
                    datos_site = obtener_datos_site(sitio_seleccionado)
                    cod_sitio_auto = datos_site.get('cod_sitio', '')
                    departamento_auto = datos_site.get('departamento', '')
                else:
                    cod_sitio_auto = ''
                    departamento_auto = ''
                
                # Código Sitio - Campo de solo lectura visible
                st.markdown("**Código Sitio** *")
                if cod_sitio_auto:
                    st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #262730;">{cod_sitio_auto}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #999;">Selecciona un sitio primero</div>', unsafe_allow_html=True)
                
                # Departamento - Campo de solo lectura visible
                st.markdown("**Departamento** *")
                if departamento_auto:
                    st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #262730;">{departamento_auto}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #999;">Selecciona un sitio primero</div>', unsafe_allow_html=True)
                
                # Selector de Código Producto
                opciones_productos = [""] + st.session_state.stock_data['Codigo'].tolist() if not st.session_state.stock_data.empty else [""]
                codigo_prod_seleccionado = st.selectbox("Código Producto *", opciones_productos, key=f"salida_codigo_{form_key}")
                
                if codigo_prod_seleccionado:
                    datos_prod = obtener_datos_producto(codigo_prod_seleccionado)
                    producto_salida_auto = datos_prod.get('producto', '')
                    um_salida_auto = datos_prod.get('um', '')
                    sistema_salida_auto = datos_prod.get('sistema', '')
                else:
                    producto_salida_auto = ''
                    um_salida_auto = ''
                    sistema_salida_auto = ''
            
            with col2:
                # Producto - Campo de solo lectura visible
                st.markdown("**Producto** *")
                if producto_salida_auto:
                    st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #262730;">{producto_salida_auto}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #999;">Selecciona un código primero</div>', unsafe_allow_html=True)
                
                code_indra = st.text_input("CODE INDRA", placeholder="Ej: a1", key=f"salida_code_indra_{form_key}")
                descripcion = st.text_input("Descripción", key=f"salida_descripcion_{form_key}")
                cantidad_salida = st.number_input("Cantidad *", min_value=0.0, step=1.0, key=f"salida_cantidad_{form_key}")
                
                # UM - Campo de solo lectura visible
                st.markdown("**UM** *")
                if um_salida_auto:
                    st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #262730;">{um_salida_auto}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #999;">Selecciona un código primero</div>', unsafe_allow_html=True)
                
                # Sistema - Campo de solo lectura visible
                st.markdown("**Sistema**")
                if sistema_salida_auto:
                    st.markdown(f'<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #262730;">{sistema_salida_auto}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 1px solid #ddd; color: #999;">Selecciona un código primero</div>', unsafe_allow_html=True)
            
            if st.button("✅ Registrar Salida", type="primary"):
                if not all([nro_guia, sitio_seleccionado, codigo_prod_seleccionado, cantidad_salida]):
                    st.error("❌ Por favor completa todos los campos obligatorios (*)")
                else:
                    datos = {
                        'nro_guia': nro_guia,
                        'nro_tarea': nro_tarea,
                        'fecha': str(fecha_salida),
                        'cod_sitio': cod_sitio_auto,
                        'sitio': sitio_seleccionado,
                        'departamento': departamento_auto,
                        'codigo': codigo_prod_seleccionado,
                        'producto': producto_salida_auto,
                        'code_indra': code_indra,
                        'descripcion': descripcion,
                        'cantidad': cantidad_salida,
                        'um': um_salida_auto,
                        'sistema': sistema_salida_auto
                    }
                    if crear_salida(datos):
                        st.success("✅ Salida registrada correctamente")
                        st.info("🔄 Datos sincronizados automáticamente")
                        # Incrementar contador para limpiar formulario
                        st.session_state['salida_form_counter'] = st.session_state.get('salida_form_counter', 0) + 1
                        st.rerun()
        
        with tab2:
            st.subheader("📋 Lista de Salidas Registradas")
            
            if st.session_state.salidas.empty:
                st.info("No hay salidas registradas aún.")
            else:
                for idx, salida in st.session_state.salidas.iterrows():
                    with st.expander(f"📤 Guía: {salida['nro_guia']} - {salida['producto']} - Sitio: {salida['sitio']} - Cantidad: {salida['cantidad']} {salida['um']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**N° Guía:** {salida.get('nro_guia', 'N/A')}")
                            st.write(f"**N° Tarea:** {salida.get('nro_tarea', 'N/A')}")
                            st.write(f"**Fecha:** {salida.get('fecha', 'N/A')}")
                            st.write(f"**Cod Sitio:** {salida.get('cod_sitio', 'N/A')}")
                            st.write(f"**Sitio:** {salida.get('sitio', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Departamento:** {salida.get('departamento', 'N/A')}")
                            st.write(f"**Código:** {salida.get('codigo', 'N/A')}")
                            st.write(f"**Producto:** {salida.get('producto', 'N/A')}")
                            st.write(f"**CODE INDRA:** {salida.get('code_indra', 'N/A')}")
                            st.write(f"**Descripción:** {salida.get('descripcion', 'N/A')}")
                        
                        with col3:
                            st.write(f"**Cantidad:** {salida.get('cantidad', 'N/A')} {salida.get('um', '')}")
                            st.write(f"**UM:** {salida.get('um', 'N/A')}")
                            st.write(f"**Sistema:** {salida.get('sistema', 'N/A')}")
                        
                        # Clave única con idx y fecha para evitar duplicados
                        if st.button(f"🗑️ Eliminar", key=f"del_sal_{salida['id']}_{idx}_{salida.get('fecha', '')}"):
                            eliminar_salida(salida['id'])
                            st.success("✅ Salida eliminada")
                            st.info("🔄 Datos sincronizados")
                            st.rerun()

if __name__ == "__main__":
    main()
# ==================== FUNCIONES DE GITHUB API ====================

def commit_file_to_github(file_path, content, commit_message):
    """Hace commit de un archivo a GitHub usando la API"""
    try:
        print(f"🔄 Intentando commit: {file_path}")
        
        # Leer secrets de Streamlit
        github_token = st.secrets.get("GITHUB_TOKEN")
        github_repo = st.secrets.get("GITHUB_REPO")
        github_branch = st.secrets.get("GITHUB_BRANCH", "main")
        
        if not github_token or not github_repo:
            print("⚠️ Token de GitHub no configurado en Secrets")
            return False
        
        print(f"✅ Token encontrado, repo: {github_repo}")
        
        # API endpoint
        api_url = f"https://api.github.com/repos/{github_repo}/contents/{file_path}"
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Obtener SHA actual del archivo (si existe)
        response = requests.get(api_url, headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json().get("sha")
            print(f"📄 Archivo existe, SHA: {sha[:7]}...")
        else:
            print(f"📄 Archivo nuevo, será creado")
        
        # Codificar contenido en base64
        content_bytes = content.encode('utf-8') if isinstance(content, str) else content
        content_base64 = base64.b64encode(content_bytes).decode('utf-8')
        
        # Datos para el commit
        data = {
            "message": commit_message,
            "content": content_base64,
            "branch": github_branch
        }
        
        if sha:
            data["sha"] = sha
        
        # Hacer commit
        print(f"📤 Enviando commit...")
        response = requests.put(api_url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            print(f"✅ Commit exitoso: {file_path}")
            return True
        else:
            print(f"❌ Error en commit: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error al hacer commit a GitHub: {e}")
        return False

def sincronizar_github():
    """Sincroniza archivos JSON y Excel con GitHub"""
    try:
        # Leer entradas y salidas
        entradas = cargar_entradas_db()
        salidas = cargar_salidas_db()
        
        # Guardar localmente primero
        guardar_a_json(entradas, ENTRADAS_PERSIST)
        guardar_a_json(salidas, SALIDAS_PERSIST)
        
        # Leer contenido de JSON
        with open(ENTRADAS_PERSIST, 'r', encoding='utf-8') as f:
            entradas_json = f.read()
        
        with open(SALIDAS_PERSIST, 'r', encoding='utf-8') as f:
            salidas_json = f.read()
        
        # Commit a GitHub
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        commit_file_to_github(
            "data/entradas_persist.json",
            entradas_json,
            f"Auto-sync entradas - {timestamp}"
        )
        
        commit_file_to_github(
            "data/salidas_persist.json",
            salidas_json,
            f"Auto-sync salidas - {timestamp}"
        )
        
        # Crear y subir backup Excel
        auto_backup_excel_github()
        
        return True
        
    except Exception as e:
        print(f"Error en sincronización GitHub: {e}")
        return False

def auto_backup_excel_github():
    """Crea backup Excel y lo sube a GitHub"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_auto_{timestamp}.xlsx"
        local_path = DATA_DIR / filename
        
        entradas = cargar_entradas_db()
        salidas = cargar_salidas_db()
        
        # Crear Excel localmente
        with pd.ExcelWriter(local_path, engine='openpyxl') as writer:
            entradas.to_excel(writer, sheet_name='Entradas', index=False)
            salidas.to_excel(writer, sheet_name='Salidas', index=False)
        
        # Leer archivo Excel como bytes
        with open(local_path, 'rb') as f:
            excel_bytes = f.read()
        
        # Subir a GitHub
        commit_file_to_github(
            f"data/{filename}",
            excel_bytes,
            f"Auto-backup Excel - {timestamp}"
        )
        
        # Limpiar backups locales antiguos
        backups = sorted(DATA_DIR.glob("backup_auto_*.xlsx"))
        if len(backups) > 5:
            for old_backup in backups[:-5]:
                old_backup.unlink()
        
        return True
        
    except Exception as e:
        print(f"Error en backup Excel: {e}")
        return False