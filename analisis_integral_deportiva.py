¡import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import linregress

st.set_page_config(page_title='Análisis Performance Deporte', layout='wide')

# Nombre exacto del archivo de Excel en tu GitHub
archivo_excel = 'practica_potencia_critica_colab_datos.xlsx'

# --- Funciones de Simulación (HIIT W'bal - Modelo de Skiba) ---
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

# --- BARRA LATERAL IZQUIERDA ---
st.sidebar.title("🏃‍♂️ Control de Deportistas")

# Mapeo de nombres visuales a los IDs reales dentro del Excel (Enteros en trials_CP, string en 3min)
mapeo_atletas = {
    "Deportista 1 (athlete_01)": {"id_trials": 1, "id_3m": "athlete_01"},
    "Deportista 2 (athlete_02)": {"id_trials": 2, "id_3m": "athlete_02"},
    "Deportista 3 (athlete_03)": {"id_trials": 3, "id_3m": "athlete_03"},
    "Deportista 4 (athlete_04)": {"id_trials": 4, "id_3m": "athlete_04"},
    "Deportista 5 (athlete_05)": {"id_trials": 5, "id_3m": "athlete_05"}
}

if os.path.exists(archivo_excel):
    atleta_visual = st.sidebar.selectbox('Selecciona un Deportista Real:', list(mapeo_atletas.keys()))
    
    id_trials_real = mapeo_atletas[atleta_visual]["id_trials"]
    id_3m_real = mapeo_atletas[atleta_visual]["id_3m"]
    
    # 1. Cargar y filtrar estrictamente de trials_CP usando el número entero real
    df_trials_global = pd.read_excel(archivo_excel, sheet_name='trials_CP')
    df_atleta_trials = df_trials_global[df_trials_global['athlete_id'] == id_trials_real].copy()
    
    cols = df_atleta_trials.columns.tolist()
    c_dur = 'duration' if 'duration' in cols else ('duration_s' if 'duration_s' in cols else cols[2])
    c_pow = 'power' if 'power' in cols else ('power_W' if 'power_W' in cols else cols[3])
    
    df_atleta_trials[c_dur] = pd.to_numeric(df_atleta_trials[c_dur], errors='coerce')
    df_atleta_trials[c_pow] = pd.to_numeric(df_atleta_trials[c_pow], errors='coerce')
    df_atleta_trials = df_atleta_trials.dropna(subset=[c_dur, c_pow])
    
    # 2. Buscar en la hoja de 3 minutos usando su ID de texto
    df_3m_global = pd.read_excel(archivo_excel, sheet_name='three_min_allout')
    data_atleta_3m = df_3m_global[df_3m_global['athlete_id'] == id_3m_real].sort_values('time_s')
    
    if not data_atleta_3m.empty:
        # Si tiene test de 3min (Deportista 1)
        calculated_cp = data_atleta_3m[(data_atleta_3m['time_s'] >= 155) & (data_atleta_3m['time_s'] <= 180)]['power_W'].mean()
        calculated_w = ((data_atleta_3m['power_W'] - calculated_cp).clip(lower=0) * 5).sum()
        metodo_calculo = "Cálculo directo vía Test All-out de 3 min"
    else:
        # Para deportistas 2 al 5: Regresión lineal real de sus ensayos de carga (Trabajo vs Tiempo)
        df_atleta_trials['work_J'] = df_atleta_trials[c_pow] * df_atleta_trials[c_dur]
        x_data = df_atleta_trials[c_dur].astype(float)
        y_data = df_atleta_trials['work_J'].astype(float)
        
        slope, intercept, r_value, p_value, std_err = linregress(x_data, y_data)
        calculated_cp = max(100.0, slope)
        calculated_w = max(4000.0, intercept)
        metodo_calculo = "Estimación matemática por Regresión Lineal de Ensayos Carga-Tiempo"
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Perfil Fisiológico Calculado")
    st.sidebar.metric("Potencia Crítica (CP)", f"{calculated_cp:.1f} W")
    st.sidebar.metric("Capacidad Anaeróbica (W')", f"{calculated_w:.0f} J")
    st.sidebar.caption(f"*Método:* {metodo_calculo}")
else:
    st.sidebar.error("Falta el archivo Excel.")
    atleta_visual = None
    calculated_cp, calculated_w = 300.0, 20000.0

# --- INTERFAZ PRINCIPAL ---
st.title('📊 Dashboard de Rendimiento Avanzado')
tab1, tab2, tab3 = st.tabs(["Eficiencia TEI", "Test 3-min All-out", "Simulador HIIT W'bal"])

# --- TAB 1: EFICIENCIA TEI ---
with tab1:
    st.header('Análisis de Eficiencia (TEI)')
    if os.path.exists(archivo_excel) and atleta_visual:
        st.subheader(f"Relación Carga Externa vs Interna - {atleta_visual}")
        
        df_display = df_atleta_trials.sort_values(c_dur)
        st.markdown("**Datos reales extraídos de la hoja `trials_CP` para este deportista:**")
        st.dataframe(df_display[[c_dur, c_pow]])
        
        fig_tei = go.Figure()
        fig_tei.add_trace(go.Scatter(
            x=df_display[c_dur], 
            y=df_display[c_pow], 
            mode='markers+lines',
            marker=dict(size=12, color='orange'),
            name=f'{atleta_visual}'
        ))
        fig_tei.update_layout(
            title=f"Curva de Tolerancia a la Fatiga (Potencia vs Tiempo) - {atleta_visual}",
            xaxis_title="Duración del Esfuerzo (segundos)",
            yaxis_title="Potencia Soportada (Watts)"
        )
        st.plotly_chart(fig_tei, use_container_width=True)

