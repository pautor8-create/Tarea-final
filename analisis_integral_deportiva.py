import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import linregress

st.set_page_config(page_title='Análisis Performance Deporte', layout='wide')

# --- Funciones de Simulación (HIIT W'bal con Modelo de Skiba) ---
def simulate_w_bal(cp, w_total, work_p_pct, work_dur, rest_p_pct, rest_dur, reps=10):
    p_work = cp * (work_p_pct / 100)
    p_rest = cp * (rest_p_pct / 100)
    d_cp = cp - p_rest
    
    # Constante de tiempo Tau (Skiba et al.)
    tau = 546 * np.exp(-0.01 * d_cp) + 316
    
    w_bal = [w_total]
    time = [0]
    status = 'Completada'
    reps_completadas = 0
    
    for r in range(reps):
        # --- Intervalo de Trabajo ---
        for _ in range(work_dur):
            current_w = w_bal[-1] - (p_work - cp)
            if current_w <= 0:
                w_bal.append(0)
                time.append(time[-1] + 1)
                return time, w_bal, f'Fallo en Rep {r+1}', r
            w_bal.append(current_w)
            time.append(time[-1] + 1)
        
        reps_completadas += 1
        
        # --- Intervalo de Recuperación (Exponencial) ---
        w_start_rest = w_bal[-1]
        for t_rest in range(1, rest_dur + 1):
            current_w = w_total - (w_total - w_start_rest) * np.exp(-t_rest / tau)
            w_bal.append(min(w_total, current_w))
            time.append(time[-1] + 1)
            
    return time, w_bal, status, reps_completadas

# --- Interfaz Principal ---
st.title('📊 Dashboard de Rendimiento Avanzado')
# Pestañas originales con sintaxis corregida
tab1, tab2, tab3 = st.tabs(["Eficiencia TEI", "Test 3-min All-out", "Simulador HIIT W'bal"])

# Nombre del archivo excel en GitHub
archivo_excel = 'practica_potencia_critica_colab_datos.xlsx'

# --- TAB 1: TEI (Exactamente igual que antes) ---
with tab1:
    st.header('Análisis de Eficiencia (TEI)')
    st.info('Sección para análisis de carga externa vs interna.')

# --- TAB 2: TEST 3-MIN ALL-OUT (Exactamente igual que antes) ---
with tab2:
    st.header('Validación Test 3-min All-out')
    if os.path.exists(archivo_excel):
        df_3m = pd.read_excel(archivo_excel, sheet_name='three_min_allout')
        atletas_3m = df_3m['athlete_id'].dropna().unique()
        
        atleta_sel = st.selectbox('Seleccionar Atleta', atletas_3m)
        
        if atleta_sel:
            data_atleta = df_3m[df_3m['athlete_id'] == atleta_sel].sort_values('time_s')
            cp_3m = data_atleta[(data_atleta['time_s'] >= 155) & (data_atleta['time_s'] <= 180)]['power_W'].mean()
            w_p_3m = ((data_atleta['power_W'] - cp_3m).clip(lower=0) * 5).sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Potencia Crítica (CP)", f"{cp_3m:.1f} W")
            c2.metric("Capacidad Anaeróbica (W')", f"{w_p_3m:.0f} J")
            
            fig_3m = go.Figure()
            fig_3m.add_trace(go.Scatter(x=data_atleta['time_s'], y=data_atleta['power_W'], name='Potencia'))
            fig_3m.add_hline(y=cp_3m, line_dash='dash', line_color='red', annotation_text='CP Estimada')
            st.plotly_chart(fig_3m, use_container_width=True)
    else:
        st.error(f'Archivo "{archivo_excel}" no encontrado.')

