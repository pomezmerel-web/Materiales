import streamlit as st
import pandas as pd
import io

# Configuración de la página a un formato más ancho
st.set_page_config(page_title="Gestor de Materiales", layout="wide")

st.title("⚡ Costo Corte - Gestor de Materiales por Proyecto")

# 1. Cargar la base de datos maestra
@st.cache_data
def cargar_datos():
    df = pd.read_csv("master_materiales_limpio.csv")
    df['CÓDIGO'] = df['CODIGO'].astype(str)
    df['BUSCADOR'] = df['CÓDIGO'] + " - " + df['DESCRIPCION']
    return df

try:
    df_materiales = cargar_datos()
except FileNotFoundError:
    st.error("No se encontró el archivo 'master_materiales_limpio.csv'.")
    st.stop()

# 2. Base de datos en memoria para toda la sesión
if 'inventario' not in st.session_state:
    st.session_state.inventario = pd.DataFrame(columns=['PROYECTO', 'CÓDIGO', 'DESCRIPCIÓN', 'VALORIZADO', 'CANTIDAD'])

# 3. Creación de Pestañas
tab1, tab2, tab3 = st.tabs(["📝 1. Agregar Materiales", "📋 2. Ver Inventario", "🧮 3. Calculadora y Exportación"])

# === PESTAÑA 1: REGISTRAR ===
with tab1:
    st.subheader("Datos del Proyecto")
    proyecto_actual = st.text_input("Nombre del Proyecto (Ej: Reconexión 001 - Electrodunas):", value="Proyecto A").strip().upper()
    
    st.divider()
    
    st.subheader("Buscar en Base de Datos")
    col1, col2 = st.columns([3, 1])
    with col1:
        opciones_busqueda = [""] + df_materiales['BUSCADOR'].tolist()
        material_seleccionado = st.selectbox("Escribe o busca un material:", options=opciones_busqueda)
    with col2:
        cantidad = st.number_input("Cantidad", min_value=1, step=1)

    if st.button("➕ Agregar a este Proyecto", type="primary"):
        if not proyecto_actual:
            st.warning("⚠️ Por favor, ingresa el nombre del proyecto arriba.")
        elif material_seleccionado == "":
            st.warning("⚠️ Por favor, selecciona un material de la lista.")
        else:
            detalle = df_materiales[df_materiales['BUSCADOR'] == material_seleccionado].iloc[0]
            
            # --- VALIDACIÓN DE DUPLICADOS ---
            ya_existe = st.session_state.inventario[
                (st.session_state.inventario['PROYECTO'] == proyecto_actual) & 
                (st.session_state.inventario['CÓDIGO'] == detalle['CÓDIGO'])
            ]
            
            if not ya_existe.empty:
                st.warning(f"⚠️ ¡ATENCIÓN! El material **{detalle['DESCRIPCION']}** ya está agregado en el **{proyecto_actual}**.")
                st.info("💡 Si deseas modificar la cantidad, ve a la pestaña '2. Ver Inventario', elimina el material actual y vuelve a agregarlo con la nueva cantidad.")
            else:
                nuevo_item = pd.DataFrame([{
                    'PROYECTO': proyecto_actual,
                    'CÓDIGO': detalle['CÓDIGO'],
                    'DESCRIPCIÓN': detalle['DESCRIPCION'],
                    'VALORIZADO': detalle['VALORIZADO'],
                    'CANTIDAD': cantidad
                }])
                st.session_state.inventario = pd.concat([st.session_state.inventario, nuevo_item], ignore_index=True)
                st.success(f"✅ ¡Agregado a {proyecto_actual}: {cantidad} x {detalle['DESCRIPCION']}!")

    st.divider()
    
    st.subheader("O Agregar Material Manual (Si no existe)")
    col_n1, col_n2, col_n3 = st.columns([1, 2, 1])
    with col_n1:
        nuevo_codigo = st.text_input("Código", value="S/C", key="m_cod")
    with col_n2:
        nueva_desc = st.text_input("Descripción del material", key="m_desc").upper()
    with col_n3:
        nueva_cant = st.number_input("Cant.", min_value=1, step=1, key="m_cant")

    if st.button("➕ Agregar Material Manual"):
        if not proyecto_actual:
            st.warning("⚠️ Debes ingresar un nombre de proyecto.")
        elif nueva_desc.strip() != "":
            # --- VALIDACIÓN DE DUPLICADOS MANUALES ---
            ya_existe_manual = st.session_state.inventario[
                (st.session_state.inventario['PROYECTO'] == proyecto_actual) & 
                (st.session_state.inventario['DESCRIPCIÓN'] == nueva_desc.strip())
            ]
            
            if not ya_existe_manual.empty:
                st.warning(f"⚠️ ¡ATENCIÓN! Ya existe un material con esa descripción en el **{proyecto_actual}**.")
            else:
                nuevo_item = pd.DataFrame([{
                    'PROYECTO': proyecto_actual,
                    'CÓDIGO': nuevo_codigo,
                    'DESCRIPCIÓN': nueva_desc.strip(),
                    'VALORIZADO': '0.00', 
                    'CANTIDAD': nueva_cant
                }])
                st.session_state.inventario = pd.concat([st.session_state.inventario, nuevo_item], ignore_index=True)
                st.success(f"✅ ¡Material manual agregado a {proyecto_actual}!")
        else:
            st.error("⚠️ Ingresa una descripción válida.")

