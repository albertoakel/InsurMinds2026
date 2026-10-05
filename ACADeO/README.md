# ACADeO — Agente Comparador de Apólices D&O

MVP educacional para extração, organização e comparação de informações de apólices de seguro D&O utilizando IA Generativa.

## Estrutura

```text
ACADeO/
├── app.py
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── .streamlit/
├── src/
│   └── pipeline.py
├── vectorbase/
│   ├── apolices.db
│   └── README.md
└── docs/
```

## Persistência

O banco SQLite utilizado pela aplicação fica em:

```text
vectorbase/apolices.db
```

O diretório `vectorbase` é apenas a área de persistência do MVP. Não há banco vetorial implementado nesta versão.

## Execução

```bash
pip install -r requirements.txt
streamlit run app.py
```

Configure a chave da API Gemini no `.env`:

```text
GOOGLE_API_KEY=sua_chave
```

A aplicação cria automaticamente `vectorbase/apolices.db` quando o banco ainda não existe.

## Uso de Inteligência Artificial no Desenvolvimento

A Inteligência Artificial Generativa foi utilizada como ferramenta de apoio durante o desenvolvimento do ACADeO, principalmente para auxiliar na elaboração, revisão e depuração do código, na organização da arquitetura do projeto, na identificação de erros e na elaboração da documentação técnica.

O uso de IA no desenvolvimento não substituiu a execução e validação do código. As funcionalidades foram testadas no ambiente do projeto e as decisões de implementação foram avaliadas de acordo com os requisitos do Projeto Final.

Além do uso da IA como ferramenta de desenvolvimento, a própria solução utiliza Inteligência Artificial Generativa como componente funcional do sistema. O modelo Gemini é utilizado para analisar os documentos enviados, extrair informações relevantes das apólices e retornar os dados em formato estruturado, posteriormente validado pelo Pydantic.

Dessa forma, é importante distinguir:

- **IA como ferramenta de desenvolvimento:** utilizada como apoio à programação, depuração, revisão e documentação.
- **IA como componente da solução:** utilizada pelo ACADeO para a extração automática de informações das apólices de seguro D&O.

A utilização de IA no desenvolvimento foi orientada por validação humana, testes e revisão dos resultados produzidos.

## Licença

Este projeto é distribuído sob a licença MIT.

A licença permite o uso, cópia, modificação, distribuição e sublicenciamento do software, observadas as condições estabelecidas no texto da licença.

Consulte o arquivo [`LICENSE`](LICENSE) para o texto completo da licença.
