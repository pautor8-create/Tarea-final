import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

class AnalisisRendimiento:
    def __init__(self, excel_path="practica_potencia_critica_colab_datos.xlsx"):
        self.path = excel_path
        self.df_trials = None
        self.df_results = None

    def cargar_y_modelar(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"No se encuentra el archivo {self.path}")
        
        # Carga de datos de trials
        self.df_trials = pd.read_excel(self.path, sheet_name='trials_CP')
        self.df_trials['work_J'] = self.df_trials['mean_power_W'] * self.df_trials['duration_s']
        
        # Modelado Lineal por Atleta
        res = []
        for athlete in self.df_trials['athlete_id'].unique():
            subset = self.df_trials[self.df_trials['athlete_id'] == athlete]
            slope, intercept, r_val, _, _ = stats.linregress(subset['duration_s'], subset['work_J'])
            res.append({'athlete_id': athlete, 'CP_W': slope, 'W_prime_kJ': intercept/1000, 'R2': r_val**2})
        self.df_results = pd.DataFrame(res)
        print("\n[1] Parámetros de Potencia Crítica calculados para todos los atletas.")

    def generar_tabla_tte(self):
        intensities = [1.05, 1.10, 1.20, 1.30]
        tte_data = []
        for _, row in self.df_results.iterrows():
            cp, w_p = row['CP_W'], row['W_prime_kJ'] * 1000
            for pct in intensities:
                power = cp * pct
                tte_s = w_p / (power - cp)
                m, s = divmod(int(tte_s), 60)
                tte_data.append({'Atleta': row['athlete_id'], 'Intensidad': f"{int(pct*100)}% CP", 'TTE': f"{m:02d}:{s:02d}"})
        
        pivot = pd.DataFrame(tte_data).pivot(index='Atleta', columns='Intensidad', values='TTE')
        print("\n[2] Tabla de TTE (Tiempo hasta el agotamiento):")
        print(pivot)

    def analizar_3mt(self):
        try:
            df_3mt = pd.read_excel(self.path, sheet_name='three_min_allout')
            cp_3mt = df_3mt[df_3mt['time_s'] >= 150]['power_W'].mean()
            dt = 5
            w_p_3mt = ((df_3mt['power_W'] - cp_3mt).clip(lower=0) * dt).sum()
            print(f"\n[3] Análisis Test 3-min (Atleta A): CP={cp_3mt:.1f}W, W'={w_p_3mt/1000:.2f}kJ")
        except:
            print("\n[!] No se pudo procesar la hoja 'three_min_allout'.")

    def simular_hiit(self, athlete_id='A'):
        row = self.df_results[self.df_results['athlete_id'] == athlete_id].iloc[0]
        cp, w_p = row['CP_W'], row['W_prime_kJ'] * 1000
        
        # Simulación S3 (Risky): 120s @ 120% CP, Rec 60s @ 70% CP
        w_bal = w_p
        p_work = cp * 1.20
        p_rec = cp * 0.70
        tau = 546 * np.exp(-0.01 * (cp - p_rec)) + 316
        
        print(f"\n[4] Simulación HIIT S3 para Atleta {athlete_id}:")
        for rep in range(1, 11):
            w_bal -= (p_work - cp) * 120
            if w_bal <= 0:
                print(f"    -> Fallo en Repetición {rep}")
                break
            w_bal = w_p - (w_p - w_bal) * np.exp(-60 / tau)
            if rep == 10: print("    -> Sesión completada con éxito.")

if __name__ == '__main__':
    app = AnalisisRendimiento()
    try:
        app.cargar_y_modelar()
        app.generar_tabla_tte()
        app.analizar_3mt()
        app.simular_hiit('A')
        print("\n--- Análisis Finalizado ---")
    except Exception as e:
        print(f"Error: {e}")
