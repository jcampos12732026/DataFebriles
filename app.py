import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Sala Situacional - C.S. César López Silva", layout="wide"
)


# Estandarización de columnas
def estandarizar_columnas(df):
    df.columns = [str(col).upper().strip() for col in df.columns]
    renombres = {"AÑO": "ANO", "ANIO": "ANO"}
    df.rename(columns=renombres, inplace=True)
    return df


# Carga de datos
@st.cache_data
def cargar_datos(evento):
    if evento == "Febriles":
        ruta = os.path.join(
            os.path.dirname(__file__), "febriles_consolidado.csv"
        )
        if not os.path.exists(ruta):
            return None
        df = pd.read_csv(ruta, low_memory=False)
        df = estandarizar_columnas(df)

        if "FEB_TOT" in df.columns:
            df["TOTAL_CASOS"] = pd.to_numeric(
                df["FEB_TOT"], errors="coerce"
            ).fillna(0)
        elif "TOTAL" in df.columns:
            df["TOTAL_CASOS"] = pd.to_numeric(
                df["TOTAL"], errors="coerce"
            ).fillna(0)
        else:
            cols_num = df.select_dtypes(include=["number"]).columns
            df["TOTAL_CASOS"] = df[cols_num[0]] if len(cols_num) > 0 else 0
        return df

    elif evento == "IRAS":
        ruta = os.path.join(os.path.dirname(__file__), "iras_consolidado.csv")
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


# Sidebar
st.sidebar.title("📌 Menú de Navegación")
evento = st.sidebar.radio(
    "Seleccione Evento Epidemiológico:", ["Febriles", "IRAS"]
)

df = cargar_datos(evento)

if df is None:
    st.error(f"⚠️ No se encontró el archivo consolidado para **{evento}**.")
else:
    # Limpieza de años
    df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce")
    df = df.dropna(subset=["ANO"])
    df["ANO"] = df["ANO"].astype(int)

    anios = sorted(df["ANO"].unique())
    anio_actual = max(anios)
    anio_anterior = anio_actual - 1 if (anio_actual - 1) in anios else anios[-2]

    # Encabezado Oficial MINSA
    st.markdown(
        f"### **Total de casos de {evento} por semana epidemiológica - C.S. César López Silva / RIS CHACLACAYO**"
    )
    st.caption(f"Años comparados: {anio_anterior} vs {anio_actual}")
    st.markdown("---")

    # Métricas KPI
    casos_act = int(df[df["ANO"] == anio_actual]["TOTAL_CASOS"].sum())
    casos_ant = int(df[df["ANO"] == anio_anterior]["TOTAL_CASOS"].sum())
    variacion = (
        ((casos_act - casos_ant) / casos_ant * 100) if casos_ant > 0 else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Casos {anio_anterior}", f"{casos_ant:,}")
    c2.metric(
        f"Casos {anio_actual}",
        f"{casos_act:,}",
        delta=f"{variacion:+.1f}% vs {anio_anterior}",
    )
    c3.metric(
        "Semanas Registradas",
        int(df[df["ANO"] == anio_actual]["SEMANA"].max()),
    )

    # 1. Gráfico Comparativo Semanal (Líneas / Barras combinadas estilo dashboard Excel/MINSA)
    st.subheader(
        f"Curva Epidemiológica Semanal ({anio_anterior} vs {anio_actual})"
    )

    df_sem = (
        df[df["ANO"].isin([anio_anterior, anio_actual])]
        .groupby(["SEMANA", "ANO"])["TOTAL_CASOS"]
        .sum()
        .reset_index()
    )

    fig_sem = go.Figure()

    # Año Anterior (Línea Azul con marcadores)
    df_ant_data = df_sem[df_sem["ANO"] == anio_anterior]
    fig_sem.add_trace(
        go.Scatter(
            x=df_ant_data["SEMANA"],
            y=df_ant_data["TOTAL_CASOS"],
            mode="lines+markers+text",
            name=str(anio_anterior),
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=6),
            text=df_ant_data["TOTAL_CASOS"],
            textposition="top center",
        )
    )

    # Año Actual (Barras Naranjas / Color de alerta)
    df_act_data = df_sem[df_sem["ANO"] == anio_actual]
    fig_sem.add_trace(
        go.Bar(
            x=df_act_data["SEMANA"],
            y=df_act_data["TOTAL_CASOS"],
            name=str(anio_actual),
            marker_color="#d95f02",
            opacity=0.8,
            text=df_act_data["TOTAL_CASOS"],
            textposition="auto",
        )
    )

    fig_sem.update_layout(
        xaxis=dict(title="Semana Epidemiológica", dtick=1),
        yaxis=dict(title="Número de Casos"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20),
        height=420,
    )
    st.plotly_chart(fig_sem, use_container_width=True)

    # 2. Desglose Etario
    if evento == "IRAS":
        st.subheader(f"Casos por Grupo Etario Pediátrico ({anio_actual})")

        df_act_full = df[df["ANO"] == anio_actual]
        m2 = df_act_full["IRA_M2"].sum()
        m11 = df_act_full["IRA_2_11"].sum()
        a4 = df_act_full["IRA_1_4A"].sum()

        df_etario = pd.DataFrame(
            {
                "Grupo Etario": [
                    "< de 2 Meses",
                    "2 a 11 Meses",
                    "1 a 4 Años",
                ],
                "Casos": [m2, m11, a4],
            }
        )

        fig_et = px.bar(
            df_etario,
            x="Grupo Etario",
            y="Casos",
            text="Casos",
            color="Grupo Etario",
            color_discrete_sequence=["#2b5c8f", "#d95f02", "#1f77b4"],
        )
        fig_et.update_traces(
            textposition="outside", texttemplate="%{text:.0f}"
        )
        fig_et.update_layout(
            showlegend=False, height=350, margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_et, use_container_width=True)
