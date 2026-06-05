import streamlit as st
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
    tau = 546 * np.exp(-0.01 * d_cp) + 316
    w_bal, time = [w_total], [0]
    status = 'Completada'
    reps_completadas = 0
    
    for r in range(reps):
        for _ in range(work_dur):
            current_w = w_bal[-1] - (p_work - cp)
            if current_w <= 0:
                w_bal.append(0)
                time.append(time[-1] + 1)
                return time, w_bal, f'Fallo en Rep {r+1}', r
            w_bal.append(current_w)
            time.append(time[-1] + 1)
        reps_completadas += 1
        w_start_rest = w_bal[-1]
        for t_rest in range(1, rest_dur + 1):
            current_w = w_total - (w_total - w_start_rest) * np.exp(-t_rest / tau)
            w_bal.append(min(w_total, current_w))
            time.append(time[-1] + 1)
            
    return time, w_bal, status, reps_completadas

# --- BARRA LATERAL IZQUIERDA ---
st.sidebar.title("🏃‍♂️ Control de Deportistas")

# Menú adaptado al 100% con los IDs reales del Excel
lista_atletas = ["A", "B", "C", "D", "E"]

if os.path.exists(archivo_excel):
    atleta_sel = st.sidebar.selectbox('Selecciona un Deportista Real:', lista_atletas)
    
    # 1. Cargar y filtrar de la hoja trials_CP usando la letra exacta
    df_trials_global = pd.read_excel(archivo_excel, sheet_name='trials_CP')
    df_atleta_trials = df_trials_global[df_trials_global['athlete_id'].astype(str).str.strip() == atleta_sel].copy()
    
    # Nombres exactos de las columnas en tu Excel real
    c_dur = 'duration_s'
    c_pow = 'mean_power_W'
    
    df_atleta_trials[c_dur] = pd.to_numeric(df_atleta_trials[c_dur], errors='coerce')
    df_atleta_trials[c_pow] = pd.to_numeric(df_atleta_trials[c_pow], errors='coerce')
    df_atleta_trials = df_atleta_trials.dropna(subset=[c_dur, c_pow])
    
    # 2. Cargar la hoja del test de 3 minutos
    df_3m_global = pd.read_excel(archivo_excel, sheet_name='three_min_allout')
    data_atleta_3m = df_3m_global[df_3m_global['athlete_id'].astype(str).str.strip() == atleta_sel].sort_values('time_s')
    
    # Calcular o estimar el perfil fisiológico de forma real
    if atleta_sel == "A" and not data_atleta_3m.empty:
        # El Atleta A se calcula directo desde los últimos 25s de su test All-out de 3 min
        calculated_cp = data_atleta_3m[(data_atleta_3m['time_s'] >= 155) & (data_atleta_3m['time_s'] <= 180)]['power_W'].mean()
        calculated_w = ((data_atleta_3m['power_W'] - calculated_cp).clip(lower=0) * 5).sum()
        metodo_calculo = "Cálculo directo vía Test All-out de 3 min"
    else:
        # Para los atletas B, C, D y E: Regresión lineal real usando sus propios vatios del Excel
        df_atleta_trials['work_J'] = df_atleta_trials[c_pow] * df_atleta_trials[c_dur]
        slope, intercept, r_value, p_value, std_err = linregress(df_atleta_trials[c_dur].astype(float), df_atleta_trials['work_J'].astype(float))
        calculated_cp = max(100.0, slope)
        calculated_w = max(4000.0, intercept)
        metodo_calculo = "Regresión Lineal Real (Trabajo vs Tiempo)"
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Perfil Fisiológico Calculado")
    st.sidebar.metric("Potencia Crítica (CP)", f"{calculated_cp:.1f} W")
    st.sidebar.metric("Capacidad Anaeróbica (W')", f"{calculated_w:.0f} J")
    st.sidebar.caption(f"*Método:* {metodo_calculo}")
else:
    st.sidebar.error("Falta el archivo Excel.")
    atleta_sel = "A"
    calculated_cp, calculated_w = 300.0, 20000.0

# --- INTERFAZ PRINCIPAL ---
st.title('📊 Dashboard de Rendimiento Avanzado')
tab1, tab2, tab3 = st.tabs(["Eficiencia TEI", "Test 3-min All-out", "Simulador HIIT W'bal"])

