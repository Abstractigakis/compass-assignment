# Pagent OS FastAPI Application

A FastAPI application for Pagent OS.

## Installation

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

### Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /items/{item_id}` - Example endpoint with path parameters
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## Development

The application will be available at:

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
pagent-os/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .venv/              # Virtual environment
```
