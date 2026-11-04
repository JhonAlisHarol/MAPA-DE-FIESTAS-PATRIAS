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
        filter: drop-shadow(0px 3px 5px rgba(0, 0, 0, 0.9)); 
    }
    
    .neon-sub-text {
        color: #ffffff;
        font-size: 13px;
        font-style: italic;
        margin-top: 8px;
        text-shadow: 0px 2px 5px rgba(0, 0, 0, 0.9);
    }
    
    /* Estilos del selector SLA */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 20px;
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
    
    # Sistema para evitar errores con columnas de Excel duplicadas (CON-C5 y CORCOL)
    columnas_crudas = df_raw.iloc[fila_encabezado].astype(str).str.strip().str.upper().tolist()
    nuevas_cols = []
    vistos = {}
    for c in columnas_crudas:
        if c in vistos:
            vistos[c] += 1
            nuevas_cols.append(f"{c}_{vistos[c]}")
        else:
            vistos[c] = 0
            nuevas_cols.append(c)
            
    df.columns = nuevas_cols
    df = df.reset_index(drop=True)
    return df

def limpiar_numeros_llamadas(val):
    if pd.isna(val) or str(val).strip() == "":
        return 0
    val_str = str(val).replace('.', '').replace(',', '').strip()
    try:
        return int(float(val_str))
    except:
        return 0

