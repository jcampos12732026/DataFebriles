import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Sala Situacional - Febriles", layout="wide")

@st.cache_data
def cargar_datos():
    # Cargar CSV delimitado por comas
    df = pd.read_csv("febriles_consolidado.csv")
    
    # Normalizar nombres de columnas a minúsculas y sin espacios
    df.columns = df.columns.str.strip().str.lower()
    
    # Renombrar 'ano' a 'año' para visualización clara
    if 'ano' in df.columns:
        df = df.rename(columns={'ano': 'año'})
        
    return df

# Cargar los datos
try:
    df = cargar_datos()

    st.title("🏥 SALA SITUATIONAL DE FEBRILES")
    st.caption("Centro de Salud César López Silva | Vigilancia Epidemiológica")

    # Filtros en la barra lateral
    st.sidebar.header("Filtros de Análisis")
    
    anios_disponibles = sorted(df['año'].dropna().unique())
    anio_sel = st.sidebar.multiselect("Seleccionar Año(s):", anios_disponibles, default=anios_disponibles)
    
    semanas_disponibles = sorted(df['semana'].dropna().unique())
    semana_sel = st.sidebar.multiselect("Seleccionar Semana(s):", semanas_disponibles, default=semanas_disponibles)

    # Filtrar DataFrame
    df_filtrado = df[(df['año'].isin(anio_sel)) & (df['semana'].isin(semana_sel))]

    # Métricas Principales
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registro Febriles", int(df_filtrado['feb_tot'].sum()) if 'feb_tot' in df_filtrado.columns else len(df_filtrado))
    col2.metric("Total Atenciones", int(df_filtrado['tot_aten'].sum()) if 'tot_aten' in df_filtrado.columns else 0)
    col3.metric("Establecimiento(s)", df_filtrado['e_salud'].nunique() if 'e_salud' in df_filtrado.columns else 1)

    st.divider()

    # Gráfico por Semana Epidemiológica
    if 'feb_tot' in df_filtrado.columns:
        st.subheader("Evolución de Casos Febriles por Semana Epidemiológica")
        df_grafico = df_filtrado.groupby(['semana', 'año'])['feb_tot'].sum().unstack().fillna(0)
        st.line_chart(df_grafico)

    # Vista previa de datos
    with st.expander("Ver tabla de datos detallada"):
        st.dataframe(df_filtrado)

except Exception as e:
    st.error(f"Error al procesar el archivo: {e}")
