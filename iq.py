import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import time

TOKEN_TELEGRAM = "8262824397:AAERAJr6Epu2UvUPlOeLvJ2VJlB19o9c-xo"
MEU_ID_TELEGRAM = "1007733041"

if "alertas_enviados" not in st.session_state:
    st.session_state.alertas_enviados = set()

def enviar_alerta(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": MEU_ID_TELEGRAM, "text": mensagem, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except:
        return False

def calcular_tempo(tge_dt):
    if not tge_dt:
        return None, "unknown"
    agora = datetime.now(timezone.utc)
    delta = tge_dt - agora
    total = delta.total_seconds()
    if total < 0: return delta, "finalizado"
    elif total < 3600: return delta, "critico"
    elif total < 86400: return delta, "urgente"
    else: return delta, "normal"

def formatar_tempo(delta):
    if not delta: return "N/A"
    total = int(delta.total_seconds())
    if total < 0:
        horas_atras = abs(total) // 3600
        mins_atras = abs(total) // 60
        if horas_atras > 0: return f"Finalizado ha {horas_atras}h"
        return f"Finalizado ha {mins_atras}min"
    dias = total // 86400
    horas = (total % 86400) // 3600
    mins = (total % 3600) // 60
    secs = total % 60
    if dias > 0: return f"{dias}d {horas:02}h {mins:02}m"
    return f"{horas:02}h {mins:02}m {secs:02}s"

def cor_status(status):
    return {"critico":"#FF4444","urgente":"#FF8C00","normal":"#00FF00","finalizado":"#888888","unknown":"#555555"}.get(status,"#00FF00")

def badge_status(status):
    return {"critico":"🔴 CRITICO","urgente":"🟠 URGENTE","normal":"🟢 UPCOMING","finalizado":"⚫ FINALIZADO","unknown":"⚪ A CONFIRMAR"}.get(status,"🟢 UPCOMING")

def cor_risco(risco):
    return {"BAIXO":"#00FF00","MEDIO":"#FF8C00","ALTO":"#FF4444"}.get(risco,"#FFFFFF")

def estrelas_score(score_str):
    try:
        n = int(score_str.split("/")[0])
        return "★" * n + "☆" * (10 - n)
    except:
        return score_str

def checar_e_alertar_icos(icos):
    for ico in icos:
        delta, status = calcular_tempo(ico.get("tge_dt"))
        chave = f"{ico['token']}_{status}"
        if chave in st.session_state.alertas_enviados:
            continue
        if status in ["critico", "urgente"]:
            emoji = "🔴" if status == "critico" else "🟠"
            titulo = "CRITICO - MENOS DE 1H!" if status == "critico" else "HOJE!"
            msg = (
                f"{emoji} *ALERTA ICO {titulo}*\n\n"
                f"🚀 *{ico['projeto']} ({ico['token']})*\n"
                f"⏰ Faltam: {formatar_tempo(delta)}\n"
                f"💵 Preco: {ico['preco']}\n"
                f"🌐 Plataforma: {ico['plataformas']}\n"
                f"💰 Backers: {ico['backers']}\n"
                f"📊 FDV: {ico['fdv']} | Score: {ico['score']}\n"
                f"🔗 {ico['link']}"
            )
            if enviar_alerta(msg):
                st.session_state.alertas_enviados.add(chave)

def render_ico_card(ico, numero_ico):
    delta, status = calcular_tempo(ico.get("tge_dt"))
    tge_dt    = ico.get("tge_dt")
    cor       = cor_status(status)
    badge     = badge_status(status)
    tempo_str = formatar_tempo(delta)
    hora_utc_s = tge_dt.strftime("%H:%M UTC") if tge_dt else "N/A"
    hora_brt  = ico.get("hora_brt", "N/A")
    c_risco   = cor_risco(ico.get("risco", "MEDIO"))
    estrelas  = estrelas_score(ico.get("score", "N/A"))

    if status == "finalizado":
        card_bg = "background:#0d0d0d;"
    elif status == "critico":
        card_bg = "background:linear-gradient(135deg,#1a0000,#0d0000);"
    elif status == "urgente":
        card_bg = "background:linear-gradient(135deg,#1a0800,#0d0500);"
    else:
        card_bg = "background:linear-gradient(135deg,#001a00,#000d00);"

    botao_texto = "ENCERRADO" if status == "finalizado" else "COMPRAR AGORA"
    tag_enc = (
        f"<span style='background:rgba(255,68,68,0.15);color:#FF4444;"
        f"padding:8px 14px;border-radius:6px;font-size:12px;font-weight:bold;"
        f"border:1px solid #FF4444;margin-left:8px;'>"
        f"VENDA ENCERRADA {hora_brt}</span>"
    ) if status == "finalizado" else ""

    return (
        f"<div style='{card_bg}border:2px solid {cor};border-radius:16px;padding:22px;margin-bottom:20px;box-shadow:0 0 20px {cor}33;'>"

        f"<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;'>"
        f"<div style='display:flex;align-items:center;gap:14px;flex-wrap:wrap;'>"
        f"<div style='width:50px;height:50px;border-radius:50%;border:2px solid {cor};background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;flex-shrink:0;'>"
        f"<span style='color:{cor};font-size:22px;font-weight:900;'>{numero_ico}</span>"
        f"</div>"
        f"<div>"
        f"<div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px;'>"
        f"<span style='color:#FFFFFF;font-size:24px;font-weight:900;text-shadow:0 0 12px {cor};'>{ico['projeto']}</span>"
        f"<span style='background:{cor};color:#000000;padding:3px 12px;border-radius:20px;font-size:13px;font-weight:900;'>{ico['token']}</span>"
        f"<span style='background:rgba(0,0,0,0.4);color:{cor};padding:3px 10px;border-radius:20px;font-size:11px;border:1px solid {cor};'>{badge}</span>"
        f"<span style='background:rgba(0,0,0,0.4);color:{c_risco};padding:3px 10px;border-radius:20px;font-size:11px;border:1px solid {c_risco};'>⚠ {ico.get('risco','N/A')}</span>"
        f"</div>"
        f"<div style='color:#777;font-size:12px;'>📅 {ico.get('tge_str','N/A')} · {hora_brt} · {hora_utc_s} · {ico.get('categoria','N/A')}</div>"
        f"</div>"
        f"</div>"
        f"<div style='text-align:right;'>"
        f"<div style='color:{cor};font-size:28px;font-weight:900;font-family:Consolas,monospace;letter-spacing:2px;'>{tempo_str}</div>"
        f"<div style='color:#666;font-size:11px;margin-top:3px;'>Contagem Regressiva</div>"
        f"</div>"
        f"</div>"

        f"<div style='border-top:1px solid {cor}44;margin:14px 0;'></div>"

        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:10px;'>"
        f"<div style='background:rgba(0,0,0,0.45);padding:11px;border-radius:9px;border:1px solid #1e1e1e;'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:4px;'>TIPO</div>"
        f"<div style='color:#FFFFFF;font-size:14px;font-weight:bold;'>{ico['tipo']}</div>"
        f"</div>"
        f"<div style='background:rgba(0,0,0,0.45);padding:11px;border-radius:9px;border:1px solid #1e1e1e;'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:4px;'>PRECO TGE</div>"
        f"<div style='color:#00FF00;font-size:15px;font-weight:bold;'>{ico['preco']}</div>"
        f"<div style='color:#555;font-size:11px;'>Listing: {ico['preco_listing']}</div>"
        f"</div>"
        f"<div style='background:rgba(0,0,0,0.45);padding:11px;border-radius:9px;border:1px solid #1e1e1e;'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:4px;'>FDV / RAISED</div>"
        f"<div style='color:#FFD700;font-size:15px;font-weight:bold;'>{ico['fdv']}</div>"
        f"<div style='color:#555;font-size:11px;'>Raised: {ico['raised']}</div>"
        f"</div>"
        f"<div style='background:rgba(0,0,0,0.45);padding:11px;border-radius:9px;border:1px solid #1e1e1e;'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:4px;'>SCORE</div>"
        f"<div style='color:{cor};font-size:15px;font-weight:bold;'>{ico['score']}</div>"
        f"<div style='color:#FFD700;font-size:11px;'>{estrelas[:10]}</div>"
        f"</div>"
        f"</div>"

        f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:10px;'>"
        f"<div style='background:rgba(0,0,0,0.45);padding:11px;border-radius:9px;border:1px solid #1e1e1e;'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:4px;'>PLATAFORMAS</div>"
        f"<div style='color:#00FFFF;font-size:13px;'>{ico['plataformas']}</div>"
        f"</div>"
        f"<div style='background:rgba(0,0,0,0.45);padding:11px;border-radius:9px;border:1px solid #1e1e1e;'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:4px;'>BACKERS</div>"
        f"<div style='color:#FFD700;font-size:13px;'>{ico['backers']}</div>"
        f"</div>"
        f"<div style='background:rgba(0,0,0,0.45);padding:11px;border-radius:9px;border:1px solid #1e1e1e;'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:4px;'>UNLOCK / VESTING</div>"
        f"<div style='color:#FF8C00;font-size:13px;'>{ico['unlock']}</div>"
        f"</div>"
        f"</div>"

        f"<div style='display:grid;grid-template-columns:2fr 1fr;gap:10px;margin-bottom:14px;'>"
        f"<div style='background:rgba(0,0,0,0.45);padding:13px;border-radius:9px;border-left:3px solid {cor};'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:6px;'>ANALISE FUNDAMENTALISTA</div>"
        f"<div style='color:#CCCCCC;font-size:13px;line-height:1.55;'>{ico['descricao']}</div>"
        f"</div>"
        f"<div style='background:rgba(0,0,0,0.45);padding:13px;border-radius:9px;border:1px solid #1e1e1e;text-align:center;'>"
        f"<div style='color:#777;font-size:10px;text-transform:uppercase;margin-bottom:6px;'>ROI ALVO</div>"
        f"<div style='color:#00FF00;font-size:26px;font-weight:900;margin:6px 0;'>{ico['roi_alvo']}</div>"
        f"<div style='color:#555;font-size:11px;'>sobre R$400 investidos</div>"
        f"</div>"
        f"</div>"

        f"<a href='{ico['link']}' target='_blank' class='link-btn'>{botao_texto}</a>"
        f"<a href='{ico['link_info']}' target='_blank' class='link-btn-green'>🔍 PESQUISAR PROJETO</a>"
        f"{tag_enc}"
        f"</div>"
    )

st.set_page_config(layout="wide", page_title="THANOS v5.5 - MAXIMUM", page_icon="💎")

if "logado" not in st.session_state:
    st.markdown("<h1 style='text-align:center;color:#FFD700;font-size:36px;'>🛡️ ACESSO RESTRITO</h1>", unsafe_allow_html=True)
    senha = st.text_input("Senha da Manopla:", type="password")
    if senha == "thanos2025":
        st.session_state.logado = True
        st.rerun()
    st.stop()

@st.cache_data(ttl=30)
def carregar_mercado():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&sparkline=true&price_change_percentage=1h,24h,7d"
    try:
        r = requests.get(url, timeout=15)
        df = pd.DataFrame(r.json())
        colunas = ['image','symbol','name','current_price','price_change_percentage_24h','market_cap','total_volume','atl','atl_date','sparkline_in_7d','market_cap_rank']
        for col in colunas:
            if col not in df.columns: df[col] = None
        df['sparkline_7d_clean'] = df['sparkline_in_7d'].apply(lambda x: x.get('price', []) if isinstance(x, dict) else [])
        df['whale_activity'] = (df['total_volume'].fillna(0) / df['market_cap'].replace(0,1).fillna(1) * 100).fillna(0)
        df['data_listagem'] = pd.to_datetime(df['atl_date'], errors='coerce').dt.strftime('%d/%m/%Y')
        return df.fillna(0)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=180)
