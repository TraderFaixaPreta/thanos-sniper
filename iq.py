import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="THANOS v2.0 - PROTECTED", page_icon="💎")

# --- SUA CHAVE E COORDENADA ---
API_KEY = "CG-xEE61PQYvY6AYtUMNfXmoMKi"
COORDENADA_SALDO = "(1660, 27, 80, 29)"

# --- SISTEMA DE SEGURANÇA ---
def check_password():
    """Retorna True se o utilizador inseriu a senha correta."""
    def password_entered():
        if st.session_state["password"] == "thanos2025": # <--- TUA SENHA
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align:center; color:#FFD700;'>🛡️ ACESSO RESTRITO</h1>", unsafe_allow_html=True)
        st.text_input("Insira a Senha da Manopla:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("🚫 Senha Incorreta. Tente novamente.")
        st.text_input("Insira a Senha da Manopla:", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

if check_password():
    # --- AUTO-REFRESH (30s) ---
    if "last_update" not in st.session_state:
        st.session_state.last_update = time.time()
    if time.time() - st.session_state.last_update > 30:
        st.session_state.last_update = time.time()
        st.rerun()

    # --- ESTILIZAÇÃO NEON ---
    st.markdown("""
        <style>
        .stApp { background-color: #000000; color: #00FF00; }
        [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #8A2BE2; }
        h1, h2, h3, p, span, label, div { color: #00FF00 !important; font-family: 'Consolas', monospace; }
        .thanos-title { text-align: center; font-size: 50px; font-weight: bold; color: #FFD700 !important; text-shadow: 0 0 20px #8A2BE2; }
        .metric-box { background: #000; border: 2px solid #FFD700; padding: 20px; border-radius: 15px; text-align: center; }
        .simulator-card { background: linear-gradient(145deg, #1a1a1a, #000); border: 2px solid #8A2BE2; padding: 25px; border-radius: 20px; }
        </style>
        """, unsafe_allow_html=True)

    # --- MOTOR DE DADOS ---
    @st.cache_data(ttl=30)
    def fetch_thanos_data(api_key):
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&sparkline=true&price_change_percentage=1h,24h,7d&x_cg_demo_api_key={api_key}"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                df = pd.DataFrame(r.json())
                df['sparkline_7d_clean'] = df['sparkline_in_7d'].apply(lambda x: x.get('price', []) if isinstance(x, dict) else [])
                df['data_listagem'] = pd.to_datetime(df['atl_date']).dt.strftime('%d/%m/%Y')
                df['explosion_score'] = (df['total_volume'] / df['market_cap'] * 100)
                return df
            return pd.DataFrame()
        except: return pd.DataFrame()

    df = fetch_thanos_data(API_KEY)

    # --- SIDEBAR (FILTROS) ---
    with st.sidebar:
        st.markdown("<h2 style='color:#FFD700;'>🛡️ MANOPLA</h2>", unsafe_allow_html=True)
        f_preco = st.slider("PREÇO MÁXIMO ($)", 0.0, 2.0, 0.10, step=0.01)
        f_vol = st.number_input("VOLUME MÍNIMO (24H)", value=100000)
        st.divider()
        st.info(f"📍 COORDENADA SALDO:\n{COORDENADA_SALDO}")
        if st.button("RESETAR REALIDADE"):
            st.cache_data.clear()
            st.rerun()

    # --- CABEÇALHO ---
    st.markdown("<div class='thanos-title'>THANOS v2.0</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #8A2BE2;'>Sincronia: {time.strftime('%H:%M:%S')} | Acesso Autorizado</p>", unsafe_allow_html=True)

    # --- MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='metric-box'>GEMAS ENCONTRADAS<br><h2>{len(df[df['current_price'] <= f_preco])}</h2></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-box'>LÍDER ATUAL<br><h2>{df.iloc[0]['symbol'].upper()}</h2></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='metric-box'>ATUALIZAÇÃO<br><h2>30s</h2></div>", unsafe_allow_html=True)

    st.divider()

    # --- ABAS ---
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 100x SNIPER", "🎯 RADAR GERAL", "🔮 MÁQUINA DO TEMPO", "🆕 LANÇAMENTOS"])

    with tab1:
        st.subheader("Gemas com Potencial de Explosão")
        df_f = df[(df['current_price'] <= f_preco) & (df['total_volume'] >= f_vol)].copy()
        st.data_editor(
            df_f[['image', 'symbol', 'current_price', 'price_change_percentage_24h', 'sparkline_7d_clean', 'explosion_score']],
            column_config={
                "image": st.column_config.ImageColumn(""),
                "current_price": st.column_config.NumberColumn("PREÇO", format="$%.8f"),
                "price_change_percentage_24h": st.column_config.NumberColumn("VAR 24H", format="%.2f%%"),
                "sparkline_7d_clean": st.column_config.LineChartColumn("TENDÊNCIA 7D", y_min=0),
                "explosion_score": st.column_config.ProgressColumn("FORÇA", min_value=0, max_value=30)
            }, hide_index=True, use_container_width=True
        )

    with tab3:
        st.markdown("### 💰 Máquina do Tempo: O Poder do 100x")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            alvo = st.selectbox("Selecione a Moeda:", df['name'].tolist())
            invest = st.number_input("Valor Investido ($):", value=100)
        with col_b:
            d = df[df['name'] == alvo].iloc[0]
            v_final = (invest / d['atl']) * d['current_price']
            multi = v_final / invest
            st.markdown(f"""
            <div class='simulator-card'>
                <h3 style='color:#FFD700;'>Se compraste {alvo} no ATL...</h3>
                <h1 style='color:#00FF00;'>TERIAS: ${v_final:,.2f}</h1>
                <p style='color:#8A2BE2;'>Multiplicador: <b>{multi:,.1f}x</b></p>
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.subheader("Novas Listagens Detectadas")
        df_new = df.sort_values(by='atl_date', ascending=False).head(20)
        st.data_editor(
            df_new[['image', 'symbol', 'name', 'data_listagem', 'current_price']],
            column_config={
                "image": st.column_config.ImageColumn(""),
                "data_listagem": "DATA LISTAGEM",
                "current_price": st.column_config.NumberColumn("PREÇO ATUAL", format="$%.8f")
            }, hide_index=True, use_container_width=True
        )

    with tab2:
        st.dataframe(df[['symbol', 'current_price', 'market_cap', 'total_volume']], use_container_width=True)