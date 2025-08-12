"""AI-powered analysis for prediction markets."""

import openai
from typing import List, Dict, Any
from database.models import Market, Outcome
from utils.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


class AIAnalyzer:
    """AI-powered analyzer for prediction market insights."""
    
    def __init__(self):
        self.config = get_config()
        self.client = openai.OpenAI(api_key=self.config.get("OPENAI_API_KEY"))
        self.logger = logger
    
    async def analyze_market_sentiment(self, market: Market, outcomes: List[Outcome]) -> Dict[str, Any]:
        """Analyze market sentiment using AI."""
        try:
            prompt = self._create_sentiment_prompt(market, outcomes)
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a prediction market analyst. Analyze the sentiment and provide insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            
            return {
                "sentiment": response.choices[0].message.content,
                "confidence": 0.8,  # Placeholder
                "analysis_type": "sentiment"
            }
            
        except Exception as e:
            self.logger.error(f"Error in AI sentiment analysis: {e}")
            return {"error": str(e)}
    
    async def predict_market_outcome(self, market: Market, historical_data: List[Dict]) -> Dict[str, Any]:
        """Predict market outcome using AI."""
        try:
            prompt = self._create_prediction_prompt(market, historical_data)
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a prediction market forecaster. Analyze the data and make predictions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            
            return {
                "prediction": response.choices[0].message.content,
                "confidence": 0.7,  # Placeholder
                "analysis_type": "prediction"
            }
            
        except Exception as e:
            self.logger.error(f"Error in AI prediction: {e}")
            return {"error": str(e)}
    
    def _create_sentiment_prompt(self, market: Market, outcomes: List[Outcome]) -> str:
        """Create a prompt for sentiment analysis."""
        return f"""
        Analyze the sentiment for this prediction market:
        
        Market: {market.title}
        Description: {market.description}
        Category: {market.category}
        
        Outcomes:
        {chr(10).join([f"- {outcome.title}: {outcome.probability}% (Volume: {outcome.volume})" for outcome in outcomes])}
        
        Provide insights on market sentiment, potential biases, and market dynamics.
        """
    
    def _create_prediction_prompt(self, market: Market, historical_data: List[Dict]) -> str:
        """Create a prompt for outcome prediction."""
        return f"""
        Based on the following data, predict the most likely outcome:
        
        Market: {market.title}
        Historical Data: {historical_data}
        
        Provide your prediction and reasoning.
        """
