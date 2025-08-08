import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
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
    SUM(CASE WHEN month = 'January' THEN sales_amount ELSE 0 END) as jan_sales,
    SUM(CASE WHEN month = 'February' THEN sales_amount ELSE 0 END) as feb_sales,
    ((SUM(CASE WHEN month = 'February' THEN sales_amount ELSE 0 END) - SUM(CASE WHEN month = 'January' THEN sales_amount ELSE 0 END)) / SUM(CASE WHEN month = 'January' THEN sales_amount ELSE 0 END) * 100) as growth_percentage
FROM sales WHERE month IN ('January', 'February')
"""
        
        prompt = f"""
You are an expert SQL query generator. Convert the natural language question to a SQL query.

Database Schema:
{schema_desc}

{examples_text}

Question: {question}

Generate a SQL query that answers this question. Return only the SQL query, nothing else.
"""
        
        return prompt
    
    def _format_schema(self, schema: Dict) -> str:
        """Format schema for prompt"""
        schema_text = ""
        for table_name, table_info in schema.get("tables", {}).items():
            schema_text += f"Table: {table_name}\n"
            for col_name, col_info in table_info.get("columns", {}).items():
                desc = col_info.get("description", "")
                schema_text += f"  - {col_name} ({col_info['type']}): {desc}\n"
            schema_text += "\n"
        return schema_text
    
    def _generate_suggestions(self, question: str, schema: Dict) -> Dict[str, List[str]]:
        """Generate visualization and follow-up suggestions"""
        
        # Simple rule-based suggestions
        visualizations = []
        follow_up_questions = []
        
        question_lower = question.lower()
        
        # Visualization suggestions
        if "por região" in question_lower or "by region" in question_lower:
            visualizations.extend(["bar_chart", "pie_chart", "map"])
        if "por mês" in question_lower or "by month" in question_lower or "crescimento" in question_lower:
            visualizations.extend(["line_chart", "area_chart"])
        if "top" in question_lower or "ranking" in question_lower:
            visualizations.extend(["bar_chart", "horizontal_bar"])
        if "comparação" in question_lower or "comparison" in question_lower:
            visualizations.extend(["bar_chart", "line_chart"])
        
        # Default visualization
        if not visualizations:
            visualizations = ["table", "bar_chart"]
        
        # Follow-up questions
        if "vendas" in question_lower or "sales" in question_lower:
            if "região" in question_lower or "region" in question_lower:
                follow_up_questions.extend([
                    "Quais produtos vendem melhor em cada região?",
                    "Como as vendas variam por mês em cada região?",
                    "Qual região tem o maior crescimento de vendas?"
                ])
            if "mês" in question_lower or "month" in question_lower:
                follow_up_questions.extend([
                    "Quais produtos tiveram melhor performance neste período?",
                    "Como as vendas se comparam com o período anterior?",
                    "Qual foi a tendência de crescimento?"
                ])
        
        return {
            "visualizations": visualizations[:3],  # Limit to 3 suggestions
            "follow_up_questions": follow_up_questions[:3]  # Limit to 3 suggestions
        }
