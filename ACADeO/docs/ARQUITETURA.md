# ACADeO — Arquitetura

## 1. Visão geral

O ACADeO foi estruturado como um MVP em camadas simples:

```text
Interface
   │
   ▼
app.py
   │
   ▼
src/pipeline.py
   ├── recebimento
   ├── extração multimodal
   ├── validação
   ├── persistência
   ├── consulta
   └── comparação
        │
        ▼
   apolices.db
```

## 2. Responsabilidade de cada componente

### `app.py`

Responsável pela camada de apresentação:

- upload do documento;
- confirmação de reprocessamento;
- exibição dos dados extraídos;
- consulta das apólices salvas;
- seleção de duas apólices;
- apresentação da comparação.

A interface utiliza as funções do pipeline em vez de duplicar a lógica de extração e comparação.

### `src/pipeline.py`

Concentra a lógica do MVP.

Principais funções:

- `receber()` — verifica existência, extensão e tamanho do arquivo;
- `extrair()` — envia documento e prompt ao Gemini;
- `validar()` — atribui indicador heurístico de confiabilidade e alertas;
- `salvar()` — persiste o JSON estruturado no SQLite;
- `listar_apolices()` — consulta os registros;
- `buscar_apolice()` — recupera uma apólice pelo ID;
- `comparar()` — produz as diferenças entre duas apólices.

### Pydantic

O modelo `ApoliceDO` define a estrutura esperada para o resultado da extração.

O modelo `Evidencia` associa um campo extraído a uma página e a um trecho literal do documento.

Isso cria uma base de rastreabilidade no dado estruturado, mesmo que a interface do MVP não apresente todas as evidências individualmente.

### SQLite

A tabela `apolices` mantém:

- ID;
- nome do arquivo;
- data de processamento;
- seguradora;
- tipo do documento;
- confiabilidade;
- LMI;
- JSON completo da análise.

O JSON completo é mantido para que os campos estruturados possam ser recuperados posteriormente sem uma nova chamada ao Gemini.

## 3. Uso do modelo generativo

O Gemini é utilizado na etapa de extração.

O documento é enviado como parte multimodal, acompanhado de instruções para:

1. extrair somente dados explicitamente presentes;
2. não inventar informações;
3. priorizar regiões relevantes da apólice;
4. produzir evidências de página e trecho;
5. devolver exclusivamente o JSON definido pelo schema.

A configuração utiliza resposta JSON estruturada e temperatura baixa.

## 4. Validação

A resposta do modelo é convertida em `ApoliceDO` por Pydantic.

Depois da validação estrutural, o pipeline calcula um indicador heurístico:

- `alta`;
- `media`;
- `baixa`.

Também são produzidos alertas quando há pouca informação extraída ou ausência de evidências em campos relevantes.

## 5. Comparação

A comparação não tenta produzir uma decisão jurídica automática.

Para valores numéricos, como LMI e limite agregado, o sistema calcula a diferença percentual quando ambos os valores estão disponíveis.

Para textos, o sistema diferencia:

- informação ausente;
- textos iguais;
- textos diferentes, que requerem leitura da cláusula.

As exclusões são comparadas por diferença entre conjuntos de textos.

## 6. Decisões arquiteturais

### Por que Streamlit?

Porque permite construir rapidamente uma interface funcional para demonstrar o MVP sem introduzir uma camada web complexa.

### Por que SQLite?

Porque o projeto é um protótipo educacional e precisa apenas de persistência local simples.

### Por que Pydantic?

Porque fornece uma estrutura explícita para os dados extraídos e permite validar a resposta JSON do modelo.

### Por que Gemini multimodal?

Porque a entrada principal é um documento PDF/imagem e o objetivo do MVP é demonstrar extração automática de conteúdo documental.

### Por que não usar vector database agora?

A comparação atual é baseada nos campos estruturados extraídos. Busca semântica, RAG ou recuperação vetorial podem ser adicionadas em uma evolução posterior, mas não são necessárias para demonstrar os requisitos centrais do MVP.

## 7. Evolução futura

Possibilidades:

- RAG e busca semântica;
- vector database;
- comparação semântica de cláusulas;
- apresentação das evidências diretamente na interface;
- processamento de maior volume de documentos;
- API;
- banco relacional externo;
- autenticação e controle de acesso;
- observabilidade;
- avaliação sistemática da qualidade da extração.
