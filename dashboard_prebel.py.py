import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Prebel Analytics", layout="wide", page_icon="📊")

# Aplicar un estilo visual más limpio
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. ENLACE DE DATOS (Tu Google Sheets publicado como CSV)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTWbfjheQmmmkyZOxQRNyfgYSZ9AWvhOPsVnBrA-7f6MMOkH4RD2xBr3M9GpDVaFQ/pub?output=csv"

@st.cache_data(ttl=600) # Cache de 10 minutos
def cargar_datos(url):
    # Saltamos las primeras 4 filas decorativas de tu reporte
    df = pd.read_csv(url, skiprows=4)
    
    # Renombrar columnas para trabajar fácil
    df.columns = ['Cuentas', '2024', '2023']
    
    # Función para convertir "$472.759.275 M" en número real
    def limpiar_monto(valor):
        if pd.isna(valor) or valor == '-' or str(valor).strip() == '':
            return 0.0
        # Quitamos basura visual
        limpio = str(valor).replace('$', '').replace('M', '').replace('.', '').replace(' ', '').replace(',', '.')
        try:
            return float(limpio)
        except:
            return 0.0

    df['2024'] = df['2024'].apply(limpiar_monto)
    df['2023'] = df['2023'].apply(limpiar_monto)
    
    # Filtramos filas que no tienen nombre de cuenta o están vacías
    df = df.dropna(subset=['Cuentas'])
    df = df[df['2024'] + df['2023'] > 0] # Solo filas con valores
    
    return df

# 3. INTERFAZ DE USUARIO
st.title("📊 Informe Integral Prebel S.A.")
st.caption("Dashboard interactivo sincronizado con Google Sheets")

try:
    df_final = cargar_datos(CSV_URL)

    # Métricas clave en la parte superior
    c1, c2, c3 = st.columns(3)
    
    # Buscamos filas específicas para los KPIs
    ingresos = df_final[df_final['Cuentas'].str.contains("Ingresos", case=False, na=False)].iloc[0]
    costos = df_final[df_final['Cuentas'].str.contains("Costo de ventas", case=False, na=False)].iloc[0]
    
    with c1:
        crecimiento = ((ingresos['2024'] / ingresos['2023']) - 1) * 100
        st.metric("Ventas Totales 2024", f"${ingresos['2024']:,.0f}", f"{crecimiento:.1f}% vs 2023")
    
    with c2:
        st.metric("Costos Operativos", f"${costos['2024']:,.0f}", delta_color="inverse")
        
    with c3:
        utilidad = ingresos['2024'] - costos['2024']
        st.metric("Utilidad Bruta Est.", f"${utilidad:,.0f}")

    st.divider()

    # Gráficos
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("Comparativa por Cuenta (2024 vs 2023)")
        # Preparar datos para el gráfico
        df_plot = df_final.melt(id_vars='Cuentas', var_name='Año', value_name='Monto')
        fig = px.bar(df_plot, x='Cuentas', y='Monto', color='Año', barmode='group',
                     color_discrete_sequence=['#4F46E5', '#CBD5E1'],
                     template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with col_der:
        st.subheader("Estructura de Gastos")
        # Mostrar solo gastos principales
        gastos = df_final[df_final['Cuentas'].str.contains("Gastos", case=False, na=False)]
        fig_pie = px.pie(gastos, values='2024', names='Cuentas', hole=0.5)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tabla de datos crudos
    with st.expander("Ver tabla de datos detallada"):
        st.dataframe(df_final.style.format({"2024": "${:,.0f}", "2023": "${:,.0f}"}), use_container_width=True)

except Exception as e:
    st.error("⚠️ Error cargando datos. Verifica que el Google Sheets esté publicado como CSV.")
    st.info(f"Detalle técnico: {e}")

# Botón para refrescar
if st.sidebar.button('🔄 Sincronizar ahora'):
    st.cache_data.clear()
    st.rerun()