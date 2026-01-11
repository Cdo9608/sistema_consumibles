import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

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

# Rutas de archivos
DATA_DIR = Path("data")
EXPORTS_DIR = Path("exports")
ENTRADAS_FILE = DATA_DIR / "entradas.xlsx"
SALIDAS_FILE = DATA_DIR / "salidas.xlsx"
SITES_FILE = DATA_DIR / "SITES.xlsx"
STOCK_FILE = DATA_DIR / "Stock.xlsx"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Inicializar session state para ENTRADAS
if 'entradas' not in st.session_state:
    if ENTRADAS_FILE.exists():
        st.session_state.entradas = pd.read_excel(ENTRADAS_FILE)
    else:
        st.session_state.entradas = pd.DataFrame(columns=[
            'id', 'orden_compra', 'fecha', 'codigo', 'producto', 'cantidad', 'um', 
            'sistema', 'almacen_salida', 'fecha_envio', 'responsable_envio',
            'almacen_recepcion', 'fecha_recepcion', 'responsable_recepcion',
            'creado_por', 'fecha_creacion'
        ])

# Inicializar session state para SALIDAS
if 'salidas' not in st.session_state:
    if SALIDAS_FILE.exists():
        st.session_state.salidas = pd.read_excel(SALIDAS_FILE)
    else:
        st.session_state.salidas = pd.DataFrame(columns=[
            'id', 'nro_guia', 'nro_tarea', 'fecha', 'cod_sitio', 'sitio', 
            'departamento', 'codigo', 'producto', 'code_indra', 'descripcion',
            'cantidad', 'um', 'sistema',
            'creado_por', 'fecha_creacion'
        ])

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

def guardar_entradas():
    """Guarda las entradas en Excel"""
    st.session_state.entradas.to_excel(ENTRADAS_FILE, index=False)

def guardar_salidas():
    """Guarda las salidas en Excel"""
    st.session_state.salidas.to_excel(SALIDAS_FILE, index=False)

def obtener_datos_producto(codigo_o_producto):
    """Obtiene datos del producto desde Stock.xlsx"""
    if st.session_state.stock_data.empty:
        return {}
    
    try:
        # Buscar por código o producto
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
    nuevo_id = len(st.session_state.entradas) + 1
    datos['id'] = nuevo_id
    datos['creado_por'] = 'Usuario'
    datos['fecha_creacion'] = obtener_hora_peru()
    
    nuevo_registro = pd.DataFrame([datos])
    st.session_state.entradas = pd.concat([st.session_state.entradas, nuevo_registro], ignore_index=True)
    guardar_entradas()
    return True

def crear_salida(datos):
    """Crea un nuevo registro de salida"""
    nuevo_id = len(st.session_state.salidas) + 1
    datos['id'] = nuevo_id
    datos['creado_por'] = 'Usuario'
    datos['fecha_creacion'] = obtener_hora_peru()
    
    nuevo_registro = pd.DataFrame([datos])
    st.session_state.salidas = pd.concat([st.session_state.salidas, nuevo_registro], ignore_index=True)
    guardar_salidas()
    return True

def eliminar_entrada(entrada_id):
    """Elimina un registro de entrada"""
    st.session_state.entradas = st.session_state.entradas[st.session_state.entradas['id'] != entrada_id]
    guardar_entradas()

def eliminar_salida(salida_id):
    """Elimina un registro de salida"""
    st.session_state.salidas = st.session_state.salidas[st.session_state.salidas['id'] != salida_id]
    guardar_salidas()

