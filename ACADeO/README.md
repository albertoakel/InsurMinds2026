# ACADeO --- Agente Comparador de Apólices D&O

MVP educacional para **extração, organização e comparação de informações
de apólices de seguro D&O utilizando Inteligência Artificial
Generativa**.

## Sobre o projeto

O ACADeO recebe uma apólice em PDF ou imagem, realiza análise documental
com Gemini e organiza as informações em uma estrutura padronizada.

A versão final utiliza três etapas especializadas:

1.  **Agente 1 --- Triagem**
2.  **Agente 2 --- Extração Estrutural**
3.  **Agente 3 --- Análise de Cláusulas**

Depois da extração, os resultados são consolidados e validados com
Pydantic, armazenados em SQLite e disponibilizados para consulta e
comparação.

A comparação entre apólices é realizada por regras determinísticas em
Python.

> **Importante:** o ACADeO é um MVP educacional e não constitui
> ferramenta de decisão jurídica, subscrição, regulação ou
> aconselhamento profissional.

## Arquitetura

``` text
PDF / imagem
     ↓
Streamlit / app.py
     ↓
pipeline_multiagent.py
     ↓
┌───────────────┬────────────────────┬─────────────────────┐
│ Agente 1      │ Agente 2           │ Agente 3            │
│ Triagem       │ Extração Estrutural│ Análise de Cláusulas│
└───────────────┴────────────────────┴─────────────────────┘
     ↓
Consolidação / Pydantic
     ↓
SQLite
     ↓
Consulta / Comparação
```

Durante o processamento, a interface apresenta o andamento dos três
agentes.

## Estrutura do projeto

``` text
ACADeO/
├── app.py
├── app_zero.py
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml
├── src/
│   ├── __init__.py
│   ├── pipeline.py
│   └── pipeline_multiagent.py
├── vectorbase/
│   ├── apolices.db
│   └── README.md
└── docs/
    ├── README.md
    ├── RELATORIO_TECNICO.md
    ├── ARQUITETURA.md
    └── TESTES_E_LIMITACOES.md
```

-   `app.py` --- interface final.
-   `app_zero.py` --- versão anterior da interface.
-   `src/pipeline_multiagent.py` --- pipeline final multiagente.
-   `src/pipeline.py` --- versão anterior da interface.
-   `vectorbase/apolices.db` --- banco SQLite.
-   `docs/` --- documentação técnica.

## Tecnologias

-   Python
-   Streamlit
-   Google Gemini / Google GenAI
-   Pydantic
-   SQLite
-   python-dotenv

## Instalação

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows:

``` powershell
.venv\Scripts\activate
```

## Configuração da API

Crie `.env` na raiz:

``` env
GOOGLE_API_KEY=sua_chave_aqui
```

O projeto também aceita `GOOGLE_API`.

Não publique a chave da API no GitHub.

## Execução

``` bash
streamlit run app.py
```

## Fluxo de utilização

### Upload e análise

Selecione `Upload e Análise`, envie um PDF ou imagem e clique em
`Analisar Documento`.

A aplicação executará:

``` text
Agente 1 — Triagem
        ↓
Agente 2 — Extração Estrutural
        ↓
Agente 3 — Análise de Cláusulas
```

O andamento aparece no Streamlit e no terminal.

### Apólices salvas

A área `Apólices Salvas` apresenta os documentos armazenados no SQLite.

### Comparação

A área `Comparar Apólices` permite selecionar duas apólices e visualizar
LMI, limite agregado, coberturas, custos de defesa, base de reclamações,
POS/franquia, prazos, retroatividade, territorialidade e exclusões.

Diferenças textuais são sinalizadas para análise humana.

## Persistência

``` text
vectorbase/apolices.db
```

Apesar do nome `vectorbase`, não há banco vetorial nesta versão. O
diretório funciona como área de persistência e ponto de extensão para
uma futura implementação de RAG ou busca vetorial.

## Limitações

-   dependência da qualidade dos documentos;
-   dependência da disponibilidade e cota da API Gemini;
-   possível variação da extração;
-   comparação textual literal;
-   ausência de interpretação jurídica semântica;
-   indicador de confiabilidade heurístico;
-   SQLite para persistência local;
-   ausência de autenticação e infraestrutura de produção.

Os resultados devem ser considerados apoio à análise documental.

## Documentação

-   [`docs/RELATORIO_TECNICO.md`](docs/RELATORIO_TECNICO.md)
-   [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md)
-   [`docs/TESTES_E_LIMITACOES.md`](docs/TESTES_E_LIMITACOES.md)

## Uso de Inteligência Artificial no desenvolvimento

A IA Generativa foi utilizada como apoio à elaboração e revisão de
código, depuração, investigação de erros, organização arquitetural e
documentação. Os resultados foram revisados e testados antes da
incorporação.

No produto, a IA também é componente funcional: o Gemini realiza a
análise multimodal e a extração automática das informações.

Distingue-se, portanto:

-   **IA como ferramenta de desenvolvimento:** programação, depuração,
    revisão e documentação.
-   **IA como componente da solução:** extração automática dos
    documentos.

## Licença

Este projeto é distribuído sob a licença MIT.

Consulte [`LICENSE`](LICENSE) para o texto completo.
