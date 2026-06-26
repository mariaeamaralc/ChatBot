import os
import json
import PyPDF2
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai

load_dotenv()

API_KEYS = [
    os.environ.get("GEMINI_API_KEY_1"),
    os.environ.get("GEMINI_API_KEY_2"),
    os.environ.get("GEMINI_API_KEY_3")
]

if "key_index" not in st.session_state:
    st.session_state.key_index = 0

SYSTEM_PROMPT = (
    "Você é o 'Computador de Bordo', o mestre de um jogo interativo de ficção científica e sobrevivência espacial. "
    "Seu papel é testar os conhecimentos do usuário em Ciências da Natureza (Física, Química, Biologia e Astronomia). "
    "A cada turno, descreva uma situação crítica de sobrevivência no espaço de forma imersiva. "
    "Ofereça sempre 3 opções de ação (A, B e C) baseadas em conceitos científicos reais. "
    "Se o jogador errar, explique cientificamente o porquê de forma curta, e mude o rumo da história."
)

CHAVES_VALIDAS = [key for key in API_KEYS if key]

if CHAVES_VALIDAS:
    if st.session_state.key_index >= len(CHAVES_VALIDAS):
        st.session_state.key_index = 0
    genai.configure(api_key=CHAVES_VALIDAS[st.session_state.key_index])
else:
    st.error("Nenhuma chave de API válida encontrada. Verifique seu arquivo .env.")
    st.stop()

CHAT_HISTORY_DIR = "historico_missoes"
if not os.path.exists(CHAT_HISTORY_DIR):
    os.makedirs(CHAT_HISTORY_DIR)

st.set_page_config(page_title="COSMOS", page_icon="🛸", layout="wide")

# ── ACESSIBILIDADE: Estado inicial ────────────────────────────────────────────
if "font_size" not in st.session_state:
    st.session_state.font_size = "normal"   # "normal" | "grande" | "muito_grande"
if "alto_contraste" not in st.session_state:
    st.session_state.alto_contraste = False
if "espacamento" not in st.session_state:
    st.session_state.espacamento = False
if "daltonismo" not in st.session_state:
    st.session_state.daltonismo = "none"  # "none" | "deuteranopia" | "protanopia" | "tritanopia"

# Mapas de tamanho de fonte
FONT_SCALE = {
    "normal":       {"body": 15, "small": 11, "label": 8,  "title": 18, "mono": 11},
    "grande":       {"body": 19, "small": 14, "label": 10, "title": 22, "mono": 14},
    "muito_grande": {"body": 24, "small": 18, "label": 13, "title": 28, "mono": 18},
}

fs = FONT_SCALE[st.session_state.font_size]

# Paleta: normal vs alto contraste
if st.session_state.alto_contraste:
    COR_TEXTO      = "#FFFFFF"
    COR_ACENTO     = "#00FFD4"
    COR_SECUNDARIO = "#FFD600"
    COR_BG         = "#000000"
    COR_BG2        = "#0A0A0A"
    COR_BORDA      = "rgba(0,255,212,0.6)"
    COR_USER_BG    = "rgba(255,214,0,0.08)"
    COR_USER_BORDA = "rgba(255,214,0,0.8)"
else:
    COR_TEXTO      = "#B8D4E0"
    COR_ACENTO     = "#00DCB4"
    COR_SECUNDARIO = "#FF3264"
    COR_BG         = "#060A14"
    COR_BG2        = "#040710"
    COR_BORDA      = "rgba(0,220,180,0.1)"
    COR_USER_BG    = "rgba(255,50,100,0.03)"
    COR_USER_BORDA = "rgba(255,50,100,0.5)"

# Espaçamento de linha ampliado
LINE_HEIGHT = "2.2" if st.session_state.espacamento else "1.75"
LETTER_SPACING = "0.06em" if st.session_state.espacamento else "normal"
WORD_SPACING   = "0.12em" if st.session_state.espacamento else "normal"

# ── ESTILOS GLOBAIS ──────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, .stApp {{
    background-color: {COR_BG} !important;
    font-family: 'Inter', sans-serif !important;
}}

.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(0,220,180,0.06) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    z-index: 0;
}}

.block-container {{
    padding-top: 0 !important;
    padding-bottom: 80px !important;
    max-width: 100% !important;
}}

