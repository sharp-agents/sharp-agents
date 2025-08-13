# Sharp Agents

A prediction market analysis and arbitrage detection system that scrapes data from various prediction market platforms and uses AI to analyze opportunities.

## Features

- **Data Scraping**: Collects data from Polymarket, Kalshi, The Odds API, and other prediction markets
- **Arbitrage Detection**: Identifies price differences across platforms and sportsbooks
- **AI Analysis**: Uses OpenAI to analyze market sentiment and predict outcomes
- **REST API**: Flask-based API for data access and analysis
- **Database**: SQLAlchemy models for storing market data and opportunities
- **Sports Betting**: Integrates with The Odds API for sportsbook odds comparison

## Project Structure

```
scrapers/          # Data collection modules
├── __init__.py
├── base.py        # Base scraper class
├── polymarket.py  # Polymarket scraper
├── kalshi.py      # Kalshi scraper
└── theodds.py     # The Odds API scraper

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
   # Set environment variables or create .env file
   export THEODDS_API_KEY='your_api_key_here'
   export OPENAI_API_KEY='your_openai_api_key_here'
   # Or run the setup script:
   python setup_theodds.py
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

## Configuration

Set the following environment variables:

- `THEODDS_API_KEY`: Your The Odds API key for sportsbook data
- `OPENAI_API_KEY`: Your OpenAI API key for AI analysis
- `DATABASE_URL`: Database connection string
- `POLYMARKET_API_KEY`: Polymarket API key (if available)
- `KALSHI_API_KEY`: Kalshi API key (if available)

### The Odds API Setup

The Odds API provides access to sportsbook odds from major bookmakers including:
- DraftKings
- FanDuel  
- BetMGM
- Caesars
- And many more

**Free Tier**: 500 requests/month
**Paid Plans**: Available for higher request limits

To get started:
1. Visit [The Odds API](https://the-odds-api.com/liveapi/guides/v4/#overview)
2. Sign up for a free API key
3. Run `python setup_theodds.py` to configure
4. Test with `python test_theodds_api.py`

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
- **The Odds API** for sportsbook data

## Testing

Test individual components:
```bash
# Test The Odds API
python test_theodds_api.py

# Test database
python test_database.py

# Test Kalshi API
python test_kalshi_api.py
```

## License

MIT License
