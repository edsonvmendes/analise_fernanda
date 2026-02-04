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
.clock{ color: var(--muted); font-size: 12px; }
.live{
  display:inline-flex;
  align-items:center;
  gap:6px;
  color:#059669;
  font-size: 12px;
  font-weight: 800;
}
.dot{ width:8px; height:8px; border-radius:999px; background:#10b981; display:inline-block; }

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
  white-space: nowrap;
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

# =========================
# Loaders (Excel upload)
# =========================
@st.cache_data(ttl=3600)
def load_excel_data(file_bytes: bytes, sheet_name: str) -> pd.DataFrame:
    # Comentario: Lee el Excel de datos desde bytes (upload), normaliza y calcula m²
    df = pd.read_excel(file_bytes, sheet_name=sheet_name)
    df = normalize_date_column(df, "DATA")
    df = enrich_m2(df)
    return df

@st.cache_data(ttl=3600)
def load_excel_metas(file_bytes: bytes) -> pd.DataFrame:
    # Comentario: Lee el Excel de metas (sheet: Metas)
    df = pd.read_excel(file_bytes, sheet_name="Metas")

    # Comentario: Limpieza mínima y tipado
    needed = ["Nivel", "Referencia", "Metrica", "Periodo", "Meta"]
    for c in needed:
        if c not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente no Excel de metas: {c}")

    df = df.dropna(subset=needed).copy()
    df["Nivel"] = df["Nivel"].astype(str).str.strip()
    df["Referencia"] = df["Referencia"].astype(str).str.strip()
    df["Metrica"] = df["Metrica"].astype(str).str.strip()
    df["Periodo"] = df["Periodo"].astype(str).str.strip()
    df["Meta"] = pd.to_numeric(df["Meta"], errors="coerce")
    df["Prioridade"] = pd.to_numeric(df.get("Prioridade", 99), errors="coerce").fillna(99).astype(int)

    # Comentario: Fechas opcionales (validez)
    if "Ativo de" in df.columns:
        df["Ativo de"] = pd.to_datetime(df["Ativo de"], errors="coerce").dt.date
    else:
        df["Ativo de"] = pd.NaT

    if "Ativo até" in df.columns:
        df["Ativo até"] = pd.to_datetime(df["Ativo até"], errors="coerce").dt.date
    else:
        df["Ativo até"] = pd.NaT

    df = df[df["Meta"].notna()].copy()
    return df

def _metas_validas_no_periodo(df_metas: pd.DataFrame, d1, d2) -> pd.DataFrame:
    # Comentario: Filtra metas por ventana de validez (si existe)
    if df_metas is None or df_metas.empty:
        return df_metas
    df = df_metas.copy()
    # Comentario: Si no hay fecha, consideramos válida
    cond_ini = df["Ativo de"].isna() | (df["Ativo de"] <= d2)
    cond_fim = df["Ativo até"].isna() | (df["Ativo até"] >= d1)
    return df[cond_ini & cond_fim].copy()

def resolve_meta_diaria_m2_total(df_metas: pd.DataFrame, contexto: dict, d1, d2) -> float | None:
    """
    Comentario: Devuelve la meta (Dia, m2_total) según jerarquía:
    Equipe > Supervisor > Encarregado > Tipo > Geral
    """
    if df_metas is None or df_metas.empty:
        return None

    df = _metas_validas_no_periodo(df_metas, d1, d2)

    # Comentario: Solo para este MVP: m2_total y Dia
    df = df[(df["Metrica"] == "m2_total") & (df["Periodo"] == "Dia")].copy()
    if df.empty:
        return None

    ordem = ["Equipe", "Supervisor", "Encarregado", "Tipo", "Geral"]
    for nivel in ordem:
        if nivel == "Geral":
            ref = "ALL"
        else:
            ref = contexto.get(nivel)

        if not ref:
            continue

        cand = df[(df["Nivel"] == nivel) & (df["Referencia"] == str(ref).strip())].copy()
        if not cand.empty:
            return float(cand.sort_values("Prioridade").iloc[0]["Meta"])

    return None

# =========================
# Sidebar: Acesso + Upload
# =========================
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")

with st.sidebar:
    st.markdown("## Acesso")
    pwd = st.text_input("Senha", type="password")
    if APP_PASSWORD and pwd != APP_PASSWORD:
        st.warning("Acesso restrito.")
        st.stop()

    st.markdown("## Carregar dados")
    up_data = st.file_uploader("Upload do Excel (dados) — .xlsx", type=["xlsx"], key="dados")
    sheet_name = st.text_input("Nome da aba (dados)", value="Respostas ao formulário 1")

    st.markdown("## Metas (opcional)")
    up_metas = st.file_uploader("Upload do Excel (metas) — .xlsx", type=["xlsx"], key="metas")

    colA, colB = st.columns(2)
    with colA:
        processar = st.button("📥 Processar")
    with colB:
        limpar = st.button("🧹 Limpar sessão")

    if limpar:
        st.cache_data.clear()
        st.session_state.pop("df", None)
        st.session_state.pop("df_metas", None)
        st.session_state.pop("meta", None)
        st.session_state.pop("meta_context", None)

# =========================
# Processamento por botão
# =========================
if processar:
    if up_data is None:
        st.error("Faça upload do Excel de dados primeiro.")
        st.stop()

    try:
        df_loaded = load_excel_data(up_data.getvalue(), sheet_name)
    except Exception as e:
        st.error(f"Erro ao ler o Excel/aba de dados. Verifique o nome da aba. Detalhe: {e}")
        st.stop()

    st.session_state["df"] = df_loaded

    # Comentario: Metas son opcionales
    if up_metas is not None:
        try:
            dfm = load_excel_metas(up_metas.getvalue())
            st.session_state["df_metas"] = dfm
        except Exception as e:
            st.error(f"Erro ao ler o Excel de metas (aba 'Metas'). Detalhe: {e}")
            st.stop()
    else:
        st.session_state["df_metas"] = None

# =========================
# Estado: sem dados carregados
# =========================
if "df" not in st.session_state:
    st.markdown("""
    <div class="card">
      <div class="section-title">Como usar</div>
      <div class="section-sub">MVP online (upload do Excel)</div>
      <ol style="color:#334155; margin:0; padding-left:18px;">
        <li>Digite a senha</li>
        <li>Faça upload do Excel (dados)</li>
        <li>Confirme o nome da aba</li>
        <li>(Opcional) Faça upload do Excel (metas)</li>
        <li>Clique em <b>Processar</b></li>
      </ol>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = st.session_state["df"]
df_metas = st.session_state.get("df_metas", None)

if df.empty:
    st.warning("A base carregada está vazia após normalização de DATA.")
    st.stop()

# =========================
# Sidebar filtros (depois do carregamento)
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
# KPIs principais
# =========================
m2_total = float(df_f["m2_total"].sum())
dias = int(df_f["DATA"].nunique())
m2_por_dia = (m2_total / dias) if dias else 0.0
equipes_ativas = int(df_f["EQUIPE"].nunique()) if "EQUIPE" in df_f.columns else 0
registros = int(len(df_f))

# =========================
# Resolver meta (m²/dia para m2_total)
# =========================
# Comentario: Si hay múltiples selecciones, este MVP aplica meta por "Equipe" SOLO si hay 1 equipo seleccionado.
contexto = {}
if len(sel_equipes) == 1:
    contexto["Equipe"] = sel_equipes[0]
if len(sel_sup) == 1:
    contexto["Supervisor"] = sel_sup[0]
if len(sel_enc) == 1:
    contexto["Encarregado"] = sel_enc[0]

meta_diaria = resolve_meta_diaria_m2_total(df_metas, contexto, d1, d2)

# Badge da meta
badge_meta_text = None
badge_meta_kind = "blue"
if meta_diaria is None:
    badge_meta_text = "Sem meta"
    badge_meta_kind = "blue"
else:
    if m2_por_dia >= meta_diaria:
        badge_meta_text = f"🟢 Meta: {fmt_int_br(meta_diaria)}"
        badge_meta_kind = "green"
    else:
        badge_meta_text = f"🔴 Meta: {fmt_int_br(meta_diaria)}"
        badge_meta_kind = "red"

# =========================
# KPIs row (cards)
# =========================
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi_card("m² total", fmt_int_br(m2_total), "🧱"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("m² / dia (média)", fmt_int_br(m2_por_dia), "📈", badge_meta_text, badge_meta_kind), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Dias", str(dias), "🗓️"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Equipes ativas", str(equipes_ativas), "👷"), unsafe_allow_html=True)
with k5:
    st.markdown(kpi_card("Registros", str(registros), "🧾"), unsafe_allow_html=True)

# Mensagem rápida sobre contexto
if meta_diaria is not None:
    if len(sel_equipes) != 1:
        st.caption("Meta aplicada: usando regra mais geral disponível (ou nível diferente de Equipe), porque há 0 ou várias equipes selecionadas.")
else:
    st.caption("Nenhuma meta aplicada. (Opcional) Faça upload do Excel de metas para ativar comparação.")

st.write("")

# =========================
# Charts (cards)
# =========================
c1, c2 = st.columns([1.35, 1])

with c1:
    st.markdown('<div class="card"><div class="section-title">Tendência</div><div class="section-sub">m² por dia</div>', unsafe_allow_html=True)

    trend = df_f.groupby("DATA", as_index=False)["m2_total"].sum().sort_values("DATA")

    area = alt.Chart(trend).mark_area(
        line={"color": "#2563eb", "strokeWidth": 3},
        opacity=0.18
    ).encode(
        x=alt.X("DATA:T", title=None),
        y=alt.Y("m2_total:Q", title=None),
        tooltip=[
            alt.Tooltip("DATA:T", title="Data"),
            alt.Tooltip("m2_total:Q", title="m²", format=",.0f")
        ]
    )

    layers = [area]

    # Comentario: Línea de meta (si existe)
    if meta_diaria is not None:
        meta_line = alt.Chart(pd.DataFrame({"meta": [meta_diaria]})).mark_rule(
            color="#ef4444", strokeWidth=2
        ).encode(
            y="meta:Q",
            tooltip=[alt.Tooltip("meta:Q", title="Meta (m²/dia)", format=",.0f")]
        )
        layers.append(meta_line)

    st.altair_chart(alt.layer(*layers).properties(height=260), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card"><div class="section-title">Ranking</div><div class="section-sub">Top equipes por m²</div>', unsafe_allow_html=True)

    rank = df_f.groupby("EQUIPE", as_index=False)["m2_total"].sum().sort_values("m2_total", ascending=False).head(10)
    bar = alt.Chart(rank).mark_bar(
        cornerRadiusTopRight=10, cornerRadiusBottomRight=10, color="#2563eb"
    ).encode(
        y=alt.Y("EQUIPE:N", sort="-x", title=None),
        x=alt.X("m2_total:Q", title=None),
        tooltip=[
            alt.Tooltip("EQUIPE:N", title="Equipe"),
            alt.Tooltip("m2_total:Q", title="m²", format=",.0f")
        ]
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
        color=alt.Color("Tipo:N", scale=alt.Scale(range=["#94a3b8", "#2563eb", "#10b981"]),
                        legend=alt.Legend(title=None)),
        tooltip=[
            alt.Tooltip("Tipo:N", title="Tipo"),
            alt.Tooltip("m2:Q", title="m²", format=",.0f")
        ]
    ).properties(height=260)

    st.altair_chart(donut, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="card"><div class="section-title">Qualidade</div><div class="section-sub">checagens rápidas</div>', unsafe_allow_html=True)

    zero = int((df_f["m2_total"] <= 0).sum())
    st.markdown(f"- **m² = 0**: {zero} registros")
    st.markdown(f"- **Outliers** (p95): {outliers} registros")

    st.markdown("<br>", unsafe_allow_html=True)
    if meta_diaria is None:
        st.markdown('<span class="badge blue">Meta</span>', unsafe_allow_html=True)
        st.markdown("Upload do Excel de metas para ativar comparação automática.")
    else:
        if m2_por_dia >= meta_diaria:
            st.markdown('<span class="badge green">Meta atingida</span>', unsafe_allow_html=True)
            st.markdown(f"Média diária: **{fmt_int_br(m2_por_dia)}** ≥ Meta: **{fmt_int_br(meta_diaria)}**")
        else:
            st.markdown('<span class="badge red">Abaixo da meta</span>', unsafe_allow_html=True)
            st.markdown(f"Média diária: **{fmt_int_br(m2_por_dia)}** < Meta: **{fmt_int_br(meta_diaria)}**")

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
