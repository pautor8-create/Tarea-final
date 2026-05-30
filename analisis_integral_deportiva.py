import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# Configuración premium del Dashboard de Rendimiento
st.set_page_config(page_title="Analizador Fisiológico de Potencia", layout="wide")

st.title("🚴 Dashboard de Rendimiento: Potencia Crítica & W' Balance")
st.markdown("Cálculo avanzado de perfiles metabólicos, predicción de TTE y modelado dinámico de HIIT.")

excel_file = 'practica_potencia_critica_colab_datos.xlsx'

if not os.path.exists(excel_file):
    st.error(f"❌ No se encuentra el archivo '{excel_file}' en tu repositorio de GitHub.")
    st.info("💡 Sube el archivo Excel a la misma carpeta de GitHub para que la aplicación pueda procesar las pestañas.")
else:
    # ==========================================
    # 1. CARGA Y MODELADO DE DATOS (trials_CP)
    # ==========================================
    @st.cache_data
    def procesar_datos_atleta(path):
        df_trials = pd.read_excel(path, sheet_name='trials_CP')
        df_trials['work_J'] = df_trials['mean_power_W'] * df_trials['duration_s']
        
        athlete_models = {}
        for athlete in df_trials['athlete_id'].unique():
            subset = df_trials[df_trials['athlete_id'] == athlete].sort_values('duration_s')
            slope, intercept, r_val, _, _ = stats.linregress(subset['duration_s'], subset['work_J'])
            athlete_models[athlete] = {
                'CP': slope,
                'W_prime': intercept,
                'R2': r_val**2,
                'data': subset
            }
        return athlete_models, df_trials

    models, df_raw = procesar_datos_atleta(excel_file)
    atletas_disponibles = sorted(list(models.keys()))

    # PANEL LATERAL INTERACTIVO
    st.sidebar.header("🎛️ Panel de Control")
    atleta_sel = st.sidebar.selectbox("Selecciona el Atleta a analizar:", options=atletas_disponibles)

    cp_atleta = models[atleta_sel]['CP']
    w_prime_atleta = models[atleta_sel]['W_prime']
    r2_atleta = models[atleta_sel]['R2']
    df_atleta = models[atleta_sel]['data']

    # KPIs Fisiológicos principales
    col1, col2, col3 = st.columns(3)
    col1.metric("Potencia Crítica (CP)", f"{cp_atleta:.1f} W", help="Máximo estado estable metabólico.")
    col2.metric("Capacidad Anaeróbica (W')", f"{w_prime_atleta/1000:.2f} kJ", help="Energía disponible por encima de la CP.")
    col3.metric("Ajuste del Modelo ($R^2$)", f"{r2_atleta:.4f}", help="Bondad de ajuste de la regresión.")

    st.divider()

    # PESTAÑAS DE LA INTERFAZ
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Ajuste de Modelos", 
        "⏱️ Predicción TTE", 
        "⚡ Test 3-Min All-Out (3MT)", 
        "🏃 Simulación HIIT Avanzada"
    ])

    # PESTAÑA 1: GRÁFICOS DE AJUSTE
    with tab1:
        st.subheader(f"📈 Curvas Fisiológicas de Potencia: Atleta {atleta_sel}")
        c1, c2 = st.columns(2)
        t_plot = np.linspace(df_atleta['duration_s'].min() * 0.8, df_atleta['duration_s'].max() * 1.2, 100)
        
        with c1:
            fig1, ax1 = plt.subplots(figsize=(6, 4.2))
            ax1.scatter(df_atleta['duration_s'], df_atleta['work_J'], color='blue', s=80, edgecolors='black', label='Tests Reales')
            ax1.plot(t_plot, cp_atleta * t_plot + w_prime_atleta, 'b--', label=f'Ajuste Lineal (CP: {cp_atleta:.1f}W)')
            ax1.set_title('Gráfico Trabajo - Tiempo')
            ax1.set_xlabel('Duración (s)')
            ax1.set_ylabel('Trabajo Total (J)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            st.pyplot(fig1)
            
        with c2:
            fig2, ax2 = plt.subplots(figsize=(6, 4.2))
            ax2.scatter(df_atleta['duration_s'], df_atleta['mean_power_W'], color='red', s=80, edgecolors='black', label='Tests Reales')
            ax2.plot(t_plot, cp_atleta + (w_prime_atleta / t_plot), 'r-', linewidth=2, label="Modelo $P(t) = CP + W'/t$")
            ax2.set_title('Gráfico Potencia - Duración')
            ax2.set_xlabel('Duración (s)')
            ax2.set_ylabel('Potencia Media (W)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig2)

    # PESTAÑA 2: TABLA TTE INTERACTIVA
    with tab2:
        st.subheader("⏱️ Tiempo hasta el Agotamiento Estimado (TTE)")
        st.markdown("Predicción exacta del tiempo de tolerancia metabólica para diferentes porcentajes por encima de la CP.")
        
        intensities = [1.05, 1.10, 1.20, 1.30]
        tte_data = []
        for pct in intensities:
            power = cp_atleta * pct
            tte_s = w_prime_atleta / (power - cp_atleta)
            m, s = divmod(int(tte_s), 60)
            tte_data.append({
                'Porcentaje': f"{int(pct*100)}% CP",
                'Potencia Objetivo': f"{power:.1f} W",
                'Tiempo Límite (TTE)': f"{m:02d}:{s:02d} min"
            })
        st.table(pd.DataFrame(tte_data))

    # PESTAÑA 3: TEST DE 3 MINUTOS
    with tab3:
        st.subheader("⚡ Análisis Fisiológico del Test 3MT")
        try:
            df_3mt_all = pd.read_excel(excel_file, sheet_name='three_min_allout')
            df_3mt = df_3mt_all[df_3mt_all['athlete_id'] == atleta_sel].sort_values('time_s')
            
            if df_3mt.empty:
                st.info(f"No se registran datos del test 3MT para el atleta {atleta_sel} en este archivo.")
            else:
                cp_3mt = df_3mt[df_3mt['time_s'] >= 150]['power_W'].mean()
                # Ajustamos el diferencial dt basándonos en la frecuencia real detectada en las filas
                dt = 5 if len(df_3mt) <= 40 else 1 
                w_p_3mt = ((df_3mt['power_W'] - cp_3mt).clip(lower=0) * dt).sum()
                
                cx1, cx2 = st.columns(2)
                cx1.metric("CP Final (3MT)", f"{cp_3mt:.1f} W")
                cx2.metric("W' Agotada", f"{w_p_3mt/1000:.2f} kJ")
                
                fig3, ax3 = plt.subplots(figsize=(12, 4))
                ax3.plot(df_3mt['time_s'], df_3mt['power_W'], color='purple', label='Potencia Real')
                ax3.axhline(cp_3mt, color='black', linestyle='--', label=f'CP: {cp_3mt:.1f}W')
                ax3.fill_between(df_3mt['time_s'], df_3mt['power_W'], cp_3mt, where=(df_3mt['power_W'] > cp_3mt), color='purple', alpha=0.15)
                ax3.set_xlabel('Tiempo (s)')
                ax3.set_ylabel('Potencia (W)')
                ax3.legend()
                ax3.grid(True, alpha=0.3)
                st.pyplot(fig3)
        except Exception as e:
            st.error(f"Pestaña 3MT no disponible o con formato diferente: {e}")

    # PESTAÑA 4: SIMULACIÓN HIIT CON EXPONENCIAL (TAU)
    with tab4:
        st.subheader("🏃 Modelo Dinámico de HIIT: Simulación S3 (Risky)")
        st.markdown("Simulación matemática de la fatiga aplicando el modelo no lineal de reconstitución de la energía anaeróbica.")
        
        p_work = cp_atleta * 1.20
        p_rec = cp_atleta * 0.70
        # Fórmula exponencial del script original para calcular la constante de tiempo Tau
        tau = 546 * np.exp(-0.01 * (cp_atleta - p_rec)) + 316
        
        st.caption(f"**Constante Fisiológica de Recuperación (Tau):** {tau:.1f} segundos.")
        
        w_bal = w_prime_atleta
        historial_hiit = []
        segundos_eje = []
        tiempo_total = 0
        fallo_detectado = False
        rep_fallo = 0
        
        for rep in range(1, 11):
            # Fase de Trabajo: 120 segundos segundo a segundo
            for _ in range(120):
                tiempo_total += 1
                w_bal -= (p_work - cp_atleta)
                historial_hiit.append(w_bal)
                segundos_eje.append(tiempo_total)
                
            if w_bal <= 0 and not fallo_detectado:
                fallo_detectado = True
                rep_fallo = rep
                
            # Fase de Recuperación: 60 segundos aplicando decaimiento exponencial (Tau)
            w_inicial_rec = w_bal
            for _ in range(60):
                tiempo_total += 1
                # Reconstitución segundo a segundo basada en la distancia al máximo tanque
                w_bal = w_prime_atleta - (w_prime_atleta - w_inicial_rec) * np.exp(-1 / tau)
                historial_hiit.append(w_bal)
                segundos_eje.append(tiempo_total)

        if fallo_detectado:
            st.error(f"⚠️ **FALLO FISIOLÓGICO:** El deportista {atleta_sel} entra en el punto de agotamiento limitante en la **Repetición {rep_fallo}**.")
        else:
            st.success(f"✅ **SESIÓN COMPLETADA:** El deportista {atleta_sel} asimila correctamente las 10 repeticiones de la sesión de intervalos.")
            
        # Graficar dinámica de la simulación HIIT
        fig4, ax4 = plt.subplots(figsize=(12, 4.5))
        ax4.plot(segundos_eje, np.array(historial_hiit)/1000, color='darkorange', linewidth=2, label="W' balance (kJ)")
        ax4.axhline(0, color='red', linestyle='--', alpha=0.7)
        ax4.set_xlabel("Tiempo acumulado de la sesión (s)")
        ax4.set_ylabel("Tanque de Energía Anaeróbica (kJ)")
        ax4.set_title("EVOLUCIÓN EN TIEMPO REAL DEL W' BALANCE CON CONSTANTE TAU")
        ax4.grid(True, linestyle=':', alpha=0.5)
        ax4.legend()
        st.pyplot(fig4)