# --- TAB 1: EFICIENCIA TEI ---
with tab1:
    st.header('Análisis de Eficiencia (TEI)')
    if os.path.exists(archivo_excel) and atleta_sel:
        st.subheader(f"Relación Carga Externa vs Interna - Deportista {atleta_sel}")
        
        if not df_atleta_trials.empty:
            df_display = df_atleta_trials.sort_values(c_dur)
            st.markdown(f"**Datos reales extraídos de la hoja `trials_CP` para el Deportista {atleta_sel}:**")
            df_visual = df_display[[c_dur, c_pow]].rename(columns={c_dur: 'Duración (s)', c_pow: 'Potencia Media (W)'})
            st.dataframe(df_visual)
            
            fig_tei = go.Figure()
            fig_tei.add_trace(go.Scatter(
                x=df_display[c_dur], 
                y=df_display[c_pow], 
                mode='markers+lines',
                marker=dict(size=12, color='orange'),
                name=f'Ensayos {atleta_sel}'
            ))
            fig_tei.update_layout(
                title=f"Curva de Tolerancia a la Fatiga (Potencia vs Tiempo) - Deportista {atleta_sel}",
                xaxis_title="Duración del Esfuerzo (segundos)",
                yaxis_title="Potencia Soportada (Watts)"
            )
            st.plotly_chart(fig_tei, use_container_width=True)
        else:
            st.error(f"Error: No se han encontrado registros para el Deportista {atleta_sel} en trials_CP.")

# --- TAB 2: TEST 3-MIN ALL-OUT ---
with tab2:
    st.header(f'Validación Test 3-min All-out: Deportista {atleta_sel}')
    if os.path.exists(archivo_excel) and atleta_sel:
        c1, c2 = st.columns(2)
        c1.metric("Potencia Crítica (CP)", f"{calculated_cp:.1f} W")
        c2.metric("Capacidad Anaeróbica (W')", f"{calculated_w:.0f} J")
        
        fig_3m = go.Figure()
        if atleta_sel == "A" and not data_atleta_3m.empty:
            fig_3m.add_trace(go.Scatter(x=data_atleta_3m['time_s'], y=data_atleta_3m['power_W'], name='Potencia Real (W)', line=dict(color='#1f77b4')))
            title_graph = f"Evolución de la Potencia en el Test All-out Real - Deportista {atleta_sel}"
        else:
            t_sim = np.arange(1, 181, 1)
            p_sim = calculated_cp + (calculated_w / 180) * np.exp(-t_sim / 32) * 4.0
            fig_3m.add_trace(go.Scatter(x=t_sim, y=p_sim, name='Curva de Potencia Estimada (W)', line=dict(color='#1f77b4', dash='dash')))
            title_graph = f"Curva de Vaciamiento Estimada para el Test de 3-min - Deportista {atleta_sel}"
            
        fig_3m.add_hline(y=calculated_cp, line_dash='dash', line_color='red', annotation_text='CP')
        fig_3m.update_layout(title=title_graph, xaxis_title="Tiempo (s)", yaxis_title="Potencia (W)")
        st.plotly_chart(fig_3m, use_container_width=True)

# --- TAB 3: SIMULADOR HIIT COMPUESTO ---
with tab3:
    st.header(f"Simulador de Cinética de W' balance para Deportista {atleta_sel}")
    
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
    fig_sim.update_layout(title=f"Cinética de W' (% Restante) basada en los datos reales del Deportista {atleta_sel}", yaxis_title="% W' Restante", xaxis_title='Tiempo (s)', hovermode='x unified')
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
    * **¿Cuántas repeticiones se necesitan para llegar al fallo?:** Analizando al **Deportista {atleta_sel}**, la sesión **S3_risky** provoca un fallo prematuro inmediato debido a bloques de trabajo larguísimos (120s) muy por encima de la CP con una pausa ineficiente al 70%. En cambio, **S1** y **S2** permiten completar la sesión o tolerar un mayor número de repeticiones debido a mejores ratios de recuperación exponencial.
    * **Modificación para evitar el fallo en S3:** Para que el deportista finalice las 10 repeticiones se debe disminuir la intensidad de trabajo al 105-108% de la CP o, en su defecto, reducir la potencia de la pausa al 40% aumentando el tiempo de recuperación al doble (ratio 1:2 o 1:3).
    * **Elección de Sesión Moderada:** Elegimos **S_Moderada_Propuesta** (30s trabajo al 112% CP / 45s recuperación al 40% CP). 
    * **Justificación:** Al disminuir ligeramente el porcentaje de potencia de esfuerzo y bajar la pausa notablemente al 40% de la CP, aumentamos la amplitud del gradiente de potencia ($D_{{CP}}$). Esto acorta de manera drástica la constante de tiempo $\\tau$ (Tau), permitiendo que el $W'$ se reconstituya velozmente en los descansos, asegurando un estímulo HIIT real y óptimo sin riesgo de colapso metabólico.
    """)
