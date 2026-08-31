import os
import pandas as pd
import streamlit as st

# Configuración de página
st.set_page_config(page_title="Sala Situacional Epidemiológica", layout="wide")

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))


# Función para estandarizar nombres de columnas
def estandarizar_columnas(df):
    # Convertir todos los nombres de columnas a mayúsculas
    df.columns = [str(col).upper().strip() for col in df.columns]

    # Renombrar variaciones de AÑO a ANO
    renombres = {"AÑO": "ANO", "ANIO": "ANO"}
    df.rename(columns=renombres, inplace=True)
    return df


# Carga de datos según evento
@st.cache_data
def cargar_datos(evento):
    if evento == "Febriles":
        ruta = os.path.join(DIRECTORIO, "febriles_consolidado.csv")
        if not os.path.exists(ruta):
            return None
        df = pd.read_csv(ruta, low_memory=False)
        df = estandarizar_columnas(df)

        # Manejo flexible de la columna total para febriles
        if "FEB_TOT" in df.columns:
            df["TOTAL_CASOS"] = df["FEB_TOT"]
        elif "TOTAL" in df.columns:
            df["TOTAL_CASOS"] = df["TOTAL"]
        else:
            # Si no encuentra columna de total, busca columnas numéricas
            cols_num = df.select_dtypes(include=["number"]).columns
            df["TOTAL_CASOS"] = (
                df[cols_num[0]] if len(cols_num) > 0 else 0
            )

        return df

    elif evento == "IRAS":
        ruta = os.path.join(DIRECTORIO, "iras_consolidado.csv")
        if not os.path.exists(ruta):
            return None
        df = pd.read_csv(ruta, low_memory=False)
        df = estandarizar_columnas(df)

        cols_ped = ["IRA_M2", "IRA_2_11", "IRA_1_4A"]
        for col in cols_ped:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            else:
                df[col] = 0

        df["TOTAL_CASOS"] = df["IRA_M2"] + df["IRA_2_11"] + df["IRA_1_4A"]
        return df

    return None


# Barra Lateral
st.sidebar.title("📊 Control Epidemiológico")
evento_seleccionado = st.sidebar.radio(
    "Seleccione Evento:", ["Febriles", "IRAS"]
)

# Cargar dataset
df = cargar_datos(evento_seleccionado)

if df is None:
    st.error(
        f"⚠️ No se encontró el archivo consolidado para **{evento_seleccionado}**. "
        f"Asegúrate de haber generado el archivo consolidado correspondiente."
    )
else:
    st.title(f"📈 Sala Situacional - {evento_seleccionado}")
    st.markdown("---")

    # Métrica de Años (Con conversión segura a entero)
    df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce")
    df = df.dropna(subset=["ANO"])
    df["ANO"] = df["ANO"].astype(int)

    anios_disponibles = sorted(df["ANO"].unique())
    anio_actual = max(anios_disponibles)
    anio_anterior = (
        anio_actual - 1
        if (anio_actual - 1) in anios_disponibles
        else anios_disponibles[-2]
        if len(anios_disponibles) > 1
        else anio_actual
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label=f"Total Casos {anio_actual}",
            value=int(
                df[df["ANO"] == anio_actual]["TOTAL_CASOS"].sum()
            ),
        )
    with col2:
        st.metric(
            label=f"Total Casos {anio_anterior}",
            value=int(
                df[df["ANO"] == anio_anterior]["TOTAL_CASOS"].sum()
            ),
        )

    # 1. Gráfico de Curva Semanal Comparativa
    st.subheader(
        f"Comparativo Semanal: {anio_anterior} vs {anio_actual}"
    )

    df_comp = (
        df[df["ANO"].isin([anio_anterior, anio_actual])]
        .groupby(["SEMANA", "ANO"])["TOTAL_CASOS"]
        .sum()
        .unstack()
    )

    st.line_chart(df_comp)

    # 2. Desglose por Grupos Etarios (Exclusivo IRAS)
    if evento_seleccionado == "IRAS":
        st.subheader(f"Desglose por Grupo Etario Pediátrico ({anio_actual})")

        df_act = df[df["ANO"] == anio_actual]
        m2 = df_act["IRA_M2"].sum()
        m11 = df_act["IRA_2_11"].sum()
        a4 = df_act["IRA_1_4A"].sum()

        datos_etarios = pd.DataFrame(
            {"Casos": [m2, m11, a4]},
            index=["< de 2 Meses", "2 a 11 Meses", "1 a 4 Años"],
        )

        st.bar_chart(datos_etarios)
