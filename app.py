"""
Mental Health in Tech — interactive dashboard
=============================================
Run with:  streamlit run app.py

Every number shown here comes from src/data_prep.py, the same module the EDA
notebook imports, so the dashboard and the report can never disagree.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
sys.path.append(str(ROOT / "src"))

from data_prep import (  # noqa: E402
    COMPANY_SIZE_ORDER,
    INTERFERE_ORDER,
    LEAVE_ORDER,
    SUPPORT_COLS,
    clean,
    encode_for_correlation,
    load_raw,
    treatment_rate,
)

# --------------------------------------------------------------------------- #
# Page config + design tokens
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Mental Health in Tech · OSMI 2014",
    page_icon="◍",
    layout="wide",
    initial_sidebar_state="expanded",
)

INK = "#142027"
PAPER = "#F5F7F6"
TEAL = "#157A6E"
CORAL = "#C1583F"
AMBER = "#D9A441"
PLUM = "#6B4E71"
MIST = "#9DB2B5"
SEQ = [TEAL, CORAL, AMBER, PLUM, MIST, "#7A9E9F"]
BINARY = {"Yes": TEAL, "No": CORAL, "Maybe": AMBER, "Don't know": AMBER, "Not sure": AMBER,
          "Some of them": "#4F8F84"}

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif; }}
    .stApp {{ background: {PAPER}; color: {INK}; }}

    h1, h2, h3 {{ font-family: 'Newsreader', Georgia, serif !important;
                  font-weight: 600 !important; color: {INK} !important;
                  letter-spacing: -0.01em; }}

    /* ---- masthead ---- */
    .masthead {{ border-bottom: 2px solid {INK}; padding: 0.2rem 0 1.1rem 0; margin-bottom: 1.6rem; }}
    .masthead h1 {{ font-size: 2.6rem; line-height: 1.1; margin: 0 0 .45rem 0; }}
    .masthead p {{ margin: 0; color: #4B5C63; font-size: .95rem; max-width: 62ch; }}
    .dek {{ display:inline-block; font-size:.74rem; letter-spacing:.06em; color:{TEAL};
            border:1px solid {TEAL}; border-radius:2px; padding:.14rem .5rem; margin-bottom:.7rem; }}

    /* ---- stat blocks ---- */
    .stat {{ border-top: 3px solid {TEAL}; padding: .85rem .1rem .2rem 0; }}
    .stat .v {{ font-family:'Newsreader',serif; font-size: 2.5rem; line-height: 1;
                font-weight: 600; color: {INK}; }}
    .stat .k {{ font-size: .8rem; color: #566A70; margin-top: .35rem; }}
    .stat.alt {{ border-top-color: {CORAL}; }}
    .stat.warn {{ border-top-color: {AMBER}; }}
    .stat.plum {{ border-top-color: {PLUM}; }}

    /* ---- takeaway note ---- */
    .note {{ background: #EAF0EE; border-left: 3px solid {TEAL}; padding: .75rem .95rem;
             font-size: .9rem; color: #31444B; border-radius: 0 3px 3px 0; margin-top:.3rem; }}

    section[data-testid="stSidebar"] {{ background: #ECF0EE; border-right: 1px solid #D8E0DD; }}
    section[data-testid="stSidebar"] h2 {{ font-size: 1.05rem !important; }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 1.6rem; border-bottom: 1px solid #D8E0DD; }}
    .stTabs [data-baseweb="tab"] {{ padding: .45rem 0; background: transparent; font-size: .93rem; }}
    .stTabs [aria-selected="true"] {{ color: {TEAL} !important;
                                      border-bottom: 2px solid {TEAL} !important; }}
    [data-testid="stDataFrame"] {{ border: 1px solid #D8E0DD; }}
    footer, #MainMenu {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Streamlit renamed `use_container_width=True` to `width="stretch"` in 1.49.
# Detect once so the app runs cleanly on both old and new installs.
_V = tuple(int(p) for p in st.__version__.split(".")[:2] if p.isdigit())
STRETCH = {"width": "stretch"} if _V >= (1, 49) else {"use_container_width": True}


def style(fig: go.Figure, height: int = 380, legend_top: bool = True) -> go.Figure:
    """One place that makes every Plotly chart look like it belongs to this report."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=46, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color=INK),
        title_font=dict(family="Newsreader, serif", size=16, color=INK),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter"),
        legend=dict(orientation="h", y=1.02, x=0, yanchor="bottom", title_text="")
        if legend_top
        else {},
    )
    fig.update_xaxes(showgrid=False, linecolor="#D8E0DD", zeroline=False)
    fig.update_yaxes(gridcolor="#E2E8E6", zeroline=False, linecolor="rgba(0,0,0,0)")
    return fig