def exportar_excel_completo():
    """Exporta entradas y salidas en un solo Excel con 2 hojas"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = EXPORTS_DIR / f"consumibles_stock_{timestamp}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Hoja de Entradas
        df_entradas = st.session_state.entradas.copy()
        columnas_entradas = [
            'orden_compra', 'fecha', 'codigo', 'producto', 'cantidad', 'um', 
            'sistema', 'almacen_salida', 'fecha_envio', 'responsable_envio',
            'almacen_recepcion', 'fecha_recepcion', 'responsable_recepcion'
        ]
        df_entradas = df_entradas[[col for col in columnas_entradas if col in df_entradas.columns]]
        df_entradas.to_excel(writer, sheet_name='Entradas', index=False)
        
        # Hoja de Salidas
        df_salidas = st.session_state.salidas.copy()
        columnas_salidas = [
            'nro_guia', 'nro_tarea', 'fecha', 'cod_sitio', 'sitio', 
            'departamento', 'codigo', 'producto', 'code_indra', 'descripcion',
            'cantidad', 'um', 'sistema'
        ]
        df_salidas = df_salidas[[col for col in columnas_salidas if col in df_salidas.columns]]
        df_salidas.to_excel(writer, sheet_name='Salidas', index=False)
    
    return filename

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
    
    # Sidebar para navegación
    st.sidebar.title("📋 Navegación")
    pagina = st.sidebar.radio(
        "Selecciona una página:",
        ["🏠 Panel Principal", "📊 Dashboard", "📥 Entradas", "📤 Salidas"]
    )
    
    # Botón de exportación en sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Exportar Datos")
    if st.sidebar.button("Exportar TODO a Excel", type="primary"):
        try:
            archivo = exportar_excel_completo()
            with open(archivo, 'rb') as f:
                st.sidebar.download_button(
                    label="⬇️ Descargar Excel Completo",
                    data=f,
                    file_name=archivo.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            total_registros = len(st.session_state.entradas) + len(st.session_state.salidas)
            st.sidebar.success(f"✅ Excel generado con {total_registros} registros")
        except Exception as e:
            st.sidebar.error(f"❌ Error al exportar: {str(e)}")
    
    # Panel Principal
    if pagina == "🏠 Panel Principal":
        st.header("📊 Resumen General")
        
        # Calcular métricas
        stock_actual_df = calcular_stock_actual()
        total_entradas = st.session_state.entradas['cantidad'].sum() if not st.session_state.entradas.empty else 0
        total_salidas = st.session_state.salidas['cantidad'].sum() if not st.session_state.salidas.empty else 0
        stock_total_inicial = stock_actual_df['Stock inicial'].sum() if not stock_actual_df.empty else 0
        stock_total_actual = stock_actual_df['stock_actual'].sum() if not stock_actual_df.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Stock Inicial Total", f"{stock_total_inicial:,.2f}")
        with col2:
            st.metric("📥 Total Entradas", f"{total_entradas:,.2f}")
        with col3:
            st.metric("📤 Total Salidas", f"{total_salidas:,.2f}")
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
                ultimas_entradas = st.session_state.entradas.tail(5)[['fecha', 'producto', 'cantidad', 'orden_compra']]
                st.dataframe(ultimas_entradas, use_container_width=True, hide_index=True)
            else:
                st.info("No hay entradas registradas")
        
        with col_sal:
            st.subheader("📤 Últimas Salidas")
            if not st.session_state.salidas.empty:
                ultimas_salidas = st.session_state.salidas.tail(5)[['fecha', 'producto', 'cantidad', 'sitio']]
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
            
            with col1:
                orden_compra = st.text_input("Orden de Compra *", placeholder="Ej: OC-2006")
                fecha_entrada = st.date_input("Fecha *")
                
                # Selector de Código o Producto
                opciones_productos = [""] + st.session_state.stock_data['Codigo'].tolist() if not st.session_state.stock_data.empty else [""]
                codigo_seleccionado = st.selectbox("Código *", opciones_productos)
                
                if codigo_seleccionado:
                    datos_prod = obtener_datos_producto(codigo_seleccionado)
                    producto_auto = datos_prod.get('producto', '')
                    um_auto = datos_prod.get('um', '')
                    sistema_auto = datos_prod.get('sistema', '')
                else:
                    producto_auto = ''
                    um_auto = ''
                    sistema_auto = ''
                
                producto = st.text_input("Producto *", value=producto_auto, disabled=bool(codigo_seleccionado))
                cantidad = st.number_input("Cantidad *", min_value=0.0, step=1.0)
                um = st.text_input("UM *", value=um_auto, disabled=bool(codigo_seleccionado))
                sistema = st.text_input("Sistema", value=sistema_auto, disabled=bool(codigo_seleccionado))
            
            with col2:
                almacen_salida = st.text_input("Almacén de Salida", placeholder="Ej: Chorrillos")
                fecha_envio = st.date_input("Fecha de Envío")
                responsable_envio = st.text_input("Responsable de Envío")
                almacen_recepcion = st.text_input("Almacén de Recepción", placeholder="Ej: Ica")
                fecha_recepcion = st.date_input("Fecha de Recepción")
                responsable_recepcion = st.text_input("Responsable de Recepción")
            
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
                        st.success("✅ Entrada registrada exitosamente")
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
                        
                        if st.button(f"🗑️ Eliminar", key=f"del_ent_{entrada['id']}"):
                            eliminar_entrada(entrada['id'])
                            st.success("✅ Entrada eliminada")
                            st.rerun()
    
    # Página de Salidas
    elif pagina == "📤 Salidas":
        st.header("📤 Gestión de Salidas")
        
        tab1, tab2 = st.tabs(["➕ Nueva Salida", "📋 Lista de Salidas"])
        
        with tab1:
            st.subheader("Registrar Nueva Salida")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nro_guia = st.text_input("N° Guía de Salida *", placeholder="Ej: A123")
                nro_tarea = st.text_input("N° Tarea", placeholder="Ej: cm-00312")
                fecha_salida = st.date_input("Fecha *")
                
                # Selector de Site
                opciones_sites = [""] + st.session_state.sites_data['Nombre'].tolist() if not st.session_state.sites_data.empty else [""]
                sitio_seleccionado = st.selectbox("Sitio *", opciones_sites)
                
                if sitio_seleccionado:
                    datos_site = obtener_datos_site(sitio_seleccionado)
                    cod_sitio_auto = datos_site.get('cod_sitio', '')
                    departamento_auto = datos_site.get('departamento', '')
                else:
                    cod_sitio_auto = ''
                    departamento_auto = ''
                
                cod_sitio = st.text_input("Código Sitio *", value=cod_sitio_auto, disabled=bool(sitio_seleccionado))
                departamento = st.text_input("Departamento *", value=departamento_auto, disabled=bool(sitio_seleccionado))
                
                # Selector de Código o Producto
                opciones_productos = [""] + st.session_state.stock_data['Codigo'].tolist() if not st.session_state.stock_data.empty else [""]
                codigo_prod_seleccionado = st.selectbox("Código Producto *", opciones_productos)
                
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
                producto_salida = st.text_input("Producto *", value=producto_salida_auto, disabled=bool(codigo_prod_seleccionado))
                code_indra = st.text_input("CODE INDRA", placeholder="Ej: a1")
                descripcion = st.text_input("Descripción")
                cantidad_salida = st.number_input("Cantidad *", min_value=0.0, step=1.0)
                um_salida = st.text_input("UM *", value=um_salida_auto, disabled=bool(codigo_prod_seleccionado))
                sistema_salida = st.text_input("Sistema", value=sistema_salida_auto, disabled=bool(codigo_prod_seleccionado))
            
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
                        st.success("✅ Salida registrada exitosamente")
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
                        
                        if st.button(f"🗑️ Eliminar", key=f"del_sal_{salida['id']}"):
                            eliminar_salida(salida['id'])
                            st.success("✅ Salida eliminada")
                            st.rerun()

if __name__ == "__main__":
    main()