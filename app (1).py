
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import linregress

st.set_page_config(page_title='Análisis Performance Deporte', layout='wide')

# --- Funciones de Simulación (HIIT W'bal) ---
def simulate_w_bal(cp, w_total, work_p_pct, work_dur, rest_p_pct, rest_dur, reps=10):
    p_work = cp * (work_p_pct / 100)
    p_rest = cp * (rest_p_pct / 100)
    d_cp = cp - p_rest
    # Modelo de Skiba para Tau
    tau = 546 * np.exp(-0.01 * d_cp) + 316
    w_bal, time = [w_total], [0]
    status = 'Completada'
    
    for r in range(reps):
        # Trabajo
        for _ in range(work_dur):
            current_w = w_bal[-1] - (p_work - cp)
            w_bal.append(max(0, current_w))
            time.append(time[-1] + 1)
            if current_w <= 0:
                return time, w_bal, f'Fallo en Rep {r+1}'
        
        # Recuperación (Exponencial)
        w_start_rest = w_bal[-1]
        for t_rest in range(1, rest_dur + 1):
            current_w = w_total - (w_total - w_start_rest) * np.exp(-t_rest / tau)
            w_bal.append(current_w)
            time.append(time[-1] + 1)
            
    return time, w_bal, status

# --- Interfaz Principal ---
st.title('📊 Dashboard de Rendimiento Avanzado')
tab1, tab2, tab3 = st.tabs(['Eficiencia TEI', 'Test 3-min All-out', 'Simulador HIIT W'bal'])

# Configuración global
archivo_excel = 'practica_potencia_critica_colab_datos (1).xlsx'

# --- TAB 1: TEI ---
with tab1:
    st.header('Análisis de Eficiencia (TEI)')
    st.info('Sección para análisis de carga externa vs interna.')

# --- TAB 2: TEST 3-MIN ALL-OUT ---
with tab2:
    st.header('Validación Test 3-min All-out')
    if os.path.exists(archivo_excel):
        df_3m = pd.read_excel(archivo_excel, sheet_name='three_min_allout')
        atletas_3m = df_3m['athlete_id'].dropna().unique()
        
        atleta_sel = st.selectbox('Seleccionar Atleta', atletas_3m)
        
        if atleta_sel:
            data_atleta = df_3m[df_3m['athlete_id'] == atleta_sel].sort_values('time_s')
            # Criterio: CP = media 155-180s
            cp_3m = data_atleta[(data_atleta['time_s'] >= 155) & (data_atleta['time_s'] <= 180)]['power_W'].mean()
            # W' = Area above CP (5s intervals)
            w_p_3m = ((data_atleta['power_W'] - cp_3m).clip(lower=0) * 5).sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Potencia Crítica (CP)", f"{cp_3m:.1f} W")
            c2.metric("Capacidad Anaeróbica (W')", f"{w_p_3m:.0f} J")
            
            fig_3m = go.Figure()
            fig_3m.add_trace(go.Scatter(x=data_atleta['time_s'], y=data_atleta['power_W'], name='Potencia'))
            fig_3m.add_hline(y=cp_3m, line_dash='dash', line_color='red', annotation_text='CP Estimada')
            st.plotly_chart(fig_3m, use_container_width=True)
    else:
        st.error('Archivo no encontrado.')

# --- TAB 3: SIMULADOR HIIT ---
with tab3:
    st.header("Simulador de Cinética de W' balance")
    col_p1, col_p2, col_p3 = st.columns(3)
    u_cp = col_p1.number_input('CP (W)', 150, 450, 300)
    u_w = col_p2.number_input("W' (J)", 5000, 35000, 20000)
    u_reps = col_p3.slider('Repeticiones', 1, 15, 8)
    
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    w_int = col_s1.number_input('% Potencia Trabajo', 100, 150, 115)
    w_dur = col_s2.number_input('Segundos Trabajo', 10, 300, 60)
    r_int = col_s3.number_input('% Potencia Recuperación', 30, 90, 50)
    r_dur = col_s4.number_input('Segundos Recuperación', 10, 300, 120)

    t, w, res = simulate_w_bal(u_cp, u_w, w_int, w_dur, r_int, r_dur, reps=u_reps)
    
    fig_sim = go.Figure()
    fig_sim.add_trace(go.Scatter(x=t, y=np.array(w)/u_w*100, name="W'bal%"))
    fig_sim.update_layout(title=f'Estado de la sesión: {res}', yaxis_title="% W' Disponible", xaxis_title='Tiempo (s)')
    st.plotly_chart(fig_sim, use_container_width=True)
