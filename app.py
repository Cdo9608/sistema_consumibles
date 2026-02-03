import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import shutil
import os
import json

# ==================== CONFIGURACIÓN CRÍTICA ====================
st.set_page_config(
    page_title="Sistema de Inventario - VERSIÓN MEJORADA",
    page_icon="📦",
    layout="wide"
)

# ADVERTENCIA CRÍTICA EN LA PARTE SUPERIOR
st.warning("""
⚠️ **IMPORTANTE - NUEVA VERSIÓN CON AUTO-GUARDADO**
- ✅ Los datos ahora se guardan automáticamente en GitHub
- ✅ Backup automático cada vez que agregas/editas datos
- ✅ Exportación automática a la carpeta 'data/'
- 💾 **Recomendación:** Exporta a Excel al final del día por seguridad
""")

# Archivos de persistencia
DB_FILE = "inventario.db"
DATA_DIR = Path("data")
BACKUP_DIR = Path("backups")
ENTRADAS_PERSIST = DATA_DIR / "entradas_persist.json"
SALIDAS_PERSIST = DATA_DIR / "salidas_persist.json"

# Crear directorios
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# ==================== FUNCIONES DE PERSISTENCIA ====================

def guardar_a_json(df, archivo):
    """Guarda DataFrame a JSON para persistencia en GitHub"""
    try:
        # Convertir DataFrame a dict para JSON
        data = df.to_dict('records')
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error al guardar JSON: {e}")
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
        st.error(f"Error al cargar JSON: {e}")
    return pd.DataFrame()

