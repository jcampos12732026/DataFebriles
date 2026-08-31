import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración inicial de la página
st.set_page_config(
    page_title="Sala Situacional - Análisis Epidemiológico",
    page_icon="📊",
    layout="wide",
)

# Configuración común para los gráficos de Plotly
config_plotly = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

# ==========================================
# CARGA DE DATOS DINÁMICA DESDE LOS CONSOLIDADOS
# ==========================================
@st.cache_data
def cargar_datos_evento(evento_sel):
    key = evento_sel.lower().replace(" ", "_")
    
    # Asignar el nombre del archivo consolidado según el evento
    if key == "edas":
        archivo = "consolidado_edas_total.csv"
    elif key == "iras":
        archivo = "consolidado_iras_total.csv"
    else:
        archivo = f"consolidado_{key}_total.csv"
        
    try:
        # Intenta leer el archivo CSV real de la carpeta / repositorio
        df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8')
        return df
    except Exception as e:
        # Fallback de seguridad por si el archivo aún no está subido
        st.warning(f"⚠️ No se encontró el archivo '{archivo}'. Usando datos de ejemplo temporales.")
        
        if key == "edas":
            data_fallback = {
                "año": [2024, 2025, 2024, 2025],
                "semana": [1, 1, 2, 2],
                "mes": ["Enero", "Enero", "Febrero", "Febrero"],
                "evento": [evento_sel, evento_sel, evento_sel, evento_sel],
                "DAA_C1": [2, 5, 3, 4],
                "DAA_C1_4": [10, 15, 12, 18],
                "DAA_C5_11": [20, 25, 22, 30],
                "DAA_C12_17": [5, 8, 6, 9],
                "DAA_C18_29": [8, 12, 10, 14],
                "DAA_C30_59": [12, 18, 15, 20],
                "DAA_C60": [4, 7, 5, 8],
                "casos_totales": [61, 90, 73, 103]
            }
        else:
            data_fallback = {
                "año": [2024, 2025, 2024, 2025],
                "semana": [1, 1, 2, 2],
                "mes": ["Enero", "Enero", "Febrero", "Febrero"],
                "evento": [evento_sel, evento_sel, evento_sel, evento_sel],
                "grupo_edad": ["0-11m", "1-4 años", "0-11m", "5-9 años"],
                "casos_totales": [10, 15, 20, 25]
            }
        return pd.DataFrame(data_fallback)

# ==========================================
# BARRA LATERAL / NAVEGACIÓN
# ==========================================
st.sidebar.title("🎛️ Panel de Control")
st.sidebar.markdown("---")

# Selector de Módulo / Evento Epidemiológico
evento_seleccionado = st.sidebar.selectbox(
    "Seleccione el Evento:",
    options=["IRAS", "EDAS", "Dengue", "Otras Eventos"],
    index=0
)

# Mapeo de prefijos y títulos
key_prefix = evento_seleccionado.lower().replace(" ", "_")
titulo_evento = evento_seleccionado

st.sidebar.markdown("---")
st.sidebar.info("ℹ️ Utilice los filtros adicionales en cada sección según sea necesario.")

# Cargar el DataFrame correspondiente al evento seleccionado
df = cargar_datos_evento(evento_seleccionado)

# ==========================================
# CUERPO PRINCIPAL - SALA SITUACIONAL
# ==========================================
st.title(f"📈 Sala Situacional - {titulo_evento}")
st.markdown("Monitoreo epidemiológico, tendencias y distribución por grupos etarios.")

# Obtener años disponibles
anios_disponibles = sorted(df["año"].unique()) if "año" in df.columns else [2024, 2025]
ultimos_dos_anios = anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles

