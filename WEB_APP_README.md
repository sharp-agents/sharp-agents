# 🚀 Sharp Agents - Market Monitor Web App

A beautiful, responsive Flask web application for monitoring prediction markets in real-time.

## ✨ Features

### 🎯 **Dashboard Overview**
- **Real-time market monitoring** across multiple platforms
- **Summary cards** showing total markets, active markets, platforms, and last update time
- **Connection status indicator** (Online/Offline)
- **Auto-refresh** every 30 seconds

### 📊 **Market Data Display**
- **Comprehensive market table** with all key information:
  - Platform (Kalshi, Polymarket, etc.)
  - Market title and team information
  - Yes/No bid and ask prices
  - Spread calculations
  - Volume and liquidity data
  - Last updated timestamps

### 🔄 **Data Collection**
- **Manual refresh button** to trigger immediate data collection
- **Loading modal** with progress indication
- **Real-time status updates** via API calls
- **Error handling** with user-friendly messages

### 🎨 **Modern UI/UX**
- **Bootstrap 5** for responsive design
- **Bootstrap Icons** for visual appeal
- **Custom CSS styling** for professional appearance
- **Mobile-responsive** design
- **Interactive elements** with hover effects

## 🚀 Getting Started

### 1. **Prerequisites**
- Python 3.8+
- Virtual environment activated
- Database initialized with sample data
- Kalshi API credentials configured

### 2. **Installation**
```bash
# Ensure Flask is installed
pip install flask

# Make sure your virtual environment is activated
source venv/bin/activate
```

### 3. **Running the Application**
```bash
# Set Python path and run
PYTHONPATH=/path/to/Sharp-Agents python app.py
```

The app will start on **http://localhost:8000**

## 🌐 API Endpoints

### **Main Routes**
- **`/`** - Main dashboard page
- **`/api/markets`** - Get all markets as JSON
- **`/api/collect`** - Trigger data collection (POST)
- **`/api/status`** - Get system status

### **API Examples**

#### Get System Status
```bash
curl http://localhost:8000/api/status
```

#### Get All Markets
```bash
curl http://localhost:8000/api/markets
```

#### Trigger Data Collection
```bash
curl -X POST http://localhost:8000/api/collect \
  -H "Content-Type: application/json"
```

## 🎨 UI Components

### **Navigation Bar**
- Brand logo and title
- Connection status indicator
- Real-time online/offline status

### **Summary Cards**
- **Total Markets**: Count of all markets in database
- **Active Markets**: Markets with recent activity (last hour)
- **Platforms**: Number of different platforms
- **Last Updated**: Timestamp of most recent data

### **Markets Table**
- **Platform badges** with color coding
- **Market titles** with team information
- **Price data** in monospace font for readability
- **Volume indicators** with color coding (high/medium/low)
- **Responsive design** for mobile devices

### **Interactive Elements**
- **Refresh button** with loading states
- **Auto-refresh countdown** timer
- **Alert notifications** for user feedback
- **Loading modal** for data collection

## 🔧 Configuration

### **Environment Variables**
The app uses the same configuration as the main application:
- `DATABASE_URL` - Database connection string
- `KALSHI_API_URL` - Kalshi API endpoint
- `KALSHI_API_KEY` - Kalshi API key
- `KALSHI_API_SECRET` - Kalshi API secret

### **Port Configuration**
- **Default port**: 8000 (changed from 5000 to avoid macOS AirPlay conflicts)
- **Host**: 0.0.0.0 (accessible from any network interface)
- **Debug mode**: Enabled for development

## 📱 Responsive Design

### **Breakpoints**
- **Mobile**: < 768px (single column layout)
- **Tablet**: 768px - 992px (responsive grid)
- **Desktop**: > 992px (full layout with sidebars)

### **Mobile Features**
- Collapsible navigation
- Scrollable tables
- Touch-friendly buttons
- Optimized typography

## 🚨 Error Handling

### **Graceful Degradation**
- Database connection failures
- API authentication errors
- Network timeouts
- Invalid data responses

### **User Feedback**
- **Success alerts** for completed operations
- **Warning alerts** for non-critical issues
- **Error alerts** for critical failures
- **Auto-dismissing** notifications

## 🔄 Auto-Refresh System

### **Countdown Timer**
- **30-second intervals** for automatic data refresh
- **Visual countdown** display
- **Manual override** with refresh button
- **Reset on manual refresh**

### **Smart Updates**
- **Incremental updates** without page reload
- **Status monitoring** for system health
- **Connection checking** every 30 seconds
- **Background updates** for real-time data

## 🎯 Usage Scenarios

### **Market Monitoring**
1. Open the dashboard in your browser
2. View real-time market data
3. Monitor price movements and spreads
4. Track volume and liquidity changes

### **Data Collection**
1. Click "Refresh Now" button
2. Wait for collection to complete
3. View updated market information
4. Monitor collection statistics

### **API Integration**
1. Use API endpoints for external tools
2. Integrate with trading systems
3. Build custom dashboards
4. Automate data collection

## 🛠️ Development

### **File Structure**
```
app.py                 # Main Flask application
templates/
  index.html          # Main dashboard template
WEB_APP_README.md     # This documentation
```

### **Key Functions**
- `initialize_app()` - Setup database and configuration
- `index()` - Render main dashboard
- `api_markets()` - Return markets as JSON
- `api_collect()` - Trigger data collection
- `api_status()` - Return system status

### **Customization**
- **Styling**: Modify CSS in `templates/index.html`
- **Layout**: Update HTML structure
- **Functionality**: Extend JavaScript functions
- **API**: Add new endpoints as needed

## 🚀 Deployment

### **Production Considerations**
- Disable debug mode
- Use production WSGI server (Gunicorn, uWSGI)
- Set up reverse proxy (Nginx, Apache)
- Configure SSL certificates
- Set up monitoring and logging

### **Environment Setup**
```bash
# Production environment
export FLASK_ENV=production
export FLASK_DEBUG=0

# Run with production server
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 🎉 Success!

Your Sharp Agents Market Monitor web application is now running successfully! 

**Access it at**: http://localhost:8000

**Features working**:
- ✅ Beautiful Bootstrap 5 UI
- ✅ Real-time market data display
- ✅ Auto-refresh every 30 seconds
- ✅ Manual data collection trigger
- ✅ Responsive design for all devices
- ✅ Comprehensive API endpoints
- ✅ Error handling and user feedback

Enjoy monitoring your prediction markets! 🏈📊
