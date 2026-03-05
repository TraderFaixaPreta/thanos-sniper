import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import time

# --- CONFIGURAÇÃO DE SEGURANÇA E TELEGRAM ---
TOKEN_TELEGRAM = "8262824397:AAERAJr6Epu2UvUPlOeLvJ2VJlB19o9c-xo"
MEU_ID_TELEGRAM = "1007733041" 

def enviar_alerta(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": MEU_ID_TELEGRAM, "text": mensagem, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except: return False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="THANOS v5.4 - MAXIMUM", page_icon="💎")

# --- SISTEMA DE SENHA ---
if "logado" not in st.session_state:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>ACESSO RESTRITO</h1>", unsafe_allow_html=True)
    senha = st.text_input("Senha da Manopla:", type="password")
    if senha == "thanos2025":
        st.session_state.logado = True
        st.rerun()
    st.stop()

# --- MOTOR DE DADOS ---
@st.cache_data(ttl=30)
def carregar_mercado():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&sparkline=true&price_change_percentage=1h,24h,7d"
    try:
        r = requests.get(url, timeout=15)
        df = pd.DataFrame(r.json())
        cols = ['image', 'symbol', 'name', 'current_price', 'price_change_percentage_24h', 'market_cap', 'total_volume', 'atl', 'atl_date', 'sparkline_in_7d']
        for col in cols:
            if col not in df.columns: df[col] = 0
        df['sparkline_7d_clean'] = df['sparkline_in_7d'].apply(lambda x: x.get('price', []) if isinstance(x, dict) else [])
        df['whale_activity'] = (df['total_volume'] / df['market_cap'].replace(0, 1) * 100).fillna(0)
        df['data_listagem'] = pd.to_datetime(df['atl_date'], errors='coerce').dt.strftime('%d/%m/%Y')
        return df
    except: return pd.DataFrame()

# --- MOTOR DE ICOs ---
@st.cache_data(ttl=300)
def carregar_icos():
    """Busca ICOs do CoinMarketCap + dados reais conhecidos"""
    icos = []
    
    # Tenta CoinMarketCal API
    try:
        headers = {"x-api-key": "public"}
        url = "https://developers.coinmarketcal.com/v1/events?max=50&categoryId=8"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json().get("body", {}).get("items", [])
            for ev in data:
                tge_str = ev.get("date_event", "")
                try:
                    tge_dt = datetime.strptime(tge_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except:
                    tge_dt = None
                icos.append({
                    "projeto": ev.get("title", "N/A"),
                    "token": ev.get("coins", [{}])[0].get("symbol", "N/A") if ev.get("coins") else "N/A",
                    "tipo": "TGE/ICO",
                    "tge_dt": tge_dt,
                    "tge_str": tge_str[:10] if tge_str else "N/A",
                    "hora_brt": "A confirmar",
                    "preco": "A confirmar",
                    "plataformas": "A confirmar",
                    "backers": "A confirmar",
                    "fdv": "A confirmar",
                    "score": "N/A",
                    "descricao": ev.get("description", "N/A"),
                    "link": ev.get("source", "#"),
                    "status": "Upcoming"
                })
    except:
        pass

    # Dados reais fixos conhecidos (atualize manualmente)
    icos_fixos = [
        {
            "projeto": "idOS Network",
            "token": "IDOS",
            "tipo": "TGE / CCA",
            "tge_dt": datetime(2026, 3, 5, 12, 0, 0, tzinfo=timezone.utc),
            "tge_str": "2026-03-05",
            "hora_brt": "09:00 BRT",
            "preco": "$0.039",
            "plataformas": "Arbitrum, Ethereum, Tally.xyz",
            "backers": "Circle, Ripple, Arbitrum Foundation, Fabric Ventures",
            "fdv": "$39M",
            "score": "8/10",
            "descricao": "Identidade Web3 portavel para stablecoins e DeFi. KYC unico em 40+ chains.",
            "link": "https://www.tally.xyz/sale/idos",
            "status": "Ativo"
        },
        {
            "projeto": "Power Protocol",
            "token": "POWER",
            "tipo": "Token Unlock",
            "tge_dt": datetime(2026, 3, 5, 14, 0, 0, tzinfo=timezone.utc),
            "tge_str": "2026-03-05",
            "hora_brt": "11:00 BRT",
            "preco": "$0.91",
            "plataformas": "Binance, MEXC, KuCoin",
            "backers": "A confirmar",
            "fdv": "$91M",
            "score": "6/10",
            "descricao": "Unlock $23M (2.5% supply). Risco de pressao de venda.",
            "link": "https://coinmarketcap.com",
            "status": "Upcoming"
        },
    ]
    
    # Mescla API + fixos sem duplicatas
    tokens_existentes = [i["token"] for i in icos]
    for ico in icos_fixos:
        if ico["token"] not in tokens_existentes:
            icos.append(ico)
    
    return icos

def calcular_tempo(tge_dt):
    """Retorna delta e status de urgencia"""
    if not tge_dt:
        return None, "unknown"
    agora = datetime.now(timezone.utc)
    delta = tge_dt - agora
    total_seg = delta.total_seconds()
    if total_seg < 0:
        return delta, "lancado"
    elif total_seg < 3600:
        return delta, "critico"      # menos 1h
    elif total_seg < 86400:
        return delta, "urgente"      # menos 24h
    else:
        return delta, "normal"

def formatar_tempo(delta):
    """Formata delta em string legivel"""
    if not delta:
        return "Data N/A"
    total = int(delta.total_seconds())
    if total < 0:
        return "LANCADO!"
    dias = total // 86400
    horas = (total % 86400) // 3600
    mins = (total % 3600) // 60
    secs = total % 60
    if dias > 0:
        return f"{dias}d {horas:02}h {mins:02}m"
    return f"{horas:02}h {mins:02}m {secs:02}s"

def cor_urgencia(status):
    cores = {
        "critico": "#FF0000",
        "urgente": "#FF8C00",
        "normal": "#00FF00",
        "lancado": "#888888",
        "unknown": "#444444"
    }
    return cores.get(status, "#00FF00")

def badge_urgencia(status):
    badges = {
        "critico": "CRITICO - MENOS DE 1H",
        "urgente": "URGENTE - HOJE",
        "normal": "Upcoming",
        "lancado": "LANCADO",
        "unknown": "A confirmar"
    }
    return badges.get(status, "Upcoming")

df = carregar_mercado()

# --- ESTILIZAÇÃO NEON ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF00; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #8A2BE2; }
    h1, h2, h3, p, span, label, div { color: #00FF00 !important; font-family: 'Consolas', monospace; }
    .thanos-title { text-align: center; font-size: 60px; font-weight: bold; color: #FFD700 !important; text-shadow: 0 0 30px #8A2BE2; }
    .premium-card { background: #0a0a0a; border: 1px solid #FFD700; padding: 20px; border-radius: 15px; margin-bottom: 15px; box-shadow: 0 0 15px rgba(138, 43, 226, 0.5); }
    .ico-card-critico { background: #1a0000; border: 2px solid #FF0000; padding: 20px; border-radius: 15px; margin-bottom: 15px; box-shadow: 0 0 25px rgba(255,0,0,0.6); }
    .ico-card-urgente { background: #0d0800; border: 2px solid #FF8C00; padding: 20px; border-radius: 15px; margin-bottom: 15px; box-shadow: 0 0 20px rgba(255,140,0,0.5); }
    .ico-card-normal { background: #000d00; border: 2px solid #00FF00; padding: 20px; border-radius: 15px; margin-bottom: 15px; box-shadow: 0 0 15px rgba(0,255,0,0.3); }
    .ico-card-lancado { background: #0a0a0a; border: 2px solid #444; padding: 20px; border-radius: 15px; margin-bottom: 15px; opacity: 0.6; }
    .countdown { font-size: 28px; font-weight: bold; font-family: 'Consolas', monospace; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 10px; }
    .link-button { display: inline-block; padding: 8px 15px; background-color: #8A2BE2; color: white !important; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px; margin-right: 5px; }
    .metric-card { background: #0a0a0a; border: 2px solid #FFD700; padding: 25px; border-radius: 15px; text-align: center; margin-top: 10px; }
    .step-box { border-left: 3px solid #00FFFF; padding-left: 15px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG DE RENDERIZAÇÃO ---
config_visual = {
    "image": st.column_config.ImageColumn("ICON"),
    "current_price": st.column_config.NumberColumn("PRECO", format="$%.8f"),
    "sparkline_7d_clean": st.column_config.LineChartColumn("7 DIAS"),
    "whale_activity": st.column_config.ProgressColumn("BALEIA", min_value=0, max_value=50),
}

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='color:#FFD700;'>MANOPLA</h2>", unsafe_allow_html=True)
    if st.button("TESTAR TELEGRAM"):
        enviar_alerta("*SISTEMA v5.4 ONLINE!*")
    st.divider()
    f_p = st.slider("PRECO MAX ($)", 0.0, 1.0, 0.10, step=0.01)
    f_w = st.slider("VOL/MCAP MIN (%)", 0, 100, 5)
    st.divider()
    st.info(f"REGIAO_SALDO: (1660, 27, 80, 29)")
    if st.button("REFRESH TOTAL"):
        st.cache_data.clear()
        st.rerun()

# --- CABECALHO ---
st.markdown("<div class='thanos-title'>THANOS v5.4</div>", unsafe_allow_html=True)

# --- ABAS ---
t1, t2, t3, t4, t5, t6, t7 = st.tabs([
    "UNIVERSO TOTAL", "SNIPER 100x", "RADAR BALEIAS",
    "NOVAS LISTAGENS", "MAQUINA DO TEMPO", "ICO LANCAMENTOS", "MANUAL PREMIUM"
])

with t1:
    st.data_editor(df[['image', 'market_cap_rank', 'name', 'symbol', 'current_price', 'price_change_percentage_24h']], 
                   column_config=config_visual, hide_index=True, use_container_width=True)

with t2:
    df_f = df[(df['current_price'] <= f_p) & (df['whale_activity'] >= f_w)]
    st.data_editor(df_f[['image', 'symbol', 'current_price', 'sparkline_7d_clean', 'whale_activity']], 
                   column_config=config_visual, hide_index=True, use_container_width=True)

with t3:
    st.dataframe(df.sort_values('whale_activity', ascending=False).head(50)[['name', 'symbol', 'total_volume', 'whale_activity']], use_container_width=True)

with t4:
    df_new = df.sort_values(by='atl_date', ascending=False).head(50)
    st.data_editor(df_new[['image', 'name', 'symbol', 'data_listagem', 'current_price']], 
                   column_config=config_visual, hide_index=True, use_container_width=True)

with t5:
    st.subheader("Simulador de Lucro Historico")
    with st.form("sim_form"):
        c1, c2 = st.columns(2)
        with c1:
            m_sim = st.selectbox("Escolha a Moeda:", df['name'].tolist())
        with c2:
            v_sim = st.number_input("Investir ($):", value=100.0)
        btn = st.form_submit_button("EFETUAR SIMULACAO")
    if btn:
        d = df[df['name'] == m_sim].iloc[0]
        res = (v_sim / d['atl']) * d['current_price']
        st.markdown(f"""
        <div class='metric-card'>
            <h1 style='color:#00FF00;'>${res:,.2f}</h1>
            <p><b>Preco Inicial (ATL):</b> ${d['atl']:.8f} | <b>Data:</b> {d['data_listagem']}</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# ABA 6: ICO LANCAMENTOS (NOVA!)
# ============================================================
with t6:
    st.markdown("<h2 style='color:#FFD700; text-align:center;'>ICO / TGE - RADAR DE LANCAMENTOS</h2>", unsafe_allow_html=True)
    
    # --- FILTROS ---
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        hoje = datetime.now(timezone.utc).date()
        data_inicio = st.date_input("Data INICIO:", value=hoje)
    with col_f2:
        data_fim = st.date_input("Data FIM:", value=hoje + timedelta(days=30))
    with col_f3:
        filtro_status = st.multiselect(
            "Status:", 
            ["critico", "urgente", "normal", "lancado"],
            default=["critico", "urgente", "normal"]
        )
    with col_f4:
        auto_refresh = st.toggle("Auto Refresh 30s", value=True)

    st.divider()

    # --- CARREGAR ICOs ---
    icos = carregar_icos()
    
    # --- ALERTAS URGENTES NO TOPO ---
    criticos = []
    for ico in icos:
        delta, status = calcular_tempo(ico.get("tge_dt"))
        if status in ["critico", "urgente"]:
            criticos.append((ico, delta, status))
    
    if criticos:
        st.markdown("<h3 style='color:#FF0000;'>ATENCAO - LANCAMENTOS PROXIMOS!</h3>", unsafe_allow_html=True)
        for ico, delta, status in criticos:
            cor = cor_urgencia(status)
            st.markdown(f"""
            <div style='background:#1a0000; border:2px solid {cor}; padding:15px; border-radius:10px; 
                        margin-bottom:10px; box-shadow: 0 0 20px {cor}88;'>
                <span style='color:{cor}; font-size:20px; font-weight:bold;'>
                    {badge_urgencia(status)} - {ico["projeto"]} ({ico["token"]})
                </span>
                <div class='countdown' style='color:{cor};'>{formatar_tempo(delta)}</div>
                <span style='color:#FFFFFF;'>Plataforma: {ico["plataformas"]} | Preco: {ico["preco"]} | Score: {ico["score"]}</span>
            </div>
            """, unsafe_allow_html=True)
        st.divider()

    # --- LISTA COMPLETA FILTRADA ---
    st.markdown("<h3 style='color:#00FF00;'>TODOS OS LANCAMENTOS</h3>", unsafe_allow_html=True)
    
    encontrou = False
    for ico in icos:
        delta, status = calcular_tempo(ico.get("tge_dt"))
        
        # Filtro por data
        tge_date = ico.get("tge_dt")
        if tge_date:
            tge_date_only = tge_date.date()
            if not (data_inicio <= tge_date_only <= data_fim):
                continue
        
        # Filtro por status
        if status not in filtro_status:
            continue
        
        encontrou = True
        cor = cor_urgencia(status)
        
        # Classe do card por urgencia
        if status == "critico":
            card_class = "ico-card-critico"
        elif status == "urgente":
            card_class = "ico-card-urgente"
        elif status == "lancado":
            card_class = "ico-card-lancado"
        else:
            card_class = "ico-card-normal"
        
        with st.container():
            st.markdown(f"""
            <div class='{card_class}'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <span style='color:{cor}; font-size:22px; font-weight:bold;'>
                            {ico["projeto"]} ({ico["token"]})
                        </span>
                        <span style='background:{cor}; color:#000; padding:3px 10px; border-radius:10px; 
                                     font-size:11px; font-weight:bold; margin-left:10px;'>
                            {badge_urgencia(status)}
                        </span>
                    </div>
                    <div class='countdown' style='color:{cor};'>{formatar_tempo(delta)}</div>
                </div>
                <hr style='border-color:{cor}33; margin:10px 0;'>
                <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:15px; margin-top:10px;'>
                    <div>
                        <p style='color:#888; margin:0;'>Tipo</p>
                        <p style='color:#FFF; margin:0; font-weight:bold;'>{ico["tipo"]}</p>
                    </div>
                    <div>
                        <p style='color:#888; margin:0;'>Data/Hora BRT</p>
                        <p style='color:#FFF; margin:0; font-weight:bold;'>{ico["tge_str"]} {ico["hora_brt"]}</p>
                    </div>
                    <div>
                        <p style='color:#888; margin:0;'>Preco TGE</p>
                        <p style='color:#00FF00; margin:0; font-weight:bold;'>{ico["preco"]}</p>
                    </div>
                    <div>
                        <p style='color:#888; margin:0;'>Plataformas</p>
                        <p style='color:#00FFFF; margin:0;'>{ico["plataformas"]}</p>
                    </div>
                    <div>
                        <p style='color:#888; margin:0;'>Backers</p>
                        <p style='color:#FFD700; margin:0;'>{ico["backers"]}</p>
                    </div>
                    <div>
                        <p style='color:#888; margin:0;'>FDV / Score</p>
                        <p style='color:{cor}; margin:0; font-weight:bold;'>{ico["fdv"]} | Score {ico["score"]}</p>
                    </div>
                </div>
                <div style='margin-top:12px; border-left:3px solid {cor}; padding-left:10px;'>
                    <p style='color:#AAA; margin:0;'>{ico["descricao"]}</p>
                </div>
                <a href='{ico["link"]}' target='_blank' class='link-button'>COMPRAR / VER</a>
            </div>
            """, unsafe_allow_html=True)
    
    if not encontrou:
        st.markdown(f"""
        <div style='text-align:center; padding:50px; border:2px dashed #333; border-radius:15px;'>
            <h2 style='color:#555;'>Nenhum ICO encontrado</h2>
            <p style='color:#444;'>Periodo: {data_inicio} ate {data_fim}</p>
            <p style='color:#444;'>Tente ampliar o intervalo de datas ou ajustar os filtros</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # --- RODAPE DECISAO ---
    st.markdown(f"""
    <div style='background:#050505; border:2px solid #FFD700; padding:20px; border-radius:15px; margin-top:20px;'>
        <h3 style='color:#FFD700; text-align:center;'>POR QUE ICOs PODEM MULTIPLICAR SEU CAPITAL?</h3>
        <hr style='border-color:#FFD70033;'>
        <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:20px;'>
            <div>
                <p style='color:#00FF00; font-weight:bold;'>ENTRADA ANTECIPADA</p>
                <p style='color:#AAA;'>Voce compra antes das exchanges. Preco TGE e sempre menor que listing price.</p>
            </div>
            <div>
                <p style='color:#FFD700; font-weight:bold;'>BACKERS = CONFIANCA</p>
                <p style='color:#AAA;'>Projetos com Circle, Ripple, a16z garantem liquidez e listagens em CEX grandes.</p>
            </div>
            <div>
                <p style='color:#00FFFF; font-weight:bold;'>ROI R$400</p>
                <p style='color:#AAA;'>10.256 IDOS x $0.20 = R$2.000 (5X) | x $0.39 = R$4.000 (10X) | x $1.00 = R$10.000 (25X)</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Auto refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

# --- ABA 7: MANUAL PREMIUM ---
with t7:
    st.markdown("## Manual Estrategico Premium")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>Caca-Lancamentos (Launchpads)</h3>
            <p>Projetos em estagio inicial antes das corretoras:</p>
            <a href='https://daomaker.com/' class='link-button'>DAO Maker</a>
            <a href='https://seedify.fund/' class='link-button'>Seedify</a>
            <a href='https://jup.ag/' class='link-button'>Jupiter (Solana)</a>
            <div class='step-box'>
                <b>Dica X (Twitter):</b> Monitore as tags #TGE e #MainnetLaunch.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>Analise Social</h3>
            <a href='https://lunarcrush.com/' class='link-button'>LunarCrush</a>
        </div>
        """, unsafe_allow_html=True)
    with cb:
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>Seguranca (Anti-Rugpull)</h3>
            <a href='https://tokensniffer.com/' class='link-button'>Token Sniffer</a>
            <a href='https://dexscreener.com/' class='link-button'>DEX Screener</a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>Estrategia Sniper</h3>
            <ul>
                <li>Nunca entre apos pump de 100% no dia.</li>
                <li>Siga baleias na aba RADAR BALEIAS.</li>
                <li>Monitore a aba ICO LANCAMENTOS.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)