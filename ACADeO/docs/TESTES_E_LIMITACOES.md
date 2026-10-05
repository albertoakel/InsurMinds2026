# Testes e limitações — ACADeO

## 1. Teste funcional principal

O fluxo mínimo esperado é:

1. iniciar o Streamlit;
2. enviar uma apólice;
3. verificar a extração;
4. confirmar o armazenamento;
5. enviar uma segunda apólice;
6. abrir a área de comparação;
7. selecionar as duas apólices;
8. executar a comparação.

## 2. Cenários de validação

### Documento novo

Resultado esperado: processamento normal e registro no SQLite.

### Documento já processado

Resultado esperado: a interface informa que o documento já existe e oferece cancelamento ou reprocessamento.

### Duas apólices salvas

Resultado esperado: os documentos aparecem como opções de seleção e a comparação é apresentada em tabela.

### Campo numérico ausente

Resultado esperado: o campo é marcado como não informado/incomparável.

### Texto diferente

Resultado esperado: a interface informa que a diferença requer análise da cláusula.

### Exclusões diferentes

Resultado esperado: as exclusões identificadas somente em cada apólice aparecem separadamente.

### Documento incompatível

O pipeline possui tratamento para documentos de outros ramos, identificando o tipo do documento e reduzindo a confiabilidade da análise.

## 3. Limitações conhecidas

A solução não deve ser interpretada como ferramenta de decisão jurídica automática.

A extração é dependente do modelo generativo e da qualidade do documento.

A comparação textual não equivale a uma comparação jurídica semântica.

O banco SQLite é adequado ao MVP, mas não foi escolhido para um cenário de alta concorrência.

O diretório `vectorbase` não participa do fluxo atual.

## 4. Critério de aceite do MVP

O MVP pode ser considerado funcional quando:

- a aplicação inicia;
- uma apólice é processada;
- os dados são persistidos;
- duas apólices podem ser consultadas;
- duas apólices podem ser comparadas;
- a interface apresenta as diferenças;
- o projeto pode ser instalado seguindo o README.