#MainMenu, footer, header {{ visibility: hidden; }}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background: {COR_BG2} !important;
    border-right: 1px solid {COR_BORDA} !important;
    padding-top: 0 !important;
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 0 !important; }}
[data-testid="stSidebarContent"] {{ padding: 0 16px 24px !important; }}

[data-testid="stSidebar"] h3 {{
    font-family: 'Orbitron', monospace !important;
    font-size: {fs["label"]}px !important;
    font-weight: 700 !important;
    letter-spacing: 4px !important;
    text-transform: uppercase !important;
    color: {COR_ACENTO} !important;
    opacity: 0.7;
    padding: 20px 0 8px !important;
    margin: 0 !important;
    border-bottom: 1px solid {COR_BORDA} !important;
}}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] small {{
    font-family: 'Inter', sans-serif !important;
    color: #7090A0 !important;
    font-size: {fs["small"]}px !important;
}}

/* ── BOTÕES ── */
button[kind="primary"] {{
    background: transparent !important;
    border: 1px solid rgba(255,50,100,0.6) !important;
    color: #FF3264 !important;
    font-family: 'Orbitron', monospace !important;
    font-size: {fs["label"]}px !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    border-radius: 3px !important;
    transition: all 0.2s !important;
    text-transform: uppercase !important;
}}
button[kind="primary"]:hover {{
    background: rgba(255,50,100,0.1) !important;
    border-color: #FF3264 !important;
    box-shadow: 0 0 16px rgba(255,50,100,0.3) !important;
}}

button[kind="secondary"] {{
    background: transparent !important;
    border: 1px solid {COR_BORDA} !important;
    color: {COR_ACENTO} !important;
    opacity: 0.7;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: {fs["label"]}px !important;
    border-radius: 3px !important;
    text-align: left !important;
    transition: all 0.2s !important;
}}
button[kind="secondary"]:hover {{
    border-color: {COR_ACENTO} !important;
    opacity: 1 !important;
    background: rgba(0,220,180,0.05) !important;
}}

/* ── MENSAGENS DE CHAT ── */
[data-testid="stChatMessage"] {{
    background: rgba(8,14,26,0.85) !important;
    border: 1px solid {COR_BORDA} !important;
    border-left: 3px solid {COR_ACENTO} !important;
    border-radius: 4px !important;
    margin-bottom: 12px !important;
    padding: 16px 20px !important;
}}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
    border-left-color: {COR_USER_BORDA} !important;
    background: {COR_USER_BG} !important;
}}

[data-testid="stChatMessageContent"] p {{
    font-family: 'Inter', sans-serif !important;
    font-size: {fs["body"]}px !important;
    line-height: {LINE_HEIGHT} !important;
    letter-spacing: {LETTER_SPACING} !important;
    word-spacing: {WORD_SPACING} !important;
    color: {COR_TEXTO} !important;
}}

[data-testid="stChatMessageContent"] strong {{ color: {COR_ACENTO} !important; }}
[data-testid="stChatMessageContent"] em {{ color: rgba(184,212,224,0.7) !important; }}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] {{
    background: {COR_BG} !important;
    border-top: 1px solid {COR_BORDA} !important;
}}
[data-testid="stChatInput"] > div {{
    background: linear-gradient(135deg, {COR_BG} 0%, #1A1D24 100%) !important;
    border-radius: 6px !important;
    padding: 6px !important;
}}
[data-testid="stChatInput"] textarea {{
    background: {COR_BG} !important;
    border: 1px solid {COR_BORDA} !important;
    border-radius: 4px !important;
    color: {COR_ACENTO} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: {fs["body"]}px !important;
    caret-color: {COR_ACENTO} !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: {COR_BG} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: {fs["small"]}px !important;
}}
[data-testid="stChatInput"] textarea:focus {{
    border-color: {COR_ACENTO} !important;
    box-shadow: 0 0 0 2px rgba(0,220,180,0.15) !important;
    outline: 2px solid {COR_ACENTO} !important;
}}

/* ── ACESSIBILIDADE: foco visível em todos os elementos ── */
*:focus-visible {{
    outline: 2px solid {COR_ACENTO} !important;
    outline-offset: 3px !important;
}}

/* FILE UPLOADER */
[data-testid="stFileUploader"] {{
    background: rgba(0,220,180,0.02) !important;
    border: 1px dashed rgba(0,220,180,0.15) !important;
    border-radius: 3px !important;
}}

/* SCROLLBAR */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: {COR_BG}; }}
::-webkit-scrollbar-thumb {{ background: {COR_ACENTO}; opacity: 0.3; border-radius: 2px; }}

