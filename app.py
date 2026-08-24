import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Configuración de página
st.set_page_config(
    page_title="Sala Situacional - Febriles C.S. César López Silva", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS unificados y limpios
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
        color: #ffffff;
    }

    .homenaje-banner {
        background: linear-gradient(90deg, rgba(20,30,48,0.85), rgba(36,59,85,0.85));
        border: 1px solid #ffd700;
        border-radius: 6px;
        padding: 6px 15px;
        text-align: center;
        color: #ffeb3b;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 12px;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.2);
    }
    .homenaje-banner span {
        color: #ffffff;
        font-weight: bold;
        margin: 0 5px;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    [data-testid="stSidebar"] {
        width: 280px !important;
        min-width: 280px !important;
        background-color: #0d131d !important;
    }

    /* TARJETA UNIFICADA INTEGRADA (SEMANA + FILTROS) */
    .unified-card-header {
        background: linear-gradient(145deg, #151c28, #1a2436);
        border: 2px solid #0056b3;
        border-radius: 10px 10px 0px 0px;
        padding: 12px 10px 8px 10px;
        text-align: center;
        box-shadow: 0px 4px 12px rgba(0, 86, 179, 0.3);
    }
    
    .unified-card-divider {
        background-color: #0056b3;
        height: 2px;
        margin: 0px;
    }

    /* Chips de selección en multiselect */
    span[data-baseweb="tag"] {
        background-color: #d90429 !important;
        border-radius: 4px !important;
        padding: 1px 5px !important;
        font-size: 11px !important;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    df = pd.read_csv("febriles_consolidado.csv")
    df.columns = df.columns.str.strip().str.lower()
    
    if 'ano' in df.columns:
        df = df.rename(columns={'ano': 'año'})
    
    for col in ['feb_tot', 'tot_aten', 'semana', 'año', 'mes']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    df['año'] = df['año'].astype(int)
    df['semana'] = df['semana'].astype(int)
    
    meses_nombre = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Setiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    if 'mes' in df.columns:
        df['mes_nom'] = df['mes'].map(meses_nombre).fillna('Desconocido')
    elif 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['mes_num'] = df['fecha'].dt.month
        df['mes_nom'] = df['mes_num'].map(meses_nombre).fillna('Desconocido')
    else:
        df['mes_num'] = ((df['semana'] - 1) // 4.33 + 1).astype(int).clip(1, 12)
        df['mes_nom'] = df['mes_num'].map(meses_nombre)

    return df

config_plotly = {'displayModeBar': 'hover'}

try:
    df = cargar_datos()

    fecha_hoy = datetime.now()
    semana_actual_sistema = fecha_hoy.isocalendar()[1]
    anio_actual_sistema = fecha_hoy.year

    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']

    # --- BARRA LATERAL UNIFICADA (UNA SOLA TARJETA CONTINUA) ---
    with st.sidebar:
        # Encabezado con Tarjeta de Semana Actual
        st.markdown(f"""
        <div class="unified-card-header">
            <h4 style="margin:0; color:#4da6ff; font-size: 13px; font-weight: bold; text-transform: uppercase;">Semana Epidemiológica</h4>
            <h1 style="font-size: 52px; margin: 0px; color: #ffcc00; font-weight: 900; line-height: 1;">{semana_actual_sistema}</h1>
            <p style="margin:2px 0 0 0; color:#dddddd; font-size: 13px; font-weight: 600;">Año: {anio_actual_sistema}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Filtros dentro del mismo bloque contiguo
        st.markdown("<h4 style='color:#ffffff; font-size: 14px; margin-top: 15px; font-weight: bold;'>🔍 Panel de Filtros</h4>", unsafe_allow_html=True)
        
        anios_disponibles = sorted(df['año'].unique())
        ultimos_dos_anios = anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles
        
        # Filtro de Años
        anio_sel = st.multiselect("Filtrar por Año(s):", anios_disponibles, default=ultimos_dos_anios)

        # Filtro de Meses
        meses_disponibles = [m for m in orden_meses if m in df['mes_nom'].unique()]
        mes_sel = st.multiselect("Filtrar por Mes(es):", meses_disponibles, default=[])

    # --- ÁREA PRINCIPAL ---
    
    # Banner Homenaje
    st.markdown("""
    <div class="homenaje-banner">
        ✨ <strong>En Honor y Memoria Acaecidas en Pandemia:</strong> 
        <span>Angela Neyra</span> ⭐ <span>Violeta Huacho</span> ⭐ <span>Celia Silva</span> ✨
    </div>
    """, unsafe_allow_html=True)

    # Logotipo Institucional
    if os.path.exists("logo_minsa.png"):
        st.image("logo_minsa.png", use_container_width=True)
    else:
        st.markdown('<div style="background-color:#003366; color:white; font-weight:bold; padding:10px; text-align:center; border-radius:6px;">PERÚ Ministerio de Salud | Diris Lima Este | RIS Chaclacayo | C.S. CÉSAR LÓPEZ SILVA</div>', unsafe_allow_html=True)

    # Filtrado de Datos
    df_filtered = df[df['año'].isin(anio_sel)].copy()
    if mes_sel:
        df_filtered = df_filtered[df_filtered['mes_nom'].isin(mes_sel)]
    df_filtered['año_str'] = df_filtered['año'].astype(str)

    ultimo_anio_csv = max(anios_disponibles)
    df_ultimo_anio = df[df['año'] == ultimo_anio_csv]
    semanas_csv = [int(s) for s in sorted(df_ultimo_anio['semana'].unique())]
    ultimas_2_semanas = semanas_csv[-2:] if len(semanas_csv) >= 2 else semanas_csv

    # FILA 1
    col_mid, col_right = st.columns([1.8, 1])

    with col_mid:
        st.subheader("📊 Episodios Semanales de Febriles")
        if 'feb_tot' in df_filtered.columns and not df_filtered.empty:
            df_sem = df_filtered.groupby(['semana', 'año_str'])['feb_tot'].sum().reset_index()
            fig_sem = px.bar(
                df_sem, x='semana', y='feb_tot', color='año_str', barmode='group',
                title="FEBRILES SEMANALES - C.S. CÉSAR LÓPEZ SILVA",
                labels={'semana': 'N° de Semana', 'feb_tot': 'Casos', 'año_str': 'Año'},
                template="plotly_dark"
            )
            fig_sem.update_xaxes(type='category')
            fig_sem.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_sem, use_container_width=True, config=config_plotly)

    with col_right:
        st.subheader("📈 Útimas Semanas Comparativo")
        penultimo_anio_csv = ultimo_anio_csv - 1
        
        df_comp_data = df[
            (df['año'].isin([penultimo_anio_csv, ultimo_anio_csv])) & 
            (df['semana'].isin(ultimas_2_semanas))
        ].copy()

        df_comp_data['año_str'] = df_comp_data['año'].astype(str)

        if not df_comp_data.empty:
            df_comp = df_comp_data.groupby(['semana', 'año_str'])['feb_tot'].sum().reset_index()
            texto_semanas = " y ".join([str(s) for s in ultimas_2_semanas])
            titulo_comparativo = f"Comparativo Semanas {texto_semanas} ({penultimo_anio_csv} vs {ultimo_anio_csv})"
            
            fig_ult = px.bar(
                df_comp, x='semana', y='feb_tot', color='año_str', barmode='group',
                text_auto=True, template="plotly_dark",
                title=titulo_comparativo,
                labels={'semana': 'N° de Semana', 'feb_tot': 'Casos', 'año_str': 'Año'}
            )
            fig_ult.update_xaxes(type='category')
            fig_ult.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_ult, use_container_width=True, config=config_plotly)

    st.divider()

    # FILA 2
    col_mes, col_hist = st.columns([1.5, 1])

    with col_mes:
        st.subheader("📅 Episodios Mensualizados")
        if not df_filtered.empty:
            df_mes = df_filtered.groupby(['mes_nom', 'año_str'])['feb_tot'].sum().reset_index()
            df_mes['mes_nom'] = pd.Categorical(df_mes['mes_nom'], categories=orden_meses, ordered=True)
            df_mes = df_mes.sort_values('mes_nom')

            anio_inicio = min(anio_sel) if anio_sel else min(anios_disponibles)
            anio_fin = max(anio_sel) if anio_sel else max(anios_disponibles)

            fig_mes = px.bar(
                df_mes, x='mes_nom', y='feb_tot', color='año_str', barmode='group',
                text_auto=True, template="plotly_dark",
                title=f"COMPARATIVO MENSUAL ({anio_inicio} - {anio_fin})",
                labels={'mes_nom': 'Mes', 'feb_tot': 'Casos', 'año_str': 'Año'}
            )
            fig_mes.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_mes, use_container_width=True, config=config_plotly)

    with col_hist:
        st.subheader("📉 Evolución Anual")
        if not df_filtered.empty:
            df_hist = df_filtered.groupby('año')['feb_tot'].sum().reset_index()
            fig_hist = px.area(
                df_hist, x='año', y='feb_tot',
                title="EVOLUCIÓN ANUAL HISTÓRICA",
                markers=True, template="plotly_dark", color_discrete_sequence=['#ff7f0e']
            )
            fig_hist.update_xaxes(type='category')
            fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_hist, use_container_width=True, config=config_plotly)

except Exception as e:
    st.error(f"Error al cargar la visualización: {e}")