# === PESTAÑA 2: VER INVENTARIO Y ELIMINAR ===
with tab2:
    st.header("Lista General de Materiales")
    if st.session_state.inventario.empty:
        st.info("Aún no has registrado ningún material.")
    else:
        proyectos_registrados = ["Ver Todos"] + st.session_state.inventario['PROYECTO'].unique().tolist()
        filtro = st.selectbox("Filtrar vista de tabla:", proyectos_registrados)

        if filtro == "Ver Todos":
            df_mostrar = st.session_state.inventario
        else:
            df_mostrar = st.session_state.inventario[st.session_state.inventario['PROYECTO'] == filtro]
        
        st.dataframe(df_mostrar, use_container_width=True)

        st.divider()
        
        st.subheader("🗑️ Eliminar un material específico")
        
        lista_proyectos_eliminar = st.session_state.inventario['PROYECTO'].unique().tolist()
        col_e1, col_e2 = st.columns([1, 2])
        
        with col_e1:
            proy_eliminar = st.selectbox("1. Selecciona el proyecto:", lista_proyectos_eliminar)
        
        with col_e2:
            mats_proyecto = st.session_state.inventario[st.session_state.inventario['PROYECTO'] == proy_eliminar]
            opciones_eliminar = {f"{row['CÓDIGO']} - {row['DESCRIPCIÓN']} (Cant: {row['CANTIDAD']})": row['CÓDIGO'] for _, row in mats_proyecto.iterrows()}
            
            if opciones_eliminar:
                mat_eliminar_str = st.selectbox("2. Selecciona el material a eliminar:", list(opciones_eliminar.keys()))
            else:
                mat_eliminar_str = None
                st.info("No hay materiales en este proyecto para eliminar.")

        if st.button("❌ Eliminar Material Seleccionado"):
            if mat_eliminar_str:
                codigo_a_borrar = opciones_eliminar[mat_eliminar_str]
                condicion_mantener = ~((st.session_state.inventario['PROYECTO'] == proy_eliminar) & (st.session_state.inventario['CÓDIGO'] == codigo_a_borrar))
                st.session_state.inventario = st.session_state.inventario[condicion_mantener].reset_index(drop=True)
                st.success("¡Material eliminado correctamente!")
                st.rerun() 

        st.divider()
        with st.expander("Opciones avanzadas"):
            if st.button("⚠️ Borrar TODOS los datos y empezar de cero"):
                st.session_state.inventario = pd.DataFrame(columns=['PROYECTO', 'CÓDIGO', 'DESCRIPCIÓN', 'VALORIZADO', 'CANTIDAD'])
                st.rerun()

