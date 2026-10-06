# ACADeO --- Arquitetura

## 1. Visão geral

A versão final utiliza uma arquitetura em camadas simples: interface
Streamlit, pipeline multiagente, modelos estruturados, persistência
SQLite e comparação determinística.

``` text
PDF / imagem
     ↓
app.py / Streamlit
     ↓
src/pipeline_multiagent.py
     ↓
┌──────────────┬─────────────────────┬─────────────────────┐
│ Agente 1     │ Agente 2            │ Agente 3            │
│ Triagem      │ Extração Estrutural │ Análise de Cláusulas│
└──────────────┴─────────────────────┴─────────────────────┘
     ↓
Consolidação / Pydantic
     ↓
SQLite / apolices.db
     ↓
Consulta / Comparação
```

## 2. Componentes

### `app.py`

Interface final. Responsável por upload, acionamento do processamento,
status dos agentes, reprocessamento, consulta e apresentação da
comparação.

### `app_zero.py`

Versão anterior da interface. Mantida como referência histórica e não
utilizada pelo fluxo final.

### `src/pipeline_multiagent.py`

Núcleo da versão final. Concentra recebimento, agentes Gemini,
consolidação, validação, persistência, consulta e comparação.

## 3. Agentes

### Agente 1 --- Triagem

Classifica o documento, verifica se é relacionado a D&O e identifica o
tipo. Pode interromper a extração detalhada quando não houver
classificação como D&O.

### Agente 2 --- Extração Estrutural

Extrai dados cadastrais, financeiros e de vigência: seguradora, tomador,
SUSEP, tipo, vigência, LMI, limite agregado, prêmio e evidências.

### Agente 3 --- Análise de Cláusulas

Extrai base de reclamações, POS/franquia, Coberturas A/B/C, custos de
defesa, prazos, retroatividade, territorialidade, exclusões e
evidências.

## 4. Fluxo

``` text
1. Upload
   ↓
2. receber()
   ↓
3. Triagem
   ↓
4. Extração Estrutural
   ↓
5. Análise de Cláusulas
   ↓
6. Consolidação
   ↓
7. Pydantic
   ↓
8. validar()
   ↓
9. salvar()
```

## 5. Comunicação com a interface

O pipeline recebe um callback opcional e envia:

``` text
(nome_agente, "processando")
(nome_agente, "concluído")
```

O `app.py` converte os eventos em mensagens do Streamlit. O terminal
também mantém os prints de acompanhamento.

## 6. Modelo de dados

`ApoliceDO` representa a apólice consolidada. `Evidencia` associa um
campo ao número da página e a um trecho literal.

``` text
campo extraído
     ↓
página
     ↓
trecho literal
```

## 7. Persistência

``` text
vectorbase/apolices.db
```

A tabela `apolices` mantém o registro principal e o JSON completo da
análise. O JSON permite recuperar os dados sem nova chamada ao Gemini.

O diretório `vectorbase` não contém banco vetorial nesta versão; é área
de persistência e ponto de extensão.

## 8. Comparação

``` text
Apolice A ─┐
           ├── Python determinístico ──► resultado
Apolice B ─┘
```

Valores numéricos são comparados por regras determinísticas. Textos são
classificados como ausentes, iguais ou diferentes. Exclusões são
comparadas por diferença literal entre listas.

## 9. Separação entre IA e regras

``` text
IA Generativa
 ├── classificação
 ├── extração
 └── identificação de cláusulas
             ↓
       dados estruturados
             ↓
Python determinístico
 ├── validação
 ├── persistência
 └── comparação
```

A arquitetura limita a responsabilidade do modelo generativo na etapa de
comparação.

## 10. Decisões arquiteturais

-   **Streamlit:** interface funcional com baixa complexidade.
-   **Gemini multimodal:** adequado a documentos PDF/imagem.
-   **Multiagente:** separa triagem, extração estrutural e cláusulas.
-   **Pydantic:** valida respostas estruturadas.
-   **SQLite:** persistência simples para o MVP.
-   **Comparação determinística:** comportamento reproduzível para
    regras numéricas e literais.
-   **Sem RAG/vector database:** não necessário para a comparação atual.

## 11. Limites

A arquitetura atual não foi projetada para alta concorrência,
processamento massivo, operação distribuída, integração com seguradoras,
autenticação, autorização, auditoria operacional completa ou decisão
jurídica automática.

## 12. Evolução

Uma evolução possível adicionaria validação/revisão, RAG, banco
vetorial, busca semântica, comparação semântica, geração de relatórios,
API, autenticação e observabilidade.

## 13. Estrutura final

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