def carregar_icos():
    icos_fixos = [
        {
            "projeto": "idOS Network", "token": "IDOS", "tipo": "TGE / CCA",
            "tge_dt": datetime(2026, 3, 5, 12, 0, 0, tzinfo=timezone.utc),
            "tge_str": "05/03/2026", "hora_brt": "09:00 BRT",
            "preco": "$0.039", "preco_listing": "$0.065 (estimado)",
            "plataformas": "Tally.xyz, Arbitrum, Ethereum",
            "backers": "Circle (USDC), Ripple (XRP), Arbitrum Foundation, Fabric Ventures",
            "fdv": "$39M", "score": "8/10", "unlock": "100% no TGE (Fase 2)",
            "raised": "$769k / $1M", "categoria": "Identidade Web3 / DeFi / KYC",
            "descricao": "Sistema operacional de identidade descentralizada. KYC portavel em 40+ chains. Infraestrutura para neobancos crypto e conformidade DeFi global.",
            "risco": "BAIXO", "roi_alvo": "3X-10X",
            "link": "https://www.tally.xyz/sale/idos", "link_info": "https://icodrops.com/idos/"
        },
        {
            "projeto": "Power Protocol", "token": "POWER", "tipo": "Token Unlock",
            "tge_dt": datetime(2026, 3, 5, 14, 0, 0, tzinfo=timezone.utc),
            "tge_str": "05/03/2026", "hora_brt": "11:00 BRT",
            "preco": "$0.91", "preco_listing": "$0.85 (pressao venda)",
            "plataformas": "Binance, MEXC, KuCoin", "backers": "A confirmar",
            "fdv": "$91M", "score": "5/10", "unlock": "$23M desbloqueado (2.5% supply)",
            "raised": "N/A", "categoria": "DeFi / Infra",
            "descricao": "Unlock massivo de tokens. Alta probabilidade de pressao de venda imediata. Monitorar para short.",
            "risco": "ALTO", "roi_alvo": "Negativo (short oportunidade)",
            "link": "https://coinmarketcap.com", "link_info": "https://coinmarketcap.com"
        },
        {
            "projeto": "Kaito AI", "token": "KAITO", "tipo": "TGE / IDO",
            "tge_dt": datetime(2026, 3, 12, 14, 0, 0, tzinfo=timezone.utc),
            "tge_str": "12/03/2026", "hora_brt": "11:00 BRT",
            "preco": "$0.15 (estimado)", "preco_listing": "$0.40 (estimado)",
            "plataformas": "Binance Launchpad, Uniswap", "backers": "Binance Labs, a16z crypto",
            "fdv": "$150M", "score": "9/10", "unlock": "20% no TGE, 80% vesting 12m",
            "raised": "$10M Series A", "categoria": "IA / Crypto Intelligence / DeFi",
            "descricao": "Plataforma de inteligencia artificial para analise de narrativas crypto. Indexa dados do X (Twitter) e mede influencia de projetos. Narrativa AI+Crypto explosiva 2026.",
            "risco": "MEDIO", "roi_alvo": "5X-15X",
            "link": "https://binance.com/launchpad", "link_info": "https://icodrops.com"
        },
        {
            "projeto": "Humanity Protocol", "token": "RWT", "tipo": "TGE / Public Sale",
            "tge_dt": datetime(2026, 3, 18, 16, 0, 0, tzinfo=timezone.utc),
            "tge_str": "18/03/2026", "hora_brt": "13:00 BRT",
            "preco": "$0.012", "preco_listing": "$0.05 (estimado)",
            "plataformas": "Gate.io, MEXC, Uniswap V3",
            "backers": "Polygon, OKX Ventures, Samsung Next",
            "fdv": "$12M", "score": "8/10", "unlock": "100% no TGE",
            "raised": "$30M total", "categoria": "Identidade / Proof of Humanity / Web3",
            "descricao": "Prova de humanidade via palmeira biometrica. Competidor direto do Worldcoin. Samsung + OKX = listagens garantidas. FDV $12M vs Worldcoin $2B = upside gigante.",
            "risco": "MEDIO", "roi_alvo": "5X-25X",
            "link": "https://gate.io", "link_info": "https://humanityprotocol.com"
        },
        {
            "projeto": "Nillion Network", "token": "NIL", "tipo": "TGE / Airdrop + Sale",
            "tge_dt": datetime(2026, 3, 25, 15, 0, 0, tzinfo=timezone.utc),
            "tge_str": "25/03/2026", "hora_brt": "12:00 BRT",
            "preco": "$0.35 (seed)", "preco_listing": "$0.80 (estimado)",
            "plataformas": "Binance, Coinbase, Kraken", "backers": "a16z, Coinbase Ventures, HashKey",
            "fdv": "$350M", "score": "9/10", "unlock": "15% TGE, vesting 18m",
            "raised": "$25M", "categoria": "Privacy / Compute / AI",
            "descricao": "Computacao cega descentralizada. Processa dados sensiveis sem revelar o conteudo. Parceiros: MetaMask, Uniswap. a16z como backer principal = credibilidade maxima.",
            "risco": "BAIXO", "roi_alvo": "3X-8X",
            "link": "https://binance.com", "link_info": "https://nillion.com"
        }
    ]
    return sorted(icos_fixos, key=lambda x: x.get("tge_dt") or datetime.max.replace(tzinfo=timezone.utc))

