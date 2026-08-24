import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de página ancha
st.set_page_config(page_title="Sala Situacional - Febriles C.S. César López Silva", layout="wide")

# Estilos CSS personalizados (Elimina espacio sobrante arriba para alinear con la barra lateral)
st.markdown("""
    <style>
    .stApp {
        background-color: #0b111e;
        color: #ffffff;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    .header-box {
        background-color: #003366;
        padding: 10px 15px;
        border-radius: 6px;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 15px;
    }
    .card-semana {
        background-color: #1a2332;
        border: 2px solid #0056b3;
        border-radius: 8px;
        padding: 20px 15px;
        text-align: center;
        min-height: 320px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    df = pd.read_csv("febriles_consolidado.csv")
    df.columns = df.columns.str.strip().str.lower()
    
    if 'ano' in df.columns:
        df = df.rename(columns={'ano': 'año'})
    
    for col in ['feb_tot', 'tot_aten', 'semana', 'año']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    df['año'] = df['año'].astype(int)
    df['semana'] = df['semana'].astype(int)
    
    return df

try:
    df = cargar_datos()

    # Encabezado Institucional
    st.markdown('<div class="header-box">PERÚ Ministerio de Salud | Diris Lima Este | RIS Chaclacayo | C.S. CÉSAR LÓPEZ SILVA</div>', unsafe_allow_html=True)

    # Sidebar: Control de Filtros
    st.sidebar.header("🔍 Control de Filtros")
    
    anios_disponibles = sorted(df['año'].unique())
    ultimos_dos_anios = anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles
    
    anio_sel = st.sidebar.multiselect("Seleccionar Año(s):", anios_disponibles, default=ultimos_dos_anios)
    
    semanas_disponibles = sorted(df['semana'].unique())
    semana_sel = st.sidebar.select_slider("Rango de Semanas Epidemiológicas:", options=semanas_disponibles, value=(min(semanas_disponibles), max(semanas_disponibles)))

    # Filtrar datos de la data principal
    df_filtered = df[(df['año'].isin(anio_sel)) & (df['semana'].between(semana_sel[0], semana_sel[1]))].copy()
    df_filtered['año_str'] = df_filtered['año'].astype(str)

    # CÁLCULOS DE SEMANAS
    ultimo_anio_csv = max(anios_disponibles)
    df_ultimo_anio = df[df['año'] == ultimo_anio_csv]
    semanas_csv = sorted(df_ultimo_anio['semana'].unique())
    semana_max_csv = semanas_csv[-1] if len(semanas_csv) > 0 else 0
    ultimas_2_semanas = semanas_csv[-2:] if len(semanas_csv) >= 2 else semanas_csv

    # Layout Principal (Primera Fila)
    col_left, col_mid, col_right = st.columns([1.2, 2.4, 2])

    with col_left:
        # Tarjeta limpia con la última semana registrada en la data
        st.markdown(f"""
        <div class="card-semana">
            <h4 style="margin:0; color:#4da6ff;">Semana Epidemiológica Actual</h4>
            <h1 style="font-size: 58px; margin: 10px 0; color: #ffcc00;">===> {semana_max_csv}</h1>
            <p style="margin:0; color:#cccccc; font-size: 16px;">Año: {ultimo_anio_csv}</p>
        </div>
        """, unsafe_allow_html=True)

    with col_mid:
        st.subheader("📊 Episodios Semanales de Febriles")
        if 'feb_tot' in df_filtered.columns and not df_filtered.empty:
            df_sem = df_filtered.groupby(['semana', 'año_str'])['feb_tot'].sum().reset_index()
            fig_sem = px.bar(
                df_sem, x='semana', y='feb_tot', color='año_str', barmode='group',
                title="TOTAL DE EPISODIOS SEMANALES DE FEBRILES",
                labels={'semana': 'N° de Semana', 'feb_tot': 'Casos', 'año_str': 'Año'},
                template="plotly_dark"
            )
            fig_sem.update_xaxes(type='category')
            fig_sem.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320)
            st.plotly_chart(fig_sem, use_container_width=True)

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
            fig_ult = px.bar(
                df_comp, x='semana', y='feb_tot', color='año_str', barmode='group',
                text_auto=True, template="plotly_dark",
                title=f"Comparativo Semanas {ultimas_2_semanas} ({penultimo_anio_csv} vs {ultimo_anio_csv})",
                labels={'semana': 'N° de Semana', 'feb_tot': 'Casos', 'año_str': 'Año'}
            )
            fig_ult.update_xaxes(type='category')
            fig_ult.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320)
            st.plotly_chart(fig_ult, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la visualización: {e}")