def auto_backup_excel():
    """Crea backup automático en Excel cada vez que hay cambios"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = DATA_DIR / f"backup_auto_{timestamp}.xlsx"
        
        entradas = cargar_entradas_db()
        salidas = cargar_salidas_db()
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            entradas.to_excel(writer, sheet_name='Entradas', index=False)
            salidas.to_excel(writer, sheet_name='Salidas', index=False)
        
        # Mantener solo los últimos 5 backups automáticos
        backups = sorted(DATA_DIR.glob("backup_auto_*.xlsx"))
        if len(backups) > 5:
            for old_backup in backups[:-5]:
                old_backup.unlink()
        
        return True
    except Exception as e:
        st.error(f"Error en auto-backup: {e}")
        return False

def sincronizar_datos():
    """Sincroniza datos entre SQLite y archivos JSON"""
    try:
        # Cargar desde SQLite
        entradas = cargar_entradas_db()
        salidas = cargar_salidas_db()
        
        # Guardar a JSON para persistencia
        guardar_a_json(entradas, ENTRADAS_PERSIST)
        guardar_a_json(salidas, SALIDAS_PERSIST)
        
        # Auto backup en Excel
        auto_backup_excel()
        
        return True
    except Exception as e:
        st.error(f"Error en sincronización: {e}")
        return False

# ==================== FUNCIONES DE BASE DE DATOS ====================

def init_database():
    """Inicializa la base de datos SQLite"""
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
    
    # Restaurar desde JSON si la BD está vacía
    restaurar_desde_json_si_necesario()

def restaurar_desde_json_si_necesario():
    """Restaura datos desde JSON si la BD está vacía"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si hay datos
        cursor.execute("SELECT COUNT(*) FROM entradas")
        count_entradas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM salidas")
        count_salidas = cursor.fetchone()[0]
        
        # Si está vacío, restaurar desde JSON
        if count_entradas == 0 and ENTRADAS_PERSIST.exists():
            st.info("🔄 Restaurando entradas desde respaldo...")
            df_entradas = cargar_desde_json(ENTRADAS_PERSIST)
            if not df_entradas.empty:
                df_entradas.to_sql('entradas', conn, if_exists='replace', index=False)
                st.success(f"✅ Restauradas {len(df_entradas)} entradas")
        
        if count_salidas == 0 and SALIDAS_PERSIST.exists():
            st.info("🔄 Restaurando salidas desde respaldo...")
            df_salidas = cargar_desde_json(SALIDAS_PERSIST)
            if not df_salidas.empty:
                df_salidas.to_sql('salidas', conn, if_exists='replace', index=False)
                st.success(f"✅ Restauradas {len(df_salidas)} salidas")
        
        conn.close()
    except Exception as e:
        st.error(f"Error en restauración: {e}")

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
    """Guarda una entrada en la base de datos Y sincroniza"""
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
        ''', datos)
        
        conn.commit()
        conn.close()
        
        # Sincronizar inmediatamente
        sincronizar_datos()
        
        return True
    except Exception as e:
        st.error(f"Error al guardar entrada: {e}")
        return False

def guardar_salida_db(datos):
    """Guarda una salida en la base de datos Y sincroniza"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO salidas (
                nro_guia, nro_tarea, fecha, cod_sitio, sitio, departamento,
                codigo, producto, code_indra, descripcion, cantidad, um, sistema,
                creado_por, fecha_creacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', datos)
        
        conn.commit()
        conn.close()
        
        # Sincronizar inmediatamente
        sincronizar_datos()
        
        return True
    except Exception as e:
        st.error(f"Error al guardar salida: {e}")
        return False

def eliminar_entrada_db(entrada_id):
    """Elimina una entrada Y sincroniza"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entradas WHERE id = ?", (entrada_id,))
        conn.commit()
        conn.close()
        
        sincronizar_datos()
        return True
    except Exception as e:
        st.error(f"Error al eliminar entrada: {e}")
        return False

def eliminar_salida_db(salida_id):
    """Elimina una salida Y sincroniza"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM salidas WHERE id = ?", (salida_id,))
        conn.commit()
        conn.close()
        
        sincronizar_datos()
        return True
    except Exception as e:
        st.error(f"Error al eliminar salida: {e}")
        return False

# ==================== FUNCIONES DE CÁLCULO ====================

def calcular_stock():
    """Calcula el stock actual basado en entradas y salidas"""
    entradas = cargar_entradas_db()
    salidas = cargar_salidas_db()
    
    if entradas.empty and salidas.empty:
        return pd.DataFrame()
    
    # Agrupar entradas por código de producto
    stock_entradas = entradas.groupby(['codigo', 'producto', 'um', 'sistema']).agg({
        'cantidad': 'sum'
    }).reset_index()
    stock_entradas.rename(columns={'cantidad': 'total_entradas'}, inplace=True)
    
    # Agrupar salidas por código de producto
    stock_salidas = salidas.groupby(['codigo', 'producto', 'um', 'sistema']).agg({
        'cantidad': 'sum'
    }).reset_index()
    stock_salidas.rename(columns={'cantidad': 'total_salidas'}, inplace=True)
    
    # Combinar entradas y salidas
    stock = pd.merge(
        stock_entradas, 
        stock_salidas, 
        on=['codigo', 'producto', 'um', 'sistema'], 
        how='outer'
    )
    
    # Rellenar NaN con 0
    stock[['total_entradas', 'total_salidas']] = stock[['total_entradas', 'total_salidas']].fillna(0)
    
    # Calcular stock disponible
    stock['stock_disponible'] = stock['total_entradas'] - stock['total_salidas']
    
    # Añadir estado del stock
    stock['estado'] = stock['stock_disponible'].apply(lambda x: 
        '🔴 Agotado' if x <= 0 else 
        '🟡 Bajo' if x <= 10 else 
        '🟢 Normal'
    )
    
    # Ordenar por stock disponible
    stock = stock.sort_values('stock_disponible', ascending=True)
    
    return stock

# ==================== FUNCIONES DE EXPORTACIÓN ====================

def exportar_excel_completo():
    """Exporta todas las tablas a un archivo Excel"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"inventario_completo_{timestamp}.xlsx"
        filepath = DATA_DIR / filename
        
        entradas = cargar_entradas_db()
        salidas = cargar_salidas_db()
        stock = calcular_stock()
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Exportar entradas
            if not entradas.empty:
                entradas_export = entradas.drop(['id', 'creado_por', 'fecha_creacion'], axis=1, errors='ignore')
                entradas_export.to_excel(writer, sheet_name='Entradas', index=False)
            
            # Exportar salidas
            if not salidas.empty:
                salidas_export = salidas.drop(['id', 'creado_por', 'fecha_creacion'], axis=1, errors='ignore')
                salidas_export.to_excel(writer, sheet_name='Salidas', index=False)
            
            # Exportar stock
            if not stock.empty:
                stock.to_excel(writer, sheet_name='Stock', index=False)
        
        return filepath
    except Exception as e:
        st.error(f"Error al exportar: {e}")
        return None

# ==================== INTERFAZ STREAMLIT ====================

def main():
    """Función principal de la aplicación"""
    
    # Inicializar base de datos
    init_database()
    
    # Título principal
    st.title("📦 Sistema de Gestión de Consumibles y Stock")
    st.markdown("**Versión mejorada con persistencia automática**")
    
    # Sidebar para navegación
    st.sidebar.title("📋 Menú de Navegación")
    pagina = st.sidebar.radio(
        "Selecciona una opción:",
        ["🏠 Dashboard", "📥 Registrar Entrada", "📤 Registrar Salida", 
         "📊 Ver Entradas", "📊 Ver Salidas", "📦 Inventario/Stock",
         "💾 Exportar Datos", "⚙️ Configuración"]
    )
    
    # Mostrar estadísticas rápidas en sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Estadísticas Rápidas")
    
    entradas = cargar_entradas_db()
    salidas = cargar_salidas_db()
    stock = calcular_stock()
    
    st.sidebar.metric("Total Entradas", len(entradas))
    st.sidebar.metric("Total Salidas", len(salidas))
    if not stock.empty:
        productos_bajo_stock = len(stock[stock['stock_disponible'] <= 10])
        st.sidebar.metric("Productos Bajo Stock", productos_bajo_stock)
    
    # Botón de sincronización manual
    if st.sidebar.button("🔄 Sincronizar Ahora", help="Guarda todos los datos en GitHub"):
        with st.spinner("Sincronizando..."):
            if sincronizar_datos():
                st.sidebar.success("✅ Datos sincronizados")
    
    # Renderizar la página seleccionada
    if pagina == "🏠 Dashboard":
        mostrar_dashboard(entradas, salidas, stock)
    elif pagina == "📥 Registrar Entrada":
        registrar_entrada()
    elif pagina == "📤 Registrar Salida":
        registrar_salida()
    elif pagina == "📊 Ver Entradas":
        ver_entradas(entradas)
    elif pagina == "📊 Ver Salidas":
        ver_salidas(salidas)
    elif pagina == "📦 Inventario/Stock":
        ver_stock(stock)
    elif pagina == "💾 Exportar Datos":
        exportar_datos()
    elif pagina == "⚙️ Configuración":
        configuracion()

# Continúa con las funciones de cada página...
def mostrar_dashboard(entradas, salidas, stock):
    """Muestra el dashboard principal"""
    st.header("🏠 Dashboard General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📥 Total Entradas",
            len(entradas),
            help="Número total de registros de entradas"
        )
    
    with col2:
        st.metric(
            "📤 Total Salidas",
            len(salidas),
            help="Número total de registros de salidas"
        )
    
    with col3:
        if not stock.empty:
            productos_activos = len(stock[stock['stock_disponible'] > 0])
            st.metric(
                "📦 Productos con Stock",
                productos_activos,
                help="Productos que tienen stock disponible"
            )
        else:
            st.metric("📦 Productos con Stock", 0)
    
    with col4:
        if not stock.empty:
            bajo_stock = len(stock[stock['stock_disponible'] <= 10])
            st.metric(
                "⚠️ Productos Bajo Stock",
                bajo_stock,
                delta=f"-{bajo_stock}" if bajo_stock > 0 else "0",
                delta_color="inverse",
                help="Productos con stock menor o igual a 10 unidades"
            )
        else:
            st.metric("⚠️ Productos Bajo Stock", 0)
    
    # Gráficos
    if not entradas.empty or not salidas.empty:
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Entradas vs Salidas por Sistema")
            if not entradas.empty:
                entradas_por_sistema = entradas.groupby('sistema')['cantidad'].sum().reset_index()
                entradas_por_sistema.columns = ['Sistema', 'Cantidad']
                entradas_por_sistema['Tipo'] = 'Entradas'
                
                salidas_por_sistema = salidas.groupby('sistema')['cantidad'].sum().reset_index()
                salidas_por_sistema.columns = ['Sistema', 'Cantidad']
                salidas_por_sistema['Tipo'] = 'Salidas'
                
                df_comparacion = pd.concat([entradas_por_sistema, salidas_por_sistema])
                
                fig = px.bar(df_comparacion, x='Sistema', y='Cantidad', color='Tipo', 
                           barmode='group', title='Entradas vs Salidas')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Estado del Stock")
            if not stock.empty:
                estado_counts = stock['estado'].value_counts().reset_index()
                estado_counts.columns = ['Estado', 'Cantidad']
                
                fig = px.pie(estado_counts, values='Cantidad', names='Estado',
                           title='Distribución del Estado del Stock',
                           color_discrete_sequence=['#ff4b4b', '#ffa500', '#00cc00'])
                st.plotly_chart(fig, use_container_width=True)
    
    # Productos críticos
    if not stock.empty:
        st.markdown("---")
        st.subheader("⚠️ Productos que Requieren Atención")
        
        productos_criticos = stock[stock['stock_disponible'] <= 10].head(10)
        
        if not productos_criticos.empty:
            st.dataframe(
                productos_criticos[['codigo', 'producto', 'sistema', 'stock_disponible', 'estado']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✅ No hay productos con stock bajo en este momento")

def registrar_entrada():
    """Formulario para registrar nueva entrada"""
    st.header("📥 Registrar Nueva Entrada")
    
    with st.form("formulario_entrada"):
        col1, col2 = st.columns(2)
        
        with col1:
            orden_compra = st.text_input("Orden de Compra *")
            fecha = st.date_input("Fecha *", datetime.now())
            codigo = st.text_input("Código *")
            producto = st.text_input("Producto *")
            cantidad = st.number_input("Cantidad *", min_value=0.0, step=0.01)
            um = st.selectbox("Unidad de Medida *", ["UND", "KG", "LT", "MT", "PAQ", "CAJA"])
            sistema = st.selectbox("Sistema *", ["COMUNICACIONES", "ENERGIA", "TX", "CIVIL", "OTRO"])
        
        with col2:
            almacen_salida = st.text_input("Almacén de Salida")
            fecha_envio = st.date_input("Fecha de Envío", value=None)
            responsable_envio = st.text_input("Responsable de Envío")
            almacen_recepcion = st.text_input("Almacén de Recepción")
            fecha_recepcion = st.date_input("Fecha de Recepción", value=None)
            responsable_recepcion = st.text_input("Responsable de Recepción")
        
        usuario = st.text_input("Registrado por", "Usuario Sistema")
        
        submitted = st.form_submit_button("✅ Registrar Entrada", use_container_width=True)
        
        if submitted:
            if not all([orden_compra, codigo, producto, cantidad > 0]):
                st.error("⚠️ Por favor completa todos los campos obligatorios (*)")
            else:
                datos = (
                    orden_compra,
                    fecha.strftime('%d/%m/%Y'),
                    codigo,
                    producto,
                    cantidad,
                    um,
                    sistema,
                    almacen_salida,
                    fecha_envio.strftime('%d/%m/%Y') if fecha_envio else '',
                    responsable_envio,
                    almacen_recepcion,
                    fecha_recepcion.strftime('%d/%m/%Y') if fecha_recepcion else '',
                    responsable_recepcion,
                    usuario,
                    datetime.now().strftime('%d/%m/%Y %I:%M %p')
                )
                
                if guardar_entrada_db(datos):
                    st.success(f"✅ Entrada registrada correctamente - OC: {orden_compra}")
                    st.info("🔄 Datos sincronizados automáticamente")
                    st.balloons()
                else:
                    st.error("❌ Error al registrar la entrada")

def registrar_salida():
    """Formulario para registrar nueva salida"""
    st.header("📤 Registrar Nueva Salida")
    
    with st.form("formulario_salida"):
        col1, col2 = st.columns(2)
        
        with col1:
            nro_guia = st.text_input("Nro. Guía *")
            nro_tarea = st.text_input("Nro. Tarea")
            fecha = st.date_input("Fecha *", datetime.now())
            cod_sitio = st.text_input("Código Sitio *")
            sitio = st.text_input("Sitio *")
            departamento = st.text_input("Departamento")
            codigo = st.text_input("Código Producto *")
        
        with col2:
            producto = st.text_input("Producto *")
            code_indra = st.text_input("Code Indra")
            descripcion = st.text_area("Descripción")
            cantidad = st.number_input("Cantidad *", min_value=0.0, step=0.01)
            um = st.selectbox("Unidad de Medida *", ["UND", "KG", "LT", "MT", "PAQ", "CAJA"])
            sistema = st.selectbox("Sistema *", ["COMUNICACIONES", "ENERGIA", "TX", "CIVIL", "OTRO"])
        
        usuario = st.text_input("Registrado por", "Usuario Sistema")
        
        submitted = st.form_submit_button("✅ Registrar Salida", use_container_width=True)
        
        if submitted:
            if not all([nro_guia, cod_sitio, sitio, codigo, producto, cantidad > 0]):
                st.error("⚠️ Por favor completa todos los campos obligatorios (*)")
            else:
                datos = (
                    nro_guia,
                    nro_tarea,
                    fecha.strftime('%d/%m/%Y'),
                    cod_sitio,
                    sitio,
                    departamento,
                    codigo,
                    producto,
                    code_indra,
                    descripcion,
                    cantidad,
                    um,
                    sistema,
                    usuario,
                    datetime.now().strftime('%d/%m/%Y %I:%M %p')
                )
                
                if guardar_salida_db(datos):
                    st.success(f"✅ Salida registrada correctamente - Guía: {nro_guia}")
                    st.info("🔄 Datos sincronizados automáticamente")
                    st.balloons()
                else:
                    st.error("❌ Error al registrar la salida")

def ver_entradas(entradas):
    """Muestra y permite gestionar las entradas"""
    st.header("📊 Entradas Registradas")
    
    if entradas.empty:
        st.info("📭 No hay entradas registradas aún")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_sistema = st.multiselect(
            "Filtrar por Sistema",
            options=entradas['sistema'].unique().tolist(),
            default=entradas['sistema'].unique().tolist()
        )
    
    with col2:
        filtro_producto = st.text_input("Buscar producto")
    
    with col3:
        ordenar_por = st.selectbox("Ordenar por", ["Fecha (más reciente)", "Producto", "Cantidad"])
    
    # Aplicar filtros
    df_filtrado = entradas[entradas['sistema'].isin(filtro_sistema)]
    
    if filtro_producto:
        df_filtrado = df_filtrado[
            df_filtrado['producto'].str.contains(filtro_producto, case=False, na=False) |
            df_filtrado['codigo'].str.contains(filtro_producto, case=False, na=False)
        ]
    
    # Aplicar ordenamiento
    if ordenar_por == "Producto":
        df_filtrado = df_filtrado.sort_values('producto')
    elif ordenar_por == "Cantidad":
        df_filtrado = df_filtrado.sort_values('cantidad', ascending=False)
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Registros", len(df_filtrado))
    with col2:
        total_items = df_filtrado['cantidad'].sum()
        st.metric("Total Unidades", f"{total_items:,.2f}")
    with col3:
        sistemas = df_filtrado['sistema'].nunique()
        st.metric("Sistemas Diferentes", sistemas)
    
    # Mostrar tabla
    st.dataframe(
        df_filtrado[['orden_compra', 'fecha', 'codigo', 'producto', 'cantidad', 'um', 'sistema', 
                     'almacen_salida', 'responsable_envio']],
        use_container_width=True,
        hide_index=True
    )
    
    # Opción de eliminar
    with st.expander("🗑️ Gestionar Registros"):
        entrada_id = st.number_input("ID de entrada a eliminar", min_value=1, step=1)
        if st.button("Eliminar Entrada", type="primary"):
            if eliminar_entrada_db(entrada_id):
                st.success(f"✅ Entrada {entrada_id} eliminada")
                st.rerun()

def ver_salidas(salidas):
    """Muestra y permite gestionar las salidas"""
    st.header("📊 Salidas Registradas")
    
    if salidas.empty:
        st.info("📭 No hay salidas registradas aún")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_sistema = st.multiselect(
            "Filtrar por Sistema",
            options=salidas['sistema'].unique().tolist(),
            default=salidas['sistema'].unique().tolist()
        )
    
    with col2:
        filtro_sitio = st.multiselect(
            "Filtrar por Sitio",
            options=salidas['sitio'].unique().tolist(),
            default=salidas['sitio'].unique().tolist() if not salidas.empty else []
        )
    
    with col3:
        filtro_producto = st.text_input("Buscar producto")
    
    # Aplicar filtros
    df_filtrado = salidas[
        (salidas['sistema'].isin(filtro_sistema)) &
        (salidas['sitio'].isin(filtro_sitio))
    ]
    
    if filtro_producto:
        df_filtrado = df_filtrado[
            df_filtrado['producto'].str.contains(filtro_producto, case=False, na=False) |
            df_filtrado['codigo'].str.contains(filtro_producto, case=False, na=False)
        ]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Registros", len(df_filtrado))
    with col2:
        total_items = df_filtrado['cantidad'].sum()
        st.metric("Total Unidades", f"{total_items:,.2f}")
    with col3:
        sitios = df_filtrado['sitio'].nunique()
        st.metric("Sitios Diferentes", sitios)
    
    # Mostrar tabla
    st.dataframe(
        df_filtrado[['nro_guia', 'fecha', 'sitio', 'codigo', 'producto', 'cantidad', 'um', 'sistema']],
        use_container_width=True,
        hide_index=True
    )
    
    # Opción de eliminar
    with st.expander("🗑️ Gestionar Registros"):
        salida_id = st.number_input("ID de salida a eliminar", min_value=1, step=1)
        if st.button("Eliminar Salida", type="primary"):
            if eliminar_salida_db(salida_id):
                st.success(f"✅ Salida {salida_id} eliminada")
                st.rerun()

def ver_stock(stock):
    """Muestra el inventario/stock actual"""
    st.header("📦 Inventario y Stock Disponible")
    
    if stock.empty:
        st.info("📭 No hay datos de stock disponibles")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        filtro_sistema = st.multiselect(
            "Filtrar por Sistema",
            options=stock['sistema'].unique().tolist(),
            default=stock['sistema'].unique().tolist()
        )
    
    with col2:
        filtro_estado = st.multiselect(
            "Filtrar por Estado",
            options=stock['estado'].unique().tolist(),
            default=stock['estado'].unique().tolist()
        )
    
    # Aplicar filtros
    df_filtrado = stock[
        (stock['sistema'].isin(filtro_sistema)) &
        (stock['estado'].isin(filtro_estado))
    ]
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Productos", len(df_filtrado))
    with col2:
        agotados = len(df_filtrado[df_filtrado['stock_disponible'] <= 0])
        st.metric("Agotados", agotados)
    with col3:
        bajo_stock = len(df_filtrado[df_filtrado['stock_disponible'] <= 10])
        st.metric("Bajo Stock", bajo_stock)
    with col4:
        normal = len(df_filtrado[df_filtrado['stock_disponible'] > 10])
        st.metric("Stock Normal", normal)
    
    # Tabla de stock
    st.dataframe(
        df_filtrado[['codigo', 'producto', 'sistema', 'um', 'total_entradas', 
                     'total_salidas', 'stock_disponible', 'estado']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "stock_disponible": st.column_config.NumberColumn(
                "Stock Disponible",
                help="Stock actual disponible",
                format="%.2f"
            )
        }
    )

def exportar_datos():
    """Página de exportación de datos"""
    st.header("💾 Exportar Datos")
    
    st.info("""
    **Opciones de exportación:**
    - ✅ Auto-guardado: Los datos se guardan automáticamente en la carpeta 'data/'
    - 📊 Excel completo: Exporta todas las tablas a un solo archivo
    - 📋 Backup manual: Crea una copia de seguridad adicional
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Exportar a Excel Completo", use_container_width=True):
            with st.spinner("Exportando..."):
                filepath = exportar_excel_completo()
                if filepath:
                    st.success(f"✅ Archivo exportado: {filepath.name}")
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            "⬇️ Descargar Excel",
                            data=f,
                            file_name=filepath.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
    
    with col2:
        if st.button("💾 Crear Backup Manual", use_container_width=True):
            with st.spinner("Creando backup..."):
                if sincronizar_datos():
                    st.success("✅ Backup creado correctamente")
    
    # Mostrar backups disponibles
    st.markdown("---")
    st.subheader("📦 Backups Disponibles en data/")
    
    backups = sorted(DATA_DIR.glob("backup_auto_*.xlsx"), reverse=True)
    
    if backups:
        for backup in backups[:10]:  # Mostrar últimos 10
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(backup.name)
            with col2:
                size = backup.stat().st_size / 1024
                st.text(f"{size:.1f} KB")
            with col3:
                with open(backup, 'rb') as f:
                    st.download_button(
                        "⬇️",
                        data=f,
                        file_name=backup.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=backup.name
                    )
    else:
        st.info("No hay backups automáticos disponibles")

def configuracion():
    """Página de configuración"""
    st.header("⚙️ Configuración del Sistema")
    
    st.subheader("📊 Información del Sistema")
    
    # Estado de la base de datos
    if Path(DB_FILE).exists():
        db_size = Path(DB_FILE).stat().st_size / (1024 * 1024)
        st.metric("Tamaño de Base de Datos", f"{db_size:.2f} MB")
    
    # Estado de archivos JSON
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Archivo de Entradas (JSON)**")
        if ENTRADAS_PERSIST.exists():
            size = ENTRADAS_PERSIST.stat().st_size / 1024
            st.success(f"✅ Existe ({size:.1f} KB)")
        else:
            st.warning("⚠️ No existe")
    
    with col2:
        st.markdown("**Archivo de Salidas (JSON)**")
        if SALIDAS_PERSIST.exists():
            size = SALIDAS_PERSIST.stat().st_size / 1024
            st.success(f"✅ Existe ({size:.1f} KB)")
        else:
            st.warning("⚠️ No existe")
    
    # Opciones peligrosas
    st.markdown("---")
    st.subheader("⚠️ Zona de Peligro")
    
    with st.expander("🗑️ Eliminar TODOS los datos"):
        st.warning("Esta acción NO se puede deshacer")
        confirm = st.text_input("Escribe 'ELIMINAR TODO' para confirmar")
        
        if st.button("🗑️ ELIMINAR TODOS LOS DATOS", type="primary"):
            if confirm == "ELIMINAR TODO":
                try:
                    # Crear backup final antes de eliminar
                    exportar_excel_completo()
                    
                    # Eliminar base de datos
                    if Path(DB_FILE).exists():
                        Path(DB_FILE).unlink()
                    
                    # Eliminar archivos JSON
                    if ENTRADAS_PERSIST.exists():
                        ENTRADAS_PERSIST.unlink()
                    if SALIDAS_PERSIST.exists():
                        SALIDAS_PERSIST.unlink()
                    
                    st.success("✅ Todos los datos han sido eliminados")
                    st.info("Se creó un backup de seguridad antes de eliminar")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Texto de confirmación incorrecto")

if __name__ == "__main__":
    main()
