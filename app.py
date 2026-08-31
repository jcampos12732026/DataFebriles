import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. Configuración de página
st.set_page_config(
    page_title="Sala Situacional Epidemiológica - C.S. César López Silva",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Estilos CSS con Identidad Institucional MINSA y Mejora de Tablas
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}

    .stApp {
        background: radial-gradient(ellipse at bottom, #0d1b2a 0%, #080d1a 100%);
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
        background-color: #060a12 !important;
    }

    .unified-card-header {
        background: linear-gradient(145deg, #002244, #003366);
        border: 2px solid #0056b3;
        border-radius: 10px;
        padding: 14px 10px;
        text-align: center;
        box-shadow: 0px 4px 12px rgba(0, 86, 179, 0.4);
        margin-bottom: 15px;
        margin-top: 10px;
    }

    span[data-baseweb="tag"] {
        background-color: #d90429 !important;
        border-radius: 4px !important;
        padding: 1px 5px !important;
        font-size: 11px !important;
    }

    /* Estilo profesional para dataframes en Streamlit */
    dataframe, [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #0056b3;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# 3. Función para calcular la Semana Epidemiológica
def obtener_semana_epidemiologica(fecha):
    primer_dia = datetime(fecha.year, 1, 1)
    dias_hasta_domingo = (6 - primer_dia.weekday()) % 7
    primer_domingo = primer_dia + timedelta(days=dias_hasta_domingo)

    if fecha < primer_domingo:
        return obtener_semana_epidemiologica(datetime(fecha.year - 1, 12, 31))

    dias_transcurridos = (fecha - primer_domingo).days
    semana = (dias_transcurridos // 7) + 1
    return semana


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


# 4. Carga y procesamiento de datos específicos para IRAS
def cargar_datos_iras():
    nombre_archivo = "iras_consolidado.csv"
    if not os.path.exists(nombre_archivo):
        if os.path.exists("iras.csv"):
            nombre_archivo = "iras.csv"
        else:
            return None

    df = pd.read_csv(nombre_archivo)
    df.columns = df.columns.str.strip().str.lower()

    if "ano" in df.columns:
        df = df.rename(columns={"ano": "año"})

    cols_iras = ["ira_m2", "ira_2_11", "ira_1_4a"]
    for col in cols_iras:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if all(col in df.columns for col in cols_iras):
        df["casos_totales"] = df["ira_m2"] + df["ira_2_11"] + df["ira_1_4a"]
    else:
        posibles_cols = [
            c
            for c in df.columns
            if "tot" in c or "casos" in c or "num" in c
        ]
        target_col = posibles_cols[0] if posibles_cols else df.columns[-1]
        df[target_col] = pd.to_numeric(df[target_col], errors="coerce").fillna(
            0
        )
        df["casos_totales"] = df[target_col]

    cols_a_convertir = ["semana", "año", "mes"]
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

    return df


config_plotly = {"displayModeBar": "hover"}
hoy = datetime.now()
semana_epidemiologica_actual = obtener_semana_epidemiologica(hoy)

df = cargar_data_iras = cargar_datos_iras()

# --- BARRA LATERAL EXCLUSIVA IRAS ---
with st.sidebar:
    st.markdown(
        "<h4 style='color:#ffffff; font-size: 14px; font-weight: bold; margin-bottom: 5px;'>📡 Módulo Activo</h4>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="background: linear-gradient(145deg, #002244, #003366); border: 2px solid #0056b3; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px;">
            <span style="color: #00CCFF; font-weight: bold; font-size: 15px;">🫁 Infecciones Respiratorias Agudas (IRAS)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

if df is not None and not df.empty and "año" in df.columns:
    max_anio_data_t = int(df["año"].max())
    df_max_anio_t = df[df["año"] == max_anio_data_t]
    df_con_casos_t = df_max_anio_t[df_max_anio_t["casos_totales"] > 0]
    if not df_con_casos_t.empty and pd.notna(df_con_casos_t["semana"].max()):
        max_semana_real_t = int(df_con_casos_t["semana"].max())
    else:
        max_semana_v = (
            df_max_anio_t["semana"].max() if not df_max_anio_t.empty else 1
        )
        max_semana_real_t = int(max_semana_v) if pd.notna(max_semana_v) else 1
    brecha_semanas_t = semana_epidemiologica_actual - max_semana_real_t
else:
    max_anio_data_t = hoy.year
    max_semana_real_t = semana_epidemiologica_actual
    brecha_semanas_t = 0

with st.sidebar:
    st.markdown(
        f"""
        <div class="unified-card-header">
            <h4 style="margin:0; color:#00CCFF; font-size: 13px; font-weight: bold; text-transform: uppercase;">Semana Actual</h4>
            <h1 style="font-size: 52px; margin: 0px; color: #ffcc00; font-weight: 900; line-height: 1;">SE {semana_epidemiologica_actual}</h1>
            <p style="margin:4px 0 0 0; color:#ffffff; font-size: 16px; font-weight: 700;">Año: {hoy.year}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if brecha_semanas_t > 0:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(61, 12, 17, 0.95), rgba(92, 29, 36, 0.95)); border-left: 5px solid #D90429; border-radius: 6px; padding: 12px 14px; margin-bottom: 15px; box-shadow: 0px 4px 15px rgba(217, 4, 4, 0.25);">
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span style="font-size: 14px; margin-right: 6px;">⚠️</span>
                    <h4 style="margin: 0; color: #ff8093; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Brecha (IRAS)</h4>
                </div>
                <p style="margin: 0; color: #f1f1f1; font-size: 11px; line-height: 1.4;">
                    SE actual: <b>{semana_epidemiologica_actual}</b><br>
                    Último registro: <b>SE {max_semana_real_t}</b> ({max_anio_data_t})<br>
                    Desfase: <b style="color: #ff8093;">{brecha_semanas_t} semana(s)</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(10, 51, 26, 0.95), rgba(17, 92, 42, 0.95)); border-left: 5px solid #00FF66; border-radius: 6px; padding: 12px 14px; margin-bottom: 15px; box-shadow: 0px 4px 15px rgba(0, 255, 102, 0.2);">
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span style="font-size: 14px; margin-right: 6px;">✅</span>
                    <h4 style="margin: 0; color: #80ffb2; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Sincronizado (IRAS)</h4>
                </div>
                <p style="margin: 0; color: #f1f1f1; font-size: 11px; line-height: 1.4;">
                    Información al día en <b>SE {max_semana_real_t}</b> del período {max_anio_data_t}.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if os.path.exists("logo_minsa.png"):
    st.image("logo_minsa.png", use_container_width=True)
else:
    st.markdown(
        '<div style="background-color:#003366; color:white; font-weight:bold; padding:10px; text-align:center; border-radius:6px; margin-bottom: 10px;">PERÚ Ministerio de Salud | Diris Lima Este | RIS Chaclacayo | C.S. CÉSAR LÓPEZ SILVA</div>',
        unsafe_allow_html=True,
    )

st.title("🫁 Sala Situacional - Vigilancia Epidemiológica de IRAS")
st.divider()

if df is None or df.empty:
    st.warning(
        "⚠️ No se encontró el archivo de datos de IRAS (`iras_consolidado.csv` o `iras.csv`)."
    )
else:
    max_anio_data = int(df["año"].max())
    df_max_anio = df[df["año"] == max_anio_data]
    df_con_casos = df_max_anio[df_max_anio["casos_totales"] > 0]

    max_semana_real_data = (
        int(df_con_casos["semana"].max())
        if not df_con_casos.empty and pd.notna(df_con_casos["semana"].max())
        else 1
    )
    max_mes_num_real_data = (
        int(df_con_casos["mes_num"].max())
        if not df_con_casos.empty and pd.notna(df_con_casos["mes_num"].max())
        else 1
    )
    max_mes_num_real_data = max(1, min(12, max_mes_num_real_data))

    orden_meses = [
        "Enero",
        "Feb",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Setiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    max_mes_nombre_real_data = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Setiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ][max_mes_num_real_data - 1]

    anios_disponibles = sorted(df["año"].unique())
    ultimos_dos_anios = (
        anios_disponibles[-2:]
        if len(anios_disponibles) >= 2
        else anios_disponibles
    )

    # =========================================================================
    # GRÁFICO 1 & 2 (Fila Superior): Episodios Semanales & Mensualizados
    # =========================================================================
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📊 1. Episodios Semanales")
        anios_g1 = st.multiselect(
            "Seleccionar Año(s) - Semanal:",
            anios_disponibles,
            default=ultimos_dos_anios,
            key="iras_g1_anios",
        )
        corte_acumulado_g1 = st.checkbox(
            f"Acumulado hasta SE {max_semana_real_data}",
            value=True,
            key="iras_chk_g1",
        )

        df_g1 = df[df["año"].isin(anios_g1)].copy()
        if not df_g1.empty:
            df_sem = (
                df_g1.groupby(["semana", "año"])["casos_totales"]
                .sum()
                .reset_index()
            )
            if corte_acumulado_g1 and max_anio_data in anios_g1:
                df_sem = df_sem[
                    ~(
                        (df_sem["año"] == max_anio_data)
                        & (df_sem["semana"] > max_semana_real_data)
                    )
                ]

            fig_sem = px.line(
                df_sem,
                x="semana",
                y="casos_totales",
                color="año",
                markers=True,
                template="plotly_dark",
                labels={"semana": "Semana Epidemiológica", "casos_totales": "Casos"},
                color_discrete_sequence=["#0056B3", "#00CCFF", "#FF9100", "#D90429"],
            )
            fig_sem.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(
                fig_sem, use_container_width=True, config=config_plotly
            )

    with col_g2:
        st.subheader("📅 2. Episodios Mensualizados")
        anios_mes_sel = st.multiselect(
            "Año(s) - Mensual:",
            anios_disponibles,
            default=ultimos_dos_anios,
            key="iras_g2_anios",
        )
        corte_acumulado_m = st.checkbox(
            f"Acumulado hasta {max_mes_nombre_real_data}",
            value=True,
            key="iras_chk_m",
        )

        df_mes_base = df[df["año"].isin(anios_mes_sel)].copy()
        if corte_acumulado_m and max_anio_data in anios_mes_sel:
            df_mes_base = df_mes_base[
                ~(
                    (df_mes_base["año"] == max_anio_data)
                    & (df_mes_base["mes_num"] > max_mes_num_real_data)
                )
            ]

        if not df_mes_base.empty:
            df_mes = (
                df_mes_base.groupby(["mes_nom", "mes_num", "año"])[
                    "casos_totales"
                ]
                .sum()
                .reset_index()
            )
            df_mes = df_mes.sort_values("mes_num")

            fig_mes = px.bar(
                df_mes,
                x="mes_nom",
                y="casos_totales",
                color="año",
                barmode="group",
                template="plotly_dark",
                labels={"mes_nom": "Mes", "casos_totales": "Casos"},
                color_discrete_sequence=["#0056B3", "#00CCFF", "#FF9100", "#D90429"],
            )
            fig_mes.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(
                fig_mes, use_container_width=True, config=config_plotly
            )

    st.divider()

    # =========================================================================
    # GRÁFICO 3 & 4 (Fila Media): Tendencia Anual & Comparativo Reciente
    # =========================================================================
    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.subheader("📉 3. Tendencia Anual vs. Promedios")
        df_totales_anuales = (
            df.groupby("año", as_index=False)["casos_totales"]
            .sum()
            .sort_values("año")
        )
        if not df_totales_anuales.empty:
            promedio_total = df_totales_anuales["casos_totales"].mean()

            fig_hist = px.bar(
                df_totales_anuales,
                x="año",
                y="casos_totales",
                text="casos_totales",
                template="plotly_dark",
                labels={"año": "Año", "casos_totales": "Casos Totales"},
                color_discrete_sequence=["#0077B6"],
            )
            fig_hist.add_hline(
                y=promedio_total,
                line_dash="dash",
                line_color="#00FF66",
                annotation_text=f"Promedio: {int(promedio_total):,}",
                annotation_position="top left",
                annotation_font_color="#00FF66",
            )
            fig_hist.update_traces(textposition="auto")
            fig_hist.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(
                fig_hist, use_container_width=True, config=config_plotly
            )

    with col_g4:
        st.subheader("📈 4. Comparativo de Últimas Semanas")
        semanas_disp = sorted(
            df_max_anio[df_max_anio["casos_totales"] > 0]["semana"].unique()
        )
        semanas_ultimas = (
            semanas_disp[-2:]
            if len(semanas_disp) >= 2
            else (semanas_disp if semanas_disp else [semana_epidemiologica_actual])
        )

        df_comp = df[
            (df["año"].isin(ultimos_dos_anios))
            & (df["semana"].isin(semanas_ultimas))
        ].copy()
        df_comp["año_str"] = df_comp["año"].astype(str)

        if not df_comp.empty:
            df_comp_grp = (
                df_comp.groupby(["semana", "año_str"])["casos_totales"]
                .sum()
                .reset_index()
            )
            fig_ult = px.bar(
                df_comp_grp,
                x="semana",
                y="casos_totales",
                color="año_str",
                barmode="group",
                text="casos_totales",
                template="plotly_dark",
                labels={
                    "semana": "Semana",
                    "casos_totales": "Casos",
                    "año_str": "Año",
                },
                color_discrete_sequence=["#0056B3", "#D90429"],
            )
            fig_ult.update_traces(textposition="auto")
            fig_ult.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(
                fig_ult, use_container_width=True, config=config_plotly
            )

    st.divider()

    # =========================================================================
    # GRÁFICO 5 & TABLA ESTILIZADA (Fila Inferior): Grupos Etarios IRAS
    # =========================================================================
    cols_iras = ["ira_m2", "ira_2_11", "ira_1_4a"]
    if all(c in df.columns for c in cols_iras):
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(0, 34, 68, 0.8), rgba(10, 25, 47, 0.95)); border-left: 5px solid #FF9100; border-top: 1px solid rgba(0, 204, 255, 0.2); border-right: 1px solid rgba(0, 204, 255, 0.2); border-bottom: 1px solid rgba(0, 204, 255, 0.2); padding: 12px 18px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.3);">
                <h3 style='color: #00CCFF; margin: 0; font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>
                    👶 5. Distribución Estratificada por Grupos Etarios (IRAS - Menores de 5 Años)
                </h3>
                <p style='color: #cbd5e1; margin: 4px 0 0 0; font-size: 12px;'>
                    Comportamiento histórico apilado con alto contraste clínico (Rojo alerta, Naranja y Azul institucional) - C.S. César López Silva
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        df_et_sum = (
            df.groupby("año")[["ira_m2", "ira_2_11", "ira_1_4a"]]
            .sum()
            .reset_index()
        )

        if not df_et_sum.empty:
            df_et_sum["total_anual"] = (
                df_et_sum["ira_m2"]
                + df_et_sum["ira_2_11"]
                + df_et_sum["ira_1_4a"]
            )

            fig_et = px.bar(
                df_et_sum,
                x="año",
                y=["ira_m2", "ira_2_11", "ira_1_4a"],
                barmode="stack",
                template="plotly_dark",
                labels={
                    "value": "Total de Episodios",
                    "año": "Año de Registro",
                    "variable": "Grupo etario",
                },
                color_discrete_map={
                    "ira_m2": "#D90429",  # Rojo intenso clínico (< de 2 Meses)
                    "ira_2_11": "#FF9100",  # Naranja dinámico alerta (2M a 11 Meses)
                    "ira_1_4a": "#0077B6",  # Azul institucional (1 a 4 Años)
                },
            )

            nombres_leyenda = {
                "ira_m2": "< de 2 Meses (Alto Riesgo)",
                "ira_2_11": "2M a 11 Meses",
                "ira_1_4a": "1 a 4 Años",
            }
            for serie in fig_et.data:
                if serie.name in nombres_leyenda:
                    serie.name = nombres_leyenda[serie.name]

            fig_et.add_trace(
                go.Scatter(
                    x=df_et_sum["año"],
                    y=df_et_sum["total_anual"],
                    mode="text",
                    text=df_et_sum["total_anual"],
                    textposition="top center",
                    textfont=dict(
                        size=12,
                        color="#FFCC00",
                        family="sans-serif",
                        weight="bold",
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

            fig_et.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=420,
                margin=dict(l=20, r=20, t=30, b=10),
                xaxis=dict(type="category", dtick=1, showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.04,
                    xanchor="right",
                    x=1,
                ),
            )

            st.plotly_chart(
                fig_et, use_container_width=True, config=config_plotly
            )

            # Tabla Resumen Estilizada con Fondo Profesional
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, rgba(13, 27, 42, 0.95), rgba(5, 13, 26, 0.98)); padding: 16px; border-radius: 8px; border: 1px solid rgba(0, 119, 182, 0.5); box-shadow: 0 4px 15px rgba(0,0,0,0.5); margin-top: 15px;">
                    <p style='font-size: 13px; font-weight: bold; color: #00CCFF; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.5px;'>
                        📋 Matriz Estadística Oficial por Grupo Etario (IRAS)
                    </p>
                """,
                unsafe_allow_html=True,
            )

            df_tabla = df_et_sum.set_index("año")[
                ["ira_m2", "ira_2_11", "ira_1_4a", "total_anual"]
            ].T
            df_tabla.index = [
                "< de 2 Meses",
                "2M a 11 Meses",
                "1 a 4 Años",
                "TOTAL GENERAL",
            ]

            st.dataframe(df_tabla, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
