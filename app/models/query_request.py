from pydantic import BaseModel

class QueryRequest(BaseModel):
    user_input: str
    table_schema: str  # Pode ser JSON ou string com estrutura da tabela
