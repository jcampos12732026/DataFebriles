import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página ancha
st.set_page_config(page_title="Sala Situacional - Febriles C.S. César López Silva", layout="wide")

# Estilos CSS para imitar el tema de la imagen (fondos oscuros, títulos azules)
st.markdown("""
    <style>
    .stApp {
        background-color: #0b111e;
        color: #ffffff;
    }
    .header-box {
        background-color: #003366;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 15px;
    }
    .card-semana {
        background-color: #1a2332;
        border: 2px solid #0056b3;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    df = pd.read_csv("febriles_consolidado.csv")
    df.columns = df.columns.str.strip().str.lower()
    
    if 'ano' in df.columns:
        df = df.rename(columns={'ano': 'año'})
    
    # Asegurar que las columnas de fechas y totales sean numéricas
    for col in ['feb_tot', 'tot_aten', 'semana', 'año']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

try:
    df = cargar_datos()

    # Encabezado Institucional
    st.markdown('<div class="header-box">PERÚ Ministerio de Salud | Diris Lima Este | RIS Chaclacayo | C.S. CÉSAR LÓPEZ SILVA</div>', unsafe_allow_html=True)

    # Sidebar: Filtros de Control
    st.sidebar.header("🔍 Control de Filtros")
    
    anios_disponibles = sorted(df['año'].unique().astype(int))
    anio_sel = st.sidebar.multiselect("Seleccionar Año(s):", anios_disponibles, default=[2025, 2026] if 2026 in anios_disponibles else anios_disponibles[-2:])
    
    semanas_disponibles = sorted(df['semana'].unique().astype(int))
    semana_sel = st.sidebar.select_slider("Rango de Semanas Epidemiológicas:", options=semanas_disponibles, value=(1, max(semanas_disponibles)))

    # Filtrar datos
    df_filtered = df[(df['año'].isin(anio_sel)) & (df['semana'].between(semana_sel[0], semana_sel[1]))]

    # Fila Superior: Semana Actual + Gráficos Principales
    col_left, col_mid, col_right = st.columns([1, 2.5, 2])

    with col_left:
        semana_max = int(df['semana'].max())
        st.markdown(f"""
        <div class="card-semana">
            <h4 style="margin:0; color:#4da6ff;">Semana Epidemiológica Actual</h4>
            <h1 style="font-size: 56px; margin: 10px 0; color: #ffcc00;">===> {semana_max}</h1>
            <p style="margin:0; color:#cccccc;">C.S. César López Silva</p>
        </div>
        """, unsafe_allow_html=True)

    with col_mid:
        st.subheader("📊 Episodios Semanales de Febriles")
        if 'feb_tot' in df_filtered.columns:
            df_sem = df_filtered.groupby(['semana', 'año'])['feb_tot'].sum().reset_index()
            fig_sem = px.bar(df_sem, x='semana', y='feb_tot', color='año', barmode='group',
                             title="TOTAL DE EPISODIOS SEMANALES DE FEBRILES",
                             labels={'semana': 'N° de Semana', 'feb_tot': 'Casos', 'año': 'Año'},
                             template="plotly_dark")
            fig_sem.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320)
            st.plotly_chart(fig_sem, use_container_width=True)

    with col_right:
        st.subheader("📈 Útimas Semanas Comparativo")
        # Filtrar últimas 2 semanas disponibles
        semanas_ultimas = [semana_max - 1, semana_max]
        df_ultimas = df[df['semana'].isin(semanas_ultimas) & df['año'].isin(anio_sel)]
        
        if not df_ultimas.empty:
            df_comp = df_ultimas.groupby(['semana', 'año'])['feb_tot'].sum().reset_index()
            fig_ult = px.bar(df_comp, x='semana', y='feb_tot', color='año', barmode='group',
                             text_auto=True, template="plotly_dark",
                             title=f"Comparativo Semanas {semanas_ultimas[0]} y {semanas_ultimas[1]}")
            fig_ult.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320)
            st.plotly_chart(fig_ult, use_container_width=True)

    st.divider()

    # Fila Inferior: Tendencia Histórica del Área
    st.subheader("📉 Comparativo Histórico de Febriles (2006 - Presente)")
    df_hist = df.groupby('año')['feb_tot'].sum().reset_index()
    
    fig_hist = px.area(df_hist, x='año', y='feb_tot', title="EVOLUCIÓN ANUAL HISTÓRICA DE FEBRILES",
                       markers=True, template="plotly_dark", color_discrete_sequence=['#ff7f0e'])
    fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig_hist, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la visualización: {e}")
