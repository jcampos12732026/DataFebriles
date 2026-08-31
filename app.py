from datetime import datetime, timedelta
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Sala Situacional Epidemiológica - C.S. César López Silva",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS unificados y ocultamiento de elementos predeterminados
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}
    
    .stApp {
        background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
        color: #ffffff;
    }

    .homenaje-banner-sidebar {
        background: linear-gradient(135deg, rgba(20,30,48,0.95), rgba(36,59,85,0.95));
        border: 1px solid rgba(255, 215, 0, 0.6);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        color: #ffeb3b;
        font-size: 12px;
        font-weight: 500;
        margin-top: 15px;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.25), inset 0 0 10px rgba(255, 255, 255, 0.1);
        text-shadow: 0 0 6px rgba(255, 235, 59, 0.4);
    }
    .homenaje-banner-sidebar span {
        color: #ffffff;
        font-weight: bold;
        display: block;
        margin-top: 3px;
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.8);
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

    span[data-baseweb="tag"] {
        background-color: #d90429 !important;
        border-radius: 4px !important;
        padding: 1px 5px !important;
        font-size: 11px !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Cálculo de Semana Epidemiológica
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


# Carga de datos para Febriles
def cargar_datos_febriles():
  df = pd.read_csv("febriles_consolidado.csv")
  df.columns = df.columns.str.strip().str.lower()

  if "ano" in df.columns:
    df = df.rename(columns={"ano": "año"})

  for col in ["feb_tot", "tot_aten", "semana", "año", "mes"]:
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
    df["mes_num"] = ((df["semana"] - 1) // 4.33 + 1).astype(int).clip(1, 12)
    df["mes_nom"] = df["mes_num"].map(meses_nombre)

  return df


# Carga de datos para IRAS
def cargar_datos_iras():
  if not os.path.exists("iras_consolidado.csv"):
    return None
  df = pd.read_csv("iras_consolidado.csv")
  df.columns = df.columns.str.strip().str.lower()

  if "ano" in df.columns:
    df = df.rename(columns={"ano": "año"})

  cols_etarios = ["ira_m2", "ira_2_11", "ira_1_4a"]
  for col in cols_etarios:
    if col in df.columns:
      df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

  for col in ["semana", "año", "mes"]:
    if col in df.columns:
      df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

  df["año"] = df["año"].astype(int)
  df["semana"] = df["semana"].astype(int)

  if all(c in df.columns for c in cols_etarios):
    df["casos_totales"] = df["ira_m2"] + df["ira_2_11"] + df["ira_1_4a"]
  else:
    df["casos_totales"] = 0

  return df


config_plotly = {"displayModeBar": "hover"}
hoy = datetime.now()
semana_epidemiologica_actual = obtener_semana_epidemiologica(hoy)

# --- BARRA LATERAL UNIFICADA ---
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
      "Seleccionar Módulo:", ["🌡️ Febriles", "🫁 IRAS", "🦟 Dengue"], index=0
  )

  st.markdown(
      "<h4 style='color:#ffffff; font-size: 14px; margin-top: 10px;"
      " font-weight: bold;'>⚙️ Estado del Sistema</h4>",
      unsafe_allow_html=True,
  )
  st.info("Módulos independientes operativos.")

  st.markdown(
      """
        <div class="homenaje-banner-sidebar">
            ✨ <strong>En Honor y Memoria Acaecidas en Pandemia:</strong> 
            <span>⭐ Angela Neyra</span>
            <span>⭐ Violeta Huacho</span>
            <span>⭐ Celia Silva</span> ✨
        </div>
        """,
      unsafe_allow_html=True,
  )


# Logo institucional superior
if os.path.exists("logo_minsa.png"):
  st.image("logo_minsa.png", use_container_width=True)
else:
  st.markdown(
      '<div style="background-color:#003366; color:white; font-weight:bold;'
      " padding:10px; text-align:center; border-radius:6px; margin-bottom:"
      ' 10px;">PERÚ Ministerio de Salud | Diris Lima Este | RIS Chaclacayo |'
      " C.S. CÉSAR LÓPEZ SILVA</div>",
      unsafe_allow_html=True,
  )


# ==========================================
# MÓDULO 1: FEBRILES (Bloque exacto independiente)
# ==========================================
if modulo_seleccionado == "🌡️ Febriles":
  try:
    df = cargar_datos_febriles()

    max_anio_data = int(df["año"].max())
    df_max_anio = df[df["año"] == max_anio_data]

    max_semana_real_data = (
        int(df_max_anio[df_max_anio["feb_tot"] > 0]["semana"].max())
        if not df_max_anio.empty
        else 1
    )

    max_mes_num_real_data = (
        int(df_max_anio[df_max_anio["feb_tot"] > 0]["mes_num"].max())
        if not df_max_anio.empty
        else 1
    )

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
      st.subheader("📊 Episodios Semanales de Febriles")

      col_f1, col_f2 = st.columns([1.5, 1])
      with col_f1:
        anios_g1 = st.multiselect(
            "Seleccionar Año(s) - Semanal:",
            anios_disponibles,
            default=ultimos_dos_anios,
            key="g1_anios",
        )
      with col_f2:
        st.markdown(
            "<div style='height: 22px;'></div>", unsafe_allow_html=True
        )
        incluye_anio_actual_g1 = max_anio_data in anios_g1
        label_chk_g1 = (
            f"Acumulado hasta SE {max_semana_real_data} ({max_anio_data})"
        )
        corte_acumulado_g1 = st.checkbox(
            label_chk_g1,
            value=True if incluye_anio_actual_g1 else False,
            disabled=not incluye_anio_actual_g1,
            key="chk_corte_g1",
        )

      df_g1 = df[df["año"].isin(anios_g1)].copy()
      if incluye_anio_actual_g1 and corte_acumulado_g1:
        df_g1 = df_g1[df_g1["semana"] <= max_semana_real_data]

      if not df_g1.empty:
        df_sem = (
            df_g1.groupby(["semana", "año"])["feb_tot"].sum().reset_index()
        )
        fig_sem = go.Figure()
        anios_en_datos = sorted(df_sem["año"].unique())
        max_anio_presente = (
            max(anios_en_datos) if anios_en_datos else max_anio_data
        )
        colores_barras = [
            "#636EFA",
            "#00CC96",
            "#AB63FA",
            "#FFA15A",
            "#19D3F3",
        ]

        for idx, anio in enumerate(anios_en_datos):
          if anio != max_anio_presente:
            df_anio = df_sem[df_sem["año"] == anio].sort_values("semana")
            fig_sem.add_trace(
                go.Bar(
                    x=df_anio["semana"],
                    y=df_anio["feb_tot"],
                    name=str(anio),
                    marker_color=colores_barras[idx % len(colores_barras)],
                    opacity=0.75,
                    text=df_anio["feb_tot"],
                    textposition="auto",
                    textfont=dict(size=13, color="white"),
                )
            )

        if max_anio_presente in anios_en_datos:
          df_ultimo = df_sem[df_sem["año"] == max_anio_presente].sort_values(
              "semana"
          )
          fig_sem.add_trace(
              go.Scatter(
                  x=df_ultimo["semana"],
                  y=df_ultimo["feb_tot"],
                  name=f"{max_anio_presente} (Actual)",
                  mode="lines+markers+text",
                  text=df_ultimo["feb_tot"],
                  textposition="top center",
                  textfont=dict(
                      size=14,
                      color="#FF3333",
                      family="sans-serif",
                      weight="bold",
                  ),
                  line=dict(
                      shape="spline", smoothing=1.3, width=4, color="#FF3333"
                  ),
                  marker=dict(size=8, color="#FF3333"),
              )
          )

        texto_corte_titulo_g1 = (
            f" (HASTA SE {max_semana_real_data})"
            if (incluye_anio_actual_g1 and corte_acumulado_g1)
            else " (AÑOS COMPLETOS)"
        )
        fig_sem.update_layout(
            title=(
                "TOTAL DE EPISODIOS SEMANALES DE"
                f" FEBRILES{texto_corte_titulo_g1}"
            ),
            xaxis_title="N° de Semana",
            yaxis_title="Casos",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=340,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(type="category"),
            barmode="group",
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
            key="g3_anios_multiselect",
        )
      with col_m2:
        st.markdown(
            "<div style='height: 22px;'></div>", unsafe_allow_html=True
        )
        incluye_anio_actual_m = max_anio_data in anios_mes_sel
        label_chk_m = (
            f"Acumulado hasta {max_mes_nombre_real_data} ({max_anio_data})"
        )
        corte_acumulado_m = st.checkbox(
            label_chk_m,
            value=True if incluye_anio_actual_m else False,
            disabled=not incluye_anio_actual_m,
            key="chk_corte_mes",
        )

      df_mes_base = df[df["año"].isin(anios_mes_sel)].copy()

      if incluye_anio_actual_m and corte_acumulado_m:
        df_mes_base = df_mes_base[
            df_mes_base["mes_num"] <= max_mes_num_real_data
        ]

      if not df_mes_base.empty:
        df_mes = (
            df_mes_base.groupby(["mes_nom", "mes_num", "año"])["feb_tot"]
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
        colores_barras = [
            "#636EFA",
            "#00CC96",
            "#AB63FA",
            "#FFA15A",
            "#19D3F3",
        ]

        for idx, anio in enumerate(anios_seleccionados_ordenados):
          if anio != max_anio_mes:
            df_anio_m = df_mes[df_mes["año"] == anio]
            fig_mes.add_trace(
                go.Bar(
                    x=df_anio_m["mes_nom"],
                    y=df_anio_m["feb_tot"],
                    name=str(anio),
                    marker_color=colores_barras[idx % len(colores_barras)],
                    opacity=0.75,
                    text=df_anio_m["feb_tot"],
                    textposition="auto",
                    textfont=dict(size=12, color="white"),
                )
            )

        if max_anio_mes is not None:
          df_ultimo_m = df_mes[df_mes["año"] == max_anio_mes]
          fig_mes.add_trace(
              go.Scatter(
                  x=df_ultimo_m["mes_nom"],
                  y=df_ultimo_m["feb_tot"],
                  name=f"{max_anio_mes} (Actual)",
                  mode="lines+markers+text",
                  text=df_ultimo_m["feb_tot"],
                  textposition="top center",
                  textfont=dict(
                      size=13,
                      color="#FF3333",
                      family="sans-serif",
                      weight="bold",
                  ),
                  line=dict(
                      shape="spline", smoothing=1.3, width=4, color="#FF3333"
                  ),
                  marker=dict(size=8, color="#FF3333"),
              )
          )

        if anios_mes_sel:
          min_sel = min(anios_mes_sel)
          max_sel = max(anios_mes_sel)
          rango_str = (
              f"DESDE EL AÑO {min_sel} HASTA EL AÑO {max_sel}"
              if len(anios_mes_sel) > 1
              else f"AÑO {min_sel}"
          )
        else:
          rango_str = "SELECCIONADOS"

        fig_mes.update_layout(
            title=f"COMPARATIVO DE FEBRILES MENSUALIZADOS {rango_str}",
            xaxis_title="Mes",
            yaxis_title="Casos",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=340,
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

    # FILA 2: Evolución Anual y Comparativo Últimas Semanas
    col_hist, col_right = st.columns([1.8, 1])

    with col_hist:
      st.subheader("📉 Evolución Anual Acumulada")

      anios_hist = st.multiselect(
          "Seleccionar Año(s) - Anual:",
          anios_disponibles,
          default=anios_disponibles,
          key="g4_anios",
      )
      df_hist_base = df[df["año"].isin(anios_hist)].copy()

      if not df_hist_base.empty:
        df_hist = (
            df_hist_base.groupby("año")["feb_tot"]
            .sum()
            .reset_index()
            .sort_values("año")
        )

        fig_hist = go.Figure()
        fig_hist.add_trace(
            go.Scatter(
                x=df_hist["año"],
                y=df_hist["feb_tot"],
                mode="lines+markers+text",
                text=df_hist["feb_tot"],
                textposition="top center",
                textfont=dict(size=12, color="#ffffff"),
                line=dict(
                    shape="spline", smoothing=1.3, width=3, color="#ff7f0e"
                ),
                marker=dict(size=7, color="#ff7f0e"),
                fill="tozeroy",
                fillcolor="rgba(255, 127, 14, 0.3)",
            )
        )

        fig_hist.update_layout(
            title="COMPARATIVO DE FEBRILES (ANUAL)",
            xaxis_title="Año",
            yaxis_title="feb_tot",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=340,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(type="category"),
        )
        st.plotly_chart(
            fig_hist, use_container_width=True, config=config_plotly
        )

    with col_right:
      st.subheader("📈 Comparativo Últimas Semanas")

      anios_g2 = st.multiselect(
          "Seleccionar Año(s) - Últimas Semanas:",
          anios_disponibles,
          default=ultimos_dos_anios,
          key="g2_anios_independiente",
      )

      semanas_disponibles_data = sorted(
          df_max_anio[df_max_anio["feb_tot"] > 0]["semana"].unique()
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
          (df["año"].isin(anios_g2)) & (df["semana"].isin(semanas_ultimas))
      ].copy()
      df_comp_data["año_str"] = df_comp_data["año"].astype(str)

      if not df_comp_data.empty:
        df_comp = (
            df_comp_data.groupby(["semana", "año_str"])["feb_tot"]
            .sum()
            .reset_index()
        )
        fig_ult = px.bar(
            df_comp,
            x="semana",
            y="feb_tot",
            color="año_str",
            barmode="group",
            text="feb_tot",
            template="plotly_dark",
            title=f"Semanas {' y '.join(map(str, semanas_ultimas))}",
            labels={
                "semana": "N° de Semana",
                "feb_tot": "Casos",
                "año_str": "Año",
            },
        )
        fig_ult.update_traces(textfont_size=13, textposition="auto")
        fig_ult.update_xaxes(type="category")
        fig_ult.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=340,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(
            fig_ult, use_container_width=True, config=config_plotly
        )

  except Exception as e:
    st.error(f"Error al cargar el módulo de Febriles: {e}")


# ==========================================
# MÓDULO 2: IRAS (Bloque exacto independiente)
# ==========================================
elif modulo_seleccionado == "🫁 IRAS":
  st.title("🫁 Sala Situacional de IRAS")

  df_iras = cargar_datos_iras()

  if df_iras is not None:
    cols_grupos = {
        "ira_m2": "Menores de 2 meses",
        "ira_2_11": "2-11 Meses",
        "ira_1_4a": "1-4 Años",
    }
    cols_presentes = [c for c in cols_grupos.keys() if c in df_iras.columns]

    if cols_presentes:
      anios_disponibles_iras = sorted(df_iras["año"].unique())
      max_anio_iras = (
          max(anios_disponibles_iras)
          if anios_disponibles_iras
          else hoy.year
      )
      df_max_iras = df_iras[
          (df_iras["año"] == max_anio_iras) & (df_iras["casos_totales"] > 0)
      ]

      semana_max_data_iras = (
          int(df_max_iras["semana"].max())
          if not df_max_iras.empty
          else semana_epidemiologica_actual
      )

      ultimos_dos_anios_iras = (
          anios_disponibles_iras[-2:]
          if len(anios_disponibles_iras) >= 2
          else anios_disponibles_iras
      )

      anios_sel_etario = st.multiselect(
          "Seleccionar Año(s) - Grupo Etario:",
          anios_disponibles_iras,
          default=ultimos_dos_anios_iras,
          key="etario_multiselect_iras",
      )

      df_filtrado_iras = df_iras[df_iras["año"].isin(anios_sel_etario)].copy()

      df_etario = df_filtrado_iras.melt(
          id_vars=["año"],
          value_vars=cols_presentes,
          var_name="grupo_raw",
          value_name="casos",
      )
      df_etario["Grupo Etario"] = df_etario["grupo_raw"].map(cols_grupos)

      df_resumen = (
          df_etario.groupby(["Grupo Etario", "año"])["casos"]
          .sum()
          .reset_index()
      )
      df_resumen["año_str"] = df_resumen["año"].astype(str)

      orden_categorias = ["Menores de 2 meses", "2-11 Meses", "1-4 Años"]

      st.markdown(
          "#### Total de casos de IRAs por grupo etario - C.S. César López Silva"
          " / RIS CHACLACAYO (hasta la semana epidemiológica"
          f" {semana_max_data_iras})"
      )

      fig_etario = px.bar(
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

      fig_etario.update_traces(
          textposition="outside",
          textfont=dict(size=14, color="white", weight="bold"),
      )

      fig_etario.update_layout(
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

      st.plotly_chart(
          fig_etario, use_container_width=True, config=config_plotly
      )

  else:
    st.error("⚠️ No se encontró el archivo `iras_consolidado.csv`.")


# ==========================================
# MÓDULO 3: DENGUE
# ==========================================
elif modulo_seleccionado == "🦟 Dengue":
  st.title("🦟 Sala Situacional de Dengue")
  st.info("Módulo en construcción para Dengue.")
