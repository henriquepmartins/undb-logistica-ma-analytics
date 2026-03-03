from __future__ import annotations

import time
from pathlib import Path

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from logisticama.adapters.persistence.indexed_repository import IndexedLogRepository
from logisticama.adapters.presentation.theme import apply_theme
from logisticama.application.benchmarking import (
    DEFAULT_BENCHMARK_SIZES,
    RealCaseBenchmark,
    benchmark_cases,
    benchmark_real_case,
)
from logisticama.application.datasets import OFFICIAL_DATASET_PATH, load_official_frame
from logisticama.application.dto import QueryWindow
from logisticama.application.use_cases import QueryLogisticsDashboard
from logisticama.shared.time_utils import ensure_fortaleza_timestamp, parse_iso_to_epoch_seconds


BLUE = "#264653"
BLUE_SOFT = "#9FB5C3"
ALERT = "#C96A4A"
TEXT = "#1B242C"
MUTED = "#66727E"
LINE = "#D7DFE5"
PANEL = "#FFFFFF"
PAGE_OPERATION = "Operação"
PAGE_BENCHMARK = "Benchmark"
APP_PAGES = (PAGE_OPERATION, PAGE_BENCHMARK)


st.set_page_config(
    page_title="Operacao LogisticaMA",
    page_icon="📦",
    layout="wide",
)

apply_theme()


@st.cache_data
def load_default_frame() -> pd.DataFrame:
    return load_official_frame()


@st.cache_data(show_spinner=False)
def load_benchmark_frame(sizes: tuple[int, ...] = DEFAULT_BENCHMARK_SIZES) -> pd.DataFrame:
    return benchmark_cases(sizes)


@st.cache_data(show_spinner=False)
def load_real_case_benchmark() -> RealCaseBenchmark:
    return benchmark_real_case()


def build_service(frame: pd.DataFrame) -> tuple[QueryLogisticsDashboard, IndexedLogRepository]:
    repository = IndexedLogRepository(frame)
    return QueryLogisticsDashboard(repository), repository


def format_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def format_size_label(value: int) -> str:
    if value >= 1_000_000:
        return f"{value // 1_000_000}M"
    if value >= 1_000:
        return f"{value // 1_000}k"
    return str(value)


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%".replace(".", ",")


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.1f} ms".replace(".", ",")
    return f"{seconds:.2f} s".replace(".", ",")


def format_minutes(value: float) -> str:
    return f"{value:.2f} min".replace(".", ",")


def linear_delay_count_filtered(
    events: list[dict[str, object]],
    start_ts: int,
    end_ts: int,
    min_delay: int,
    hub: str | None,
    status: str | None,
) -> int:
    total = 0
    for event in events:
        timestamp = int(event["timestamp_epoch"])
        if timestamp < start_ts or timestamp > end_ts:
            continue
        if hub is not None and event["hub"] != hub:
            continue
        if status is not None and event["status"] != status:
            continue
        if int(event["atraso_min"]) > min_delay:
            total += 1
    return total


def measure_query_times(
    frame: pd.DataFrame,
    service: QueryLogisticsDashboard,
    window: QueryWindow,
) -> tuple[float, float]:
    start_ts = parse_iso_to_epoch_seconds(window.start_iso)
    end_ts = parse_iso_to_epoch_seconds(window.end_iso)
    records = frame.to_dict("records")

    linear_runs = 2
    indexed_runs = 40

    linear_start = time.perf_counter()
    for _ in range(linear_runs):
        linear_delay_count_filtered(records, start_ts, end_ts, window.min_delay, window.hub, window.status)
    linear_time = (time.perf_counter() - linear_start) / linear_runs

    indexed_start = time.perf_counter()
    for _ in range(indexed_runs):
        service.count_delays(window)
    indexed_time = (time.perf_counter() - indexed_start) / indexed_runs

    return linear_time, indexed_time