df = carregar_mercado()

st.markdown("""
<style>
body, .stApp { background-color: #000 !important; }
[data-testid="stSidebar"] { background: #050505 !important; border-right: 2px solid #8A2BE2; }
* { font-family: 'Consolas', monospace !important; }
.stApp > header { color: #00FF00 !important; }
section[data-testid="stSidebar"] * { color: #00FF00 !important; }
.thanos-title { text-align:center; font-size:60px; font-weight:bold; color:#FFD700 !important; text-shadow:0 0 30px #8A2BE2; }
.link-btn { display:inline-block; padding:9px 18px; background:#8A2BE2; color:#FFF !important; text-decoration:none; border-radius:6px; font-weight:bold; margin:5px 5px 0 0; font-size:13px; }
.link-btn-green { display:inline-block; padding:9px 18px; background:#006600; color:#FFF !important; text-decoration:none; border-radius:6px; font-weight:bold; margin:5px 5px 0 0; font-size:13px; }
.premium-card { background:#0a0a0a; border:1px solid #FFD700; padding:20px; border-radius:15px; margin-bottom:15px; box-shadow:0 0 15px rgba(138,43,226,0.5); }
.metric-card { background:#0a0a0a; border:2px solid #FFD700; padding:25px; border-radius:15px; text-align:center; margin-top:10px; }
.step-box { border-left:3px solid #00FFFF; padding-left:15px; margin-top:10px; }
</style>
""", unsafe_allow_html=True)

