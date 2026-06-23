import streamlit as st
import requests
import json
from datetime import datetime
from urllib.parse import urlencode, parse_qs, urlparse

# ─── CONFIG ───────────────────────────────────────────────────────────────────
CLIENT_ID = "cf858739-80c5-4bf0-bc5c-6f5b0cefb70d"
TENANT_ID = "e1362ab7-0546-4f12-9f44-0867415479b9"
SCOPES = "Tasks.ReadWrite Group.Read.All User.Read.All offline_access"
REDIRECT_URI = "https://ibgp-planner-qn2vrzsh36olfjspwx8lj8.streamlit.app/"
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]

FILTROS = [
    "PERÍODO DE INSCRIÇÕES",
    "PERÍODO SOLICITAÇÃO DE ISENÇÃO",
]

# ─── PÁGINA ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IBGP · Datas dos Concursos",
    page_icon="📋",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .header {
        background: #1B3A6B;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .header h1 { color: white; font-size: 1.6rem; font-weight: 700; margin: 0; }
    .header p  { color: #9DB8E0; font-size: 0.9rem; margin: 0.25rem 0 0; }

    .login-box {
        background: #F0F4FA;
        border: 1px solid #D0DAEA;
        border-radius: 12px;
        padding: 2.5rem;
        text-align: center;
        max-width: 480px;
        margin: 3rem auto;
    }
    .login-box h2 { color: #1B3A6B; font-size: 1.2rem; margin-bottom: 0.5rem; }
    .login-box p  { color: #5A6A80; font-size: 0.9rem; margin-bottom: 1.5rem; }

    .concurso-header {
        background: #1B3A6B;
        color: white;
        padding: 0.6rem 1.2rem;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        font-size: 0.95rem;
        margin-top: 1.5rem;
    }
    .tarefa-row {
        background: white;
        border: 1px solid #E2E8F0;
        border-top: none;
        padding: 0.8rem 1.2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.9rem;
    }
    .tarefa-row:last-child { border-radius: 0 0 8px 8px; }
    .tarefa-nome { color: #2D3748; flex: 1; }
    .tarefa-data {
        background: #EBF4FF;
        color: #1B3A6B;
        font-weight: 600;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        white-space: nowrap;
    }
    .tarefa-data.vencida {
        background: #FFF0F0;
        color: #C53030;
    }
    .tarefa-data.proxima {
        background: #FFFBEB;
        color: #B7791F;
    }
    .badge-inscricao {
        background: #E6FFFA;
        color: #276749;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        margin-right: 0.5rem;
    }
    .badge-isencao {
        background: #EBF4FF;
        color: #2B6CB0;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        margin-right: 0.5rem;
    }
    .stats-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        flex: 1;
        text-align: center;
    }
    .stat-num  { font-size: 2rem; font-weight: 700; color: #1B3A6B; }
    .stat-lbl  { font-size: 0.8rem; color: #718096; margin-top: 0.2rem; }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header">
    <div>
        <h1>📋 IBGP · Datas dos Concursos</h1>
        <p>Prazos de inscrição e isenção por concurso, direto do Planner</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── AUTH ─────────────────────────────────────────────────────────────────────

def auth_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "response_mode": "query",
    }
    return f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?" + urlencode(params)


def trocar_codigo(code):
    resp = requests.post(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
        }
    )
    return resp.json()


def renovar_token(refresh_token):
    resp = requests.post(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": SCOPES,
        }
    )
    return resp.json()


# ─── GRAPH ────────────────────────────────────────────────────────────────────

def graph_get(token, url):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def graph_get_all(token, url):
    """Busca todos os resultados paginados da Graph API."""
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    next_url = url
    while next_url:
        resp = requests.get(next_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("value", []))
        next_url = data.get("@odata.nextLink")
    return results


@st.cache_data(ttl=300, show_spinner=False)
def buscar_dados(token, _cache_key=0):
    # Grupos
    groups = graph_get(token, "https://graph.microsoft.com/v1.0/me/memberOf")
    planos = []
    for g in groups.get("value", []):
        gid = g.get("id")
        if not gid:
            continue
        try:
            result = graph_get(token, f"https://graph.microsoft.com/v1.0/groups/{gid}/planner/plans")
            for p in result.get("value", []):
                planos.append({"id": p["id"], "title": p.get("title", "Sem nome")})
        except:
            continue

    # Filtra apenas o plano PLANNER IBGP
    planos = [p for p in planos if "PLANNER IBGP" in p["title"].upper()]

    todos = []
    todas_tarefas_debug = []
    for plano in planos:
        buckets_data = graph_get(token, f"https://graph.microsoft.com/v1.0/planner/plans/{plano['id']}/buckets")
        buckets = {b["id"]: b["name"] for b in buckets_data.get("value", [])}

        tarefas = graph_get_all(token, f"https://graph.microsoft.com/v1.0/planner/plans/{plano['id']}/tasks")
        for t in tarefas:
            nome = t.get("title", "")
            bucket = buckets.get(t.get("bucketId", ""), "—")
            todas_tarefas_debug.append({"plano": plano["title"], "bucket": bucket, "tarefa": nome, "due": t.get("dueDateTime", "")})
            if not any(f in nome.upper() for f in FILTROS):
                continue
            bucket = buckets.get(t.get("bucketId", ""), "—")
            due = t.get("dueDateTime")
            data_fmt = "Sem data"
            dias_restantes = None
            if due:
                dt = datetime.fromisoformat(due.replace("Z", "+00:00")).replace(tzinfo=None)
                data_fmt = dt.strftime("%d/%m/%Y")
                dias_restantes = (dt - datetime.now()).days

            tipo = "inscricao" if "INSCRIÇÕES" in nome.upper() else "isencao"
            todos.append({
                "plano": plano["title"],
                "concurso": bucket,
                "tarefa": nome,
                "data": data_fmt,
                "dias": dias_restantes,
                "tipo": tipo,
            })

    return sorted(todos, key=lambda x: (x["concurso"], x["tipo"])), todas_tarefas_debug


# ─── ESTADO DE AUTH ───────────────────────────────────────────────────────────

params = st.query_params
code = params.get("code")

if "access_token" not in st.session_state:
    if code:
        with st.spinner("Autenticando..."):
            token_data = trocar_codigo(code)
            if "access_token" in token_data:
                st.session_state["access_token"] = token_data["access_token"]
                st.session_state["refresh_token"] = token_data.get("refresh_token")
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"Erro na autenticação: {token_data.get('error_description', 'Erro desconhecido')}")
    else:
        st.markdown(f"""
        <div class="login-box">
            <h2>Entrar com Microsoft 365</h2>
            <p>Faça login com sua conta do IBGP para visualizar os prazos dos concursos direto do Planner.</p>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.link_button("🔐 Entrar com Microsoft", auth_url(), use_container_width=True)
        st.stop()

# ─── DADOS ────────────────────────────────────────────────────────────────────

token = st.session_state["access_token"]

col_logout, col_refresh = st.columns([8, 1])
with col_logout:
    st.caption("✅ Conectado ao Microsoft 365")
with col_refresh:
    if st.button("↻ Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

try:
    with st.spinner("Buscando tarefas no Planner..."):
        dados, debug_tarefas = buscar_dados(token)
except requests.HTTPError as e:
    if e.response.status_code == 401 and st.session_state.get("refresh_token"):
        new_token = renovar_token(st.session_state["refresh_token"])
        if "access_token" in new_token:
            st.session_state["access_token"] = new_token["access_token"]
            st.rerun()
    st.error("Sessão expirada. Faça login novamente.")
    if st.button("Fazer login novamente"):
        del st.session_state["access_token"]
        st.rerun()
    st.stop()

if not dados:
    st.warning("Nenhuma tarefa de inscrição ou isenção encontrada no Planner.")
    st.stop()

# ─── DEBUG ───────────────────────────────────────────────────────────────────
with st.expander("🔍 Ver todas as tarefas encontradas (diagnóstico)"):
    if debug_tarefas:
        st.caption(f"Total de tarefas encontradas no Planner: {len(debug_tarefas)}")
        for t in sorted(debug_tarefas, key=lambda x: (x["bucket"], x["tarefa"])):
            st.text(f"[{t['plano']}] [{t['bucket']}] {t['tarefa']} | due: {t['due']}")
    else:
        st.warning("Nenhuma tarefa encontrada.")

# ─── STATS ────────────────────────────────────────────────────────────────────

concursos = list({d["concurso"] for d in dados})
vencendo_em_7 = [d for d in dados if d["dias"] is not None and 0 <= d["dias"] <= 7]
vencidos = [d for d in dados if d["dias"] is not None and d["dias"] < 0]

c1, c2, c3 = st.columns(3)
c1.metric("Concursos ativos", len(concursos))
c2.metric("Prazos nos próximos 7 dias", len(vencendo_em_7))
c3.metric("Prazos vencidos", len(vencidos))

st.divider()

# ─── TABELA POR CONCURSO ──────────────────────────────────────────────────────

from itertools import groupby

dados_sorted = sorted(dados, key=lambda x: x["concurso"])

for concurso, tarefas_iter in groupby(dados_sorted, key=lambda x: x["concurso"]):
    tarefas = list(tarefas_iter)
    st.markdown(f'<div class="concurso-header">🏛 {concurso}</div>', unsafe_allow_html=True)

    for t in tarefas:
        badge = '<span class="badge-inscricao">INSCRIÇÃO</span>' if t["tipo"] == "inscricao" else '<span class="badge-isencao">ISENÇÃO</span>'

        if t["dias"] is None:
            data_class = "tarefa-data"
            data_txt = t["data"]
        elif t["dias"] < 0:
            data_class = "tarefa-data vencida"
            data_txt = f"{t['data']} · vencida"
        elif t["dias"] <= 7:
            data_class = "tarefa-data proxima"
            data_txt = f"{t['data']} · {t['dias']}d restantes"
        else:
            data_class = "tarefa-data"
            data_txt = f"{t['data']} · {t['dias']}d restantes"

        st.markdown(f"""
        <div class="tarefa-row">
            <span class="tarefa-nome">{badge}{t['tarefa']}</span>
            <span class="{data_class}">{data_txt}</span>
        </div>
        """, unsafe_allow_html=True)
