# ============================================================
# PROYECTO FINAL - PROGRAMACIÓN SIG
# Análisis espacial de servicios municipales
# Autora: Laura Mora Calvo
# ============================================================

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
from streamlit_folium import st_folium
import folium

# ------------------------------------------------------------
# Título e introducción de la aplicación
# ------------------------------------------------------------
st.title("Análisis espacial de servicios municipales")
st.write(
    "Esta aplicación interactiva analiza la distribución espacial de los "
    "servicios municipales utilizando información catastral, tablas, "
    "gráficos estadísticos y mapas interactivos. Los datos provienen de "
    "los archivos empleados en la Tarea 3 del curso."
)

# ------------------------------------------------------------
# Función para cargar los datos desde GitHub.
# Se utiliza cache para evitar recargas innecesarias.
# ------------------------------------------------------------

@st.cache_data
def cargar_datos():
    cuentas = pd.read_csv(
        "https://raw.githubusercontent.com/Laumora07/ProyectoFinal/main/cuentas.csv",
        sep=";"
    )

    servicios = pd.read_csv(
        "https://raw.githubusercontent.com/Laumora07/ProyectoFinal/main/servicios.csv",
        sep=";"
    )

    catastro = gpd.read_file(
        "https://raw.githubusercontent.com/Laumora07/ProyectoFinal/main/catastro.gpkg"
    )

    return cuentas, servicios, catastro

cuentas, servicios, catastro = cargar_datos()

st.success("Datos cargados correctamente")

# ------------------------------------------------------------
# Tabla de frecuencias de los servicios municipales registrados.
# ------------------------------------------------------------

st.header("Tabla de frecuencias")

st.write(
    "La siguiente tabla presenta la frecuencia de los servicios "
    "municipales registrados en la base de datos."
)

tabla = (
    servicios["descripcion_servicio"]
    .value_counts()
    .reset_index()
)

tabla.columns = ["Servicio", "Cantidad"]

st.dataframe(tabla)

# ------------------------------------------------------------
# Conversión de las llaves a texto para realizar correctamente
# las uniones entre las tablas.
# ------------------------------------------------------------

catastro["id_finca"] = catastro["id_finca"].astype(str)
cuentas["id_finca"] = cuentas["id_finca"].astype(str)

# ------------------------------------------------------------
# Integración de la información catastral con las cuentas y
# los servicios municipales.
# ------------------------------------------------------------

catastro_cuentas = catastro.merge(
    cuentas,
    on="id_finca",
    how="left"
)

# Unir con servicios
catastro_total = catastro_cuentas.merge(
    servicios,
    on="id_cuenta",
    how="left"
)

# ------------------------------------------------------------
# Filtro interactivo que permite seleccionar uno o más
# servicios municipales.
# ------------------------------------------------------------

st.header("Filtro interactivo")

servicios_seleccionados = st.multiselect(
    "Seleccione uno o más servicios:",
    options=sorted(catastro_total["descripcion_servicio"].dropna().unique()),
    default=sorted(catastro_total["descripcion_servicio"].dropna().unique())[:5]
)

datos_filtrados = catastro_total[
    catastro_total["descripcion_servicio"].isin(servicios_seleccionados)
]

if datos_filtrados.empty:
    st.warning("Seleccione al menos un servicio para visualizar la información.")
    st.stop()

st.subheader("Predios de los servicios seleccionados")

st.write(
    "La siguiente tabla muestra los registros correspondientes "
    "a los servicios seleccionados."
)

st.dataframe(
    datos_filtrados[
        [
            "id_finca",
            "descripcion_servicio",
            "monto_ibi"
        ]
    ]
)

st.header("Gráfico estadístico")

st.write(
    "El gráfico circular muestra la distribución de los servicios seleccionados por el usuario."
)

st.subheader("Distribución de los servicios seleccionados")

# ------------------------------------------------------------
# Gráfico circular que muestra la distribución de los
# servicios seleccionados.
# ------------------------------------------------------------

grafico = (
    datos_filtrados["descripcion_servicio"]
    .value_counts()
    .reset_index()
)

grafico.columns = ["Servicio", "Cantidad"]

fig = px.pie(
    grafico,
    names="Servicio",
    values="Cantidad",
    title="Distribución de los servicios seleccionados",
    hole=0.3
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# Creación del mapa interactivo con Folium.
# Se convierten las geometrías a coordenadas geográficas
# (EPSG:4326) para su correcta visualización.
# ------------------------------------------------------------

st.header("Mapa interactivo")

st.write(
    "El mapa muestra la ubicación de los predios correspondientes a los servicios seleccionados."
)

# Convertir a coordenadas geográficas
datos_mapa = datos_filtrados.to_crs(epsg=4326)

# Crear mapa base
m = folium.Map(
    location=[
        datos_mapa.total_bounds[1:4:2].mean(),
        datos_mapa.total_bounds[0:3:2].mean()
    ],
    zoom_start=16
)

# Dibujar las geometrías directamente
folium.GeoJson(
    datos_mapa[["id_finca", "descripcion_servicio", "geometry"]].to_json(),
    tooltip=folium.GeoJsonTooltip(
        fields=["id_finca", "descripcion_servicio"],
        aliases=["ID Finca", "Servicio"]
    ),
    style_function=lambda x: {
        "fillColor": "#4CAF50",
        "color": "#555555",
        "weight": 0.5,
        "fillOpacity": 0.4
    }
).add_to(m)

st_folium(
    m,
    width=900,
    height=600,
    key="mapa"
)