def stat(col, value, label, variant=""):
    col.markdown(
        f'<div class="stat {variant}"><div class="v">{value}</div>'
        f'<div class="k">{label}</div></div>',
        unsafe_allow_html=True,
    )


def note(text: str):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner="Cleaning the survey…")
def get_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = load_raw(ROOT / "data" / "survey.csv")
    return raw, clean(raw)


try:
    raw, full = get_data()
except FileNotFoundError:
    st.error("survey.csv is missing. Put it back in the data/ folder and reload.")
    st.stop()

# --------------------------------------------------------------------------- #
# Sidebar filters
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("## Filter the sample")
    st.caption("Every chart on the page responds to these.")

    countries = ["All countries"] + (
        full["Country"].value_counts().loc[lambda s: s >= 10].index.tolist()
    )
    country = st.selectbox("Country", countries)

    genders = st.multiselect(
        "Gender", full["Gender"].unique().tolist(), default=full["Gender"].unique().tolist()
    )
    age = st.slider("Age range", int(full["Age"].min()), int(full["Age"].max()), (18, 65))
    sizes = st.multiselect("Company size", COMPANY_SIZE_ORDER, default=COMPANY_SIZE_ORDER)
    remote = st.radio("Remote work", ["Everyone", "Remote only", "On-site only"], horizontal=False)

    st.divider()
    st.caption(
        "Source: Open Sourcing Mental Illness (OSMI) 2014 survey · 1,259 raw responses, "
        "1,251 after removing impossible ages."
    )
    if st.button("Reset filters", **STRETCH):
        st.rerun()

df = full.copy()
if country != "All countries":
    df = df[df["Country"] == country]
if genders:
    df = df[df["Gender"].isin(genders)]
df = df[df["Age"].between(*age)]
if sizes:
    df = df[df["no_employees"].isin(sizes)]
if remote == "Remote only":
    df = df[df["remote_work"] == "Yes"]
elif remote == "On-site only":
    df = df[df["remote_work"] == "No"]

