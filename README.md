# Sharp Agents

A prediction market analysis and arbitrage detection system that scrapes data from various prediction market platforms and uses AI to analyze opportunities.

## Features

- **Data Scraping**: Collects data from Polymarket, Kalshi, and other prediction markets
- **Arbitrage Detection**: Identifies price differences across platforms
- **AI Analysis**: Uses OpenAI to analyze market sentiment and predict outcomes
- **REST API**: Flask-based API for data access and analysis
- **Database**: SQLAlchemy models for storing market data and opportunities

## Project Structure

```
scrapers/          # Data collection modules
├── __init__.py
├── base.py        # Base scraper class
├── polymarket.py  # Polymarket scraper
└── kalshi.py      # Kalshi scraper

database/          # Data persistence
├── __init__.py
├── models.py      # SQLAlchemy models
└── queries.py     # Database query functions

analysis/          # Data analysis
├── __init__.py
├── arbitrage.py   # Arbitrage detection
└── ai_analyzer.py # AI-powered analysis

api/               # Web API
├── __init__.py
└── routes.py      # Flask routes

utils/             # Utilities
├── __init__.py
├── logger.py      # Logging configuration
└── config.py      # Configuration management
```

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sharp-agents/sharp-agents.git
   cd sharp-agents
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

## Configuration

Copy `.env.example` to `.env` and configure:

- `OPENAI_API_KEY`: Your OpenAI API key for AI analysis
- `DATABASE_URL`: Database connection string
- `POLYMARKET_API_KEY`: Polymarket API key (if available)
- `KALSHI_API_KEY`: Kalshi API key (if available)

## API Endpoints

- `GET /` - Health check
- `GET /api/markets` - List all markets
- `GET /api/markets/<id>` - Get specific market
- `GET /api/arbitrage` - Get arbitrage opportunities
- `POST /api/analysis/sentiment` - Analyze market sentiment

## Development

The project uses:
- **SQLAlchemy** for database operations
- **Flask** for the web API
- **Loguru** for structured logging
- **OpenAI** for AI-powered analysis
- **APScheduler** for scheduled tasks

## License

MIT License