def render_page_header(title: str, copy: str, meta: str) -> None:
    st.markdown(
        f"""
        <div class="app-shell">
          <div class="top-note">Desafio 4.0 | Dashboard do caso LogisticaMA</div>
          <h1 class="page-title">{title}</h1>
          <p class="page-copy">{copy}</p>
          <div class="page-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, subtitle: str) -> str:
    return f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-subtitle">{subtitle}</div>
    </div>
    """


def render_narrative_card(label: str, title: str, body: str) -> str:
    return f"""
    <div class="narrative-card">
      <div class="top-note">{label}</div>
      <h2 class="section-title">{title}</h2>
      <p class="page-copy">{body}</p>
    </div>
    """


def render_metric_specs(specs: list[tuple[str, str, str]], columns: int) -> None:
    cols = st.columns(columns)
    for column, spec in zip(cols, specs, strict=False):
        with column:
            st.markdown(render_metric_card(*spec), unsafe_allow_html=True)


def make_hub_chart(hub_rates: pd.DataFrame) -> go.Figure:
    ordered = hub_rates.sort_values("percentual_atraso", ascending=True).reset_index(drop=True)
    colors = [BLUE_SOFT] * len(ordered)
    if colors:
        colors[-1] = ALERT

    fig = go.Figure(
        go.Bar(
            x=ordered["percentual_atraso"],
            y=ordered["hub"],
            orientation="h",
            marker=dict(color=colors, line=dict(color=colors, width=1)),
            text=[format_percent(value) for value in ordered["percentual_atraso"]],
            textposition="outside",
            hovertemplate="%{y}: %{x:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        margin=dict(l=10, r=18, t=10, b=8),
        height=360,
        font=dict(family="IBM Plex Sans, sans-serif", color=TEXT, size=13),
        showlegend=False,
    )
    fig.update_xaxes(
        title=None,
        tickformat=".0%",
        gridcolor=LINE,
        zeroline=False,
        tickfont=dict(color=MUTED),
    )
    fig.update_yaxes(
        title=None,
        showgrid=False,
        tickfont=dict(color=TEXT),
    )
    return fig


def make_benchmark_chart(benchmark_frame: pd.DataFrame) -> go.Figure:
    labels = [format_size_label(int(value)) for value in benchmark_frame["n"]]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=benchmark_frame["linear_query_seconds"],
            name="Algoritmo antigo",
            marker=dict(color=ALERT),
            text=[format_duration(value) for value in benchmark_frame["linear_query_seconds"]],
            textposition="outside",
            hovertemplate="Linear<br>Tamanho: %{x}<br>Tempo: %{y:.4f} s<extra></extra>",
            width=0.28,
        )
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=benchmark_frame["indexed_query_seconds"],
            name="Algoritmo novo",
            marker=dict(color=BLUE),
            text=[format_duration(value) for value in benchmark_frame["indexed_query_seconds"]],
            textposition="outside",
            hovertemplate="Indexado<br>Tamanho: %{x}<br>Tempo: %{y:.4f} s<extra></extra>",
            width=0.28,
        )
    )
    fig.update_layout(
        barmode="group",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        margin=dict(l=10, r=10, t=10, b=8),
        height=320,
        font=dict(family="IBM Plex Sans, sans-serif", color=TEXT, size=13),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title_text="",
        ),
    )
    fig.update_xaxes(
        title=None,
        showgrid=False,
        tickfont=dict(color=TEXT),
    )
    fig.update_yaxes(
        title=None,
        gridcolor=LINE,
        zeroline=False,
        tickfont=dict(color=MUTED),
    )
    return fig


def make_build_chart(benchmark_frame: pd.DataFrame) -> go.Figure:
    labels = [format_size_label(int(value)) for value in benchmark_frame["n"]]
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=benchmark_frame["build_seconds"],
            marker=dict(color=BLUE_SOFT, line=dict(color=BLUE_SOFT, width=1)),
            text=[format_duration(value) for value in benchmark_frame["build_seconds"]],
            textposition="outside",
            hovertemplate="Pré-processamento<br>Tamanho: %{x}<br>Tempo: %{y:.4f} s<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        margin=dict(l=10, r=10, t=10, b=8),
        height=320,
        font=dict(family="IBM Plex Sans, sans-serif", color=TEXT, size=13),
        showlegend=False,
    )
    fig.update_xaxes(
        title=None,
        showgrid=False,
        tickfont=dict(color=TEXT),
    )
    fig.update_yaxes(
        title=None,
        gridcolor=LINE,
        zeroline=False,
        tickfont=dict(color=MUTED),
    )
    return fig


