# 🚴 Dashboard de Rendimiento: Potencia Crítica & W' Balance

Este repositorio contiene una aplicación web interactiva desarrollada en **Streamlit** y **Python** para el análisis avanzado de la carga externa y el perfil metabólico de deportistas de resistencia, basado en los modelos de **Potencia Crítica (CP)** y capacidad de trabajo anaeróbico (**W'**).

La aplicación ha sido optimizada para su despliegue y visualización tanto en entornos locales, servidores en la nube (Streamlit Cloud), como en cuadernos de **Google Colab**.

## 📊 Características de la Aplicación

El software se divide en tres módulos analíticos interactivos:
1. **Modelos de Potencia (Multi-Test):** Ajuste del modelo lineal (Trabajo-Tiempo: $W = CP \cdot t + W'$) y el modelo no lineal o hiperbólico (Potencia-Duración: $P(t) = CP + \frac{W'}{t}$) mediante regresión por mínimos cuadrados.
2. **Test 3-Min All-Out (3MT):** Estimación automatizada de la CP de fin de test (media de los últimos 30 segundos) y cálculo de la $W'$ mediante la integral del área bajo la curva de potencia segundo a segundo.
3. **Simulación de Intervalos (W' Balance):** Algoritmo predictivo en tiempo real que modela el vaciado y la tasa de reconstitución del tanque energético anaeróbico ($W'$ balance) frente a diferentes plantillas y picos de intensidad.

## 📁 Estructura del Repositorio

* `colab_notebook_export.py`: Código fuente principal de la aplicación web de Streamlit.
* `practica_potencia_critica_colab_datos.xlsx`: Base de datos en formato Excel que contiene los trials de esfuerzo, los datos a 1 Hz del test 3MT y las plantillas de entrenamiento.
* `requirements.txt`: Archivo de configuración con las dependencias necesarias del entorno (Streamlit, Pandas, Openpyxl, Scipy, Matplotlib).

## 🚀 Instrucciones de Ejecución en Google Colab

Si deseas ejecutar este ecosistema dentro de Google Colab utilizando **LocalTunnel** para abrir la interfaz gráfica, copia el bloque unificado en una celda y sigue estos pasos:
1. Sube el archivo `practica_potencia_critica_colab_datos.xlsx` al almacenamiento temporal de la sesión (icono de la carpeta 📁 a la izquierda).
2. Ejecuta la celda para instalar las dependencias y generar el archivo `app.py`.
3. Copia la dirección **IP pública** que te imprimirá la consola (contraseña de red).
4. Haz clic en el enlace generado por `localtunnel`, pega la IP en el campo *Endpoint IP* y presiona *Submit*.

## 🛠️ Tecnologías Utilizadas

* **Python 3.11+**
* **Streamlit** (Diseño de la interfaz de usuario)
* **SciPy** (Módulo estadístico para regresiones lineales)
* **Pandas** (Tratamiento y estructuración de matrices de datos)
* **Matplotlib** (Motor de renderizado de las gráficas fisiológicas)
