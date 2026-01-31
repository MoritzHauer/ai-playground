# Copilot Instructions — AI Playground

## Project Overview
Personal experimentation workspace for AI/ML tooling, focused on:
- **Mistral AI integration** — OCR, LLM testing, API-based workflows
- **RAG (Retrieval-Augmented Generation)** — Document processing for scientific papers
- **Agentic workflows** — Custom agent definitions for research and architecture tasks

## Repository Structure
```
RAG/                    # OCR and document processing scripts
  MistralOCR3.py        # Main CLI tool for Mistral OCR
  input/                # Source documents (PDFs, images)
  output/               # Processed markdown + extracted images
.github/
  agents/               # Agent definitions (*.agent.md)
  prompts/              # Reusable prompt templates (*.prompt.md)
.vscode/mcp.json        # MCP server configurations (e.g., Mermaid)
```

## Development Setup

### Python Environment
```bash
source .venv/bin/activate
pip install -r RAG/requirements.txt
```

### Environment Variables
- `MISTRAL_API_KEY` — Required for all Mistral API calls; set in `.env` or pass via `--MistralApiKey`

### Running the OCR Tool
```bash
# Process single file or directory
python RAG/MistralOCR3.py <input> --outputDir output

# Process URL directly
python RAG/MistralOCR3.py "https://example.com/paper.pdf"
```
The tool shows cost estimates before processing (at $0.002/page) and prompts for confirmation.

## Code Patterns & Conventions

### Python Style
- Use `argparse` for CLI interfaces with sensible defaults
- Load secrets via `python-dotenv` from `.env` files
- Validate external dependencies (API keys) before main execution
- Cost estimation pattern: calculate and display before expensive operations

### Agent & Prompt Files
- Agents: `.github/agents/*.agent.md` — Include `description`, `tools`, and detailed behavioral specs
- Prompts: `.github/prompts/*.prompt.md` — Reusable task-specific instructions
- Templates: `.github/agents/templates/` — Document structure templates

### Mermaid Diagrams
When creating architecture diagrams:
1. **Always validate** using `mermaid-diagram-validator` before presenting
2. **Preview** with `mermaid-diagram-preview` after validation
3. Use MCP server configured in `.vscode/mcp.json`

## Key Integration Points

### Mistral API Usage
```python
from mistralai import Mistral
client = Mistral(api_key=api_key)

# OCR processing
ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={"type": "document_url", "document_url": url},
    include_image_base64=True
)
```

### Output Format
- OCR results → Markdown files with embedded image references
- Images extracted to same directory as output markdown
- Directory structure mirrors input document names

## Quality & Tooling Preferences
- Use **Ruff** for Python linting (mentioned in project notes)
- Consider **SonarQube** for code quality analysis
- Prefer explicit error handling over silent failures