config_visual = {
    "image": st.column_config.ImageColumn("ICON"),
    "current_price": st.column_config.NumberColumn("PRECO", format="$%.8f"),
    "sparkline_7d_clean": st.column_config.LineChartColumn("7 DIAS"),
    "whale_activity": st.column_config.ProgressColumn("BALEIA", min_value=0, max_value=50),
}

with st.sidebar:
    st.markdown("<h2 style='color:#FFD700;'>🛡️ MANOPLA</h2>", unsafe_allow_html=True)
    if st.button("🚀 TESTAR TELEGRAM"):
        ok = enviar_alerta("🔥 *THANOS v5.5 ONLINE!*\nSistema de monitoramento ICO ativo.")
        st.success("Telegram OK!") if ok else st.error("Falhou!")
    st.divider()
    f_p = st.slider("PRECO MAX ($)", 0.0, 1.0, 0.10, step=0.01)
    f_w = st.slider("VOL/MCAP MIN (%)", 0, 100, 5)
    st.divider()
    if st.button("🔄 REFRESH TOTAL"):
        st.cache_data.clear()
        st.rerun()
    st.markdown(f"<small style='color:#555;'>Atualizado: {datetime.now().strftime('%H:%M:%S')}</small>", unsafe_allow_html=True)

st.markdown("<div class='thanos-title'>💎 THANOS v5.5 💎</div>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;color:#555;'>Mercado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S BRT')}</p>", unsafe_allow_html=True)

