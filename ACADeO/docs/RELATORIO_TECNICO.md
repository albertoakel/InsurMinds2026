# Relatório Técnico --- ACADeO

## Agente Comparador de Apólices D&O

### 1. Resumo executivo

O **ACADeO --- Agente Comparador de Apólices D&O** é um MVP educacional
de aplicação de Inteligência Artificial Generativa voltado à extração,
organização e comparação de informações presentes em apólices de seguro
D&O.

A solução recebe documentos em PDF ou imagem, utiliza o Gemini para
análise multimodal, organiza as informações em estruturas tipadas,
armazena o resultado em SQLite e permite consultar e comparar duas
apólices por meio de uma interface Streamlit.

A versão final utiliza uma arquitetura **multiagente**, composta por
três etapas especializadas:

1.  **Agente 1 --- Triagem**
2.  **Agente 2 --- Extração Estrutural**
3.  **Agente 3 --- Análise de Cláusulas**

A comparação entre apólices permanece determinística, implementada em
Python, evitando que o modelo generativo seja responsável por concluir
automaticamente qual contrato é juridicamente superior.

O projeto prioriza uma arquitetura simples, demonstrável e evolutiva,
adequada ao escopo educacional.

### 2. Problema

Apólices de seguro D&O são documentos extensos e não estruturados, com
informações distribuídas entre quadro-resumo, condições gerais,
cláusulas específicas e outras seções.

A comparação manual exige localizar informações, organizar campos
equivalentes, verificar valores e identificar diferenças entre cláusulas
e exclusões.

O ACADeO automatiza principalmente o trabalho mecânico de localização e
organização dessas informações, mantendo a análise humana para situações
em que diferenças textuais ou contratuais exigem interpretação
especializada.

### 3. Objetivo

O MVP foi desenvolvido para:

1.  receber uma apólice em PDF ou imagem;
2.  classificar o documento;
3.  extrair automaticamente informações relevantes;
4.  estruturar os dados em formato padronizado;
5.  armazenar as análises;
6.  consultar documentos processados;
7.  comparar pelo menos duas apólices;
8.  apresentar as principais diferenças em interface gráfica;
9.  tornar visível a execução das etapas multiagente.

### 4. Escopo

O MVP contempla:

-   upload de PDF e imagens;
-   análise multimodal com Gemini;
-   três agentes especializados;
-   respostas em JSON estruturado;
-   validação com Pydantic;
-   persistência em SQLite;
-   consulta das apólices processadas;
-   detecção e reprocessamento de documentos já existentes;
-   comparação de duas apólices;
-   comparação numérica e textual;
-   identificação de exclusões presentes somente em cada apólice;
-   indicador heurístico de confiabilidade;
-   alertas;
-   interface Streamlit;
-   exibição do andamento dos agentes no Streamlit e no terminal.

O projeto não pretende ser sistema comercial de subscrição, regulação ou
aconselhamento jurídico.

### 5. Arquitetura

``` text
PDF / imagem
     ↓
Streamlit / app.py
     ↓
src/pipeline_multiagent.py
     ↓
Agente 1 — Triagem
     ↓
Agente 2 — Extração Estrutural
     ↓
Agente 3 — Análise de Cláusulas
     ↓
Consolidação / Pydantic
     ↓
SQLite / apolices.db
     ↓
Consulta / Comparação
```

O `app_zero.py` é a versão anterior da interface e não participa do
fluxo final.

### 6. Tecnologias

-   **Python:** linguagem principal.
-   **Streamlit:** interface.
-   **Google Gemini / Google GenAI:** análise multimodal e extração.
-   **Pydantic:** estrutura e validação dos dados.
-   **SQLite:** persistência local.
-   **python-dotenv:** carregamento da credencial da API.

### 7. Uso de IA

A IA Generativa participa do projeto em duas dimensões.

**Como ferramenta de desenvolvimento:** apoio à elaboração e revisão de
código, depuração, discussão arquitetural e documentação. Os resultados
foram revisados e testados antes da incorporação.

**Como componente funcional:** o Gemini analisa os documentos e executa
as três etapas especializadas. As respostas são solicitadas em JSON
estruturado e consolidadas e validadas pelo Pydantic.

A IA não substitui a revisão humana das cláusulas.

### 8. Pipeline multiagente

#### Agente 1 --- Triagem

Classifica o documento, verifica se é relacionado a D&O e identifica seu
tipo. Pode interromper a extração detalhada quando o documento não é
classificado como D&O.

#### Agente 2 --- Extração Estrutural

Extrai dados cadastrais, financeiros e de vigência, incluindo
seguradora, tomador, SUSEP, tipo, vigência, LMI, limite agregado, prêmio
e evidências.

#### Agente 3 --- Análise de Cláusulas

Extrai base de reclamações, POS/franquia, Coberturas A/B/C, custos de
defesa, prazos, retroatividade, territorialidade, exclusões e
evidências.

#### Consolidação

Os resultados são reunidos em uma única estrutura `ApoliceDO`, incluindo
as evidências produzidas pelos agentes.

### 9. Status dos agentes

A versão final utiliza um callback entre pipeline e interface. O
pipeline envia os estados `processando` e `concluído` para cada agente.

Exemplo:

