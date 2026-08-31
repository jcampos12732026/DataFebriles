import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="Sala Situacional Epidemiológica - C.S. César López Silva",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS generales
st.markdown(
    """
    <style>
    #MainMenu, header, footer, div[data-testid="stStatusWidget"] {visibility: hidden;}
    .stApp { background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%); color: #ffffff; }
    .block-container { padding: 2.5rem 1rem 1rem 1rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { width: 290px !important; min-width: 290px !important; background-color: #0d131d !important; }
    .unified-card-header {
        background: linear-gradient(145deg, #151c28, #1a2436);
        border: 2px solid #0056b3; border-radius: 10px; padding: 14px 10px;
        text-align: center; box-shadow: 0px 4px 12px rgba(0, 86, 179, 0.3); margin-bottom: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Helper: Cálculo de Semana Epidemiológica
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


# Carga genérica de archivos CSV
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

# Sidebar
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
        index=0,
    )

if os.path.exists("logo_minsa.png"):
    st.sidebar.image("logo_minsa.png", use_container_width=True)


# --- GRÁFICO GRUPOS ETARIOS (IRAS) ---
def renderizar_grafico_grupos_etarios(df, titulo_evento):
    cols_grupos = {
        "ira_m2": "Menores de 2 meses",
        "ira_2_11": "2-11 Meses",
        "ira_1_4a": "1-4 Años",
    }
    cols_presentes = [c for c in cols_grupos.keys() if c in df.columns]

    if not cols_presentes:
        return

    anios_disponibles = sorted(df["año"].unique())
    max_anio = max(anios_disponibles) if anios_disponibles else hoy.year
    df_max = df[(df["año"] == max_anio) & (df["casos_totales"] > 0)]

    semana_max_data = (
        int(df_max["semana"].max())
        if not df_max.empty
        else semana_epidemiologica_actual
    )

    ultimos_dos_anios = (
        anios_disponibles[-2:]
        if len(anios_disponibles) >= 2
        else anios_disponibles
    )
    anios_sel = st.multiselect(
        "Seleccionar Año(s) - Grupo Etario:",
        anios_disponibles,
        default=ultimos_dos_anios,
        key="etario_multiselect",
    )

    df_filtrado = df[df["año"].isin(anios_sel)].copy()

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
    df_resumen["año_str"] = df_resumen["año"].astype(str)

    orden_categorias = ["Menores de 2 meses", "2-11 Meses", "1-4 Años"]

    st.markdown(
        f"#### Total de casos de {titulo_evento} por grupo etario - C.S. César"
        f" López Silva / RIS CHACLACAYO, {min(anios_sel)}-{max(anios_sel)}"
        f" (hasta la semana epidemiológica {semana_max_data})"
    )

    fig = px.bar(
        df_resumen,
        x="Grupo Etario",
        y="casos",
        color="año_str",
        barmode="group",
        text="casos",
        category_orders={"Grupo Etario": orden_categorias},
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
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=orden_categorias,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config=config_plotly)


# --- GRÁFICO TENDENCIA SE (FEBRILES Y GENERAL) ---
def renderizar_grafico_tendencia(df, titulo):
    st.subheader(f"📈 Tendencia Semanal de {titulo}")
    anios_disponibles = sorted(df["año"].unique())
    anios_sel = st.multiselect(
        "Seleccionar Año(s) para Tendencia:",
        anios_disponibles,
        default=anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles,
        key="tendencia_multiselect",
    )

    df_filt = df[df["año"].isin(anios_sel)]
    df_agrup = (
        df_filt.groupby(["semana", "año"])["casos_totales"].sum().reset_index()
    )
    df_agrup["año_str"] = df_agrup["año"].astype(str)

    fig = px.line(
        df_agrup,
        x="semana",
        y="casos_totales",
        color="año_str",
        markers=True,
        labels={
            "semana": "Semana Epidemiológica",
            "casos_totales": "Casos",
            "año_str": "Año",
        },
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=380,
        margin=dict(l=10, r=10, t=30, b=10),
    )

    st.plotly_chart(fig, use_container_width=True, config=config_plotly)


# --- RENDERIZADO POR MÓDULOS ---
if modulo_seleccionado == "🌡️ Febriles":
    st.title("🌡️ Sala Situacional de Febriles")
    df_feb = cargar_datos_csv("febriles_consolidado.csv", col_total_casos="feb_tot")

    if df_feb is not None:
        # Métricas principales
        max_anio = df_feb["año"].max()
        df_actual = df_feb[df_feb["año"] == max_anio]
        tot_casos = df_actual["casos_totales"].sum()

        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"Total Casos Febriles ({max_anio})", f"{int(tot_casos)}")
        with col2:
            st.metric("Semanas Registradas", f"{df_actual['semana'].nunique()}")

        st.markdown("---")
        renderizar_grafico_tendencia(df_feb, "Febriles")
    else:
        st.error("⚠️ No se encontró la data `febriles_consolidado.csv`.")

elif modulo_seleccionado == "🫁 IRAS":
    st.title("🫁 Sala Situacional de IRAS")
    df_iras = cargar_datos_csv("iras_consolidado.csv", col_total_casos="feb_tot")

    if df_iras is not None:
        renderizar_grafico_grupos_etarios(df_iras, "IRAs")
        st.markdown("---")
        renderizar_grafico_tendencia(df_iras, "IRAs")
    else:
        st.error("⚠️ No se encontró la data `iras_consolidado.csv`.")

elif modulo_seleccionado == "🦟 Dengue":
    st.title("🦟 Sala Situacional de Dengue")
    st.info("Módulo en construcción para Dengue.")
