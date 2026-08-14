
# 📊 Agente Inteligente para Dados Fiscais

Aplicação Streamlit para processamento, análise e consulta inteligente de Notas Fiscais Eletrônicas (NF-e) e dados fiscais em formato CSV/XML. O sistema combina um dashboard interativo com KPIs e gráficos com um assistente conversacional baseado em LLM (Google Gemini + LangChain) capaz de responder perguntas em linguagem natural sobre os dados carregados.

---

##  Funcionalidades

- **📤 Upload seguro de ZIPs** — Aceita arquivos ZIP contendo CSVs e/ou XMLs de notas fiscais, com validação de tamanho, quantidade de arquivos e proteção contra path traversal.
- **🤖 Assistente Conversacional** — Chatbot em português, alimentado por LLM (Gemini), que consulta os DataFrames diretamente via agente LangChain, respondendo perguntas sobre fornecedores, produtos, valores, datas e mais.
- **📈 Dashboard de KPIs** — Indicadores principais calculados automaticamente: total de notas, valor total, itens processados e ticket médio.
- **📉 Gráficos Interativos** — Visualizações em Plotly com tema escuro customizado:
  - Distribuição de notas por hora
  - Top 10 UF (emitente/destinatário)
  - Valor total por UF
  - Top produtos por valor e quantidade
  - Evolução temporal de itens por dia
- **🔄 Processamento Inteligente** — Conversão automática de tipos (datas ISO e formato brasileiro, valores monetários, quantidades, identificadores numéricos) e remoção automática de duplicatas.
- **📖 Dicionário de Dados** — Suporta dicionário manual (`dicionario_dados.csv`) ou geração automática a partir das colunas detectadas.
- **🧾 Leitura de XML (NF-e)** — Parser de arquivos XML de Nota Fiscal Eletrônica, extraindo dados do cabeçalho e itens/produtos.

---

##  Estrutura do Projeto

```
.
├── app2.py                      # Aplicação principal (Streamlit)
├── config.toml                  # Tema visual do Streamlit (dark mode customizado)
├── dataset/                     # Exemplos de dados e dicionário
│   ├── 202401_NFs.zip
│   ├── 202505_NFe.zip
│   ├── dicionario_dados.csv
│   ├── notas_fiscais.csv
│   └── produtos.csv
├── fullcode.txt                 # Código completo consolidado
└── src/                         # Módulos Python
    ├── __init__.py
    ├── agente.py                # Configuração do agente LangChain + Gemini
    ├── carregador.py            # Leitura de CSV, transformação de tipos e dicionário
    ├── carregador_original.py   # Versão original do carregador (backup)
    ├── kpis.py                  # Cálculo de KPIs e geração de gráficos Plotly
    ├── validador.py             # Extração segura de ZIPs
    └── xml_carregador.py        # Parser de XMLs de NF-e
```

---

## Instalação e Execução

### 1. Pré-requisitos
### Em contrução...


### 3. Configure a API Key

Crie um arquivo `.env` na raiz do projeto:

```env
GOOGLE_API_KEY=sua_chave_aqui
```

Ou exporte diretamente no terminal:

```bash
export GOOGLE_API_KEY=sua_chave_aqui  # Linux/Mac
set GOOGLE_API_KEY=sua_chave_aqui     # Windows
```

### 4. Execute

```bash
streamlit run app2.py
```

A aplicação abrirá em `http://localhost:8501`.

---

##  Formato dos Dados de Entrada

O sistema espera um arquivo **ZIP** contendo:

### CSVs
Arquivos `.csv` com dados de notas fiscais e/ou itens/produtos. As colunas são detectadas automaticamente por palavras-chave (case-insensitive), por exemplo:

- **Notas fiscais**: colunas com `numero`, `valor`, `total`, `uf`, `data`, `emissao`
- **Itens/Produtos**: colunas com `produto`, `descricao`, `quantidade`, `valor`, `unitario`, `ncm`, `cfop`

**Opcional**: inclua um arquivo `dicionario_dados.csv` com as colunas:
- `arquivo` — nome do arquivo (ex: `notas_fiscais.csv`)
- `coluna` — nome da coluna
- `descricao` — descrição da coluna
- `tipo` — tipo de dado

### XMLs (NF-e)
Arquivos XML de Nota Fiscal Eletrônica no layout da NF-e. O parser extrai automaticamente:
- Dados da nota (chave, número, série, data, emitente, destinatário, valores)
- Itens da nota (código, nome, NCM, CFOP, quantidade, valor unitário, valor total)

---

## 💬 Exemplos de Perguntas para o Assistente

> *"Qual fornecedor recebeu o maior valor?"*
> 
> *"Qual foi o total de vendas no mês de janeiro?"*
> 
> *"Quais são os 5 produtos mais vendidos por quantidade?"*
> 
> *"Qual a média de valor das notas emitidas por SP?"*

O agente utiliza o contexto das últimas 6 mensagens da conversa para manter a coerência do diálogo.

---


## Segurança️ 🛡

- **Validação de ZIP**: limite de 100 arquivos, 500MB descompactados, proteção contra path traversal (`..`).
- **Sanitização**: nomes de colunas normalizados (minúsculos, snake_case).
- **Agente restrito**: o LLM só pode operar sobre os DataFrames carregados, sem acesso a dados externos.

---

## Tecnologias

- [Streamlit](https://streamlit.io/) — Interface web
- [Pandas](https://pandas.pydata.org/) — Manipulação de dados
- [Plotly](https://plotly.com/python/) — Visualizações interativas
- [LangChain](https://www.langchain.com/) + [Google Generative AI](https://python.langchain.com/docs/integrations/chat/google_generative_ai/) — Agente conversacional
- [python-dotenv](https://saurabh-kumar.com/python-dotenv/) — Gerenciamento de variáveis de ambiente

---

## Suporte de Inteligência Artificial no Desenvolvimento
O desenvolvimento deste projeto contou com o suporte ativo de modelos de linguagem (LLMs) em diversas etapas do ciclo de criação, incluindo:
* Arquitetura e design de código — Estruturação dos módulos, padrões de projeto e separação de responsabilidades.
* Implementação e refatoração — Geração de código, otimização de funções e melhorias de performance.
* Debugging e testes — Identificação de bugs, análise de edge cases e validação de comportamentos.
* Documentação — Elaboração de docstrings, comentários técnicos e este próprio README.
As ferramentas de IA utilizadas incluem:
* Claude (Anthropic)
* DeepSeek
* Gemini (Google)

**Nota**: Todo o código gerado com auxílio de IA foi revisado, validado e adaptado manualmente para garantir qualidade, segurança e adequação ao domínio de dados fiscais brasileiros.
## Licença
Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para detalhes.

---

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests com melhorias, correções de bugs ou novas funcionalidades.
```