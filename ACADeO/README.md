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