# --------------------------------------------------------------------------- #
# Masthead
# --------------------------------------------------------------------------- #
st.markdown(
    """
    <div class="masthead">
      <span class="dek">OSMI survey · 2014 · exploratory data analysis</span>
      <h1>Half of tech had already asked for help.<br>Most workplaces never noticed.</h1>
      <p>1,251 people in technology answered 27 questions about mental health at work — what their
      employer offers, and whether they would ever use it. This dashboard is the interactive half
      of the analysis; the notebook carries the full write-up.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if len(df) < 25:
    st.warning(
        f"Only {len(df)} responses match these filters. Percentages below will be unstable — "
        "widen the selection before reading anything into them."
    )

c1, c2, c3, c4, c5 = st.columns(5)
stat(c1, f"{len(df):,}", "respondents in view")
stat(c2, f"{df['Treated'].mean()*100:.0f}%", "have sought treatment", "alt")
stat(c3, f"{(df['work_interfere'] != 'Not applicable').mean()*100:.0f}%", "report a condition", "warn")
stat(c4, f"{(df['Employer_Support_Score'] == 0).mean()*100:.0f}%", "get zero employer support", "plum")
unsure_anon = (df["anonymity"] == "Don't know").mean() * 100
stat(c5, f"{unsure_anon:.0f}%", "unsure about anonymity")

st.write("")

tab_over, tab_who, tab_work, tab_stigma, tab_deep, tab_data = st.tabs(
    ["Overview", "Who answered", "The workplace", "Stigma", "Deep dive", "The data"]
)

# --------------------------------------------------------------------------- #
# 1. Overview
# --------------------------------------------------------------------------- #
with tab_over:
    left, right = st.columns([1.15, 1])

    with left:
        t = df["treatment"].value_counts()
        fig = go.Figure(
            go.Pie(
                labels=t.index, values=t.values, hole=0.66, sort=False,
                marker=dict(colors=[BINARY[i] for i in t.index],
                            line=dict(color=PAPER, width=3)),
                textinfo="none", hovertemplate="%{label}: %{value} people (%{percent})<extra></extra>",
            )
        )
        rate = df["Treated"].mean() * 100
        fig.add_annotation(text=f"<b>{rate:.0f}%</b>", showarrow=False, font=dict(size=46, color=TEAL))
        fig.add_annotation(text="sought treatment", y=0.36, showarrow=False,
                           font=dict(size=13, color=INK))
        st.plotly_chart(style(fig, 400).update_layout(title="The headline number", showlegend=False),
                        **STRETCH)
        note(
            "An almost even split. Mental illness in this workforce is not an edge case affecting "
            "a handful of employees — it is a coin flip."
        )

    with right:
        wi = treatment_rate(df, "work_interfere").set_index("work_interfere")
        order = [c for c in ["Not applicable", "Never", "Rarely", "Sometimes", "Often"]
                 if c in wi.index]
        wi = wi.reindex(order)
        fig = go.Figure(
            go.Scatter(
                x=wi.index, y=wi["rate"], mode="lines+markers+text",
                text=[f"{v:.0f}%" for v in wi["rate"]], textposition="top center",
                line=dict(color=TEAL, width=3), marker=dict(size=11, color=TEAL),
                fill="tozeroy", fillcolor="rgba(21,122,110,0.10)",
                hovertemplate="%{x}: %{y:.1f}% treated<extra></extra>",
            )
        )
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(
            style(fig, 400).update_layout(title="People wait until work suffers"),
            **STRETCH,
        )
        note(
            "Treatment tracks severity almost perfectly (r = 0.65, the strongest relationship in "
            "the dataset). The jump happens the moment work is affected at all — which means the "
            "opportunity sits upstream of that point."
        )

    st.markdown("### What actually moves the treatment rate")
    enc = encode_for_correlation(df)
    corr = enc.corr()["treatment"].drop("treatment").sort_values(key=abs, ascending=False).head(10)
    fig = go.Figure(
        go.Bar(
            x=corr.values[::-1], y=corr.index[::-1], orientation="h",
            marker_color=[TEAL if v > 0 else CORAL for v in corr.values[::-1]],
            text=[f"{v:+.2f}" for v in corr.values[::-1]], textposition="outside",
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )
    fig.update_xaxes(range=[min(corr.min() * 1.4, -0.1), corr.max() * 1.25])
    st.plotly_chart(
        style(fig, 420, legend_top=False).update_layout(
            title="Correlation with having sought treatment (ordinal-encoded)"
        ),
        **STRETCH,
    )
    note(
        "Work interference and family history dominate. Among the things an employer controls, "
        "<b>knowing your care options</b> outranks every individual benefit — awareness beats "
        "provision."
    )

# --------------------------------------------------------------------------- #
# 2. Who answered
# --------------------------------------------------------------------------- #
with tab_who:
    a, b = st.columns(2)

    with a:
        fig = px.histogram(df, x="Age", nbins=28, color_discrete_sequence=[TEAL])
        fig.update_traces(marker_line_color=PAPER, marker_line_width=1.5,
                          hovertemplate="Age %{x}: %{y} people<extra></extra>")
        fig.add_vline(x=df["Age"].median(), line_dash="dash", line_color=CORAL,
                      annotation_text=f"median {df['Age'].median():.0f}",
                      annotation_font_color=CORAL)
        st.plotly_chart(style(fig, 340, False).update_layout(
            title="A workforce in its early thirties", yaxis_title="respondents"),
            **STRETCH)

        tg = treatment_rate(df, "Gender")
        fig = go.Figure(go.Bar(
            x=tg["Gender"], y=tg["rate"],
            marker_color=[PLUM if g.startswith("Non") else TEAL if g == "Female" else CORAL
                          for g in tg["Gender"]],
            text=[f"{r:.0f}%<br><span style='font-size:10px'>n={n}</span>"
                  for r, n in zip(tg["rate"], tg["n"])],
            textposition="outside",
            hovertemplate="%{x}: %{y:.1f}% treated<extra></extra>",
        ))
        fig.update_yaxes(range=[0, 108], ticksuffix="%")
        st.plotly_chart(style(fig, 340, False).update_layout(
            title="Treatment rate by gender"), **STRETCH)
        note(
            "Women seek treatment far more often than men. Clinical prevalence does not differ "
            "by anything like this margin — so this reads as a help-seeking gap, not a health gap. "
            "Men are 79% of this sample."
        )

    with b:
        top = df["Country"].value_counts().head(10)
        fig = go.Figure(go.Bar(
            x=top.values[::-1], y=top.index[::-1], orientation="h",
            marker_color=[TEAL if i == len(top) - 1 else MIST for i in range(len(top))],
            text=top.values[::-1], textposition="outside",
            hovertemplate="%{y}: %{x} responses<extra></extra>",
        ))
        st.plotly_chart(style(fig, 340, False).update_layout(
            title="Where the responses come from", xaxis_title="respondents"),
            **STRETCH)

        fh = pd.crosstab(df["family_history"], df["treatment"], normalize="index") * 100
        fig = go.Figure()
        for col in [c for c in ["Yes", "No"] if c in fh.columns]:
            fig.add_bar(x=fh.index, y=fh[col], name=f"Treatment: {col}",
                        marker_color=BINARY[col],
                        hovertemplate="%{y:.1f}%<extra></extra>")
        fig.update_layout(barmode="stack")
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(style(fig, 340).update_layout(
            title="Family history is the strongest personal predictor",
            xaxis_title="family history of mental illness"), **STRETCH)
        note(
            "People with a family history seek treatment at roughly double the rate. Growing up "
            "around mental illness appears to remove the barrier to naming it — which is exactly "
            "what workplace education is trying to replicate."
        )

# --------------------------------------------------------------------------- #
# 3. The workplace
# --------------------------------------------------------------------------- #
with tab_work:
    st.markdown("### What employers provide — and what employees know about it")

    sup = (df[SUPPORT_COLS].apply(lambda s: s.value_counts(normalize=True) * 100)
           .T.reindex(columns=["Yes", "No", "Don't know", "Not sure"]).fillna(0))
    sup.index = ["Health benefits", "Knows care options", "Wellness programme",
                 "Seek-help resources", "Anonymity protected"]
    fig = go.Figure()
    for col, color in zip(sup.columns, [TEAL, CORAL, AMBER, "#E8C77A"]):
        fig.add_bar(y=sup.index, x=sup[col], name=col, orientation="h",
                    marker_color=color, hovertemplate="%{y} — " + col + ": %{x:.0f}%<extra></extra>")
    fig.update_layout(barmode="stack")
    fig.update_xaxes(range=[0, 100], ticksuffix="%")
    st.plotly_chart(style(fig, 360).update_layout(
        title="The most common answer is not 'no' — it is 'I don't know'"),
        **STRETCH)
    note(
        "Two thirds cannot say whether their anonymity is protected, and a third cannot say "
        "whether they have benefits at all. Uncertainty — not absence — is the biggest block, "
        "and it is the cheapest one to fix."
    )

    a, b = st.columns(2)
    with a:
        es = treatment_rate(df, "Employer_Support_Score").sort_values("Employer_Support_Score")
        fig = go.Figure(go.Bar(
            x=es["Employer_Support_Score"], y=es["rate"],
            marker_color=[CORAL if s <= 1 else AMBER if s == 2 else TEAL
                          for s in es["Employer_Support_Score"]],
            text=[f"{r:.0f}%<br><span style='font-size:10px'>n={n}</span>"
                  for r, n in zip(es["rate"], es["n"])],
            textposition="outside", hovertemplate="score %{x}: %{y:.1f}% treated<extra></extra>",
        ))
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(style(fig, 380, False).update_layout(
            title="More support, more treatment — up to a point",
            xaxis_title="supports provided (of 5)"), **STRETCH)
        note(
            "The climb is steep to three supports and then flattens. The argument to a budget "
            "holder is 'do three things properly', not 'buy everything'."
        )

    with b:
        sizes_present = [s for s in COMPANY_SIZE_ORDER if s in df["no_employees"].unique()]
        tr = treatment_rate(df, "no_employees").set_index("no_employees").reindex(sizes_present)
        avg = df.groupby("no_employees", observed=True)["Employer_Support_Score"].mean().reindex(
            sizes_present)
        fig = go.Figure()
        fig.add_bar(x=sizes_present, y=tr["rate"], name="Treatment rate", marker_color=MIST,
                    hovertemplate="%{x}: %{y:.1f}% treated<extra></extra>")
        fig.add_trace(go.Scatter(x=sizes_present, y=avg.values, name="Avg support score",
                                 yaxis="y2", mode="lines+markers",
                                 line=dict(color=TEAL, width=3), marker=dict(size=10),
                                 hovertemplate="%{x}: %{y:.2f} of 5<extra></extra>"))
        fig.update_layout(yaxis=dict(ticksuffix="%", range=[0, 100]),
                          yaxis2=dict(overlaying="y", side="right", range=[0, 3.4],
                                      showgrid=False, title="support score"))
        st.plotly_chart(style(fig, 380).update_layout(
            title="Big companies provide more and get barely more"),
            **STRETCH)
        note(
            "Support rises sharply with headcount; the treatment rate does not follow. Enterprise "
            "spend is leaking somewhere between the benefits page and the employee."
        )

    lv = df["leave"].value_counts().reindex([c for c in LEAVE_ORDER if c in df["leave"].unique()])
    fig = go.Figure(go.Bar(
        x=lv.index, y=lv.values, text=lv.values, textposition="outside",
        marker_color=[TEAL, "#4F8F84", AMBER, "#D08A6A", CORAL][:len(lv)],
        hovertemplate="%{x}: %{y} people<extra></extra>",
    ))
    st.plotly_chart(style(fig, 320, False).update_layout(
        title="How easy is it to take mental-health leave?", yaxis_title="respondents"),
        **STRETCH)
    note("The largest group cannot answer the question at all — and an employee who cannot "
         "predict the answer assumes the worst and never asks.")

# --------------------------------------------------------------------------- #
# 4. Stigma
# --------------------------------------------------------------------------- #
with tab_stigma:
    st.markdown("### The same person, two illnesses, two different behaviours")
    a, b = st.columns(2)
    pairs = [
        (a, "mental_health_consequence", "phys_health_consequence",
         "Expect negative consequences if they disclose"),
        (b, "mental_health_interview", "phys_health_interview",
         "Would raise it in a job interview"),
    ]
    for col, m, p, title in pairs:
        cats = ["Yes", "Maybe", "No"]
        mv = df[m].value_counts(normalize=True).reindex(cats).fillna(0) * 100
        pv = df[p].value_counts(normalize=True).reindex(cats).fillna(0) * 100
        fig = go.Figure()
        fig.add_bar(x=cats, y=mv.values, name="Mental health", marker_color=PLUM,
                    hovertemplate="%{x}: %{y:.0f}%<extra>mental</extra>")
        fig.add_bar(x=cats, y=pv.values, name="Physical health", marker_color=MIST,
                    hovertemplate="%{x}: %{y:.0f}%<extra>physical</extra>")
        fig.update_yaxes(ticksuffix="%", range=[0, 95])
        col.plotly_chart(style(fig, 360).update_layout(title=title), **STRETCH)

    note(
        "Because the same respondents answered both questions, this comparison controls for "
        "personality and workplace automatically — the only thing that changed is the illness. "
        "Four in five would stay silent about mental health in an interview, against two in five "
        "for a physical condition."
    )

    a, b = st.columns(2)
    with a:
        audiences = {"Coworkers": "coworkers", "Direct supervisor": "supervisor",
                     "A job interviewer": "mental_health_interview"}
        cats = ["Yes", "Some of them", "Maybe", "No"]
        data = pd.DataFrame(
            {k: df[v].value_counts(normalize=True).reindex(cats).fillna(0) * 100
             for k, v in audiences.items()}
        ).T
        fig = go.Figure()
        for c, color in zip(cats, [TEAL, "#4F8F84", AMBER, CORAL]):
            fig.add_bar(y=data.index, x=data[c], name=c, orientation="h", marker_color=color,
                        hovertemplate="%{y} — " + c + ": %{x:.0f}%<extra></extra>")
        fig.update_layout(barmode="stack")
        fig.update_xaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(style(fig, 340).update_layout(title="Who would you actually tell?"),
                        **STRETCH)
        note("Supervisors are trusted more than coworkers — which makes manager training the "
             "highest-leverage, lowest-cost intervention available.")

    with b:
        mv = df["mental_vs_physical"].value_counts(normalize=True) * 100
        mv = mv.reindex([c for c in ["Yes", "No", "Don't know"] if c in mv.index])
        fig = go.Figure()
        for idx, color in zip(mv.index, [TEAL, CORAL, AMBER]):
            fig.add_bar(y=["parity"], x=[mv[idx]], name=idx, orientation="h",
                        marker_color=color, text=f"{idx} {mv[idx]:.0f}%", insidetextanchor="middle",
                        hovertemplate=idx + ": %{x:.0f}%<extra></extra>")
        fig.update_layout(barmode="stack")
        fig.update_xaxes(range=[0, 100], ticksuffix="%")
        fig.update_yaxes(showticklabels=False)
        st.plotly_chart(style(fig, 200).update_layout(
            title="Does your employer take mental health as seriously as physical?"),
            **STRETCH)

        an = treatment_rate(df, "anonymity").set_index("anonymity")
        an = an.reindex([c for c in ["Yes", "No", "Don't know"] if c in an.index])
        fig = go.Figure(go.Bar(
            x=an.index, y=an["rate"], marker_color=[BINARY[i] for i in an.index],
            text=[f"{r:.0f}%<br><span style='font-size:10px'>n={n}</span>"
                  for r, n in zip(an["rate"], an["n"])],
            textposition="outside", hovertemplate="%{x}: %{y:.1f}% treated<extra></extra>",
        ))
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(style(fig, 300, False).update_layout(
            title="Treatment rate by anonymity protection",
            xaxis_title="is your anonymity protected?"), **STRETCH)

# --------------------------------------------------------------------------- #
# 5. Deep dive — build your own cross-tab
# --------------------------------------------------------------------------- #
with tab_deep:
    st.markdown("### Cross any two questions")
    st.caption(
        "Pick a row and a column. The heatmap shows the treatment rate inside every cell, with "
        "the number of people it is based on — thin cells are not evidence."
    )

    options = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype) == "category"]
    options = [c for c in options if c not in ("state", "Country") and df[c].nunique() <= 8]
    options += ["Age_Group", "Employer_Support_Score", "Openness_Score"]
    options = sorted(set(options))

    c1, c2 = st.columns(2)
    row_var = c1.selectbox("Rows", options, index=options.index("no_employees")
                           if "no_employees" in options else 0)
    col_var = c2.selectbox("Columns", options, index=options.index("benefits")
                           if "benefits" in options else 1)

    if row_var == col_var:
        st.info("Pick two different variables to see a cross-tab.")
    else:
        piv = df.pivot_table(index=row_var, columns=col_var, values="Treated",
                             aggfunc="mean", observed=True) * 100
        cnt = df.pivot_table(index=row_var, columns=col_var, values="Treated",
                             aggfunc="size", observed=True)
        if row_var == "no_employees":
            piv = piv.reindex([s for s in COMPANY_SIZE_ORDER if s in piv.index])
            cnt = cnt.reindex(piv.index)
        text = piv.round(0).astype("Int64").astype(str) + "%<br>n=" + cnt.astype("Int64").astype(str)
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=[str(c) for c in piv.columns], y=[str(i) for i in piv.index],
            text=text.values, texttemplate="%{text}", textfont=dict(size=11, color=INK),
            colorscale=[[0, "#FFFFFF"], [1, TEAL]], zmin=20, zmax=85,
            colorbar=dict(title="% treated", thickness=12),
            hovertemplate=f"{row_var}: %{{y}}<br>{col_var}: %{{x}}<br>%{{z:.1f}}% treated<extra></extra>",
            xgap=3, ygap=3,
        ))
        st.plotly_chart(style(fig, 460, False).update_layout(
            title=f"Treatment rate: {row_var} × {col_var}"), **STRETCH)
        note("Cells with fewer than about 20 people swing wildly. Read the direction of the "
             "pattern, not the individual number.")

    st.markdown("### Rank any question by treatment rate")
    var = st.selectbox("Question", options, index=options.index("care_options")
                       if "care_options" in options else 0, key="rank")
    tr = treatment_rate(df, var)
    fig = go.Figure(go.Bar(
        x=tr["rate"][::-1], y=[str(v) for v in tr[var]][::-1], orientation="h",
        marker_color=[TEAL if r >= df["Treated"].mean() * 100 else CORAL
                      for r in tr["rate"]][::-1],
        text=[f"{r:.0f}%  (n={n})" for r, n in zip(tr["rate"], tr["n"])][::-1],
        textposition="outside", hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.update_xaxes(range=[0, 115], ticksuffix="%")
    fig.add_vline(x=df["Treated"].mean() * 100, line_dash="dot", line_color=INK,
                  annotation_text="overall average")
    st.plotly_chart(style(fig, 360, False).update_layout(title=f"Treatment rate by {var}"),
                    **STRETCH)

# --------------------------------------------------------------------------- #
# 6. The data
# --------------------------------------------------------------------------- #
with tab_data:
    st.markdown("### What the cleaning pipeline did")
    c1, c2, c3 = st.columns(3)
    stat(c1, f"{raw.shape[0]:,}", "raw responses")
    stat(c2, f"{full.shape[0]:,}", "after cleaning", "alt")
    stat(c3, f"{raw['Gender'].nunique()} → 3", "gender variants collapsed", "warn")

    st.markdown(
        """
- **Age** filtered to 18–75. The raw file contains −1726 and 99999999999, which would break every
  average and every axis. 8 rows removed.
- **Gender** normalised from 49 free-text spellings into three buckets by rule, not by hand.
- **work_interfere** blanks kept as *"Not applicable"* rather than dropped. Those 264 people are
  almost entirely untreated, so deleting them would have inflated the headline rate from 50% to
  about 62%.
- **self_employed** → "No", **state** → "Not in US", **comments** dropped (87% empty free text).
- **Engineered:** `Employer_Support_Score` (0–5) and `Openness_Score` (0–3).
        """
    )

    st.markdown("### Cleaned data, as filtered")
    st.dataframe(df.head(300), **STRETCH, height=380)
    st.download_button(
        "Download this filtered slice as CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="mental_health_tech_filtered.csv",
        mime="text/csv",
    )

    with st.expander("Missing values in the raw file"):
        miss = pd.DataFrame({
            "missing": raw.isna().sum(),
            "missing_%": (raw.isna().mean() * 100).round(1),
        }).query("missing > 0").sort_values("missing", ascending=False)
        st.dataframe(miss, **STRETCH)

st.write("")
st.caption(
    "Data: Open Sourcing Mental Illness (OSMI), Mental Health in Tech Survey 2014 · "
    "Self-reported and self-selected — every relationship shown here is correlational. "
    "Cleaning logic: src/data_prep.py · Full analysis: notebooks/Mental_Health_in_Tech_EDA.ipynb"
)
