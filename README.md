# LogisticaMA Analytics

Desafio 4.0 - Projeto e Análise de Algoritmos · UNDB

## Colaboradores

- Carlos Arthur Rodrigues
- Davilson Carvalho
- Everson Gastão
- Henrique Martins
- José Fernando de Sá
- Pedro Reche

## Visão rápida

Este projeto foi criado para ajudar a empresa fictícia **LogísticaMA** a entender, com clareza, onde a operação está falhando.

Na prática, o sistema responde perguntas como:

- quantos pacotes atrasaram em um período
- quais hubs estão com pior desempenho
- em que horário os atrasos aumentaram

Tudo isso aparece em um **dashboard visual em Streamlit**, pensado para apresentação acadêmica e para pessoas que não são técnicas.

## Por que este projeto existe

O problema do desafio é simples de entender:

- a empresa tem muitos logs
- as consultas estavam sendo feitas de forma lenta
- quando o volume cresce, o sistema trava

A solução deste repositório é trocar a busca linear por uma estratégia com **índices em memória**, o que reduz muito o tempo de resposta.

## O que você encontra aqui

- um dashboard pronto para demonstrar a solução
- um motor de consultas otimizado
- benchmark comparando abordagem lenta e abordagem indexada
- testes automatizados
- documentação organizada para facilitar entendimento

## Como usar sem ser técnico

### 1. Abrir o painel

Depois de instalar o projeto, rode:

```bash
uv run streamlit run app/streamlit_app.py
```

O painel abrirá no navegador.

### 2. O que dá para fazer no painel

- usar a base de demonstração que já acompanha o projeto
- enviar um arquivo real em `CSV` ou `JSON`
- escolher período de análise
- filtrar por hub e status
- ajustar o limite de atraso em minutos

### 3. Como interpretar o dashboard

**Eventos na janela**  
Mostra quantos registros existem no período escolhido.

**Atrasos acima do corte**  
Mostra quantos eventos ultrapassaram o limite definido.

**Atraso médio**  
Resume o tamanho médio dos atrasos naquele recorte.

**Pior atraso**  
Aponta o caso mais crítico encontrado.

**Panorama**  
Ajuda a entender rapidamente se a operação está estável ou sob pressão.

**Hubs críticos**  
Mostra onde a operação está mais sensível.

**Linha do tempo**  
Permite enxergar quando os problemas aumentam.

**Base carregada**  
Mostra os registros usados e permite baixar o recorte filtrado.

## Ideia central do algoritmo

A abordagem lenta faz o seguinte:

1. lê todos os eventos
2. percorre tudo a cada consulta
3. conta manualmente os atrasos

Isso tende a custo **Θ(n)** por consulta.

Neste projeto, a abordagem escolhida:

1. ordena os eventos por tempo
2. cria índices por tempo, hub e status
3. usa busca binária para localizar a janela da consulta
4. usa prefix sums para responder mais rápido

Resultado:

- preparação inicial com custo maior
- consultas repetidas muito mais rápidas
- melhor escalabilidade para grandes volumes

## Estrutura do projeto

O código mistura conceitos de **arquitetura limpa** e **arquitetura hexagonal** para ficar mais fácil de manter:

```text
src/logisticama/
  domain/        regras centrais e contratos
  application/   casos de uso
  adapters/      ingestão, índices e interface
  shared/        utilitários comuns
app/
  streamlit_app.py
benchmarks/
  run_benchmarks.py
tests/
  test_indexed_repository.py
```

## Tecnologias usadas

- Python 3.12
- uv
- Streamlit
- pandas
- numpy
- plotly
- pytest

## Setup técnico

### Instalar dependências

```bash
uv sync
```

### Rodar testes

```bash
uv run pytest
```

### Rodar benchmark

```bash
uv run python benchmarks/run_benchmarks.py --sizes 1000 10000 100000
```

### Rodar o dashboard

```bash
uv run streamlit run app/streamlit_app.py
```

### Gerar requirements para deploy

```bash
uv export --no-dev --no-hashes --format requirements-txt > requirements.txt
```

## Formato esperado do dataset

O projeto espera estas colunas:

- `id`
- `timestamp`
- `status`
- `hub`
- `atraso_min`

Exemplo:

```csv
id,timestamp,status,hub,atraso_min
LM20260207-00123,2026-02-07T09:15:42-03:00,triagem,Ponta_Areia,0
```

## Arquivos mais importantes

- `app/streamlit_app.py`: dashboard principal
- `src/logisticama/adapters/persistence/indexed_repository.py`: motor indexado
- `benchmarks/run_benchmarks.py`: comparação de desempenho
- `data/demo/logistica_ma_demo.csv`: base de demonstração

## Próximos passos naturais

- carregar o dataset real da disciplina
- executar benchmarks com volumes maiores
- registrar prints do dashboard
- transformar os resultados em PDF para entrega final