hr {{ border: none !important; border-top: 1px solid rgba(0,220,180,0.08) !important; margin: 12px 0 !important; }}

/* Respeita preferência de sistema para movimento reduzido */
@media (prefers-reduced-motion: reduce) {{
    * {{ animation: none !important; transition: none !important; }}
}}
</style>

<!-- Filtros SVG para simulação/correção de daltonismo -->
<svg style="position:absolute;width:0;height:0;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Deuteranopia (verde) -->
    <filter id="filter-deuteranopia">
      <feColorMatrix type="matrix" values="
        0.625 0.375 0     0 0
        0.70  0.30  0     0 0
        0     0.30  0.70  0 0
        0     0     0     1 0"/>
    </filter>
    <!-- Protanopia (vermelho) -->
    <filter id="filter-protanopia">
      <feColorMatrix type="matrix" values="
        0.567 0.433 0     0 0
        0.558 0.442 0     0 0
        0     0.242 0.758 0 0
        0     0     0     1 0"/>
    </filter>
    <!-- Tritanopia (azul) -->
    <filter id="filter-tritanopia">
      <feColorMatrix type="matrix" values="
        0.95  0.05  0     0 0
        0     0.433 0.567 0 0
        0     0.475 0.525 0 0
        0     0     0     1 0"/>
    </filter>
  </defs>
</svg>

