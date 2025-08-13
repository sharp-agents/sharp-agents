# The Odds API Integration

This document describes the integration of The Odds API into the Sharp Agents project for sportsbook data collection and arbitrage detection.

## Overview

The Odds API provides real-time sports betting odds from major bookmakers including:
- DraftKings
- FanDuel
- BetMGM
- Caesars
- BetOnline.ag
- LowVig.ag
- And many more

## API Key

**Current API Key**: `2d3f0080085a382f269ffc8fd5d83cbd`

**Free Tier Limits**: 500 requests/month
**API Base URL**: https://api.the-odds-api.com/v4

## Components Created

### 1. Configuration Updates (`utils/config.py`)
- Added `THEODDS_API_URL` configuration
- Added `THEODDS_API_KEY` configuration
- Added getter methods for The Odds API

### 2. TheOddsClient (`scrapers/theodds.py`)
Main client class for interacting with The Odds API:

```python
from scrapers.theodds import TheOddsClient

client = TheOddsClient(api_key="your_api_key")

# Get available sports
sports = client.get_sports()

# Get NFL games with odds
nfl_games = client.get_nfl_games()

# Get odds for specific game
odds = client.get_odds(game_id)

# Get historical odds
historical = client.get_historical_odds(sport, event_id, date)
```

### 3. TheOddsScraper (`scrapers/theodds.py`)
Scraper class inheriting from BaseScraper for data collection:

```python
from scrapers.theodds import TheOddsScraper

scraper = TheOddsScraper()

# Fetch NFL markets
markets = scraper.fetch_markets()

# Fetch odds for specific market
odds = scraper.fetch_prices(market_id)

# Find arbitrage opportunities
opportunities = scraper.get_arbitrage_opportunities(min_threshold=0.02)
```

### 4. Utility Functions
- `normalize_odds_to_probability()`: Converts American odds to implied probability
- `get_arbitrage_opportunities()`: Finds arbitrage opportunities across bookmakers
- `_calculate_optimal_bets()`: Calculates optimal bet amounts for arbitrage

## Key Features

### American Odds Conversion
The scraper automatically converts American odds to implied probabilities:

- **Positive odds** (e.g., +150): `probability = 100 / (odds + 100)`
- **Negative odds** (e.g., -110): `probability = |odds| / (|odds| + 100)`

### Arbitrage Detection
Automatically identifies arbitrage opportunities when:
- Total probability across all outcomes < 100%
- Configurable minimum threshold (default: 2%)

### Multi-Bookmaker Support
Aggregates odds from multiple bookmakers to find:
- Best odds for each team/outcome
- Price differences across platforms
- Optimal betting strategies

## API Endpoints Used

