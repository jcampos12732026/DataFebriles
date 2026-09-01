import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# Configuración de la página
st.set_page_config(layout="wide", page_title="Monitoreo Epidemiológico - C.S. César López Silva")

config_plotly = {
    "displayModeBar": "hover",
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

# Encabezado Oficial
st.markdown("<h2 style='text-align: center; color: white;'>PERÚ: Ministerio de Salud | DIRIS Lima Este | RIS Chaclacayo | C.S. CÉSAR LÓPEZ SILVA</h2>", unsafe_allow_html=True)
st.markdown("---")

# Selector en barra lateral para eventos
evento_seleccionado = st.sidebar.selectbox(
    "Seleccione el Evento Epidemiológico:",
    options=["EDAS", "IRAS", "FEBRILES", "DENGUE"],
    index=0
)

key_prefix = evento_seleccionado.lower().replace(" ", "_")

# Función de carga adaptada a rutas de GitHub / Web
@st.cache_data
def cargar_datos_con_diagnostico(evento):
    archivos_evento = {
        "EDAS": "consolidado_edas_total.csv",
        "IRAS": "iras_consolidado.csv",
        "FEBRILES": "febriles_consolidado.csv"
    }
    
    archivo_objetivo = archivos_evento.get(evento, "consolidado_edas_total.csv")
    
    # Busca directamente en la carpeta raíz del repositorio en la web
    ruta_completa = os.path.join(os.getcwd(), archivo_objetivo)
    
    df = None
    if os.path.exists(ruta_completa):
        try:
            df = pd.read_csv(ruta_completa, sep=None, engine='python', encoding='utf-8')
        except Exception as e:
            st.sidebar.error(f"Error al leer CSV: {e}")
    
    if df is None or df.empty:
        archivo_subido = st.sidebar.file_uploader(f"Subir manualmente {evento}:", type=["csv"], key=f"loader_{evento.lower()}")
        if archivo_subido is not None:
            try:
                df = pd.read_csv(archivo_subido, sep=None, engine='python', encoding='utf-8')
            except Exception as e:
                st.sidebar.error(f"Error al leer subido: {e}")

    if df is None or df.empty:
        return pd.DataFrame()
    
    # Normalización de columnas año y semana
    for col in df.columns:
        col_lower = col.strip().lower()
        if col_lower in ["año", "anio", "ano", "year"]:
            df = df.rename(columns={col: "año"})
        elif col_lower in ["semana", "se", "sem"]:
            df = df.rename(columns={col: "semana"})

    if "año" not in df.columns:
        df["año"] = 2026 
    if "semana" not in df.columns:
        df["semana"] = 1

    if "mes" not in df.columns:
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"]
        df["mes_num"] = ((df["semana"] - 1) // 4 + 1).clip(1, 12)
        mapping_meses = {i+1: m for i, m in enumerate(meses_nombres)}
        df["mes"] = df["mes_num"].map(mapping_meses)
        
    return df

# Carga del DataFrame
df = cargar_datos_con_diagnostico(evento_seleccionado)

# PANEL DE DEPURACIÓN EN PANTALLA
with st.expander("🛠️ Ver estado interno de los datos (Depuración)", expanded=False):
    if df.empty:
        st.error("El DataFrame está completamente VACÍO. No hay datos para mostrar.")
    else:
        st.success(f"DataFrame cargado con éxito. Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas.")
        st.write("**Columnas detectadas en tu archivo:**", list(df.columns))
        st.write("**Primeras 3 filas de tus datos:**", df.head(3))

anios_disponibles = sorted(df["año"].unique()) if not df.empty and "año" in df.columns else [2024, 2025, 2026]
ultimos_dos_anios = anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles
colores_inst = ["#1d4ed8", "#ef4444", "#10b981", "#f59e0b"]
orden_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"]

# RENDERIZADOR DE PANELES
def renderizar_panel_evento(df_evento, nombre_evento, cols_etarias, mapeo_etario, nota_pie=None):
    if df_evento.empty:
        st.warning(f"No hay registros disponibles para procesar gráficos en {nombre_evento}.")
        return

    df_ev = df_evento.copy()
    cols_pres = [c for c in cols_etarias if c in df_ev.columns]

    col_tot_directa = None
    for candidate in ["feb_tot", "total_casos", "total"]:
        if candidate in df_ev.columns:
            col_tot_directa = candidate
            break

    if col_tot_directa:
        df_ev["total_casos_fila"] = pd.to_numeric(df_ev[col_tot_directa], errors="coerce").fillna(0)
    elif cols_pres:
        df_ev[cols_pres] = df_ev[cols_pres].apply(pd.to_numeric, errors="coerce").fillna(0)
        df_ev["total_casos_fila"] = df_ev[cols_pres].sum(axis=1)
    else:
        df_ev["total_casos_fila"] = 0

    col_panel1, col_panel2 = st.columns(2)
    
    # 1. SEMANAL
    with col_panel1:
        st.subheader(f"📅 Episodios Semanales de {nombre_evento}")
        c_sel1, c_chk1 = st.columns([2, 1.5])
        with c_sel1:
            anios_sem = st.multiselect(f"Años ({nombre_evento} - Sem):", anios_disponibles, default=ultimos_dos_anios, key=f"{key_prefix}_sem_multi")
        
        max_sem_ult = 52
        if anios_sem:
            df_ult_s = df_ev[df_ev["año"] == max(anios_sem)]
            if not df_ult_s.empty:
                max_sem_ult = int(df_ult_s["semana"].max())

        with c_chk1:
            st.write("")
            st.write("")
            aplicar_corte_sem = st.checkbox(f"Acumulado hasta SE {max_sem_ult}", value=True, key=f"{key_prefix}_chk_sem")
        
        if anios_sem:
            if aplicar_corte_sem:
                df_s_base = df_ev[(df_ev["año"].isin(anios_sem)) & (df_ev["semana"] <= max_sem_ult)].copy()
                titulo_sem = f"TOTAL DE EPISODIOS SEMANALES DE {nombre_evento} (HASTA SE {max_sem_ult})"
            else:
                df_s_base = df_ev[df_ev["año"].isin(anios_sem)].copy()
                titulo_sem = f"TOTAL DE EPISODIOS SEMANALES DE {nombre_evento} (AÑO COMPLETO)"
            
            df_s_agg = df_s_base.groupby(["año", "semana"], as_index=False)["total_casos_fila"].sum()
            
            fig_sem = go.Figure()
            for i, anio in enumerate(sorted(anios_sem)):
                df_a = df_s_agg[df_s_agg["año"] == anio]
                color = colores_inst[i % len(colores_inst)]
                nombre_leyenda = f"{anio} (Actual)" if anio == max(anios_sem) else str(anio)
                
                if anio == max(anios_sem):
                    fig_sem.add_trace(go.Scatter(
                        x=df_a["semana"], y=df_a["total_casos_fila"], name=nombre_leyenda, 
                        mode="lines+markers+text", text=df_a["total_casos_fila"], textposition="top center",
                        line=dict(color="#ef4444", width=3, shape="spline")
                    ))
                else:
                    fig_sem.add_trace(go.Bar(
                        x=df_a["semana"], y=df_a["total_casos_fila"], name=nombre_leyenda, 
                        marker=dict(color=color), opacity=0.85
                    ))
            
            fig_sem.update_layout(
                template="plotly_dark", title=titulo_sem, barmode="group", height=380, 
                margin=dict(l=10, r=10, t=60, b=10), 
                legend=dict(orientation="h", y=1.12, x=0, xanchor="left"),
                xaxis=dict(dtick=1)
            )
            st.plotly_chart(fig_sem, use_container_width=True, config=config_plotly)

    # 2. MENSUALIZADO
    with col_panel2:
        st.subheader(f"📊 Episodios Mensualizados de {nombre_evento}")
        c_sel2, c_chk2 = st.columns([2, 1.5])
        with c_sel2:
            anios_mes = st.multiselect(f"Años ({nombre_evento} - Mes):", anios_disponibles, default=ultimos_dos_anios, key=f"{key_prefix}_mes_multi")
        
        max_mes_ult = "Marzo"
        if anios_mes:
            df_ult_m = df_ev[df_ev["año"] == max(anios_mes)]
            if not df_ult_m.empty and "mes" in df_ult_m.columns:
                max_mes_ult = df_ult_m.iloc[-1]["mes"]

        with c_chk2:
            st.write("")
            st.write("")
            aplicar_corte_mes = st.checkbox(f"Acumulado hasta {max_mes_ult}", value=True, key=f"{key_prefix}_chk_mes")

        if anios_mes and "mes" in df_ev.columns:
            if aplicar_corte_mes and max_mes_ult in orden_meses:
                idx_corte = orden_meses.index(max_mes_ult)
                meses_permitidos = orden_meses[:idx_corte+1]
                df_m_base = df_ev[(df_ev["año"].isin(anios_mes)) & (df_ev["mes"].isin(meses_permitidos))].copy()
                titulo_mes = f"COMPARATIVO DE {nombre_evento} MENSUALIZADOS"
            else:
                df_m_base = df_ev[df_ev["año"].isin(anios_mes)].copy()
                titulo_mes = f"COMPARATIVO DE {nombre_evento} MENSUALIZADOS (AÑO COMPLETO)"

            df_m_agg = df_m_base.groupby(["año", "mes"], as_index=False)["total_casos_fila"].sum()
            
            fig_mes = go.Figure()
            for i, anio in enumerate(sorted(anios_mes)):
                df_am = df_m_agg[df_m_agg["año"] == anio].copy()
                df_am["mes"] = pd.Categorical(df_am["mes"], categories=orden_meses, ordered=True)
                df_am = df_am.sort_values("mes")
                color = colores_inst[i % len(colores_inst)]
                nombre_leyenda = f"{anio} (Actual)" if anio == max(anios_mes) else str(anio)
                
                if anio == max(anios_mes):
                    fig_mes.add_trace(go.Scatter(
                        x=df_am["mes"], y=df_am["total_casos_fila"], name=nombre_leyenda, 
                        mode="lines+markers+text", text=df_am["total_casos_fila"], textposition="top center",
                        line=dict(color="#ef4444", width=3, shape="spline")
                    ))
                else:
                    fig_mes.add_trace(go.Bar(
                        x=df_am["mes"], y=df_am["total_casos_fila"], name=nombre_leyenda, 
                        marker=dict(color=color), opacity=0.85
                    ))
            
            fig_mes.update_layout(
                template="plotly_dark", title=titulo_mes, barmode="group", height=380, 
                margin=dict(l=10, r=10, t=60, b=10), 
                legend=dict(orientation="h", y=1.12, x=0, xanchor="left")
            )
            st.plotly_chart(fig_mes, use_container_width=True, config=config_plotly)

    st.markdown("---")

    col_panel3, col_panel4 = st.columns([1.5, 1])

    # 3. TENDENCIA ANUAL VS PROMEDIOS HISTÓRICOS
    with col_panel3:
        st.subheader(f"📈 Evolución Anual vs. Promedios Históricos")
        if not df_ev.empty and "año" in df_ev.columns:
            df_clean = df_ev.copy()
            df_clean["año"] = pd.to_numeric(df_clean["año"], errors="coerce")
            df_clean = df_clean.dropna(subset=["año"])
            df_clean["año"] = df_clean["año"].astype(int)
            
            df_anual = df_clean.groupby("año", as_index=False)["total_casos_fila"].sum().sort_values("año")
            
            if not df_anual.empty:
                anio_actual = int(df_anual["año"].max())
                prom_total = int(df_anual["total_casos_fila"].mean())
                
                df_10 = df_anual[df_anual["año"] >= (anio_actual - 10)]
                prom_10 = int(df_10["total_casos_fila"].mean()) if not df_10.empty else 0
                
                df_5 = df_anual[df_anual["año"] >= (anio_actual - 5)]
                prom_5 = int(df_5["total_casos_fila"].mean()) if not df_5.empty else 0

                anio_inicio_10 = anio_actual - 10
                anio_inicio_5 = anio_actual - 5

                fig_hist = go.Figure()
                
                fig_hist.add_trace(go.Scatter(
                    x=df_anual["año"], y=df_anual["total_casos_fila"], name=f"Casos Anuales", 
                    mode="lines+markers+text", text=df_anual["total_casos_fila"], textposition="top center",
                    fill="tozeroy", fillcolor="rgba(0, 180, 216, 0.15)",
                    line=dict(color="#00b4d8", width=3, shape="spline")
                ))
                
                fig_hist.add_hline(y=prom_total, line_dash="dash", line_color="#2ecc71", line_width=2, 
                                   annotation_text=f"Prom. Histórico Total ({prom_total})", annotation_position="top right")
                fig_hist.add_hline(y=prom_10, line_dash="dot", line_color="#f1c40f", line_width=2.5, 
                                   annotation_text=f"Prom. Últimos 10 Años ({prom_10})", annotation_position="top right")
                fig_hist.add_hline(y=prom_5, line_color="#e74c3c", line_width=2, 
                                   annotation_text=f"Prom. Últimos 5 Años ({prom_5})", annotation_position="top right")

                fig_hist.add_vline(x=anio_inicio_10, line_dash="dash", line_color="#00bcd4", line_width=1.5,
                                   annotation_text="Inicio Út. 10 Años", annotation_position="top")
                fig_hist.add_vline(x=anio_inicio_5, line_dash="dash", line_color="#ff9800", line_width=1.5,
                                   annotation_text="Inicio Út. 5 Años", annotation_position="top")

                min_x = df_anual["año"].min()
                max_x = df_anual["año"].max()

                fig_hist.update_layout(
                    template="plotly_dark", title=f"TENDENCIA ANUAL DE {nombre_evento} VS. PROMEDIOS HISTÓRICOS",
                    height=450, margin=dict(l=10, r=10, t=90, b=30), 
                    legend=dict(orientation="h", y=1.18, x=1, xanchor="right"),
                    xaxis=dict(title="Año", tickmode="linear", tick0=min_x, dtick=1, range=[min_x - 0.5, max_x + 0.5]),
                    yaxis=dict(title="Casos Totales")
                )
                st.plotly_chart(fig_hist, use_container_width=True, config=config_plotly)

    # 4. GRUPOS ETARIOS
    with col_panel4:
        st.subheader(f"👶 Distribución por Grupos Etarios")
        anios_etario = st.multiselect(f"Seleccionar Año(s) - Grupos Etarios:", anios_disponibles, default=ultimos_dos_anios, key=f"{key_prefix}_etario_multi")
        
        if anios_etario and cols_pres:
            df_et_base = df_ev[df_ev["año"].isin(anios_etario)].copy()
            df_et_base[cols_pres] = df_et_base[cols_pres].apply(pd.to_numeric, errors="coerce").fillna(0)
            
            df_melt = df_et_base.melt(id_vars=["año"], value_vars=cols_pres, var_name="grupo", value_name="casos")
            df_melt["grupo_label"] = df_melt["grupo"].map(mapeo_etario).fillna(df_melt["grupo"])
            
            df_et_agg = df_melt.groupby(["año", "grupo_label"], as_index=False)["casos"].sum()
            df_et_agg["Año"] = df_et_agg["año"].astype(str)
            
            orden_etario_labels = [mapeo_etario[c] for c in cols_etarias if c in mapeo_etario]
            df_et_agg["grupo_label"] = pd.Categorical(df_et_agg["grupo_label"], categories=orden_etario_labels, ordered=True)
            df_et_agg = df_et_agg.sort_values("grupo_label")

            fig_et = px.bar(
                df_et_agg, x="grupo_label", y="casos", color="Año", barmode="group", 
                text="casos", template="plotly_dark", 
                color_discrete_map={str(a): colores_inst[i % len(colores_inst)] for i, a in enumerate(sorted(anios_etario))}
            )
            fig_et.update_traces(textposition='auto')
            fig_et.update_layout(
                height=450, margin=dict(l=10, r=10, t=50, b=40), 
                xaxis=dict(title="Grupo de Edad", tickangle=0),
                yaxis=dict(title="Casos"),
                legend=dict(orientation="h", y=1.12, x=0.8, xanchor="center", title_text="Año")
            )
            st.plotly_chart(fig_et, use_container_width=True, config=config_plotly)

    if nota_pie:
        st.markdown(f"<div style='margin-top: 15px; text-align: center; font-size: 15px; color: #ff5555;'>{nota_pie}</div>", unsafe_allow_html=True)

# ENRUTAMIENTO DE EVENTOS
if key_prefix == "edas":
    renderizar_panel_evento(
        df, "EDAS", 
        ["DAA_C1", "DAA_C1_4", "DAA_C5", "DAA_C5_11", "DAA_C12_17", "DAA_C18_29", "DAA_C30_59", "DAA_C60"], 
        {"DAA_C1": "< 1 Año", "DAA_C1_4": "1 a 4 Años", "DAA_C5": ">= 5 Años", "DAA_C5_11": "5 a 11 Años", "DAA_C12_17": "12 a 17 Años", "DAA_C18_29": "18 a 29 Años", "DAA_C30_59": "30 a 59 Años", "DAA_C60": "60 a +"}, 
        "<b>Nota:</b> Desde 2024 se incorporan datos de 5 a 11 años."
    )

elif key_prefix == "iras":
    renderizar_panel_evento(
        df, "IRAS", 
        ["IRA_M2", "IRA_2_11", "IRA_1_4A"], 
        {"IRA_M2": "< 2 Meses", "IRA_2_11": "2 a 11 Meses", "IRA_1_4A": "1 a 4 Años"}, 
        "<b>Nota:</b> Vigilancia de Infecciones Respiratorias Agudas por grupos etarios principales (< 5 Años)."
    )

elif key_prefix == "febriles":
    renderizar_panel_evento(
        df, "FEBRILES", 
        ["feb_m1", "feb_1_4", "feb_5_9", "feb_10_19", "feb_20_59", "feb_m60"], 
        {"feb_m1": "< 1 Año", "feb_1_4": "1 a 4 Años", "feb_5_9": "5 a 9 Años", "feb_10_19": "10 a 19 Años", "feb_20_59": "20 a 59 Años", "feb_m60": "60 a + Años"}, 
        "<b>Nota:</b> Vigilancia epidemiológica de casos febriles capturados."
    )

else:
    st.info("⚙️ **Módulo de DENGUE en Fase de Configuración de Campo.**")