t1, t2, t3, t4, t5, t6, t7 = st.tabs([
    "🌌 UNIVERSO", "🚀 SNIPER 100x", "🐋 BALEIAS",
    "🆕 LISTAGENS", "🔮 SIMULADOR", "🎯 ICO RADAR", "📖 MANUAL"
])

with t1:
    if not df.empty:
        cols = [c for c in ['image','market_cap_rank','name','symbol','current_price','price_change_percentage_24h'] if c in df.columns]
        st.data_editor(df[cols], column_config=config_visual, hide_index=True, use_container_width=True)
    else:
        st.warning("Dados do mercado indisponiveis.")

with t2:
    if not df.empty:
        df_f = df[(df['current_price'].fillna(999) <= f_p) & (df['whale_activity'].fillna(0) >= f_w)]
        cols = [c for c in ['image','symbol','current_price','sparkline_7d_clean','whale_activity'] if c in df_f.columns]
        st.data_editor(df_f[cols], column_config=config_visual, hide_index=True, use_container_width=True)
    else:
        st.warning("Dados indisponiveis.")

with t3:
    if not df.empty:
        cols = [c for c in ['name','symbol','total_volume','whale_activity'] if c in df.columns]
        st.dataframe(df.sort_values('whale_activity', ascending=False).head(50)[cols], use_container_width=True)
    else:
        st.warning("Dados indisponiveis.")

