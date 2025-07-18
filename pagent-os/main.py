from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, Response
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
import base64
import gzip
from typing import Optional, Dict, Any
from web_scrapper import WebScrapper
from etl_writer import ETLWriter
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Pagent OS API",
    description="A FastAPI application for Pagent OS",
    version="1.0.0",
)


class ScrapeRequest(BaseModel):
    url: str
    format: str = "json"  # Options: "json", "base64", "gzip", "raw"


class ScrapeMetadata(BaseModel):
    url: str
    method: str
    timestamp: str
    content_length: int
    status: str
    browser_type: str = None


class ScrapeResponse(BaseModel):
    html: str
    meta: ScrapeMetadata


class ScrapeResponseCompressed(BaseModel):
    html_base64: str
    meta: ScrapeMetadata


class ScrapeResponseGzip(BaseModel):
    html_gzip_base64: str
    meta: ScrapeMetadata


class LearnETLRequest(BaseModel):
    # Support both formats for backward compatibility
    html_gzip_base64: Optional[str] = None  # Original format
    html: Optional[str] = None  # New format from client
    html_compressed: Optional[bool] = False  # Whether html is compressed
    goal: Optional[str] = None  # Goal for extraction
    etl_function_code: Optional[str] = None  # ETL function code (for execute endpoint)


class LearnETLResponse(BaseModel):
    entities_schema: Optional[Dict[str, Any]] = None
    etl_function_code: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    status: str
    timestamp: str
    error: Optional[str] = None


class ExecuteETLRequest(BaseModel):
    etl_function_code: str
    html: Optional[str] = None
    html_gzip_base64: Optional[str] = None
    html_compressed: Optional[bool] = False


class ExecuteETLResponse(BaseModel):
    status: str
    extracted_data: Optional[Dict[str, Any]] = None
    timestamp: str
    error: Optional[str] = None


@app.post("/pages/get-html")
async def create_page_html(request: ScrapeRequest):
    """Scrape a web page and return the HTML content in various formats."""
    try:
        # Create WebScrapper instance (automatically fetches the page)
        scrapper = WebScrapper(request.url)

        if scrapper.html:
            print(
                f"Scraped {request.url} successfully, content length: {len(scrapper.html)}"
            )

            # Save to file for debugging
            with open("scraped_page.html", "w", encoding="utf-8") as f:
                f.write(scrapper.html)

            # Create metadata like the old Pagent
            metadata = ScrapeMetadata(
                url=request.url,
                method="playwright",
                timestamp=datetime.now().isoformat(),
                content_length=len(scrapper.html),
                status="success",
                browser_type="firefox",  # Default from WebScrapper
            )

            # Return different formats based on request
            if request.format == "raw":
                # Return as plain text to avoid JSON encoding issues
                # Add metadata as headers
                return PlainTextResponse(
                    content=scrapper.html,
                    media_type="text/html; charset=utf-8",
                    headers={
                        "X-URL": request.url,
                        "X-Content-Length": str(len(scrapper.html)),
                        "X-Timestamp": metadata.timestamp,
                        "X-Method": "playwright",
                        "X-Status": "success",
                    },
                )
            elif request.format == "base64":
                # Encode HTML as base64 to avoid unicode issues
                html_base64 = base64.b64encode(scrapper.html.encode("utf-8")).decode(
                    "ascii"
                )
                return ScrapeResponseCompressed(html_base64=html_base64, meta=metadata)
            elif request.format == "gzip":
                # Compress with gzip then base64 encode for maximum efficiency
                html_bytes = scrapper.html.encode("utf-8")
                compressed = gzip.compress(html_bytes)
                compressed_base64 = base64.b64encode(compressed).decode("ascii")
                return ScrapeResponseGzip(
                    html_gzip_base64=compressed_base64, meta=metadata
                )
            else:
                # Default JSON format with escaped content
                # Use repr() to properly escape the string
                safe_html = repr(scrapper.html)[1:-1]  # Remove quotes added by repr
                return ScrapeResponse(html=safe_html, meta=metadata)
        else:
            raise HTTPException(
                status_code=422, detail=f"Failed to fetch page: {request.url}"
            )
    except Exception as e:
        # Log the error for debugging
        print(f"Error scraping {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error while scraping: {str(e)}"
        )


