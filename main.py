import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen
from streamlit_folium import st_folium
import html
import datetime
import re  

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
    
    .bg-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-image: linear-gradient(rgba(11, 15, 25, 0.65), rgba(11, 15, 25, 0.65)), url("https://upload.wikimedia.org/wikipedia/commons/a/ab/Flag_of_Panama.svg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        z-index: -99998;
        pointer-events: none;
    }

    .stApp, .block-container, [data-testid="stVerticalBlock"] {
        background: transparent !important;
        color: #ffffff;
        text-shadow: 0px 1px 3px rgba(0,0,0,0.8);
    }
    
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

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_data(ttl=45)
def cargar_datos_bitacora():
    url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTuFSvR6xnmXiAz4JRGVfrIDHdPVRV2fKM4jkPNKhW_Y-cRLlbJOI_O0SYZNDu6puEaYqcZd4hDWh20/pub?output=csv&gid=1525160468"
    try:
        df_raw = pd.read_csv(url_csv, header=None)
        
        fila_encabezado = 0
        for i, row in df_raw.head(10).iterrows():
            fila_texto = " ".join([str(val).upper().strip() for val in row.values])
            if "ZONA" in fila_texto and ("HORA" in fila_texto or "DÍA" in fila_texto or "DIA" in fila_texto):
                fila_encabezado = i
                break
        
        df = df_raw.iloc[fila_encabezado+1:].copy()
        
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
    except Exception as e:
        st.error(f"Error crítico conectando a la base de datos: {e}")
        return pd.DataFrame()

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

    if not df.empty:
        col_lat = next((c for c in df.columns if "LAT" in str(c)), None)
        col_lon = next((c for c in df.columns if "LON" in str(c) or "LNG" in str(c)), None)
        col_num = next((c for c in df.columns if "N°" in str(c) or "NO" in str(c) or "ID" in str(c) or "NUM" in str(c)), None)
        col_dia = next((c for c in df.columns if "DIA" in str(c) or "FECHA" in str(c)), None)
        col_hora = next((c for c in df.columns if "HORA" in str(c)), None)
        col_zona = next((c for c in df.columns if "ZONA" in str(c) or "SERVICIO" in str(c)), None)
        col_centro = next((c for c in df.columns if "CENTRO" in str(c) or "LUGAR" in str(c)), None)
        col_rep = next((c for c in df.columns if "REPORTE" in str(c) or "INCIDENTE" in str(c) or "DETALLE" in str(c)), None)
        col_provincia = next((c for c in df.columns if "PROVINCIA" in str(c)), None)
        
        cols_ll_rec = [c for c in df.columns if "RECIBIDA" in str(c)]
        cols_ll_cont = [c for c in df.columns if "CONTESTADA" in str(c)]
        cols_ll_aban = [c for c in df.columns if "ABANDONADA" in str(c)]
        cols_i_crea = [c for c in df.columns if "CREADO" in str(c)]
        
        col_rec_c5 = cols_ll_rec[0] if len(cols_ll_rec) > 0 else None
        col_rec_corcol = cols_ll_rec[1] if len(cols_ll_rec) > 1 else None
        col_cont_c5 = cols_ll_cont[0] if len(cols_ll_cont) > 0 else None
        col_cont_corcol = cols_ll_cont[1] if len(cols_ll_cont) > 1 else None
        col_aban_c5 = cols_ll_aban[0] if len(cols_ll_aban) > 0 else None
        col_aban_corcol = cols_ll_aban[1] if len(cols_ll_aban) > 1 else None
        col_crea_c5 = cols_i_crea[0] if len(cols_i_crea) > 0 else None
        col_crea_corcol = cols_i_crea[1] if len(cols_i_crea) > 1 else None

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

        # --- LÓGICA DE FILTRADO ---
        df_base_fecha = df.copy()
        if col_dia and 'Fecha_dt' in df_base_fecha.columns:
            df_base_fecha = df_base_fecha[(df_base_fecha['Fecha_dt'].dt.date >= fecha_inicio) & (df_base_fecha['Fecha_dt'].dt.date <= fecha_fin)]
        
        df_llamadas = df_base_fecha.copy()
        df_mapa = df_base_fecha.copy()
        if col_centro and centro_seleccionado != "TODOS":
            df_mapa = df_mapa[df_mapa[col_centro].astype(str) == centro_seleccionado]

        # --- PREPARACIÓN DEL MAPA ---
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

        col_grupo_prov = col_provincia if col_provincia else col_zona

        with st.sidebar:
            st.markdown("---")
            st.metric(label="Casos Georreferenciados (Filtrados)", value=f"{len(df_geo):,}")

        # --- MOTOR DE LECTURA ROBUSTO ---
        categorias_lista = [
            "Aprehendidos (Alteración/Riña/Agresión)",
            "Aprehendidos (Indocumentados)",
            "Aprehendidos (Libar Licor)",
            "Aprehendidos (Por Oficio)",
            "Otras Capturas y Conducciones",
            "Atenciones Médicas y Evacuaciones",
            "Decomiso de Armas o Drogas",
            "Retención de Licor",
            "Artículos Varios Decomisados / Recuperados",
            "Desalojos y Desórdenes (Multitudes)",
            "Retención de Carnets (Salud)",
            "Destrucción de Alimentos (MINSA)",
            "Multas, Sanciones y Citaciones"
        ]

        def analizar_fila(texto):
            res = {c: 0 for c in categorias_lista}
            if pd.isna(texto): return pd.Series(res)
            texto_str = str(texto).lower()
            
            texto_str = re.sub(r'\b\d+\s*(?:años|año|pm|am|horas|hora|minutos|hrs)\b', '', texto_str)
            texto_str = re.sub(r'\b(?:19|20)\d{2}\b', '', texto_str)
            
            texto_str = texto_str.replace("un (01)", "1").replace("un (1)", "1").replace("una (01)", "1").replace("una (1)", "1").replace("un ", "1 ").replace("una ", "1 ")
            texto_str = texto_str.replace("dos (02)", "2").replace("dos (2)", "2").replace("dos ", "2 ")
            texto_str = texto_str.replace("tres (03)", "3").replace("tres (3)", "3").replace("tres ", "3 ")
            texto_str = texto_str.replace("cuatro (04)", "4").replace("cuatro (4)", "4").replace("cuatro ", "4 ")
            texto_str = texto_str.replace("cinco (05)", "5").replace("cinco (5)", "5").replace("cinco ", "5 ")
            texto_str = texto_str.replace("seis (06)", "6").replace("seis (6)", "6").replace("seis ", "6 ")
            texto_str = texto_str.replace("siete ", "7 ").replace("ocho ", "8 ").replace("nueve ", "9 ").replace("diez ", "10 ").replace("veinte ", "20 ")
            
            frases = re.split(r'[.;,\n]|\by\b', texto_str)
            
            for frase in frases:
                numeros = re.findall(r'\b(\d+)\b', frase)
                cant = sum(int(n) for n in numeros) if numeros else 0
                if cant == 0:
                    continue 
                
                if re.search(r'\b(?:indocumentad|documento)', frase):
                    res["Aprehendidos (Indocumentados)"] += cant
                elif re.search(r'\b(?:libar|livar)', frase):
                    res["Aprehendidos (Libar Licor)"] += cant
                elif re.search(r'\b(?:alteraci|riña|agresi|agred)', frase):
                    res["Aprehendidos (Alteración/Riña/Agresión)"] += cant
                elif re.search(r'\b(?:oficio)', frase):
                    res["Aprehendidos (Por Oficio)"] += cant
                elif re.search(r'\b(?:captur|aprehend|aprehens|deteni|deten|conducci|conducid)', frase):
                    res["Otras Capturas y Conducciones"] += cant
                elif re.search(r'\b(?:evacuaci|evacuad|traslado|traslad|rescate|rescat|ambulancia|paramédic|atendido|atendida|atendidas|desmay|golpe de calor)', frase):
                    res["Atenciones Médicas y Evacuaciones"] += cant
                elif re.search(r'\b(?:carnet)', frase):
                    res["Retención de Carnets (Salud)"] += cant
                elif re.search(r'\b(?:multa|multas|sancion|sancionado|sancionados|citaci|citacion|citaciones)', frase):
                    res["Multas, Sanciones y Citaciones"] += cant
                elif re.search(r'\b(?:destrucci|destruido|insalubre)', frase):
                    res["Destrucción de Alimentos (MINSA)"] += cant
                elif re.search(r'\b(?:licor|bebida|cerveza)', frase):
                    res["Retención de Licor"] += cant
                elif re.search(r'\b(?:arma|droga|incautaci|incautad|sustancia)', frase):
                    res["Decomiso de Armas o Drogas"] += cant
                elif re.search(r'\b(?:decomis|recuperaci|recuperad|retenci|retenid|mercancía|artículo|vario)', frase):
                    res["Artículos Varios Decomisados / Recuperados"] += cant
                elif re.search(r'\b(?:desalojo|desalojad|multitud|desorden|pleito|violencia|altercado|escándalo|convivencia)', frase):
                    res["Desalojos y Desórdenes (Multitudes)"] += cant
                    
            return pd.Series(res)

        # --- SISTEMA DE PESTAÑAS (TABS) ---
        tab_tactico, tab_presentacion = st.tabs(["🗺️ Tablero Operativo Táctico", "📊 Presentación Operaciones"])

        # ==========================================
        # PESTAÑA 1: TABLERO OPERATIVO TÁCTICO
        # ==========================================
        with tab_tactico:
            if len(cols_ll_rec) > 0:
                st.markdown("<h4 style='color: #00ffff; text-shadow: 0 0 5px #00ffff; margin-bottom: -10px; margin-top: -10px;'>📡 Centro SLA:</h4>", unsafe_allow_html=True)
                opcion_sla = st.radio(
                    "Centro SLA:",
                    ["🔴 AMBOS CENTROS (Sumados)", "⚫ CON-C5", "⚫ CORCOL"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="radio_sla_main"
                )
                st.write("") 
                
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

            modo_mapa = st.radio(
                "Capa de Visualización Táctica:",
                ["🌐 1. Mapa por Grupo (Cluster con Reportes)", "🔥 2. Mapa de Calor (Density)", "📍 3. Incidentes Individuales (Puntos Sueltos)"],
                index=0,
                horizontal=True,
                key="radio_modo_mapa_main"
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
                
                # Procesamiento para KPIs y Tabla
                df_kpi = df_geo[col_rep].apply(analizar_fila)
                df_geo_procesado = pd.concat([df_geo, df_kpi], axis=1)

                # --- KPIS SUPERIORES DE ACCIONES ---
                st.markdown("""
                    <div style="text-align: center; margin-top: 30px; margin-bottom: 20px;">
                        <h3 style="color: #00ffff; text-shadow: 0 0 10px rgba(0,255,255,0.7); font-family: 'Segoe UI', sans-serif;">
                            🚨 ACCIONES POLICIALES RELEVANTES (Auto-Suma)
                        </h3>
                    </div>
                """, unsafe_allow_html=True)

                tot_capturas = df_kpi["Aprehendidos (Alteración/Riña/Agresión)"].sum() + df_kpi["Aprehendidos (Indocumentados)"].sum() + df_kpi["Aprehendidos (Libar Licor)"].sum() + df_kpi["Aprehendidos (Por Oficio)"].sum() + df_kpi["Otras Capturas y Conducciones"].sum()
                tot_evacuaciones = df_kpi["Atenciones Médicas y Evacuaciones"].sum()
                tot_decomisos = df_kpi["Decomiso de Armas o Drogas"].sum() + df_kpi["Retención de Licor"].sum() + df_kpi["Artículos Varios Decomisados / Recuperados"].sum()
                tot_alteraciones = df_kpi["Desalojos y Desórdenes (Multitudes)"].sum()
                tot_faltas = df_kpi["Retención de Carnets (Salud)"].sum() + df_kpi["Destrucción de Alimentos (MINSA)"].sum() + df_kpi["Multas, Sanciones y Citaciones"].sum()
                
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.markdown(f"""
                    <div style="background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(255, 50, 50, 0.4); border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 0 10px rgba(255,51,51,0.15);">
                        <div style="color: #e2e8f0; font-size: 12px; font-weight: bold; margin-bottom: 5px;">CAPTURAS / APREHENSIONES</div>
                        <div style="color: #ff3333; font-size: 28px; font-weight: bold; text-shadow: 0 0 10px rgba(255,51,51,0.7);">{int(tot_capturas)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div style="background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(0, 255, 100, 0.4); border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 0 10px rgba(0,255,100,0.15);">
                        <div style="color: #e2e8f0; font-size: 12px; font-weight: bold; margin-bottom: 5px;">EVACUACIONES / MÉDICAS</div>
                        <div style="color: #00ff66; font-size: 28px; font-weight: bold; text-shadow: 0 0 10px rgba(0,255,102,0.7);">{int(tot_evacuaciones)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""
                    <div style="background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(255, 174, 0, 0.4); border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 0 10px rgba(255,174,0,0.15);">
                        <div style="color: #e2e8f0; font-size: 12px; font-weight: bold; margin-bottom: 5px;">DECOMISOS / RECUPERACIONES</div>
                        <div style="color: #ffae00; font-size: 28px; font-weight: bold; text-shadow: 0 0 10px rgba(255,174,0,0.7);">{int(tot_decomisos)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c4:
                    st.markdown(f"""
                    <div style="background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(189, 0, 255, 0.4); border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 0 10px rgba(189,0,255,0.15);">
                        <div style="color: #e2e8f0; font-size: 12px; font-weight: bold; margin-bottom: 5px;">ALTERACIÓN DEL ORDEN</div>
                        <div style="color: #bd00ff; font-size: 28px; font-weight: bold; text-shadow: 0 0 10px rgba(189,0,255,0.7);">{int(tot_alteraciones)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c5:
                    st.markdown(f"""
                    <div style="background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(0, 200, 255, 0.4); border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 0 10px rgba(0,200,255,0.15);">
                        <div style="color: #e2e8f0; font-size: 12px; font-weight: bold; margin-bottom: 5px;">FALTAS ADM. / MINSA</div>
                        <div style="color: #00c8ff; font-size: 28px; font-weight: bold; text-shadow: 0 0 10px rgba(0,200,255,0.7);">{int(tot_faltas)}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # --- CUADRO DE EXCEL PARA DESGLOSE POR PROVINCIA ---
                st.markdown("""
                    <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
                        <h3 style="color: #00ffff; text-shadow: 0 0 10px rgba(0,255,255,0.7); font-family: 'Segoe UI', sans-serif;">
                            📋 DESGLOSE DETALLADO DE ACCIONES POR PROVINCIA
                        </h3>
                    </div>
                """, unsafe_allow_html=True)
                
                resumen_acciones = df_geo_procesado.groupby(col_grupo_prov)[categorias_lista].sum()
                
                if not resumen_acciones.empty:
                    resumen_acciones = resumen_acciones.loc[:, (resumen_acciones != 0).any(axis=0)]
                    resumen_acciones = resumen_acciones.loc[(resumen_acciones != 0).any(axis=1)]
                    
                    resumen_acciones_t = resumen_acciones.T
                    resumen_acciones_t['Total General'] = resumen_acciones_t.sum(axis=1)
                    
                    if not resumen_acciones_t.empty:
                        resumen_acciones_t = resumen_acciones_t.sort_values(by='Total General', ascending=False)
                        
                        totales_columnas = resumen_acciones_t.sum(axis=0)
                        totales_columnas.name = 'TOTAL GENERAL'
                        resumen_acciones_t = pd.concat([resumen_acciones_t, pd.DataFrame(totales_columnas).T])
                        
                        resumen_acciones_t = resumen_acciones_t.reset_index()
                        resumen_acciones_t = resumen_acciones_t.rename(columns={'index': 'Acción / Incidente'})
                        
                        df_desglose = resumen_acciones_t
                        
                        for col in df_desglose.columns:
                            if col != 'Acción / Incidente':
                                df_desglose[col] = df_desglose[col].astype(int)
                        
                        col_izq, col_der = st.columns([4, 1])
                        with col_izq:
                            st.dataframe(df_desglose, use_container_width=True, hide_index=True)
                        with col_der:
                            csv = df_desglose.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Descargar Cuadro",
                                data=csv,
                                file_name='Desglose_Provincial.csv',
                                mime='text/csv',
                                key="btn_download_tactico"
                            )
                    else:
                        st.info("No se detectaron acciones policiales o administrativas para desglosar en este rango de fechas.")
                else:
                    st.info("No hay datos geográficos para agrupar por provincia en este rango.")
            else:
                st.warning("⚠️ No hay incidentes para mostrar con los filtros seleccionados o faltan coordenadas.")

        # ==========================================
        # PESTAÑA 2: PRESENTACIÓN OPERATIVA (MAPA ESTÁTICO DE FONDO TIPO PANAMÁ)
        # ==========================================
        with tab_presentacion:
            st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.85); border: 2px solid #00ffff; border-radius: 12px; padding: 20px; margin-bottom: 25px; box-shadow: 0 0 20px rgba(0,255,255,0.2);">
                    <h2 style="color: #00ffff; text-align: center; margin: 0; font-family: 'Segoe UI', sans-serif; text-shadow: 0 0 10px #00ffff;">
                        📊 PRESENTACIÓN OPERATIVA | MAPA TÉCNICO REGIONAL ({fecha_inicio.strftime('%d/%m/%Y')} AL {fecha_fin.strftime('%d/%m/%Y')})
                    </h2>
                    <p style="color: #e2e8f0; text-align: center; font-style: italic; margin-top: 5px; font-size: 14px;">
                        Mapa estático de la República de Panamá con tarjetas ejecutivas regionales integradas (sin valores en cero).
                    </p>
                </div>
            """, unsafe_allow_html=True)

            if col_rep and col_grupo_prov and not df_base_fecha.empty:
                df_pres = df_base_fecha.copy()
                
                def extraer_delegaciones_pres(texto):
                    if pd.isna(texto): return 0
                    texto_str = str(texto).lower()
                    match = re.search(r'(\d+)\s*(?:delegacion|banda)', texto_str)
                    if match:
                        return int(match.group(1))
                    elif "delegacion" in texto_str or "banda" in texto_str:
                        return 1
                    return 0

                df_pres['Cant_Del'] = df_pres[col_rep].apply(extraer_delegaciones_pres)
                df_pres_kpi = df_pres[col_rep].apply(analizar_fila)
                df_pres_full = pd.concat([df_pres, df_pres_kpi], axis=1)
                
                agrupado_prov = df_pres_full.groupby(col_grupo_prov).agg(
                    Total_Eventos=(col_grupo_prov, 'count'),
                    Total_Delegaciones=('Cant_Del', 'sum'),
                    Capturas_Totales=(
                        'Aprehendidos (Alteración/Riña/Agresión)', 
                        lambda x: x.sum() + df_pres_full.loc[x.index, 'Aprehendidos (Indocumentados)'].sum() + 
                                  df_pres_full.loc[x.index, 'Aprehendidos (Libar Licor)'].sum() + 
                                  df_pres_full.loc[x.index, 'Aprehendidos (Por Oficio)'].sum() + 
                                  df_pres_full.loc[x.index, 'Otras Capturas y Conducciones'].sum()
                    ),
                    Evacuaciones_Totales=('Atenciones Médicas y Evacuaciones', 'sum'),
                    Decomisos_Totales=(
                        'Decomiso de Armas o Drogas',
                        lambda x: x.sum() + df_pres_full.loc[x.index, 'Retención de Licor'].sum() + 
                                  df_pres_full.loc[x.index, 'Artículos Varios Decomisados / Recuperados'].sum()
                    ),
                    Alteracion_Totales=('Desalojos y Desórdenes (Multitudes)', 'sum'),
                    Faltas_Totales=(
                        'Retención de Carnets (Salud)',
                        lambda x: x.sum() + df_pres_full.loc[x.index, 'Destrucción de Alimentos (MINSA)'].sum() + 
                                  df_pres_full.loc[x.index, 'Multas, Sanciones y Citaciones'].sum()
                    )
                ).reset_index()

                # --- CONTENEDOR CON EL MAPA DE RELIEVE REAL DE PANAMÁ DE FONDO ---
                st.markdown("""
                <div style="position: relative; width: 100%; background-image: linear-gradient(rgba(11, 15, 25, 0.45), rgba(11, 15, 25, 0.45)), url('https://upload.wikimedia.org/wikipedia/commons/e/ec/Panama_relieve.png'); background-size: cover; background-position: center; border: 3px solid #00ffff; border-radius: 16px; padding: 25px; box-shadow: 0 0 30px rgba(0,255,255,0.4);">
                """, unsafe_allow_html=True)

                num_cols = 3
                filas_prov = [agrupado_prov.iloc[i] for i in range(len(agrupado_prov))]
                
                for i in range(0, len(filas_prov), num_cols):
                    cols_st = st.columns(num_cols)
                    for j in range(num_cols):
                        if i + j < len(filas_prov):
                            row = filas_prov[i + j]
                            provincia_nombre = row[col_grupo_prov]
                            t_ev = int(row['Total_Eventos'])
                            t_del = int(row['Total_Delegaciones'])
                            c_cap = int(row['Capturas_Totales'])
                            c_med = int(row['Evacuaciones_Totales'])
                            c_dec = int(row['Decomisos_Totales'])
                            c_alt = int(row['Alteracion_Totales'])
                            c_fal = int(row['Faltas_Totales'])

                            acciones_html = ""
                            if c_cap > 0:
                                acciones_html += f"<div style='color:#ff3333; font-size:12px; font-weight:bold; margin-top:4px;'>• Capturas / Aprehensiones: {c_cap}</div>"
                            if c_med > 0:
                                acciones_html += f"<div style='color:#00ff66; font-size:12px; font-weight:bold; margin-top:4px;'>• Evacuaciones / Médicas: {c_med}</div>"
                            if c_dec > 0:
                                acciones_html += f"<div style='color:#ffae00; font-size:12px; font-weight:bold; margin-top:4px;'>• Decomisos / Recuperaciones: {c_dec}</div>"
                            if c_alt > 0:
                                acciones_html += f"<div style='color:#bd00ff; font-size:12px; font-weight:bold; margin-top:4px;'>• Alteración del Orden: {c_alt}</div>"
                            if c_fal > 0:
                                acciones_html += f"<div style='color:#00c8ff; font-size:12px; font-weight:bold; margin-top:4px;'>• Faltas Adm. / MINSA: {c_fal}</div>"

                            seccion_acciones = f"""
                            <div style="margin-top: 6px; font-weight: bold; color: #ffae00; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Acciones Clave:</div>
                            {acciones_html}
                            """ if acciones_html else ""

                            with cols_st[j]:
                                st.markdown(f"""
                                <div style="background: rgba(11, 15, 25, 0.95); border: 2px solid rgba(0, 255, 255, 0.75); border-radius: 12px; padding: 18px; margin-bottom: 22px; box-shadow: 0 0 15px rgba(0,255,255,0.3);">
                                    <div style="background: linear-gradient(90deg, #1b365d, #0b0f19); color: #ffffff; padding: 10px 14px; border-radius: 8px; font-weight: bold; font-size: 15px; margin-bottom: 14px; text-align: center; border-bottom: 2px solid #00ffff; letter-spacing: 1px;">
                                        🛡️ PROVINCIA: {provincia_nombre.upper()}
                                    </div>
                                    <div style="font-size: 13px; color: #e2e8f0; line-height: 1.8;">
                                        <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed rgba(255,255,255,0.15); padding-bottom: 4px; margin-bottom: 6px;">
                                            <span style="color: #00ffff; font-weight: bold;">Total Eventos:</span> 
                                            <span style="font-weight: bold; color: #ffffff; font-size: 14px;">{t_ev}</span>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed rgba(255,255,255,0.15); padding-bottom: 6px; margin-bottom: 8px;">
                                            <span style="color: #00ff66; font-weight: bold;">Total Delegaciones:</span> 
                                            <span style="font-weight: bold; color: #ffffff; font-size: 14px;">{t_del}</span>
                                        </div>
                                        {seccion_acciones}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("ℹ️ No hay registros suficientes en el rango de fechas seleccionado para generar la presentación técnica regional.")

    else:
        st.warning("⚠️ No hay incidentes cargados en la base de datos de Google Sheets.")
        
except Exception as e:
    st.error(f"Error procesando la bitácora: {e}")
