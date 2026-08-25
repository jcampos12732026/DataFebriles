import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# ... [MANTENER SECCIONES DE CONFIGURACIÓN Y CSS INICIALES] ...

# --- ÁREA DE CÓDIGO DEL GRÁFICO PRINCIPAL ---
with col_mid:
    st.subheader("📊 Episodios Semanales de Febriles")
    if 'feb_tot' in df_filtered.columns and not df_filtered.empty:
        
        # Agrupar datos por semana y año
        df_sem = df_filtered.groupby(['semana', 'año'])['feb_tot'].sum().reset_index()
        
        # Crear objeto de figura avanzado de Plotly
        fig_sem = go.Figure()
        
        anios_en_datos = sorted(df_sem['año'].unique())
        max_anio_presente = max(anios_en_datos)
        
        # Paleta de colores para mantener consistencia
        colores = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']
        
        for idx, anio in enumerate(anios_en_datos):
            df_anio = df_sem[df_sem['año'] == anio].sort_values('semana')
            color = colores[idx % len(colores)]
            
            # El año actual/más reciente va en Barras; los años anteriores en Líneas Suavizadas
            if anio == max_anio_presente:
                fig_sem.add_trace(go.Bar(
                    x=df_anio['semana'],
                    y=df_anio['feb_tot'],
                    name=str(anio),
                    marker_color='#ff595e',
                    opacity=0.85
                ))
            else:
                fig_sem.add_trace(go.Scatter(
                    x=df_anio['semana'],
                    y=df_anio['feb_tot'],
                    name=str(anio),
                    mode='lines+markers',
                    line=dict(shape='spline', smoothing=1.3, width=3, color=color),
                    marker=dict(size=6)
                ))

        # Título dinámico limpio
        texto_corte = f"(HASTA SE {max_semana_data})" if corte_acumulado else "(AÑO COMPLETO)"
        titulo_limpio = f"FEBRILES SEMANALES {texto_corte}"

        fig_sem.update_layout(
            title=titulo_limpio,
            xaxis_title="N° de Semana",
            yaxis_title="Casos",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=340,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(type='category'),
            legend=dict(title="Año", orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
        )
        
        st.plotly_chart(fig_sem, use_container_width=True, config=config_plotly)
