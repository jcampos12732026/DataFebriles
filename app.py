import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="Sala Situacional - MINSA",
    page_icon="📊",
    layout="wide"
)

# -----------------------------------------------------------------------------
# NAVEGACIÓN LATERAL
# -----------------------------------------------------------------------------
st.sidebar.title("Navegación")
modulo_seleccionado = st.sidebar.radio(
    "Seleccione Módulo:",
    ["IRAS", "FEBRILES", "DENGUE"]
)

# -----------------------------------------------------------------------------
# MÓDULO 1: IRAS
# -----------------------------------------------------------------------------
if modulo_seleccionado == "IRAS":
    st.title("📊 Sala Situacional de IRAS (Infecciones Respiratorias Agudas)")
    
    try:
        # Carga de datos
        try:
            df_iras = pd.read_csv("iras_consolidado.csv")
        except FileNotFoundError:
            df_iras = pd.read_csv("iras.csv")
            
        # Asegurar tipos de datos
        df_iras['ANO'] = df_iras['ANO'].astype(int)
        df_iras['SEMANA'] = df_iras['SEMANA'].astype(int)
        df_iras['CASOS'] = df_iras['CASOS'].astype(int)

        anos_disponibles = sorted(df_iras['ANO'].unique())
        max_ano = max(anos_disponibles) if anos_disponibles else 2026
        max_semana = int(df_iras[df_iras['ANO'] == max_ano]['SEMANA'].max()) if anos_disponibles else 52

        # --- TARJETAS KPI ---
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        
        casos_ano_actual = df_iras[df_iras['ANO'] == max_ano]['CASOS'].sum()
        casos_se_actual = df_iras[(df_iras['ANO'] == max_ano) & (df_iras['SEMANA'] == max_semana)]['CASOS'].sum()
        
        with col_kpi1:
            st.metric(label=f"Total Casos Acumulados ({max_ano})", value=f"{casos_ano_actual:,}")
        with col_kpi2:
            st.metric(label=f"Casos en Última Semana (SE {max_semana})", value=f"{casos_se_actual:,}")
        with col_kpi3:
            st.metric(label="Semanas Notificadas", value=f"SE 1 - SE {max_semana}")

        st.markdown("---")

        # --- SECCIÓN 1: COMPARATIVO SEMANAL ACUMULADO (COMBINADO) ---
        st.subheader("📈 Comparativo Semanal Acumulado")
        
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            anos_sel_comp = st.multiselect(
                "Año(s) - Comparativo:",
                options=anos_disponibles,
                default=anos_disponibles[-2:] if len(anos_disponibles) >= 2 else anos_disponibles,
                key="iras_multiselect_comp"
            )
        with col_f2:
            recortar_se = st.checkbox(
                f"Recortar hasta SE {max_semana} ({max_ano})",
                value=True,
                key="iras_check_recorte"
            )

        if anos_sel_comp:
            df_comp = df_iras[df_iras['ANO'].isin(anos_sel_comp)].copy()
            
            if recortar_se:
                df_comp = df_comp[df_comp['SEMANA'] <= max_semana]

            # Agrupar datos por año y semana ordenados numéricamente
            df_agrupado = df_comp.groupby(['ANO', 'SEMANA'])['CASOS'].sum().reset_index()
            df_agrupado = df_agrupado.sort_values(by=['SEMANA', 'ANO'])
            
            fig_comp = go.Figure()
            ultimo_ano_sel = max(anos_sel_comp)

            # Años anteriores en BARRAS, Último año en LÍNEA SUAVIZADA
            for ano in sorted(anos_sel_comp):
                df_sub = df_agrupado[df_agrupado['ANO'] == ano].sort_values('SEMANA')
                
                if ano == ultimo_ano_sel:
                    fig_comp.add_trace(go.Scatter(
                        x=df_sub['SEMANA'],
                        y=df_sub['CASOS'],
                        mode='lines+markers+text',
                        name=f"{ano} (Actual)",
                        line=dict(shape='spline', width=3, color='#FF2A2A'),
                        marker=dict(size=8, color='#FF2A2A'),
                        text=df_sub['CASOS'],
                        textposition="top center"
                    ))
                else:
                    fig_comp.add_trace(go.Bar(
                        x=df_sub['SEMANA'],
                        y=df_sub['CASOS'],
                        name=str(ano),
                        text=df_sub['CASOS'],
                        textposition="auto"
                    ))

            fig_comp.update_layout(
                title=f"TOTAL DE EPISODIOS SEMANALES DE IRAS (HASTA SE {max_semana if recortar_se else 52})",
                xaxis=dict(title="N° de Semana", tickmode='linear', dtick=1),
                yaxis=dict(title="Casos"),
                barmode='group',
                template="plotly_dark",
                legend_title="Año"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        # --- SECCIÓN 2: DISTRIBUCIÓN POR GRUPOS ETARIOS ---
        st.subheader("👶 Distribución por Grupos Etarios (< 5 Años)")
        
        anos_sel_etarios = st.multiselect(
            "Seleccionar Año(s) - Grupos Etarios:",
            options=anos_disponibles,
            default=anos_disponibles[-2:] if len(anos_disponibles) >= 2 else anos_disponibles,
            key="iras_multiselect_etarios"
        )

        if anos_sel_etarios and 'GRUPO_EDAD' in df_iras.columns:
            df_etarios = df_iras[df_iras['ANO'].isin(anos_sel_etarios)].groupby(['GRUPO_EDAD', 'ANO'])['CASOS'].sum().reset_index()
            
            fig_etarios = go.Figure()
            for ano in sorted(anos_sel_etarios):
                df_ano_e = df_etarios[df_etarios['ANO'] == ano]
                fig_etarios.add_trace(go.Bar(
                    x=df_ano_e['GRUPO_EDAD'],
                    y=df_ano_e['CASOS'],
                    name=str(ano),
                    text=df_ano_e['CASOS'],
                    textposition="auto"
                ))

            fig_etarios.update_layout(
                xaxis=dict(title="Grupo de Edad"),
                yaxis=dict(title="Casos"),
                barmode='group',
                template="plotly_dark",
                legend_title="Año"
            )
            st.plotly_chart(fig_etarios, use_container_width=True)

    except FileNotFoundError:
        st.warning("⚠️ Aún no se detecta el archivo `iras_consolidado.csv` o `iras.csv` en el repositorio.")

# -----------------------------------------------------------------------------
# MÓDULO 2: FEBRILES
# -----------------------------------------------------------------------------
elif modulo_seleccionado == "FEBRILES":
    st.title("🌡️ Sala Situacional de FEBRILES")
    
    try:
        # Carga de datos
        try:
            df_febriles = pd.read_csv("febriles_consolidado.csv")
        except FileNotFoundError:
            df_febriles = pd.read_csv("febriles.csv")
            
        # Asegurar tipos de datos
        df_febriles['ANO'] = df_febriles['ANO'].astype(int)
        df_febriles['SEMANA'] = df_febriles['SEMANA'].astype(int)
        df_febriles['CASOS'] = df_febriles['CASOS'].astype(int)

        anos_disponibles_f = sorted(df_febriles['ANO'].unique())
        max_ano_f = max(anos_disponibles_f) if anos_disponibles_f else 2026
        max_semana_f = int(df_febriles[df_febriles['ANO'] == max_ano_f]['SEMANA'].max()) if anos_disponibles_f else 52

        # --- TARJETAS KPI ---
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        
        casos_ano_actual_f = df_febriles[df_febriles['ANO'] == max_ano_f]['CASOS'].sum()
        casos_se_actual_f = df_febriles[(df_febriles['ANO'] == max_ano_f) & (df_febriles['SEMANA'] == max_semana_f)]['CASOS'].sum()
        
        with col_kpi1:
            st.metric(label=f"Total Captación Febriles ({max_ano_f})", value=f"{casos_ano_actual_f:,}")
        with col_kpi2:
            st.metric(label=f"Febriles en Última Semana (SE {max_semana_f})", value=f"{casos_se_actual_f:,}")
        with col_kpi3:
            st.metric(label="Semanas Notificadas", value=f"SE 1 - SE {max_semana_f}")

        st.markdown("---")

        # --- SECCIÓN 1: COMPARATIVO SEMANAL ACUMULADO (COMBINADO) ---
        st.subheader("📈 Comparativo Semanal Acumulado de Febriles")
        
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            anos_sel_comp_f = st.multiselect(
                "Año(s) - Comparativo:",
                options=anos_disponibles_f,
                default=anos_disponibles_f[-2:] if len(anos_disponibles_f) >= 2 else anos_disponibles_f,
                key="febriles_multiselect_comp"
            )
        with col_f2:
            recortar_se_f = st.checkbox(
                f"Recortar hasta SE {max_semana_f} ({max_ano_f})",
                value=True,
                key="febriles_check_recorte"
            )

        if anos_sel_comp_f:
            df_comp_f = df_febriles[df_febriles['ANO'].isin(anos_sel_comp_f)].copy()
            
            if recortar_se_f:
                df_comp_f = df_comp_f[df_comp_f['SEMANA'] <= max_semana_f]

            # Agrupar datos por año y semana ordenados numéricamente
            df_agrupado_f = df_comp_f.groupby(['ANO', 'SEMANA'])['CASOS'].sum().reset_index()
            df_agrupado_f = df_agrupado_f.sort_values(by=['SEMANA', 'ANO'])
            
            fig_comp_f = go.Figure()
            ultimo_ano_sel_f = max(anos_sel_comp_f)

            # Años anteriores en BARRAS, Último año en LÍNEA SUAVIZADA
            for ano in sorted(anos_sel_comp_f):
                df_sub_f = df_agrupado_f[df_agrupado_f['ANO'] == ano].sort_values('SEMANA')
                
                if ano == ultimo_ano_sel_f:
                    fig_comp_f.add_trace(go.Scatter(
                        x=df_sub_f['SEMANA'],
                        y=df_sub_f['CASOS'],
                        mode='lines+markers+text',
                        name=f"{ano} (Actual)",
                        line=dict(shape='spline', width=3, color='#FF2A2A'),
                        marker=dict(size=8, color='#FF2A2A'),
                        text=df_sub_f['CASOS'],
                        textposition="top center"
                    ))
                else:
                    fig_comp_f.add_trace(go.Bar(
                        x=df_sub_f['SEMANA'],
                        y=df_sub_f['CASOS'],
                        name=str(ano),
                        text=df_sub_f['CASOS'],
                        textposition="auto"
                    ))

            fig_comp_f.update_layout(
                title=f"TOTAL DE CASOS FEBRILES SEMANALES (HASTA SE {max_semana_f if recortar_se_f else 52})",
                xaxis=dict(title="N° de Semana", tickmode='linear', dtick=1),
                yaxis=dict(title="Casos"),
                barmode='group',
                template="plotly_dark",
                legend_title="Año"
            )
            st.plotly_chart(fig_comp_f, use_container_width=True)

        # --- SECCIÓN 2: DISTRIBUCIÓN POR GRUPOS ETARIOS ---
        st.subheader("👶 Distribución por Grupos Etarios")
        
        anos_sel_etarios_f = st.multiselect(
            "Seleccionar Año(s) - Grupos Etarios:",
            options=anos_disponibles_f,
            default=anos_disponibles_f[-2:] if len(anos_disponibles_f) >= 2 else anos_disponibles_f,
            key="febriles_multiselect_etarios"
        )

        if anos_sel_etarios_f and 'GRUPO_EDAD' in df_febriles.columns:
            df_etarios_f = df_febriles[df_febriles['ANO'].isin(anos_sel_etarios_f)].groupby(['GRUPO_EDAD', 'ANO'])['CASOS'].sum().reset_index()
            
            fig_etarios_f = go.Figure()
            for ano in sorted(anos_sel_etarios_f):
                df_ano_e_f = df_etarios_f[df_etarios_f['ANO'] == ano]
                fig_etarios_f.add_trace(go.Bar(
                    x=df_ano_e_f['GRUPO_EDAD'],
                    y=df_ano_e_f['CASOS'],
                    name=str(ano),
                    text=df_ano_e_f['CASOS'],
                    textposition="auto"
                ))

            fig_etarios_f.update_layout(
                xaxis=dict(title="Grupo de Edad"),
                yaxis=dict(title="Casos"),
                barmode='group',
                template="plotly_dark",
                legend_title="Año"
            )
            st.plotly_chart(fig_etarios_f, use_container_width=True)

    except FileNotFoundError:
        st.warning("⚠️ Aún no se detecta el archivo `febriles_consolidado.csv` o `febriles.csv` en el repositorio.")

# -----------------------------------------------------------------------------
# MÓDULO 3: OTROS (DENGUE U OTROS MÓDULOS)
# -----------------------------------------------------------------------------
else:
    st.title("🚧 Módulo en Desarrollo")
    st.info(
        f"El módulo de **{modulo_seleccionado}** estará disponible en las próximas iteraciones."
    )
