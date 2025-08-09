import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4"
        
    def generate_query(self, request) -> Dict[str, Any]:
        """Generate SQL query from natural language question"""
        
        # Default schema if not provided
        default_schema = {
            "tables": {
                "sales": {
                    "columns": {
                        "id": {"type": "INTEGER", "description": "Primary key"},
                        "region": {"type": "TEXT", "description": "Sales region (North, South, East, West)"},
                        "product": {"type": "TEXT", "description": "Product name (Product A, Product B)"},
                        "month": {"type": "TEXT", "description": "Month name (January, February, etc.)"},
                        "sales_amount": {"type": "REAL", "description": "Total sales amount in currency"},
                        "quantity": {"type": "INTEGER", "description": "Number of units sold"},
                        "created_at": {"type": "DATETIME", "description": "Record creation timestamp"}
                    }
                }
            }
        }
        
        schema = request.schema or default_schema
        
        # If no API key, use heuristic fallback directly
        if not self.client:
            sql_query = self._fallback_sql(request.question)
            suggestions = self._generate_suggestions(request.question, schema)
            return {
                "query": sql_query,
                "confidence": 0.7,
                "explanation": f"Heuristic SQL for: '{request.question}'",
                "suggested_visualizations": suggestions["visualizations"],
                "suggested_follow_up_questions": suggestions["follow_up_questions"]
            }
        
        # Build the prompt (improved)
        prompt = self._build_prompt(request.question, schema, request.examples)
        
        try:
            # Generate SQL query
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert analytics engineer. Convert natural language questions into production-grade SQL for SQLite. Prefer aggregated, decision-ready results that are easy to visualize."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=600
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Generate suggestions
            suggestions = self._generate_suggestions(request.question, schema)
            
            return {
                "query": sql_query,
                "confidence": 0.95,  # High confidence for simple queries
                "explanation": f"Generated SQL query for: '{request.question}'",
                "suggested_visualizations": suggestions["visualizations"],
                "suggested_follow_up_questions": suggestions["follow_up_questions"]
            }
            
        except Exception as e:
            logger.error(f"Error generating query: {e}")
            # Heuristic fallback on error
            sql_query = self._fallback_sql(request.question)
            suggestions = self._generate_suggestions(request.question, schema)
            return {
                "query": sql_query,
                "confidence": 0.6,
                "explanation": f"Fallback SQL due to error: {str(e)}",
                "suggested_visualizations": suggestions["visualizations"],
                "suggested_follow_up_questions": suggestions["follow_up_questions"]
            }
    
    def _build_prompt(self, question: str, schema: Dict, examples: Optional[List] = None) -> str:
        """Build a comprehensive prompt for SQL generation"""
        
        # Schema description
        schema_desc = self._format_schema(schema)
        
        # Examples
        examples_text = ""
        if examples:
            examples_text = "\n\nExamples:\n"
            for example in examples:
                examples_text += f"Question: {example.get('question', '')}\n"
                examples_text += f"SQL: {example.get('sql', '')}\n\n"
        
        # Default examples if none provided
        if not examples:
            examples_text = """
Examples:
Question: Quero vendas por região no mês de maio
SQL: SELECT region, SUM(sales_amount) AS total_sales FROM sales WHERE month = 'May' GROUP BY region ORDER BY total_sales DESC

Question: Mostre os top 5 produtos por quantidade vendida
SQL: SELECT product, SUM(quantity) AS total_quantity FROM sales GROUP BY product ORDER BY total_quantity DESC LIMIT 5

Question: Compare vendas por produto e região
SQL: SELECT product, region, SUM(sales_amount) AS total_sales FROM sales GROUP BY product, region ORDER BY product, region

Question: Vendas por mês ao longo do tempo
SQL: SELECT month, SUM(sales_amount) AS total_sales FROM sales GROUP BY month ORDER BY CASE lower(month)
  WHEN 'january' THEN 1 WHEN 'february' THEN 2 WHEN 'march' THEN 3 WHEN 'april' THEN 4 WHEN 'may' THEN 5 WHEN 'june' THEN 6 WHEN 'july' THEN 7 WHEN 'august' THEN 8 WHEN 'september' THEN 9 WHEN 'october' THEN 10 WHEN 'november' THEN 11 WHEN 'december' THEN 12 ELSE 99 END
"""
        
        guidelines = """
Instructions:
- Return ONLY the SQL. No markdown, no explanations.
- Use SELECT-only queries compatible with SQLite.
- Prefer aggregated results (SUM of measures) and GROUP BY all non-aggregated columns.
- Detect intent and structure the SQL accordingly:
  - Growth/variação/evolução/tendência: SELECT time period (e.g., month) and SUM(metric), GROUP BY period (and any secondary category if present). Do NOT compute growth in SQL; just return the aggregated time series for the visualization layer to compute.
  - Proporção/participação/percentual: SELECT category and SUM(metric), GROUP BY category.
  - Comparar duas dimensões (ex.: produto e região): SELECT both dimensions and SUM(metric), GROUP BY both.
  - Ranking/top/bottom: ORDER BY aggregated metric and add LIMIT (e.g., 5 ou 10).
- Choose a single main measure relevant to the question: prefer sales_amount; fallback to quantity.
- Keep column names as in the schema (product, region, month, sales_amount, quantity).
- Avoid SELECT *; select only necessary columns.
- Do not filter months unless the question specifies; keep the full range available.
"""
        
        prompt = f"""Given the following database schema:

{schema_desc}

{examples_text}

{guidelines}

Question: {question}

Return only the SQL query that answers the question.
"""
        
        return prompt
    
    def _format_schema(self, schema: Dict) -> str:
        """Format schema for prompt"""
        schema_text = "Database Schema:\n"
        for table_name, table_info in schema.get("tables", {}).items():
            schema_text += f"\nTable: {table_name}\n"
            for col_name, col_info in table_info.get("columns", {}).items():
                schema_text += f"  - {col_name} ({col_info.get('type', 'TEXT')}): {col_info.get('description', '')}\n"
        return schema_text
    
    def _generate_suggestions(self, question: str, schema: Dict) -> Dict[str, List[str]]:
        """Generate visualization and follow-up suggestions"""
        
        # Rule-based suggestions
        question_lower = question.lower()
        
        # Visualization suggestions
        visualizations = []
        if any(word in question_lower for word in ['vendas', 'sales', 'amount', 'quantidade']):
            if any(word in question_lower for word in ['região', 'region', 'produto', 'product']):
                visualizations.append('bar_chart')
            elif any(word in question_lower for word in ['tempo', 'time', 'mês', 'month', 'crescimento', 'variação', 'evolução']):
                visualizations.append('line_chart')
            else:
                visualizations.append('pie_chart')
        else:
            visualizations.append('table')
        
        # Follow-up questions
        follow_up_questions = []
        if 'região' in question_lower or 'region' in question_lower:
            follow_up_questions.append("Quais regiões tiveram melhor performance?")
            follow_up_questions.append("Compare vendas por região e produto")
        elif 'produto' in question_lower or 'product' in question_lower:
            follow_up_questions.append("Qual produto teve maior crescimento?")
            follow_up_questions.append("Mostre vendas por produto ao longo do tempo")
        else:
            follow_up_questions.append("Quero vendas por região no mês de maio")
            follow_up_questions.append("Mostre os top 5 produtos por quantidade vendida")
        
        return {
            "visualizations": visualizations,
            "follow_up_questions": follow_up_questions
        }

    def _fallback_sql(self, question: str) -> str:
        """Heuristic SQL generator for SQLite based on question keywords."""
        q = (question or '').lower()
        table = 'sales'
        measure = 'sales_amount'
        if 'quantidade' in q or 'quantity' in q:
            measure = 'quantity'
        has_region = 'região' in q or 'region' in q
        has_product = 'produto' in q or 'product' in q
        has_month = 'mês' in q or 'mes' in q or 'month' in q or 'tempo' in q or 'tend' in q or 'crescimento' in q or 'variação' in q or 'evolução' in q
        wants_top = 'top' in q or 'maiores' in q or 'rank' in q or 'melhores' in q
        limit = 10 if '10' in q else (5 if '5' in q or 'cinco' in q else 0)

        select_cols: List[str] = []
        group_cols: List[str] = []

        if has_month:
            select_cols.append('month')
            group_cols.append('month')
        if has_product:
            select_cols.append('product')
            group_cols.append('product')
        if has_region:
            select_cols.append('region')
            group_cols.append('region')

        # Default dimension if none detected
        if not select_cols:
            select_cols.append('product')
            group_cols.append('product')

        select_cols.append(f"SUM({measure}) AS total_{measure}")

        select_clause = ', '.join(select_cols)
        group_clause = f" GROUP BY {', '.join(group_cols)}" if group_cols else ''

        order_expr = f"total_{measure} DESC"
        # If only month present, order by chronological month order
        order_clause = " ORDER BY "
        if group_cols == ['month']:
            order_clause += "CASE lower(month) WHEN 'january' THEN 1 WHEN 'february' THEN 2 WHEN 'march' THEN 3 WHEN 'april' THEN 4 WHEN 'may' THEN 5 WHEN 'june' THEN 6 WHEN 'july' THEN 7 WHEN 'august' THEN 8 WHEN 'september' THEN 9 WHEN 'october' THEN 10 WHEN 'november' THEN 11 WHEN 'december' THEN 12 ELSE 99 END"
        else:
            order_clause += order_expr

        limit_clause = f" LIMIT {limit}" if wants_top and limit > 0 else (" LIMIT 5" if wants_top else "")

        sql = f"SELECT {select_clause} FROM {table}{group_clause}{order_clause}{limit_clause}"
        return sql
