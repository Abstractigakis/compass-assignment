import json
import gzip
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import os
import google.generativeai as genai
from pathlib import Path


class ETLWriter:
    """
    A class that consumes HTML content and uses Google Gemini to:
    1. Learn what entities are on the page worth extracting
    2. Generate an entities.json schema
    3. Create a Python ETL function to extract the data
    4. Execute the ETL function
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ETL Writer with Gemini API key

        Args:
            api_key: Google API key for Gemini. If None, will try to get from environment
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        # Storage for generated artifacts
        self.entities_schema = None
        self.etl_function_code = None
        self.extracted_data = None

    def decompress_html(self, html_gzip_base64: str) -> str:
        """
        Decompress gzipped base64 HTML content

        Args:
            html_gzip_base64: Base64 encoded gzipped HTML string

        Returns:
            Decompressed HTML string
        """
        try:
            # Decode base64
            compressed_data = base64.b64decode(html_gzip_base64)
            # Decompress gzip
            html_content = gzip.decompress(compressed_data).decode("utf-8")
            return html_content
        except Exception as e:
            raise ValueError(f"Failed to decompress HTML: {str(e)}")

    def generate_entities_schema(
        self, html_content: str, goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use Gemini to analyze HTML and generate entities.json schema

        Args:
            html_content: The HTML content to analyze
            goal: Optional goal text to guide extraction

        Returns:
            Dictionary representing the entities schema
        """
        goal_instruction = f"\n\nEXTRACTION GOAL: {goal}" if goal else ""

        prompt = f"""You are an expert data analyst examining HTML content. Analyze the ENTIRE HTML content below and identify ALL meaningful entities that should be extracted.

{goal_instruction}

INSTRUCTIONS:
1. Examine the HTML structure carefully - look for repeating patterns, data-rich elements, forms, lists, tables, etc.
2. Identify specific CSS selectors, class names, and element patterns
3. Focus on actionable data: products, articles, contact info, prices, reviews, metadata, navigation, etc.
4. Create a comprehensive schema covering ALL entity types found

Return ONLY valid JSON with this exact structure:
{{
    "entities": {{
        "entity_name": {{
            "description": "What this entity represents",
            "is_collection": true,
            "css_selectors": ["actual CSS selectors found in HTML"],
            "fields": {{
                "field_name": {{
                    "type": "string|number|boolean|array|object",
                    "description": "Field purpose",
                    "selector": "CSS selector or extraction method",
                    "required": true,
                    "example": "actual example from HTML"
                }}
            }}
        }}
    }},
    "page_metadata": {{
        "page_type": "e.g. product_listing, article, contact_page",
        "extraction_complexity": "low|medium|high",
        "total_entities": 0,
        "main_content_areas": ["CSS selectors for main content"]
    }}
}}

HTML CONTENT:
{html_content}

IMPORTANT: Base your schema on what you ACTUALLY see in the HTML, not assumptions. Include real CSS selectors and class names."""

        try:
            response = self.model.generate_content(prompt)
            schema_text = response.text.strip()

            # Clean up markdown formatting
            if schema_text.startswith("```json"):
                schema_text = schema_text[7:]
            if schema_text.endswith("```"):
                schema_text = schema_text[:-3]

            schema = json.loads(schema_text)
            self.entities_schema = schema
            return schema

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to generate entities schema: {str(e)}")

    def generate_etl_function(
        self, html_content: str, entities_schema: Dict[str, Any]
    ) -> str:
        """
        Generate Python ETL function code using Gemini

        Args:
            html_content: The HTML content to analyze
            entities_schema: The entities schema generated previously

        Returns:
            Python code string for the ETL function
        """
        prompt = f"""You are an expert Python developer. Generate a working ETL function that extracts data from HTML using the provided schema.

ENTITIES SCHEMA:
{json.dumps(entities_schema, indent=2)}

REQUIREMENTS:
1. Function name: extract_entities_from_html
2. Parameter: html_content (string)
3. Returns: dictionary matching schema structure
4. Use BeautifulSoup for parsing
5. Extract ALL items for collections, not just first
6. Handle missing elements gracefully
7. Include actual CSS selectors from schema
8. Clean and normalize extracted text
9. Return meaningful data, not empty collections

CRITICAL: 
- Use the exact CSS selectors from the schema
- Actually extract data, don't return empty results
- Check element existence before accessing properties
- Handle both single items and collections properly

Generate working Python code that will successfully extract data from this HTML:

{html_content}

Return ONLY the Python code, no explanations or markdown."""

        try:
            response = self.model.generate_content(prompt)
            function_code = response.text.strip()

            # Clean up code formatting
            if function_code.startswith("```python"):
                function_code = function_code[9:]
            if function_code.endswith("```"):
                function_code = function_code[:-3]

            self.etl_function_code = function_code
            return function_code

        except Exception as e:
            raise ValueError(f"Failed to generate ETL function: {str(e)}")

    def execute_etl_function(
        self, html_content: str, etl_function_code: str
    ) -> Dict[str, Any]:
        """
        Execute the generated ETL function on the HTML content

        Args:
            html_content: The HTML content to process
            etl_function_code: The generated Python ETL function code

        Returns:
            Extracted data dictionary
        """
        try:
            # Create execution environment with required imports
            namespace = {
                "html_content": html_content,
                "__builtins__": __builtins__,
                "print": print,
            }

            # Add required imports
            imports_to_add = [
                ("bs4", "BeautifulSoup"),
                ("re", None),
                ("json", None),
                ("urllib.parse", None),
                ("datetime", None),
            ]

            for module_name, specific_import in imports_to_add:
                try:
                    if specific_import:
                        module = __import__(module_name, fromlist=[specific_import])
                        namespace[specific_import] = getattr(module, specific_import)
                        namespace[module_name] = module
                    else:
                        namespace[module_name] = __import__(module_name)
                except ImportError:
                    continue

            # Execute the ETL function code
            exec(etl_function_code, namespace)

            # Get and validate the function
            extract_function = namespace.get("extract_entities_from_html")
            if not extract_function:
                raise ValueError(
                    "Generated code missing 'extract_entities_from_html' function"
                )

            if not callable(extract_function):
                raise ValueError("'extract_entities_from_html' is not callable")

            # Execute the function
            extracted_data = extract_function(html_content)

            # Validate results
            if extracted_data is None:
                raise ValueError("ETL function returned None")

            if not isinstance(extracted_data, dict):
                raise ValueError(
                    f"ETL function returned {type(extracted_data)}, expected dict"
                )

            self.extracted_data = extracted_data
            return extracted_data

        except Exception as e:
            raise ValueError(f"Failed to execute ETL function: {str(e)}")

    def save_artifacts(self, output_dir: str = "etl_artifacts"):
        """
        Save generated artifacts to files

        Args:
            output_dir: Directory to save artifacts
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save entities schema
        if self.entities_schema:
            with open(output_path / f"entities_{timestamp}.json", "w") as f:
                json.dump(self.entities_schema, f, indent=2)

        # Save ETL function code
        if self.etl_function_code:
            with open(output_path / f"etl_function_{timestamp}.py", "w") as f:
                f.write(self.etl_function_code)

        # Save extracted data
        if self.extracted_data:
            with open(output_path / f"extracted_data_{timestamp}.json", "w") as f:
                json.dump(self.extracted_data, f, indent=2)

    def process_html(
        self, html_gzip_base64: str, goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ETL pipeline: decompress HTML, generate schema, create function (no execution)

        Args:
            html_gzip_base64: Base64 encoded gzipped HTML string
            goal: Optional goal text to guide extraction

        Returns:
            Dictionary containing generated schema and function code
        """
        try:
            # Step 1: Decompress HTML
            print("Step 1: Decompressing HTML...")
            html_content = self.decompress_html(html_gzip_base64)
            print(f"HTML decompressed: {len(html_content)} characters")

            # Step 2: Generate entities schema
            print("Step 2: Generating entities schema...")
            entities_schema = self.generate_entities_schema(html_content, goal)
            print(
                f"Entities schema generated with {len(entities_schema.get('entities', {}))} entity types"
            )

            # Step 3: Generate ETL function
            print("Step 3: Generating ETL function...")
            etl_function_code = self.generate_etl_function(
                html_content, entities_schema
            )
            print(f"ETL function generated: {len(etl_function_code)} characters")

            return {
                "entities_schema": entities_schema,
                "etl_function_code": etl_function_code,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }
