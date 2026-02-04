import pandas as pd
import streamlit as st
import altair as alt

# Comentario: Configuración general
st.set_page_config(page_title="Dashboard Produção (m²) — SLN RDT", layout="wide")

# =========================
# CSS (estilo “dashboard product”)
# =========================
st.markdown("""
<style>
:root{
  --bg:#f4f6fb;
  --card:#ffffff;
  --muted:#6b7280;
  --text:#0f172a;
  --border:#e8edf5;
  --shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
  --radius:16px;
  --blue:#2563eb;
  --green:#10b981;
  --red:#ef4444;
}

.stApp{ background: var(--bg); }
.block-container{ padding-top: 1.0rem; padding-bottom: 2rem; max-width: 1400px; }

section[data-testid="stSidebar"]{
  background:#ffffff;
  border-right:1px solid var(--border);
}

header[data-testid="stHeader"]{ background: transparent; }

.card{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 14px 14px;
}

.section-title{
  font-weight: 900;
  color: var(--text);
  letter-spacing: .2px;
  font-size: 16px;
  margin: 0 0 8px 0;
}
.section-sub{
  color: var(--muted);
  font-size: 12px;
  margin: -4px 0 10px 0;
}

.topbar{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  margin-bottom: 12px;
}
.brand{
  display:flex;
  align-items:center;
  gap:10px;
}
.brand .pill{
  background:#e9efff;
  color:#1d4ed8;
  border:1px solid #dbe7ff;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}
.clock{
  color: var(--muted);
  font-size: 12px;
}
.live{
  display:inline-flex;
  align-items:center;
  gap:6px;
  color:#059669;
  font-size: 12px;
  font-weight: 800;
}
.dot{
  width:8px; height:8px; border-radius:999px; background:#10b981; display:inline-block;
}

.alert{
  background: #fee2e2;
  border: 1px solid #fecaca;
  color: #991b1b;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 14px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom: 12px;
}
.alert strong{ font-weight: 900; }
.alert small{ color:#7f1d1d; display:block; margin-top:4px; }

.kpi{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 12px 12px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  min-height: 78px;
}
.kpi .left{ display:flex; gap:10px; align-items:center; }
.icon{
  width:34px; height:34px;
  border-radius: 12px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight:900;
  color: var(--text);
  background:#f1f5ff;
  border:1px solid var(--border);
}
.kpi .label{ color: var(--muted); font-size: 12px; margin-bottom: 2px; }
.kpi .value{ color: var(--text); font-size: 20px; font-weight: 950; letter-spacing: .2px; }

.badge{
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 900;
  border: 1px solid var(--border);
  background:#f8fafc;
  color: var(--muted);
}
.badge.red{ background:#fee2e2; border-color:#fecaca; color:#991b1b; }
.badge.green{ background:#dcfce7; border-color:#bbf7d0; color:#166534; }
.badge.blue{ background:#dbeafe; border-color:#bfdbfe; color:#1e40af; }
</style>
""", unsafe_allow_html=True)

# =========================
# Helpers
# =========================
def fmt_int_br(x: float) -> str:
    # Comentario: Formato BR (1.234.567)
    try:
        return f"{float(x):,.0f}".replace(",", ".")
    except Exception:
        return "0"

def safe_unique(df: pd.DataFrame, col: str) -> list:
    # Comentario: Valores únicos sin NaN/vacío
    if col not in df.columns:
        return []
    vals = df[col].dropna().astype(str).tolist()
    vals = [v.strip() for v in vals if v.strip() != ""]
    return sorted(list(set(vals)))

def calc_m2(df: pd.DataFrame, km_ini: str, km_fim: str, largura: str) -> pd.Series:
    # Comentario: m² = |Δkm| * 1000 * ancho(m)
    ini = pd.to_numeric(df.get(km_ini), errors="coerce")
    fim = pd.to_numeric(df.get(km_fim), errors="coerce")
    lar = pd.to_numeric(df.get(largura), errors="coerce")
    m2 = (fim - ini).abs() * 1000 * lar
    return m2.fillna(0)

def normalize_date_column(df: pd.DataFrame, col: str = "DATA") -> pd.DataFrame:
    # Comentario: Normaliza DATA robustamente (texto / datetime / número Excel)
    if col not in df.columns:
        return df
    s = df[col]
    dt = pd.to_datetime(s, errors="coerce")
    if dt.isna().any():
        num = pd.to_numeric(s, errors="coerce")
        dt2 = pd.to_datetime(num, unit="D", origin="1899-12-30", errors="coerce")
        dt = dt.fillna(dt2)
    df = df.copy()
    df[col] = dt
    df = df[df[col].notna()].copy()
    df[col] = df[col].dt.date
    return df

def enrich_m2(df: pd.DataFrame) -> pd.DataFrame:
    # Comentario: Calcula m² por frente y total
    df = df.copy()
    df["m2_manual"] = calc_m2(df, "KM INICIAL (Roçada Manual)", "KM FINAL (Roçada Manual)", "LARGURA (média) (Roçada Manual)")
    df["m2_trator_a"] = calc_m2(df, "KM INICIAL (Trator A)", "KM FINAL (Trator A)", "LARGURA (média) (Trator A)")
    df["m2_trator_b"] = calc_m2(df, "KM INICIAL (Trator B)", "KM FINAL (Trator B)", "LARGURA (média) (Trator B)")
    df["m2_trator_c"] = calc_m2(df, "KM INICIAL (Trator C)", "KM FINAL (Trator C)", "LARGURA (média) (Trator C)")
    df["m2_robo"] = calc_m2(df, "KM INICIAL (Robô)", "KM FINAL (Robô)", "LARGURA (média) (Robô)")
    df["m2_tratores"] = df[["m2_trator_a", "m2_trator_b", "m2_trator_c"]].sum(axis=1)
    df["m2_total"] = df[["m2_manual", "m2_tratores", "m2_robo"]].sum(axis=1)
    return df

def kpi_card(label: str, value: str, icon_text: str = "•", badge_text: str | None = None, badge_kind: str = "blue") -> str:
    # Comentario: KPI en HTML para estética tipo producto
    badge_html = ""
    if badge_text is not None:
        badge_html = f'<span class="badge {badge_kind}">{badge_text}</span>'
    return f"""
    <div class="kpi">
      <div class="left">
        <div class="icon">{icon_text}</div>
        <div>
          <div class="label">{label}</div>
          <div class="value">{value}</div>
        </div>
      </div>
      <div>{badge_html}</div>
    </div>
    """

@st.cache_data(ttl=3600)
def load_excel(file_bytes: bytes, sheet_name: str) -> pd.DataFrame:
    # Comentario: Lee el Excel desde bytes (upload) y normaliza
    df = pd.read_excel(file_bytes, sheet_name=sheet_name)
    df = normalize_date_column(df, "DATA")
    df = enrich_m2(df)
    return df

# =========================
# Acesso (senha simples)
# =========================
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")

with st.sidebar:
    st.markdown("## Acesso")
    pwd = st.text_input("Senha", type="password")
    if APP_PASSWORD and pwd != APP_PASSWORD:
        st.warning("Acesso restrito.")
        st.stop()

# =========================
# Upload + parâmetros
# =========================
with st.sidebar:
    st.markdown("## Carregar dados")
    up = st.file_uploader("Upload do Excel (.xlsx)", type=["xlsx"])
    sheet = st.text_input("Nome da aba (sheet)", value="Respostas ao formulário 1")
    colA, colB = st.columns(2)
    with colA:
        processar = st.button("📥 Processar")
    with colB:
        if st.button("🧹 Limpar cache"):
            st.cache_data.clear()
            st.session_state.pop("df", None)

# Comentario: Processamiento controlado por botón (no automático)
if processar:
    if up is None:
        st.error("Faça upload do arquivo Excel primeiro.")
        st.stop()
    try:
        st.session_state["df"] = load_excel(up.getvalue(), sheet)
    except Exception as e:
        st.error(f"Erro ao ler o Excel/aba. Verifique o nome da aba. Detalhe: {e}")
        st.stop()

