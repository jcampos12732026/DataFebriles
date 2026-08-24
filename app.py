import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página ancha
st.set_page_config(page_title="Sala Situacional - Febriles C.S. César López Silva", layout="wide")

# Estilos CSS personalizados
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
    
    # Asegurar tipos de datos numéricos limpios
    for col in ['feb_tot', 'tot_aten', 'semana', 'año']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # Forzar 'año' y 'semana' a entero
    df['año'] = df['año'].astype(int)
    df['semana'] = df['semana'].astype(int)
    
    return df

try:
    df = cargar_datos()

    # Encabezado
    st.markdown('<div class="header-box">PERÚ Ministerio de Salud | Diris Lima Este | RIS Chaclacayo | C.S. CÉSAR LÓPEZ SILVA</div>', unsafe_allow_html=True)

    # Sidebar: Filtros de Control
    st.sidebar.header("🔍 Control de Filtros")
    
    anios_disponibles = sorted(df['año'].unique())
    ultimos_dos_anios = anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles
    
    # Filtro de Años (Por defecto selecciona los dos últimos años)
    anio_sel = st.sidebar.multiselect("Seleccionar Año(s):", anios_disponibles, default=ultimos_dos_anios)
    
    # Filtro de Semanas
    semanas_disponibles = sorted(df['semana'].unique())
    semana_sel = st.sidebar.select_slider("Rango de Semanas Epidemiológicas:", options=semanas_disponibles, value=(min(semanas_disponibles), max(semanas_disponibles)))

    # Filtrar datos globales para los primeros dos gráficos
    df_filtered = df[(df['año'].isin(anio_sel)) & (df['semana'].between(semana_sel[0], semana_sel[1]))].copy()

    # Convertir 'año' a string para evitar decimales en leyendas/ejes
    df_filtered['año_str'] = df_filtered['año'].astype(str)

    # --- LÓGICA AUTOMÁTICA DE ÚLTIMAS 2 SEMANAS Y ÚLTIMOS 2 AÑOS ---
    ultimo_anio_data = max(anios_disponibles)
    penultimo_anio_data = ultimo_anio_data - 1

    # Obtener las dos últimas semanas registradas en el último año activo
    df_ultimo_anio = df[df['año'] == ultimo_anio_data]
    semanas_ultimo_anio = sorted(df_ultimo_anio['semana'].unique())
    ultimas_2_semanas = semanas_ultimo_anio[-2:] if len(semanas_ultimo_anio) >= 2 else semanas_ultimo_anio

    # Layout Principal
    col_left, col_mid, col_right = st.columns([1, 2.5, 2])

    with col_left:
        semana_actual = ultimas_2_semanas[-1] if len(ultimas_2_semanas) > 0 else 0
        st.markdown(f"""
        <div class="card-semana">
            <h4 style="margin:0; color:#4da6ff;">Semana Epidemiológica Actual</h4>
            <h1 style="font-size: 56px; margin: 10px 0; color: #ffcc00;">===> {semana_actual}</h1>
            <p style="margin:0; color:#cccccc;">Año: {ultimo_anio_data}</p>
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
        # Filtrar exactamente las 2 últimas semanas de los 2 últimos años
        df_comp_data = df[
            (df['año'].isin([penultimo_anio_data, ultimo_anio_data])) & 
            (df['semana'].isin(ultimas_2_semanas))
        ].copy()

        df_comp_data['año_str'] = df_comp_data['año'].astype(str)

        if not df_comp_data.empty:
            df_comp = df_comp_data.groupby(['semana', 'año_str'])['feb_tot'].sum().reset_index()
            fig_ult = px.bar(
                df_comp, x='semana', y='feb_tot', color='año_str', barmode='group',
                text_auto=True, template="plotly_dark",
                title=f"Comparativo Semanas {ultimas_2_semanas} ({penultimo_anio_data} vs {ultimo_anio_data})",
                labels={'semana': 'N° de Semana', 'feb_tot': 'Casos', 'año_str': 'Año'}
            )
            fig_ult.update_xaxes(type='category')
            fig_ult.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320)
            st.plotly_chart(fig_ult, use_container_width=True)

    st.divider()

    # --- HISTÓRICO AMARRADO A FILTROS ---
    st.subheader("📉 Comparativo Histórico de Febriles")
    
    # Filtrar histórico según los años seleccionados en la sidebar
    df_hist_filtered = df[df['año'].isin(anio_sel)].copy()
    df_hist = df_hist_filtered.groupby('año')['feb_tot'].sum().reset_index()
    
    fig_hist = px.area(
        df_hist, x='año', y='feb_tot',
        title="EVOLUCIÓN ANUAL HISTÓRICA (Años Seleccionados)",
        markers=True, template="plotly_dark", color_discrete_sequence=['#ff7f0e']
    )
    fig_hist.update_xaxes(type='category')
    fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
    st.plotly_chart(fig_hist, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la visualización: {e}")
