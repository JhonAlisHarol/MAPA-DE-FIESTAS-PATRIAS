import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import unicodedata
import re
import base64
import os
import html

# ==============================================================================
# 0. CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="S-Portal Hexagon | Traffic Center", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. CARGA LOCAL DEL VIDEO DE FONDO (CONVERSIÓN SEGURA A BASE64)
# ==============================================================================
def obtener_video_base64(ruta_video):
    if os.path.exists(ruta_video):
        with open(ruta_video, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    return None

video_path = "video_dashboard.mp4"
video_base64 = obtener_video_base64(video_path)

video_html = f"""
    <video autoplay muted loop class="bg-video">
        <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
        Tu navegador no soporta videos de fondo HTML5.
    </video>
""" if video_base64 else "<div style='position:fixed; top:0; left:0; width:100vw; height:100vh; background:#0a0e17; z-index:-2;'></div>"

# ==============================================================================
# 2. ESTILOS CSS UNIFICADOS (CINTA NEÓN EN TONOS AZULES / CIAN E ICONOS HUD)
# ==============================================================================
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    .stApp {{
        background-color: #0a0e17;
    }}

    .bg-video {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        object-fit: cover;
        z-index: -2;
    }}

    .stApp, [data-testid="stSidebar"], .stMainBlockContainer {{
        background-color: transparent !important;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.65);
        z-index: -1;
    }}
    
    div, p, h1, h2, h3, label, span {{
        color: #ffffff !important;
    }}

    .stMetric {{ 
        background: rgba(255, 255, 255, 0.05); 
        border: 1px solid #00ebff; 
        border-radius: 10px; 
        padding: 10px; 
    }}

    .neon-container {{
        position: relative;
        border-radius: 10px;
        padding: 4px;
        background: rgba(10, 14, 23, 1);
        background-clip: padding-box;
        border: 1px solid transparent;
        overflow: hidden;
        margin-bottom: 1rem;
    }}

    .neon-container::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            #001133, #0077ff, #00ebff, #ffffff, #00ebff, #0077ff, #001133
        );
        animation: rotate-neon 3s linear infinite;
        z-index: 0;
    }}

    .neon-title-container {{
        position: relative;
        border-radius: 12px;
        padding: 3px; 
        background: #0d121f;
        overflow: hidden;
        margin-bottom: 1.5rem;
        box-shadow: 0 0 20px rgba(0, 235, 255, 0.2);
    }}
    
    .neon-title-container::before {{
        content: '';
        position: absolute;
        top: -150%;
        left: -150%;
        width: 400%;
        height: 400%;
        background: conic-gradient(
            from 0deg, #00ffff 0%, #0077ff 25%, #001133 50%, #0077ff 75%, #00ffff 100%
        );
        animation: rotate-neon 4s linear infinite;
        z-index: 0;
    }}

    .neon-title-inner {{
        position: relative;
        background: #0d121f; 
        border-radius: 9px;
        padding: 22px;
        z-index: 1;
        text-align: center;
    }}

    .neon-title-inner h1 {{
        margin: 0; font-size: 32px; font-weight: 800; letter-spacing: 1px;
        text-transform: uppercase;
        background: linear-gradient(45deg, #ffffff, #00ebff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        display: inline-block;
    }}

    .neon-inner-content {{
        position: relative; background: #0d121f; border-radius: 7px; padding: 15px; z-index: 1;
    }}

    @keyframes rotate-neon {{
        from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }}
    }}

    .neon-inner-content h3 {{ margin: 0; font-size: 14px; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }}
    .neon-inner-content p {{ margin: 0; font-size: 28px; font-weight: bold; color: #00ebff !important; }}
    .author-text {{ color: #00ebff !important; font-size: 14px; font-style: italic; margin-top: -5px; margin-bottom: 20px; text-align: center; }}
    
    .map-overlay-total {{
        position: relative; top: 60px; left: 20px;
        background: rgba(10, 14, 23, 0.85); border: 2px solid #00ebff;
        padding: 10px 20px; border-radius: 10px; z-index: 100;
        width: fit-content; margin-bottom: -70px;
    }}

    .hud-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #ffffff;
        margin: 15px 0 10px 0;
        border-left: 3px solid #00ebff;
        padding-left: 10px;
    }}

    .hud-sub {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 16px;
        font-weight: 700;
        color: #00ebff !important;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .ops-security-card {{
        background: linear-gradient(180deg, rgba(6, 22, 42, 0.92) 0%, rgba(3, 10, 22, 0.98) 100%);
        border: 2px solid #00d4ff;
        border-radius: 12px;
        padding: 14px 12px;
        box-shadow: 0 0 18px rgba(0, 212, 255, 0.35), inset 0 0 20px rgba(0, 168, 255, 0.15);
        position: relative;
        overflow: hidden;
        height: 150px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }}
    .ops-security-card::before {{
        content: "";
        position: absolute;
        top: 4px; left: 4px; right: 4px; bottom: 4px;
        border: 1px dashed rgba(0, 212, 255, 0.22);
        border-radius: 8px;
        pointer-events: none;
    }}
    .ops-card-body {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        height: 100%;
        z-index: 2;
        padding: 0 4px;
    }}
    .ops-card-left {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: left;
        max-width: 52%;
    }}
    .ops-card-title {{
        color: #a0d8ef !important;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 8px;
        text-shadow: 0 0 6px rgba(0, 212, 255, 0.6);
        line-height: 1.1;
    }}
    .ops-card-value {{
        color: #ffffff !important;
        font-size: 32px;
        font-weight: 900;
        line-height: 1;
        text-shadow: 0 0 14px rgba(0, 235, 255, 0.9);
        font-family: sans-serif;
    }}
    .ops-card-right {{
        width: 48%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    ::-webkit-scrollbar {{
        width: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05); 
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(0, 212, 255, 0.5); 
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(0, 212, 255, 0.8); 
    }}

    @media (max-width: 768px) {{
        .neon-title-inner h1 {{ font-size: 22px !important; }}
        .neon-inner-content p {{ font-size: 22px !important; }}
        .map-overlay-total {{ position: relative; top: 10px; left: 10px; margin-bottom: 10px; width: 90%; }}
        .stPlotlyChart {{ height: 350px !important; }}
    }}
    </style>

    {video_html}
""", unsafe_allow_html=True)

# ==============================================================================
# 2.5 CATÁLOGO DE ILUSTRACIONES TÁCTICAS AVANZADAS
# ==============================================================================
SVG_SHIELD = '<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 6px #00ebff); vertical-align:middle;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
SVG_ACTIVITY = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
SVG_CHECK = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ffaa" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ffaa); vertical-align:middle;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
SVG_RADAR = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/><line x1="12" y1="2" x2="12" y2="12"/></svg>'
SVG_MAP_PIN = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'
SVG_GRID = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>'
SVG_SIGNAL = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><path d="M2 20h.01"/><path d="M7 20v-4"/><path d="M12 20v-8"/><path d="M17 20V8"/><path d="M22 4v16"/></svg>'
SVG_CLOCK = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
SVG_TARGET = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><circle cx="12" cy="12" r="10"/><line x1="22" y1="12" x2="18" y2="12"/><line x1="6" y1="12" x2="2" y2="12"/><line x1="12" y1="6" x2="12" y2="2"/><line x1="12" y1="22" x2="12" y2="18"/></svg>'
SVG_GUN = '<svg viewBox="0 0 24 24" width="22" height="22" fill="#00ebff" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><path d="M3 8h16a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-3v1l1.5 4.5a2 2 0 0 1-1.9 2.5h-3.2a2 2 0 0 1-1.9-1.4L9.3 16H3a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2z"/></svg>'
SVG_FILE = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#00ebff" stroke-width="2" style="filter:drop-shadow(0 0 5px #00ebff); vertical-align:middle;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
SVG_ALERT = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#ff4b4b" stroke-width="2" style="filter:drop-shadow(0 0 5px #ff4b4b); vertical-align:middle;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'

ILLUST_FLAGRANCIA = '<svg viewBox="0 0 130 115" width="85" height="85" style="filter:drop-shadow(0 0 6px rgba(0,212,255,0.5));"><rect x="4" y="4" width="66" height="24" rx="4" fill="#06152d" stroke="#00d4ff" stroke-width="1.2"/><path d="M10 14 C10 11, 15 11, 15 14 C15 11, 20 11, 20 14 C20 19, 15 22, 15 24 C15 22, 10 19, 10 14 Z" fill="#ff3366"/><polyline points="24,16 30,16 33,9 37,23 41,12 44,18 48,16 66,16" fill="none" stroke="#00ffaa" stroke-width="1.5"/><circle cx="110" cy="18" r="11" fill="#06152d" stroke="#00d4ff" stroke-width="1.5"/><polyline points="110,11 110,18 115,18" fill="none" stroke="#ffffff" stroke-width="1.5"/><ellipse cx="68" cy="106" rx="45" ry="5" fill="rgba(0,212,255,0.25)"/><path d="M35 38 L49 38 L52 33 L32 33 Z" fill="#00a8ff"/><circle cx="41" cy="44" r="6.5" fill="#f0c8a0"/><path d="M28 54 C28 50, 50 50, 52 56 L54 80 L30 80 Z" fill="#103466" stroke="#00d4ff" stroke-width="1"/><polygon points="46,58 49,58 49,62 46,62" fill="#ffcc00"/><path d="M32 80 L30 105 M48 80 L52 105" stroke="#0c2852" stroke-width="5" stroke-linecap="round"/><circle cx="68" cy="54" r="6" fill="#d8b08c"/><path d="M56 62 C62 58, 76 60, 78 68 L74 86 L54 84 Z" fill="#3a506b" stroke="#a0d8ef" stroke-width="1"/><path d="M58 84 L55 104 M71 85 L74 104" stroke="#2b3d54" stroke-width="4.5" stroke-linecap="round"/><path d="M90 36 L104 36 L107 31 L87 31 Z" fill="#00a8ff"/><circle cx="96" cy="42" r="6.5" fill="#f0c8a0"/><path d="M84 52 C86 48, 108 48, 110 55 L108 80 L84 80 Z" fill="#103466" stroke="#00d4ff" stroke-width="1"/><path d="M88 80 L84 105 M104 80 L108 105" stroke="#0c2852" stroke-width="5" stroke-linecap="round"/><path d="M48 64 L64 72 M88 62 L70 72" stroke="#103466" stroke-width="4" stroke-linecap="round"/><circle cx="65" cy="73" r="3" fill="none" stroke="#ffffff" stroke-width="1.5"/><circle cx="70" cy="73" r="3" fill="none" stroke="#ffffff" stroke-width="1.5"/></svg>'

ILLUST_OFICIO = '<svg viewBox="0 0 130 115" width="85" height="85" style="filter:drop-shadow(0 0 6px rgba(0,212,255,0.5));"><ellipse cx="65" cy="65" rx="52" ry="22" fill="none" stroke="#00ebff" stroke-width="1.5" stroke-dasharray="6 4"/><ellipse cx="65" cy="72" rx="46" ry="16" fill="none" stroke="#00a8ff" stroke-width="1"/><rect x="30" y="10" width="64" height="86" rx="4" fill="#0a192f" stroke="#00a8ff" stroke-width="1.5"/><rect x="36" y="15" width="64" height="86" rx="4" fill="#e6f2ff" stroke="#00d4ff" stroke-width="2"/><path d="M48 22 L56 25 L56 33 C56 38, 48 41, 48 41 C48 41, 40 38, 40 33 L40 25 Z" fill="#ffd700" stroke="#996515" stroke-width="1.2"/><rect x="60" y="24" width="28" height="4" rx="1" fill="#06152d"/><rect x="60" y="32" width="22" height="4" rx="1" fill="#0077cc"/><line x1="44" y1="48" x2="90" y2="48" stroke="#0077cc" stroke-width="2"/><line x1="44" y1="55" x2="90" y2="55" stroke="#4a7c59" stroke-width="1.5"/><line x1="44" y1="62" x2="90" y2="62" stroke="#4a7c59" stroke-width="1.5"/><line x1="44" y1="69" x2="78" y2="69" stroke="#4a7c59" stroke-width="1.5"/><polygon points="48,92 43,108 51,103 57,108 54,92" fill="#0066cc"/><circle cx="50" cy="88" r="9" fill="#ffd700" stroke="#b8860b" stroke-width="1.5"/><path d="M62 88 Q70 82 76 87 T88 85" fill="none" stroke="#06152d" stroke-width="1.5"/><g transform="translate(86, 42) rotate(35)"><rect x="0" y="0" width="7" height="42" rx="2" fill="#102a45" stroke="#ffd700" stroke-width="1.2"/><polygon points="0,42 7,42 3.5,51" fill="#ffd700"/><rect x="0" y="6" width="7" height="3" fill="#ffd700"/></g></svg>'

ILLUST_ARMAS = '<svg viewBox="0 0 130 115" width="85" height="85" style="filter:drop-shadow(0 0 6px rgba(0,212,255,0.5));"><rect x="8" y="8" width="38" height="22" rx="2" fill="rgba(0,168,255,0.12)" stroke="#00d4ff" stroke-width="1"/><path d="M12 19 L38 19 M18 19 L16 25 M26 15 L32 15" stroke="#00ebff" stroke-width="1.5"/><g transform="translate(65,58) rotate(-35) translate(-65,-58)"><rect x="15" y="53" width="95" height="5" fill="#2b3d54" stroke="#00d4ff" stroke-width="1"/><path d="M15 53 L4 62 L18 64 L25 58 Z" fill="#1a2636" stroke="#00d4ff" stroke-width="1"/><rect x="52" y="58" width="10" height="18" rx="1" fill="#1a2636" stroke="#00a8ff" stroke-width="1"/><rect x="38" y="58" width="7" height="12" fill="#1a2636" stroke="#00a8ff" stroke-width="1"/><rect x="48" y="47" width="22" height="5" fill="#101824" stroke="#00ebff" stroke-width="1"/></g><g transform="translate(65,58) rotate(35) translate(-65,-58)"><rect x="15" y="53" width="95" height="5.5" fill="#3a506b" stroke="#00d4ff" stroke-width="1"/><path d="M110 53 L124 62 L112 65 L102 58 Z" fill="#1a2636" stroke="#00d4ff" stroke-width="1"/><rect x="65" y="58" width="9" height="17" transform="rotate(15 65 58)" fill="#1a2636" stroke="#00a8ff" stroke-width="1"/><rect x="80" y="58" width="6" height="11" fill="#1a2636" stroke="#00a8ff" stroke-width="1"/></g><g transform="translate(60, 12)"><path d="M0 6 L28 6 L28 14 L10 14 L14 26 L5 26 L2 14 L0 14 Z" fill="#2b3d54" stroke="#00ebff" stroke-width="1.2"/></g><g transform="translate(14, 52)"><path d="M0 6 L26 6 L26 14 L9 14 L13 25 L4 25 L2 14 L0 14 Z" fill="#1c2d42" stroke="#00a8ff" stroke-width="1.2"/></g><g transform="translate(22, 86)"><rect x="0" y="6" width="5" height="14" fill="#d4af37"/><path d="M0 6 Q2.5 0 5 6 Z" fill="#b87333"/><rect x="8" y="6" width="5" height="14" fill="#d4af37"/><path d="M8 6 Q10.5 0 13 6 Z" fill="#b87333"/><rect x="16" y="6" width="5" height="14" fill="#d4af37"/><path d="M16 6 Q18.5 0 21 6 Z" fill="#b87333"/><rect x="24" y="6" width="5" height="14" fill="#d4af37"/><path d="M24 6 Q26.5 0 29 6 Z" fill="#b87333"/></g><g transform="translate(68, 86) rotate(20)"><rect x="0" y="3" width="16" height="5" rx="1" fill="#1a2636" stroke="#00a8ff" stroke-width="1"/><path d="M16 1 L44 5.5 L16 10 Z" fill="#e0e8f0" stroke="#00d4ff" stroke-width="1"/></g></svg>'

ILLUST_DROGAS = '<svg viewBox="0 0 130 115" width="85" height="85" style="filter:drop-shadow(0 0 6px rgba(0,212,255,0.5));"><polygon points="105,12 118,32 92,32" fill="rgba(255,170,0,0.2)" stroke="#ffaa00" stroke-width="1.5"/><line x1="105" y1="18" x2="105" y2="25" stroke="#ffaa00" stroke-width="2" stroke-linecap="round"/><circle cx="105" cy="29" r="1.2" fill="#ffaa00"/><rect x="44" y="12" width="38" height="46" rx="2" fill="rgba(0, 212, 255, 0.15)" stroke="#00ebff" stroke-width="1.5"/><line x1="44" y1="19" x2="82" y2="19" stroke="#ff3366" stroke-width="1.5"/><circle cx="55" cy="36" r="4.5" fill="#00d4ff"/><circle cx="67" cy="33" r="4.5" fill="#0099cc"/><circle cx="61" cy="44" r="4.5" fill="#00ebff"/><circle cx="72" cy="43" r="4.5" fill="#00a8ff"/><circle cx="52" cy="48" r="4" fill="#66f0ff"/><circle cx="64" cy="51" r="4" fill="#0077aa"/><rect x="18" y="38" width="34" height="42" rx="2" fill="rgba(0, 212, 255, 0.12)" stroke="#00a8ff" stroke-width="1.5"/><line x1="18" y1="44" x2="52" y2="44" stroke="#00ebff" stroke-width="1.2"/><ellipse cx="29" cy="60" rx="5" ry="3" transform="rotate(-25 29 60)" fill="#e6c280"/><ellipse cx="41" cy="58" rx="5" ry="3" transform="rotate(15 41 58)" fill="#d4a359"/><ellipse cx="34" cy="70" rx="5" ry="3" transform="rotate(10 34 70)" fill="#f0d5a0"/><rect x="48" y="58" width="36" height="44" rx="2" fill="rgba(0, 212, 255, 0.18)" stroke="#00ebff" stroke-width="1.5"/><line x1="48" y1="64" x2="84" y2="64" stroke="#ffaa00" stroke-width="1.2"/><polygon points="58,78 65,73 72,80 65,86" fill="#80f5ff"/><polygon points="68,85 75,80 80,88 73,93" fill="#00d4ff"/><polygon points="55,88 62,84 66,93 58,96" fill="#b3faff"/><g transform="translate(80, 48)"><rect x="0" y="0" width="34" height="14" rx="2" fill="#c29b61" stroke="#ffd700" stroke-width="1"/><line x1="10" y1="0" x2="10" y2="14" stroke="#8c6d3f" stroke-width="1.5"/><line x1="24" y1="0" x2="24" y2="14" stroke="#8c6d3f" stroke-width="1.5"/><rect x="4" y="17" width="34" height="14" rx="2" fill="#b0894f" stroke="#ffd700" stroke-width="1"/><line x1="14" y1="17" x2="14" y2="31" stroke="#7a5c32" stroke-width="1.5"/><line x1="28" y1="17" x2="28" y2="31" stroke="#7a5c32" stroke-width="1.5"/></g></svg>'

ILLUST_MUNICIONES = '<svg viewBox="0 0 130 115" width="85" height="85" style="filter:drop-shadow(0 0 6px rgba(0,212,255,0.5));"><circle cx="20" cy="24" r="5" fill="#06152d" stroke="#00ebff" stroke-width="1.2"/><circle cx="112" cy="30" r="4.5" fill="#06152d" stroke="#00ebff" stroke-width="1.2"/><circle cx="24" cy="92" r="4" fill="#06152d" stroke="#00ebff" stroke-width="1.2"/><circle cx="108" cy="90" r="5" fill="#06152d" stroke="#00ebff" stroke-width="1.2"/><circle cx="68" cy="58" r="42" fill="#071936" stroke="#00ebff" stroke-width="2.5"/><circle cx="68" cy="58" r="32" fill="none" stroke="#00a8ff" stroke-width="1.2" stroke-dasharray="6 4"/><line x1="20" y1="58" x2="116" y2="58" stroke="#00ebff" stroke-width="1.5"/><line x1="68" y1="10" x2="68" y2="106" stroke="#00ebff" stroke-width="1.5"/><g transform="translate(44, 38)"><path d="M0 16 Q5.5 0 11 16 Z" fill="#d9822b" stroke="#ffd700" stroke-width="1"/><rect x="0" y="16" width="11" height="28" rx="1" fill="#e6be5a" stroke="#b8860b" stroke-width="1"/><rect x="-1" y="44" width="13" height="3" fill="#b8860b"/></g><g transform="translate(61, 28)"><path d="M0 18 Q7 0 14 18 Z" fill="#e68a2e" stroke="#ffd700" stroke-width="1.2"/><rect x="0" y="18" width="14" height="36" rx="1" fill="#ffd700" stroke="#b8860b" stroke-width="1.2"/><rect x="-1" y="54" width="16" height="4" fill="#cc9900"/></g><g transform="translate(81, 38)"><path d="M0 16 Q5.5 0 11 16 Z" fill="#d9822b" stroke="#ffd700" stroke-width="1"/><rect x="0" y="16" width="11" height="28" rx="1" fill="#e6be5a" stroke="#b8860b" stroke-width="1"/><rect x="-1" y="44" width="13" height="3" fill="#b8860b"/></g></svg>'

ILLUST_VEHICULOS = '<svg viewBox="0 0 130 115" width="85" height="85" style="filter:drop-shadow(0 0 6px rgba(0,212,255,0.5));"><g transform="translate(18, 8)"><path d="M18 14 L32 4 L68 4 L80 14 L96 16 L98 28 L4 28 L6 16 Z" fill="#102a45" stroke="#00ebff" stroke-width="1.5"/><path d="M34 6 L64 6 L74 14 L24 14 Z" fill="#e6f7ff"/><rect x="38" y="15" width="24" height="11" fill="#ffffff"/><rect x="44" y="1" width="6" height="3" fill="#ff3333"/><rect x="50" y="1" width="6" height="3" fill="#00ebff"/><circle cx="22" cy="28" r="7" fill="#0a121e" stroke="#00d4ff" stroke-width="2"/><circle cx="78" cy="28" r="7" fill="#0a121e" stroke="#00d4ff" stroke-width="2"/></g><g transform="translate(4, 46)"><circle cx="10" cy="22" r="6" fill="#0a121e" stroke="#00d4ff" stroke-width="1.8"/><circle cx="34" cy="22" r="6" fill="#0a121e" stroke="#00d4ff" stroke-width="1.8"/><path d="M10 22 L18 10 L30 12 L34 22 M16 14 L26 14" fill="none" stroke="#00ebff" stroke-width="2"/><path d="M26 10 L32 4 L36 8" fill="none" stroke="#ffffff" stroke-width="1.5"/></g><g transform="translate(36, 56)"><path d="M12 18 L24 4 L82 4 L86 20 L86 38 L4 38 L4 22 Z" fill="#163659" stroke="#00ebff" stroke-width="1.5"/><path d="M16 18 L26 7 L44 7 L44 18 Z" fill="#a0e8ff"/><rect x="48" y="7" width="14" height="11" fill="#70c8e8"/><rect x="66" y="7" width="14" height="11" fill="#70c8e8"/><rect x="44" y="1" width="10" height="3" fill="#ffaa00"/><circle cx="22" cy="38" r="8" fill="#0a121e" stroke="#00d4ff" stroke-width="2"/><circle cx="68" cy="38" r="8" fill="#0a121e" stroke="#00d4ff" stroke-width="2"/><rect x="6" y="25" width="5" height="4" fill="#ffffff"/></g></svg>'

ILLUST_COORDINACIONES = '<svg viewBox="0 0 130 115" width="85" height="85" style="filter:drop-shadow(0 0 6px rgba(0,212,255,0.5));"><rect x="15" y="15" width="100" height="85" rx="8" fill="#0a192f" stroke="#00d4ff" stroke-width="2"/><line x1="30" y1="35" x2="70" y2="35" stroke="#00ebff" stroke-width="3" stroke-linecap="round"/><line x1="30" y1="55" x2="100" y2="55" stroke="#00a8ff" stroke-width="2" stroke-linecap="round"/><line x1="30" y1="75" x2="85" y2="75" stroke="#00a8ff" stroke-width="2" stroke-linecap="round"/><circle cx="95" cy="35" r="5" fill="#00ffaa"/></svg>'

def render_ops_card(titulo, valor, svg_ilustracion):
    return (
        f'<div class="ops-security-card notranslate" translate="no">'
        f'<div class="ops-card-body">'
        f'<div class="ops-card-left">'
        f'<div class="ops-card-title">{titulo}</div>'
        f'<div class="ops-card-value">{valor:,}</div>'
        f'</div>'
        f'<div class="ops-card-right">{svg_ilustracion}</div>'
        f'</div>'
        f'</div>'
    )

# ==============================================================================
# 3. VARIABLES Y MAPEOS TÁCTICOS
# ==============================================================================
map_tactico_raw = {
    # CAPTURAS
    'Aprehensión de Menor por Alerta de Custodia': 'CAPTURAS',
    'Ciudadano Capturado por Alerta Penitenciaria': 'CAPTURAS',
    'Ciudadano Aprehendido': 'CAPTURAS',
    'Ciudadano Aprehendido por Inviolabilidad Del Domicilio': 'CAPTURAS',
    'Ciudadano Aprehendido por Libertad Vigilada': 'CAPTURAS',
    'Ciudadano Aprehendido con Accesorio De Arma De Fuego': 'CAPTURAS',
    'Ciudadano Aprehendido por Supuesta Vinculación A Delito': 'CAPTURAS',
    'Ciudadano Aprehendido por Subrogado Penal': 'CAPTURAS',
    'Ciudadano Aprehendido por Privación De Libertad': 'CAPTURAS',
    'Ciudadano Aprehendido por Estafa Simple': 'CAPTURAS',
    'Ciudadano Aprehendido por Intento De Violación': 'CAPTURAS',
    'Ciudadano Aprehendido por Maltrato De Niños(As)-Adolescentes': 'CAPTURAS',
    'Ciudadano Aprehendido por Agresiones Fisicas': 'CAPTURAS',
    'Ciudadano Aprehendido por Agresiones Verbales': 'CAPTURAS',
    'Ciudadano Aprehendido por Quebrantamiento De Boleta De Protección': 'CAPTURAS',
    'Ciudadano Aprehendido por Lesiones Personales Con Arma Blanca': 'CAPTURAS',
    'Ciudadano Aprehendido por Falsificación De Documentos': 'CAPTURAS',
    'Ciudadano Aprehendido por Falsificación De Monedas': 'CAPTURAS',
    'Ciudadano Aprehendido por No Portar Documento de Identidad Personal': 'CAPTURAS',
    'Ciudadano Aprehendido por Daño A La Prop. Privada': 'CAPTURAS',
    'Ciudadano Aprehendido por Alteración De La Convivencia Pacífica': 'CAPTURAS',
    'Ciudadano Aprehendido por Riña o Pelea': 'CAPTURAS',
    'Ciudadano Aprehendido por Consumo de Licor en Vía Pública': 'CAPTURAS',
    'Ciudadano Aprehendido por Violencia Doméstica': 'CAPTURAS',
    'Ciudadana Aprehendida por Violencia Doméstica': 'CAPTURAS',
    'Ciudadano Aprehendido con Sustancias Ilícitas': 'CAPTURAS',
    'Ciudadano Aprehendido por Lesiones Personales': 'CAPTURAS',
    'Ciudadano Aprehendido por Oficio de Captura': 'CAPTURAS',
    'Ciudadano Aprehendido por Oficio de Conducción': 'CAPTURAS',
    'Ciudadano Aprehendido por Hurto A Propiedad': 'CAPTURAS',
    'Ciudadano Aprehendido por Hurto': 'CAPTURAS',
    'Ciudadano Aprehendido por Intento de Hurto': 'CAPTURAS',
    'Ciudadano Aprehendido por Hurto de Accesorio De Vehículo': 'CAPTURAS',
    'Ciudadano Aprehendido por Hurto A local Comercial': 'CAPTURAS',
    'Ciudadano Aprehendido por Hurto Simple A Persona': 'CAPTURAS',
    'Ciudadano Aprehendido por Hurto Simple a Propiedad': 'CAPTURAS',
    'Ciudadano Aprehendido por Hurto A Residencia': 'CAPTURAS',
    'Ciudadano Aprehendido por Hurto De Vehículo': 'CAPTURAS',
    'Ciudadano Aprehendido por Robo A Persona Con Arma De Fuego': 'CAPTURAS',
    'Ciudadano Aprehendido por Robo A Propiedad': 'CAPTURAS',
    'Ciudadano Aprehendido por Robo A local Comercial': 'CAPTURAS',
    'Ciudadano Aprehendido por Robo Simple a Persona': 'CAPTURAS',
    'Ciudadano Aprehendido por Robo Simple (carterista)': 'CAPTURAS',
    'Ciudadano Aprehendido por Robo de Vehículo (Alerta Temprana)': 'CAPTURAS',
    'Ciudadano Aprehendido con Arma Blanca': 'CAPTURAS',
    'Ciudadano Aprehendido con Arma de Fuego': 'CAPTURAS',
    'Ciudadano Notificado por Oficio de Citación': 'CAPTURAS',
    'Ciudadano Aprehendido por Evasión de Centro Penal': 'CAPTURAS',
    'Supuesta Vinculación A Delito': 'CAPTURAS',

    # RECUPERACIONES
    'Arma de Fuego - Decomiso - Escopeta': 'RECUPERACIONES',
    'Arma de Fuego - Decomiso - Fusil': 'RECUPERACIONES',
    'Arma de Fuego - Decomiso - Rifle': 'RECUPERACIONES',
    'Arma de Fuego - Decomiso - Pistola': 'RECUPERACIONES',
    'Arma de Fuego - Decomiso - Revolver': 'RECUPERACIONES',
    'Arma de Fuego - Hallazgo - Escopeta': 'RECUPERACIONES',
    'Arma de Fuego - Hallazgo - Fusil': 'RECUPERACIONES',
    'Arma de Fuego - Hallazgo - Pistola': 'RECUPERACIONES',
    'Arma de Fuego - Hallazgo - Revolver': 'RECUPERACIONES',
    'Arma de Fuego - Replica Decomiso': 'RECUPERACIONES',
    'Arma de Fuego - Replica Hallazgo': 'RECUPERACIONES',
    'Articulo de Dudosa Procedencia': 'RECUPERACIONES',
    'Articulo Recuperados': 'RECUPERACIONES',
    'Decomiso de Articulos Prohibidos': 'RECUPERACIONES',
    'Decomiso de Cajetillas Cigarrillos': 'RECUPERACIONES',
    'Hallazgo de Sustancia Ilícita': 'RECUPERACIONES',
    'Decomiso de Sustancia Ilícita': 'RECUPERACIONES',
    'Menor Infractor por Hurto': 'RECUPERACIONES',
    'Menor Infractor por Robo': 'RECUPERACIONES',
    'Vehículo Recuperado': 'RECUPERACIONES',
    'Vehículo Recuperado por Secuestro Judicial de Bienes': 'RECUPERACIONES',
    'Vehículo Recuperado por Apropiación Indebida': 'RECUPERACIONES',
    'Vehículo Recuperado por Hurto (Alerta Temprana)': 'RECUPERACIONES',
    'Vehículo Recuperado por Robo (Alerta Temprana)': 'RECUPERACIONES',
    'Vehículo recuperado por Oficio de Hurto': 'RECUPERACIONES',
    'Vehículo recuperado por Oficio de Robo': 'RECUPERACIONES',

    # COORDINACIONES
    'Coordinación con Casa de Justicia y Paz': 'COORDINACIONES',
    'Coordinación con Alcaldía Municipal': 'COORDINACIONES',
    'Coordinación con Atención Primaria': 'COORDINACIONES',

    # SEGURIDAD VIAL
    'Atención de Atropello': 'SEGURIDAD VIAL',
    'Atención de Atropello con victima fatal': 'SEGURIDAD VIAL',
    'Atención de Caida de Vehiculo en la Cuneta': 'SEGURIDAD VIAL',
    'Atención de Choque con Objeto Fijo': 'SEGURIDAD VIAL',
    'Atención de Colisión de Alto Impacto': 'SEGURIDAD VIAL',
    'Atención de Colisión Con Víctima Fatal': 'SEGURIDAD VIAL',
    'Atención de Choque Con Victima Fatal': 'SEGURIDAD VIAL',
    'Atención de Colisión menor': 'SEGURIDAD VIAL',
    'Atención de Colisión multiple': 'SEGURIDAD VIAL',
    'Atención de Colision y Fuga': 'SEGURIDAD VIAL',
    'Atención de Colision y vuelco': 'SEGURIDAD VIAL',
    'Atención de Derrame de Combustible': 'SEGURIDAD VIAL',
    'Atención de Derrape de Motorizado': 'SEGURIDAD VIAL',
    'Atención de Derrape de Motorizado con Víctima Fatal': 'SEGURIDAD VIAL',
    'Atención de Triple Colisión': 'SEGURIDAD VIAL',
    'Atención de Vuelco': 'SEGURIDAD VIAL',
    'Infracción por Ceder el Manejo a Persona No Autorizada': 'SEGURIDAD VIAL',
    'Infracción por Conducir a Velocidad Superior al Limite': 'SEGURIDAD VIAL',
    'Infracción por Conducir con Aliento Alcohólico': 'SEGURIDAD VIAL',
    'Infracción por Conducir de Forma Desordenada': 'SEGURIDAD VIAL',
    'Infracción por Conductor en Estado de Embriaguez Comprobado': 'SEGURIDAD VIAL',
    'Infracción por Conductor en Estado Etilico': 'SEGURIDAD VIAL',
    'infraçción por emitir gases, ruidos o sonidos excesivos': 'SEGURIDAD VIAL',
    'Infracción por Daño a la Propiedad': 'SEGURIDAD VIAL',
    'Infracción por Desatender lineas de no pare, paso peatonal e indicaciones del': 'SEGURIDAD VIAL',
    'Infracción por Conducir por el Carril Indebido': 'SEGURIDAD VIAL',
    'Infracción por Negarse a hacerse la Prueba de Alcoholemia': 'SEGURIDAD VIAL',
    'Infracción por Desatender señales': 'SEGURIDAD VIAL',
    'Infracción por Hablar por Teléfono Celular al Conducir': 'SEGURIDAD VIAL',
    'Infracción por Licencia no Adecuada al Vehiculo': 'SEGURIDAD VIAL',
    'Infracción por Luces Inadecuadas': 'SEGURIDAD VIAL',
    'Infracción por Conducir Sin Chaleco Reflectivo': 'SEGURIDAD VIAL',
    'Infracción Nunca ha Sacado Licencia': 'SEGURIDAD VIAL',
    'Infracción por No portar licencia de Conducir': 'SEGURIDAD VIAL',
    'Infracción por No utilizar el Cinturón de Seguridad': 'SEGURIDAD VIAL',
    'Infracción por Papel ahumado en Tono o Lugar no Autorizado': 'SEGURIDAD VIAL',
    'Infracción por Pasar Semáforo en Luz Roja': 'SEGURIDAD VIAL',
    'Infracción por Poliza Vencida': 'SEGURIDAD VIAL',
    'Infracción por Portar Placa con Diseño Diferente a la Oficial': 'SEGURIDAD VIAL',
    'Infracción por Prestar el Servicio en Ruta Distinta a la Establecida': 'SEGURIDAD VIAL',
    'Infracción por Prestar servicio de tránsporte público en vehículo no autorizado': 'SEGURIDAD VIAL',
    'Infracción por Realizar Giros Prohibidos': 'SEGURIDAD VIAL',
    'Infracción por Sin Condiciones Adecuadas de Seguridad': 'SEGURIDAD VIAL',
    'Infracción por Negarse a Detener el Vehículo': 'SEGURIDAD VIAL',
    'Infracción por Sin Equipos de Seguridad': 'SEGURIDAD VIAL',
    'Infracción por Circular en Vía Contraria': 'SEGURIDAD VIAL',
    'Infracción por Transportar Exeso de Pasajero': 'SEGURIDAD VIAL',
    'Infracción por Vehículos de transporte público y Comercial sin identificación': 'SEGURIDAD VIAL',
    'Infracción por Vehiculo con luces no Adecuadas': 'SEGURIDAD VIAL',
    'Infracción por Vehículo sin Cinta Reflectiva': 'SEGURIDAD VIAL',
    'Infracción por Vehículos mal Estacionados': 'SEGURIDAD VIAL',
    'Infracción por Remolcar otro Vehículo sin las Debidas Medidas de Seguridad': 'SEGURIDAD VIAL',
    'Infracción por Licencia de Conducir Vencida': 'SEGURIDAD VIAL',
    'Infracción por Emitir Gases, Ruidos o Sonidos Excesivos': 'SEGURIDAD VIAL',
    'Infracción por Negarse a Entregar la Licencia de Conducir': 'SEGURIDAD VIAL',
    'Infracción por Conducir Obstruyendo el Tránsito': 'SEGURIDAD VIAL',

    # EMERGENCIAS
    'Apoyo a Vehiculo de Valores Desperfectos': 'EMERGENCIAS',
    'Apoyo al Ciudadano': 'EMERGENCIAS',
    'Apoyo al Ciudadano Brindar Seguridad a una Prosecion': 'EMERGENCIAS',
    'Apoyo al Ciudadano Cruce de Peatón': 'EMERGENCIAS',
    'Apoyo al Ciudadano para Reparar Vehículo': 'EMERGENCIAS',
    'Apoyo al Ciudadano Rescate de Persona': 'EMERGENCIAS',
    'Apoyo al Ciudadano Rescate de Embarcacion': 'EMERGENCIAS',
    'Proveedor': 'EMERGENCIAS',
    'Atención Prehospitalaria BCBPA': 'EMERGENCIAS',
    'Atención Prehospitalaria CSS': 'EMERGENCIAS',
    'Atención Prehospitalaria MINSACAPSI': 'EMERGENCIAS',
    'Atención Prehospitalaria Privada': 'EMERGENCIAS',
    'Atención Prehospitalaria Policía Nacional': 'EMERGENCIAS',
    'Atención Prehospitalaria SUME 911': 'EMERGENCIAS',
    'Extinción de Incendio': 'EMERGENCIAS',
    'Extinción del Conato de Incendio': 'EMERGENCIAS',
    'Recuperación de Menor Evadido': 'EMERGENCIAS',
    'Remoción de Vehículo en Grúa': 'EMERGENCIAS',
    'Rescate de Animal Domestico': 'EMERGENCIAS',
    'Rescate de Menor por Alerta AMBER': 'EMERGENCIAS',
    'Rescate de Menor por Riego Social': 'EMERGENCIAS',
    'Rescate de Persona': 'EMERGENCIAS',
    'Rescate de Vida y fauna Silvestre': 'EMERGENCIAS',
    'Restablecimiento de la Segurida Víal': 'EMERGENCIAS',
    'Restitución de Propiedad Extraviada': 'EMERGENCIAS',
    'Traslado a Hospital': 'EMERGENCIAS',
    'Traslado a Hospital por SUME 911': 'EMERGENCIAS',
    'Traslado a Hospital por BCBPA': 'EMERGENCIAS',
    'Traslado a Hospital por Serv. Privado': 'EMERGENCIAS',
    'Traslado a Hospital por Policía Nacional': 'EMERGENCIAS',
    'Traslado a Hospital por CSS': 'EMERGENCIAS'
}

# ==============================================================================
# 4. SEGURIDAD: DEFINICIÓN DE USUARIOS
# ==============================================================================
USUARIOS_AUTORIZADOS = {
    "CONC5": "12345", "CORCOL": "CORCOLONC3", "COMCH": "12345678",
    "COMAR": "hex123", "COMDA": "COMDA2027", "COMCHEP": "hex123",
    "CEVIBO": "hex123", "COMSAM": "hex123", "ALISJHON": "199432", 
    "LUIS DE LA CRUZ": "10941", "JOAQUIN CHI": "10821", "LORENZO BOWEN": "10924"
}

def login():
    st.markdown(f"<div style='display:flex; align-items:center; gap:12px;'>{SVG_SHIELD}<h1 style='margin:0;'>C.O.N - PANAMÁ | ACCESO TÁCTICO</h1></div>", unsafe_allow_html=True)
    st.markdown('<p class="author-text">DESARROLLADO POR= CABO 1° ELMER RODRIGUEZ</p>', unsafe_allow_html=True)
    usuario = st.text_input("Usuario del Centro:")
    clave = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar"):
        if usuario in USUARIOS_AUTORIZADOS and USUARIOS_AUTORIZADOS[usuario] == clave:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Credenciales inválidas")

if "autenticado" not in st.session_state: st.session_state.autenticado = False

if "modo_pantalla" not in st.session_state:
    st.session_state.modo_pantalla = "DASHBOARD OPERATIVO"

if not st.session_state.autenticado:
    login()
    st.stop()

# ==============================================================================
# 5. BARRA LATERAL DE USUARIO E INTERFAZ
# ==============================================================================
with st.sidebar:
    st.write("---")
    st.markdown(f"<div style='display:flex; align-items:center; gap:8px;'>{SVG_SHIELD}<span>OPERADOR: <b>{st.session_state.usuario.upper()}</b></span></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("◈ Dashboard Principal", use_container_width=True):
        st.session_state.modo_pantalla = "DASHBOARD OPERATIVO"
        st.rerun()
        
    if st.button("◈ Presentación Ejecutiva", use_container_width=True):
        st.session_state.modo_pantalla = "PRESENTACION_EJECUTIVA"
        st.rerun()
        
    if st.button("◈ Presentación Mando Policial", use_container_width=True):
        st.session_state.modo_pantalla = "PRESENTACION_MANDO_POLICIAL"
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⏻ Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
    st.write("---")

# ==============================================================================
# 6. FUNCIONES DE LIMPIEZA, MEDIDORES Y MAPA DE CALOR UNIVERSAL
# ==============================================================================
def create_gauge(value, title, color, is_timer=False):
    suffix = " seg" if is_timer else (" h" if value >= 60 else " min")
    display_val = value / 60 if (not is_timer and suffix == " h") else value
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = display_val,
        title = {'text': title, 'font': {'size': 14, 'color': "white"}},
        number = {'suffix': suffix, 'font': {'color': "white"}},
        gauge = {'axis': {'range': [0, 60 if is_timer else max(60, display_val * 1.5)], 'tickcolor': "white"}, 'bar': {'color': color}}
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def obtener_color_alerta(valor, limite_amarillo, limite_rojo):
    if valor >= limite_rojo: return "#ff4b4b" 
    elif valor >= limite_amarillo: return "#ffaa00" 
    else: return "#00ffaa" 

def aplicar_mapa_calor_purpura(df):
    cols_numericas = df.select_dtypes(include=['number']).columns.tolist()
    if not cols_numericas:
        return df

    try:
        max_v = df[cols_numericas].max().max()
        if pd.isna(max_v) or max_v <= 0:
            max_v = 1
    except:
        max_v = 1

    def colorear_celda(val):
        if pd.isna(val) or val == "" or val == 0:
            return 'background-color: transparent'
        try:
            v = float(val)
            alpha = 0.15 + 0.85 * (v / max_v)
            return f'background-color: rgba(148, 0, 211, {alpha}); color: #ffffff;'
        except:
            return 'background-color: transparent'

    try:
        if hasattr(df.style, 'map'):
            return df.style.map(colorear_celda, subset=cols_numericas)
        else:
            return df.style.applymap(colorear_celda, subset=cols_numericas)
    except:
        return df

# ==============================================================================
# 7. SISTEMA DE RECARGA AUTOMÁTICA
# ==============================================================================
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

elapsed = int(time.time() - st.session_state.last_update)
remaining = max(0, 300 - elapsed)

if remaining <= 0:
    st.session_state.last_update = time.time()
    st.rerun()

# ==============================================================================
# 8. CARGA DE DATOS PRINCIPALES
# ==============================================================================
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQzIFyCT2C22Hlrz80szN7J2mEfA8N1R7hiAmFAUXaoorwDTOeWNh-ktv__d0vIBS-AQcuV5ws3ZU4C/pub?gid=229458966&single=true&output=csv"

@st.cache_data(ttl=300)
def load_full_data():
    try:
        df = pd.read_csv(URL_CSV)
        df.columns = df.columns.str.strip()
        if 'CENTRO' in df.columns:
            df['CENTRO'] = df['CENTRO'].astype(str).str.replace('CONTRA', 'CON', case=False).str.strip()
        col_f = next((c for c in df.columns if 'FECHA' in c.upper()), None)
        if col_f: 
            df['FECHA_DT'] = pd.to_datetime(df[col_f], dayfirst=True, errors='coerce')
            df['MES_NUM'] = df['FECHA_DT'].dt.month
            df['MES_NOMBRE'] = df['FECHA_DT'].dt.strftime('%B').str.upper()
            dias_map = {0: 'LUNES', 1: 'MARTES', 2: 'MIÉRCOLES', 3: 'JUEVES', 4: 'VIERNES', 5: 'SÁBADO', 6: 'DOMINGO'}
            df['DIA_NUM'] = df['FECHA_DT'].dt.dayofweek
            df['DIA_NOMBRE'] = df['DIA_NUM'].map(dias_map)
            df['SEMANA_NUM'] = df['FECHA_DT'].dt.isocalendar().week.astype(str)
            
        col_h = next((c for c in df.columns if 'HORA' in c.upper()), None)
        if col_h: 
            df['HORA_NUM'] = pd.to_datetime(df[col_h], errors='coerce').dt.hour.fillna(0).astype(int)
        
        def to_m_clean(v):
            try:
                if pd.isna(v) or v == "" or v == 0: return 0.0
                p = str(v).split(':')
                minutos = float(int(p[0])*60 + int(p[1])) if len(p) >= 2 else float(v)
                if minutos < 0 or minutos > 720: 
                    return 0.0
                return minutos
            except: return 0.0
            
        for c in ['VARIANZA DE DESPACHO', 'VARIANZA DE LA ATENCION', 'VARIANZA DEL CIERRE', 'VARIANZA DE CIERRE']:
            if c in df.columns: df[c+'_M'] = df[c].apply(to_m_clean)
            
        cols_pos = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
        df['T_POS_COUNT'] = df[cols_pos].notna().sum(axis=1)
        
        def normalizar_texto(texto):
            if not texto or pd.isna(texto): return ""
            texto = str(texto).strip().lower()
            return "".join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))

        map_tactico = {normalizar_texto(k): v for k, v in map_tactico_raw.items()}

        def asignar_grupo(row):
            for col in cols_pos:
                val_raw = str(row[col]).strip() if pd.notna(row[col]) else ""
                if val_raw:
                    val_norm = normalizar_texto(val_raw)
                    if val_norm in map_tactico: return map_tactico[val_norm]
            return "EMERGENCIAS"

        df['RESULTADO_OPERACIONAL'] = df.apply(asignar_grupo, axis=1)
        return df[df['T_POS_COUNT'] > 0].copy()
    except: return None

# ==============================================================================
# 9. DISPOSICIÓN DE LA INTERFAZ DE USUARIO (DASHBOARD)
# ==============================================================================
df_raw = load_full_data()

if df_raw is not None:
    with st.sidebar:
        st.markdown(f"<div class='hud-sub'>{SVG_CLOCK} Rango Temporal</div>", unsafe_allow_html=True)
        f1 = st.date_input("Desde:", df_raw['FECHA_DT'].min().date())
        f2 = st.date_input("Hasta:", df_raw['FECHA_DT'].max().date())
        h1 = st.selectbox("Hora Inicial:", list(range(24)), index=0)
        h2 = st.selectbox("Hora Final:", list(range(24)), index=23)
        
        st.markdown("---")
        st.markdown(f"<div class='hud-sub'>{SVG_GRID} Parámetros de Filtro</div>", unsafe_allow_html=True)
        
        lista_centros = sorted([str(x) for x in df_raw['CENTRO'].dropna().unique() if str(x).strip() != ''])
        lista_canales = sorted([str(x) for x in df_raw.get('CANAL DE ENTRADA', pd.Series([])).dropna().unique() if str(x).strip() != ''])
        lista_grupos = sorted([str(x) for x in df_raw['RESULTADO_OPERACIONAL'].dropna().unique() if str(x).strip() != ''])
        lista_dias = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']
        lista_meses = [str(x) for x in df_raw.get('MES_NOMBRE', pd.Series([])).dropna().unique() if str(x).strip() != '']
        
        f_centros = st.multiselect("1. Por Centro:", lista_centros)
        f_canales = st.multiselect("2. Por Canal:", lista_canales)
        f_grupos = st.multiselect("3. Por Resultado Operacional:", lista_grupos)
        f_dias = st.multiselect("4. Por Día de Semana:", lista_dias)
        f_meses = st.multiselect("5. Por Mes:", lista_meses)
        
        st.plotly_chart(create_gauge(remaining, "ACTUALIZACIÓN", "#00ebff", is_timer=True), use_container_width=True)

    mask = (df_raw['FECHA_DT'].dt.date >= f1) & (df_raw['FECHA_DT'].dt.date <= f2) & \
           (df_raw['HORA_NUM'] >= h1) & (df_raw['HORA_NUM'] <= h2)
           
    if f_centros: mask &= df_raw['CENTRO'].isin(f_centros)
    if f_canales: mask &= df_raw['CANAL DE ENTRADA'].isin(f_canales)
    if f_grupos: mask &= df_raw['RESULTADO_OPERACIONAL'].isin(f_grupos)
    if f_dias: mask &= df_raw['DIA_NOMBRE'].isin(f_dias)
    if f_meses: mask &= df_raw['MES_NOMBRE'].isin(f_meses)

    df = df_raw[mask].copy()

    # ==============================================================================
    # OPCIÓN 1: DASHBOARD OPERATIVO
    # ==============================================================================
    if st.session_state.modo_pantalla == "DASHBOARD OPERATIVO":
        st.markdown(f"""
            <div class="neon-title-container">
                <div class="neon-title-inner">
                    <div style="display:flex; align-items:center; justify-content:center; gap:15px;">
                        {SVG_SHIELD}
                        <h1>Centro de Operación Nacional | Datos Positivos</h1>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('<p class="author-text">DESARROLLADO POR= CABO 1° ELMER RODRIGUEZ</p>', unsafe_allow_html=True)

        c_m1, c_m2 = st.columns(2)
        
        if 'df' in locals() and df is not None and not df.empty:
            total_eventos = len(df)
            total_positivos = int(df["T_POS_COUNT"].sum()) if "T_POS_COUNT" in df.columns else 0
            
            with c_m1:
                st.markdown(f'<div class="neon-container"><div class="neon-inner-content"><h3>{SVG_ACTIVITY} EVENTOS TOTALES</h3><p>{total_eventos:,}</p></div></div>', unsafe_allow_html=True)
                
            with c_m2:
                st.markdown(f'<div class="neon-container"><div class="neon-inner-content"><h3>{SVG_CHECK} TOTAL POSITIVOS</h3><p>{total_positivos:,}</p></div></div>', unsafe_allow_html=True)
        else:
            with c_m1:
                st.markdown(f'<div class="neon-container"><div class="neon-inner-content"><h3>{SVG_ACTIVITY} EVENTOS TOTALES</h3><p>0</p></div></div>', unsafe_allow_html=True)
            with c_m2:
                st.markdown(f'<div class="neon-container"><div class="neon-inner-content"><h3>{SVG_CHECK} TOTAL POSITIVOS</h3><p>0</p></div></div>', unsafe_allow_html=True)

        g1, g2, g3 = st.columns(3)
        v_desp = df['VARIANZA DE DESPACHO_M'].mean() if not df.empty and 'VARIANZA DE DESPACHO_M' in df.columns else 0
        v_aten = df['VARIANZA DE LA ATENCION_M'].mean() if not df.empty and 'VARIANZA DE LA ATENCION_M' in df.columns else 0
        v_c_col = 'VARIANZA DEL CIERRE_M' if 'VARIANZA DEL CIERRE_M' in df.columns else 'VARIANZA DE CIERRE_M'
        v_cier = df[v_c_col].mean() if not df.empty and v_c_col in df.columns else 0
        
        color_desp = obtener_color_alerta(v_desp, 10, 20)
        color_aten = obtener_color_alerta(v_aten, 30, 60)
        color_cier = obtener_color_alerta(v_cier, 60, 120)

        if color_desp == "#ff4b4b" or color_aten == "#ff4b4b":
            st.error("ALERTA OPERATIVA: Los tiempos promedios de Despacho o Atención superan los umbrales críticos de operación.")

        with g1: st.plotly_chart(create_gauge(v_desp, "VARIANZA DESPACHO", color_desp), use_container_width=True)
        with g2: st.plotly_chart(create_gauge(v_aten, "VARIANZA ATENCIÓN", color_aten), use_container_width=True)
        with g3: st.plotly_chart(create_gauge(v_cier, "VARIANZA CIERRE", color_cier), use_container_width=True)

        if not df.empty and v_c_col in df.columns:
            df[v_c_col] = pd.to_numeric(df[v_c_col], errors='coerce').fillna(0)

            r1_df = df[df[v_c_col] <= 15]
            r2_df = df[(df[v_c_col] > 15) & (df[v_c_col] <= 30)]
            r3_df = df[(df[v_c_col] > 30) & (df[v_c_col] <= 60)]
            r4_df = df[df[v_c_col] > 60]

            ev_r1 = len(r1_df)
            ev_r2 = len(r2_df)
            ev_r3 = len(r3_df)
            ev_r4 = len(r4_df)

            df_rangos_barra = pd.DataFrame({
                'Rango': ['0 - 15 Min', '15 - 30 Min', '30 Min - 1 Hora', '1 Hora y Más'],
                'Total': [ev_r1, ev_r2, ev_r3, ev_r4]
            })

            suma_total_rangos = df_rangos_barra['Total'].sum()
            df_rangos_barra['Porcentaje'] = df_rangos_barra['Total'].apply(
                lambda x: (x / suma_total_rangos * 100) if suma_total_rangos > 0 else 0
            )

            colores_dict = {
                '0 - 15 Min': '#00ffaa',
                '15 - 30 Min': '#ffaa00',
                '30 Min - 1 Hora': '#ff7300',
                '1 Hora y Más': '#ff4b4b'
            }

            fig_barra_unica = go.Figure()

            for _, row in df_rangos_barra.iterrows():
                texto_etiqueta = f"<b>{row['Rango']}</b><br>{row['Total']:,} ({row['Porcentaje']:.1f}%)"
                fig_barra_unica.add_trace(go.Bar(
                    x=[row['Total']],
                    y=['Distribución Temporal'],
                    name=row['Rango'],
                    orientation='h',
                    text=texto_etiqueta,
                    textposition='inside',
                    insidetextanchor='middle',
                    marker=dict(color=colores_dict.get(row['Rango'], '#ffffff')),
                    textfont=dict(color='white', size=13, family='sans-serif'),
                    showlegend=False
                ))

            fig_barra_unica.update_layout(
                barmode='stack',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white", size=13),
                xaxis=dict(showgrid=True, gridcolor='rgba(0, 235, 255, 0.15)', title="Total Acumulado de Eventos"),
                yaxis=dict(showgrid=False, title=""),
                height=190,
                margin=dict(t=50, b=20, l=20, r=20)
            )

            st.plotly_chart(fig_barra_unica, use_container_width=True)

        st.markdown(f"<div class='hud-header'>{SVG_MAP_PIN} MAPA TÁCTICO DETALLADO DE INCIDENCIAS</div>", unsafe_allow_html=True)
        if not df.empty and 'PROVINCIA' in df.columns:
            cols_p = [c for c in df.columns if 'RESULTADO POSITIVO' in c.upper()]
            df_long = pd.melt(df, id_vars=['PROVINCIA'], value_vars=cols_p, value_name='Tipo').dropna()
            top_details = df_long.groupby('PROVINCIA').apply(lambda g: "<br>".join([f"• {t}: {v}" for t, v in g['Tipo'].value_counts().nlargest(5).items()])).reset_index(name='DETALLE_TOP')
            prov_stats = df.groupby('PROVINCIA')['T_POS_COUNT'].sum().reset_index().sort_values('T_POS_COUNT', ascending=True)
            prov_stats = prov_stats.merge(top_details, on='PROVINCIA', how='left')
            
            coords = {'Panamá':[8.98,-79.52], 'Chiriquí':[8.43,-82.43], 'Colón':[9.35,-79.9], 'Panamá Oeste':[8.88,-79.78], 'Coclé':[8.51,-80.35], 'Veraguas':[8.1,-80.97], 'Los Santos':[7.93,-80.48], 'Herrera':[7.96,-80.7], 'Darién':[8.4,-77.91], 'Bocas del Toro':[9.33,-82.24], 'Comarca Ngäbe-Buglé':[8.41, -81.75]}
            prov_stats['lat'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[0])
            prov_stats['lon'] = prov_stats['PROVINCIA'].map(lambda x: coords.get(x, [8.5, -80.0])[1])
            
            c_map, c_rank = st.columns([2, 1])
            with c_map:
                st.markdown(f'<div class="map-overlay-total"><small style="color:#00ebff;">TOTAL POSITIVOS</small><br><span style="font-size:24px; font-weight:bold;">{int(df["T_POS_COUNT"].sum()):}</span></div>', unsafe_allow_html=True)
                
                for col in ['lat', 'lon', 'T_POS_COUNT', 'PROVINCIA', 'DETALLE_TOP']:
                    if col not in prov_stats.columns:
                        prov_stats[col] = 0 if col == 'T_POS_COUNT' else ""

                fig_m = px.scatter_mapbox(prov_stats, lat='lat', lon='lon', size='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale="Turbo", size_max=55, zoom=7.2, center=dict(lat=8.5, lon=-80.5), hover_name='PROVINCIA', hover_data={'lat':False, 'lon':False, 'T_POS_COUNT':True, 'DETALLE_TOP':True})
                fig_m.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='rgba(0,0,0,0)', coloraxis_showscale=False)
                st.plotly_chart(fig_m, use_container_width=True)
            with c_rank:
                st.plotly_chart(px.bar(prov_stats, x='T_POS_COUNT', y='PROVINCIA', orientation='h', text='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale='Tealgrn').update_layout(showlegend=False, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=400), use_container_width=True)

            st.markdown("---")
            
            cols_positivos_graf = ['RESULTADO POSITIVO 1', 'RESULTADO POSITIVO 2', 'RESULTADO POSITIVO 3', 
                                   'RESULTADO POSITIVO 4', 'RESULTADO POSITIVO 5', 'RESULTADO POSITIVO 6']
            lista_graf = []
            
            for _, row in df.iterrows():
                for col in cols_positivos_graf:
                    tipo = row[col]
                    if pd.notna(tipo) and str(tipo).strip() not in ['SELECCIONAR', '', 'None']:
                        tipo_limpio = str(tipo).strip()
                        
                        if 'ruido' in tipo_limpio.lower() or 'gases' in tipo_limpio.lower():
                            lista_graf.append({'RESULTADO_OPERACIONAL': 'SEGURIDAD VIAL'})
                            continue
                        
                        encontrado = False
                        for clave_mapeo, grupo in map_tactico_raw.items():
                            if clave_mapeo.lower().strip() in tipo_limpio.lower().strip():
                                lista_graf.append({'RESULTADO_OPERACIONAL': grupo})
                                encontrado = True
                                break
                        if not encontrado:
                            lista_graf.append({'RESULTADO_OPERACIONAL': 'SEGURIDAD VIAL'})

            df_pastel_final = pd.DataFrame(lista_graf)
            if not df_pastel_final.empty:
                df_pastel_final = df_pastel_final[df_pastel_final['RESULTADO_OPERACIONAL'].isin(['SEGURIDAD VIAL', 'CAPTURAS', 'EMERGENCIAS', 'RECUPERACIONES', 'COORDINACIONES'])]
                df_pastel_final = df_pastel_final.groupby('RESULTADO_OPERACIONAL', as_index=False).size()
                df_pastel_final.columns = ['RESULTADO_OPERACIONAL', 'TOTAL']

                cp1, cp2, cp3 = st.columns(3)
                with cp1: 
                    fig_canales = px.pie(df, names='CANAL DE ENTRADA', values='T_POS_COUNT', title="Positivos por Canales", hole=0.5, color_discrete_map={"CLL-104": "#FF1493", "Video Vigilancia": "#FF69B4", "Radio Frecuencia": "#FFB6C1"})
                    fig_canales.update_traces(textinfo='percent+value')
                    st.plotly_chart(fig_canales, use_container_width=True)
                with cp2: 
                    fig_centros = px.pie(df, names='CENTRO', values='T_POS_COUNT', title="Positivos por Centros", hole=0.5, color_discrete_sequence=px.colors.qualitative.Bold)
                    fig_centros.update_traces(textinfo='percent+value')
                    st.plotly_chart(fig_centros, use_container_width=True)
                with cp3: 
                    fig_pastel = px.pie(df_pastel_final, names='RESULTADO_OPERACIONAL', values='TOTAL', 
                                        title="Distribución por Resultado Operacional", hole=0.5, 
                                        color_discrete_sequence=px.colors.qualitative.G10)
                    fig_pastel.update_traces(textinfo='percent+value')
                    st.plotly_chart(fig_pastel, use_container_width=True)
            
        st.markdown(f"<div class='hud-header'>{SVG_GRID} DETALLE: POSITIVOS POR CENTROS</div>", unsafe_allow_html=True)
        if not df.empty:
            df_l_t = pd.melt(df, id_vars=['CENTRO'], value_vars=cols_p, value_name='Tipo').dropna()
            if not df_l_t.empty:
                t_c = df_l_t.groupby(['Tipo', 'CENTRO']).size().unstack(fill_value=0)
                t_c['TOTAL'] = t_c.sum(axis=1)
                ord_c = t_c.drop(columns='TOTAL').sum().sort_values(ascending=False).index.tolist()
                t_c = t_c[ord_c + ['TOTAL']].sort_values('TOTAL', ascending=False)
                df_mostrar = pd.concat([t_c, t_c.sum().to_frame(name='TOTAL GENERAL').T])
                st.dataframe(aplicar_mapa_calor_purpura(df_mostrar), use_container_width=True)

        st.markdown("---")
        st.markdown(f"<div class='hud-header'>{SVG_RADAR} POSITIVOS POR CANAL</div>", unsafe_allow_html=True)
        cols_positivos = ['RESULTADO POSITIVO 1', 'RESULTADO POSITIVO 2', 'RESULTADO POSITIVO 3', 
                          'RESULTADO POSITIVO 4', 'RESULTADO POSITIVO 5', 'RESULTADO POSITIVO 6']
        
        if not df.empty:
            df_m = df.melt(id_vars=['CANAL DE ENTRADA'], value_vars=cols_positivos, value_name='Tipo').dropna()
            df_m = df_m[~df_m['Tipo'].isin(['SELECCIONAR', '', None])]
            
            if not df_m.empty:
                t_canal = df_m.groupby(['Tipo', 'CANAL DE ENTRADA']).size().unstack(fill_value=0)
                t_canal['TOTAL'] = t_canal.sum(axis=1)
                orden_filas = t_canal.drop(columns=['TOTAL']).sum(axis=1).sort_values(ascending=False).index.tolist()
                orden_cols = t_canal.drop(columns=['TOTAL']).sum(axis=0).sort_values(ascending=False).index.tolist()
                t_canal_ordenada = t_canal[orden_cols + ['TOTAL']].loc[orden_filas]
                fila_total = t_canal_ordenada.sum().to_frame(name='TOTAL GENERAL').T
                tabla_final = pd.concat([t_canal_ordenada, fila_total])
                st.dataframe(aplicar_mapa_calor_purpura(tabla_final), use_container_width=True, height=400)
        st.markdown("---")

        st.markdown(f"<div class='hud-header'>{SVG_SHIELD} POSITIVOS POR RESULTADO OPERACIONAL</div>", unsafe_allow_html=True)

        def limpiar_texto(texto):
            if isinstance(texto, str):
                return texto.strip()
            return str(texto)

        mapeo_grupos = map_tactico_raw
        lista_final = []

        if not df.empty:
            for _, row in df.iterrows():
                centro_actual = row.get('CENTRO', 'N/A')
                for col in cols_positivos:
                    tipo = row.get(col)
                    if pd.notna(tipo) and str(tipo).strip() not in ['SELECCIONAR', '', 'None']:
                        tipo_limpio = limpiar_texto(tipo)
                        
                        if 'ruido' in tipo_limpio.lower() or 'gases' in tipo_limpio.lower():
                            lista_final.append({'Tipo': tipo, 'RESULTADO_OPERACIONAL': 'SEGURIDAD VIAL', 'CENTRO': centro_actual})
                            continue

                        encontrado = False
                        for clave_mapeo, grupo in mapeo_grupos.items():
                            if clave_mapeo.lower().strip() == tipo_limpio.lower().strip():
                                lista_final.append({'Tipo': tipo, 'RESULTADO_OPERACIONAL': grupo, 'CENTRO': centro_actual})
                                encontrado = True
                                break
                        
                        if not encontrado:
                            lista_final.append({'Tipo': tipo, 'RESULTADO_OPERACIONAL': 'SEGURIDAD VIAL', 'CENTRO': centro_actual})

            df_mapeado = pd.DataFrame(lista_final)

            if not df_mapeado.empty:
                tabla = pd.crosstab(df_mapeado['Tipo'], df_mapeado['RESULTADO_OPERACIONAL'])
                lista_orden = ['SEGURIDAD VIAL', 'CAPTURAS', 'EMERGENCIAS', 'RECUPERACIONES', 'COORDINACIONES']
                
                for col in lista_orden:
                    if col not in tabla.columns:
                        tabla[col] = 0
                        
                tabla = tabla[lista_orden]
                tabla['TOTAL'] = tabla.sum(axis=1)
                tabla = tabla.sort_values(by='TOTAL', ascending=False)
                fila_total = tabla.sum().to_frame(name='TOTAL GENERAL').T
                tabla_final = pd.concat([fila_total, tabla])
                
                st.dataframe(aplicar_mapa_calor_purpura(tabla_final), use_container_width=True, height=400)
                
                st.write("**Desglose de Resultado Operacional por Centro:**")
                tabla_gc = pd.crosstab(df_mapeado['RESULTADO_OPERACIONAL'], df_mapeado['CENTRO'])
                
                filas_existentes = [g for g in lista_orden if g in tabla_gc.index]
                otras_filas = [g for g in tabla_gc.index if g not in filas_existentes]
                tabla_gc = tabla_gc.reindex(filas_existentes + otras_filas)
                
                tabla_gc['TOTAL'] = tabla_gc.sum(axis=1)
                fila_total_gc = tabla_gc.sum().to_frame(name='TOTAL GENERAL').T
                tabla_final_gc = pd.concat([fila_total_gc, tabla_gc])
                
                st.dataframe(aplicar_mapa_calor_purpura(tabla_final_gc), use_container_width=True)

            else:
                st.info("No hay datos de positivos para mostrar en el período seleccionado.")
                                    
        cn1, cn2 = st.columns(2)
        with cn1:
            st.markdown(f"<div class='hud-header'>{SVG_ACTIVITY} CIERRE DEL INCIDENTE-SUBTIPO</div>", unsafe_allow_html=True)
            col_c = next((c for c in df.columns if 'CIERRE' in c.upper() and 'SUBTIPO' in c.upper()), None)
            if col_c and not df.empty:
                t_sb = df.groupby([col_c, 'CENTRO']).size().unstack(fill_value=0)
                t_sb['TOTAL'] = t_sb.sum(axis=1)
                ord_centros_cierre = t_sb.drop(columns='TOTAL').sum().sort_values(ascending=False).index.tolist()
                t_sb = t_sb[ord_centros_cierre + ['TOTAL']].sort_values('TOTAL', ascending=False)
                df_mostrar = pd.concat([t_sb, t_sb.sum().to_frame(name='TOTAL GENERAL').T])
                st.dataframe(aplicar_mapa_calor_purpura(df_mostrar), use_container_width=True, height=400)
        with cn2:
            st.markdown(f"<div class='hud-header'>{SVG_SHIELD} ZONA POLICIAL O ENLACE</div>", unsafe_allow_html=True)
            col_zp = next((c for c in df.columns if any(k in c.upper() for k in ['ZONA', 'ZP', 'SERVICIO'])), None)
            if col_zp and not df.empty:
                zp_s = df.groupby(col_zp)['T_POS_COUNT'].sum().reset_index().sort_values('T_POS_COUNT', ascending=False)
                df_mostrar = pd.concat([zp_s, pd.DataFrame({col_zp:['TOTAL GENERAL'], 'T_POS_COUNT':[zp_s['T_POS_COUNT'].sum()]})], ignore_index=True)
                st.dataframe(aplicar_mapa_calor_purpura(df_mostrar), use_container_width=True, height=400, hide_index=True)

        st.markdown("---")
        st.markdown(f"<div class='hud-header'>{SVG_SIGNAL} TENDENCIAS Y HORAS PICO</div>", unsafe_allow_html=True)
        if not df.empty and 'HORA_NUM' in df.columns:
            tendencia_hora = df.groupby('HORA_NUM')['T_POS_COUNT'].sum().reset_index()
            todas_las_horas = pd.DataFrame({'HORA_NUM': range(24)})
            tendencia_hora = todas_las_horas.merge(tendencia_hora, on='HORA_NUM', how='left').fillna(0)
            
            fig_hora = px.line(tendencia_hora, x='HORA_NUM', y='T_POS_COUNT', markers=True,
                               labels={'HORA_NUM': 'Hora del Día (Formato 24h)', 'T_POS_COUNT': 'Total de Incidencias'})
            fig_hora.update_traces(line_color="#00ebff", marker=dict(size=8, color="#ffaa00"), line=dict(width=3))
            fig_hora.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"),
                                   xaxis=dict(tickmode='linear', dtick=1))
            st.plotly_chart(fig_hora, use_container_width=True)

        st.markdown("---")
        st.markdown(f"<div class='hud-header'>{SVG_GRID} ANÁLISIS POR UNIDAD Y TIEMPO</div>", unsafe_allow_html=True)
        c_mes, c_vv, c_desp = st.columns(3)
        with c_mes:
            if 'MES_NOMBRE' in df.columns and not df.empty:
                st.markdown(f"<div class='hud-sub'>{SVG_CLOCK} Positivos por Meses</div>", unsafe_allow_html=True)
                m_s = df.groupby(['MES_NOMBRE', 'MES_NUM'])['T_POS_COUNT'].sum().reset_index().sort_values('MES_NUM', ascending=False)
                fig_m_b = px.bar(m_s, x='T_POS_COUNT', y='MES_NOMBRE', orientation='h', text='T_POS_COUNT', color='T_POS_COUNT', color_continuous_scale='Tealgrn')
                fig_m_b.update_layout(showlegend=False, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), height=400)
                st.plotly_chart(fig_m_b, use_container_width=True)
        with c_vv:
            col_vv = next((c for c in df.columns if 'UNIDAD DE VV' in c.upper() or 'VV/104' in c.upper()), None)
            if col_vv and not df.empty:
                st.markdown(f"<div class='hud-sub'>{SVG_RADAR} Unidad de VV/104</div>", unsafe_allow_html=True)
                df[col_vv] = df[col_vv].fillna("SIN ASIGNAR").astype(str)
                vv_s = df.groupby([col_vv, 'CENTRO']).size().reset_index(name='E').sort_values('E', ascending=False)
                df_mostrar = pd.concat([vv_s, pd.DataFrame({col_vv:['TOTAL GENERAL'], 'CENTRO':['-'], 'E':[vv_s['E'].sum()]})], ignore_index=True)
                st.dataframe(aplicar_mapa_calor_purpura(df_mostrar), use_container_width=True, hide_index=True)
        with c_desp:
            col_dp = next((c for c in df.columns if 'UNIDAD DE DESPACHO' in c.upper()), None)
            if col_dp and not df.empty:
                st.markdown(f"<div class='hud-sub'>{SVG_SIGNAL} Unidad de Despacho</div>", unsafe_allow_html=True)
                df[col_dp] = df[col_dp].fillna("SIN ASIGNAR").astype(str)
                dp_s = df.groupby([col_dp, 'CENTRO']).size().reset_index(name='E').sort_values('E', ascending=False)
                df_mostrar = pd.concat([dp_s, pd.DataFrame({col_dp:['TOTAL GENERAL'], 'CENTRO':['-'], 'E':[dp_s['E'].sum()]})], ignore_index=True)
                st.dataframe(aplicar_mapa_calor_purpura(df_mostrar), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown(f"<div class='hud-header'>{SVG_TARGET} ARMAS DE FUEGO Y MUNICIONES</div>", unsafe_allow_html=True)
        
        armas_oficiales = []
        if not df.empty:
            for _, row in df.iterrows():
                for col in cols_positivos: 
                    val = str(row.get(col, '')).strip()
                    if 'Arma de Fuego' in val:
                        if 'Ciudadano Aprehendido' not in val:
                            tipo = val.split('-')[-1].strip().upper() if '-' in val else val.upper()
                            armas_oficiales.append({'Tipo de Arma': tipo, 'CENTRO': row.get('CENTRO', 'N/A')})
                        
        df_armas_oficiales = pd.DataFrame(armas_oficiales)
        
        muni_data = []
        col_narrativo = next((c for c in df.columns if 'NARRATIV' in c.upper() or 'DETALLE' in c.upper() or 'HECHO' in c.upper() or 'RESUMEN' in c.upper()), None)
        
        if col_narrativo and not df.empty:
            for _, row in df.iterrows():
                text_lower = str(row.get(col_narrativo, '')).lower()
                centro = str(row.get('CENTRO', 'N/A')).strip()
                
                patrones = [
                    r'\b(\d{1,4})\s*(?:municion|municiones|bala|balas|cartucho|cartuchos|casquillo|casquillos)\b',
                    r'\b(?:municion|municiones|bala|balas|cartucho|cartuchos|casquillo|casquillos)\b\s*(?:son|fueron|:|: |-|de)?\s*(\d{1,4})\b'
                ]
                
                total_muni_narrativa = 0
                for pat in patrones:
                    matches = re.findall(pat, text_lower)
                    total_muni_narrativa += sum(int(m) for m in matches)
                    
                if total_muni_narrativa > 0:
                    if '9' in text_lower and 'mm' in text_lower or '9mm' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '9MM', 'Cantidad': total_muni_narrativa})
                    elif '380' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '.380', 'Cantidad': total_muni_narrativa})
                    elif '38' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '.38', 'Cantidad': total_muni_narrativa})
                    elif '45' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '.45', 'Cantidad': total_muni_narrativa})
                    elif '22' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '.22', 'Cantidad': total_muni_narrativa})
                    elif '12' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '12 (ESCOPETA)', 'Cantidad': total_muni_narrativa})
                    elif '5.56' in text_lower or '223' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '5.56 / .223', 'Cantidad': total_muni_narrativa})
                    elif '.40' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '.40', 'Cantidad': total_muni_narrativa})
                    elif '.25' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '.25', 'Cantidad': total_muni_narrativa})
                    elif '5.7x28' in text_lower:
                        muni_data.append({'CENTRO': centro, 'Calibre': '5.7x28', 'Cantidad': total_muni_narrativa})
                    else:
                        muni_data.append({'CENTRO': centro, 'Calibre': 'OTROS', 'Cantidad': total_muni_narrativa})

        df_municiones = pd.DataFrame(muni_data)

        c_armas, c_muni = st.columns(2)
        
        with c_armas:
            st.markdown(f"<div class='hud-sub'>{SVG_GUN} ARMAS DE FUEGO</div>", unsafe_allow_html=True)
            if not df_armas_oficiales.empty:
                st.write("**Desglose de Armas por Centro:**")
                tabla_armas = pd.crosstab(df_armas_oficiales['Tipo de Arma'], df_armas_oficiales['CENTRO'])
                tabla_armas['TOTAL'] = tabla_armas.sum(axis=1)
                tabla_armas = tabla_armas.sort_values('TOTAL', ascending=False)
                tabla_armas.loc['TOTAL GENERAL'] = tabla_armas.sum()
                st.dataframe(aplicar_mapa_calor_purpura(tabla_armas), use_container_width=True)
            else:
                st.info("No se registraron Armas de Fuego en los resultados positivos del período filtrado.")

        with c_muni:
            st.markdown(f"<div class='hud-sub'>{SVG_TARGET} MUNICIONES</div>", unsafe_allow_html=True)
            if not df_municiones.empty:
                st.write("**Desglose de Municiones por Centro:**")
                tabla_muni = df_municiones.groupby(['Calibre', 'CENTRO'])['Cantidad'].sum().unstack(fill_value=0)
                tabla_muni['TOTAL'] = tabla_muni.sum(axis=1)
                tabla_muni = tabla_muni.sort_values('TOTAL', ascending=False)
                tabla_muni.loc['TOTAL GENERAL'] = tabla_muni.sum()
                st.dataframe(aplicar_mapa_calor_purpura(tabla_muni), use_container_width=True)
            else:
                st.info("No se encontraron cantidades de municiones descritas en los narrativos del período filtrado.")

        st.markdown("---")
        st.markdown(f"<div class='hud-header'>{SVG_CLOCK} TOTAL DE INCIDENTES POR DÍA DE LA SEMANA</div>", unsafe_allow_html=True)
        
        if not df.empty and 'FECHA_DT' in df.columns:
            dias_map = {0: 'LUNES', 1: 'MARTES', 2: 'MIÉRCOLES', 3: 'JUEVES', 4: 'VIERNES', 5: 'SÁBADO', 6: 'DOMINGO'}
            orden_dias = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']
            
            df_dias = df.copy()
            df_dias['DIA_NUM'] = df_dias['FECHA_DT'].dt.dayofweek
            df_dias['DIA_NOMBRE'] = df_dias['DIA_NUM'].map(dias_map)
            df_dias = df_dias.dropna(subset=['DIA_NOMBRE'])

            if not df_dias.empty:
                # Conteo directo de eventos (filas únicas)
                resumen_dias = df_dias.groupby(['DIA_NUM', 'DIA_NOMBRE']).size().reset_index(name='TOTAL_EVENTOS')
                resumen_dias = resumen_dias.sort_values('DIA_NUM', ascending=False)
                
                c_graf, c_tab = st.columns([1, 1.5])
                
                with c_graf:
                    fig_dias = px.bar(
                        resumen_dias, 
                        x='TOTAL_EVENTOS', 
                        y='DIA_NOMBRE', 
                        orientation='h', 
                        text='TOTAL_EVENTOS',
                        labels={'DIA_NOMBRE': 'Día de la Semana', 'TOTAL_EVENTOS': 'Total de Eventos'},
                        color='TOTAL_EVENTOS', 
                        color_continuous_scale='Tealgrn', 
                        title="Eventos por Día de la Semana"
                    )
                    fig_dias.update_layout(
                        yaxis={'categoryorder': 'array', 'categoryarray': list(reversed(orden_dias))},
                        showlegend=False, 
                        coloraxis_showscale=False, 
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)', 
                        font=dict(color="white"), 
                        height=450
                    )
                    st.plotly_chart(fig_dias, use_container_width=True)
                    
                with c_tab:
                    st.write("**Desglose de Eventos por Centro:**")
                    tabla_cruzada = pd.crosstab(df_dias['DIA_NOMBRE'], df_dias['CENTRO'])
                    tabla_cruzada = tabla_cruzada.reindex(orden_dias).fillna(0).astype(int)
                    tabla_cruzada['TOTAL'] = tabla_cruzada.sum(axis=1)
                    tabla_cruzada.loc['TOTAL GENERAL'] = tabla_cruzada.sum()
                    tabla_cruzada = pd.concat([tabla_cruzada.loc[['TOTAL GENERAL']], tabla_cruzada.drop('TOTAL GENERAL')])
                    st.dataframe(aplicar_mapa_calor_purpura(tabla_cruzada), use_container_width=True)
            else:
                st.info("No hay fechas válidas para contabilizar eventos en este rango.")
        else:
            st.info("No se encontró la columna de Fechas para realizar este análisis.")

        st.markdown("---")
        st.markdown(f"<div class='hud-header'>{SVG_FILE} DESGLOSE DE OFICIOS (CAPTURA Y CONDUCCIÓN) SEGÚN NARRATIVA</div>", unsafe_allow_html=True)

        capturas_data = []
        conducciones_data = []

        if col_narrativo and not df.empty:
            delitos_keywords = {
                'CONTRA LA VIDA E INTEGRIDAD (HOMICIDIO/LESIONES)': ['homicidio', 'asesinato', 'tentativa', 'lesiones', 'agresion', 'agresión', 'vida e integridad', 'femicidio', 'feminicidio'],
                'CONTRA EL PATRIMONIO (ROBO/HURTO)': ['robo', 'hurto', 'patrimonio economico', 'patrimonio económico', 'extorsion', 'extorsión'],
                'DELITOS SEXUALES (VIOLACIÓN)': ['violacion', 'violación', 'abuso sexual', 'delitos sexuales', 'estupro', 'libertad sexual', 'acto libidinoso', 'violacion carnal', 'acoso'],
                'DROGAS / NARCOTRÁFICO': ['droga', 'drogas', 'sustancias ilicitas', 'sustancias ilícitas', 'narcotrafico', 'narcotráfico', 'microtrafico', 'posesion agravada de drogas', 'venta de drogas'],
                'VIOLENCIA DOMÉSTICA': ['violencia domestica', 'violencia doméstica', 'violencia intrafamiliar', 'orden familiar', 'maltrato'],
                'ESTAFA / DELITOS FINANCIEROS': ['estafa', 'fraude', 'orden economico', 'orden económico', 'blanqueo', 'falsificacion', 'falsificación', 'cheque', 'tarjeta'],
                'PANDILLERISMO / ASOCIACIÓN ILÍCITA': ['pandillerismo', 'asociacion ilicita', 'asociación ilícita', 'pandilla'],
                'PENSIÓN ALIMENTICIA / DESACATO': ['pension alimenticia', 'pensión alimenticia', 'desacato', 'juez de paz', 'alimentos', 'pension'],
                'PORTE ILEGAL DE ARMAS': ['arma de fuego', 'posesion ilicita de arma', 'porte ilegal', 'seguridad colectiva', 'armas', 'municiones']
            }

            df_oficios_melt = df.melt(id_vars=['CENTRO', col_narrativo], value_vars=cols_positivos, value_name='Tipo').dropna()
            df_oficios_melt = df_oficios_melt[~df_oficios_melt['Tipo'].astype(str).str.strip().isin(['SELECCIONAR', '', 'None', 'nan'])]

            for _, row in df_oficios_melt.iterrows():
                centro = str(row.get('CENTRO', 'N/A')).strip()
                tipo_oficial = str(row.get('Tipo', '')).lower()
                text_lower = str(row.get(col_narrativo, '')).lower()
                
                es_captura = 'oficio de captura' in tipo_oficial
                es_conduccion = 'oficio de conducci' in tipo_oficial
                
                if es_captura or es_conduccion:
                    tipo_delito = 'OTRO / NO ESPECIFICADO'
                    for delito, keywords in delitos_keywords.items():
                        if any(kw in text_lower for kw in keywords):
                            tipo_delito = delito
                            break
                            
                    if es_conduccion:
                        conducciones_data.append({'CENTRO': centro, 'Delito': tipo_delito})
                    elif es_captura:
                        capturas_data.append({'CENTRO': centro, 'Delito': tipo_delito})

        df_conducciones = pd.DataFrame(conducciones_data)
        df_capturas = pd.DataFrame(capturas_data)

        st.markdown(f"<div class='hud-sub'>{SVG_FILE} OFICIOS DE CONDUCCIÓN</div>", unsafe_allow_html=True)
        if not df_conducciones.empty:
            tabla_cond = pd.crosstab(df_conducciones['Delito'], df_conducciones['CENTRO'])
            tabla_cond['TOTAL'] = tabla_cond.sum(axis=1)
            tabla_cond = tabla_cond.sort_values('TOTAL', ascending=False)
            fila_total = tabla_cond.sum().to_frame(name='TOTAL GENERAL').T
            tabla_cond = pd.concat([fila_total, tabla_cond])
            st.dataframe(aplicar_mapa_calor_purpura(tabla_cond), use_container_width=True)
        else:
            st.info("No se encontraron registros de Oficios de Conducción en el período filtrado.")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"<div class='hud-sub'>{SVG_ALERT} OFICIOS DE CAPTURA</div>", unsafe_allow_html=True)
        if not df_capturas.empty:
            tabla_capt = pd.crosstab(df_capturas['Delito'], df_capturas['CENTRO'])
            tabla_capt['TOTAL'] = tabla_capt.sum(axis=1)
            tabla_capt = tabla_capt.sort_values('TOTAL', ascending=False)
            fila_total = tabla_capt.sum().to_frame(name='TOTAL GENERAL').T
            tabla_capt = pd.concat([fila_total, tabla_capt])
            st.dataframe(aplicar_mapa_calor_purpura(tabla_capt), use_container_width=True)
        else:
            st.info("No se encontraron registros de Oficios de Captura en el período filtrado.")

   # ==============================================================================
    # OPCIÓN 2: PRESENTACIÓN EJECUTIVA TÁCTICA
    # ==============================================================================
    elif st.session_state.modo_pantalla == "PRESENTACION_EJECUTIVA":
        st.markdown(
            f"<h1 style='color: #00d4ff; text-shadow: 0 0 12px #00d4ff; text-align: center;'>{SVG_SIGNAL} PRESENTACIÓN EJECUTIVA TÁCTICA</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #ffffff; font-size: 16px;'>Desglose Operacional por Centro y Resultados Operacionales (Modo Alto Contraste)</p>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='border: 1px solid #00d4ff;'>", unsafe_allow_html=True)

        if df.empty:
            st.info("No hay datos para mostrar en esta presentación con los filtros actuales.")
        else:
            # Función local para evitar NameError
            def normalizar_texto(t):
                if not t or pd.isna(t): return ""
                t = str(t).strip().lower()
                return "".join(c for c in unicodedata.normalize('NFKD', t) if not unicodedata.combining(c))

            cols_positivos = ['RESULTADO POSITIVO 1', 'RESULTADO POSITIVO 2', 'RESULTADO POSITIVO 3', 
                              'RESULTADO POSITIVO 4', 'RESULTADO POSITIVO 5', 'RESULTADO POSITIVO 6']
            col_narrativo = next((c for c in df.columns if 'NARRATIV' in c.upper() or 'DETALLE' in c.upper() or 'HECHO' in c.upper() or 'RESUMEN' in c.upper()), None)
            
            map_tactico_norm = {normalizar_texto(k): v for k, v in map_tactico_raw.items()}
            lista_final_ejecutiva = []
            
            for _, row in df.iterrows():
                centro_actual = str(row.get('CENTRO', 'N/A')).strip()
                for col in cols_positivos:
                    tipo = row.get(col)
                    if pd.notna(tipo) and str(tipo).strip() not in ['SELECCIONAR', '', 'None']:
                        tipo_limpio = str(tipo).strip()
                        tipo_norm = normalizar_texto(tipo_limpio)
                        
                        if 'ruido' in tipo_norm or 'gases' in tipo_norm:
                            grupo = 'SEGURIDAD VIAL'
                        else:
                            grupo = map_tactico_norm.get(tipo_norm, 'SEGURIDAD VIAL')
                            
                        lista_final_ejecutiva.append({
                            'Tipo': tipo_limpio,
                            'Tipo_Norm': tipo_norm,
                            'RESULTADO_OPERACIONAL': grupo,
                            'CENTRO': centro_actual
                        })
                            
            df_ejecutivo = pd.DataFrame(lista_final_ejecutiva)

            if not df_ejecutivo.empty:
                centros_unicos = df_ejecutivo['CENTRO'].value_counts().index.tolist()
                todas_las_tarjetas_html = "" 
                
                # Los 2 únicos tipos oficiales de orden judicial
                oficios_dos_tipos = [
                    'ciudadano aprehendido por oficio de captura',
                    'ciudadano aprehendido por oficio de conduccion'
                ]
                
                for i in range(0, len(centros_unicos), 2):
                    col1, col2 = st.columns(2)
                    centros_par = centros_unicos[i:i+2]
                    
                    for idx, centro_card in enumerate(centros_par):
                        with (col1 if idx == 0 else col2):
                            df_c = df_ejecutivo[df_ejecutivo['CENTRO'] == centro_card]
                            df_raw_c = df[df['CENTRO'] == centro_card]
                            conteo_grupos = df_c['RESULTADO_OPERACIONAL'].value_counts()
                            total_centro = int(len(df_c))
                            
                            # CÁLCULO ESTRICTO: OFICIOS (SOLO LOS 2 TIPOS) vs FLAGRANCIA (RESTO DE CAPTURAS)
                            total_capturas_centro = int(conteo_grupos.get('CAPTURAS', 0))
                            df_capturas_c = df_c[df_c['RESULTADO_OPERACIONAL'] == 'CAPTURAS']
                            
                            es_oficio = df_capturas_c['Tipo_Norm'].isin(oficios_dos_tipos)
                            oficios_count = int(es_oficio.sum())
                            aprehensiones_count = total_capturas_centro - oficios_count  # Flagrancia absorbe el resto exacto
                            
                            # Métricas complementarias del Panel Operacional
                            cond_armas = df_c['Tipo_Norm'].apply(lambda x: 'arma de fuego' in x and 'aprehendido' not in x)
                            cond_vehic = df_c['Tipo_Norm'].apply(lambda x: 'vehiculo recuperado' in x)
                            cond_drogas = df_c['Tipo_Norm'].apply(lambda x: 'sustancia' in x or 'droga' in x)

                            armas_count = int(cond_armas.sum())
                            vehiculos_count = int(cond_vehic.sum())
                            drogas_count = int(cond_drogas.sum())

                            # Conteo de municiones desde narrativa
                            total_muni_centro = 0
                            if col_narrativo:
                                patrones = [
                                    r'\b(\d{1,4})\s*(?:municion|municiones|bala|balas|cartucho|cartuchos|casquillo|casquillos)\b',
                                    r'\b(?:municion|municiones|bala|balas|cartucho|cartuchos|casquillo|casquillos)\b\s*(?:son|fueron|:|: |-|de)?\s*(\d{1,4})\b'
                                ]
                                for _, r_data in df_raw_c.iterrows():
                                    text_lower = str(r_data.get(col_narrativo, '')).lower()
                                    for pat in patrones:
                                        matches = re.findall(pat, text_lower)
                                        total_muni_centro += sum(int(m) for m in matches)

                            centro_safe = html.escape(str(centro_card))
                            html_card = f"<div class='notranslate' translate='no' style='background: rgba(5, 10, 20, 0.95); border: 2px solid #00a8ff; border-radius: 12px; padding: 20px; margin-bottom: 25px; box-shadow: 0 0 15px rgba(0, 168, 255, 0.3);'>"
                            
                            html_card += "<div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0, 168, 255, 0.5); padding-bottom: 15px; margin-bottom: 15px;'>"
                            html_card += "<div style='display: flex; align-items: center; gap: 10px;'>"
                            html_card += f"<span>{SVG_MAP_PIN}</span>"
                            html_card += f"<h2 style='color: #00a8ff; margin: 0; font-size: 24px; text-transform: uppercase; letter-spacing: 2px;'>{centro_safe}</h2>"
                            html_card += "</div>"
                            html_card += "<div style='background: rgba(0, 168, 255, 0.15); border: 1px solid #00a8ff; padding: 5px 20px; border-radius: 25px; box-shadow: 0 0 10px rgba(0, 168, 255, 0.4);'>"
                            html_card += "<span style='color: #e0e0e0; font-size: 14px; font-weight: bold; margin-right: 8px;'>TOTAL:</span>"
                            html_card += f"<span style='color: #ffffff; font-size: 24px; font-weight: 900; text-shadow: 0 0 10px #ffffff;'>{total_centro}</span>"
                            html_card += "</div>"
                            html_card += "</div>"
                            
                            html_card += "<div style='display: flex; flex-wrap: wrap; justify-content: space-between; gap: 15px; margin-top: 10px;'>"
                            
                            svg_iconos = {
                                'CAPTURAS': ILLUST_FLAGRANCIA,
                                'RECUPERACIONES': ILLUST_ARMAS,
                                'SEGURIDAD VIAL': ILLUST_VEHICULOS,
                                'COORDINACIONES': ILLUST_COORDINACIONES,
                                'EMERGENCIAS': '<svg viewBox="0 0 24 24" width="45" height="45" fill="#00a8ff" style="filter: drop-shadow(0 0 8px #00a8ff);"><path d="M19 3H5c-1.1 0-1.99.9-1.99 2L3 19c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 11h-4v4h-4v-4H6v-4h4V6h4v4h4v4z"/></svg>'
                            }

                            for grupo_nombre, cantidad in conteo_grupos.items():
                                icono_svg = svg_iconos.get(grupo_nombre, SVG_SHIELD)
                                g_safe = html.escape(str(grupo_nombre))
                                html_card += "<div style='width: calc(50% - 8px); background: linear-gradient(135deg, rgba(0, 168, 255, 0.15) 0%, rgba(0,0,0,0.5) 100%); border: 1px solid #00a8ff; border-radius: 6px; padding: 15px; position: relative; overflow: hidden;'>"
                                html_card += "<div style='position: absolute; top: 0; left: 0; width: 20px; height: 2px; background: #ffffff;'></div>"
                                html_card += "<div style='position: absolute; top: 0; left: 0; width: 2px; height: 20px; background: #ffffff;'></div>"
                                html_card += "<div style='position: absolute; bottom: 0; right: 0; width: 20px; height: 2px; background: #ffffff;'></div>"
                                html_card += "<div style='position: absolute; bottom: 0; right: 0; width: 2px; height: 20px; background: #ffffff;'></div>"
                                html_card += "<div style='display: flex; justify-content: space-between; align-items: center;'>"
                                html_card += "<div style='text-align: left;'>"
                                html_card += f"<div style='color: #ffffff; font-size: 14px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase;'>{g_safe}</div>"
                                html_card += f"<div style='color: #ffffff; font-size: 38px; font-weight: 900; text-shadow: 0 0 15px rgba(255,255,255,0.5); line-height: 1.1;'>{cantidad}</div>"
                                html_card += "</div>"
                                html_card += f"<div style='width:65px; height:65px; display:flex; align-items:center; justify-content:center;'>{icono_svg}</div>"
                                html_card += "</div></div>"
                            html_card += "</div>"

                            html_card += "<div style='margin-top: 25px; border: 1px solid #00a8ff; background: rgba(0, 0, 0, 0.4); border-radius: 6px; padding: 20px 15px 15px 15px; position: relative;'>"
                            html_card += "<div style='position: absolute; top: -12px; left: 20px; background: #040d1a; padding: 0 15px; border: 1px solid #00a8ff; border-radius: 4px; color: #ffffff; font-size: 13px; font-weight: bold; letter-spacing: 1px; display: flex; align-items: center; gap: 8px;'><div style='width: 8px; height: 8px; background: #00a8ff; border-radius: 50%; box-shadow: 0 0 8px #00a8ff;'></div>PANEL DE SEGURIDAD OPERACIONAL</div>"
                            
                            mini_items = [
                                ("A. FLAGRANCIA", aprehensiones_count, ILLUST_FLAGRANCIA),
                                ("A. OFICIO", oficios_count, ILLUST_OFICIO),
                                ("ARMAS RECUPERADAS", armas_count, ILLUST_ARMAS),
                                ("DROGAS INCAUTADAS", drogas_count, ILLUST_DROGAS),
                                ("MUNICIONES INCAUTADAS", total_muni_centro, ILLUST_MUNICIONES),
                                ("VEHÍCULOS RECUPERADOS", vehiculos_count, ILLUST_VEHICULOS)
                            ]
                            
                            html_card += "<div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;'>"
                            for m_tit, m_val, m_svg in mini_items:
                                html_card += f"<div style='border: 1.5px solid #00d4ff; background: linear-gradient(180deg, rgba(6,22,42,0.9) 0%, rgba(3,10,22,0.95) 100%); border-radius: 8px; padding: 8px 10px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 0 10px rgba(0,212,255,0.25);'>"
                                html_card += f"<div><div style='color:#a0d8ef; font-size:9px; font-weight:800; margin-bottom:3px;'>{m_tit}</div><div style='color:#ffffff; font-size:20px; font-weight:900; text-shadow:0 0 8px #00ebff; line-height:1;'>{m_val:,}</div></div>"
                                html_card += f"<div style='width:48px; height:48px; display:flex; align-items:center; justify-content:center;'>{m_svg}</div>"
                                html_card += "</div>"
                            
                            html_card += "</div>"
                            html_card += "</div>"
                            html_card += "</div>"
                            
                            st.markdown(html_card, unsafe_allow_html=True)
                            todas_las_tarjetas_html += html_card

                st.markdown("<hr style='border: 1px solid rgba(0, 212, 255, 0.3); margin-top: 30px;'>", unsafe_allow_html=True)
                
                html_completo = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Reporte Táctico C.O.N.</title>"
                html_completo += "<style>body { background-color: #040d1a; color: white; font-family: Arial, sans-serif; padding: 20px; }</style></head><body>"
                html_completo += "<h1 style='color: #00d4ff; text-align: center; margin-bottom: 40px; font-family: sans-serif; letter-spacing: 2px;'>REPORTE TÁCTICO - CENTRO DE OPERACIÓN NACIONAL</h1>"
                html_completo += "<div style='display: flex; flex-direction: column; gap: 40px; max-width: 1200px; margin: 0 auto;'>"
                html_completo += todas_las_tarjetas_html
                html_completo += "</div></body></html>"
                
                b64 = base64.b64encode(html_completo.encode('utf-8')).decode()
                href = '<a href="data:text/html;base64,' + b64 + '" download="reporte_tactico_con.html" style="background-color: #00a8ff; color: #040d1a; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block; margin-top: 10px; font-family: sans-serif; letter-spacing: 1px; box-shadow: 0 0 15px rgba(0, 168, 255, 0.4);">[ DESCARGAR REPORTE TÁCTICO HTML ]</a>'
                
                col_btn_1, col_btn_2, col_btn_3 = st.columns([1,2,1])
                with col_btn_2:
                    st.markdown("<div style='text-align: center;'>" + href + "</div>", unsafe_allow_html=True)
                    st.markdown("<p style='text-align: center; font-size: 11px; color: #888; margin-top: 10px;'>El archivo descargado se puede abrir en cualquier navegador web y guardarlo como PDF usando la opción de Imprimir (Ctrl+P).</p>", unsafe_allow_html=True)


    # ==============================================================================
    # OPCIÓN 3: PRESENTACION MANDO POLICIAL
    # ==============================================================================
    elif st.session_state.modo_pantalla == "PRESENTACION_MANDO_POLICIAL":
        st.markdown(
            f"<h1 style='color: #00ebff; text-shadow: 0 0 15px rgba(0,235,255,0.7); text-align: center; letter-spacing: 2px; font-family: sans-serif;'>{SVG_SHIELD} CENTRO DE OPERACIÓN NACIONAL | RESUMEN OPERACIONAL</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #a0d8ef; font-size: 16px; font-family: monospace;'>[ SISTEMA DE MONITOREO OPERACIONAL - VISTA MANDO POLICIAL ]</p>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='border: 1px solid #00ebff; box-shadow: 0 0 12px #00ebff;'>", unsafe_allow_html=True)

        st.markdown(f"<h3 style='color: #00ebff; border-left: 4px solid #00ebff; padding-left: 10px; font-family: monospace;'>{SVG_ACTIVITY} RESUMEN OPERATIVO GLOBAL</h3>", unsafe_allow_html=True)
        tot_eventos_glob = len(df)
        tot_positivos_glob = int(df["T_POS_COUNT"].sum()) if not df.empty and "T_POS_COUNT" in df.columns else 0

        c_op1, c_op2 = st.columns(2)
        with c_op1:
            st.markdown(f'''
                <div style="background: rgba(5, 15, 30, 0.95); border: 2px solid #00a8ff; border-radius: 12px; padding: 22px; box-shadow: 0 0 20px rgba(0, 168, 255, 0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #a0d8ef; font-size: 12px; font-weight: bold; letter-spacing: 1px; font-family: monospace;">TOTAL DE EVENTOS</div>
                            <div style="color: #ffffff; font-size: 42px; font-weight: 900; text-shadow: 0 0 15px #00a8ff; margin-top: 5px;">{tot_eventos_glob:,}</div>
                        </div>
                        <div style="border: 2px solid rgba(0,168,255,0.5); border-radius: 10px; padding: 12px; background: rgba(0,168,255,0.12);">{SVG_ACTIVITY}</div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        with c_op2:
            st.markdown(f'''
                <div style="background: rgba(5, 15, 30, 0.95); border: 2px solid #00ffaa; border-radius: 12px; padding: 22px; box-shadow: 0 0 20px rgba(0, 255, 170, 0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #a0ffdf; font-size: 12px; font-weight: bold; letter-spacing: 1px; font-family: monospace;">TOTAL DE EVENTOS POSITIVOS</div>
                            <div style="color: #ffffff; font-size: 42px; font-weight: 900; text-shadow: 0 0 15px #00ffaa; margin-top: 5px;">{tot_positivos_glob:,}</div>
                        </div>
                        <div style="border: 2px solid rgba(0,255,170,0.5); border-radius: 10px; padding: 12px; background: rgba(0,255,170,0.12);">{SVG_CHECK}</div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Función local para evitar NameError
        def normalizar_texto_mando(t):
            if not t or pd.isna(t): return ""
            t = str(t).strip().lower()
            return "".join(c for c in unicodedata.normalize('NFKD', t) if not unicodedata.combining(c))

        cols_positivos = ['RESULTADO POSITIVO 1', 'RESULTADO POSITIVO 2', 'RESULTADO POSITIVO 3', 
                          'RESULTADO POSITIVO 4', 'RESULTADO POSITIVO 5', 'RESULTADO POSITIVO 6']
        col_narrativo = next((c for c in df.columns if 'NARRATIV' in c.upper() or 'DETALLE' in c.upper() or 'HECHO' in c.upper() or 'RESUMEN' in c.upper()), None)
        
        map_tactico_norm = {normalizar_texto_mando(k): v for k, v in map_tactico_raw.items()}
        conteo_gt_globales = {'SEGURIDAD VIAL': 0, 'EMERGENCIAS': 0, 'CAPTURAS': 0, 'RECUPERACIONES': 0, 'COORDINACIONES': 0}
        
        oficios_total_count = 0
        armas_incautadas_count = 0
        drogas_incautadas_count = 0
        vehiculos_recuperados_count = 0
        
        # Los 2 únicos tipos oficiales de orden judicial
        oficios_dos_tipos = [
            'ciudadano aprehendido por oficio de captura',
            'ciudadano aprehendido por oficio de conduccion'
        ]

        if not df.empty:
            for _, row in df.iterrows():
                for col in cols_positivos:
                    val = row.get(col)
                    if pd.notna(val) and str(val).strip() not in ['SELECCIONAR', '', 'None']:
                        v_norm = normalizar_texto_mando(str(val))
                        
                        if 'ruido' in v_norm or 'gases' in v_norm:
                            grupo = 'SEGURIDAD VIAL'
                        else:
                            grupo = map_tactico_norm.get(v_norm, 'SEGURIDAD VIAL')
                            
                        conteo_gt_globales[grupo] = conteo_gt_globales.get(grupo, 0) + 1
                        
                        # Panel de Seguridad Global
                        if grupo == 'CAPTURAS' and v_norm in oficios_dos_tipos:
                            oficios_total_count += 1
                        if 'arma de fuego' in v_norm and 'aprehendido' not in v_norm:
                            armas_incautadas_count += 1
                        if 'sustancia' in v_norm or 'droga' in v_norm:
                            drogas_incautadas_count += 1
                        if 'vehiculo recuperado' in v_norm:
                            vehiculos_recuperados_count += 1

        # Cuadre de Flagrancia Global: CAPTURAS = FLAGRANCIA + OFICIOS
        flagrancia_count = conteo_gt_globales['CAPTURAS'] - oficios_total_count

        # Extracción global de municiones
        municiones_total_count = 0
        if col_narrativo and not df.empty:
            patrones_muni = [
                r'\b(\d{1,4})\s*(?:municion|municiones|bala|balas|cartucho|cartuchos|casquillo|casquillos)\b',
                r'\b(?:municion|municiones|bala|balas|cartucho|cartuchos|casquillo|casquillos)\b\s*(?:son|fueron|:|: |-|de)?\s*(\d{1,4})\b'
            ]
            for _, row in df.iterrows():
                text_narr = str(row.get(col_narrativo, '')).lower()
                for pat in patrones_muni:
                    matches = re.findall(pat, text_narr)
                    municiones_total_count += sum(int(m) for m in matches)

        st.markdown(f"<h3 style='color: #00ebff; border-left: 4px solid #00ebff; padding-left: 10px; font-family: monospace;'>{SVG_SHIELD} RESULTADOS OPERACIONALES (TOTALES GLOBALES)</h3>", unsafe_allow_html=True)
        
        gt1, gt2 = st.columns(2)
        with gt1:
            st.markdown(f'''
                <div class="notranslate" translate="no" style="background: rgba(5, 15, 30, 0.95); border: 2px solid #00a8ff; border-radius: 12px; padding: 22px; box-shadow: 0 0 20px rgba(0, 168, 255, 0.35); margin-bottom: 15px; position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #a0d8ef; font-size: 14px; font-weight: bold; letter-spacing: 1px; font-family: monospace;">SEGURIDAD VIAL</div>
                            <div style="color: #ffffff; font-size: 44px; font-weight: 900; text-shadow: 0 0 15px #00a8ff; margin-top: 5px;">{conteo_gt_globales["SEGURIDAD VIAL"]:,}</div>
                        </div>
                        <div style="border: 2px solid rgba(0,168,255,0.5); border-radius: 10px; padding: 6px; background: rgba(0,168,255,0.12);">
                            {ILLUST_VEHICULOS}
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        with gt2:
            st.markdown(f'''
                <div class="notranslate" translate="no" style="background: rgba(5, 15, 30, 0.95); border: 2px solid #00a8ff; border-radius: 12px; padding: 22px; box-shadow: 0 0 20px rgba(0, 168, 255, 0.35); margin-bottom: 15px; position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #a0d8ef; font-size: 14px; font-weight: bold; letter-spacing: 1px; font-family: monospace;">EMERGENCIAS</div>
                            <div style="color: #ffffff; font-size: 44px; font-weight: 900; text-shadow: 0 0 15px #00a8ff; margin-top: 5px;">{conteo_gt_globales["EMERGENCIAS"]:,}</div>
                        </div>
                        <div style="border: 2px solid rgba(0,168,255,0.5); border-radius: 10px; padding: 18px; background: rgba(0,168,255,0.12);">
                            <svg viewBox="0 0 24 24" width="55" height="55" fill="#00a8ff" style="filter: drop-shadow(0 0 6px #00a8ff);"><path d="M19 3H5c-1.1 0-1.99.9-1.99 2L3 19c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 11h-4v4h-4v-4H6v-4h4V6h4v4h4v4z"/></svg>
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

        gt3, gt4 = st.columns(2)
        with gt3:
            st.markdown(f'''
                <div class="notranslate" translate="no" style="background: rgba(5, 15, 30, 0.95); border: 2px solid #00a8ff; border-radius: 12px; padding: 22px; box-shadow: 0 0 20px rgba(0, 168, 255, 0.35); margin-bottom: 15px; position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #a0d8ef; font-size: 14px; font-weight: bold; letter-spacing: 1px; font-family: monospace;">CAPTURAS</div>
                            <div style="color: #ffffff; font-size: 44px; font-weight: 900; text-shadow: 0 0 15px #00a8ff; margin-top: 5px;">{conteo_gt_globales["CAPTURAS"]:,}</div>
                        </div>
                        <div style="border: 2px solid rgba(0,168,255,0.5); border-radius: 10px; padding: 6px; background: rgba(0,168,255,0.12);">
                            {ILLUST_FLAGRANCIA}
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
        with gt4:
            st.markdown(f'''
                <div class="notranslate" translate="no" style="background: rgba(5, 15, 30, 0.95); border: 2px solid #00a8ff; border-radius: 12px; padding: 22px; box-shadow: 0 0 20px rgba(0, 168, 255, 0.35); margin-bottom: 15px; position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #a0d8ef; font-size: 14px; font-weight: bold; letter-spacing: 1px; font-family: monospace;">RECUPERACIONES</div>
                            <div style="color: #ffffff; font-size: 44px; font-weight: 900; text-shadow: 0 0 15px #00a8ff; margin-top: 5px;">{conteo_gt_globales["RECUPERACIONES"]:,}</div>
                        </div>
                        <div style="border: 2px solid rgba(0,168,255,0.5); border-radius: 10px; padding: 6px; background: rgba(0,168,255,0.12);">
                            {ILLUST_ARMAS}
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

        gt5, _ = st.columns(2)
        with gt5:
            st.markdown(f'''
                <div class="notranslate" translate="no" style="background: rgba(5, 15, 30, 0.95); border: 2px solid #00a8ff; border-radius: 12px; padding: 22px; box-shadow: 0 0 20px rgba(0, 168, 255, 0.35); margin-bottom: 15px; position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #a0d8ef; font-size: 14px; font-weight: bold; letter-spacing: 1px; font-family: monospace;">COORDINACIONES</div>
                            <div style="color: #ffffff; font-size: 44px; font-weight: 900; text-shadow: 0 0 15px #00a8ff; margin-top: 5px;">{conteo_gt_globales["COORDINACIONES"]:,}</div>
                        </div>
                        <div style="border: 2px solid rgba(0,168,255,0.5); border-radius: 10px; padding: 6px; background: rgba(0,168,255,0.12);">
                            {ILLUST_COORDINACIONES}
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('''
            <div class="notranslate" translate="no" style="background: rgba(4, 12, 26, 0.95); border: 2px solid #00d4ff; border-radius: 14px; padding: 18px 18px 8px 18px; box-shadow: 0 0 25px rgba(0, 212, 255, 0.4); margin-bottom: 10px;">
                <div style="text-align: center; color: #ffffff; font-size: 18px; font-weight: 900; letter-spacing: 3px; margin-bottom: 6px; font-family: sans-serif; text-shadow: 0 0 10px #00ebff;">
                    PANEL DE SEGURIDAD OPERACIONAL
                </div>
            </div>
        ''', unsafe_allow_html=True)

        rc1, rc2, rc3, rc4, rc5, rc6 = st.columns(6)
        with rc1:
            st.markdown(render_ops_card("A. FLAGRANCIA", flagrancia_count, ILLUST_FLAGRANCIA), unsafe_allow_html=True)
        with rc2:
            st.markdown(render_ops_card("A. OFICIO", oficios_total_count, ILLUST_OFICIO), unsafe_allow_html=True)
        with rc3:
            st.markdown(render_ops_card("ARMAS RECUPERADAS", armas_incautadas_count, ILLUST_ARMAS), unsafe_allow_html=True)
        with rc4:
            st.markdown(render_ops_card("DROGAS INCAUTADAS", drogas_incautadas_count, ILLUST_DROGAS), unsafe_allow_html=True)
        with rc5:
            st.markdown(render_ops_card("MUNICIONES INCAUTADAS", municiones_total_count, ILLUST_MUNICIONES), unsafe_allow_html=True)
        with rc6:
            st.markdown(render_ops_card("VEHÍCULOS RECUPERADOS", vehiculos_recuperados_count, ILLUST_VEHICULOS), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"<h3 style='color: #00ebff; border-left: 4px solid #00ebff; padding-left: 10px; font-family: monospace;'>{SVG_GRID} ANÁLISIS POR CENTROS</h3>", unsafe_allow_html=True)

        if not df_raw.empty and not df.empty:
            tot_gen_filtrado = len(df)
            
            centros_resumen = df.groupby('CENTRO').agg(
                TOTAL_EVENTOS=('CENTRO', 'count'),
                TOTAL_POSITIVOS=('T_POS_COUNT', 'sum')
            ).reset_index()

            centros_resumen['PORCENTAJE'] = centros_resumen['TOTAL_EVENTOS'].apply(lambda x: (x / tot_gen_filtrado * 100) if tot_gen_filtrado > 0 else 0)
            centros_resumen = centros_resumen.sort_values(by='TOTAL_EVENTOS', ascending=False)

            centros_resumen['TEXTO_BARRA'] = centros_resumen.apply(
                lambda r: f"<b>T. Evento: {r['TOTAL_EVENTOS']:,}</b><br><b>T. Positivo: {r['TOTAL_POSITIVOS']:,}</b><br><b>({r['PORCENTAJE']:.1f}%)</b>", 
                axis=1
            )

            colores_centros = ['#00ebff', '#00ffaa', '#ffaa00', '#ff4b4b', '#b000ff', '#ff00c8', '#00ffd5', '#7a00ff']

            fig_centros_mando = go.Figure()

            fig_centros_mando.add_trace(go.Bar(
                x=centros_resumen['CENTRO'],
                y=centros_resumen['TOTAL_EVENTOS'],
                text=centros_resumen['TEXTO_BARRA'],
                textposition='outside',
                marker_color=colores_centros[:len(centros_resumen)],
                showlegend=False,
                textfont=dict(color='#ffffff', size=11, family='monospace')
            ))

            fig_centros_mando.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white", family="monospace"),
                xaxis=dict(title="Centro de Operación", showgrid=False, tickfont=dict(color='white', size=12)),
                yaxis=dict(title="Cantidad de Eventos", showgrid=True, gridcolor='rgba(0, 235, 255, 0.15)', tickfont=dict(color='white')),
                margin=dict(t=80, b=30, l=40, r=20),
                height=520
            )

            st.plotly_chart(fig_centros_mando, use_container_width=True)
        else:
            st.info("No hay suficientes datos para generar el análisis por centros.")