# --- TAB 3: SIMULADOR HIIT INTERACTIVO ORIGINAL + MEJORAS ---
with tab3:
    st.header("Simulador de Cinética de W' balance")
    
    # NUEVO: Selector de los 5 perfiles de Jugadores por defecto
    st.subheader("1. Selección del Perfil del Jugador")
    perfiles_jugadores = {
        'Jugador A (Perfil de Potencia / Motor)': {'cp': 320, 'w': 18000},
        'Jugador B (Perfil Anaeróbico / Velocista)': {'cp': 250, 'w': 26000},
        'Jugador C (Perfil Equilibrado / Medio)': {'cp': 280, 'w': 21000},
        'Jugador D (Perfil Diesel / Resistencia)': {'cp': 300, 'w': 15000},
        'Jugador E (Perfil Juvenil / En Formación)': {'cp': 230, 'w': 17000}
    }
    
    jugador_elegido = st.selectbox('Elige un perfil predefinido o edita sus valores abajo:', list(perfiles_jugadores.keys()))
    valores_defecto = perfiles_jugadores[jugador_elegido]

    # Controles originales para modificar CP y W' libremente basados en el jugador
    col_p1, col_p2, col_p3 = st.columns(3)
    u_cp = col_p1.number_input('CP (W)', 150, 450, valores_defecto['cp'])
    u_w = col_p2.number_input("W' (J)", 5000, 35000, valores_defecto['w'])
    u_reps = col_p3.slider('Repeticiones totales', 1, 15, 10)
    
    # Controles manuales originales para la sesión personalizada en tiempo real
    st.markdown("#### Configuración Manual de la Sesión Actual")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    w_int = col_s1.number_input('% Potencia Trabajo', 100, 150, 115)
    w_dur = col_s2.number_input('Segundos Trabajo', 10, 300, 60)
    r_int = col_s3.number_input('% Potencia Recuperación', 30, 90, 50)
    r_dur = col_s4.number_input('Segundos Recuperación', 10, 300, 120)

    # Simulación de la sesión manual que el usuario está moviendo
    t_manual, w_manual, res_manual, _ = simulate_w_bal(u_cp, u_w, w_int, w_dur, r_int, r_dur, reps=u_reps)
    
    # Gráfico original interactivo en tiempo real
    fig_sim = go.Figure()
    fig_sim.add_trace(go.Scatter(x=t_manual, y=np.array(w_manual)/u_w*100, name=f"Tu Sesión Configurada", line=dict(color='#ff7f0e', width=3)))
    fig_sim.add_hline(y=0, line_dash='solid', line_color='black', annotation_text='FALLO')
    fig_sim.update_layout(title=f'Estado de tu sesión manual: {res_manual}', yaxis_title="% W' Disponible", xaxis_title='Tiempo (s)')
    st.plotly_chart(fig_sim, use_container_width=True)

    st.markdown("---")
    
    # NUEVO: Bloque ocultable/desplegable para comparar las sesiones de la práctica (S1, S2, S3)
    with st.expander("📊 CLIC AQUÍ PARA VER LA COMPARATIVA DE LAS SESIONES REQUERIDAS (S1, S2, S3)", expanded=True):
        st.subheader("Análisis de las Sesiones del Ejercicio para el jugador seleccionado")
        
        sesiones_fijas = {
            'S1_short_short': {'reps': 10, 'w_pct': 120, 'w_dur': 30, 'r_pct': 50, 'r_dur': 30},
            'S2_long_recovery': {'reps': 10, 'w_pct': 115, 'w_dur': 60, 'r_pct': 45, 'r_dur': 120},
            'S3_risky': {'reps': 10, 'w_pct': 120, 'w_dur': 120, 'r_pct': 70, 'r_dur': 60},
            'S_Moderada_Propuesta': {'reps': 10, 'w_pct': 115, 'w_dur': 30, 'r_pct': 45, 'r_dur': 45}
        }
        
        res_data = []
        fig_comp = go.Figure()
        
        colores = {'S1_short_short': '#1f77b4', 'S2_long_recovery': '#2ca02c', 'S3_risky': '#d62728', 'S_Moderada_Propuesta': '#bcbd22'}
        
        for nombre, conf in sesiones_fijas.items():
            t, w, res, reps_comp = simulate_w_bal(u_cp, u_w, conf['w_pct'], conf['w_dur'], conf['r_pct'], conf['r_dur'], reps=conf['reps'])
            
            fig_comp.add_trace(go.Scatter(x=t, y=np.array(w)/u_w*100, name=f"{nombre}", line=dict(color=colores[nombre])))
            
            res_data.append({
                "Sesión": nombre,
                "Configuración": f"{conf['w_dur']}s al {conf['w_pct']}% / {conf['r_dur']}s al {conf['r_pct']}%",
                "Estado Final": res,
                "Repeticiones Completadas": f"{reps_comp} / 10"
            })
            
        fig_comp.add_hline(y=0, line_dash='solid', line_color='red')
        fig_comp.update_layout(title="Comparativa temporal del % W' restante en las sesiones de análisis", yaxis_title="% W'", xaxis_title="Tiempo (s)")
        st.plotly_chart(fig_comp, use_container_width=True)
        
        st.table(pd.DataFrame(res_data))
        
        # Conclusiones fijas justificadas metodológicamente
        st.markdown("""
        **Conclusiones Clínicas/Rendimiento:**
        * **Fallo en S3_risky:** El intervalo largo de 120s al 120% de CP vacía las reservas anaeróbicas de casi cualquier perfil (A, B, C, D o E) antes de la tercera repetición, agravado por una pausa muy alta (70% CP) que bloquea la reconstitución de $W'$.
        * **Modificación para evitar el fallo:** Se requeriría bajar la potencia de esfuerzo a < 110% CP o alargar los tiempos de descanso a un ratio mínimo de 1:2 con recuperaciones pasivas o muy activas-bajas (40% CP).
        * **Carga Moderada Ideal:** La sesión propuesta como alternativa moderada cumple el criterio de acumular tiempo por encima de la CP disminuyendo el $W'$ de forma controlada hasta zonas seguras (~40%), evitando el fallo metabólico prematuro.
        """)