try:
    df = cargar_datos_bitacora()

    # Identificación de columnas principales
    col_lat = next((c for c in df.columns if "LAT" in c), None)
    col_lon = next((c for c in df.columns if "LON" in c or "LNG" in c), None)
    col_num = next((c for c in df.columns if "N°" in c or "NO" in c or "ID" in c or "NUM" in c), None)
    col_dia = next((c for c in df.columns if "DIA" in c or "FECHA" in c), None)
    col_hora = next((c for c in df.columns if "HORA" in c), None)
    col_zona = next((c for c in df.columns if "ZONA" in c or "SERVICIO" in c), None)
    col_centro = next((c for c in df.columns if "CENTRO" in c or "LUGAR" in c), None)
    col_rep = next((c for c in df.columns if "REPORTE" in c or "INCIDENTE" in c or "DETALLE" in c), None)
    
    # Identificación MÚLTIPLE de columnas de Llamadas (Detecta C5 y CORCOL dinámicamente)
    cols_ll_rec = [c for c in df.columns if "RECIBIDA" in c]
    cols_ll_cont = [c for c in df.columns if "CONTESTADA" in c]
    cols_ll_aban = [c for c in df.columns if "ABANDONADA" in c]
    cols_i_crea = [c for c in df.columns if "CREADO" in c]
    
    col_rec_c5 = cols_ll_rec[0] if len(cols_ll_rec) > 0 else None
    col_rec_corcol = cols_ll_rec[1] if len(cols_ll_rec) > 1 else None
    col_cont_c5 = cols_ll_cont[0] if len(cols_ll_cont) > 0 else None
    col_cont_corcol = cols_ll_cont[1] if len(cols_ll_cont) > 1 else None
    col_aban_c5 = cols_ll_aban[0] if len(cols_ll_aban) > 0 else None
    col_aban_corcol = cols_ll_aban[1] if len(cols_ll_aban) > 1 else None
    col_crea_c5 = cols_i_crea[0] if len(cols_i_crea) > 0 else None
    col_crea_corcol = cols_i_crea[1] if len(cols_i_crea) > 1 else None

    # ---------------------------------------------------------------------
    # FECHAS: Extracción estricta y blindada
    # ---------------------------------------------------------------------
    if col_dia:
        fechas_limpias = df[col_dia].astype(str).str.split(' ').str[0]
        df['Fecha_dt'] = pd.to_datetime(fechas_limpias, dayfirst=True, errors='coerce')

    # --- PANEL LATERAL Y FILTROS ---
    with st.sidebar:
        st.markdown("### ⚙️ Panel de Control Operativo")
        
        if st.button("🔄 Refrescar Bitácora", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        st.markdown("---")
        
        st.markdown("<h4 style='color: #00ffff; text-shadow: 0 0 5px #00ffff;'>🕒 RANGO TEMPORAL</h4>", unsafe_allow_html=True)
        fecha_inicio = st.date_input("Desde:", value=datetime.date(2026, 11, 1))
        fecha_fin = st.date_input("Hasta:", value=datetime.date(2026, 11, 4))
        
        st.markdown("---")
        
        centro_seleccionado = "TODOS"
        if col_centro:
            st.markdown("#### 🏢 Centro / Ubicación")
            lista_centros = ["TODOS"] + sorted([str(x) for x in df[col_centro].dropna().unique() if str(x).strip() != ""])
            centro_seleccionado = st.selectbox("Filtrar por centro:", lista_centros)

    # ---------------------------------------------------------------------
    # LÓGICA DE FILTRADO
    # ---------------------------------------------------------------------
    df_base_fecha = df.copy()
    if col_dia and 'Fecha_dt' in df_base_fecha.columns:
        df_base_fecha = df_base_fecha[(df_base_fecha['Fecha_dt'].dt.date >= fecha_inicio) & (df_base_fecha['Fecha_dt'].dt.date <= fecha_fin)]
    
    df_llamadas = df_base_fecha.copy()

    df_mapa = df_base_fecha.copy()
    if col_centro and centro_seleccionado != "TODOS":
        df_mapa = df_mapa[df_mapa[col_centro].astype(str) == centro_seleccionado]

    # --- MÉTRICAS SUPERIORES DE LLAMADAS (SLA) ---
    if len(cols_ll_rec) > 0:
        st.markdown("<h4 style='color: #00ffff; text-shadow: 0 0 5px #00ffff; margin-bottom: -10px; margin-top: -10px;'>📡 Centro SLA:</h4>", unsafe_allow_html=True)
        opcion_sla = st.radio(
            "Centro SLA:",
            ["🔴 AMBOS CENTROS (Sumados)", "⚫ CON-C5", "⚫ CORCOL"],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.write("") # Espaciador
        
        def sumar_col(col_name, df_datos):
            if col_name and col_name in df_datos.columns:
                return sum(df_datos[col_name].apply(limpiar_numeros_llamadas))
            return 0

        if "AMBOS" in opcion_sla:
            t_rec = sumar_col(col_rec_c5, df_llamadas) + sumar_col(col_rec_corcol, df_llamadas)
            t_cont = sumar_col(col_cont_c5, df_llamadas) + sumar_col(col_cont_corcol, df_llamadas)
            t_aban = sumar_col(col_aban_c5, df_llamadas) + sumar_col(col_aban_corcol, df_llamadas)
            t_crea = sumar_col(col_crea_c5, df_llamadas) + sumar_col(col_crea_corcol, df_llamadas)
        elif "CON-C5" in opcion_sla:
            t_rec = sumar_col(col_rec_c5, df_llamadas)
            t_cont = sumar_col(col_cont_c5, df_llamadas)
            t_aban = sumar_col(col_aban_c5, df_llamadas)
            t_crea = sumar_col(col_crea_c5, df_llamadas)
        elif "CORCOL" in opcion_sla:
            t_rec = sumar_col(col_rec_corcol, df_llamadas)
            t_cont = sumar_col(col_cont_corcol, df_llamadas)
            t_aban = sumar_col(col_aban_corcol, df_llamadas)
            t_crea = sumar_col(col_crea_corcol, df_llamadas)
            
        pct_prod = (t_cont / t_rec * 100) if t_rec > 0 else 0
        
        st.markdown(f"""
        <div style="display: flex; gap: 12px; margin-bottom: 25px; flex-wrap: wrap; justify-content: center;">
            <div style="flex: 1; min-width: 140px; background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(0, 255, 255, 0.4); border-radius: 8px; padding: 15px 10px; text-align: center; box-shadow: 0 0 10px rgba(0,255,255,0.15);">
                <div style="color: #e2e8f0; font-size: 11px; font-weight: bold; margin-bottom: 5px; text-shadow: 0px 2px 4px rgba(0,0,0,0.8);">LL. RECIBIDAS</div>
                <div style="color: #00ffff; font-size: 26px; font-weight: 900; text-shadow: 0 0 10px rgba(0,255,255,0.7);">{t_rec:,}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(0, 255, 100, 0.4); border-radius: 8px; padding: 15px 10px; text-align: center; box-shadow: 0 0 10px rgba(0,255,100,0.15);">
                <div style="color: #e2e8f0; font-size: 11px; font-weight: bold; margin-bottom: 5px; text-shadow: 0px 2px 4px rgba(0,0,0,0.8);">LL. CONTESTADAS</div>
                <div style="color: #00ff66; font-size: 26px; font-weight: 900; text-shadow: 0 0 10px rgba(0,255,102,0.7);">{t_cont:,}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(255, 50, 50, 0.4); border-radius: 8px; padding: 15px 10px; text-align: center; box-shadow: 0 0 10px rgba(255,50,50,0.15);">
                <div style="color: #e2e8f0; font-size: 11px; font-weight: bold; margin-bottom: 5px; text-shadow: 0px 2px 4px rgba(0,0,0,0.8);">LL. ABANDONADAS</div>
                <div style="color: #ff3333; font-size: 26px; font-weight: 900; text-shadow: 0 0 10px rgba(255,51,51,0.7);">{t_aban:,}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(255, 174, 0, 0.4); border-radius: 8px; padding: 15px 10px; text-align: center; box-shadow: 0 0 10px rgba(255,174,0,0.15);">
                <div style="color: #e2e8f0; font-size: 11px; font-weight: bold; margin-bottom: 5px; text-shadow: 0px 2px 4px rgba(0,0,0,0.8);">INCIDENTES CREADOS</div>
                <div style="color: #ffae00; font-size: 26px; font-weight: 900; text-shadow: 0 0 10px rgba(255,174,0,0.7);">{t_crea:,}</div>
            </div>
            <div style="flex: 1; min-width: 140px; background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(189, 0, 255, 0.4); border-radius: 8px; padding: 15px 10px; text-align: center; box-shadow: 0 0 10px rgba(189,0,255,0.15);">
                <div style="color: #e2e8f0; font-size: 11px; font-weight: bold; margin-bottom: 5px; text-shadow: 0px 2px 4px rgba(0,0,0,0.8);">% PRODUCTIVIDAD</div>
                <div style="color: #bd00ff; font-size: 26px; font-weight: 900; text-shadow: 0 0 10px rgba(189,0,255,0.7);">{pct_prod:.1f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # PREPARACIÓN DEL MAPA
    # ---------------------------------------------------------------------
    if col_lat and col_lon:
        df_mapa['Lat_clean'] = pd.to_numeric(
            df_mapa[col_lat].astype(str).str.replace(',', '.', regex=False).str.replace(r'[^0-9.\-]', '', regex=True), 
            errors='coerce'
        )
        df_mapa['Lon_clean'] = pd.to_numeric(
            df_mapa[col_lon].astype(str).str.replace(',', '.', regex=False).str.replace(r'[^0-9.\-]', '', regex=True), 
            errors='coerce'
        )
        df_geo = df_mapa.dropna(subset=['Lat_clean', 'Lon_clean']).copy()
        df_geo = df_geo[(df_geo['Lat_clean'] != 0) & (df_geo['Lon_clean'] != 0)]
    else:
        df_geo = pd.DataFrame()

    with st.sidebar:
        st.markdown("---")
        st.metric(label="Casos Georreferenciados (Filtrados)", value=f"{len(df_geo):,}")

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
        
        # --- TABLERO TÁCTICO DE CENTROS ---
        if col_centro:
            st.markdown("""
                <div style="text-align: center; margin-top: 30px; margin-bottom: 20px;">
                    <h3 style="color: #00ffff; text-shadow: 0 0 10px rgba(0,255,255,0.7); font-family: 'Segoe UI', sans-serif;">
                        🏢 RESUMEN OPERATIVO POR CENTRO
                    </h3>
                </div>
            """, unsafe_allow_html=True)
            
            resumen_centros = df_geo[col_centro].value_counts().reset_index()
            resumen_centros.columns = ['Centro', 'Cantidad']
            
            cols_c = st.columns(6) 
            for idx, row in resumen_centros.iterrows():
                col_idx = idx % 6
                with cols_c[col_idx]:
                    st.markdown(f"""
                    <div style="background: rgba(0, 0, 0, 0.15); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 6px; padding: 10px 5px; margin-bottom: 10px; text-align: center; box-shadow: 0 0 5px rgba(0,255,255,0.1);">
                        <div style="color: #e2e8f0; font-size: 11px; line-height: 1.1; min-height: 25px; display: flex; align-items: center; justify-content: center; margin-bottom: 5px;">
                            {row['Centro']}
                        </div>
                        <div style="color: #ff3333; font-size: 22px; font-weight: bold; text-shadow: 0 0 8px rgba(255,0,0,0.8);">
                            {row['Cantidad']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # --- TABLERO TÁCTICO DE ZONAS ---
        if col_zona:
            st.markdown("""
                <div style="text-align: center; margin-top: 20px; margin-bottom: 20px;">
                    <h3 style="color: #00ffff; text-shadow: 0 0 10px rgba(0,255,255,0.7); font-family: 'Segoe UI', sans-serif;">
                        📊 RESUMEN OPERATIVO POR ZONA POLICIAL
                    </h3>
                </div>
            """, unsafe_allow_html=True)
            
            resumen_zonas = df_geo[col_zona].value_counts().reset_index()
            resumen_zonas.columns = ['Zona Policial', 'Cantidad']
            
            cols = st.columns(6) 
            for idx, row in resumen_zonas.iterrows():
                col_idx = idx % 6
                with cols[col_idx]:
                    st.markdown(f"""
                    <div style="background: rgba(0, 0, 0, 0.15); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 6px; padding: 10px 5px; margin-bottom: 10px; text-align: center; box-shadow: 0 0 5px rgba(0,255,255,0.1);">
                        <div style="color: #e2e8f0; font-size: 11px; line-height: 1.1; min-height: 25px; display: flex; align-items: center; justify-content: center; margin-bottom: 5px;">
                            {row['Zona Policial']}
                        </div>
                        <div style="color: #ff3333; font-size: 22px; font-weight: bold; text-shadow: 0 0 8px rgba(255,0,0,0.8);">
                            {row['Cantidad']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
    else:
        st.warning("⚠️ No hay incidentes para mostrar con los filtros seleccionados o faltan coordenadas.")
        
except Exception as e:
    st.error(f"Error procesando la bitácora: {e}")
