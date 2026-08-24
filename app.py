import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Sala Situacional de Febriles - MINSA",
    page_icon="🏥",
    layout="wide",
)

# Estilo visual MINSA
st.markdown(
    """
    <style>
    .main-title { font-size: 26px; font-weight: bold; color: #003366; }
    .sub-title { font-size: 16px; color: #555555; margin-bottom: 20px; }
    </style>
""",
    unsafe_allow_html=True,
)


# Cargar datos
@st.cache_data
def cargar_datos():
  ruta = os.path.join(
      os.path.dirname(__file__), "febriles_consolidado.csv"
  )
  df = pd.read_csv(ruta)
  return df


try:
  df = cargar_datos()

  # Encabezado
  st.markdown(
      '<div class="main-title">🏥 SALA SITUACIONAL DE FEBRILES</div>',
      unsafe_allow_html=True,
  )
  st.markdown(
      '<div class="sub-title">Centro de Salud César López Silva | Vigilancia'
      ' Epidemiológica</div>',
      unsafe_allow_html=True,
  )

  # Filtros Laterales (Sidebar)
  st.sidebar.header("Filtros de Análisis")

  # Detectar columna de año
  col_ano = (
      "AnoNoti"
      if "AnoNoti" in df.columns
      else ("ANO" if "ANO" in df.columns else None)
  )
  col_semana = (
      "Semana"
      if "Semana" in df.columns
      else ("SEMANA" if "SEMANA" in df.columns else None)
  )

  if col_ano and col_semana:
    anos_disponibles = sorted(df[col_ano].unique(), reverse=True)
    ano_seleccionado = st.sidebar.selectbox("Seleccionar Año:", anos_disponibles)

    semanas_disponibles = sorted(
        df[df[col_ano] == ano_seleccionado][col_semana].unique()
    )
    semana_seleccionada = st.sidebar.multiselect(
        "Semanas Epidemiológicas:",
        semanas_disponibles,
        default=semanas_disponibles,
    )

    # Filtrar DataFrame
    df_filtrado = df[
        (df[col_ano] == ano_seleccionado)
        & (df[col_semana].isin(semana_seleccionada))
    ]

    # Métricas Principales
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Total Febriles Registrados",
        f"{len(df_filtrado):,}",
        f"Año {ano_seleccionado}",
    )
    col2.metric("Semanas Analizadas", f"{len(semana_seleccionada)}")
    col3.metric(
        "Promedio de Casos / Semana",
        (
            f"{round(len(df_filtrado) / len(semana_seleccionada), 1)}"
            if semana_seleccionada
            else "0"
        ),
    )

    st.markdown("---")

    # Gráfico de Tendencia
    st.subheader(" Curva Epidemiológica por Semana")
    casos_por_semana = (
        df_filtrado.groupby(col_semana).size().reset_index(name="Casos")
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(
        data=casos_por_semana,
        x=col_semana,
        y="Casos",
        marker="o",
        color="#003366",
        linewidth=2,
        ax=ax,
    )
    ax.set_title(f"Distribución de Casos Febriles - Año {ano_seleccionado}")
    ax.set_xlabel("Semana Epidemiológica")
    ax.set_ylabel("N° de Casos")
    ax.grid(True, linestyle="--", alpha=0.5)

    st.pyplot(fig)

    # Tabla de datos
    with st.expander(" Ver Vista Previa de Datos Filtrados"):
      st.dataframe(df_filtrado.head(100), use_container_width=True)

  else:
    st.warning(
        "No se encontraron las columnas de Año o Semana en el archivo CSV."
    )

except FileNotFoundError:
  st.error(
      "No se encontró el archivo 'febriles_consolidado.csv'. Ejecuta primero"
      " 'consolidar.py'."
  )