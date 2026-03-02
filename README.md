# LogisticaMA Analytics

Desafio 4.0 — Projeto e Análise de Algoritmos · UNDB

## Colaboradores

- Carlos Arthur Rodrigues
- Davilson Carvalho
- Everson Gastão
- Henrique Martins
- José Fernando de Sá
- Pedro Reche

---

## Problema

A LogísticaMA precisa responder consultas como _"quantos pacotes atrasaram mais de 30 minutos entre 14h e 18h?"_ sobre até **2 milhões de eventos** em menos de **3 segundos**.

A abordagem atual usa varredura linear: para cada consulta, percorre todos os registros um a um — custo **Θ(n)** por consulta.

```python
# abordagem lenta — O(n) por consulta
def contar_atrasos_linear(logs, inicio, fim):
    return sum(1 for e in logs if inicio <= e['timestamp'] <= fim and e['atraso_min'] > 30)
```

Com 100 mil registros isso já leva ~18s. Com 1,2 milhão, passa de 4 minutos.

---

## Algoritmo escolhido — Índice ordenado + Busca binária + Prefix sums

### Pré-processamento (feito uma vez)

1. Ordenar os eventos por `timestamp` → **Θ(n log n)**
2. Para cada fatia relevante (hub, status), construir um vetor de prefix sums sobre `atraso_min` → **Θ(n)**

### Consulta (executada repetidamente)

1. Usar busca binária (`bisect`) para localizar os limites do intervalo de tempo → **Θ(log n)**
2. Responder com diferença de prefix sums → **Θ(1)**

### Complexidade

| Etapa              | Custo        |
|--------------------|--------------|
| Pré-processamento  | Θ(n log n)   |
| Consulta           | Θ(log n)     |
| Memória extra      | Θ(n)         |

A ordenação domina o setup. Depois disso, **cada consulta custa Θ(log n)** — ganho expressivo frente ao Θ(n) linear, especialmente com volume alto e consultas repetidas.

---

## Estrutura

```
src/logisticama/
  domain/        entidades e contratos
  application/   casos de uso
  adapters/      ingestão, índice, dashboard
  shared/        utilitários
app/
  streamlit_app.py      dashboard
benchmarks/
  run_benchmarks.py     comparação linear × indexado
tests/
  test_indexed_repository.py
```

**Arquivo central:** [src/logisticama/adapters/persistence/indexed_repository.py](src/logisticama/adapters/persistence/indexed_repository.py)

---

## Setup

```bash
uv sync                  # instalar dependências
uv run pytest            # testes
uv run streamlit run app/streamlit_app.py   # dashboard
uv run python benchmarks/run_benchmarks.py --sizes 1000 10000 100000 1000000
```

---

## Formato do dataset

```csv
id,timestamp,status,hub,atraso_min
LM20260207-00123,2026-02-07T09:15:42-03:00,triagem,Ponta_Areia,0
```

Colunas obrigatórias: `id`, `timestamp`, `status`, `hub`, `atraso_min`.