with t4:
    if not df.empty:
        df_new = df.sort_values(by='atl_date', ascending=False).head(50)
        cols = [c for c in ['image','name','symbol','data_listagem','current_price'] if c in df_new.columns]
        st.data_editor(df_new[cols], column_config=config_visual, hide_index=True, use_container_width=True)
    else:
        st.warning("Dados indisponiveis.")

with t5:
    st.subheader("🔮 Simulador de Lucro Historico")
    if not df.empty:
        with st.form("sim_form"):
            c1, c2 = st.columns(2)
            with c1: m_sim = st.selectbox("Moeda:", df['name'].tolist())
            with c2: v_sim = st.number_input("Investir ($):", value=100.0)
            if st.form_submit_button("🚀 SIMULAR"):
                d = df[df['name'] == m_sim].iloc[0]
                atl = float(d['atl']) if float(d['atl']) > 0 else 0.0001
                res = (v_sim / atl) * float(d['current_price'])
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<h1 style='color:#00FF00;font-size:48px;margin:0;'>${res:,.2f}</h1>"
                    f"<p style='color:#888;margin:8px 0 0;'>ATL: ${atl:.8f} | Data: {d['data_listagem']}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )

with t6:
    st.markdown(
        "<div style='text-align:center;padding:10px 0 5px;'>"
        "<span style='color:#FFD700;font-size:28px;font-weight:900;letter-spacing:2px;'>"
        "🎯 ICO RADAR — CENTRAL DE LANCAMENTOS"
        "</span></div>",
        unsafe_allow_html=True
    )

    hoje_utc = datetime.now(timezone.utc)
    icos = carregar_icos()

    total       = len(icos)
    hoje_count  = sum(1 for i in icos if i.get("tge_dt") and i["tge_dt"].date() == hoje_utc.date())
    urgentes    = sum(1 for i in icos if calcular_tempo(i.get("tge_dt"))[1] in ["critico","urgente"])
    finalizados = sum(1 for i in icos if calcular_tempo(i.get("tge_dt"))[1] == "finalizado")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total ICOs", total, "monitorados")
    m2.metric("Hoje", hoje_count, "lancamentos")
    m3.metric("Urgentes", urgentes, "proximas 24h")
    m4.metric("Finalizados", finalizados, "hoje")
    st.divider()

    checar_e_alertar_icos(icos)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: data_inicio = st.date_input("De:", value=hoje_utc.date())
    with col2: data_fim    = st.date_input("Ate:", value=hoje_utc.date() + timedelta(days=30))
    with col3:
        filtro_status = st.multiselect("Status:",
            ["finalizado","critico","urgente","normal"],
            default=["finalizado","critico","urgente","normal"])
    with col4:
        filtro_risco = st.multiselect("Risco:",
            ["BAIXO","MEDIO","ALTO"],
            default=["BAIXO","MEDIO","ALTO"])
    with col5:
        auto_refresh = st.toggle("Auto Refresh", value=True)
        if st.button("📨 Alertar Urgentes"):
            for ico in icos:
                _, s = calcular_tempo(ico.get("tge_dt"))
                if s in ["critico","urgente"]:
                    enviar_alerta(
                        f"🚨 *{ico['projeto']} ({ico['token']})*\n"
                        f"⏰ {formatar_tempo(calcular_tempo(ico.get('tge_dt'))[0])}\n"
                        f"💵 {ico['preco']} | Score: {ico['score']}\n"
                        f"🔗 {ico['link']}"
                    )
            st.success("Alertas enviados!")

    st.divider()

    encontrou  = False
    numero_ico = 0

    for ico in icos:
        _, status = calcular_tempo(ico.get("tge_dt"))
        tge_dt = ico.get("tge_dt")
        if tge_dt and not (data_inicio <= tge_dt.date() <= data_fim): continue
        if status not in filtro_status: continue
        if ico.get("risco","MEDIO") not in filtro_risco: continue

        encontrou  = True
        numero_ico += 1
        st.markdown(render_ico_card(ico, numero_ico), unsafe_allow_html=True)

    if not encontrou:
        st.markdown(
            f"<div style='text-align:center;padding:60px;border:2px dashed #333;border-radius:15px;'>"
            f"<div style='color:#555;font-size:28px;'>📭 Nenhum ICO encontrado</div>"
            f"<div style='color:#444;margin-top:10px;'>Periodo: {data_inicio} ate {data_fim}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.divider()
    st.markdown(
        "<div style='background:linear-gradient(135deg,#050505,#0a0500);border:2px solid #FFD700;padding:25px;border-radius:15px;'>"
        "<div style='color:#FFD700;font-size:18px;font-weight:bold;text-align:center;margin-bottom:18px;'>💡 POR QUE ICOs MULTIPLICAM CAPITAL?</div>"
        "<div style='display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:20px;'>"
        "<div style='border-left:3px solid #00FF00;padding-left:12px;'>"
        "<div style='color:#00FF00;font-weight:bold;margin-bottom:5px;'>ENTRADA ANTECIPADA</div>"
        "<div style='color:#AAA;font-size:12px;'>Preco TGE sempre menor que listing.</div>"
        "</div>"
        "<div style='border-left:3px solid #FFD700;padding-left:12px;'>"
        "<div style='color:#FFD700;font-weight:bold;margin-bottom:5px;'>BACKERS = LISTING</div>"
        "<div style='color:#AAA;font-size:12px;'>a16z garantem listagens Binance/Coinbase.</div>"
        "</div>"
        "<div style='border-left:3px solid #00FFFF;padding-left:12px;'>"
        "<div style='color:#00FFFF;font-weight:bold;margin-bottom:5px;'>FDV BAIXO = UPSIDE</div>"
        "<div style='color:#AAA;font-size:12px;'>FDV $39M vs Worldcoin $2B = 50x room.</div>"
        "</div>"
        "<div style='border-left:3px solid #FF8C00;padding-left:12px;'>"
        "<div style='color:#FF8C00;font-weight:bold;margin-bottom:5px;'>ROI R$400</div>"
        "<div style='color:#AAA;font-size:12px;'>x$1.00 = R$10.000 (25X)</div>"
        "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    if auto_refresh:
        time.sleep(30)
        st.rerun()

with t7:
    st.markdown("<div style='color:#FFD700;font-size:22px;font-weight:bold;margin-bottom:15px;'>📖 Manual Estrategico Premium</div>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        st.markdown(
            "<div class='premium-card'>"
            "<div style='color:#FFD700;font-size:16px;font-weight:bold;margin-bottom:12px;'>🛰️ Caca-Lancamentos</div>"
            "<a href='https://daomaker.com/' class='link-btn'>DAO Maker</a>"
            "<a href='https://seedify.fund/' class='link-btn'>Seedify</a>"
            "<a href='https://jup.ag/' class='link-btn'>Jupiter</a>"
            "<a href='https://icodrops.com' class='link-btn'>ICO Drops</a>"
            "<div class='step-box' style='margin-top:12px;'>"
            "<span style='color:#00FFFF;font-weight:bold;'>Dica:</span>"
            "<span style='color:#AAA;'> Monitore #TGE e #MainnetLaunch no X.</span>"
            "</div></div>"
            "<div class='premium-card'>"
            "<div style='color:#FFD700;font-size:16px;font-weight:bold;margin-bottom:12px;'>📊 Analise Social</div>"
            "<a href='https://lunarcrush.com/' class='link-btn'>LunarCrush</a>"
            "<a href='https://coinmarketcal.com' class='link-btn'>CoinMarketCal</a>"
            "</div>",
            unsafe_allow_html=True
        )
    with cb:
        st.markdown(
            "<div class='premium-card'>"
            "<div style='color:#FFD700;font-size:16px;font-weight:bold;margin-bottom:12px;'>🛡️ Seguranca Anti-Rugpull</div>"
            "<a href='https://tokensniffer.com/' class='link-btn'>Token Sniffer</a>"
            "<a href='https://dexscreener.com/' class='link-btn'>DEX Screener</a>"
            "<div class='step-box' style='margin-top:12px;'>"
            "<span style='color:#AAA;'>Verifique liquidez travada e honeypot antes de comprar.</span>"
            "</div></div>"
            "<div class='premium-card'>"
            "<div style='color:#FFD700;font-size:16px;font-weight:bold;margin-bottom:12px;'>⚖️ Regras Sniper</div>"
            "<ul style='color:#AAA;padding-left:18px;margin:0;'>"
            "<li>Nunca entre apos pump +100% no dia</li>"
            "<li>FDV abaixo de $50M = oportunidade</li>"
            "<li>Backers tier-1 = listagem garantida</li>"
            "<li>100% unlock TGE = sem pressao vesting</li>"
            "</ul></div>",
            unsafe_allow_True=True
        )
