## Objective

Build a small-scale pipeline that:

1. **Scrapes product data** from a public e-commerce site (e.g., Staples or Costco).
2. **Uses a Large Language Model (LLM)** to generate a brief summary or insight for each product (e.g., comparison, feature highlight, or marketing blurb).
3. **Outputs the results** in a structured format or via a basic API.

---

## Requirements

### 1. Technology Stack

- **Language:** Python
- **Web Scraping:**
  - Playwright (recommended for dynamic websites)
  - BeautifulSoup + Requests (acceptable for static sites)
- **LLM Processing:**
  - OpenAI API
  - Hugging Face Transformers
  - Or a local LLM (via Ollama, LLaMA.cpp, etc.)

### 2. Scraping Target

- Choose a publicly accessible product listing page from a major retailer:
  - Staples Canada/US
  - Costco
  - Best Buy
  - Walmart
- Scrape **at least 10 products** from a single category (e.g., laptops, office chairs, TVs).
- For each product, extract:
  - Product title
  - Price
  - Description/specs
  - Product URL
  - _(Optional)_ Product rating or image URL

### 3. LLM Summarization Task

- Use the LLM to generate one of the following for each product:
  - A concise 2–3 sentence product summary (e.g., for a marketing site)
  - A short comparison across a few products _(optional advanced version)_
  - A tagline or bullet-point highlights based on features/specs

### 4. Output Format

- **Either:**
  - A JSON file with entries like:
    ```json
    {
      "title": "...",
      "price": "...",
      "description": "...",
      "summary": "...",
      "url": "..."
    }
    ```
  - Or a basic REST API (using Flask or FastAPI) with an endpoint like `GET /products`

### 5. Documentation

- Include a PowerPoint presentation describing:
  - What you built and why
  - Your scraping target and rationale
  - Any assumptions or limitations
  - How to install and run your code
  - Example output

---

## Bonus Points

- Handling infinite scroll or client-side rendering with Playwright
- Rotating user agents or handling basic anti-bot measures
- Using LLM prompts creatively for better summarization
- Deploying the API to GCP

---

## Time Estimate

**4–6 hours**, depending on your experience
