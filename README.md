# PROJETO PARA GERAR INSIGHTS E BUSCAR POSSÍVEIS VENDAS

> Scripts e dados para coletar e transformar informações públicas do PNCP (Portal Nacional de Contratações Públicas).

- `Contratação_Total/` — coleta e parsing de propostas de contratação (JSON + parser -> fichas_propostas.txt).
- `Contratos_Total/` — coleta e parsing de contratos fechados (JSON + parser -> fichas_contratos.txt).


## Visão geral

O objetivo é coletar dados públicos do PNCP (propostas e contratos), agregar páginas da API em JSONs locais e transformar esses JSONs em arquivos de texto legíveis (`fichas_propostas.txt`, `fichas_contratos.txt`).


## Estrutura do repositório

```
Contratação_Total/
  ├─ contratacao_total.py          # coleta paginada e grava dados JSON de propostas
  ├─ dados_contratacoes.json       # JSON agregado (campo top-level `data`)
  ├─ parser.py                     # converte JSON -> fichas_propostas.txt
  └─ fichas_propostas.txt          # saída de exemplo (legível)

Contratos_Total/
  ├─ contratos_total.py            # coleta paginada de contratos e grava JSON agregado
  ├─ dados_contratos.json          # JSON grande com lista de contratos
  └─ fichas_contratos.txt          # saída de exemplo (legível)

README.md                          # este arquivo
```


## Dependências

- Python 3.8+ recomendado
- Biblioteca Python: `requests`, `json`, `time`, `pathlib` e `datetime`


## Como executar

1) Gerar `dados_contratacoes.json` (Contratação_Total)

```bat
python contratacao_total.py
```

Esse script faz paginação no endpoint de propostas do PNCP e grava `dados_contratacoes.json` e em seguida gera `fichas_propostas.txt` a partir do JSON.

2) Gerar `dados_contratos.json` (Contratos_Total)

```bat
python contratos_total.py
```

Esse script faz paginação no endpoint de propostas do PNCP e grava `dados_contratos.json` e em seguida gera `fichas_contratos.txt` a partir do JSON.# Mestrado_PPGMC