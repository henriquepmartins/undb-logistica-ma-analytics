# Design do Projeto LogisticaMA

## Resumo

Projeto em Python com `uv`, dashboard em Streamlit e motor de consultas indexado para responder perguntas logisticas em menos tempo do que uma varredura linear. A arquitetura mistura conceitos de arquitetura limpa e hexagonal:

- `domain`: regras e contratos essenciais
- `application`: casos de uso
- `adapters`: entrada, persistencia e apresentacao
- `shared`: utilitarios comuns

## Decisoes principais

1. Linguagem unica: Python.
2. Interface: Streamlit com visual editorial voltado para apresentacao academica.
3. Estrategia de consulta: indices em memoria com arrays ordenados por tempo, prefix sums e segmentacao por `hub`, `status` e `hub + status`.
4. Dependencias: gerenciadas por `uv`, com export adicional de `requirements.txt` para deploy no Streamlit Cloud.

## Estruturas de dados

- DataFrame normalizado na ingestao.
- Vetores ordenados por `timestamp_epoch`.
- Prefix sums para contagem de atrasos e soma de minutos.
- Dicionarios de slices indexados por hub e status.

## Entregaveis previstos

- Dashboard Streamlit
- Motor de consultas e benchmarks
- README amigavel para publico nao tecnico
- Relatorio tecnico e base para apresentacao