# Layout de dos columnas principales para los gráficos
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Tendencia Semanal")
    # --- GRÁFICO 1: Comportamiento semanal ---
    if not df.empty and "semana" in df.columns and "casos_totales" in df.columns:
        df_semanal = df.groupby(["año", "semana"])["casos_totales"].sum().reset_index()
        df_semanal["semana_str"] = "SE " + df_semanal["semana"].astype(str) + " (" + df_semanal["año"].astype(str) + ")"
        
        fig_semanal = px.line(
            df_semanal,
            x="semana",
            y="casos_totales",
            color="año",
            markers=True,
            template="plotly_dark",
            title=f"COMPORTAMIENTO SEMANAL DE {titulo_evento.upper()}",
            labels={"semana": "Semana Epidemiológica", "casos_totales": "Casos Totales", "año": "Año"}
        )
        fig_semanal.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_semanal, use_container_width=True, config=config_plotly)
    else:
        st.warning("No hay datos suficientes para el gráfico semanal.")

    st.markdown("---")
    
    st.subheader("📅 Distribución Mensual")
    # --- GRÁFICO 2: Mensualizado ---
    if not df.empty and "mes" in df.columns:
        df_mensual = df.groupby(["año", "mes"])["casos_totales"].sum().reset_index()
        fig_mensual = px.bar(
            df_mensual,
            x="mes",
            y="casos_totales",
            color="año",
            barmode="group",
            template="plotly_dark",
            title=f"CASOS MENSUALES DE {titulo_evento.upper()}",
            labels={"mes": "Mes", "casos_totales": "Casos Totales", "año": "Año"}
        )
        fig_mensual.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_mensual, use_container_width=True, config=config_plotly)
    else:
        st.warning("No hay datos suficientes para el gráfico mensual.")


