import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Sala Situacional - Febriles", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS unificados
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
        color: #ffffff;
    }

    .homenaje-banner {
        background: linear-gradient(90deg, rgba(20,30,48,0.85), rgba(36,59,85,0.85));
        border: 1px solid rgba(255, 215, 0, 0.6);
        border-radius: 8px;
        padding: 8px 15px;
        text-align: center;
        color: #ffeb3b;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 15px;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.35), inset 0 0 10px rgba(255, 255, 255, 0.1);
        text-shadow: 0 0 8px rgba(255, 235, 59, 0.5);
    }
    .homenaje-banner span {
        color: #ffffff;
        font-weight: bold;
        margin: 0 5px;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
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

    max_semana_real_data = int(df_max_anio[df_max_anio['feb_tot'] > 0]['semana'].max()) if not df_max_anio.empty else 1

    hoy = datetime.now()
    semana_pc_actual = int(hoy.strftime("%V")) 
    if hoy.year == 2026:
        semana_pc_actual = 34

    anios_disponibles = sorted(df['año'].unique())
    ultimos_dos_anios = anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown(f"""
        <div class="unified-card-header">
            <h4 style="margin:0; color:#4da6ff; font-size: 13px; font-weight: bold; text-transform: uppercase;">Semana Actual (PC)</h4>
            <h1 style="font-size: 52px; margin: 0px; color: #ffcc00; font-weight: 900; line-height: 1;">SE {semana_pc_actual}</h1>
            <p style="margin:2px 0 0 0; color:#dddddd; font-size: 13px; font-weight: 600;">Año: {hoy.year}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h4 style='color:#ffffff; font-size: 14px; margin-top: 10px; font-weight: bold;'>⚙️ Estado del Sistema</h4>", unsafe_allow_html=True)
        st.info("Módulos independientes operativos.")

    # --- ÁREA PRINCIPAL ---
    
    st.markdown("""
    <div class="homenaje-banner">
        ✨ <strong>En Honor y Memoria Acaecidas en Pandemia:</strong> 
        <span>Angela Neyra</span> ⭐ <span>Violeta Huacho</span> ⭐ <span>Celia Silva</span> ✨
    </div>
    """, unsafe_allow_html=True)

    if os.path.exists("logo_minsa.png"):
        st.image("logo_minsa.png", use_container_width=True)
    else:
        st.markdown('<div style="background-color:#003366; color:white; font-weight:bold; padding:10px; text-align:center; border-radius:6px;">Ministerio de Salud | Diris Lima Este | RIS Chaclacayo | C.S. CÉSAR LÓPEZ SILVA</div>', unsafe_allow_html=True)

    # ==========================================
    # FILA 1: Gráfico Semanal y Comparativo de Últimas Semanas
    # ==========================================
    col_mid, col_right = st.columns([1.8, 1])

    # --- GRÁFICO 1: Episodios Semanales ---
    with col_mid:
        st.subheader("📊 Episodios Semanales de Febriles")
        
        col_f1, col_f2 = st.columns([1.5, 1])
        with col_f1:
            anios_g1 = st.multiselect("Seleccionar Año(s) - Semanal:", anios_disponibles, default=ultimos_dos_anios, key="g1_anios")
        with col_f2:
            st.markdown("<div style='height: 22px;'></div>", unsafe_allow_html=True)
            incluye_anio_actual = max_anio_data in anios_g1
            label_chk = f"Acumulado hasta SE {max_semana_real_data} ({max_anio_data})"
            corte_acumulado = st.checkbox(label_chk, value=True if incluye_anio_actual else False, disabled=not incluye_anio_actual, key="chk_corte_g1")
        
        df_g1 = df[df['año'].isin(anios_g1)].copy()
        if incluye_anio_actual and corte_acumulado:
            df_g1 = df_g1[df_g1['semana'] <= max_semana_real_data]

        if not df_g1.empty:
            df_sem = df_g1.groupby(['semana', 'año'])['feb_tot'].sum().reset_index()
            fig_sem = go.Figure()
            anios_en_datos = sorted(df_sem['año'].unique())
            max_anio_presente = max(anios_en_datos) if anios_en_datos else max_anio_data
            colores_barras = ['#636EFA', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']
            
            for idx, anio in enumerate(anios_en_datos):
                if anio != max_anio_presente:
                    df_anio = df_sem[df_sem['año'] == anio].sort_values('semana')
                    fig_sem.add_trace(go.Bar(
                        x=df_anio['semana'], y=df_anio['feb_tot'],
                        name=str(anio), marker_color=colores_barras[idx % len(colores_barras)], opacity=0.75,
                        text=df_anio['feb_tot'], textposition='auto',
                        textfont=dict(size=13, color='white')
                    ))

            if max_anio_presente in anios_en_datos:
                df_ultimo = df_sem[df_sem['año'] == max_anio_presente].sort_values('semana')
                fig_sem.add_trace(go.Scatter(
                    x=df_ultimo['semana'], y=df_ultimo['feb_tot'],
                    name=f"{max_anio_presente} (Actual)", mode='lines+markers+text',
                    text=df_ultimo['feb_tot'], textposition="top center",
                    textfont=dict(size=14, color='#FF3333', family='sans-serif', weight='bold'),
                    line=dict(shape='spline', smoothing=1.3, width=4, color='#FF3333'),
                    marker=dict(size=8, color='#FF3333')
                ))

            texto_corte_titulo = f" (HASTA SE {max_semana_real_data})" if (incluye_anio_actual and corte_acumulado) else " (AÑOS COMPLETOS)"
            fig_sem.update_layout(
                title=f"TOTAL DE EPISODIOS SEMANALES DE FEBRILES{texto_corte_titulo}",
                xaxis_title="N° de Semana", yaxis_title="Casos",
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=340, margin=dict(l=10, r=10, t=40, b=10), xaxis=dict(type='category'), barmode='group',
                legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
            )
            st.plotly_chart(fig_sem, use_container_width=True, config=config_plotly)

    # --- GRÁFICO 2: Comparativo Últimas Semanas ---
    with col_right:
        st.subheader("📈 Comparativo Últimas Semanas")
        
        anios_g2 = st.multiselect("Seleccionar Año(s) - Últimas Semanas:", anios_disponibles, default=ultimos_dos_anios, key="g2_anios_independiente")
        
        semanas_disponibles_data = sorted(df_max_anio[df_max_anio['feb_tot'] > 0]['semana'].unique())
        if len(semanas_disponibles_data) >= 2:
            semanas_ultimas = [semanas_disponibles_data[-2], semanas_disponibles_data[-1]]
        elif len(semanas_disponibles_data) == 1:
            semanas_ultimas = [semanas_disponibles_data[0]]
        else:
            semanas_ultimas = [semana_pc_actual]

        df_comp_data = df[(df['año'].isin(anios_g2)) & (df['semana'].isin(semanas_ultimas))].copy()
        df_comp_data['año_str'] = df_comp_data['año'].astype(str)

        if not df_comp_data.empty:
            df_comp = df_comp_data.groupby(['semana', 'año_str'])['feb_tot'].sum().reset_index()
            fig_ult = px.bar(
                df_comp, x='semana', y='feb_tot', color='año_str', barmode='group',
                text='feb_tot', template="plotly_dark",
                title=f"Semanas {' y '.join(map(str, semanas_ultimas))}",
                labels={'semana': 'N° de Semana', 'feb_tot': 'Casos', 'año_str': 'Año'}
            )
            fig_ult.update_traces(textfont_size=13, textposition='auto')
            fig_ult.update_xaxes(type='category')
            fig_ult.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=340, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_ult, use_container_width=True, config=config_plotly)

    st.divider()

    # ==========================================
    # FILA 2: Gráfico Mensualizado (Multiselección de Años) y Evolución Anual
    # ==========================================
    col_mes, col_hist = st.columns([1.5, 1])

    with col_mes:
        st.subheader("📅 Episodios Mensualizados")
        
        # Multiselect para años en el gráfico mensualizado
        anios_mes_sel = st.multiselect("Año(s) - Mensual:", anios_disponibles, default=ultimos_dos_anios, key="g3_anios_multiselect")
        df_mes_base = df[df['año'].isin(anios_mes_sel)].copy()

        if not df_mes_base.empty:
            df_mes = df_mes_base.groupby('mes_nom')['feb_tot'].sum().reset_index()
            df_mes['mes_nom'] = pd.Categorical(df_mes['mes_nom'], categories=orden_meses, ordered=True)
            df_mes = df_mes.sort_values('mes_nom')

            # Rango dinámico de años para el título del gráfico
            if anios_mes_sel:
                min_sel = min(anios_mes_sel)
                max_sel = max(anios_mes_sel)
                rango_str = f"DESDE EL AÑO {min_sel} HASTA EL AÑO {max_sel}" if len(anios_mes_sel) > 1 else f"AÑO {min_sel}"
            else:
                rango_str = "SELECCIONADOS"

            fig_mes = px.bar(
                df_mes, x='mes_nom', y='feb_tot',
                text='feb_tot', template="plotly_dark",
                title=f"COMPARATIVO DE FEBRILES MENSUALIZADOS {rango_str}",
                labels={'mes_nom': 'Mes', 'feb_tot': 'Casos'}
            )
            fig_mes.update_traces(textfont_size=13, textposition='auto')
            fig_mes.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=340, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_mes, use_container_width=True, config=config_plotly)

    with col_hist:
        st.subheader("📉 Evolución Anual Acumulada")
        
        anios_hist = st.multiselect("Seleccionar Año(s) - Anual:", anios_disponibles, default=anios_disponibles, key="g4_anios")
        df_hist_base = df[df['año'].isin(anios_hist)].copy()
        
        if not df_hist_base.empty:
            df_hist = df_hist_base.groupby('año')['feb_tot'].sum().reset_index()
            fig_hist = px.area(
                df_hist, x='año', y='feb_tot',
                title="COMPARATIVO DE FEBRILES (ANUAL)",
                markers=True, template="plotly_dark", color_discrete_sequence=['#ff7f0e']
            )
            fig_hist.update_xaxes(type='category')
            fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=340, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_hist, use_container_width=True, config=config_plotly)

except Exception as e:
    st.error(f"Error al cargar la visualización: {e}")
