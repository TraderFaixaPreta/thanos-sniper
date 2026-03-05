import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import time

TOKEN_TELEGRAM = "8262824397:AAERAJr6Epu2UvUPlOeLvJ2VJlB19o9c-xo"
MEU_ID_TELEGRAM = "1007733041"
alertas_enviados = set()

def enviar_alerta(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": MEU_ID_TELEGRAM, "text": mensagem, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except:
        return False

def checar_e_alertar_icos(icos):
    global alertas_enviados
    for ico in icos:
        delta, status = calcular_tempo(ico.get("tge_dt"))
        chave = f"{ico['token']}_{status}"
        if chave in alertas_enviados:
            continue
        if status == "critico":
            msg = (
                f"🔴 *ALERTA CRITICO - ICO EM MENOS DE 1H!*\n\n"
                f"🚀 *{ico['projeto']} ({ico['token']})*\n"
                f"⏰ Faltam: {formatar_tempo(delta)}\n"
                f"💵 Preco: {ico['preco']}\n"
                f"🌐 Plataforma: {ico['plataformas']}\n"
                f"💰 Backers: {ico['backers']}\n"
                f"📊 FDV: {ico['fdv']} | Score: {ico['score']}\n"
                f"🔗 {ico['link']}"
            )
            if enviar_alerta(msg):
                alertas_enviados.add(chave)
        elif status == "urgente":
            msg = (
                f"🟠 *ALERTA - ICO HOJE!*\n\n"
                f"🚀 *{ico['projeto']} ({ico['token']})*\n"
                f"⏰ Faltam: {formatar_tempo(delta)}\n"
                f"💵 Preco: {ico['preco']}\n"
                f"🌐 Plataforma: {ico['plataformas']}\n"
                f"💰 Backers: {ico['backers']}\n"
                f"📊 FDV: {ico['fdv']} | Score: {ico['score']}\n"
                f"🔗 {ico['link']}"
            )
            if enviar_alerta(msg):
                alertas_enviados.add(chave)

st.set_page_config(layout="wide", page_title="THANOS v5.5 - MAXIMUM", page_icon="💎")

if "logado" not in st.session_state:
    st.markdown("<h1 style='text-align:center;color:#FFD700;'>🛡️ ACESSO RESTRITO</h1>", unsafe_allow_html=True)
    senha = st.text_input("Senha da Manopla:", type="password")
    if senha == "thanos2025":
        st.session_state.logado = True
        st.rerun()
    st.stop()

# ✅ CORRIGIDO: carregar_mercado com colunas seguras
@st.cache_data(ttl=30)
def carregar_mercado():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&sparkline=true&price_change_percentage=1h,24h,7d"
    try:
        r = requests.get(url, timeout=15)
        df = pd.DataFrame(r.json())
        colunas_necessarias = [
            'image', 'symbol', 'name', 'current_price',
            'price_change_percentage_24h', 'market_cap',
            'total_volume', 'atl', 'atl_date', 'sparkline_in_7d',
            'market_cap_rank'
        ]
        for col in colunas_necessarias:
            if col not in df.columns:
                df[col] = None
        df['sparkline_7d_clean'] = df['sparkline_in_7d'].apply(
            lambda x: x.get('price', []) if isinstance(x, dict) else []
        )
        df['whale_activity'] = (
            df['total_volume'].fillna(0) /
            df['market_cap'].replace(0, 1).fillna(1) * 100
        ).fillna(0)
        df['data_listagem'] = pd.to_datetime(
            df['atl_date'], errors='coerce'
        ).dt.strftime('%d/%m/%Y')
        return df.fillna(0)
    except Exception as e:
        st.error(f"Erro ao carregar mercado: {e}")
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
            "link": "https://www.tally.xyz/sale/idos",
            "link_info": "https://icodrops.com/idos/", "status_manual": "Finalizado"
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
            "link": "https://coinmarketcap.com",
            "link_info": "https://coinmarketcap.com", "status_manual": "Upcoming"
        },
        {
            "projeto": "Kaito AI", "token": "KAITO", "tipo": "TGE / IDO",
            "tge_dt": datetime(2026, 3, 12, 14, 0, 0, tzinfo=timezone.utc),
            "tge_str": "12/03/2026", "hora_brt": "11:00 BRT",
            "preco": "$0.15 (estimado)", "preco_listing": "$0.40 (estimado)",
            "plataformas": "Binance Launchpad, Uniswap",
            "backers": "Binance Labs, a16z crypto",
            "fdv": "$150M", "score": "9/10", "unlock": "20% no TGE, 80% vesting 12m",
            "raised": "$10M Series A", "categoria": "IA / Crypto Intelligence / DeFi",
            "descricao": "Plataforma de inteligencia artificial para analise de narrativas crypto. Indexa dados do X (Twitter) e mede influencia de projetos. Narrativa AI+Crypto = explosiva 2026.",
            "risco": "MEDIO", "roi_alvo": "5X-15X",
            "link": "https://binance.com/launchpad",
            "link_info": "https://icodrops.com", "status_manual": "Upcoming"
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
            "descricao": "Prova de humanidade via palmeira (biometria). Competidor direto do Worldcoin. Samsung + OKX = listagens garantidas. FDV $12M vs Worldcoin $2B = upside gigante.",
            "risco": "MEDIO", "roi_alvo": "5X-25X",
            "link": "https://gate.io",
            "link_info": "https://humanityprotocol.com", "status_manual": "Upcoming"
        },
        {
            "projeto": "Nillion Network", "token": "NIL", "tipo": "TGE / Airdrop + Sale",
            "tge_dt": datetime(2026, 3, 25, 15, 0, 0, tzinfo=timezone.utc),
            "tge_str": "25/03/2026", "hora_brt": "12:00 BRT",
            "preco": "$0.35 (seed)", "preco_listing": "$0.80 (estimado)",
            "plataformas": "Binance, Coinbase, Kraken",
            "backers": "a16z, Coinbase Ventures, HashKey",
            "fdv": "$350M", "score": "9/10", "unlock": "15% TGE, vesting 18m",
            "raised": "$25M", "categoria": "Privacy / Compute / AI",
            "descricao": "Computacao cega descentralizada. Processa dados sensiveis sem revelar o conteudo. Parceiros: MetaMask, Uniswap. a16z como backer principal = credibilidade maxima.",
            "risco": "BAIXO", "roi_alvo": "3X-8X",
            "link": "https://binance.com",
            "link_info": "https://nillion.com", "status_manual": "Upcoming"
        },
    ]
    try:
        r = requests.get(
            "https://coinmarketcal.com/api/events?dateRangeStart=" +
            datetime.now().strftime("%m/%d/%Y") +
            "&dateRangeEnd=" +
            (datetime.now() + timedelta(days=30)).strftime("%m/%d/%Y") +
            "&categories=TGE,ICO,IDO&max=20", timeout=8
        )
        if r.status_code == 200:
            for ev in r.json().get("body", {}).get("items", [])[:5]:
                try:
                    tge_dt = datetime.strptime(ev.get("date_event","")[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    token_sym = ev.get("coins",[{}])[0].get("symbol","???") if ev.get("coins") else "???"
                    if token_sym not in [i["token"] for i in icos_fixos]:
                        icos_fixos.append({
                            "projeto": ev.get("title","N/A"), "token": token_sym,
                            "tipo": "TGE/ICO", "tge_dt": tge_dt,
                            "tge_str": tge_dt.strftime("%d/%m/%Y"), "hora_brt": "A confirmar",
                            "preco": "A confirmar", "preco_listing": "A confirmar",
                            "plataformas": "A confirmar", "backers": "A confirmar",
                            "fdv": "A confirmar", "score": "N/A", "unlock": "A confirmar",
                            "raised": "A confirmar", "categoria": "A confirmar",
                            "descricao": ev.get("description","N/A")[:200],
                            "risco": "MEDIO", "roi_alvo": "A confirmar",
                            "link": ev.get("source","#"), "link_info": ev.get("source","#"),
                            "status_manual": "Upcoming"
                        })
                except:
                    pass
    except:
        pass
    return sorted(icos_fixos, key=lambda x: x.get("tge_dt") or datetime.max.replace(tzinfo=timezone.utc))

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
    return {"critico":"#FF0000","urgente":"#FF8C00","normal":"#00FF00","finalizado":"#666666","unknown":"#444444"}.get(status,"#00FF00")

def badge_status(status):
    return {"critico":"🔴 CRITICO - MENOS DE 1H","urgente":"🟠 URGENTE - HOJE","normal":"🟢 UPCOMING","finalizado":"⚫ FINALIZADO","unknown":"⚪ A CONFIRMAR"}.get(status,"🟢 UPCOMING")

def cor_risco(risco):
    return {"BAIXO":"#00FF00","MEDIO":"#FF8C00","ALTO":"#FF0000"}.get(risco,"#FFF")

def estrelas_score(score_str):
    try:
        n = int(score_str.split("/")[0])
        return "★" * n + "☆" * (10 - n)
    except:
        return score_str

df = carregar_mercado()

st.markdown("""
<style>
.stApp{background:#000;color:#00FF00;}
[data-testid="stSidebar"]{background:#050505!important;border-right:2px solid #8A2BE2;}
h1,h2,h3,p,span,label,div{color:#00FF00!important;font-family:'Consolas',monospace;}
.thanos-title{text-align:center;font-size:60px;font-weight:bold;color:#FFD700!important;text-shadow:0 0 30px #8A2BE2;}
.premium-card{background:#0a0a0a;border:1px solid #FFD700;padding:20px;border-radius:15px;margin-bottom:15px;box-shadow:0 0 15px rgba(138,43,226,0.5);}
.link-button{display:inline-block;padding:8px 15px;background:#8A2BE2;color:white!important;text-decoration:none;border-radius:5px;font-weight:bold;margin:5px 5px 0 0;}
.link-button-green{display:inline-block;padding:8px 15px;background:#006600;color:white!important;text-decoration:none;border-radius:5px;font-weight:bold;margin:5px 5px 0 0;}
.metric-card{background:#0a0a0a;border:2px solid #FFD700;padding:25px;border-radius:15px;text-align:center;margin-top:10px;}
.step-box{border-left:3px solid #00FFFF;padding-left:15px;margin-top:10px;}
.countdown-big{font-size:32px;font-weight:bold;font-family:'Consolas',monospace;letter-spacing:2px;}
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

# ✅ CORRIGIDO t1 - colunas seguras
with t1:
    cols_t1 = [c for c in ['image','market_cap_rank','name','symbol','current_price','price_change_percentage_24h'] if c in df.columns]
    if not df.empty:
        st.data_editor(df[cols_t1], column_config=config_visual, hide_index=True, use_container_width=True)
    else:
        st.warning("Dados do mercado indisponiveis.")

# ✅ CORRIGIDO t2
with t2:
    if not df.empty:
        df_f = df[(df['current_price'].fillna(999) <= f_p) & (df['whale_activity'].fillna(0) >= f_w)]
        cols_t2 = [c for c in ['image','symbol','current_price','sparkline_7d_clean','whale_activity'] if c in df_f.columns]
        st.data_editor(df_f[cols_t2], column_config=config_visual, hide_index=True, use_container_width=True)

# ✅ CORRIGIDO t3
with t3:
    if not df.empty:
        cols_t3 = [c for c in ['name','symbol','total_volume','whale_activity'] if c in df.columns]
        st.dataframe(df.sort_values('whale_activity', ascending=False).head(50)[cols_t3], use_container_width=True)

# ✅ CORRIGIDO t4
with t4:
    if not df.empty:
        df_new = df.sort_values(by='atl_date', ascending=False).head(50)
        cols_t4 = [c for c in ['image','name','symbol','data_listagem','current_price'] if c in df_new.columns]
        st.data_editor(df_new[cols_t4], column_config=config_visual, hide_index=True, use_container_width=True)

with t5:
    st.subheader("🔮 Simulador de Lucro Historico")
    if not df.empty:
        with st.form("sim_form"):
            c1, c2 = st.columns(2)
            with c1: m_sim = st.selectbox("Moeda:", df['name'].tolist())
            with c2: v_sim = st.number_input("Investir ($):", value=100.0)
            if st.form_submit_button("🚀 SIMULAR"):
                d = df[df['name'] == m_sim].iloc[0]
                atl = float(d['atl']) if float(str(d['atl']).replace('0','1') or 1) != 0 else 0.0001
                res = (v_sim / atl) * float(d['current_price'])
                st.markdown(f"""
                <div class='metric-card'>
                    <h1 style='color:#00FF00;'>${res:,.2f}</h1>
                    <p>ATL: ${atl:.8f} | Data: {d['data_listagem']}</p>
                </div>""", unsafe_allow_html=True)

with t6:
    st.markdown("<h2 style='color:#FFD700;text-align:center;'>🎯 ICO RADAR - CENTRAL DE LANCAMENTOS</h2>", unsafe_allow_html=True)
    hoje_utc = datetime.now(timezone.utc)
    icos = carregar_icos()
    total = len(icos)
    hoje_count = sum(1 for i in icos if i.get("tge_dt") and i["tge_dt"].date() == hoje_utc.date())
    urgentes = sum(1 for i in icos if calcular_tempo(i.get("tge_dt"))[1] in ["critico","urgente"])
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
    with col2: data_fim = st.date_input("Ate:", value=hoje_utc.date() + timedelta(days=30))
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
    encontrou = False
    for ico in icos:
        delta, status = calcular_tempo(ico.get("tge_dt"))
        tge_dt = ico.get("tge_dt")
        if tge_dt and not (data_inicio <= tge_dt.date() <= data_fim): continue
        if status not in filtro_status: continue
        if ico.get("risco","MEDIO") not in filtro_risco: continue

        encontrou = True
        cor = cor_status(status)
        badge = badge_status(status)
        tempo_str = formatar_tempo(delta)
        hora_utc = tge_dt.strftime("%H:%M UTC") if tge_dt else "N/A"
        hora_brt = ico.get("hora_brt","N/A")
        c_risco = cor_risco(ico.get("risco","MEDIO"))
        estrelas = estrelas_score(ico.get("score","N/A"))
        bg_map = {
            "critico":   "background:linear-gradient(135deg,#1a0000,#0d0000);border:2px solid #FF0000;box-shadow:0 0 30px #FF000066;",
            "urgente":   "background:linear-gradient(135deg,#1a0800,#0d0500);border:2px solid #FF8C00;box-shadow:0 0 25px #FF8C0066;",
            "normal":    "background:linear-gradient(135deg,#001a00,#000d00);border:2px solid #00FF00;box-shadow:0 0 20px #00FF0033;",
            "finalizado":"background:#0a0a0a;border:2px solid #333;opacity:0.75;"
        }
        bg_style = bg_map.get(status, bg_map["normal"])
        botao_comprar = "ENCERRADO" if status == "finalizado" else "COMPRAR AGORA"
        tag_encerrado = (
            f"<span style='background:#FF000033;color:#FF0000;padding:8px 15px;"
            f"border-radius:5px;font-size:13px;font-weight:bold;margin-left:5px;"
            f"border:1px solid #FF0000;'>VENDA ENCERRADA - {hora_brt}</span>"
            if status == "finalizado" else ""
        )

        st.markdown(f"""
        <div style='{bg_style} padding:25px;border-radius:18px;margin-bottom:20px;'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;'>
                <div>
                    <span style='color:{cor};font-size:24px;font-weight:bold;'>{ico["projeto"]}</span>
                    <span style='background:#1a1a1a;color:{cor};padding:4px 12px;border-radius:20px;font-size:13px;font-weight:bold;margin-left:10px;border:1px solid {cor};'>{ico["token"]}</span>
                    <span style='background:{cor}22;color:{cor};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:bold;margin-left:8px;'>{badge}</span>
                    <span style='background:{c_risco}22;color:{c_risco};padding:4px 10px;border-radius:20px;font-size:11px;margin-left:8px;border:1px solid {c_risco};'>Risco: {ico.get("risco","N/A")}</span>
                </div>
                <div style='text-align:right;'>
                    <div class='countdown-big' style='color:{cor};'>{tempo_str}</div>
                    <div style='color:#888;font-size:13px;'>{hora_brt} | {hora_utc}</div>
                </div>
            </div>
            <hr style='border:none;border-top:1px solid {cor}33;margin:15px 0;'>
            <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:15px;'>
                <div style='background:#00000066;padding:12px;border-radius:10px;border:1px solid #333;'>
                    <p style='color:#888;font-size:11px;margin:0;'>TIPO</p>
                    <p style='color:#FFF;font-size:14px;font-weight:bold;margin:3px 0;'>{ico["tipo"]}</p>
                </div>
                <div style='background:#00000066;padding:12px;border-radius:10px;border:1px solid #333;'>
                    <p style='color:#888;font-size:11px;margin:0;'>PRECO TGE</p>
                    <p style='color:#00FF00;font-size:14px;font-weight:bold;margin:3px 0;'>{ico["preco"]}</p>
                    <p style='color:#555;font-size:11px;margin:0;'>Listing: {ico["preco_listing"]}</p>
                </div>
                <div style='background:#00000066;padding:12px;border-radius:10px;border:1px solid #333;'>
                    <p style='color:#888;font-size:11px;margin:0;'>FDV</p>
                    <p style='color:#FFD700;font-size:14px;font-weight:bold;margin:3px 0;'>{ico["fdv"]}</p>
                    <p style='color:#555;font-size:11px;margin:0;'>Raised: {ico["raised"]}</p>
                </div>
                <div style='background:#00000066;padding:12px;border-radius:10px;border:1px solid #333;'>
                    <p style='color:#888;font-size:11px;margin:0;'>SCORE</p>
                    <p style='color:{cor};font-size:14px;font-weight:bold;margin:3px 0;'>{ico["score"]}</p>
                    <p style='color:#FFD700;font-size:11px;margin:0;'>{estrelas[:10]}</p>
                </div>
            </div>
            <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-bottom:15px;'>
                <div style='background:#00000066;padding:12px;border-radius:10px;border:1px solid #333;'>
                    <p style='color:#888;font-size:11px;margin:0;'>PLATAFORMAS</p>
                    <p style='color:#00FFFF;font-size:13px;margin:3px 0;'>{ico["plataformas"]}</p>
                </div>
                <div style='background:#00000066;padding:12px;border-radius:10px;border:1px solid #333;'>
                    <p style='color:#888;font-size:11px;margin:0;'>BACKERS</p>
                    <p style='color:#FFD700;font-size:13px;margin:3px 0;'>{ico["backers"]}</p>
                </div>
                <div style='background:#00000066;padding:12px;border-radius:10px;border:1px solid #333;'>
                    <p style='color:#888;font-size:11px;margin:0;'>UNLOCK / VESTING</p>
                    <p style='color:#FF8C00;font-size:13px;margin:3px 0;'>{ico["unlock"]}</p>
                    <p style='color:#888;font-size:11px;margin:0;'>Categoria: {ico["categoria"]}</p>
                </div>
            </div>
            <div style='display:grid;grid-template-columns:2fr 1fr;gap:15px;margin-bottom:15px;'>
                <div style='background:#00000066;padding:12px;border-radius:10px;border-left:3px solid {cor};'>
                    <p style='color:#888;font-size:11px;margin:0;'>ANALISE FUNDAMENTALISTA</p>
                    <p style='color:#CCC;font-size:13px;margin:5px 0;'>{ico["descricao"]}</p>
                </div>
                <div style='background:#00000066;padding:12px;border-radius:10px;border:1px solid #333;text-align:center;'>
                    <p style='color:#888;font-size:11px;margin:0;'>ROI ALVO</p>
                    <p style='color:#00FF00;font-size:20px;font-weight:bold;margin:8px 0;'>{ico["roi_alvo"]}</p>
                    <p style='color:#555;font-size:11px;margin:0;'>R$400 investidos</p>
                </div>
            </div>
            <a href='{ico["link"]}' target='_blank' class='link-button'>{botao_comprar}</a>
            <a href='{ico["link_info"]}' target='_blank' class='link-button-green'>PESQUISAR PROJETO</a>
            {tag_encerrado}
        </div>
        """, unsafe_allow_html=True)

    if not encontrou:
        st.markdown(f"""
        <div style='text-align:center;padding:60px;border:2px dashed #333;border-radius:15px;'>
            <h2 style='color:#555;'>Nenhum ICO encontrado</h2>
            <p style='color:#444;'>Periodo: {data_inicio} ate {data_fim}</p>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style='background:linear-gradient(135deg,#050505,#0a0500);border:2px solid #FFD700;padding:25px;border-radius:15px;'>
        <h3 style='color:#FFD700;text-align:center;'>POR QUE ICOs MULTIPLICAM CAPITAL?</h3>
        <div style='display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:20px;margin-top:15px;'>
            <div style='border-left:3px solid #00FF00;padding-left:12px;'>
                <p style='color:#00FF00;font-weight:bold;margin:0;'>ENTRADA ANTECIPADA</p>
                <p style='color:#AAA;font-size:12px;'>Preco TGE sempre menor que listing.</p>
            </div>
            <div style='border-left:3px solid #FFD700;padding-left:12px;'>
                <p style='color:#FFD700;font-weight:bold;margin:0;'>BACKERS = LISTING</p>
                <p style='color:#AAA;font-size:12px;'>Circle, a16z garantem listagens Binance/Coinbase.</p>
            </div>
            <div style='border-left:3px solid #00FFFF;padding-left:12px;'>
                <p style='color:#00FFFF;font-weight:bold;margin:0;'>FDV BAIXO = UPSIDE</p>
                <p style='color:#AAA;font-size:12px;'>FDV $39M vs Worldcoin $2B = 50x room.</p>
            </div>
            <div style='border-left:3px solid #FF8C00;padding-left:12px;'>
                <p style='color:#FF8C00;font-weight:bold;margin:0;'>ROI R$400</p>
                <p style='color:#AAA;font-size:12px;'>x$0.39 = R$4.000 (10X) | x$1.00 = R$10.000 (25X)</p>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    if auto_refresh:
        time.sleep(30)
        st.rerun()

with t7:
    st.markdown("## 📖 Manual Estrategico Premium")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>Caca-Lancamentos</h3>
            <a href='https://daomaker.com/' class='link-button'>DAO Maker</a>
            <a href='https://seedify.fund/' class='link-button'>Seedify</a>
            <a href='https://jup.ag/' class='link-button'>Jupiter</a>
            <a href='https://icodrops.com' class='link-button'>ICO Drops</a>
            <div class='step-box'><b>Dica:</b> Monitore #TGE e #MainnetLaunch no X.</div>
        </div>
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>Analise Social</h3>
            <a href='https://lunarcrush.com/' class='link-button'>LunarCrush</a>
            <a href='https://coinmarketcal.com' class='link-button'>CoinMarketCal</a>
        </div>""", unsafe_allow_html=True)
    with cb:
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>Seguranca Anti-Rugpull</h3>
            <a href='https://tokensniffer.com/' class='link-button'>Token Sniffer</a>
            <a href='https://dexscreener.com/' class='link-button'>DEX Screener</a>
            <div class='step-box'>Verifique liquidez travada antes de comprar.</div>
        </div>
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>Regras Sniper</h3>
            <ul>
                <li>Nunca entre apos pump +100% no dia</li>
                <li>FDV abaixo de $50M = oportunidade</li>
                <li>Backers tier-1 = listagem garantida</li>
                <li>100% unlock TGE = sem pressao vesting</li>
            </ul>
        </div>""", unsafe_allow_html=True)