``` text
🔄 Agente 1 - Triagem: processando...
✅ Agente 1 - Triagem: concluído
🔄 Agente 2 - Extração Estrutural: processando...
✅ Agente 2 - Extração Estrutural: concluído
🔄 Agente 3 - Análise de Cláusulas: processando...
✅ Agente 3 - Análise de Cláusulas: concluído
```

O mesmo andamento pode ser acompanhado no terminal.

### 10. Ingestão e extração

`receber()` verifica existência, extensão, arquivo não vazio e limite de
20 MB. O pipeline aceita PDF, PNG, JPG, JPEG e WEBP.

Cada agente utiliza o SDK Google GenAI com documento multimodal, prompt
especializado, resposta JSON estruturada e temperatura baixa. Há
tratamento para indisponibilidade temporária e cota da API.

### 11. Dados e validação

`ApoliceDO` organiza seguradora, tomador, SUSEP, tipo, vigência, base de
reclamações, valores, coberturas, condições, exclusões, evidências,
confiabilidade e alertas.

`Evidencia` associa campo, página e trecho literal.

Após a consolidação, Pydantic valida a estrutura. O sistema calcula uma
confiabilidade heurística (`alta`, `media` ou `baixa`) e registra
alertas. Essa classificação não representa probabilidade estatística de
acerto.

### 12. Persistência

O banco é:

``` text
vectorbase/apolices.db
```

A tabela `apolices` armazena `id`, arquivo, data de processamento,
seguradora, tipo, confiabilidade, LMI e o JSON completo.

O JSON completo permite recuperar a análise sem nova chamada ao Gemini.

Apesar do nome `vectorbase`, não existe banco vetorial nesta versão. O
diretório é uma área de persistência e ponto de extensão futuro.

### 13. Comparação

A função `comparar()` é determinística e executada em Python.

Para LMI e limite agregado, verifica ausência, igualdade e diferença
percentual quando ambos os valores existem.

Para informações textuais, identifica ausência, igualdade ou diferença e
sinaliza textos diferentes para análise humana.

As exclusões são comparadas por diferença literal entre as listas
extraídas. Isso não equivale a interpretação jurídica semântica.

### 14. Interface

A interface final possui:

-   **Upload e Análise:** upload, processamento, status dos agentes,
    reprocessamento, dados, confiabilidade e alertas;
-   **Apólices Salvas:** consulta dos registros;
-   **Comparar Apólices:** seleção de duas apólices e apresentação das
    diferenças.

### 15. Tratamento de erros

São tratados, entre outros:

-   arquivo inexistente;
-   extensão não suportada;
-   arquivo vazio;
-   arquivo acima do limite;
-   ausência da chave Gemini;
-   indisponibilidade temporária;
-   cota esgotada;
-   JSON incompatível;
-   apólice inexistente.

Erros temporários do Gemini podem gerar novas tentativas antes da
interrupção.

### 16. Decisões arquiteturais

**Multiagente:** separa responsabilidades em triagem, extração
estrutural e análise de cláusulas.

**Comparação determinística:** mantém regras numéricas e literais
reproduzíveis fora do modelo generativo.

**Gemini multimodal:** adequado ao processamento de documentos
PDF/imagem.

**Pydantic:** valida a resposta estruturada.

**SQLite:** simples e adequado ao protótipo.

**Streamlit:** permite demonstração funcional com baixa complexidade.

**Sem RAG/vector database:** não são necessários para a comparação
atual, baseada em campos estruturados.

### 17. Limitações

1.  resultados generativos podem variar;
2.  documentos pouco legíveis podem reduzir a qualidade;
3.  o processamento depende da API Gemini;
4.  comparação textual não significa diferença jurídica;
5.  exclusões são comparadas literalmente;
6.  confiabilidade é heurística;
7.  revisão humana continua necessária;
8.  SQLite e execução local não são escolhas de alta escala;
9.  não há autenticação ou infraestrutura de produção;
10. não há integrações externas;
11. não há banco vetorial operacional.

### 18. Evolução futura

Possibilidades:

-   RAG e banco vetorial;
-   busca e comparação semântica;
-   classificação mais detalhada de cláusulas;
-   exibição de evidências na interface;
-   geração de relatório comparativo;
-   API;
-   banco externo;
-   autenticação e controle de acesso;
-   observabilidade;
-   avaliação sistemática da qualidade.

### 19. Execução

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure:

``` env
GOOGLE_API_KEY=sua_chave_aqui
```

Execute:

``` bash
streamlit run app.py
```

### 20. Demonstração sugerida

1.  abrir a aplicação;
2.  enviar uma apólice;
3.  mostrar os três agentes;
4.  mostrar os dados extraídos;
5.  mostrar confiabilidade e alertas;
6.  carregar uma segunda apólice;
7.  abrir `Comparar Apólices`;
8.  executar a comparação;
9.  mostrar diferenças numéricas e textuais;
10. mostrar exclusões identificadas somente em cada apólice;
11. explicar que diferenças relevantes exigem análise humana.

### 21. Conclusão

O ACADeO integra modelo generativo multimodal, arquitetura multiagente,
estruturação de dados, persistência local e comparação determinística.

``` text
Documento
 ↓
Triagem
 ↓
Extração Estrutural
 ↓
Análise de Cláusulas
 ↓
Pydantic
 ↓
SQLite
 ↓
Comparação
 ↓
Interface
```

A arquitetura foi mantida deliberadamente simples para facilitar
compreensão, demonstração, avaliação e evolução posterior.