<style>
/* Aplica filtro de daltonismo no app inteiro */
{"html { filter: url(#filter-" + st.session_state.daltonismo + ") !important; }" if st.session_state.daltonismo != "none" else ""}
</style>
""", unsafe_allow_html=True)


# ── HELPER: bloco de telemetria ───────────────────────────────────────────────
def tele_card(label, value, bar_pct=None, value_color="#00DCB4", bar_color="#00DCB4"):
    glow = f"0 0 14px {value_color}80"
    bar_html = ""
    if bar_pct is not None:
        bar_html = f"""
        <div style="height:3px;background:rgba(255,255,255,0.06);border-radius:2px;margin-top:8px;"
             role="progressbar" aria-valuenow="{bar_pct}" aria-valuemin="0" aria-valuemax="100"
             aria-label="{label}: {bar_pct}%">
            <div style="height:100%;width:{bar_pct}%;background:{bar_color};
                        border-radius:2px;box-shadow:0 0 6px {bar_color}80;"></div>
        </div>"""
    return f"""
    <div style="background:rgba(6,10,20,0.9);border:1px solid rgba(0,220,180,0.1);
                border-top:1px solid rgba(0,220,180,0.25);border-radius:4px;
                padding:12px 14px;margin-bottom:10px;" role="status" aria-label="{label}: {value}">
        <div style="font-family:'Orbitron',monospace;font-size:{fs['label']}px;font-weight:700;
                    letter-spacing:3px;text-transform:uppercase;color:rgba(0,220,180,0.4);
                    margin-bottom:6px;">{label}</div>
        <div style="font-family:'Orbitron',monospace;font-size:20px;font-weight:700;
                    color:{value_color};text-shadow:{glow};line-height:1.2;">{value}</div>
        {bar_html}
    </div>"""


def coord_card():
    return f"""
    <div style="background:rgba(6,10,20,0.9);border:1px solid rgba(0,220,180,0.1);
                border-top:1px solid rgba(0,220,180,0.25);border-radius:4px;
                padding:12px 14px;margin-bottom:10px;">
        <div style="font-family:'Orbitron',monospace;font-size:{fs['label']}px;font-weight:700;
                    letter-spacing:3px;text-transform:uppercase;color:rgba(0,220,180,0.4);
                    margin-bottom:8px;">Coordenadas</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:{fs['mono']}px;
                    color:#00DCB4;line-height:2;opacity:0.85;">
            X &nbsp;4.823.091<br>
            Y −0.334.872<br>
            Z &nbsp;1.007.445
        </div>
    </div>"""


# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:13px 28px;border-bottom:1px solid rgba(0,220,180,0.12);
            background:linear-gradient(90deg,#040710,#081222,#040710);
            position:relative;overflow:hidden;margin-bottom:4px;"
     role="banner" aria-label="COSMOS — Cabeçalho principal">

  <div style="position:absolute;bottom:0;left:0;right:0;height:1px;
              background:linear-gradient(90deg,transparent,#00DCB4,#FF3264,#00DCB4,transparent);
              animation:scanline 5s linear infinite;" aria-hidden="true"></div>
  <style>@keyframes scanline{{0%{{transform:translateX(-100%)}}100%{{transform:translateX(100%)}}}}</style>

  <div style="font-family:'Orbitron',monospace;font-size:{fs['title']}px;font-weight:900;
              letter-spacing:6px;color:#00DCB4;
              text-shadow:0 0 20px rgba(0,220,180,0.7),0 0 40px rgba(0,220,180,0.2);"
       aria-label="COSMOS — Sistema Educacional de Ciências da Natureza">
    COSMOS<span style="color:#FF3264;"></span>
    <span style="font-size:{fs['small']}px;font-weight:400;opacity:0.4;letter-spacing:3px;margin-left:8px;">v4.2.1</span>
  </div>

  <div style="display:flex;gap:16px;align-items:center;" role="status" aria-label="Status do sistema">
    <span style="font-family:'Inter',sans-serif;font-size:{fs['small']}px;font-weight:600;letter-spacing:2px;
                 color:#00DCB4;border:1px solid rgba(0,220,180,0.3);background:rgba(0,220,180,0.06);
                 padding:3px 10px;border-radius:2px;" title="Sistema operacional">SYS ONLINE</span>
    <span style="font-family:'Inter',sans-serif;font-size:{fs['small']}px;font-weight:600;letter-spacing:2px;
                 color:#FFD200;border:1px solid rgba(255,210,0,0.3);background:rgba(255,210,0,0.06);
                 padding:3px 10px;border-radius:2px;" title="Alerta no Setor 7">SETOR-7 ⚠</span>
    <span style="font-family:'Inter',sans-serif;font-size:{fs['small']}px;font-weight:600;letter-spacing:2px;
                 color:#FF3264;border:1px solid rgba(255,50,100,0.3);background:rgba(255,50,100,0.06);
                 padding:3px 10px;border-radius:2px;" title="Nível de oxigênio crítico">O₂ 61%</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── MODELO ────────────────────────────────────────────────────────────────────
ai_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)

col_principal, col_status = st.columns([3, 1])


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
uploaded_context = ""

with st.sidebar:
    st.markdown(f"""
    <div style="background:rgba(0,220,180,0.04);border-bottom:1px solid rgba(0,220,180,0.1);
                padding:18px 4px 14px;text-align:center;margin-bottom:4px;">
        <div style="font-family:'Orbitron',monospace;font-size:13px;font-weight:900;
                    letter-spacing:5px;color:#00DCB4;
                    text-shadow:0 0 16px rgba(0,220,180,0.6);">COSMOS</div>
        <div style="font-family:'Inter',sans-serif;font-size:{fs['small']}px;letter-spacing:3px;
                    color:rgba(0,220,180,0.35);text-transform:uppercase;margin-top:2px;">
            Software Educacional de Ciências da Natureza
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Missão")

    if st.button("▶  NOVA MISSÃO", type="primary", use_container_width=True):
        st.session_state.active_chat = ai_model.start_chat(history=[])
        st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.rerun()

    st.markdown("### Banco de Memória")

    if os.path.exists(CHAT_HISTORY_DIR):
        saved_files = sorted(os.listdir(CHAT_HISTORY_DIR), reverse=True)
        if saved_files:
            for file_name in saved_files:
                parts = file_name.split("_", 2)
                display_title = parts[-1].replace(".json", "") if len(parts) > 2 else file_name
                label = display_title[:28].upper()
                if st.button(f"▸  {label}", key=file_name, use_container_width=True):
                    with open(os.path.join(CHAT_HISTORY_DIR, file_name), "r", encoding="utf-8") as f:
                        st.session_state.active_chat = ai_model.start_chat(history=json.load(f))
                    st.session_state.current_session_id = "_".join(file_name.split("_")[:2])
                    st.rerun()
        else:
            st.markdown(f"""
            <div style="font-family:'Inter',sans-serif;font-size:{fs['small']}px;
                        color:rgba(0,220,180,0.25);letter-spacing:1px;
                        text-align:center;padding:12px 0;">
                — Sem missões gravadas —
            </div>
            """, unsafe_allow_html=True)

    # ── PAINEL DE ACESSIBILIDADE ─────────────────────────────────────────────
    st.markdown("### ♿ Acessibilidade")

    # — Tamanho de fonte —
    st.markdown(f"<p style='font-size:{fs['small']}px;margin-bottom:4px;'>Tamanho do texto</p>", unsafe_allow_html=True)
    cols_font = st.columns(3)
    with cols_font[0]:
        if st.button("A", key="font_normal", help="Texto normal", use_container_width=True):
            st.session_state.font_size = "normal"
            st.rerun()
    with cols_font[1]:
        if st.button("A+", key="font_grande", help="Texto grande", use_container_width=True):
            st.session_state.font_size = "grande"
            st.rerun()
    with cols_font[2]:
        if st.button("A++", key="font_muito", help="Texto muito grande", use_container_width=True):
            st.session_state.font_size = "muito_grande"
            st.rerun()

    # Indicador do tamanho ativo
    tamanho_label = {"normal": "Normal", "grande": "Grande", "muito_grande": "Máximo"}
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:{fs['small']}px;
                color:rgba(0,220,180,0.5);text-align:center;margin:4px 0 10px;">
        ▸ {tamanho_label[st.session_state.font_size]}
    </div>
    """, unsafe_allow_html=True)

    # — Alto contraste —
    contraste_label = "◉ ALTO CONTRASTE: ON" if st.session_state.alto_contraste else "○ Alto contraste: off"
    if st.button(contraste_label, key="toggle_contraste", use_container_width=True,
                 help="Aumenta contraste para facilitar leitura"):
        st.session_state.alto_contraste = not st.session_state.alto_contraste
        st.rerun()

    # — Espaçamento ampliado —
    espaco_label = "◉ ESPAÇAMENTO: ON" if st.session_state.espacamento else "○ Espaçamento ampliado: off"
    if st.button(espaco_label, key="toggle_espacamento", use_container_width=True,
                 help="Aumenta espaçamento entre linhas e letras"):
        st.session_state.espacamento = not st.session_state.espacamento
        st.rerun()

    # — Modo daltônico —
    st.markdown(f"<p style='font-size:{fs['small']}px;margin-bottom:4px;'>Modo daltonismo</p>", unsafe_allow_html=True)

    MODOS_DALTONISMO = {
        "none":         "○ Desativado",
        "deuteranopia": "◉ Deuteranopia (verde)",
        "protanopia":   "◉ Protanopia (vermelho)",
        "tritanopia":   "◉ Tritanopia (azul)",
    }
    for modo, rotulo in MODOS_DALTONISMO.items():
        ativo = st.session_state.daltonismo == modo
        label = rotulo.replace("○", "◉") if ativo else rotulo.replace("◉", "○")
        estilo = "primary" if ativo else "secondary"
        if st.button(label, key=f"dalton_{modo}", use_container_width=True,
                     help=f"Filtro de cor para {rotulo.split('(')[-1].rstrip(')')} se aplicável"):
            st.session_state.daltonismo = modo
            st.rerun()

    st.markdown("### Subsistemas")

    with st.expander("Insira um documento (PDF ou TXT)"):
        uploaded_file = st.file_uploader(
            "Selecione um arquivo",
            type=["txt", "pdf"],
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".txt"):
                    uploaded_context = uploaded_file.read().decode("utf-8")
                elif uploaded_file.name.endswith(".pdf"):
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    for page in pdf_reader.pages:
                        uploaded_context += page.extract_text() + "\n"
                st.success("✓ Manual integrado ao núcleo")
            except Exception as error:
                st.error(f"Erro de leitura: {error}")

    with st.expander("⚠  Pane de Emergência"):
        st.markdown(f"""
        <div style="font-family:'Inter',sans-serif;font-size:{fs['small']}px;
                    color:rgba(255,210,0,0.5);padding:0 0 8px;">
            Simula uma falha crítica aleatória para treino de resposta.
        </div>
        """, unsafe_allow_html=True)
        trigger_quiz = st.button("▶  SIMULAR PANE", use_container_width=True)


# ── ESTADO DO JOGO ────────────────────────────────────────────────────────────
if "active_chat" not in st.session_state:
    st.session_state.active_chat = ai_model.start_chat(history=[])
    st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")


def persist_chat_history():
    if len(st.session_state.active_chat.history) > 0:
        first_prompt = st.session_state.active_chat.history[0].parts[0].text[:25]
        clean_title = "".join(c for c in first_prompt if c.isalnum() or c.isspace()).strip()
        file_title = f"{st.session_state.current_session_id}_{clean_title or 'log_missao'}.json"
        full_path = os.path.join(CHAT_HISTORY_DIR, file_title)
        formatted = [{"role": m.role, "parts": [m.parts[0].text]}
                     for m in st.session_state.active_chat.history]
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(formatted, f, ensure_ascii=False, indent=4)


def execute_safe_request(prompt_text):
    try:
        return st.session_state.active_chat.send_message(prompt_text)
    except Exception as error:
        err_msg = str(error).lower()
        if any(k in err_msg for k in ["429", "quota", "exhausted"]):
            if st.session_state.key_index < len(CHAVES_VALIDAS) - 1:
                st.session_state.key_index += 1
                genai.configure(api_key=CHAVES_VALIDAS[st.session_state.key_index])
                fallback = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=SYSTEM_PROMPT
                )
                st.session_state.active_chat = fallback.start_chat(
                    history=st.session_state.active_chat.history
                )
                st.toast("Roteando para antena reserva...", icon="📡")
                return st.session_state.active_chat.send_message(prompt_text)
            else:
                st.error("Link de comunicações rompido — sobrecarga crítica.")
                st.stop()
        else:
            st.error(f"Erro fatal de telemática: {error}")
            st.stop()


# ── PANE ALEATÓRIA ────────────────────────────────────────────────────────────
if trigger_quiz:
    quiz_prompt = "Gere um problema de sobrevivência imediato no espaço envolvendo física ou química e me dê as opções A, B e C."
    with col_principal:
        with st.spinner("Escaneando falhas mecânicas..."):
            response = execute_safe_request(quiz_prompt)
            if response:
                persist_chat_history()

# ── HISTÓRICO DE CHAT ─────────────────────────────────────────────────────────
with col_principal:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if len(st.session_state.active_chat.history) == 0:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(f"**Bem-vindo, para iniciar uma nova missão digite A, B, C ou insira um comando**")

    for message in st.session_state.active_chat.history:
        if "Gere um problema de sobrevivência" in message.parts[0].text and message.role == "user":
            continue
        role_type = "user" if message.role == "user" else "assistant"
        icon = "🧑‍🚀" if role_type == "user" else "🤖"
        with st.chat_message(role_type, avatar=icon):
            st.markdown(message.parts[0].text)


# ── INPUT DE COMANDOS ─────────────────────────────────────────────────────────
if user_input := st.chat_input("▸   Digite A, B ou C  —  ou um comando de sobrevivência..."):
    if user_input.strip().lower() == "sair":
        st.info("Desconectando do terminal central.")
        st.stop()

    with col_principal:
        with st.chat_message("user", avatar="🧑‍🚀"):
            st.markdown(user_input)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Processando dados telemétricos..."):
                if len(st.session_state.active_chat.history) == 0:
                    comando_inicial = f"O usuário iniciou o jogo com o comando: '{user_input}'. Inicie a primeira missão imediatamente com base nisso."
                    final_prompt = (
                        f"Considere os parâmetros deste manual técnico:\n{uploaded_context}\n\n{comando_inicial}"
                        if uploaded_context else comando_inicial
                    )
                else:
                    final_prompt = (
                        f"Considere os parâmetros deste manual técnico:\n{uploaded_context}\n\nComando: {user_input}"
                        if uploaded_context else user_input
                    )

                response = execute_safe_request(final_prompt)
                if response:
                    st.markdown(response.text)
                    persist_chat_history()