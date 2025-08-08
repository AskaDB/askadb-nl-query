import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
        
        # Build the prompt
        prompt = self._build_prompt(request.question, schema, request.examples)
        
        try:
            # Generate SQL query
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SQL query generator. Convert natural language questions to SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
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
            return {
                "query": "SELECT * FROM sales LIMIT 10",
                "confidence": 0.1,
                "explanation": f"Error generating query: {str(e)}",
                "suggested_visualizations": ["table"],
                "suggested_follow_up_questions": []
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
SQL: SELECT region, SUM(sales_amount) as total_sales FROM sales WHERE month = 'May' GROUP BY region ORDER BY total_sales DESC

Question: Mostre os top 5 produtos por quantidade vendida
SQL: SELECT product, SUM(quantity) as total_quantity FROM sales GROUP BY product ORDER BY total_quantity DESC LIMIT 5

Question: Qual foi o crescimento de vendas entre janeiro e fevereiro?
SQL: SELECT 
    (SELECT SUM(sales_amount) FROM sales WHERE month = 'February') - 
    (SELECT SUM(sales_amount) FROM sales WHERE month = 'January') as growth
"""
        
        prompt = f"""Given the following database schema:

{schema_desc}

{examples_text}

Question: {question}

Generate a SQL query that answers this question. Return only the SQL query, nothing else:"""
        
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
            elif any(word in question_lower for word in ['tempo', 'time', 'mês', 'month']):
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
