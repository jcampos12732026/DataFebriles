import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuración de página
st.set_page_config(
    page_title="Sala Situacional - Febriles", 
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
        width: 290px !important;
        min-width: 290px !important;
        background-color: #0d131d !important;
    }

    .unified-card-header {
        background: linear-gradient(145deg, #151c28, #1a2436);
        border: 2px solid #0056b3;
        border-radius: 10px;
        padding: 12px 10px;
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

    max_anio_data = int(df['año'].max())
    df_max_anio = df[df['año'] == max_anio_data]
    max_semana_data = int(df_max_anio[df_max_anio['feb_tot'] > 0]['semana'].max())

    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']

    # --- BARRA LATERAL UNIFICADA ---
    with st.sidebar:
        st.markdown(f"""
        <div class="unified-card-header">
            <h4 style="margin:0; color:#4da6ff; font-size: 13px; font-weight: bold; text-transform: uppercase;">Semana Registrada Máxima</h4>
            <h1 style="font-size: 52px; margin: 0px; color: #ffcc00; font-weight: 900; line-height: 1;">SE {max_semana_data}</h1>
            <p style="margin:2px 0 0 0; color:#dddddd; font-size: 13px; font-weight: 600;">Año Evaluado: {max_anio_data}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h4 style='color:#ffffff; font-size: 14px; margin-top: 10px; font-weight: bold;'>⚙️ Controles de Filtros</h4>", unsafe_allow_html=True)
        
        anios_disponibles = sorted(df['año'].unique())
        ultimos_dos_anios = anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles
        
        # FILTRO 1: Seleccionar Año(s)
        anio_sel = st.multiselect("1. Filtro Anual:", anios_disponibles, default=ultimos_dos_anios)

        # FILTRO 2: Seleccionar Mes(es)
        meses_disponibles = [m for m in orden_meses if m in df['mes_nom'].unique()]
        mes_sel = st.multiselect("2. Filtro Mensual:", meses_disponibles, default=[])

        # FILTRO 3: Corte Epidemiológico
        corte_acumulado = st.checkbox(f"3. Acumulado hasta SE {max_semana_data} ({max_anio_data})", value=True, 
                                      help=f"Al marcar esta opción, todos los años comparados se mostrarán solo hasta la Semana {max_semana_data}.")

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

    # FILTRADO DE DATOS
    df_filtered = df[df['año'].isin(anio_sel)].copy()

    if mes_sel:
        df_filtered = df_filtered[df_filtered['mes_nom'].isin(mes_sel)]

    if corte_acumulado:
        df_filtered = df_filtered[df_filtered['semana'] <= max_semana_data]

    df_filtered['año_str'] = df_filtered['año'].astype(str)

    semanas_ultimas = [max_semana_data - 1, max_semana_data] if max_semana_data > 1 else [max_semana_data]

    # FILA 1
    col_mid, col_right = st.columns([1.8, 1])

    with col_mid:
        st.subheader("📊 Episodios Semanales de Febriles")
        if 'feb_tot' in df_filtered.columns and not df_filtered.empty:
            df_sem = df_filtered.groupby(['semana', 'año'])['feb_tot'].sum().reset_index()
            
            fig_sem = go.Figure()
            anios_en_datos = sorted(df_sem['año'].unique())
            max_anio_presente = max(anios_en_datos)
            
            colores_barras = ['#636EFA', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']
            
            # Años anteriores -> BARRAS
            for idx, anio in enumerate(anios_en_datos):
                if anio != max_anio_presente:
                    df_anio = df_sem[df_sem['año'] == anio].sort_values('semana')
                    color = colores_barras[idx % len(colores_barras)]
                    fig_sem.add_trace(go.Bar(
                        x=df_anio['semana'],
                        y=df_anio['feb_tot'],
                        name=str(anio),
                        marker_color=color,
                        opacity=0.75
                    ))

            # Último año -> LÍNEA SUAVIZADA
            if max_anio_presente in anios_en_datos:
                df_ultimo = df_sem[df_sem['año'] == max_anio_presente].sort_values('semana')
                fig_sem.add_trace(go.Scatter(
                    x=df_ultimo['semana'],
                    y=df_ultimo['feb_tot'],
                    name=f"{max_anio_presente} (Actual)",
                    mode='lines+markers+text',
                    text=df_ultimo['feb_tot'],
                    textposition="top center",
                    line=dict(shape='spline', smoothing=1.3, width=4, color='#FF3333'),
                    marker=dict(size=8, color='#FF3333')
                ))

            texto_corte = f"(HASTA SE {max_semana_data})" if corte_acumulado else "(AÑO COMPLETO)"
            
            fig_sem.update_layout(
                title=f"FEBRILES SEMANALES {texto_corte}",
                xaxis_title="N° de Semana",
                yaxis_title="Casos",
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=340,
                margin=dict(l=10, r=10, t=40, b=10),
                xaxis=dict(type='category'),
                barmode='group',
                legend=dict(title="Año", orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
            )
            
            st.plotly_chart(fig_sem, use_container_width=True, config=config_plotly)

    with col_right:
        st.subheader("📈 Comparativo Últimas Semanas")
        penultimo_anio_csv = max_anio_data - 1
        
        df_comp_data = df[
            (df['año'].isin([penultimo_anio_csv, max_anio_data])) & 
            (df['semana'].isin(semanas_ultimas))
        ].copy()

        df_comp_data['año_str'] = df_comp_data['año'].astype(str)

        if not df_comp_data.empty:
            df_comp = df_comp_data.groupby(['semana', 'año_str'])['feb_tot'].sum().reset_index()
            texto_semanas = " y ".join([str(s) for s in semanas_ultimas])
            titulo_comparativo = f"Semanas {texto_semanas} ({penultimo_anio_csv} vs {max_anio_data})"
            
            fig_ult = px.bar(
                df_comp, x='semana', y='feb_tot', color='año_str', barmode='group',
                text_auto=True, template="plotly_dark",
                title=titulo_comparativo,
                labels={'semana': 'N° de Semana', 'feb_tot': 'Casos', 'año_str': 'Año'}
            )
            fig_ult.update_xaxes(type='category')
            fig_ult.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=340, margin=dict(l=10, r=10, t=40, b=10))
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
        st.subheader("📉 Evolución Anual Acumulada")
        if not df_filtered.empty:
            df_hist = df_filtered.groupby('año')['feb_tot'].sum().reset_index()
            fig_hist = px.area(
                df_hist, x='año', y='feb_tot',
                title="EVOLUCIÓN HISTÓRICA ACUMULADA",
                markers=True, template="plotly_dark", color_discrete_sequence=['#ff7f0e']
            )
            fig_hist.update_xaxes(type='category')
            fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_hist, use_container_width=True, config=config_plotly)

except Exception as e:
    st.error(f"Error al cargar la visualización: {e}")
