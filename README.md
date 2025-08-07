# askadb - nl-query

Transforma linguagem natural em SQL usando LLMs como OpenAI GPT.

## Executar localmente

```bash
uvicorn app.main:app --reload
```

## Endpoints
- POST `/translate/` → body `QueryRequest` → retorna `QueryResponse { query: string }`

## Variáveis de ambiente
- `OPENAI_API_KEY` (obrigatória)

## Makefile útil
```bash
make install
make run PORT=8001
make test
make docker-build && make docker-run
```

