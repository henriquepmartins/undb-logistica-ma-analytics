from __future__ import annotations

import json
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
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
from logisticama.shared.time_utils import ensure_fortaleza_timestamp


BLUE = "#264653"
BLUE_SOFT = "#9FB5C3"
ALERT = "#C96A4A"
TEXT = "#1B242C"
MUTED = "#66727E"
LINE = "#D7DFE5"
PANEL = "#FFFFFF"
PAGE_OPERATION = "Operação"
PAGE_BENCHMARK = "Benchmark"
BENCHMARK_CASES_SNAPSHOT_PATH = Path("data/benchmark_cases_snapshot.csv")
BENCHMARK_REAL_CASE_SNAPSHOT_PATH = Path("data/benchmark_real_case_snapshot.json")
BENCHMARK_TIME_COLUMNS = ("build_seconds", "linear_query_seconds", "indexed_query_seconds")


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
    if BENCHMARK_CASES_SNAPSHOT_PATH.exists():
        try:
            frame = pd.read_csv(BENCHMARK_CASES_SNAPSHOT_PATH)
            expected_columns = {
                "n",
                "build_seconds",
                "linear_query_seconds",
                "indexed_query_seconds",
                "linear_runs",
                "indexed_runs",
                "speedup_x",
                "same_answer",
            }
            if expected_columns.issubset(frame.columns):
                frame["same_answer"] = frame["same_answer"].map(lambda value: str(value).lower() == "true")
                if not benchmark_snapshot_is_legacy(frame):
                    return frame
        except (OSError, ValueError, pd.errors.ParserError):
            pass
    return benchmark_cases(sizes)


@st.cache_data(show_spinner=False)
def load_real_case_benchmark():
    if BENCHMARK_REAL_CASE_SNAPSHOT_PATH.exists():
        try:
            payload = json.loads(BENCHMARK_REAL_CASE_SNAPSHOT_PATH.read_text(encoding="utf-8"))
            if not real_case_snapshot_is_legacy(payload):
                return RealCaseBenchmark(**payload)
        except (OSError, ValueError, TypeError):
            pass
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


def seconds_to_milliseconds_decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value)) * Decimal("1000")


def milliseconds_float(value: float | int | str) -> float:
    return float(seconds_to_milliseconds_decimal(value))


def benchmark_snapshot_is_legacy(frame: pd.DataFrame) -> bool:
    indexed = pd.to_numeric(frame["indexed_query_seconds"], errors="coerce")
    if indexed.isna().any() or indexed.empty:
        return True
    return bool(indexed.nunique(dropna=False) == 1 and indexed.eq(0.000001).all())


def real_case_snapshot_is_legacy(payload: dict[str, object]) -> bool:
    indexed_value = payload.get("indexed_query_seconds")
    try:
        return float(indexed_value) == 0.000001
    except (TypeError, ValueError):
        return True


def format_benchmark_duration_ms(value: float | int | str) -> str:
    milliseconds = seconds_to_milliseconds_decimal(value)
    if abs(milliseconds) < Decimal("1"):
        milliseconds = milliseconds.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        return f"~{milliseconds:f} ms".replace(".", ",")
    if abs(milliseconds) >= Decimal("1"):
        milliseconds = milliseconds.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    return f"{milliseconds:f} ms".replace(".", ",")


def format_minutes(value: float) -> str:
    return f"{value:.2f} min".replace(".", ",")