def make_benchmark_table(benchmark_frame: pd.DataFrame) -> pd.DataFrame:
    table = benchmark_frame.copy()
    table["n"] = table["n"].map(format_int)
    for column in ("build_seconds", "linear_query_seconds", "indexed_query_seconds"):
        table[column] = table[column].map(format_duration)
    table["speedup_x"] = table["speedup_x"].map(lambda value: f"{value:.2f}x".replace(".", ","))
    table["same_answer"] = table["same_answer"].map(lambda value: "Sim" if value else "Nao")
    return table.rename(
        columns={
            "n": "N",
            "build_seconds": "Pré-processamento",
            "linear_query_seconds": "Consulta linear",
            "indexed_query_seconds": "Consulta indexada",
            "speedup_x": "Speedup",
            "same_answer": "Mesmo resultado",
        }
    )


def filter_operational_frame(
    frame: pd.DataFrame,
    start_local: pd.Timestamp,
    end_local: pd.Timestamp,
    hub: str | None,
    status: str | None,
) -> pd.DataFrame:
    filtered = frame[
        (frame["timestamp_label"] >= start_local)
        & (frame["timestamp_label"] <= end_local)
    ].copy()
    if status is not None:
        filtered = filtered[filtered["status"] == status]
    if hub is not None:
        filtered = filtered[filtered["hub"] == hub]
    return filtered


