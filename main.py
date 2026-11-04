import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen
from streamlit_folium import st_folium
import html
import datetime

st.set_page_config(
    page_title="Centro de Operación Nacional | Mapa Táctico C5",
    page_icon="🗺️",
    layout="wide"
)

# --- ESTILOS VISUALES Y FONDO TÁCTICO DE LA BANDERA ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    
    /* Fondo con la Bandera de Panamá más clara y viva (Opacidad reducida al 50%) */
    .bg-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-image: linear-gradient(rgba(11, 15, 25, 0.50), rgba(11, 15, 25, 0.50)), url("https://upload.wikimedia.org/wikipedia/commons/a/ab/Flag_of_Panama.svg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        z-index: -99998;
        pointer-events: none;
    }

    /* Sombras en el texto general para asegurar que se lea bien sobre el fondo más claro */
    .stApp, .block-container, [data-testid="stVerticalBlock"] {
        background: transparent !important;
        color: #ffffff;
        text-shadow: 0px 1px 3px rgba(0,0,0,0.8);
    }
    
    /* Panel Lateral Transparente (Cristal Ahumado) para ver la bandera */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 10, 15, 0.35) !important;
        border-right: 3px solid transparent;
        border-image: linear-gradient(to bottom, #0000FF, #FFFFFF, #FF0000) 1;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: transparent !important;
    }
    
    @keyframes neonBorderMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Contenedor Transparente con Borde Neón Patriótico */
    .neon-title-container {
        border: 4px solid transparent;
        /* El primer 'transparent' elimina el fondo oscuro interno */
        background: linear-gradient(transparent, transparent), 
                    linear-gradient(90deg, #0000FF 10%, #FFFFFF 50%, #FF0000 90%);
        background-origin: border-box;
        background-clip: padding-box, border-box;
        background-size: 200% 200%;
        animation: neonBorderMove 6s ease infinite;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: -15px 0 25px rgba(0, 0, 255, 0.6), 0 0 25px rgba(255, 255, 255, 0.5), 15px 0 25px rgba(255, 0, 0, 0.6);
        margin-bottom: 20px;
    }
    
    /* Título con bloques de color definidos: Azul, Blanco y Rojo */
    .neon-title-text {
        font-size: 28px;
        font-weight: 900;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        letter-spacing: 1.5px;
        background: linear-gradient(90deg, #0000FF 0%, #0000FF 30%, #FFFFFF 45%, #FFFFFF 55%, #FF0000 70%, #FF0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        /* Sombra oscura fuerte para que resalte sin importar el color del fondo */
        filter: drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.9)); 
    }
    
    .neon-sub-text {
        color: #ffffff;
        font-size: 13px;
        font-style: italic;
        margin-top: 8px;
        text-shadow: 0px 2px 5px rgba(0, 0, 0, 0.9);
    }
    </style>
    <div class="bg-overlay"></div>
""", unsafe_allow_html=True)

# --- ENCABEZADO PRINCIPAL ---
st.markdown("""
    <div class="neon-title-container">
        <div class="neon-title-text">🛰️ CENTRO DE OPERACIÓN NACIONAL | BITÁCORA DESFILES PATRIOS</div>
        <div class="neon-sub-text">SISTEMA DE GEORREFERENCIACIÓN Y CONTROL OPERATIVO</div>
    </div>