# === PESTAÑA 3: CALCULADORA Y EXPORTACIÓN ===
with tab3:
    st.header("🧮 Calculadora y Descargas")
    st.write("Selecciona los proyectos que deseas exportar o consolidar.")
    
    if st.session_state.inventario.empty:
        st.info("Agrega materiales en la primera pestaña para poder consolidarlos o exportarlos.")
    else:
        lista_unica_proyectos = st.session_state.inventario['PROYECTO'].unique().tolist()
        
        proyectos_a_sumar = st.multiselect(
            "Selecciona Proyectos:", 
            options=lista_unica_proyectos, 
            default=lista_unica_proyectos
        )

        if proyectos_a_sumar:
            df_filtrado = st.session_state.inventario[st.session_state.inventario['PROYECTO'].isin(proyectos_a_sumar)].copy()
            df_filtrado['CANTIDAD'] = pd.to_numeric(df_filtrado['CANTIDAD'])
            
            # --- CREAR EXCEL CONSOLIDADO ---
            df_consolidado = df_filtrado.groupby(['CÓDIGO', 'DESCRIPCIÓN', 'VALORIZADO'], as_index=False)['CANTIDAD'].sum()
            
            st.subheader("Vista Previa del Consolidado Sumado")
            st.dataframe(df_consolidado, use_container_width=True)

            buffer_consolidado = io.BytesIO()
            with pd.ExcelWriter(buffer_consolidado, engine='xlsxwriter') as writer:
                df_consolidado.to_excel(writer, index=False, sheet_name='Consolidado_Final')
                worksheet = writer.sheets['Consolidado_Final']
                worksheet.set_column('A:A', 15)
                worksheet.set_column('B:B', 60)
                worksheet.set_column('C:C', 15)
                worksheet.set_column('D:D', 15)

            # --- CREAR EXCEL SEPARADO POR PROYECTO ---
            buffer_proyectos = io.BytesIO()
            with pd.ExcelWriter(buffer_proyectos, engine='xlsxwriter') as writer:
                # Escribimos una pestaña en el Excel por cada proyecto seleccionado
                for proy in proyectos_a_sumar:
                    df_proy = df_filtrado[df_filtrado['PROYECTO'] == proy].drop(columns=['PROYECTO'])
                    
                    # Excel solo permite 31 caracteres para el nombre de la hoja, así que lo cortamos por si acaso
                    nombre_hoja = str(proy)[:31]
                    
                    df_proy.to_excel(writer, index=False, sheet_name=nombre_hoja)
                    worksheet = writer.sheets[nombre_hoja]
                    worksheet.set_column('A:A', 15)
                    worksheet.set_column('B:B', 60)
                    worksheet.set_column('C:C', 15)
                    worksheet.set_column('D:D', 15)

            # --- MOSTRAR BOTONES DE DESCARGA LADO A LADO ---
            st.divider()
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                st.download_button(
                    label="📥 Exportar Consolidado (Suma Total)",
                    data=buffer_consolidado.getvalue(),
                    file_name="Materiales_Suma_Consolidada.xlsx",
                    mime="application/vnd.ms-excel",
                    type="primary"
                )
                st.caption("Suma las cantidades de los materiales que se repiten en los proyectos seleccionados en una sola lista.")
                
            with col_btn2:
                st.download_button(
                    label="📂 Exportar por Proyecto (Hojas Separadas)",
                    data=buffer_proyectos.getvalue(),
                    file_name="Materiales_Por_Proyecto.xlsx",
                    mime="application/vnd.ms-excel",
                    type="primary"
                )
                st.caption("Genera un archivo Excel donde cada proyecto seleccionado tiene su propia pestaña/hoja con su lista.")