### 1. Sports List
```
GET /v4/sports?apiKey={apiKey}
```
Returns all available sports (doesn't count against quota).

### 2. NFL Odds
```
GET /v4/sports/americanfootball_nfl/odds?apiKey={apiKey}&regions=us&markets=h2h&oddsFormat=american
```
Returns upcoming NFL games with moneyline odds from all bookmakers.

### 3. Historical Odds
```
GET /v4/historical/sports/{sport}/events/{eventId}/odds?apiKey={apiKey}&date={date}
```
Returns historical odds data for analysis.

## Usage Examples

### Basic Usage
```python
from scrapers.theodds import TheOddsClient

# Initialize client
client = TheOddsClient()

# Get NFL games
games = client.get_nfl_games()

for game in games:
    print(f"{game['away_team']} @ {game['home_team']}")
    print(f"Time: {game['commence_time']}")
    
    # Get odds from each bookmaker
    for bookmaker in game['bookmakers']:
        print(f"  {bookmaker['title']}:")
        for market in bookmaker['markets']:
            if market['key'] == 'h2h':  # Moneyline
                for outcome in market['outcomes']:
                    print(f"    {outcome['name']}: {outcome['price']:+d}")
```

### Arbitrage Detection
```python
from scrapers.theodds import TheOddsScraper

scraper = TheOddsScraper()

# Find arbitrage opportunities
opportunities = scraper.get_arbitrage_opportunities(min_threshold=0.01)

for opp in opportunities:
    print(f"Arbitrage Opportunity: {opp['title']}")
    print(f"Arbitrage: {opp['arbitrage_percentage']:.2f}%")
    print(f"Total Probability: {opp['total_probability']:.1%}")
    
    # Show recommended bets
    bets = opp['recommended_bets']
    print(f"Bet per team: ${bets['bet_amount_per_team']:.2f}")
    print(f"Expected profit: ${bets['expected_profit']:.2f}")
    print(f"ROI: {bets['roi_percentage']:.2f}%")
```

## Rate Limiting & Quota Management

### Free Tier Limits
- **500 requests/month**
- Rate limiting: 429 status code when exceeded
- Quota resets monthly

### Monitoring Usage
The API returns usage information in response headers:
- `x-requests-remaining`: Credits remaining
- `x-requests-used`: Credits used this month
- `x-requests-last`: Cost of last request

### Best Practices
1. **Cache data** when possible to reduce API calls
2. **Batch requests** to minimize individual calls
3. **Monitor usage** to stay within limits
4. **Use historical endpoints** for analysis (more cost-effective)

## Error Handling

The integration includes comprehensive error handling for:
- API rate limits (429 errors)
- Authentication failures (401 errors)
- Network timeouts
- Invalid data responses
- Quota exhaustion

## Testing

### Test Scripts
1. **`test_theodds_api.py`**: Basic functionality test
2. **`setup_theodds.py`**: Interactive setup and connection test
3. **`example_theodds_arbitrage.py`**: Arbitrage detection examples

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Test basic functionality
python test_theodds_api.py

# Run setup wizard
python setup_theodds.py

# Test arbitrage detection
python example_theodds_arbitrage.py
```

## Integration with Sharp Agents

### Database Integration
The scraper integrates with the existing database system:
- Normalizes data to standard format
- Stores market and odds information
- Supports arbitrage analysis

### Arbitrage Analysis
Works with the existing arbitrage detection system:
- Identifies opportunities across platforms
- Calculates optimal bet amounts
- Provides ROI analysis

### Web API
Can be integrated into the Flask web API:
- Endpoint for current odds
- Arbitrage opportunity listings
- Historical data analysis

## Future Enhancements

### Planned Features
1. **Additional Markets**: Spread, totals, player props
2. **Real-time Updates**: WebSocket support for live odds
3. **Advanced Analytics**: Line movement tracking
4. **Multi-sport Support**: NBA, MLB, NHL, etc.
5. **Betting Simulation**: Paper trading and backtesting

### Performance Optimizations
1. **Caching Layer**: Redis integration for odds caching
2. **Async Processing**: Concurrent API requests
3. **Data Compression**: Efficient storage of historical data
4. **Smart Scheduling**: Intelligent API call timing

## Troubleshooting

### Common Issues

#### 1. API Key Errors
```
401 Client Error: Unauthorized
```
**Solution**: Verify API key is correct and not expired

#### 2. Rate Limiting
```
429 Too Many Requests
```
**Solution**: Wait before making more requests, check quota usage

#### 3. No Data Returned
**Possible Causes**:
- Off-season for requested sport
- API key has no access to requested data
- Network connectivity issues

#### 4. Import Errors
```
ModuleNotFoundError: No module named 'requests'
```
**Solution**: Install dependencies with `pip install -r requirements.txt`

### Debug Mode
Enable debug logging to see detailed API interactions:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support & Resources

### Documentation
- [The Odds API V4 Documentation](https://the-odds-api.com/liveapi/guides/v4/#overview)
- [API Reference](https://the-odds-api.com/liveapi/guides/v4/#endpoints)
- [Rate Limiting Guide](https://the-odds-api.com/liveapi/guides/v4/#rate-limiting)

### Community
- [GitHub Issues](https://github.com/sharp-agents/sharp-agents/issues)
- [Discord Community](link-to-discord)
- [Email Support](mailto:support@sharp-agents.com)

### Upgrading Plans
When you need more than 500 requests/month:
1. Visit [The Odds API Plans](https://the-odds-api.com/liveapi/guides/v4/#pricing)
2. Choose appropriate plan for your needs
3. Update API key in configuration
4. Adjust rate limiting in code if needed

## License & Attribution

The Odds API integration is part of the Sharp Agents project, licensed under MIT License.

**Data Source**: [The Odds API](https://the-odds-api.com)
**API Version**: v4
**Last Updated**: January 2025