with col_right:
    st.subheader("📉 Evolución Anual Acumulada")
    # --- GRÁFICO 3: Evolución Anual ---
    if not df.empty and "año" in df.columns:
        df_anual = df.groupby("año")["casos_totales"].sum().reset_index()
        df_anual["año_str"] = df_anual["año"].astype(str)
        
        fig_anual = px.bar(
            df_anual,
            x="año_str",
            y="casos_totales",
            text="casos_totales",
            template="plotly_dark",
            title=f"ACUMULADO ANUAL DE {titulo_evento.upper()}",
            labels={"año_str": "Año", "casos_totales": "Total Casos"}
        )
        fig_anual.update_traces(textposition='auto')
        fig_anual.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_anual, use_container_width=True, config=config_plotly)
    else:
        st.warning("No hay datos suficientes para el gráfico anual.")

    st.markdown("---")

    # --- BLOQUE DINÁMICO POR MÓDULO (IRAS, EDAS, OTROS) ---
    if key_prefix == "iras":
        st.subheader("👥 Casos por Grupos Etarios (Apilado)")
        
        anios_iras_etario = st.multiselect(
            "Seleccionar Año(s) - Etarios:",
            anios_disponibles,
            default=ultimos_dos_anios,
            key=f"{key_prefix}_etarios_anios",
        )
        
        df_etario_base = df[df["año"].isin(anios_iras_etario)].copy()
        
        if not df_etario_base.empty and "grupo_edad" in df_etario_base.columns:
            df_etario = (
                df_etario_base.groupby(["año", "grupo_edad"])["casos_totales"]
                .sum()
                .reset_index()
            )
            df_etario["año_str"] = df_etario["año"].astype(str)
            
            fig_etario = px.bar(
                df_etario,
                x="año_str",
                y="casos_totales",
                color="grupo_edad",
                barmode="stack",
                template="plotly_dark",
                title=f"DISTRIBUCIÓN APILADA DE {titulo_evento.upper()} POR EDAD",
                labels={
                    "año_str": "Año",
                    "casos_totales": "Casos Totales",
                    "grupo_edad": "Grupo Etario"
                },
            )
            fig_etario.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=380,
                margin=dict(l=10, r=10, t=50, b=10),
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
            )
            st.plotly_chart(fig_etario, use_container_width=True, config=config_plotly)
        else:
            st.info("⚠️ No se encontraron columnas de grupos etarios o datos disponibles para IRAS.")
            
    elif key_prefix == "edas":
        st.subheader("👥 Casos de EDAS por Grupos Etarios (Apilado)")
        
        # Columnas etarias horizontales presentes en el consolidado de EDAS
        columnas_etarias_edas = [
            "DAA_C1", "DAA_C1_4", "DAA_C5", "DAA_C5_11", 
            "DAA_C12_17", "DAA_C18_29", "DAA_C30_59", "DAA_C60"
        ]
        cols_presentes = [col for col in columnas_etarias_edas if col in df.columns]
        
        if not df.empty and cols_presentes:
            anios_edas_etario = st.multiselect(
                "Seleccionar Año(s) - Etarios:",
                anios_disponibles,
                default=ultimos_dos_anios,
                key="edas_etarios_anios",
            )
            
            df_base_edas = df[df["año"].isin(anios_edas_etario)].copy()
            
            if not df_base_edas.empty:
                # Transformación de formato ancho a formato largo para graficar
                df_melted = df_base_edas.melt(
                    id_vars=["año"],
                    value_vars=cols_presentes,
                    var_name="grupo_edad",
                    value_name="casos"
                )
                
                df_agrupado_edas = df_melted.groupby(["año", "grupo_edad"], as_index=False)["casos"].sum()
                df_agrupado_edas["año_str"] = df_agrupado_edas["año"].astype(str)
                
                # Mapeo de nombres limpios y profesionales
                nombres_bonitos = {
                    "DAA_C1": "< 1 Año",
                    "DAA_C1_4": "1-4 Años",
                    "DAA_C5": "5 Años",
                    "DAA_C5_11": "5-11 Años",
                    "DAA_C12_17": "12-17 Años",
                    "DAA_C18_29": "18-29 Años",
                    "DAA_C30_59": "30-59 Años",
                    "DAA_C60": "60 a +"
                }
                df_agrupado_edas["grupo_edad_etiqueta"] = df_agrupado_edas["grupo_edad"].map(nombres_bonitos)
                
                # Orden cronológico estricto
                orden_cronologico = [
                    "< 1 Año", "1-4 Años", "5 Años", "5-11 Años", 
                    "12-17 Años", "18-29 Años", "30-59 Años", "60 a +"
                ]
                df_agrupado_edas["grupo_edad_etiqueta"] = pd.Categorical(
                    df_agrupado_edas["grupo_edad_etiqueta"], 
                    categories=orden_cronologico, 
                    ordered=True
                )
                
                fig_edas_etario = px.bar(
                    df_agrupado_edas.sort_values("grupo_edad_etiqueta"),
                    x="año_str",
                    y="casos",
                    color="grupo_edad_etiqueta",
                    barmode="stack",  # Gráfico apilado igual que IRAS
                    template="plotly_dark",
                    title="DISTRIBUCIÓN APILADA DE EDAS POR EDAD",
                    labels={
                        "año_str": "Año",
                        "casos": "Casos Totales",
                        "grupo_edad_etiqueta": "Grupo Etario"
                    },
                )
                fig_edas_etario.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=380,
                    margin=dict(l=10, r=10, t=50, b=10),
                    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
                )
                st.plotly_chart(fig_edas_etario, use_container_width=True, config=config_plotly)
            else:
                st.info("⚠️ No hay datos para los años seleccionados en EDAS.")
        else:
            st.info("⚠️ No se encontraron las columnas etarias de EDAS en el archivo consolidado.")
    else:
        # Comportamiento por defecto para otros módulos
        st.subheader("👥 Distribución por Grupos Etarios")
        if not df.empty and "grupo_edad" in df.columns:
            df_etario_def = df.groupby("grupo_edad")["casos_totales"].sum().reset_index()
            fig_etario_def = px.pie(
                df_etario_def,
                names="grupo_edad",
                values="casos_totales",
                template="plotly_dark",
                title=f"PROPORCIÓN POR GRUPO ETARIO - {titulo_evento.upper()}"
            )
            fig_etario_def.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=380,
                margin=dict(l=10, r=10, t=50, b=10)
            )
            st.plotly_chart(fig_etario_def, use_container_width=True, config=config_plotly)
        else:
            st.warning("No hay datos disponibles para grupos etarios en este evento.")