@app.post("/pages/learn-etl", response_model=LearnETLResponse)
async def learn_etl(request: LearnETLRequest):
    """
    Analyze HTML content and generate ETL pipeline using Gemini AI.

    This endpoint:
    1. Analyzes the HTML to identify extractable entities
    2. Generates an entities.json schema
    3. Creates a Python ETL function
    4. Executes the ETL function and returns extracted data
    """
    try:
        # Initialize ETL Writer - this requires Google API key
        try:
            etl_writer = ETLWriter()
        except ValueError as e:
            if "Google API key is required" in str(e):
                raise HTTPException(
                    status_code=503,
                    detail="ETL service unavailable: Google API key not configured. Please set GEMINI_API_KEY environment variable.",
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"ETL service initialization failed: {str(e)}",
                )

        # Handle different input formats
        html_gzip_base64 = None

        if request.html_gzip_base64:
            # Original format - already compressed and base64 encoded
            html_gzip_base64 = request.html_gzip_base64
        elif request.html:
            # New format from client
            if request.html_compressed:
                # HTML is already compressed (gzip) and base64 encoded
                html_gzip_base64 = request.html
            else:
                # HTML is raw, need to compress it
                html_bytes = request.html.encode("utf-8")
                compressed = gzip.compress(html_bytes)
                html_gzip_base64 = base64.b64encode(compressed).decode("ascii")
        else:
            raise HTTPException(
                status_code=400,
                detail="Either html_gzip_base64 or html field is required",
            )

        # Process the HTML and generate ETL artifacts
        result = etl_writer.process_html(
            html_gzip_base64=html_gzip_base64, goal=request.goal
        )

        if result.get("status") == "error":
            raise HTTPException(
                status_code=500, detail=f"ETL generation failed: {result.get('error')}"
            )

        return LearnETLResponse(
            entities_schema=result.get("entities_schema"),
            etl_function_code=result.get("etl_function_code"),
            extracted_data=None,  # ETL execution is a separate step now
            status=result["status"],
            timestamp=result["timestamp"],
        )

    except Exception as e:
        print(f"Error in learn_etl endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during ETL learning: {str(e)}",
        )


@app.post("/pages/execute-etl", response_model=ExecuteETLResponse)
async def execute_etl(request: ExecuteETLRequest):
    """
    Execute the ETL function with the provided HTML content.
    """
    try:
        # Initialize ETL Writer
        etl_writer = ETLWriter()

        print(f"Executing ETL function with provided HTML content...")
        print(f"ETL Function Code length: {len(request.etl_function_code)} characters")

        # Handle different HTML input formats
        html_content = None

        if request.html_gzip_base64:
            # Original format - decompress it
            html_content = etl_writer.decompress_html(request.html_gzip_base64)
        elif request.html:
            if request.html_compressed:
                # HTML is compressed and base64 encoded
                html_content = etl_writer.decompress_html(request.html)
            else:
                # HTML is raw text
                html_content = request.html
        else:
            raise HTTPException(
                status_code=400,
                detail="Either html_gzip_base64 or html field is required",
            )

        print(f"HTML content length: {len(html_content)} characters")

        # Execute the ETL function
        extracted_data = etl_writer.execute_etl_function(
            html_content=html_content, etl_function_code=request.etl_function_code
        )

        return ExecuteETLResponse(
            status="success",
            extracted_data=extracted_data,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        print(f"Error in execute_etl endpoint: {str(e)}")
        return ExecuteETLResponse(
            status="error",
            extracted_data=None,
            timestamp=datetime.now().isoformat(),
            error=str(e),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8101)
