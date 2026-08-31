import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ocultar barra superior, menú y pie de página
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Configuración de página
st.set_page_config(
    page_title="Sala Situacional Epidemiológica - C.S. César López Silva",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
        color: #ffffff;
    }
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    [data-testid="stSidebar"] {
        width: 290px !important;
        min-width: 290px !important;
        background-color: #0d131d !important;
    }
    .unified-card-header {
        background: linear-gradient(145deg, #151c28, #1a2436);
        border: 2px solid #0056b3;
        border-radius: 10px;
        padding: 14px 10px;
        text-align: center;
        box-shadow: 0px 4px 12px rgba(0, 86, 179, 0.3);
        margin-bottom: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def obtener_semana_epidemiologica(fecha):
    primer_dia = datetime(fecha.year, 1, 1)
    dias_hasta_domingo = (6 - primer_dia.weekday()) % 7
    primer_domingo = primer_dia + timedelta(days=dias_hasta_domingo)
    if fecha < primer_domingo:
        return obtener_semana_epidemiologica(datetime(fecha.year - 1, 12, 31))
    return ((fecha - primer_domingo).days // 7) + 1


meses_nombre = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Setiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def cargar_datos_csv(nombre_archivo, col_total_casos="feb_tot"):
    if not os.path.exists(nombre_archivo):
        return None
    df = pd.read_csv(nombre_archivo)
    df.columns = df.columns.str.strip().str.lower()

    if "ano" in df.columns:
        df = df.rename(columns={"ano": "año"})

    cols_etarios = ["ira_m2", "ira_2_11", "ira_1_4a"]
    for col in cols_etarios:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if col_total_casos not in df.columns:
        posibles_cols = [
            c
            for c in df.columns
            if "tot" in c or "ira" in c or "casos" in c or "num" in c
        ]
        if posibles_cols:
            col_total_casos = posibles_cols[0]

    cols_a_convertir = [col_total_casos, "semana", "año", "mes"]
    for col in cols_a_convertir:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["año"] = df["año"].astype(int)
    df["semana"] = df["semana"].astype(int)

    if "mes" in df.columns:
        df["mes_num"] = df["mes"].astype(int)
        df["mes_nom"] = df["mes_num"].map(meses_nombre).fillna("Desconocido")
    elif "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df["mes_num"] = df["fecha"].dt.month
        df["mes_nom"] = df["mes_num"].map(meses_nombre).fillna("Desconocido")
    else:
        df["mes_num"] = (
            ((df["semana"] - 1) // 4.33 + 1).astype(int).clip(1, 12)
        )
        df["mes_nom"] = df["mes_num"].map(meses_nombre)

    if all(c in df.columns for c in cols_etarios):
        df["casos_totales"] = df["ira_m2"] + df["ira_2_11"] + df["ira_1_4a"]
    else:
        df["casos_totales"] = (
            df[col_total_casos] if col_total_casos in df.columns else 0
        )

    return df


config_plotly = {"displayModeBar": "hover"}
hoy = datetime.now()
semana_epidemiologica_actual = obtener_semana_epidemiologica(hoy)

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(
        f"""
        <div class="unified-card-header">
            <h4 style="margin:0; color:#4da6ff; font-size: 13px; font-weight: bold; text-transform: uppercase;">Semana Actual</h4>
            <h1 style="font-size: 52px; margin: 0px; color: #ffcc00; font-weight: 900; line-height: 1;">SE {semana_epidemiologica_actual}</h1>
            <p style="margin:4px 0 0 0; color:#ffffff; font-size: 16px; font-weight: 700;">Año: {hoy.year}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    modulo_seleccionado = st.radio(
        "Seleccionar Módulo:",
        ["🌡️ Febriles", "🫁 IRAS", "🦟 Dengue"],
        index=1,
    )

if os.path.exists("logo_minsa.png"):
    st.image("logo_minsa.png", use_container_width=True)


# RENDERIZADOR DE GRÁFICO POR GRUPOS ETARIOS CON FILTROS
def renderizar_grafico_grupos_etarios(df, titulo_evento):
    cols_grupos = {
        "ira_m2": "Menores de 2 meses",
        "ira_2_11": "2-11 Meses",
        "ira_1_4a": "1-4 Años",
    }
    cols_presentes = [c for c in cols_grupos.keys() if c in df.columns]

    if not cols_presentes:
        return

    st.subheader(f"👶 Total de casos de {titulo_evento} por grupo etario")

    anios_disponibles = sorted(df["año"].unique())
    ultimos_dos_anios = (
        anios_disponibles[-2:]
        if len(anios_disponibles) >= 2
        else anios_disponibles
    )

    max_anio = max(anios_disponibles) if anios_disponibles else hoy.year
    df_max = df[df["año"] == max_anio]
    semana_corte = (
        int(df_max[df_max["casos_totales"] > 0]["semana"].max())
        if not df_max.empty
        else semana_epidemiologica_actual
    )

    # Selector de Años y Checkbox de Corte
    col_f1, col_f2 = st.columns([1.5, 1])
    with col_f1:
        anios_sel = st.multiselect(
            "Seleccionar Año(s) - Grupo Etario:",
            anios_disponibles,
            default=ultimos_dos_anios,
            key="etario_multiselect",
        )
    with col_f2:
        st.markdown(
            "<div style='height: 22px;'></div>", unsafe_allow_html=True
        )
        aplicar_corte = st.checkbox(
            f"Acumulado hasta SE {semana_corte} ({max_anio})",
            value=True,
            key="etario_corte_chk",
        )

    # Filtrar datos
    df_filtrado = df[df["año"].isin(anios_sel)].copy()
    if aplicar_corte:
        df_filtrado = df_filtrado[df_filtrado["semana"] <= semana_corte]

    if df_filtrado.empty:
        st.warning(
            "No hay datos para mostrar con los filtros seleccionados."
        )
        return

    df_etario = df_filtrado.melt(
        id_vars=["año"],
        value_vars=cols_presentes,
        var_name="grupo_raw",
        value_name="casos",
    )
    df_etario["Grupo Etario"] = df_etario["grupo_raw"].map(cols_grupos)

    df_resumen = (
        df_etario.groupby(["Grupo Etario", "año"])["casos"].sum().reset_index()
    )
    df_resumen = df_resumen[df_resumen["casos"] > 0]
    df_resumen["año_str"] = df_resumen["año"].astype(str)

    fig = px.bar(
        df_resumen,
        x="Grupo Etario",
        y="casos",
        color="año_str",
        barmode="group",
        text="casos",
        category_orders={
            "Grupo Etario": ["Menores de 2 meses", "2-11 Meses", "1-4 Años"]
        },
        color_discrete_sequence=["#4169E1", "#FF7F0E", "#2CA02C"],
        labels={"casos": "Casos", "año_str": "Año"},
    )

    fig.update_traces(
        textposition="outside",
        textfont=dict(size=14, color="white", weight="bold"),
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="",
        yaxis_title="Total de Casos",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config=config_plotly)


# MOSTRAR MÓDULO
if modulo_seleccionado == "🫁 IRAS":
    df = cargar_datos_csv("iras_consolidado.csv")
    if df is not None:
        renderizar_grafico_grupos_etarios(df, "IRAs")
    else:
        st.error("⚠️ No se encontró el archivo `iras_consolidado.csv`.")
