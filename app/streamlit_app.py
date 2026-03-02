from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from logisticama.adapters.ingest.loaders import FileLogSource, UploadedLogSource
from logisticama.adapters.persistence.indexed_repository import IndexedLogRepository
from logisticama.adapters.presentation.theme import apply_theme
from logisticama.application.dto import QueryWindow
from logisticama.application.use_cases import QueryLogisticsDashboard
from logisticama.shared.time_utils import ensure_fortaleza_timestamp


st.set_page_config(
    page_title="Operacao LogisticaMA",
    page_icon="📦",
    layout="wide",
)

apply_theme()


@st.cache_data
def load_demo_frame() -> pd.DataFrame:
    return FileLogSource(Path("data/demo/logistica_ma_demo.csv")).load()


@st.cache_data
def load_uploaded_frame(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    import io

    buffer = io.BytesIO(file_bytes)
    return UploadedLogSource(buffer, file_name).load()


def build_service(frame: pd.DataFrame) -> tuple[QueryLogisticsDashboard, IndexedLogRepository]:
    repository = IndexedLogRepository(frame)
    return QueryLogisticsDashboard(repository), repository


def render_header(frame: pd.DataFrame) -> None:
    start = frame["timestamp_label"].min().strftime("%d/%m/%Y %H:%M")
    end = frame["timestamp_label"].max().strftime("%d/%m/%Y %H:%M")
    st.markdown(
        f"""
        <section class="hero-shell">
          <div class="eyebrow">Projeto de Algoritmos + Dashboard Streamlit</div>
          <h1 class="hero-title">Painel operacional para responder perguntas em segundos.</h1>
          <p class="hero-copy">
            Este app transforma os logs da LogisticaMA em uma sala de comando clara para a banca:
            mostra atrasos, hubs criticos, comportamento no tempo e compara a estrategia indexada
            com a varredura linear classica.
          </p>
          <div class="signal-grid">
            <div class="signal-card">
              <div class="signal-label">Janela do dataset</div>
              <div class="signal-value">{start}</div>
              <div class="metric-note">ate {end}</div>
            </div>
            <div class="signal-card">
              <div class="signal-label">Eventos carregados</div>
              <div class="signal-value">{len(frame):,}</div>
              <div class="metric-note">prontos para consulta</div>
            </div>
            <div class="signal-card">
              <div class="signal-label">Hubs mapeados</div>
              <div class="signal-value">{frame["hub"].nunique()}</div>
              <div class="metric-note">com indice proprio</div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.sidebar.title("Controle da analise")
    st.sidebar.caption("Carregue um arquivo real ou use a base de demonstracao.")

    uploaded_file = st.sidebar.file_uploader("Dataset CSV ou JSON", type=["csv", "json"])
    if uploaded_file is None:
        frame = load_demo_frame()
        data_label = "Base de demonstracao versionada no projeto"
    else:
        file_bytes = uploaded_file.getvalue()
        frame = load_uploaded_frame(file_bytes, uploaded_file.name)
        data_label = f"Arquivo enviado: {uploaded_file.name}"

    service, repository = build_service(frame)
    render_header(frame)
    st.markdown(f'<p class="footer-note">{data_label}</p>', unsafe_allow_html=True)

    timestamp_min = frame["timestamp_label"].min().floor("min")
    timestamp_max = frame["timestamp_label"].max().ceil("min")

    st.sidebar.markdown("### Filtros principais")
    time_range = st.sidebar.slider(
        "Intervalo da consulta",
        min_value=timestamp_min.to_pydatetime(),
        max_value=timestamp_max.to_pydatetime(),
        value=(timestamp_min.to_pydatetime(), timestamp_max.to_pydatetime()),
        format="DD/MM/YY HH:mm",
    )
    min_delay = st.sidebar.slider("Atraso minimo (minutos)", min_value=5, max_value=120, value=30, step=5)

    hubs = ["Todos"] + sorted(frame["hub"].dropna().unique().tolist())
    statuses = ["Todos"] + sorted(frame["status"].dropna().unique().tolist())
    selected_hub = st.sidebar.selectbox("Hub", hubs)
    selected_status = st.sidebar.selectbox("Status", statuses)
    start_local = ensure_fortaleza_timestamp(time_range[0])
    end_local = ensure_fortaleza_timestamp(time_range[1])

    window = QueryWindow(
        start_iso=start_local.isoformat(),
        end_iso=end_local.isoformat(),
        min_delay=min_delay,
        hub=None if selected_hub == "Todos" else selected_hub,
        status=None if selected_status == "Todos" else selected_status,
    )
    summary = service.build_summary(window)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Eventos na janela", f"{summary.total_events:,}")
    col2.metric("Atrasos acima do corte", f"{summary.delayed_events:,}")
    col3.metric("Atraso medio", f"{summary.average_delay:.1f} min")
    col4.metric("Pior atraso", f"{summary.max_delay} min")

    st.markdown(
        """
        <div class="callout">
          <strong>Como ler este painel:</strong> se a porcentagem de atraso cresce e concentra em poucos hubs,
          a operacao perde previsibilidade. A estrategia indexada reduz o tempo de consulta para apoiar decisoes
          de rota, priorizacao de atendimentos e comunicacao com o cliente.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_overview, tab_hubs, tab_timeline, tab_data = st.tabs(
        ["Panorama", "Hubs criticos", "Linha do tempo", "Base carregada"]
    )

    filtered = frame.copy()
    filtered = filtered[
        (filtered["timestamp_label"] >= start_local)
        & (filtered["timestamp_label"] <= end_local)
    ]
    if selected_hub != "Todos":
        filtered = filtered[filtered["hub"] == selected_hub]
    if selected_status != "Todos":
        filtered = filtered[filtered["status"] == selected_status]

    with tab_overview:
        st.markdown('<div class="section-title">Visao executiva da janela selecionada</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">A ideia aqui e permitir que qualquer pessoa veja, em poucos segundos, se o dia esta saudavel ou se a operacao precisa de intervencao.</div>',
            unsafe_allow_html=True,
        )
        chart_col1, chart_col2 = st.columns([1.2, 1])
        with chart_col1:
            trend_frame = (
                filtered.assign(hora_cheia=filtered["timestamp_label"].dt.floor("h"))
                .groupby("hora_cheia", as_index=False)
                .agg(eventos=("id", "count"), atrasos=("esta_atrasado_30", "sum"))
            )
            fig = px.area(
                trend_frame,
                x="hora_cheia",
                y=["eventos", "atrasos"],
                template="plotly_white",
                color_discrete_sequence=["#476B5D", "#C85C2C"],
            )
            fig.update_layout(
                height=360,
                legend_title_text="Serie",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.6)",
                margin=dict(l=10, r=10, t=20, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        with chart_col2:
            status_frame = (
                filtered.groupby("status", as_index=False)
                .agg(eventos=("id", "count"))
                .sort_values("eventos", ascending=False)
            )
            fig = px.bar(
                status_frame,
                x="eventos",
                y="status",
                orientation="h",
                color="eventos",
                color_continuous_scale=["#F1BE94", "#C85C2C", "#883B18"],
                template="plotly_white",
            )
            fig.update_layout(
                height=360,
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.6)",
                margin=dict(l=10, r=10, t=20, b=10),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab_hubs:
        st.markdown('<div class="section-title">Quais hubs estao sob pressao</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">Este quadro resume onde a operacao esta mais fraca dentro da janela escolhida. Quanto maior o percentual, maior a necessidade de acao.</div>',
            unsafe_allow_html=True,
        )
        fortaleza_start = start_local.tz_convert("UTC").timestamp()
        fortaleza_end = end_local.tz_convert("UTC").timestamp()
        hub_frame = repository.performance_by_hub(int(fortaleza_start), int(fortaleza_end), min_delay=min_delay)
        if hub_frame.empty:
            st.info("Nao ha eventos suficientes para montar o ranking de hubs nesse recorte.")
        else:
            fig = px.bar(
                hub_frame,
                x="hub",
                y="percentual_atraso",
                color="percentual_atraso",
                text="atrasos",
                color_continuous_scale=["#476B5D", "#F1BE94", "#C85C2C"],
                template="plotly_white",
            )
            fig.update_traces(texttemplate="%{text}", textposition="outside")
            fig.update_layout(
                height=380,
                yaxis_tickformat=".0%",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(255,255,255,0.6)",
                margin=dict(l=10, r=10, t=20, b=10),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(
                hub_frame.assign(percentual_atraso=hub_frame["percentual_atraso"].map(lambda value: f"{value:.1%}")),
                use_container_width=True,
                hide_index=True,
            )

    with tab_timeline:
        st.markdown('<div class="section-title">Comportamento do atraso ao longo do dia</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">Aqui a banca consegue enxergar quando a fila de problemas sobe e em que horario a equipe perde o controle do fluxo.</div>',
            unsafe_allow_html=True,
        )
        delay_frame = (
            filtered.assign(hora_cheia=filtered["timestamp_label"].dt.floor("h"))
            .groupby(["hora_cheia", "hub"], as_index=False)
            .agg(atraso_medio=("atraso_min", "mean"))
        )
        fig = px.line(
            delay_frame,
            x="hora_cheia",
            y="atraso_medio",
            color="hub",
            template="plotly_white",
        )
        fig.update_layout(
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.6)",
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_data:
        st.markdown('<div class="section-title">Transparencia da base usada</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-copy">Esta tabela ajuda a explicar para um publico nao tecnico o que existe por tras do dashboard e como cada linha representa um evento de rastreamento.</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            filtered[["id", "timestamp_label", "status", "hub", "atraso_min"]].rename(
                columns={"timestamp_label": "timestamp"}
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            label="Baixar recorte filtrado em CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="logistica_ma_recorte.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