def render_app_header() -> None:
    st.markdown(
                """
        <div class="app-shell">
          <div class="top-note">Desafio 4.0 | Dashboard do caso LogisticaMA</div>
          <h1 class="page-title">LogisticaMA</h1>
          <p class="page-copy">
            Acompanhe a operação da base oficial e compare o algoritmo antigo com o novo motor indexado
            sem alternar de página. A análise operacional fica em uma tab; a evidência técnica do benchmark, na outra.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tab_intro(label: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
          <div class="top-note">{label}</div>
          <h2 class="section-title">{title}</h2>
          <p class="page-copy">{body}</p>
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


def render_metric_specs(specs: list[tuple[str, str, str]], columns: int | None = None) -> None:
    if not specs:
        return
    column_count = columns or len(specs)
    cols = st.columns(column_count)
    for column, spec in zip(cols, specs, strict=False):
        with column:
            st.markdown(render_metric_card(*spec), unsafe_allow_html=True)


def make_hub_chart(hub_rates: pd.DataFrame) -> go.Figure:
    ordered = hub_rates.sort_values("percentual_atraso", ascending=True).reset_index(drop=True)
    colors = [BLUE_SOFT] * len(ordered)
    if colors:
        colors[-1] = ALERT
    max_rate = float(ordered["percentual_atraso"].max()) if not ordered.empty else 0.0

    fig = go.Figure(
        go.Bar(
            x=ordered["percentual_atraso"],
            y=ordered["hub"],
            orientation="h",
            marker=dict(color=colors, line=dict(color=colors, width=1)),
            text=[format_percent(value) for value in ordered["percentual_atraso"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        margin=dict(l=10, r=64, t=10, b=8),
        height=360,
        font=dict(family="IBM Plex Sans, sans-serif", color=TEXT, size=13),
        showlegend=False,
    )
    fig.update_xaxes(
        title=None,
        range=[0, max_rate * 1.12 if max_rate else 1],
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
    linear_ms = [milliseconds_float(value) for value in benchmark_frame["linear_query_seconds"]]
    indexed_ms = [milliseconds_float(value) for value in benchmark_frame["indexed_query_seconds"]]
    linear_labels = [format_benchmark_duration_ms(value) for value in benchmark_frame["linear_query_seconds"]]
    indexed_labels = [format_benchmark_duration_ms(value) for value in benchmark_frame["indexed_query_seconds"]]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=linear_ms,
            name="Algoritmo antigo",
            marker=dict(color=ALERT),
            text=linear_labels,
            customdata=linear_labels,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="Algoritmo antigo<br>Tamanho: %{x}<br>Tempo: %{customdata}<extra></extra>",
            width=0.28,
        )
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=indexed_ms,
            name="Algoritmo novo",
            marker=dict(color=BLUE),
            text=indexed_labels,
            customdata=indexed_labels,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="Algoritmo novo<br>Tamanho: %{x}<br>Tempo: %{customdata}<extra></extra>",
            width=0.28,
        )
    )
    fig.update_layout(
        barmode="group",
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        margin=dict(l=10, r=18, t=10, b=8),
        height=380,
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
        title="Tempo (ms)",
        gridcolor=LINE,
        zeroline=False,
        tickfont=dict(color=MUTED),
        automargin=True,
    )
    return fig


def make_build_chart(benchmark_frame: pd.DataFrame) -> go.Figure:
    labels = [format_size_label(int(value)) for value in benchmark_frame["n"]]
    build_ms = [milliseconds_float(value) for value in benchmark_frame["build_seconds"]]
    build_labels = [format_benchmark_duration_ms(value) for value in benchmark_frame["build_seconds"]]
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=build_ms,
            marker=dict(color=BLUE_SOFT, line=dict(color=BLUE_SOFT, width=1)),
            text=build_labels,
            customdata=build_labels,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="Pré-processamento<br>Tamanho: %{x}<br>Tempo: %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        margin=dict(l=10, r=18, t=10, b=8),
        height=280,
        font=dict(family="IBM Plex Sans, sans-serif", color=TEXT, size=13),
        showlegend=False,
    )
    fig.update_xaxes(
        title=None,
        showgrid=False,
        tickfont=dict(color=TEXT),
    )
    fig.update_yaxes(
        title="Tempo (ms)",
        gridcolor=LINE,
        zeroline=False,
        tickfont=dict(color=MUTED),
        automargin=True,
    )
    return fig


def make_benchmark_table(benchmark_frame: pd.DataFrame) -> pd.DataFrame:
    table = benchmark_frame.copy()
    table["n"] = table["n"].map(format_int)
    for column in BENCHMARK_TIME_COLUMNS:
        table[column] = table[column].map(format_benchmark_duration_ms)
    table["speedup_x"] = table["speedup_x"].map(lambda value: f"{value:.2f}x".replace(".", ","))
    table["same_answer"] = table["same_answer"].map(lambda value: "Sim" if value else "Nao")
    table = table.drop(columns=["linear_runs", "indexed_runs"], errors="ignore")
    return table.rename(
        columns={
            "n": "N",
            "build_seconds": "Pré-processamento",
            "linear_query_seconds": "Consulta antiga",
            "indexed_query_seconds": "Consulta nova",
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


def render_operation_filters(frame: pd.DataFrame) -> QueryWindow:
    timestamp_min = frame["timestamp_label"].min().floor("min")
    timestamp_max = frame["timestamp_label"].max().ceil("min")

    st.markdown(
        """
        <div class="section-card">
          <h2 class="section-title">Filtros da operação</h2>
          <div class="section-note">todos os controles ficam na própria tab</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2.2, 1.0, 1.0, 1.0])
    with filter_col1:
        time_range = st.slider(
            "Intervalo da consulta",
            min_value=timestamp_min.to_pydatetime(),
            max_value=timestamp_max.to_pydatetime(),
            value=(timestamp_min.to_pydatetime(), timestamp_max.to_pydatetime()),
            format="DD/MM/YY HH:mm",
        )
    with filter_col2:
        min_delay = st.slider("Atraso mínimo", min_value=5, max_value=120, value=30, step=5)
    with filter_col3:
        statuses = ["Todos"] + sorted(frame["status"].dropna().unique().tolist())
        selected_status = st.selectbox("Status", statuses)
    with filter_col4:
        hubs = ["Todos"] + sorted(frame["hub"].dropna().unique().tolist())
        selected_hub = st.selectbox("Hub", hubs)

    start_local = ensure_fortaleza_timestamp(time_range[0])
    end_local = ensure_fortaleza_timestamp(time_range[1])
    return QueryWindow(
        start_iso=start_local.isoformat(),
        end_iso=end_local.isoformat(),
        min_delay=min_delay,
        hub=None if selected_hub == "Todos" else selected_hub,
        status=None if selected_status == "Todos" else selected_status,
    )


