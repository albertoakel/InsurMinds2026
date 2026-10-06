# Testes e Limitações --- ACADeO

## 1. Objetivo

Os testes verificam o funcionamento do fluxo principal do MVP:

``` text
Upload → Triagem → Extração → Cláusulas → Consolidação → Validação → SQLite → Consulta → Comparação
```

O objetivo não é comprovar qualidade jurídica ou desempenho estatístico,
mas verificar a funcionalidade do protótipo.

## 2. Teste funcional principal

1.  iniciar o Streamlit;
2.  enviar uma apólice;
3.  acompanhar os três agentes;
4.  verificar a extração;
5.  confirmar o armazenamento;
6.  enviar uma segunda apólice;
7.  abrir a comparação;
8.  selecionar as duas apólices;
9.  executar a comparação;
10. verificar as diferenças.

## 3. Cenários de validação

### Documento novo

**Esperado:** processamento normal, consolidação, validação e registro
no SQLite.

### Acompanhamento dos agentes

**Esperado:** Streamlit e terminal apresentam `processando` e
`concluído` para os três agentes.

### Documento já processado

**Esperado:** a interface informa que o arquivo já existe e oferece
cancelamento ou reprocessamento.

### Reprocessamento

**Esperado:** os três agentes são executados novamente e um novo
registro é salvo.

### Duas apólices salvas

**Esperado:** ambas aparecem para seleção na área de comparação.

### Comparação numérica

**Esperado:** igualdade é identificada; diferenças têm percentual
calculado quando possível; ausência é indicada como não
informada/incomparável.

### Texto diferente

**Esperado:** diferença textual é sinalizada e requer análise da
cláusula.

### Exclusões diferentes

**Esperado:** exclusões identificadas somente em cada apólice aparecem
separadamente.

### Campo ausente

**Esperado:** o sistema não inventa o campo e representa a ausência no
resultado.

### Documento incompatível

**Esperado:** a triagem pode classificá-lo como não D&O e o pipeline
reduz a confiabilidade e registra alerta.

### Erro temporário do Gemini

**Esperado:** novas tentativas antes da interrupção.

### Ausência de credencial

**Esperado:** interrupção com indicação de que a chave da API não foi
encontrada.

## 4. Critério de aceite do MVP

O MVP é considerado funcional quando:

-   a aplicação inicia;
-   um documento pode ser enviado;
-   os três agentes são executados;
-   os dados são consolidados e validados;
-   a apólice é persistida;
-   duas apólices podem ser consultadas;
-   duas apólices podem ser comparadas;
-   a interface apresenta as diferenças;
-   a instalação segue o README.

## 5. Limitações conhecidas

### Modelo generativo

A extração depende do comportamento do Gemini e pode variar entre
documentos e execuções.

### Qualidade documental

PDFs ou imagens pouco legíveis podem reduzir a qualidade da extração.

### Dependência da API

O processamento depende da disponibilidade e da cota do Gemini.

### Comparação textual

Textos diferentes não significam necessariamente diferenças jurídicas. O
sistema sinaliza a diferença, mas não interpreta automaticamente seu
significado.

### Exclusões

A comparação atual é literal e não realiza comparação semântica
profunda.

### Confiabilidade

`alta`, `media` e `baixa` são categorias heurísticas, não probabilidades
estatísticas.

### Revisão humana

O ACADeO é apoio à análise documental. Diferenças contratuais relevantes
exigem leitura especializada.

### Persistência e escala

SQLite e execução local são escolhas de MVP e não de alta concorrência
ou operação distribuída.

### Segurança

Não há autenticação, autorização, gestão de usuários ou infraestrutura
de produção.

### Vectorbase

Apesar do nome, `vectorbase/apolices.db` é atualmente SQLite; não existe
banco vetorial operacional.

## 6. O que o sistema não deve afirmar

O ACADeO não deve ser interpretado como:

-   parecer jurídico;
-   recomendação automática de contratação;
-   decisão de subscrição;
-   decisão de regulação;
-   classificação definitiva de risco;
-   substituto da leitura das condições contratuais.

A comparação é um mecanismo de apoio à localização e organização das
diferenças.

## 7. Melhorias futuras

-   conjunto de documentos de referência;
-   métricas de precisão e cobertura;
-   avaliação campo a campo;
-   avaliação de evidências;
-   testes automatizados;
-   comparação semântica;
-   testes de consistência entre execuções;
-   testes de volume e concorrência;
-   RAG e banco vetorial;
-   geração de relatório;
-   API;
-   autenticação;
-   observabilidade.