# --- TAB 2: TEST 3-MIN ALL-OUT ---
with tab2:
    st.header(f'Validación Test 3-min All-out: {atleta_visual}')
    if os.path.exists(archivo_excel) and atleta_visual:
        if not data_atleta_3m.empty:
            c1, c2 = st.columns(2)
            c1.metric("Potencia Crítica (CP)", f"{calculated_cp:.1f} W")
            c2.metric("Capacidad Anaeróbica (W')", f"{calculated_w:.0f} J")
            
            fig_3m = go.Figure()
            fig_3m.add_trace(go.Scatter(x=data_atleta_3m['time_s'], y=data_atleta_3m['power_W'], name='Potencia Real (W)', line=dict(color='#1f77b4')))
            fig_3m.add_hline(y=calculated_cp, line_dash='dash', line_color='red', annotation_text='CP (Estado Estable)')
            fig_3m.update_layout(title=f"Evolución de la Potencia en el Test de Vaciamiento - {atleta_visual}", xaxis_title="Tiempo (s)", yaxis_title="Potencia (W)")
            st.plotly_chart(fig_3m, use_container_width=True)
        else:
            st.info(f"El {atleta_visual} no registra una prueba All-out de 3 minutos en el Excel. Su perfil fisiológico ha sido resuelto matemáticamente mediante el modelo lineal de la pestaña TEI.")

# --- TAB 3: SIMULADOR HIIT COMPUESTO ---
with tab3:
    st.header(f"Simulador de Cinética de W' balance para {atleta_visual}")
    
    sesiones_config = {
        'S1_short_short': {'reps': 10, 'w_pct': 120, 'w_dur': 30, 'r_pct': 50, 'r_dur': 30},
        'S2_long_recovery': {'reps': 10, 'w_pct': 115, 'w_dur': 60, 'r_pct': 45, 'r_dur': 120},
        'S3_risky': {'reps': 10, 'w_pct': 120, 'w_dur': 120, 'r_pct': 70, 'r_dur': 60},
        'S_Moderada_Propuesta': {'reps': 10, 'w_pct': 112, 'w_dur': 30, 'r_pct': 40, 'r_dur': 45}
    }
    
    st.subheader("1. Evolución Temporal del W' en las Sesiones Solicitadas")
    
    resultados = {}
    fig_sim = go.Figure()
    colores = {'S1_short_short': '#1f77b4', 'S2_long_recovery': '#2ca02c', 'S3_risky': '#d62728', 'S_Moderada_Propuesta': '#ff7f0e'}
    
    for nombre, conf in sesiones_config.items():
        t, w, res, reps_comp = simulate_w_bal(
            calculated_cp, calculated_w, conf['w_pct'], conf['w_dur'], conf['r_pct'], conf['r_dur'], reps=conf['reps']
        )
        resultados[nombre] = {'status': res, 'reps': reps_comp}
        
        fig_sim.add_trace(go.Scatter(
            x=t, 
            y=np.array(w) / calculated_w * 100, 
            name=f"{nombre}",
            line=dict(color=colores[nombre], width=2 if 'Moderada' not in nombre else 3)
        ))
        
    fig_sim.add_hline(y=0, line_dash='solid', line_color='black', annotation_text='FALLO METABÓLICO')
    fig_sim.update_layout(title=f"Cinética de W' (% Restante) basada en el perfil real de {atleta_visual}", yaxis_title="% W' Restante", xaxis_title='Tiempo (s)', hovermode='x unified')
    st.plotly_chart(fig_sim, use_container_width=True)
    
    st.subheader("2. Tabla Comparativa de Resultados")
    res_data = []
    for nombre, conf in sesiones_config.items():
        res_data.append({
            "Sesión": nombre,
            "Trabajo": f"{conf['w_dur']}s al {conf['w_pct']}% CP",
            "Recuperación": f"{conf['r_dur']}s al {conf['r_pct']}% CP",
            "Estado Final": resultados[nombre]['status'],
            "Repeticiones Completadas": f"{resultados[nombre]['reps']} / 10"
        })
    st.table(pd.DataFrame(res_data))
    
    st.subheader("3. Justificación y Toma de Decisiones")
    st.markdown(f"""
    * **¿Cuántas repeticiones se necesitan para llegar al fallo?:** Analizando a **{atleta_visual}**, la sesión **S3_risky** provoca un fallo prematuro inmediato debido a bloques de trabajo larguísimos (120s) muy por encima de la CP con una pausa ineficiente al 70%. En cambio, **S1** y **S2** permiten completar la sesión o tolerar un mayor número de repeticiones debido a mejores ratios de recuperación exponencial.
    * **Modificación para evitar el fallo en S3:** Para que el deportista finalice las 10 repeticiones se debe disminuir la intensidad de trabajo al 105-108% de la CP o, en su defecto, reducir la potencia de la pausa al 40% aumentando el tiempo de recuperación al doble (ratio 1:2 o 1:3).
    * **Elección de Sesión Moderada:** Elegimos **S_Moderada_Propuesta** (30s trabajo al 112% CP / 45s recuperación al 40% CP). 
    * **Justificación:** Al disminuir ligeramente el porcentaje de potencia de esfuerzo y bajar la pausa notablemente al 40% de la CP, aumentamos la amplitud del gradiente de potencia ($D_{{CP}}$). Esto acorta de manera drástica la constante de tiempo $\\tau$ (Tau), permitiendo que el $W'$ se reconstituya velozmente en los descansos, asegurando un estímulo HIIT real y óptimo sin riesgo de colapso metabólico.
    """)
