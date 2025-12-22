import streamlit as st
import requests
import pandas as pd
from datetime import datetime

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
st.set_page_config(layout="wide", page_title="THANOS v5.3 - MAXIMUM", page_icon="💎")

# --- SISTEMA DE SENHA ---
if "logado" not in st.session_state:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>🛡️ ACESSO RESTRITO</h1>", unsafe_allow_html=True)
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

df = carregar_mercado()

# --- ESTILIZAÇÃO NEON ORIGINAL ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00FF00; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #8A2BE2; }
    h1, h2, h3, p, span, label, div { color: #00FF00 !important; font-family: 'Consolas', monospace; }
    .thanos-title { text-align: center; font-size: 60px; font-weight: bold; color: #FFD700 !important; text-shadow: 0 0 30px #8A2BE2; }
    .premium-card { background: #0a0a0a; border: 1px solid #FFD700; padding: 20px; border-radius: 15px; margin-bottom: 15px; box-shadow: 0 0 15px rgba(138, 43, 226, 0.5); }
    .link-button { display: inline-block; padding: 8px 15px; background-color: #8A2BE2; color: white !important; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px; margin-right: 5px; }
    .metric-card { background: #0a0a0a; border: 2px solid #FFD700; padding: 25px; border-radius: 15px; text-align: center; margin-top: 10px; }
    .step-box { border-left: 3px solid #00FFFF; padding-left: 15px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG DE RENDERIZAÇÃO ---
config_visual = {
    "image": st.column_config.ImageColumn("ICON"),
    "current_price": st.column_config.NumberColumn("PREÇO", format="$%.8f"),
    "sparkline_7d_clean": st.column_config.LineChartColumn("7 DIAS"),
    "whale_activity": st.column_config.ProgressColumn("BALEIA", min_value=0, max_value=50),
}

# --- BARRA LATERAL ORIGINAL ---
with st.sidebar:
    st.markdown("<h2 style='color:#FFD700;'>🛡️ MANOPLA</h2>", unsafe_allow_html=True)
    if st.button("🚀 TESTAR TELEGRAM"):
        enviar_alerta("🔥 *SISTEMA v5.3 ONLINE!*")
    st.divider()
    f_p = st.slider("PREÇO MÁX ($)", 0.0, 1.0, 0.10, step=0.01)
    f_w = st.slider("VOL/MCAP MÍN (%)", 0, 100, 5)
    st.divider()
    st.info(f"📍 REGIAO_SALDO: (1660, 27, 80, 29)")
    if st.button("🔄 REFRESH TOTAL"):
        st.cache_data.clear()
        st.rerun()

# --- CABEÇALHO ---
st.markdown("<div class='thanos-title'>THANOS v5.3</div>", unsafe_allow_html=True)

# --- ABAS (100% ESTRUTURA ORIGINAL) ---
t1, t2, t3, t4, t5, t6 = st.tabs([
    "🌌 UNIVERSO TOTAL", "🚀 SNIPER 100x", "🎯 RADAR BALEIAS", 
    "🆕 NOVAS LISTAGENS", "🔮 MÁQUINA DO TEMPO", "📖 MANUAL PREMIUM"
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
    st.subheader("🔮 Simulador de Lucro Histórico")
    with st.form("sim_form"):
        c1, c2 = st.columns(2)
        with c1:
            m_sim = st.selectbox("Escolha a Moeda:", df['name'].tolist())
        with c2:
            v_sim = st.number_input("Investir ($):", value=100.0)
        btn = st.form_submit_button("🚀 EFETUAR SIMULAÇÃO")
    
    if btn:
        d = df[df['name'] == m_sim].iloc[0]
        res = (v_sim / d['atl']) * d['current_price']
        st.markdown(f"""
        <div class='metric-card'>
            <h1 style='color:#00FF00;'>${res:,.2f}</h1>
            <p><b>Preço Inicial (ATL):</b> ${d['atl']:.8f} | <b>Data:</b> {d['data_listagem']}</p>
            <p style='color:#00FFFF;'><b>Ecossistema:</b> {d['symbol'].upper()} Network / DeFi / Web3</p>
        </div>
        """, unsafe_allow_html=True)

# --- ABA 6: MANUAL PREMIUM COMPLETO ---
with t6:
    st.markdown("## 📖 Manual Estratégico Premium")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>🛰️ Caça-Lançamentos (Launchpads)</h3>
            <p>Projetos em estágio inicial antes das corretoras:</p>
            <a href='https://daomaker.com/' class='link-button'>DAO Maker</a>
            <a href='https://seedify.fund/' class='link-button'>Seedify</a>
            <a href='https://jup.ag/' class='link-button'>Jupiter (Solana)</a>
            <div class='step-box'>
                <b>Dica X (Twitter):</b> Monitore as tags <i>#TGE</i> e <i>#MainnetLaunch</i>. 
                Siga contas de "Listing Alerts" para saber o minuto exato da listagem.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>📊 Análise Social</h3>
            <p>Veja o que está bombando no X (Twitter):</p>
            <a href='https://lunarcrush.com/' class='link-button'>LunarCrush</a>
            <div class='step-box'>
                O <b>LunarCrush</b> mede o engajamento social. Se uma gema tem alto volume social e baixo mcap, é oportunidade!
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cb:
        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>🛡️ Segurança (Anti-Rugpull)</h3>
            <p>Ferramentas para auditar o contrato na hora:</p>
            <a href='https://tokensniffer.com/' class='link-button'>Token Sniffer</a>
            <a href='https://dexscreener.com/' class='link-button'>DEX Screener</a>
            <div class='step-box'>
                <b>Checklist:</b> Verifique se a liquidez está travada e se o contrato não é um "Honeypot" no Token Sniffer.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='premium-card'>
            <h3 style='color:#FFD700;'>⚖️ Estratégia Sniper</h3>
            <p>Regras para não ser liquidado:</p>
            <ul>
                <li>Nunca entre após um "pump" de 100% no dia.</li>
                <li>Use a aba 'NOVAS LISTAGENS' para filtrar projetos com menos de 30 dias.</li>
                <li>Siga baleias na aba 'RADAR BALEIAS'.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)