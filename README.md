# Quant Agent Platform

AI-driven stock screening platform with multi-agent architecture. Built with Python, Flask, Vue3, and LLM integration.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Frontend (Vue3 + Element Plus)          │
│   Dashboard  │  Stock Management  │  Strategy  │  AI Chat │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│                    Flask REST API (v2)                     │
│   /stocks  │  /strategies  │  /screening  │  /auth       │
└──────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌──────────────────┐ ┌────────────┐ ┌──────────────────┐
│  Strategy Engine  │ │  Data Layer │ │  Agent System     │
│  - Condition eval │ │  - TDX/mootdx│ │  - Coordinator    │
│  - Backtesting    │ │  - SQLite   │ │  - 4 Agents       │
└──────────────────┘ └────────────┘ └──────────────────┘
```

## Multi-Agent System

The core differentiator is the multi-agent AI architecture with a coordinator pattern:

| Agent | Role |
|-------|------|
| **StrategyGenerationAgent** | Converts natural language to structured screening strategy JSON |
| **ResultAnalysisAgent** | Analyzes screening results, generates investment insights |
| **AnomalyDetectionAgent** | Detects data anomalies and suspicious patterns |
| **StrategyOptimizerAgent** | Suggests parameter tuning and risk assessments |
| **AgentCoordinator** | Orchestrates agents into complete workflows |

### Workflows

**Full Screening Workflow:**
1. User describes strategy in natural language
2. `StrategyGenerationAgent` converts to structured conditions
3. `AnomalyDetectionAgent` flags data quality issues
4. `ResultAnalysisAgent` produces investment analysis

**Optimization Workflow:**
1. `StrategyOptimizerAgent` analyzes historical performance
2. Suggests parameter adjustments
3. Generates risk assessment for current market conditions

## Project Structure

```
quant_agent_platform/
├── quant_stock_screener/        # Main package (v2)
│   ├── config/                  # Settings, dataclasses
│   ├── core/                    # DataFetcher, StrategyEngine
│   ├── agents/                  # Multi-agent system
│   │   ├── base_agent.py        # Abstract base class
│   │   ├── strategy_agent.py    # NL → strategy
│   │   ├── analysis_agent.py    # Result analysis
│   │   ├── anomaly_agent.py     # Anomaly detection
│   │   ├── optimizer_agent.py   # Strategy optimization
│   │   └── coordinator.py       # Workflow orchestration
│   ├── ai/                      # LLM client wrappers
│   ├── database/                # SQLAlchemy models + CRUD
│   ├── api/                     # Flask route blueprints
│   ├── web/                     # App factory, auth, middleware
│   ├── utils/                   # Helpers
│   └── __main__.py              # CLI entry point
├── web-admin/                   # Vue3 + Element Plus frontend
├── data/                        # Stock lists, SQLite DB
├── deploy/                      # Docker, Nginx, Makefile
├── legacy/                      # Archived v1 code
└── tests/                       # Pytest suite
```

## Quick Start

### Backend

```bash
# Clone
git clone https://github.com/upessworgem/quant-agent-platform.git
cd quant-agent-platform

# Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start API server
python -m quant_stock_screener --serve

# Or run screening directly
python -m quant_stock_screener --screen --max-stocks 20
```

### Frontend

```bash
cd web-admin
npm install
npm run dev                     # Dev server at http://localhost:3000
npm run build                   # Production build
```

### AI Configuration

```bash
cp .env.example .env
# Edit .env with your API keys

# Supported providers
ANTHROPIC_API_KEY=sk-xxx        # Claude
OPENAI_API_KEY=sk-xxx           # GPT-4
```

Without API keys, the system works in mock mode (no AI features).

## API Reference

Base URL: `http://localhost:5000/api`
Interactive docs: `http://localhost:5000/docs`

### Stocks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /stocks | List stocks (paginated, searchable) |
| GET | /stocks/:code | Get stock detail |
| POST | /stocks | Create stock |
| PUT | /stocks/:code | Update stock |
| DELETE | /stocks/:code | Delete stock |
| POST | /stocks/bulk | Bulk import |
| GET | /stocks/:code/history | Historical data |

### Strategies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /strategies | List strategies |
| POST | /strategies | Create strategy |
| POST | /strategies/generate | **AI generates strategy from NL** |
| POST | /strategies/:id/duplicate | Duplicate strategy |
| PUT | /strategies/:id | Update strategy |
| DELETE | /strategies/:id | Soft delete |

### Screening

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /screening/execute | Execute screening |
| GET | /screening-results | List results |
| GET | /screening-results/:id | Result detail with items |
| POST | /screening-results/:id/analyze | **AI analyzes result** |

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Login (returns JWT) |
| GET | /auth/me | Current user info |
| POST | /auth/refresh | Refresh token |

## Tech Stack

**Backend:** Python 3.8+, Flask, SQLAlchemy 2.0, Pydantic 2.0
**Data:** mootdx (TDX broker API), SQLite, pandas, numpy
**AI:** Anthropic Claude, OpenAI GPT, multi-agent coordinator pattern
**Frontend:** Vue 3, Element Plus, Pinia, ECharts, Axios
**Deploy:** Docker multi-stage build, Nginx reverse proxy, Gunicorn

## CLI Usage

```bash
# Start server
python -m quant_stock_screener --serve --port 5000

# Run screening with default momentum strategy
python -m quant_stock_screener --screen

# AI-powered screening with natural language
python -m quant_stock_screener --screen --use-ai --strategy-desc "turnover > 15%, volume ratio > 1.5"

# Output as JSON
python -m quant_stock_screener --screen --output json --max-stocks 50
```

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# Or manually
docker build -t quant-agent-platform -f deploy/Dockerfile .
docker run -d -p 5000:5000 -e ANTHROPIC_API_KEY=xxx quant-agent-platform
```

## Testing

```bash
pytest tests/
pytest --cov=quant_stock_screener tests/
```

## License

MIT License
