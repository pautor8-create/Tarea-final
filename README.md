import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# Configuración de la interfaz premium
st.set_page_config(page_title='Analizador de Potencia Crítica', layout='wide')

st.title('🚴 Dashboard de Rendimiento: Potencia Crítica & W\' Balance')
st.markdown("Análisis avanzado de los modelos lineales y no lineales de carga externa a partir de test de esfuerzo.")

excel_file = 'practica_potencia_critica_colab_datos.xlsx'

# Verificar si el Excel está en el repositorio
if not os.path.exists(excel_file):
    st.error(f"❌ No se encuentra el archivo '{excel_file}' en tu repositorio de GitHub.")
    st.info("💡 Asegúrate de subir el archivo Excel a la misma carpeta de GitHub donde tienes este código para que la app pueda leer los datos automáticamente.")
else:
    # ==========================================
    # 1. CARGA Y PROCESAMIENTO DE DATOS BASE
    # ==========================================
    @st.cache_data
    def cargar_y_modelar(path):
        df_data = pd.read_excel(path, sheet_name='trials_CP')
        df_data['work_J'] = df_data['mean_power_W'] * df_data['duration_s']
        
        athlete_models = {}
        for athlete in df_data['athlete_id'].unique():
            subset = df_data[df_data['athlete_id'] == athlete].sort_values('duration_s')
            slope, intercept, r_value, _, _ = stats.linregress(subset['duration_s'], subset['work_J'])
            athlete_models[athlete] = {
                'CP': slope,
                'W_prime': intercept,
                'R2': r_value**2,
                'data': subset
            }
        return athlete_models, df_data

    models, df_raw = cargar_y_modelar(excel_file)
    atletas_disponibles = sorted(list(models.keys()))

    # BARRA LATERAL: Selector de Atleta
    st.sidebar.header("🎛️ Panel de Control")
    atleta_sel = st.sidebar.selectbox("Selecciona el Deportista a analizar:", options=atletas_disponibles)

    # Datos específicos del atleta seleccionado
    cp_atleta = models[atleta_sel]['CP']
    w_prime_atleta = models[atleta_sel]['W_prime']
    r2_atleta = models[atleta_sel]['R2']
    df_atleta = models[atleta_sel]['data']

    # KPIs superiores del perfil metabólico
    col1, col2, col3 = st.columns(3)
    col1.metric("Potencia Crítica (CP)", f"{cp_atleta:.1f} W", help="Umbral metabólico máximo en estado estable.")
    col2.metric("Capacidad Anaeróbica (W')", f"{w_prime_atleta/1000:.2f} kJ", help="Tanque de energía disponible por encima de la CP.")
    col3.metric("Bondad de Ajuste ($R^2$)", f"{r2_atleta:.4f}", help="Precisión matemática del modelo lineal ajustado.")

    st.divider()

    # ==========================================
    # DISEÑO DE PESTAÑAS INTERACTIVAS
    # ==========================================
    tab1, tab2, tab3 = st.tabs([
        "📊 Modelos de Potencia (Multi-Test)", 
        "⏱️ Test 3-Min All-Out (3MT)", 
        "🏃 Simulación de Intervalos"
    ])

    # PESTAÑA 1: MODELOS MULTI-TEST
    with tab1:
        st.subheader(f"📈 Ajuste de Modelos Fisiológicos: {atleta_sel}")
        c1, c2 = st.columns(2)
        
        t_plot = np.linspace(df_atleta['duration_s'].min() * 0.8, df_atleta['duration_s'].max() * 1.2, 100)
        
        with c1:
            st.markdown("#### Modelo Lineal: Trabajo vs Tiempo")
            fig1, ax1 = plt.subplots(figsize=(6, 4.5))
            ax1.scatter(df_atleta['duration_s'], df_atleta['work_J'], color='#1f77b4', s=90, edgecolors='black', label='Tests Reales', zorder=3)
            ax1.plot(t_plot, cp_atleta * t_plot + w_prime_atleta, 'b--', linewidth=2, label=f'Ajuste (Recta $W = CP \cdot t + W\'$)')
            ax1.set_xlabel('Duración del esfuerzo (s)')
            ax1.set_ylabel('Trabajo acumulado (J)')
            ax1.legend()
            ax1.grid(True, linestyle=':', alpha=0.6)
            st.pyplot(fig1)
            
        with c2:
            st.markdown("#### Modelo No Lineal: Potencia vs Duración")
            fig2, ax2 = plt.subplots(figsize=(6, 4.5))
            ax2.scatter(df_atleta['duration_s'], df_atleta['mean_power_W'], color='#d62728', s=90, edgecolors='black', label='Tests Reales', zorder=3)
            ax2.plot(t_plot, cp_atleta + (w_prime_atleta / t_plot), 'r-', linewidth=2, label="Curva Hipérbola ($P = CP + W\'/t$)")
            ax2.set_xlabel('Duración del esfuerzo (s)')
            ax2.set_ylabel('Potencia media (W)')
            ax2.legend()
            ax2.grid(True, linestyle=':', alpha=0.6)
            st.pyplot(fig2)

    # PESTAÑA 2: TEST DE 3 MINUTOS ALL-OUT
    with tab2:
        st.subheader(f"⏱️ Análisis del Test 3-Min All-Out: {atleta_sel}")
        try:
            df_3mt_all = pd.read_excel(excel_file, sheet_name='three_min_allout')
            df_3mt = df_3mt_all[df_3mt_all['athlete_id'] == atleta_sel].sort_values('time_s')
            
            if df_3mt.empty:
                st.warning(f"No hay registros de Test 3MT para el deportista {atleta_sel} en el Excel.")
            else:
                last_30s = df_3mt[df_3mt['time_s'] >= 150]
                cp_3mt = last_30s['power_W'].mean()
                df_3mt['work_above_CP'] = (df_3mt['power_W'] - cp_3mt).apply(lambda x: max(0, x))
                w_prime_3mt = df_3mt['work_above_CP'].sum()
                
                cx1, cx2 = st.columns(2)
                cx1.metric("CP de Fin de Test (3MT)", f"{cp_3mt:.1f} W", delta=f"{cp_3mt - cp_atleta:+.1f} W vs Multi-Test")
                cx2.metric("W' Agotada en Test", f"{w_prime_3mt/1000:.2f} kJ", delta=f"{(w_prime_3mt - w_prime_atleta)/1000:+.2f} kJ vs Multi-Test")
                
                fig3, ax3 = plt.subplots(figsize=(12, 4.5))
                ax3.plot(df_3mt['time_s'], df_3mt['power_W'], color='purple', linewidth=2, label='Potencia Real (1 Hz)')
                ax3.axhline(cp_3mt, color='black', linestyle='--', linewidth=1.5, label=f'Límite Aeróbico Máximo (CP: {cp_3mt:.1f}W)')
                ax3.fill_between(df_3mt['time_s'], df_3mt['power_W'], cp_3mt, where=(df_3mt['power_W'] > cp_3mt), color='purple', alpha=0.15, label="Capacidad Anaeróbica Vaciada (W')")
                ax3.set_xlabel("Tiempo transcurrido (s)")
                ax3.set_ylabel("Potencia mecánica (W)")
                ax3.legend(loc='upper right')
                ax3.grid(True, linestyle=':', alpha=0.5)
                st.pyplot(fig3)
        except Exception as e:
            st.error(f"Error procesando la pestaña 3MT: {e}")

    # PESTAÑA 3: SIMULACIÓN DE INTERVALOS (MÓDULO INTELIGENTE ARREGLADO)
    with tab3:
        st.subheader(f"🏃 Prescripción y Tolerancia de Series de Entrenamiento: {atleta_sel}")
        try:
            df_temp_all = pd.read_excel(excel_file, sheet_name='interval_templates')
            df_temp = df_temp_all[df_temp_all['athlete_id'] == atleta_sel].reset_index(drop=True)
            
            if df_temp.empty:
                st.warning(f"No hay plantillas de intervalos diseñadas para {atleta_sel} en el Excel.")
            else:
                # DETECTOR INTELIGENTE DE COLUMNAS: Evita el KeyError buscando sin importar mayúsculas o sufijos
                col_intensidad = [c for c in df_temp.columns if 'intens' in c.lower()][0]
                col_duracion = [c for c in df_temp.columns if 'durat' in c.lower() or 'tiemp' in c.lower()][0]
                
                w_balance = w_prime_atleta
                historial_wb = []
                tiempos_acumulados = []
                t_actual = 0
                
                # Ejecutar la dinámica interna del tanque de energía W'
                for idx, row in df_temp.iterrows():
                    p_int = row[col_intensidad]
                    d_int = row[col_duracion]
                    
                    for _ in range(int(d_int)):
                        t_actual += 1
                        if p_int > cp_atleta:
                            w_balance -= (p_int - cp_atleta)
                        else:
                            w_balance = min(w_prime_atleta, w_balance + (cp_atleta - p_int))
                        historial_wb.append(w_balance)
                        tiempos_acumulados.append(t_actual)
                
                # Alertas profesionales según el balance final
                min_wb = min(historial_wb)
                if min_wb < 0:
                    st.error(f"⚠️ **ALERTA DE RENDIMIENTO:** La sesión propuesta supera los límites fisiológicos de {atleta_sel}. El tanque de $W'$ se agota por debajo de cero ({min_wb/1000:.1f} kJ). ¡Peligro de pájara o colapso neuromuscular!")
                else:
                    st.success(f"✅ **SESIÓN TOLERABLE:** El deportista {atleta_sel} cuenta con el perfil metabólico necesario para completar la sesión de intervalos de forma óptima (Balance mínimo: {min_wb/1000:.1f} kJ).")
                
                # Gráfico del vaciado de W' balance en tiempo real
                fig4, ax4 = plt.subplots(figsize=(12, 4.5))
                ax4.plot(tiempos_acumulados, np.array(historial_wb)/1000, color='#e67e22', linewidth=2.5, label="Balance actual de W' (kJ)")
                ax4.axhline(0, color='red', linestyle='-', alpha=0.5, linewidth=1)
                ax4.fill_between(tiempos_acumulados, np.array(historial_wb)/1000, 0, where=(np.array(historial_wb) >= 0), color='#e67e22', alpha=0.1)
                ax4.set_xlabel("Tiempo total de la sesión (s)")
                ax4.set_ylabel("Energía Anaeróbica Disponible (kJ)")
                ax4.set_title("DINÁMICA DE RECONSTITUCIÓN Y VACIADO DEL W' BALANCE")
                ax4.grid(True, linestyle=':', alpha=0.5)
                ax4.legend(loc='lower left')
                st.pyplot(fig4)
                
                st.markdown("### 📋 Desglose de las series propuestas en el Excel")
                # Mostrar la tabla renombrando temporalmente las columnas para que el usuario las lea claras
                df_mostrar = df_temp[[col_intensidad, col_duracion]].copy()
                df_mostrar.columns = ['Potencia del Intervalo (W)', 'Duración (s)']
                st.dataframe(df_mostrar, use_container_width=True)
        except Exception as e:
            st.error(f"Error simulando las series: {e}")
