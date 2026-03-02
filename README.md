# LogisticaMA Analytics

Desafio 4.0 - Projeto e Análise de Algoritmos · UNDB

## Colaboradores

- Carlos Arthur Rodrigues
- Davilson Carvalho
- Everson Gastão
- Henrique Martins
- José Fernando de Sá
- Pedro Reche

## Descrição

Este projeto propõe uma solução computacional para o problema de consulta eficiente sobre logs de rastreamento logístico. O objetivo é responder perguntas do tipo *"quantos pacotes atrasaram mais de 30 minutos entre 14h e 18h?"* em menos de 3 segundos, mesmo com volumes de até 2 milhões de eventos.

O sistema inclui um motor de consulta indexado, benchmarks comparativos e um dashboard interativo desenvolvido em Streamlit.

## Contexto do Problema

A abordagem original percorre todos os registros a cada consulta, resultando em custo linear **O(n)**. Em ambiente de testes, o comportamento é o seguinte:

| Volume         | Tempo de resposta |
|----------------|-------------------|
| 10.000 eventos | ~0,8 segundos     |
| 100.000 eventos| ~18 segundos      |
| 1,2M de eventos| > 4 minutos       |

Esse comportamento torna o sistema inviável para tomada de decisão em tempo real.

```python
# implementação linear de referência
def contar_atrasos_linear(logs, inicio, fim):
    total = 0
    for evento in logs:
        if inicio <= evento['timestamp'] <= fim:
            if evento['atraso_min'] > 30:
                total += 1
    return total
```

## Algoritmo Adotado

A solução substitui a varredura linear por uma estrutura indexada composta de três etapas:

### Pré-processamento (executado uma única vez)

1. Ordenação dos eventos por `timestamp` - custo **Θ(n log n)**
2. Construção de vetores de prefix sums por hub e status sobre `atraso_min` - custo **Θ(n)**

### Consulta (executada repetidamente)

1. Busca binária (`bisect`) para localizar os limites do intervalo de tempo - custo **Θ(log n)**
2. Resposta via diferença de prefix sums - custo **Θ(1)**

### Análise de Complexidade

| Etapa              | Custo        |
|--------------------|--------------|
| Pré-processamento  | Θ(n log n)   |
| Consulta           | Θ(log n)     |
| Memória adicional  | Θ(n)         |

O custo de pré-processamento é amortizado ao longo das consultas. Cada consulta subsequente opera em **Θ(log n)**, o que representa uma redução substancial frente ao **Θ(n)** da abordagem linear, especialmente em bases com alto volume de dados.

## Estrutura do Projeto

```
src/logisticama/
  domain/        entidades e contratos de domínio
  application/   casos de uso
  adapters/      ingestão de dados, índice, dashboard
  shared/        utilitários comuns
app/
  streamlit_app.py      interface principal
benchmarks/
  run_benchmarks.py     comparação linear x indexado
tests/
  test_indexed_repository.py
```

Implementação central: [src/logisticama/adapters/persistence/indexed_repository.py](src/logisticama/adapters/persistence/indexed_repository.py)

## Instalação e Execução

```bash
# instalar dependências
uv sync

# executar testes
uv run pytest

# iniciar dashboard
uv run streamlit run app/streamlit_app.py

# executar benchmarks
uv run python benchmarks/run_benchmarks.py --sizes 1000 10000 100000 1000000
```

## Formato do Dataset

```csv
id,timestamp,status,hub,atraso_min
LM20260207-00123,2026-02-07T09:15:42-03:00,triagem,Ponta_Areia,0
```

Colunas obrigatórias: `id`, `timestamp`, `status`, `hub`, `atraso_min`.

Dataset fornecido pela disciplina: [Google Drive](https://drive.google.com/drive/folders/19-pRmLe-V4rKv2VeuvytIGja6qm5zybJ)

## Tecnologias

Python 3.12, uv, Streamlit, pandas, numpy, plotly, pytest
