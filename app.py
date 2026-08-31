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
# SIMULACIÓN / CARGA DE DATOS (Ajustar a tu CSV/Base real)
# ==========================================
@st.cache_data
def cargar_datos():
    # Asegúrate de reemplazar esto con tu ruta o lógica de carga real (ej. pd.read_csv("datos.csv"))
    # Creamos un DataFrame de ejemplo para que la estructura sea completamente funcional:
    data = {
        "año": [2024, 2024, 2025, 2025, 2024, 2025, 2024, 2025],
        "semana": [1, 2, 1, 2, 1, 2, 1, 2],
        "mes": ["Enero", "Enero", "Enero", "Enero", "Febrero", "Febrero", "Febrero", "Febrero"],
        "evento": ["IRAS", "IRAS", "IRAS", "IRAS", "EDAS", "EDAS", "Dengue", "Dengue"],
        "grupo_edad": ["0-11m", "1-4 años", "0-11m", "5-9 años", "1-4 años", "0-11m", "20-59 años", "60+ años"],
        "casos_totales": [45, 30, 50, 25, 12, 18, 5, 8]
    }
    return pd.DataFrame(data)

df_global = cargar_datos()

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

# Filtrar dataframe global según el evento seleccionado
df = df_global[df_global["evento"] == titulo_evento].copy()
if df.empty:
    # Fallback si no hay datos exactos en el ejemplo para evitar errores visuales
    df = df_global.copy()

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

    # --- BLOQUE DINÁMICO: GRÁFICO 4 / QUINTO GRÁFICO ---
    # Manejo específico para IRAS (Gráfico de barras apiladas por grupo etario) o por defecto para otros módulos.
    if key_prefix == "iras":
        st.subheader("👥 Casos por Grupos Etarios (Apilado)")
        
        # Selector de años para el gráfico apilado de IRAS
        anios_iras_etario = st.multiselect(
            "Seleccionar Año(s) - Etarios:",
            anios_disponibles,
            default=ultimos_dos_anios,
            key=f"{key_prefix}_etarios_anios",
        )
        
        # Filtramos el DataFrame para los años seleccionados
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
                barmode="stack",  # Gráfico de barras apiladas
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
            st.plotly_chart(
                fig_etario, use_container_width=True, config=config_plotly
            )
        else:
            st.info("⚠️ No se encontraron columnas de grupos etarios o datos disponibles para IRAS.")
    else:
        # Comportamiento estándar / por defecto para otros módulos
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
