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


# 4. Carga y procesamiento de datos
def cargar_datos_csv(nombre_archivo, col_total_casos=None):
    if not os.path.exists(nombre_archivo):
        return None
    df = pd.read_csv(nombre_archivo)
    df.columns = df.columns.str.strip().str.lower()

    if "ano" in df.columns:
        df = df.rename(columns={"ano": "año"})

    cols_iras = ["ira_m2", "ira_2_11", "ira_1_4a"]
    tiene_cols_iras = all(col in df.columns for col in cols_iras)

    if tiene_cols_iras:
        for col in cols_iras:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df["casos_totales"] = df["ira_m2"] + df["ira_2_11"] + df["ira_1_4a"]
    else:
        if col_total_casos and col_total_casos in df.columns:
            target_col = col_total_casos
        else:
            posibles_cols = [
                c
                for c in df.columns
                if "tot" in c or "feb" in c or "casos" in c or "num" in c
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


# --- BARRA LATERAL UNIFICADA ---
with st.sidebar:
    st.markdown(
        "<h4 style='color:#ffffff; font-size: 14px; font-weight: bold; margin-bottom: 5px;'>📡 Evento Epidemiológico</h4>",
        unsafe_allow_html=True,
    )

    modulo_seleccionado = st.radio(
        "Seleccionar Módulo:",
        ["🌡️ Febriles", "🫁 IRAS", "🦟 Dengue (Próximamente)"],
        index=0,
        key="radio_modulo_unico",
        label_visibility="collapsed",
    )

if "Febriles" in modulo_seleccionado:
    df_actual_temp = cargar_datos_csv(
        "febriles_consolidado.csv", col_total_casos="feb_tot"
    )
    titulo_evento_temp = "Febriles"
elif "IRAS" in modulo_seleccionado:
    df_actual_temp = cargar_datos_csv("iras_consolidado.csv")
    if df_actual_temp is None and os.path.exists("iras.csv"):
        df_actual_temp = cargar_datos_csv("iras.csv")
    titulo_evento_temp = "IRAS"
else:
    df_actual_temp = None
    titulo_evento_temp = "Dengue"

if (
    df_actual_temp is not None
    and not df_actual_temp.empty
    and "año" in df_actual_temp.columns
):
    max_anio_data_t = int(df_actual_temp["año"].max())
    df_max_anio_t = df_actual_temp[df_actual_temp["año"] == max_anio_data_t]
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
                    <h4 style="margin: 0; color: #ff8093; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Brecha ({titulo_evento_temp})</h4>
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
                    <h4 style="margin: 0; color: #80ffb2; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Sincronizado ({titulo_evento_temp})</h4>
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


# --- 5TO GRÁFICO: GRUPOS ETARIOS APILADOS CON ALTO CONTRASTE (ROJO, NARANJA, AZUL) + TABLA ESTILIZADA ---
def renderizar_quinto_grafico_iras(df):
    cols_iras = ["ira_m2", "ira_2_11", "ira_1_4a"]
    if not all(c in df.columns for c in cols_iras):
        return

    st.divider()
    
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(0, 34, 68, 0.8), rgba(10, 25, 47, 0.95)); border-left: 5px solid #FF9100; border-top: 1px solid rgba(0, 204, 255, 0.2); border-right: 1px solid rgba(0, 204, 255, 0.2); border-bottom: 1px solid rgba(0, 204, 255, 0.2); padding: 12px 18px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.3);">
            <h3 style='color: #00CCFF; margin: 0; font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>
                👶 Distribución Estratificada por Grupos Etarios (IRAS - Menores de 5 Años)
            </h3>
            <p style='color: #cbd5e1; margin: 4px 0 0 0; font-size: 12px;'>
                Comportamiento histórico apilado con alto contraste de riesgo clínico - C.S. César López Silva
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_et_sum = (
        df.groupby("año")[["ira_m2", "ira_2_11", "ira_1_4a"]].sum().reset_index()
    )

    if not df_et_sum.empty:
        df_et_sum["total_anual"] = df_et_sum["ira_m2"] + df_et_sum["ira_2_11"] + df_et_sum["ira_1_4a"]

        # Paleta de alto contraste profesional: Rojo intenso (máxima vulnerabilidad), Naranja alerta y Azul institucional
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
                "ira_m2": "#D90429",    # Rojo intenso alerta (< de 2 Meses)
                "ira_2_11": "#FF9100",  # Naranja dinámico (2M a 11 Meses)
                "ira_1_4a": "#0077B6",  # Azul sólido corporativo (1 a 4 Años)
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

        # Etiqueta de total general en la parte superior
        fig_et.add_trace(
            go.Scatter(
                x=df_et_sum["año"],
                y=df_et_sum["total_anual"],
                mode="text",
                text=df_et_sum["total_anual"],
                textposition="top center",
                textfont=dict(size=12, color="#FFCC00", family="sans-serif", weight="bold"),
                showlegend=False,
                hoverinfo="skip"
            )
        )

        fig_et.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=460,
            margin=dict(l=20, r=20, t=40, b=10),
            xaxis=dict(type="category", dtick=1, showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1
            ),
        )

        st.plotly_chart(
            fig_et, use_container_width=True, config={"displayModeBar": "hover"}
        )

        # TABLA ESTILIZADA CON FONDO Y CONTENEDOR PROFESIONAL
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(13, 27, 42, 0.9), rgba(5, 13, 26, 0.95)); padding: 15px; border-radius: 8px; border: 1px solid rgba(0, 119, 182, 0.4); box-shadow: 0 4px 12px rgba(0,0,0,0.4); margin-top: 15px;">
                <p style='font-size: 13px; font-weight: bold; color: #00CCFF; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 0.5px;'>
                    📋 Consolidado Estadístico Oficial por Grupo Etario y Año (IRAS)
                </p>
            """,
            unsafe_allow_html=True,
        )
        
        df_tabla = df_et_sum.set_index("año")[["ira_m2", "ira_2_11", "ira_1_4a", "total_anual"]].T
        df_tabla.index = ["< de 2 Meses", "2M a 11 Meses", "1 a 4 Años", "TOTAL GENERAL"]
        
        st.dataframe(df_tabla, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


# 6. Función Renderizadora Principal
def renderizar_dashboard(df, titulo_evento, key_prefix):
    if df.empty or "año" not in df.columns:
        st.warning(
            f"⚠️ El conjunto de datos de {titulo_evento} está vacío o no tiene la columna 'año'."
        )
        return

    max_anio_data = int(df["año"].max())
    df_max_anio = df[df["año"] == max_anio_data]
    df_con_casos = df_max_anio[df_max_anio["casos_totales"] > 0]

    if not df_con_casos.empty and pd.notna(df_con_casos["semana"].max()):
        max_semana_real_data = int(df_con_casos["semana"].max())
    else:
        max_semana_val = (
            df_max_anio["semana"].max() if not df_max_anio.empty else 1
        )
        max_semana_real_data = (
            int(max_semana_val) if pd.notna(max_semana_val) else 1
        )

    if not df_con_casos.empty and pd.notna(df_con_casos["mes_num"].max()):
        max_mes_num_real_data = int(df_con_casos["mes_num"].max())
    else:
        max_mes_val = (
            df_max_anio["mes_num"].max() if not df_max_anio.empty else 1
        )
        max_mes_num_real_data = (
            int(max_mes_val) if pd.notna(max_mes_val) else 1
        )

    max_mes_num_real_data = max(1, min(12, max_mes_num_real_data))

    orden_meses = [
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
    ]
    max_mes_nombre_real_data = orden_meses[max_mes_num_real_data - 1]

    anios_disponibles = sorted(df["año"].unique())
    ultimos_dos_anios = (
        anios_disponibles[-2:]
        if len(anios_disponibles) >= 2
        else anios_disponibles
    )

    # FILA 1: Episodios Semanales y Mensualizados
    col_mid, col_mes = st.columns([1.8, 1])

    with col_mid:
        st.subheader(f"📊 Episodios Semanales de {titulo_evento}")

        col_f1, col_f2 = st.columns([1.5, 1])
        with col_f1:
            anios_g1 = st.multiselect(
                "Seleccionar Año(s) - Semanal:",
                anios_disponibles,
                default=ultimos_dos_anios,
                key=f"{key_prefix}_g1_anios",
            )
        with col_f2:
            st.markdown(
                "<div style='height: 22px;'></div>", unsafe_allow_html=True
            )
            incluye_anio_actual_g1 = max_anio_data in anios_g1
            label_chk_g1 = f"Acumulado hasta SE {max_semana_real_data} ({max_anio_data})"
            corte_acumulado_g1 = st.checkbox(
                label_chk_g1,
                value=True if incluye_anio_actual_g1 else False,
                disabled=not incluye_anio_actual_g1,
                key=f"{key_prefix}_chk_corte_g1",
            )

        df_g1 = df[df["año"].isin(anios_g1)].copy()

        if not df_g1.empty:
            df_sem = (
                df_g1.groupby(["semana", "año"])["casos_totales"]
                .sum()
                .reset_index()
            )
            fig_sem = go.Figure()
            anios_en_datos = sorted(df_sem["año"].unique())
            max_anio_presente = (
                max(anios_en_datos) if anios_en_datos else max_anio_data
            )

            df_sem = df_sem.sort_values(by="semana")
            colores_barras = ["#0056B3", "#0088CC", "#4A90E2", "#6C757D"]

            if incluye_anio_actual_g1 and corte_acumulado_g1:
                df_sem = df_sem[df_sem["semana"] <= max_semana_real_data]

            idx_barra = 0
            for anio in anios_en_datos:
                if anio != max_anio_presente:
                    df_anio = df_sem[df_sem["año"] == anio]
                    fig_sem.add_trace(
                        go.Bar(
                            x=df_anio["semana"],
                            y=df_anio["casos_totales"],
                            name=str(anio),
                            marker_color=colores_barras[
                                idx_barra % len(colores_barras)
                            ],
                            opacity=0.75,
                            text=df_anio["casos_totales"],
                            textposition="auto",
                            textfont=dict(size=10, color="white"),
                        )
                    )
                    idx_barra += 1

            if max_anio_presente in anios_en_datos:
                df_ultimo = df_sem[df_sem["año"] == max_anio_presente]

                fig_sem.add_trace(
                    go.Scatter(
                        x=df_ultimo["semana"],
                        y=df_ultimo["casos_totales"],
                        name=f"{max_anio_presente} (Actual)",
                        mode="lines+markers+text",
                        text=df_ultimo["casos_totales"],
                        textposition="top center",
                        textfont=dict(
                            size=12,
                            color="#FFFFFF",
                            family="sans-serif",
                            weight="bold",
                        ),
                        line=dict(
                            shape="spline",
                            smoothing=1.3,
                            width=4,
                            color="#D90429",
                        ),
                        marker=dict(
                            size=8,
                            color="#D90429",
                            line=dict(width=2, color="#FFFFFF"),
                        ),
                    )
                )

            texto_corte_titulo_g1 = (
                f" (HASTA SE {max_semana_real_data})"
                if (incluye_anio_actual_g1 and corte_acumulado_g1)
                else " (AÑOS COMPLETOS)"
            )
            fig_sem.update_layout(
                title=f"TOTAL DE EPISODIOS SEMANALES DE {titulo_evento.upper()}{texto_corte_titulo_g1}",
                xaxis_title="N° de Semana Epidemiológica",
                yaxis_title="Casos",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=360,
                margin=dict(l=10, r=10, t=40, b=10),
                barmode="group",
                xaxis=dict(
                    type="category",
                    categoryorder="array",
                    categoryarray=list(range(1, 54)),
                    dtick=1,
                ),
                legend=dict(
                    orientation="v", yanchor="top", y=1, xanchor="left", x=1.02
                ),
            )
            st.plotly_chart(
                fig_sem, use_container_width=True, config=config_plotly
            )

    with col_mes:
        st.subheader("📅 Episodios Mensualizados")

        col_m1, col_m2 = st.columns([1.5, 1])
        with col_m1:
            anios_mes_sel = st.multiselect(
                "Año(s) - Mensual:",
                anios_disponibles,
                default=ultimos_dos_anios,
                key=f"{key_prefix}_g3_anios",
            )
        with col_m2:
            st.markdown(
                "<div style='height: 22px;'></div>", unsafe_allow_html=True
            )
            incluye_anio_actual_m = max_anio_data in anios_mes_sel
            label_chk_m = f"Acumulado hasta {max_mes_nombre_real_data} ({max_anio_data})"
            corte_acumulado_m = st.checkbox(
                label_chk_m,
                value=True if incluye_anio_actual_m else False,
                disabled=not incluye_anio_actual_m,
                key=f"{key_prefix}_chk_corte_mes",
            )

        df_mes_base = df[df["año"].isin(anios_mes_sel)].copy()
        if incluye_anio_actual_m and corte_acumulado_m:
            df_mes_base = df_mes_base[
                df_mes_base["mes_num"] <= max_mes_num_real_data
            ]

        if not df_mes_base.empty:
            df_mes = (
                df_mes_base.groupby(["mes_nom", "mes_num", "año"])[
                    "casos_totales"
                ]
                .sum()
                .reset_index()
            )
            meses_a_mostrar = (
                orden_meses[:max_mes_num_real_data]
                if (incluye_anio_actual_m and corte_acumulado_m)
                else orden_meses
            )
            df_mes["mes_nom"] = pd.Categorical(
                df_mes["mes_nom"], categories=meses_a_mostrar, ordered=True
            )
            df_mes = df_mes.dropna(subset=["mes_nom"]).sort_values("mes_nom")

            anios_seleccionados_ordenados = sorted(df_mes["año"].unique())
            max_anio_mes = (
                max(anios_seleccionados_ordenados)
                if anios_seleccionados_ordenados
                else None
            )

            fig_mes = go.Figure()
            colores_barras_inst = ["#0056B3", "#0088CC", "#4A90E2", "#6C757D"]

            for idx, anio in enumerate(anios_seleccionados_ordenados):
                if anio != max_anio_mes:
                    df_anio_m = df_mes[df_mes["año"] == anio]
                    fig_mes.add_trace(
                        go.Bar(
                            x=df_anio_m["mes_nom"],
                            y=df_anio_m["casos_totales"],
                            name=str(anio),
                            marker_color=colores_barras_inst[
                                idx % len(colores_barras_inst)
                            ],
                            opacity=0.8,
                            text=df_anio_m["casos_totales"],
                            textposition="auto",
                            textfont=dict(size=12, color="white"),
                        )
                    )

            if max_anio_mes is not None:
                df_ultimo_m = df_mes[df_mes["año"] == max_anio_mes]
                fig_mes.add_trace(
                    go.Scatter(
                        x=df_ultimo_m["mes_nom"],
                        y=df_ultimo_m["casos_totales"],
                        name=f"{max_anio_mes} (Actual)",
                        mode="lines+markers+text",
                        text=df_ultimo_m["casos_totales"],
                        textposition="top center",
                        textfont=dict(
                            size=13,
                            color="#D90429",
                            family="sans-serif",
                            weight="bold",
                        ),
                        line=dict(
                            shape="spline",
                            smoothing=1.3,
                            width=4,
                            color="#D90429",
                        ),
                        marker=dict(size=8, color="#D90429"),
                    )
                )

            rango_str = (
                f"DESDE EL AÑO {min(anios_mes_sel)} HASTA EL AÑO {max(anios_mes_sel)}"
                if len(anios_mes_sel) > 1
                else f"AÑO {min(anios_mes_sel)}"
                if anios_mes_sel
                else "SELECCIONADOS"
            )

            fig_mes.update_layout(
                title=f"COMPARATIVO DE {titulo_evento.upper()} MENSUALIZADOS {rango_str}",
                xaxis_title="Mes",
                yaxis_title="Casos",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=360,
                margin=dict(l=10, r=10, t=40, b=10),
                barmode="group",
                legend=dict(
                    orientation="v", yanchor="top", y=1, xanchor="left", x=1.02
                ),
            )
            st.plotly_chart(
                fig_mes, use_container_width=True, config=config_plotly
            )

    st.divider()

    # FILA 2: Evolución Anual (Izquierda) & Gráfico de la Derecha según el Módulo
    col_hist, col_right = st.columns([1.8, 1])

    with col_hist:
        st.subheader("📉 Evolución Anual vs. Promedios Históricos")

        df_totales_anuales = (
            df.groupby("año", as_index=False)["casos_totales"]
            .sum()
            .sort_values("año")
        )

        if not df_totales_anuales.empty:
            anio_min_total = int(df_totales_anuales["año"].min())
            anio_max_total = int(df_totales_anuales["año"].max())
            anios_totales_ord = sorted(df_totales_anuales["año"].unique())

            posiciones_texto = []
            cant_puntos = len(df_totales_anuales)

            for idx in range(cant_puntos):
                if idx == 0:
                    posiciones_texto.append("top right")
                elif idx == cant_puntos - 1:
                    posiciones_texto.append("top left")
                else:
                    posiciones_texto.append("top center")

            promedio_total = df_totales_anuales["casos_totales"].mean()

            ultimos_10 = anios_totales_ord[-10:]
            df_10 = df_totales_anuales[
                df_totales_anuales["año"].isin(ultimos_10)
            ]
            promedio_10_anios = df_10["casos_totales"].mean()
            anio_inicio_10 = int(min(ultimos_10))

            ultimos_5 = anios_totales_ord[-5:]
            df_5 = df_totales_anuales[df_totales_anuales["año"].isin(ultimos_5)]
            promedio_5_anios = df_5["casos_totales"].mean()
            anio_inicio_5 = int(min(ultimos_5))

            fig_hist = go.Figure()

            fig_hist.add_trace(
                go.Scatter(
                    x=df_totales_anuales["año"],
                    y=df_totales_anuales["casos_totales"],
                    mode="lines+markers+text",
                    name="Casos Anuales",
                    text=df_totales_anuales["casos_totales"],
                    textposition=posiciones_texto,
                    textfont=dict(size=12, color="#ffffff", weight="bold"),
                    fill="tozeroy",
                    fillcolor="rgba(0, 86, 179, 0.25)",
                    line=dict(
                        shape="spline",
                        smoothing=1.3,
                        width=4,
                        color="#00CCFF",
                    ),
                    marker=dict(
                        size=9,
                        color="#FFFFFF",
                        line=dict(width=3, color="#0056B3"),
                    ),
                )
            )

            fig_hist.add_trace(
                go.Scatter(
                    x=[anio_min_total, anio_max_total],
                    y=[promedio_total, promedio_total],
                    mode="lines",
                    name=f"Prom. Histórico Total ({int(promedio_total):,})",
                    line=dict(color="#00FF66", width=2.5, dash="dash"),
                )
            )

            fig_hist.add_trace(
                go.Scatter(
                    x=[anio_min_total, anio_max_total],
                    y=[promedio_10_anios, promedio_10_anios],
                    mode="lines",
                    name=f"Prom. Últimos 10 Años ({int(promedio_10_anios):,})",
                    line=dict(color="#FFEA00", width=3, dash="dot"),
                )
            )

            fig_hist.add_trace(
                go.Scatter(
                    x=[anio_min_total, anio_max_total],
                    y=[promedio_5_anios, promedio_5_anios],
                    mode="lines",
                    name=f"Prom. Últimos 5 Años ({int(promedio_5_anios):,})",
                    line=dict(color="#D90429", width=3, dash="solid"),
                )
            )

            fig_hist.add_vline(
                x=anio_inicio_10,
                line_width=2.5,
                line_dash="dashdot",
                line_color="#00E5FF",
                annotation_text="Inicio Út. 10 Años",
                annotation_position="top left",
                annotation_font=dict(color="#00E5FF", size=11, weight="bold"),
            )

            fig_hist.add_vline(
                x=anio_inicio_5,
                line_width=2.5,
                line_dash="dashdot",
                line_color="#FF9100",
                annotation_text="Inicio Út. 5 Años",
                annotation_position="top left",
                annotation_font=dict(color="#FF9100", size=11, weight="bold"),
            )

            max_valor_y = max(
                df_totales_anuales["casos_totales"].max(),
                promedio_total,
                promedio_10_anios,
                promedio_5_anios,
            )

            fig_hist.update_layout(
                title=f"TENDENCIA ANUAL DE {titulo_evento.upper()} VS. PROMEDIOS HISTÓRICOS",
                xaxis_title="Año",
                yaxis_title="Casos Totales",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=380,
                margin=dict(l=20, r=20, t=50, b=10),
                yaxis=dict(
                    range=[0, max_valor_y * 1.30],
                    showgrid=False,
                    zeroline=True,
                    zerolinecolor="rgba(255,255,255,0.2)",
                ),
                xaxis=dict(
                    range=[anio_min_total - 0.5, anio_max_total + 0.5],
                    dtick=1,
                    tickformat="d",
                    showgrid=False,
                ),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(
                fig_hist, use_container_width=True, config=config_plotly
            )

    with col_right:
        if key_prefix == "febriles":
            st.subheader("📈 Comparativo Últimas Semanas")

            anios_g2 = st.multiselect(
                "Seleccionar Año(s) - Últimas Semanas:",
                anios_disponibles,
                default=ultimos_dos_anios,
                key=f"{key_prefix}_g2_anios",
            )

            semanas_disponibles_data = sorted(
                df_max_anio[df_max_anio["casos_totales"] > 0]["semana"].unique()
            )
            if len(semanas_disponibles_data) >= 2:
                semanas_ultimas = [
                    semanas_disponibles_data[-2],
                    semanas_disponibles_data[-1],
                ]
            elif len(semanas_disponibles_data) == 1:
                semanas_ultimas = [semanas_disponibles_data[0]]
            else:
                semanas_ultimas = [semana_epidemiologica_actual]

            df_comp_data = df[
                (df["año"].isin(anios_g2))
                & (df["semana"].isin(semanas_ultimas))
            ].copy()
            df_comp_data["año_str"] = df_comp_data["año"].astype(str)

            if not df_comp_data.empty:
                df_comp = (
                    df_comp_data.groupby(["semana", "año_str"])[
                        "casos_totales"
                    ]
                    .sum()
                    .reset_index()
                )
                fig_ult = px.bar(
                    df_comp,
                    x="semana",
                    y="casos_totales",
                    color="año_str",
                    barmode="group",
                    text="casos_totales",
                    template="plotly_dark",
                    title=f"Semanas {' y '.join(map(str, semanas_ultimas))}",
                    labels={
                        "semana": "N° de Semana",
                        "casos_totales": "Casos",
                        "año_str": "Año",
                    },
                    color_discrete_sequence=["#0056B3", "#D90429"],
                )
                fig_ult.update_traces(textfont_size=13, textposition="auto")
                fig_ult.update_xaxes(type="category")
                fig_ult.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=380,
                    margin=dict(l=10, r=10, t=50, b=10),
                )
                st.plotly_chart(
                    fig_ult, use_container_width=True, config=config_plotly
                )
        else:
            st.info(
                "💡 El análisis detallado de los grupos etarios se encuentra desplegado en la sección inferior como el 5to gráfico completo."
            )

    # Renderizar el 5to gráfico obligatorio para IRAS
    if key_prefix == "iras":
        renderizar_quinto_grafico_iras(df)


# 7. EJECUCIÓN DEL MÓDULO SELECCIONADO
if modulo_seleccionado == "🌡️ Febriles":
    df = cargar_datos_csv("febriles_consolidado.csv", col_total_casos="feb_tot")
    if df is None:
        st.error("⚠️ No se encontró el archivo `febriles_consolidado.csv`.")
    else:
        renderizar_dashboard(
            df, titulo_evento="Febriles", key_prefix="febriles"
        )

elif modulo_seleccionado == "🫁 IRAS":
    df = cargar_datos_csv("iras_consolidado.csv")
    if df is None and os.path.exists("iras.csv"):
        df = cargar_datos_csv("iras.csv")

    if df is None:
        st.warning(
            "⚠️ Aún no se detecta el archivo `iras_consolidado.csv` o `iras.csv` en el repositorio."
        )
    else:
        renderizar_dashboard(df, titulo_evento="IRAS", key_prefix="iras")

else:
    st.title("🚧 Módulo en Desarrollo")
    st.info(
        f"El módulo de **{modulo_seleccionado}** estará disponible en las próximas iteraciones."
    )
