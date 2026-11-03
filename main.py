import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen
from streamlit_folium import st_folium
import html

st.set_page_config(
    page_title="Centro de Operación Nacional | Mapa Táctico C5",
    page_icon="🗺️",
    layout="wide"
)

# --- ESTILOS VISUALES Y FONDO TÁCTICO LIGERO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    
    /* Fondo táctico oscuro en lugar de video para no colapsar la RAM */
    .bg-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: radial-gradient(circle at center, #1b365d 0%, #0b0f19 80%);
        z-index: -99998;
        pointer-events: none;
    }

    .stApp, .block-container, [data-testid="stVerticalBlock"] {
        background: transparent !important;
        color: #ffffff;
    }
    
    [data-testid="stSidebar"] {
        background-color: rgba(11, 15, 25, 0.95) !important;
        border-right: 1px solid #1b365d;
    }
    
    @keyframes neonBorderMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .neon-title-container {
        border: 4px solid transparent;
        background: linear-gradient(135deg, rgba(16, 24, 40, 0.9) 0%, rgba(11, 15, 25, 0.9) 100%), 
                    linear-gradient(90deg, #ff0055, #00ffff, #00ff66, #ffae00, #bd00ff, #ff0055);
        background-origin: border-box;
        background-clip: padding-box, border-box;
        background-size: 300% 300%;
        animation: neonBorderMove 6s ease infinite;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 25px rgba(0, 255, 255, 0.5), inset 0 0 20px rgba(255, 0, 85, 0.3);
        margin-bottom: 20px;
    }
    
    .neon-title-text {
        color: #00ffff;
        font-size: 26px;
        font-weight: 800;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        letter-spacing: 1.5px;
        text-shadow: 0 0 15px rgba(0, 255, 255, 0.9), 0 0 25px rgba(255, 0, 85, 0.6);
    }
    
    .neon-sub-text {
        color: #ffae00;
        font-size: 13px;
        font-style: italic;
        margin-top: 8px;
        text-shadow: 0 0 10px rgba(255, 174, 0, 0.8);
    }
    </style>
    <div class="bg-overlay"></div>
""", unsafe_allow_html=True)

# --- AUTENTICACIÓN DE USUARIOS ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def pantalla_login():
    st.markdown("""
        <div class="neon-title-container">
            <div class="neon-title-text">🔐 CENTRO DE OPERACIÓN NACIONAL - C5</div>
            <div class="neon-sub-text">SISTEMA DE AUTENTICACIÓN TÁCTICO</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        usuarios_permitidos = {
            "LORENZO BOWEN": "10924",
            "ALISJHON": "199432",
            "REGGIE AGUILAR": "40506", 
            "VICTOR MARTINEZ": "12495", 
            "JAVIER GONZALEZ": "25720"
        }
        
        user = st.text_input("Usuario autorizador:")
        password = st.text_input("Contraseña de acceso:", type="password")

        if st.button("Iniciar Sesión", use_container_width=True):
            user_clean = user.strip().upper()
            if user_clean in usuarios_permitidos and usuarios_permitidos[user_clean] == password:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = user_clean
                st.success(f"✔️ Bienvenido, {user_clean}.")
                st.rerun()
            else:
                st.error("❌ Credenciales no autorizadas.")

if not st.session_state.autenticado:
    pantalla_login()
else:
    st.markdown("""
        <div class="neon-title-container">
            <div class="neon-title-text">🛰️ CENTRO DE OPERACIÓN NACIONAL | BITÁCORA DESFILES PATRIOS</div>
            <div class="neon-sub-text">SISTEMA DE GEORREFERENCIACIÓN Y CONTROL OPERATIVO</div>
        </div>
    """, unsafe_allow_html=True)

    # --- CONEXIÓN A GOOGLE SHEETS ---
    @st.cache_data(ttl=30)
    def cargar_datos_bitacora():
        url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuFSvR6xnmXiAz4JRGVfrIDHdPVRV2fKM4jkPNKhW_Y-cRLlbJOI_O0SYZNDu6puEaYqcZd4hDWh20/pub?output=csv&gid=1525160468"
        
        df_raw = pd.read_csv(url_csv, header=None)
        
        fila_encabezado = 0
        for i, row in df_raw.head(10).iterrows():
            fila_texto = " ".join([str(val).upper().strip() for val in row.values])
            if "ZONA" in fila_texto and ("HORA" in fila_texto or "DÍA" in fila_texto or "DIA" in fila_texto):
                fila_encabezado = i
                break
        
        df = pd.read_csv(url_csv, header=fila_encabezado)
        df.columns = df.columns.astype(str).str.strip().str.upper()
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

        # Identificación de columnas
        col_num = next((c for c in df.columns if "N°" in c or "NO" in c or "ID" in c or "NUM" in c), None)
        col_dia = next((c for c in df.columns if "DIA" in c or "FECHA" in c), None)
        col_hora = next((c for c in df.columns if "HORA" in c), None)
        col_zona = next((c for c in df.columns if "ZONA" in c or "SERVICIO" in c), None)
        col_centro = next((c for c in df.columns if "CENTRO" in c or "LUGAR" in c), None)
        col_rep = next((c for c in df.columns if "REPORTE" in c or "INCIDENTE" in c or "DETALLE" in c), None)
        col_img = next((c for c in df.columns if "IMAGEN" in c or "EVIDENCIA" in c or "FOTO" in c or "URL" in c or "IMG" in c), None)

        # --- PANEL LATERAL ---
        with st.sidebar:
            st.write(f"👤 Operador: **{st.session_state.get('usuario_actual', 'Operador')}**")
            if st.button("🔄 Refrescar Bitácora", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
            if st.button("Cerrar Sesión", use_container_width=True):
                st.session_state.autenticado = False
                st.rerun()
                
            st.markdown("---")
            st.metric(label="Total Registros Bitácora", value=f"{len(df):,}")
            st.metric(label="Casos Georreferenciados", value=f"{len(df_geo):,}")

        # --- SELECTOR DE CAPAS ---
        modo_mapa = st.radio(
            "Capa de Visualización:",
            ["🌐 1. Mapa por Grupo (Cluster con Reportes)", "🔥 2. Mapa de Calor (Density)", "📍 3. Incidentes Individuales (Puntos Sueltos)"],
            index=0,
            horizontal=True
        )

        if not df_geo.empty:
            lat_centro = df_geo['Lat_clean'].median()
            lon_centro = df_geo['Lon_clean'].median()

            m = folium.Map(location=[lat_centro, lon_centro], zoom_start=11)
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google Hybrid',
                name='Google Hybrid',
                overlay=False,
                control=True
            ).add_to(m)
            Fullscreen(position="topright", title="Pantalla Completa", title_cancel="Salir").add_to(m)

            def generar_popup_html(row, idx):
                num_ev = str(row.get(col_num, idx + 1)).replace(".0", "")
                if len(num_ev) > 15:
                    num_ev = str(idx + 1)
                    
                dia_ev = str(row.get(col_dia, 'N/A')) if col_dia else 'N/A'
                hora_ev = str(row.get(col_hora, 'N/A')) if col_hora else 'N/A'
                zona_ev = str(row.get(col_zona, 'N/A')) if col_zona else 'N/A'
                centro_ev = str(row.get(col_centro, 'N/A')) if col_centro else 'N/A'
                
                raw_rep = str(row.get(col_rep, 'Sin detalle registrado')) if col_rep else 'Sin detalle registrado'
                rep_limpio = html.escape(raw_rep).replace('\n', '<br>').replace('\r', '')

                url_img = str(row.get(col_img, "")).strip() if col_img else ""
                html_foto = ""
                
                if url_img and url_img.lower() != "nan":
                    if "drive.google.com/file/d/" in url_img:
                        id_foto = url_img.split("/file/d/")[1].split("/")[0]
                        url_img = f"https://drive.google.com/uc?export=view&id={id_foto}"
                    elif "drive.google.com/open?id=" in url_img:
                        id_foto = url_img.split("id=")[1].split("&")[0]
                        url_img = f"https://drive.google.com/uc?export=view&id={id_foto}"

                    if url_img.startswith("http"):
                        html_foto = f"""
                        <div style="margin-top: 8px; text-align: center; background: #000; padding: 4px; border-radius: 4px;">
                            <a href="{url_img}" target="_blank">
                                <img src="{url_img}" style="width: 100%; max-height: 180px; object-fit: contain; border-radius: 4px;" alt="Evidencia">
                            </a>
                            <div style="font-size: 10px; color: #a0aec0; margin-top: 3px;">(Clic para ampliar)</div>
                        </div>
                        """

                return f"""
                <div style="font-family: Arial, sans-serif; font-size: 12px; width: 300px; color: #1a202c;">
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
                """, num_ev

            if "Calor" in modo_mapa:
                heat_data = df_geo[['Lat_clean', 'Lon_clean']].values.tolist()
                HeatMap(heat_data, min_opacity=0.45, max_zoom=14, radius=18, blur=22, gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}).add_to(m)
            else:
                es_cluster = "Cluster" in modo_mapa
                if es_cluster:
                    grupo_marcadores = MarkerCluster(maxClusterRadius=45).add_to(m)
                else:
                    grupo_marcadores = m

                for idx, row in df_geo.iterrows():
                    popup_content, id_num = generar_popup_html(row, idx)
                    folium.Marker(
                        location=[row['Lat_clean'], row['Lon_clean']],
                        icon=folium.Icon(color='red', icon='info-sign'), 
                        popup=folium.Popup(popup_content, max_width=320, show=False),
                        tooltip=f"Caso N° {id_num}: Clic para ver reporte"
                    ).add_to(grupo_marcadores)

            st_folium(m, height=750, use_container_width=True)
        else:
            st.warning("⚠️ No se encontraron coordenadas válidas.")
            
    except Exception as e:
        st.error(f"Error procesando la bitácora: {e}")