# Comentario: Si no hay datos cargados aún, mostrar instrucción
if "df" not in st.session_state:
    st.markdown("""
    <div class="card">
      <div class="section-title">Como usar</div>
      <div class="section-sub">MVP online (upload do Excel)</div>
      <ol style="color:#334155; margin:0; padding-left:18px;">
        <li>Digite a senha</li>
        <li>Faça upload do Excel</li>
        <li>Confirme o nome da aba</li>
        <li>Clique em <b>Processar</b></li>
      </ol>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = st.session_state["df"]
if df.empty:
    st.warning("A base carregada está vazia após normalização de DATA.")
    st.stop()

# =========================
# Sidebar filtros
# =========================
with st.sidebar:
    st.markdown("## Filtros")

    dmin, dmax = min(df["DATA"]), max(df["DATA"])
    date_range = st.date_input("Período", value=(dmin, dmax), min_value=dmin, max_value=dmax)
    d1, d2 = date_range if isinstance(date_range, tuple) else (dmin, dmax)

    equipes = safe_unique(df, "EQUIPE")
    encarregados = safe_unique(df, "NOME DO ENCARREGADO")
    supervisores = safe_unique(df, "SUPERVISOR")

    sel_equipes = st.multiselect("Equipe", equipes, default=[])
    sel_enc = st.multiselect("Encarregado", encarregados, default=[])
    sel_sup = st.multiselect("Supervisor", supervisores, default=[])

# =========================
# Apply filters
# =========================
df_f = df[(df["DATA"] >= d1) & (df["DATA"] <= d2)].copy()
if sel_equipes and "EQUIPE" in df_f.columns:
    df_f = df_f[df_f["EQUIPE"].astype(str).isin(sel_equipes)]
if sel_enc and "NOME DO ENCARREGADO" in df_f.columns:
    df_f = df_f[df_f["NOME DO ENCARREGADO"].astype(str).isin(sel_enc)]
if sel_sup and "SUPERVISOR" in df_f.columns:
    df_f = df_f[df_f["SUPERVISOR"].astype(str).isin(sel_sup)]

if df_f.empty:
    st.info("Sem dados para os filtros selecionados.")
    st.stop()

# =========================
# Topbar
# =========================
st.markdown(f"""
<div class="topbar">
  <div class="brand">
    <h2 style="margin:0;">Dashboard</h2>
    <span class="pill">MVP</span>
  </div>
  <div style="display:flex; gap:14px; align-items:center;">
    <span class="clock">🕒 {pd.Timestamp.now().strftime('%H:%M:%S')}</span>
    <span class="live"><span class="dot"></span> Ao Vivo</span>
  </div>
</div>
""", unsafe_allow_html=True)

# =========================
# Alert banner (outliers como exemplo)
# =========================
outliers = int((df_f["m2_total"] > df_f["m2_total"].quantile(0.95)).sum())
if outliers > 0:
    st.markdown(f"""
    <div class="alert">
      <div>
        <strong>⚠️ {outliers} registros fora do padrão</strong>
        <small>Acima do p95 de m² no período filtrado (alerta de consistência).</small>
      </div>
      <div style="opacity:.6;">✕</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# KPIs
# =========================
m2_total = float(df_f["m2_total"].sum())
dias = int(df_f["DATA"].nunique())
m2_por_dia = (m2_total / dias) if dias else 0.0
equipes_ativas = int(df_f["EQUIPE"].nunique()) if "EQUIPE" in df_f.columns else 0
registros = int(len(df_f))

k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.markdown(kpi_card("m² total", fmt_int_br(m2_total), "🧱"), unsafe_allow_html=True)
with k2: st.markdown(kpi_card("m² / dia (média)", fmt_int_br(m2_por_dia), "📈"), unsafe_allow_html=True)
with k3: st.markdown(kpi_card("Dias", str(dias), "🗓️"), unsafe_allow_html=True)
with k4: st.markdown(kpi_card("Equipes ativas", str(equipes_ativas), "👷"), unsafe_allow_html=True)
with k5: st.markdown(kpi_card("Registros", str(registros), "🧾"), unsafe_allow_html=True)

st.write("")

# =========================
# Charts (cards)
# =========================
c1, c2 = st.columns([1.35, 1])

with c1:
    st.markdown('<div class="card"><div class="section-title">Tendência</div><div class="section-sub">m² por dia</div>', unsafe_allow_html=True)
    trend = df_f.groupby("DATA", as_index=False)["m2_total"].sum().sort_values("DATA")

    chart = alt.Chart(trend).mark_area(
        line={"color": "#2563eb", "strokeWidth": 3},
        opacity=0.18
    ).encode(
        x=alt.X("DATA:T", title=None),
        y=alt.Y("m2_total:Q", title=None),
        tooltip=[alt.Tooltip("DATA:T", title="Data"),
                 alt.Tooltip("m2_total:Q", title="m²", format=",.0f")]
    ).properties(height=260)

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card"><div class="section-title">Ranking</div><div class="section-sub">Top equipes por m²</div>', unsafe_allow_html=True)
    rank = df_f.groupby("EQUIPE", as_index=False)["m2_total"].sum().sort_values("m2_total", ascending=False).head(10)

    bar = alt.Chart(rank).mark_bar(
        cornerRadiusTopRight=10, cornerRadiusBottomRight=10, color="#2563eb"
    ).encode(
        y=alt.Y("EQUIPE:N", sort="-x", title=None),
        x=alt.X("m2_total:Q", title=None),
        tooltip=[alt.Tooltip("EQUIPE:N", title="Equipe"),
                 alt.Tooltip("m2_total:Q", title="m²", format=",.0f")]
    ).properties(height=260)

    st.altair_chart(bar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

c3, c4 = st.columns([1, 1])

with c3:
    st.markdown('<div class="card"><div class="section-title">Composição</div><div class="section-sub">Manual vs Tratores vs Robô</div>', unsafe_allow_html=True)
    comp_df = pd.DataFrame({
        "Tipo": ["Manual", "Tratores", "Robô"],
        "m2": [float(df_f["m2_manual"].sum()), float(df_f["m2_tratores"].sum()), float(df_f["m2_robo"].sum())]
    })

    donut = alt.Chart(comp_df).mark_arc(innerRadius=70).encode(
        theta=alt.Theta("m2:Q"),
        color=alt.Color("Tipo:N", scale=alt.Scale(range=["#94a3b8", "#2563eb", "#10b981"]), legend=alt.Legend(title=None)),
        tooltip=[alt.Tooltip("Tipo:N", title="Tipo"),
                 alt.Tooltip("m2:Q", title="m²", format=",.0f")]
    ).properties(height=260)

    st.altair_chart(donut, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="card"><div class="section-title">Qualidade</div><div class="section-sub">checagens rápidas</div>', unsafe_allow_html=True)
    zero = int((df_f["m2_total"] <= 0).sum())
    st.markdown(f"- **m² = 0**: {zero} registros")
    st.markdown(f"- **Outliers** (p95): {outliers} registros")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="badge blue">Recomendação</span>', unsafe_allow_html=True)
    st.markdown("Validar KM e LARGURA nos registros fora do padrão para consolidar números oficiais.")
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# =========================
# Detail table (card)
# =========================
st.markdown('<div class="card"><div class="section-title">Detalhe</div><div class="section-sub">registros filtrados (ordenados por m²)</div>', unsafe_allow_html=True)

cols = [c for c in ["DATA", "SUPERVISOR", "NOME DO ENCARREGADO", "EQUIPE", "m2_total", "m2_manual", "m2_tratores", "m2_robo"] if c in df_f.columns]
df_show = df_f[cols].copy().sort_values("m2_total", ascending=False)

a, b = st.columns([1, 1])
with a:
    show_all = st.checkbox("Mostrar todas as linhas", value=False)
with b:
    only_zero = st.checkbox("Somente m² = 0 (checagem)", value=False)

if only_zero:
    df_show = df_show[df_show["m2_total"] <= 0]
if not show_all:
    df_show = df_show.head(500)

st.dataframe(df_show, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

st.caption("Nota: m² = |KM FINAL − KM INICIAL| × 1000 × LARGURA(m). Linhas incompletas tendem a gerar m²=0.")
