# Sharp Agents Dashboard

A comprehensive web dashboard that displays sports betting odds from The Odds API alongside Kalshi prediction markets, providing a unified view of arbitrage opportunities across both platforms.

## 🎯 Features

### 📊 **Sportsbook Odds Comparison**
- **Real-time NFL odds** from major bookmakers (DraftKings, FanDuel, BetMGM, etc.)
- **Side-by-side comparison** of odds across different platforms
- **Automatic odds formatting** (American odds display)
- **Game scheduling** with commence times

### 🔍 **Arbitrage Detection**
- **Cross-bookmaker opportunities** where odds differ significantly
- **True arbitrage detection** (when total probability < 100%)
- **ROI calculations** and recommended bet amounts
- **Real-time updates** every 5 minutes

### 📈 **Kalshi Prediction Markets**
- **Binary prediction markets** with Yes/No outcomes
- **Bid/Ask spreads** for market making opportunities
- **Volume and open interest** metrics
- **Market ticker symbols** for easy identification

### 🚀 **Dashboard Features**
- **Responsive design** that works on all devices
- **Real-time status monitoring** of both APIs
- **Smart caching** to minimize API calls
- **Auto-refresh** every 5 minutes
- **Manual refresh** button for immediate updates
- **Error handling** with user-friendly messages

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API     │    │   Data Sources  │
│   (HTML/JS)     │◄──►│   (Python)      │◄──►│   The Odds API  │
│                 │    │                 │    │   Kalshi API    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Components**
1. **Flask Backend** (`dashboard/app.py`)
   - RESTful API endpoints
   - Data caching and optimization
   - Error handling and logging
   - Scraper integration

2. **Frontend Dashboard** (`dashboard/templates/dashboard.html`)
   - Bootstrap 5 responsive design
   - Real-time data updates
   - Interactive charts and tables
   - Status monitoring

3. **Data Integration**
   - The Odds API for sportsbook data
   - Kalshi API for prediction markets
   - Unified data formatting
   - Cross-platform analysis

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
# Activate your virtual environment
source venv/bin/activate

# Install dashboard requirements
pip install -r dashboard/requirements.txt
```

### 2. **Set Environment Variables**
```bash
# Set your API keys
export THEODDS_API_KEY='your_api_key_here'
export KALSHI_API_KEY='your_kalshi_key_here'  # Optional
```

### 3. **Launch Dashboard**
```bash
# Run the launcher script
python run_dashboard.py

# Or run directly
cd dashboard
python app.py
```

### 4. **Access Dashboard**
Open your browser and navigate to: **http://localhost:5000**

## 📱 Dashboard Layout

### **Top Row - Statistics**
- **NFL Games**: Total games available
- **Arbitrage Opportunities**: Found opportunities count
- **Kalshi Markets**: Available prediction markets
- **Last Update**: Timestamp of last data refresh

### **Main Content - Two Columns**
- **Left Column**: Sportsbook odds comparison
- **Right Column**: Arbitrage opportunities

### **Bottom Row - Full Width**
- **Kalshi Markets**: Complete prediction market table

### **Floating Elements**
- **Status Indicator**: System health in top-right
- **Refresh Button**: Manual refresh in bottom-right

## 🔌 API Endpoints

### **Sportsbook Data**
- `GET /api/sportsbook/odds` - NFL games with odds from all bookmakers
- `GET /api/sportsbook/arbitrage` - Arbitrage opportunities

### **Kalshi Data**
- `GET /api/kalshi/markets` - Prediction markets with pricing

### **System Management**
- `GET /api/status` - System health and API status
- `GET /api/combined/opportunities` - Cross-platform opportunities
- `POST /api/refresh` - Manually refresh cached data

## ⚙️ Configuration

### **Environment Variables**
```bash
THEODDS_API_KEY=your_api_key_here
KALSHI_API_KEY=your_kalshi_key_here
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_SECRET_KEY=your_secret_key_here
```

### **Cache Settings**
- **Default TTL**: 5 minutes (300 seconds)
- **Cache Type**: Simple in-memory cache
- **Auto-refresh**: Every 5 minutes
- **Manual refresh**: Available via button

### **Rate Limiting**
- **The Odds API**: 1 request per second minimum
- **Kalshi API**: Respects platform limits
- **Smart caching**: Prevents redundant calls

## 🎨 Customization

### **Styling**
The dashboard uses CSS custom properties for easy theming:
```css
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --danger-color: #e74c3c;
}
```

### **Data Limits**
Adjust the number of items displayed:
```python
# In app.py, modify these limits:
nfl_games[:20]          # Show first 20 NFL games
opportunities[:10]       # Show first 10 opportunities
markets[:20]             # Show first 20 Kalshi markets
```

### **Refresh Intervals**
Modify auto-refresh timing:
```javascript
// In dashboard.html
setInterval(loadDashboard, 300000); // 5 minutes
```

## 🔧 Troubleshooting

### **Common Issues**

#### 1. **Import Errors**
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**: Install requirements with `pip install -r dashboard/requirements.txt`

#### 2. **API Key Errors**
```
401 Client Error: Unauthorized
```
**Solution**: Verify your API keys are set correctly

#### 3. **Port Already in Use**
```
Address already in use
```
**Solution**: Change port in `app.py` or kill existing process

#### 4. **Caching Issues**
```
Cache not working
```
**Solution**: Check if Flask-Caching is installed and configured

### **Debug Mode**
Enable debug logging:
```python
# In app.py
logging.basicConfig(level=logging.DEBUG)
```

### **Manual Testing**
Test individual endpoints:
```bash
# Test sportsbook odds
curl http://localhost:5000/api/sportsbook/odds

# Test system status
curl http://localhost:5000/api/status
```

## 📊 Performance Optimization

### **Caching Strategy**
- **Sportsbook odds**: 5-minute cache (odds change frequently)
- **Arbitrage opportunities**: 5-minute cache (calculated from odds)
- **Kalshi markets**: 5-minute cache (market data updates)
- **System status**: Real-time (no cache)

### **API Efficiency**
- **Single calls**: Get all data in one request
- **Smart batching**: Process multiple items together
- **Error handling**: Graceful degradation on failures
- **Rate limiting**: Respect API limits

### **Frontend Optimization**
- **Lazy loading**: Load data as needed
- **Debounced updates**: Prevent excessive API calls
- **Responsive design**: Works on all screen sizes
- **Progressive enhancement**: Basic functionality without JavaScript

## 🚀 Production Deployment

### **WSGI Server**
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 dashboard.app:app
```

### **Environment Variables**
```bash
export FLASK_ENV=production
export FLASK_DEBUG=false
export FLASK_SECRET_KEY=your_secure_secret_key
```

### **Reverse Proxy**
```nginx
# Nginx configuration
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 🔮 Future Enhancements

### **Planned Features**
1. **Real-time WebSocket updates** for live odds
2. **Advanced charting** with Chart.js
3. **User authentication** and personalized dashboards
4. **Mobile app** using React Native
5. **Automated trading** integration

### **Performance Improvements**
1. **Redis caching** for distributed deployments
2. **Database persistence** for historical data
3. **Async processing** for better concurrency
4. **CDN integration** for static assets

## 📝 License

This dashboard is part of the Sharp Agents project, licensed under MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- **GitHub Issues**: [Project Issues](https://github.com/sharp-agents/sharp-agents/issues)
- **Documentation**: [Project Wiki](https://github.com/sharp-agents/sharp-agents/wiki)
- **Email**: support@sharp-agents.com

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Compatibility**: Python 3.8+, Flask 3.0+
