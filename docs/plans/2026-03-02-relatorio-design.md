# Design: Relatório técnico e pendências do desafio

## Objetivo

Produzir um relatório técnico em LaTeX (formato article) em português, com entrega do PDF em `docs/`, cobrindo solução, complexidade, experimentos e conformidade do desafio (<3s para 2M eventos). Completar pendências de testes (filtro de status, min_delay variável) e adicionar checagem de SLA no benchmark CLI.

## Escopo

- Relatório técnico completo (capa, resumo, seções: problema, abordagem, complexidade temporal/espacial, metodologia de testes/benchmarks, resultados, conclusão).
- Geração de PDF no repositório.
- Testes adicionais de repositório: filtro só por status; contagem com `min_delay` diferente de 30.
- Checagem de SLA (<3s) no benchmark para 2M eventos.

## Fora de escopo

- Template ABNT/abnTeX2 (usaremos article simples).
- Slides ou material de apresentação.

## Abordagem

- Usar `article` com packages básicos (`babel`, `geometry`, `hyperref`, `amsmath`, `graphicx`, `booktabs`, `array`, `float`).
- Estrutura proposta: Capa; Resumo; 1) Introdução/Problema; 2) Dataset e Normalização; 3) Algoritmo e Índice; 4) Complexidade (tempo e espaço); 5) Metodologia experimental (benchmarks e testes); 6) Resultados e SLA; 7) Conclusões; 8) Trabalho futuro.
- Incluir tabela com resultados de benchmark mais recentes (rodados localmente) e afirmar conformidade com SLA.

## Riscos / Mitigações

- Ambiente pode não ter LaTeX completo → tentar `pdflatex`/`latexmk`; se falhar, registrar instrução de build manual.
- Benchmarks para 2M podem ser lentos → usar semente fixa e medir; em caso de timeout, documentar limites e valores observados.

## Saídas

- `docs/report.tex` (fonte LaTeX)
- `docs/report.pdf` (gerado)
- Testes atualizados em `tests/test_indexed_repository.py`
- SLA check em `benchmarks/run_benchmarks.py`