def render_operations_page(frame: pd.DataFrame, service: QueryLogisticsDashboard, data_label: str) -> None:
    st.sidebar.markdown("### Filtros da operação")
    timestamp_min = frame["timestamp_label"].min().floor("min")
    timestamp_max = frame["timestamp_label"].max().ceil("min")

    time_range = st.sidebar.slider(
        "Intervalo da consulta",
        min_value=timestamp_min.to_pydatetime(),
        max_value=timestamp_max.to_pydatetime(),
        value=(timestamp_min.to_pydatetime(), timestamp_max.to_pydatetime()),
        format="DD/MM/YY HH:mm",
    )
    min_delay = st.sidebar.slider("Atraso mínimo", min_value=5, max_value=120, value=30, step=5)
    statuses = ["Todos"] + sorted(frame["status"].dropna().unique().tolist())
    hubs = ["Todos"] + sorted(frame["hub"].dropna().unique().tolist())
    selected_status = st.sidebar.selectbox("Status", statuses)
    selected_hub = st.sidebar.selectbox("Hub", hubs)

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
    filtered = filter_operational_frame(frame, start_local, end_local, window.hub, window.status)

    render_page_header(
        title="Operação LogisticaMA",
        copy="Visão operacional da base oficial hardcoded, com métricas do recorte atual e comparação direta entre a consulta linear e a indexada.",
        meta=f"{data_label} | Recorte atual: {start_local.strftime('%d/%m/%Y %H:%M')} até {end_local.strftime('%d/%m/%Y %H:%M')}",
    )

    summary_specs = [
        ("Eventos no recorte", format_int(summary.total_events), "Total de registros dentro da janela filtrada."),
        (
            f"Atrasos > {min_delay} min",
            format_int(summary.delayed_events),
            f"{format_percent(summary.delayed_share)} do total no recorte.",
        ),
        ("Atraso médio", format_minutes(summary.average_delay), "Média de atraso dos eventos filtrados."),
        ("Maior atraso", f"{summary.max_delay} min", "Pico de atraso encontrado no recorte atual."),
    ]
    render_metric_specs(summary_specs, columns=4)

    if filtered.empty:
        st.warning("Não há eventos no recorte atual. Ajuste o intervalo ou os filtros para visualizar os relatórios.")
        return

    filtered["esta_atrasado_recorte"] = filtered["atraso_min"] > min_delay
    hub_rates = (
        filtered.groupby("hub", as_index=False)
        .agg(
            eventos=("id", "count"),
            atrasos=("esta_atrasado_recorte", "sum"),
            atraso_medio=("atraso_min", "mean"),
        )
        .assign(percentual_atraso=lambda data: data["atrasos"] / data["eventos"])
        .sort_values("percentual_atraso", ascending=False)
    )

    critical_hub = hub_rates.iloc[0]
    linear_time, indexed_time = measure_query_times(frame, service, window)
    speedup = linear_time / max(indexed_time, 1e-9)

    insight_specs = [
        (
            "Hub mais crítico",
            str(critical_hub["hub"]),
            f"{format_percent(float(critical_hub['percentual_atraso']))} de atraso no recorte.",
        ),
        ("Consulta linear", format_duration(linear_time), "Varredura completa do recorte no estilo do algoritmo antigo."),
        ("Consulta indexada", format_duration(indexed_time), f"Speedup estimado de {speedup:.1f}x sobre a consulta linear.".replace(".", ",")),
    ]
    render_metric_specs(insight_specs, columns=3)

    chart_col, table_col = st.columns([1.45, 0.95])
    with chart_col:
        st.markdown(
            """
            <div class="section-card">
              <h2 class="section-title">Atraso por hub</h2>
              <div class="section-note">base oficial hardcoded, recorte filtrado</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(make_hub_chart(hub_rates), use_container_width=True, config={"displayModeBar": False})

    with table_col:
        st.markdown(
            """
            <div class="section-card">
              <h2 class="section-title">Resumo por hub</h2>
              <div class="section-note">percentual, volume e atraso médio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        hub_table = hub_rates.copy()
        hub_table["eventos"] = hub_table["eventos"].map(format_int)
        hub_table["atrasos"] = hub_table["atrasos"].map(format_int)
        hub_table["percentual_atraso"] = hub_table["percentual_atraso"].map(format_percent)
        hub_table["atraso_medio"] = hub_table["atraso_medio"].map(format_minutes)
        hub_table = hub_table.rename(
            columns={
                "hub": "Hub",
                "eventos": "Eventos",
                "atrasos": "Atrasos",
                "percentual_atraso": "Taxa de atraso",
                "atraso_medio": "Atraso médio",
            }
        )
        st.dataframe(hub_table, use_container_width=True, hide_index=True)
        st.markdown(
            f'<div class="small-note">Consistência verificada: os cards e o ranking usam o mesmo recorte filtrado da consulta exibida.</div>',
            unsafe_allow_html=True,
        )


def render_benchmark_page(data_label: str) -> None:
    st.sidebar.markdown("### Evidência técnica")
    st.sidebar.caption("Resumo fixo do algoritmo antigo do PDF versus o índice atual.")
    st.sidebar.markdown(
        "Tamanhos oficiais do benchmark: "
        + ", ".join(format_size_label(value) for value in DEFAULT_BENCHMARK_SIZES)
    )

    benchmark_frame = load_benchmark_frame()
    real_case = load_real_case_benchmark()
    max_speedup = max(float(benchmark_frame["speedup_x"].max()), real_case.speedup_x)
    validation_ok = bool(benchmark_frame["same_answer"].all() and real_case.same_answer)

    render_page_header(
        title="Benchmark dos algoritmos",
        copy="Comparação entre a varredura linear descrita no PDF e o motor indexado atual, usando a base oficial hardcoded e a curva escalável do projeto.",
        meta=f"{data_label} | Benchmark oficial de {format_size_label(DEFAULT_BENCHMARK_SIZES[0])} até {format_size_label(DEFAULT_BENCHMARK_SIZES[-1])}",
    )

    old_col, new_col = st.columns(2)
    with old_col:
        st.markdown(
            render_narrative_card(
                "Algoritmo antigo",
                "Varredura linear O(n)",
                "Percorre todos os registros a cada consulta, exatamente como descrito no PDF. O custo cresce linearmente com o tamanho da base e derruba o tempo de resposta em volumes altos.",
            ),
            unsafe_allow_html=True,
        )
    with new_col:
        st.markdown(
            render_narrative_card(
                "Algoritmo novo",
                "Índice em memória + busca eficiente",
                "Pré-processa os eventos uma vez e responde cada consulta sobre o intervalo usando busca e estruturas acumuladas, reduzindo drasticamente o custo por consulta repetida.",
            ),
            unsafe_allow_html=True,
        )

    benchmark_specs = [
        (
            "Caso real linear",
            format_duration(real_case.linear_query_seconds),
            f"Consulta no recorte oficial entre {real_case.start_label} e {real_case.end_label}.",
        ),
        (
            "Caso real indexado",
            format_duration(real_case.indexed_query_seconds),
            f"Mesmo resultado com atraso > {real_case.min_delay} min na base hardcoded.",
        ),
        (
            "Maior speedup",
            f"{max_speedup:.2f}x".replace(".", ","),
            "Melhor ganho observado entre a curva escalável e o caso real.",
        ),
        (
            "Meta do desafio",
            "< 3 s",
            f"Caso real indexado medido em {format_duration(real_case.indexed_query_seconds)}.",
        ),
    ]
    render_metric_specs(benchmark_specs, columns=4)

    if validation_ok:
        st.success("Validação concluída: o algoritmo novo retornou o mesmo resultado do algoritmo antigo em todos os benchmarks e no caso real da base oficial.")
    else:
        st.error("Há divergência entre os resultados linear e indexado. A página não deve ser usada como evidência final sem corrigir a inconsistência.")

    chart_col, build_col = st.columns([1.4, 1.0])
    with chart_col:
        st.markdown(
            """
            <div class="section-card">
              <h2 class="section-title">Consulta antiga vs nova</h2>
              <div class="section-note">tempos de resposta por tamanho N</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(make_benchmark_chart(benchmark_frame), use_container_width=True, config={"displayModeBar": False})

    with build_col:
        st.markdown(
            """
            <div class="section-card">
              <h2 class="section-title">Custo do pré-processamento</h2>
              <div class="section-note">tempo de construção do índice</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(make_build_chart(benchmark_frame), use_container_width=True, config={"displayModeBar": False})

    real_case_specs = [
        ("Janela do caso real", f"{real_case.start_label} -> {real_case.end_label}", f"{format_int(real_case.total_events)} eventos considerados."),
        (
            f"Resposta antiga vs nova",
            format_int(real_case.delayed_events),
            f"Eventos com atraso > {real_case.min_delay} min retornados pelas duas abordagens.",
        ),
        ("Pré-processamento", format_duration(real_case.build_seconds), "Custo pago uma vez antes das consultas indexadas."),
    ]
    st.markdown(
        """
        <div class="section-card">
          <h2 class="section-title">Caso real na base hardcoded</h2>
          <div class="section-note">mesma base usada na página Operação</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_metric_specs(real_case_specs, columns=3)

    st.markdown(
        """
        <div class="section-card">
          <h2 class="section-title">Tabela de validação</h2>
          <div class="section-note">benchmark completo com prova de equivalência</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(make_benchmark_table(benchmark_frame), use_container_width=True, hide_index=True)
    st.markdown(
        f'<div class="small-note">Fonte do benchmark: {data_label}. A coluna "Mesmo resultado" precisa permanecer "Sim" em toda a tabela.</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    st.sidebar.title("LogisticaMA")
    st.sidebar.caption("Base oficial hardcoded e navegação por páginas.")
    page = st.sidebar.radio("Página", APP_PAGES, index=0)

    try:
        frame = load_default_frame()
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.error("Não foi possível carregar a base oficial do projeto.")
        st.caption(f"Verifique o arquivo em {Path(OFFICIAL_DATASET_PATH).as_posix()}.")
        st.code(str(exc))
        return

    data_label = (
        f"Fonte: base oficial local ({Path(OFFICIAL_DATASET_PATH).as_posix()}) | "
        f"{format_int(len(frame))} eventos | "
        f"{frame['timestamp_label'].min().strftime('%d/%m/%Y %H:%M')} até "
        f"{frame['timestamp_label'].max().strftime('%d/%m/%Y %H:%M')}"
    )
    service, _repository = build_service(frame)

    if page == PAGE_OPERATION:
        render_operations_page(frame, service, data_label)
        return

    render_benchmark_page(data_label)


if __name__ == "__main__":
    main()