def render_operations_tab(frame: pd.DataFrame, service: QueryLogisticsDashboard) -> None:
    render_tab_intro(
        PAGE_OPERATION,
        "Visão operacional da base oficial",
        "Analise o recorte atual da operação com filtros inline, cards enxutos e ranking de atraso por hub.",
    )

    window = render_operation_filters(frame)
    start_local = ensure_fortaleza_timestamp(window.start_iso)
    end_local = ensure_fortaleza_timestamp(window.end_iso)

    summary = service.build_summary(window)
    filtered = filter_operational_frame(frame, start_local, end_local, window.hub, window.status)

    if filtered.empty:
        st.warning("Não há eventos no recorte atual. Ajuste o intervalo ou os filtros para visualizar os relatórios.")
        return

    filtered["esta_atrasado_recorte"] = filtered["atraso_min"] > window.min_delay
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
    summary_specs = [
        ("Eventos no recorte", format_int(summary.total_events), "Total de registros dentro da janela e dos filtros atuais."),
        (
            f"Atrasos > {window.min_delay} min",
            format_int(summary.delayed_events),
            f"{format_percent(summary.delayed_share)} do recorte atual está acima do limiar configurado.",
        ),
        (
            "Hub mais crítico",
            str(critical_hub["hub"]),
            f"{format_percent(float(critical_hub['percentual_atraso']))} de atraso no hub com pior desempenho.",
        ),
    ]
    render_metric_specs(summary_specs, columns=3)

    st.markdown(
        f"""
        <div class="small-note">
          Recorte ativo: {start_local.strftime('%d/%m/%Y %H:%M')} até {end_local.strftime('%d/%m/%Y %H:%M')}.
          Os cards, o gráfico e a tabela usam exatamente os mesmos filtros.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-card">
          <h2 class="section-title">Atraso por hub</h2>
          <div class="section-note">percentual de eventos acima do limiar no recorte atual</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(make_hub_chart(hub_rates), use_container_width=True, config={"displayModeBar": False})

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
    st.dataframe(
        hub_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Hub": st.column_config.TextColumn("Hub", width="large"),
            "Eventos": st.column_config.TextColumn("Eventos", width="small"),
            "Atrasos": st.column_config.TextColumn("Atrasos", width="small"),
            "Taxa de atraso": st.column_config.TextColumn("Taxa de atraso", width="small"),
            "Atraso médio": st.column_config.TextColumn("Atraso médio", width="small"),
        },
    )


def render_benchmark_methodology(real_case, benchmark_frame: pd.DataFrame) -> None:
    synthetic_linear_runs = int(benchmark_frame["linear_runs"].iloc[0])
    synthetic_indexed_runs = int(benchmark_frame["indexed_runs"].iloc[0])
    st.markdown(
        f"""
        <div class="method-card">
          <h2 class="section-title">Mesmo recorte, mesmo limiar, duas estratégias de consulta</h2>
          <p class="page-copy">
            O algoritmo antigo faz uma varredura linear completa sobre os registros do recorte.
            O algoritmo novo usa <code>IndexedLogRepository.count_delays(...)</code> sobre a mesma janela e o mesmo
            atraso mínimo. O custo de construção do índice é medido separadamente e não entra no tempo da consulta indexada.
          </p>
          <div class="method-grid">
            <div class="method-step">
              <strong>Caso real</strong>
              Média de {real_case.linear_runs} consultas lineares e {real_case.indexed_runs} consultas indexadas
              entre {real_case.start_label} e {real_case.end_label}, com atraso &gt; {real_case.min_delay} min.
            </div>
            <div class="method-step">
              <strong>Curva por tamanhos</strong>
              Cada ponto de 1k a 2M usa base sintética do projeto e média de {synthetic_linear_runs} execuções lineares
              e {synthetic_indexed_runs} execuções indexadas, sempre validando se a resposta final é idêntica.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_algorithm_summary_section() -> None:
    st.markdown(
        """
        <div class="method-card">
          <h2 class="section-title">Resumo do algoritmo</h2>
          <p class="page-copy">
            Em analise de algoritmos, a ideia principal e reduzir a quantidade de trabalho por consulta.
            No metodo antigo, cada pergunta exige olhar registro por registro (ideia de custo O(n)).
            No metodo novo, fazemos uma preparacao única e guardamos totais acumulados no tempo.
            Depois, a resposta vem de uma subtração simples: se até 10h havia 120 atrasos e até 12h havia 185,
            entao nesse intervalo houve 65 atrasos (185 - 120 = 65).
          </p>
          <div class="method-grid">
            <div class="method-step">
              <strong>O que muda no custo</strong>
              Antes, cada consulta repetia uma contagem completa. Agora, pagamos uma organizacao inicial
              (pre-processamento) e reaproveitamos essa estrutura para responder com muito menos operacoes.
            </div>
            <div class="method-step">
              <strong>Como ler isso no app</strong>
              O dashboard mostra separado o tempo de preparo e o tempo da consulta.
              Depois compara o algoritmo novo com o antigo no mesmo recorte e confirma que o resultado final continua igual.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_benchmark_tab() -> None:
    render_tab_intro(
        PAGE_BENCHMARK,
        "Benchmark dos algoritmos",
        "Veja quanto tempo o algoritmo antigo leva, quanto o motor indexado responde no mesmo caso real e como a curva se comporta conforme o volume cresce.",
    )
    render_algorithm_summary_section()

    benchmark_frame = load_benchmark_frame()
    real_case = load_real_case_benchmark()
    max_speedup = max(float(benchmark_frame["speedup_x"].max()), real_case.speedup_x)
    validation_ok = bool(benchmark_frame["same_answer"].all() and real_case.same_answer)

    render_benchmark_methodology(real_case, benchmark_frame)
    st.markdown(
        """
        <div class="benchmark-context">
          <div class="top-note">benchmark normalizado</div>
          <p class="benchmark-context-copy">
            Cards, gráficos, tooltips e tabela usam a mesma unidade e preservam a precisão disponível
            dos benchmarks carregados no app.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    benchmark_specs = [
        (
            "Tempo do algoritmo antigo",
            format_benchmark_duration_ms(real_case.linear_query_seconds),
            f"Média no caso real com {real_case.linear_runs} execuções lineares no mesmo recorte.",
        ),
        (
            "Tempo do algoritmo novo",
            format_benchmark_duration_ms(real_case.indexed_query_seconds),
            f"Média no mesmo caso real com {real_case.indexed_runs} execuções indexadas.",
        ),
        (
            "Speedup",
            f"{real_case.speedup_x:.2f}x".replace(".", ","),
            f"Ganho no caso real; melhor speedup observado na curva completa: {max_speedup:.2f}x.".replace(".", ","),
        ),
    ]
    render_metric_specs(benchmark_specs, columns=3)

    if validation_ok:
        st.success("Validação concluída: o algoritmo novo retornou o mesmo resultado do algoritmo antigo no caso real e em todos os tamanhos do benchmark.")
    else:
        st.error("Há divergência entre os resultados linear e indexado. A evidência técnica precisa ser corrigida antes de ser usada.")

    st.markdown(
        """
        <div class="benchmark-panel benchmark-panel--primary">
          <h2 class="section-title">Consulta antiga vs nova por tamanho</h2>
          <div class="section-note">Curva complementar de 1k a 2M eventos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(make_benchmark_chart(benchmark_frame), use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        """
        <div class="benchmark-panel benchmark-panel--secondary">
          <div class="benchmark-chip">custo pago uma vez</div>
          <h2 class="section-title">Custo do pré-processamento</h2>
          <div class="section-note">Tempo para construir o índice antes das consultas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(make_build_chart(benchmark_frame), use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        """
        <div class="section-card">
          <h2 class="section-title">Detalhes do caso real</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    real_case_specs = [
        (
            "Janela medida",
            f"{real_case.start_label} -> {real_case.end_label}",
            f"{format_int(real_case.total_events)} eventos avaliados no caso real.",
        ),
        (
            "Resposta antiga vs nova",
            format_int(real_case.delayed_events),
            f"Eventos com atraso > {real_case.min_delay} min retornados pelas duas abordagens.",
        ),
        (
            "Pré-processamento",
            format_benchmark_duration_ms(real_case.build_seconds),
            "Tempo para construir o índice, separado da consulta indexada.",
        ),
    ]
    render_metric_specs(real_case_specs, columns=3)

    st.markdown(
        """
        <div class="section-card">
          <h2 class="section-title">Tabela de validação</h2>
          <div class="section-note">Benchmark completo com prova de equivalência</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(make_benchmark_table(benchmark_frame), use_container_width=True, hide_index=True)


def main() -> None:
    try:
        frame = load_default_frame()
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.error("Não foi possível carregar a base oficial do projeto.")
        st.caption(f"Verifique o arquivo em {Path(OFFICIAL_DATASET_PATH).as_posix()}.")
        st.code(str(exc))
        return

    service, _repository = build_service(frame)

    render_app_header()
    operation_tab, benchmark_tab = st.tabs([PAGE_OPERATION, PAGE_BENCHMARK])

    with operation_tab:
        render_operations_tab(frame, service)

    with benchmark_tab:
        render_benchmark_tab()


if __name__ == "__main__":
    main()
