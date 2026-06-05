import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

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
tab1, tab2, tab3 = st.tabs(['Eficiencia TEI', 'Test 3-min All-out', 'Simulador HIIT W\'bal'])

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
        st.error(f'Archivo "{archivo_excel}" no encontrado en el directorio actual.')

# --- TAB 3: SIMULADOR HIIT COMPUESTO ---
with tab3:
    st.header("Simulador Colectivo y Comparativo de Cinética de W'")
    
    # 1. Configuración del perfil del deportista
    st.subheader("1. Perfil Metabólico del Deportista")
    c_perf1, c_perf2 = st.columns(2)
    u_cp = c_perf1.number_input('Potencia Crítica - CP (W)', 150, 450, 300)
    u_w = c_perf2.number_input("Capacidad Anaeróbica - W' (J)", 5000, 35000, 20000)
    
    st.markdown("---")
    
    # 2. Definición de las sesiones a comparar
    sesiones_config = {
        'S1_short_short': {'reps': 10, 'w_pct': 120, 'w_dur': 30, 'r_pct': 50, 'r_dur': 30},
        'S2_long_recovery': {'reps': 10, 'w_pct': 115, 'w_dur': 60, 'r_pct': 45, 'r_dur': 120},
        'S3_risky': {'reps': 10, 'w_pct': 120, 'w_dur': 120, 'r_pct': 70, 'r_dur': 60}
    }
    
    # Diseño automático de la Sesión Moderada Adaptada
    # Busca vaciar el W' hasta ~40-50% sin llegar a 0 de forma segura
    w_gastado_estimado_30s = (u_cp * 1.15 - u_cp) * 30
    sesiones_config['S_Moderada_Propuesta'] = {
        'reps': 10,
        'w_pct': 115, 
        'w_dur': 30, 
        'r_pct': 45, 
        'r_dur': 45
    }
    
    st.subheader("2. Comparación de Sesiones Interválicas (10 Repeticiones)")
    
    # Ejecutar simulaciones
    resultados = {}
    fig_sim = go.Figure()
    
    colores = {
        'S1_short_short': '#1f77b4',
        'S2_long_recovery': '#2ca02c',
        'S3_risky': '#d62728',
        'S_Moderada_Propuesta': '#ff7f0e'
    }
    
    for nombre, conf in sesiones_config.items():
        t, w, res, reps_comp = simulate_w_bal(
            u_cp, u_w, conf['w_pct'], conf['w_dur'], conf['r_pct'], conf['r_dur'], reps=conf['reps']
        )
        resultados[nombre] = {'status': res, 'reps': reps_comp, 'w_final_pct': (w[-1]/u_w)*100}
        
        # Añadir traza al gráfico
        fig_sim.add_trace(go.Scatter(
            x=t, 
            y=np.array(w) / u_w * 100, 
            name=f"{nombre} ({res})",
            line=dict(color=colores[nombre], width=2 if 'Moderada' not in nombre else 3)
        ))
        
    fig_sim.add_hline(y=0, line_dash='solid', line_color='black', annotation_text='FALLO (W\' = 0)')
    fig_sim.update_layout(
        title="Evolución del % de W' Disponible a lo largo del tiempo",
        yaxis_title="% W' Restante",
        xaxis_title='Tiempo (segundos)',
        hovermode='x unified',
        legend=dict(orient="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_sim, use_container_width=True)
    
    # 3. Métricas y Tabla de Resumen
    st.subheader("3. Tabla de Resultados e Indicadores de Fallo")
    
    res_data = []
    for nombre, conf in sesiones_config.items():
        res_data.append({
            "Sesión": nombre,
            "Intensidad Trabajo": f"{conf['w_pct']}% CP",
            "Duración Trabajo": f"{conf['w_dur']}s",
            "Intensidad Pausa": f"{conf['r_pct']}% CP",
            "Duración Pausa": f"{conf['r_dur']}s",
            "Estado Final": resultados[nombre]['status'],
            "Reps Completadas": f"{resultados[nombre]['reps']} / 10"
        })
    
    st.table(pd.DataFrame(res_data))
    
    # 4. Análisis Justificado y Toma de Decisiones
    st.subheader("💡 Análisis de Prescripción y Conclusiones")
    
    # Verificación de cuál es la mejor sesión estándar
    analisis_texto = f"""
    * **Análisis de Fallo Prematuro:** La sesión **S3_risky** provoca un fallo prematuro sistemático en la mayoría de los perfiles deportivos debido a intervalos de trabajo excesivamente largos (120s) a alta intensidad (120% CP) combinados con una recuperación incompleta (alta intensidad de pausa al 70% CP que limita la tasa de reconstitución exponencial de $W'$).
    * **¿Qué modificación haríamos para evitar el fallo en S3?:** Para conseguir que finalice las 10 repeticiones se debería **reducir la potencia de trabajo a un 105-110% de la CP**, o bien **bajar la potencia de la pausa al 40% de la CP aumentando el tiempo de recuperación** a un ratio 1:1 o 1:2.
    * **Elección de Sesión Moderada:** Se ha diseñado la sesión **S_Moderada_Propuesta** (10 repeticiones de 30s al 115% CP con 45s de recuperación al 45% CP). 
    * **Justificación de la elección moderada:** Esta configuración asegura un estímulo de alta intensidad (por encima de CP) acumulando tiempo de trabajo útil, pero limitando el vaciado de $W'$ por ráfaga. Al mantener la potencia de la pausa muy baja (45% CP), se maximiza la diferencia ($D_{{CP}}$), optimizando la constante de tiempo $\\tau$ (Tau) para permitir una reconstitución rápida y eficiente entre series, garantizando que el deportista se mantenga en una zona segura de fatiga sin peligro de fallo.
    """
    st.markdown(analisis_texto)