""", unsafe_allow_html=True)

# --- CONEXIÓN OPTIMIZADA A GOOGLE SHEETS ---
@st.cache_data(ttl=45)
def cargar_datos_bitacora():
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuFSvR6xnmXiAz4JRGVfrIDHdPVRV2fKM4jkPNKhW_Y-cRLlbJOI_O0SYZNDu6puEaYqcZd4hDWh20/pub?output=csv&gid=1525160468"
    df_raw = pd.read_csv(url_csv, header=None)
    
    fila_encabezado = 0
    for i, row in df_raw.head(10).iterrows():
        fila_texto = " ".join([str(val).upper().strip() for val in row.values])
        if "ZONA" in fila_texto and ("HORA" in fila_texto or "DÍA" in fila_texto or "DIA" in fila_texto):
            fila_encabezado = i
            break
    
    df = df_raw.iloc[fila_encabezado+1:].copy()
    df.columns = df_raw.iloc[fila_encabezado].astype(str).str.strip().str.upper()
    df = df.reset_index(drop=True)
    return df

try:
    df = cargar_datos_bitacora()

    # Limpieza de coordenadas
    col_lat = next((c for c in df.columns if "LAT" in c), None)
    col_lon = next((c for c in df.columns if "LON" in c or "LNG" in c), None)

    if col_lat and col_lon:
        df['Lat_clean'] = pd.to_numeric(
            df[col_lat].astype(str).str.replace(',', '.', regex=False).str.replace(r'[^0-9.\-]', '', regex=True), 
            errors='coerce'
        )
        df['Lon_clean'] = pd.to_numeric(
            df[col_lon].astype(str).str.replace(',', '.', regex=False).str.replace(r'[^0-9.\-]', '', regex=True), 
            errors='coerce'
        )
        df_geo = df.dropna(subset=['Lat_clean', 'Lon_clean']).copy()
        df_geo = df_geo[(df_geo['Lat_clean'] != 0) & (df_geo['Lon_clean'] != 0)]
    else:
        df_geo = pd.DataFrame()

    # Identificación de columnas descriptivas
    col_num = next((c for c in df.columns if "N°" in c or "NO" in c or "ID" in c or "NUM" in c), None)
    col_dia = next((c for c in df.columns if "DIA" in c or "FECHA" in c), None)
    col_hora = next((c for c in df.columns if "HORA" in c), None)
    col_zona = next((c for c in df.columns if "ZONA" in c or "SERVICIO" in c), None)
    col_centro = next((c for c in df.columns if "CENTRO" in c or "LUGAR" in c), None)
    col_rep = next((c for c in df.columns if "REPORTE" in c or "INCIDENTE" in c or "DETALLE" in c), None)

    # Convertir fechas para el filtro
    if col_dia and not df_geo.empty:
        df_geo['Fecha_dt'] = pd.to_datetime(df_geo[col_dia], dayfirst=True, errors='coerce')

    # --- PANEL LATERAL Y FILTROS ---
    with st.sidebar:
        st.markdown("### ⚙️ Panel de Control Operativo")
        
        if st.button("🔄 Refrescar Bitácora", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        st.markdown("---")
        
        st.markdown("#### 📅 Fecha de Reporte")
        hoy = datetime.date.today()
        rango_fechas = st.date_input(
            "Seleccione rango (Desde - Hasta):",
            value=(datetime.date(hoy.year, 11, 1), datetime.date(hoy.year, 11, 30)),
            format="DD/MM/YYYY"
        )
        
        centro_seleccionado = "TODOS"
        if col_centro and not df_geo.empty:
            st.markdown("#### 🏢 Centro / Ubicación")
            lista_centros = ["TODOS"] + sorted([str(x) for x in df_geo[col_centro].dropna().unique() if str(x).strip() != ""])
            centro_seleccionado = st.selectbox("Filtrar por centro:", lista_centros)

    # Aplicar filtros
    if col_dia and 'Fecha_dt' in df_geo.columns:
        if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
            fecha_inicio, fecha_fin = rango_fechas
            df_geo = df_geo[(df_geo['Fecha_dt'].dt.date >= fecha_inicio) & (df_geo['Fecha_dt'].dt.date <= fecha_fin)]
            
    if col_centro and centro_seleccionado != "TODOS":
        df_geo = df_geo[df_geo[col_centro].astype(str) == centro_seleccionado]

    with st.sidebar:
        st.markdown("---")
        st.metric(label="Casos Georreferenciados (Filtrados)", value=f"{len(df_geo):,}")

    # --- MAPA ---
    modo_mapa = st.radio(
        "Capa de Visualización Táctica:",
        ["🌐 1. Mapa por Grupo (Cluster con Reportes)", "🔥 2. Mapa de Calor (Density)", "📍 3. Incidentes Individuales (Puntos Sueltos)"],
        index=0,
        horizontal=True
    )

    if not df_geo.empty:
        lat_centro = df_geo['Lat_clean'].median()
        lon_centro = df_geo['Lon_clean'].median()

        m = folium.Map(location=[lat_centro, lon_centro], zoom_start=11, prefer_canvas=True)
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google Hybrid',
            name='Google Hybrid',
            overlay=False,
            control=True
        ).add_to(m)

        Fullscreen(position="topright", title="Pantalla Completa", title_cancel="Salir").add_to(m)

        def generar_popup_html(row, idx):
            num_ev_raw = str(row[col_num]).replace(".0", "") if col_num and pd.notna(row[col_num]) else str(idx + 1)
            num_ev = num_ev_raw if len(num_ev_raw) <= 15 else str(idx + 1)
            
            dia_ev = str(row[col_dia]) if col_dia and pd.notna(row[col_dia]) else 'N/A'
            hora_ev = str(row[col_hora]) if col_hora and pd.notna(row[col_hora]) else 'N/A'
            zona_ev = str(row[col_zona]) if col_zona and pd.notna(row[col_zona]) else 'N/A'
            centro_ev = str(row[col_centro]) if col_centro and pd.notna(row[col_centro]) else 'N/A'
            raw_rep = str(row[col_rep]) if col_rep and pd.notna(row[col_rep]) else 'Sin detalle registrado'
            
            rep_limpio = html.escape(raw_rep).replace('\n', '<br>').replace('\r', '')

            # ESCÁNER UNIVERSAL DE IMÁGENES
            url_img = ""
            for val in row.values:
                val_str = str(val).strip()
                if "http" in val_str and ("drive.google.com" in val_str or ".jpg" in val_str or ".png" in val_str):
                    url_img = val_str
                    break
                elif "drive.google.com" in val_str:
                    url_img = "https://" + val_str
                    break

            html_foto = ""
            
            if url_img:
                url_mostrar = url_img 
                id_foto = ""
                
                if "drive.google.com" in url_img:
                    try:
                        if "/d/" in url_img:
                            id_foto = url_img.split("/d/")[1].split("/")[0]
                        elif "id=" in url_img:
                            id_foto = url_img.split("id=")[1].split("&")[0]
                        
                        if id_foto:
                            url_mostrar = f"https://drive.google.com/thumbnail?id={id_foto}&sz=w800"
                    except:
                        pass

                html_foto = f"""
                <div style="margin-top: 10px; text-align: center; background: #0b0f19; padding: 6px; border-radius: 6px; border: 1px solid #1b365d;">
                    <a href="{url_img}" target="_blank" style="text-decoration: none; color: #00ffff; font-size: 13px; font-weight: bold; display: block; margin-bottom: 6px; padding: 4px; background: rgba(0,255,255,0.1); border-radius: 4px;">
                        📸 Abrir Evidencia Original
                    </a>
                    <a href="{url_img}" target="_blank">
                        <img src="{url_mostrar}" style="width: 100%; max-height: 160px; object-fit: contain; border-radius: 4px;" alt="Evidencia">
                    </a>
                </div>
                """

            return f"""
            <div style="font-family: Arial, sans-serif; font-size: 12px; width: 300px; color: #1a202c; text-shadow: none;">
                <div style="background-color: #1b365d; color: #ffffff; padding: 6px 10px; border-radius: 4px 4px 0 0; font-weight: bold; font-size: 13px;">
                    🚨 CASO N° {num_ev} — {hora_ev}
                </div>
                <div style="padding: 8px; border: 1px solid #cbd5e0; background: #ffffff; border-radius: 0 0 4px 4px;">
                    <p style="margin: 2px 0;"><b>Fecha:</b> {dia_ev}</p>
                    <p style="margin: 2px 0;"><b>Zona Policial:</b> {zona_ev}</p>
                    <p style="margin: 2px 0;"><b>Ubicación:</b> {centro_ev}</p>
                    <div style="background: #f7fafc; border-left: 3px solid #00ffff; padding: 6px; margin-top: 8px; max-height: 150px; overflow-y: auto;">
                        <b>Reporte:</b><br>{rep_limpio}
                    </div>
                    {html_foto}
                </div>
            </div>
            """

        if "Calor" in modo_mapa:
            heat_data = df_geo[['Lat_clean', 'Lon_clean']].values.tolist()
            HeatMap(heat_data, min_opacity=0.45, max_zoom=14, radius=18, blur=22, gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}).add_to(m)
        else:
            es_cluster = "Cluster" in modo_mapa
            if es_cluster:
                grupo_marcadores = MarkerCluster(maxClusterRadius=45, disableClusteringAtZoom=16).add_to(m)
            else:
                grupo_marcadores = m

            for idx, row in df_geo.iterrows():
                popup_content = generar_popup_html(row, idx)

                icono_patrio = folium.DivIcon(
                    html=f"""
                    <div style="
                        background-color: rgba(11, 15, 25, 0.9);
                        border: 2px solid #00ffff;
                        border-radius: 50%;
                        width: 32px;
                        height: 32px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        box-shadow: 0 0 12px rgba(0, 255, 255, 0.9);
                        overflow: hidden;
                    ">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/a/ab/Flag_of_Panama.svg" style="width: 20px; height: 14px; object-fit: cover; border-radius: 2px;">
                    </div>
                    """
                )

                folium.Marker(
                    location=[row['Lat_clean'], row['Lon_clean']],
                    icon=icono_patrio, 
                    popup=folium.Popup(popup_content, max_width=320, show=False)
                ).add_to(grupo_marcadores)

        st_folium(m, height=750, use_container_width=True, returned_objects=[])
        
    else:
        st.warning("⚠️ No hay incidentes para mostrar con los filtros seleccionados o faltan coordenadas.")
        
except Exception as e:
    st.error(f"Error procesando la bitácora: {e}")
