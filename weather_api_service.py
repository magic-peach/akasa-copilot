"""Weather API Service for Akasa Airlines
Handles weather data fetching from weather API
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WeatherApiService:
    """Service to interact with Weather API for real-time weather data"""
    
    def __init__(self):
        self.api_key = "94e73031524b4860a1f45607251409"  # API key provided
        self.base_url = "https://api.weatherapi.com/v1"
        self.cache = {}  # Simple cache to reduce API calls
        self.cache_expiry = 1800  # Cache expiry in seconds (30 minutes)
        self.cache_timestamps = {}  # Track when cache entries were created
    
    def get_current_weather(self, location: str) -> Dict[str, Any]:
        """Get current weather conditions for a location"""
        try:
            cache_key = f"current_weather_{location}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            endpoint = f"{self.base_url}/current.json"
            params = {
                "key": self.api_key,
                "q": location,
                "aqi": "yes"  # Include air quality data
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            self._add_to_cache(cache_key, data)
            
            logger.info(f"Retrieved current weather for {location}")
            return data
        except Exception as e:
            logger.error(f"Error getting current weather for {location}: {str(e)}")
            return {"error": str(e), "location": location}
    
    def get_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        """Get weather forecast for a location"""
        try:
            cache_key = f"forecast_{location}_{days}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            endpoint = f"{self.base_url}/forecast.json"
            params = {
                "key": self.api_key,
                "q": location,
                "days": days,
                "aqi": "yes",
                "alerts": "yes"  # Include weather alerts
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            self._add_to_cache(cache_key, data)
            
            logger.info(f"Retrieved {days}-day forecast for {location}")
            return data
        except Exception as e:
            logger.error(f"Error getting forecast for {location}: {str(e)}")
            return {"error": str(e), "location": location}
    
    def get_airport_weather(self, airport_code: str) -> Dict[str, Any]:
        """Get weather for a specific airport by IATA code"""
        # Convert airport code to location query
        return self.get_current_weather(airport_code)
    
    def get_weather_alerts(self, location: str) -> Dict[str, Any]:
        """Get weather alerts for a location"""
        try:
            # Weather alerts are included in the forecast endpoint
            forecast_data = self.get_forecast(location, days=1)
            
            if "error" in forecast_data:
                return forecast_data
            
            alerts = forecast_data.get("alerts", {})
            
            logger.info(f"Retrieved weather alerts for {location}")
            return {
                "location": location,
                "alerts": alerts,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting weather alerts for {location}: {str(e)}")
            return {"error": str(e), "location": location}
    
    def calculate_weather_risk(self, location: str) -> Dict[str, Any]:
        """Calculate weather risk score for a location"""
        try:
            weather_data = self.get_current_weather(location)
            
            if "error" in weather_data:
                return {"error": weather_data["error"], "location": location, "risk_score": 50}
            
            # Extract relevant weather data
            current = weather_data.get("current", {})
            condition = current.get("condition", {}).get("text", "").lower()
            wind_kph = current.get("wind_kph", 0)
            precip_mm = current.get("precip_mm", 0)
            visibility_km = current.get("vis_km", 10)
            humidity = current.get("humidity", 50)
            pressure = current.get("pressure_mb", 1013)
            is_day = current.get("is_day", 1)
            
            # Calculate base risk score (0-100, higher is riskier)
            risk_score = 0
            
            # Condition-based risk
            high_risk_conditions = ["thunderstorm", "heavy rain", "blizzard", "fog", "mist", "freezing", "ice", "snow"]
            medium_risk_conditions = ["rain", "drizzle", "showers", "cloudy", "overcast"]
            low_risk_conditions = ["clear", "sunny", "partly cloudy"]
            
            if any(term in condition for term in high_risk_conditions):
                risk_score += 40
            elif any(term in condition for term in medium_risk_conditions):
                risk_score += 20
            elif any(term in condition for term in low_risk_conditions):
                risk_score += 5
            else:
                risk_score += 15  # Default for unknown conditions
            
            # Wind-based risk
            if wind_kph > 50:  # Strong winds
                risk_score += 30
            elif wind_kph > 30:  # Moderate winds
                risk_score += 15
            elif wind_kph > 15:  # Light winds
                risk_score += 5
            
            # Precipitation-based risk
            if precip_mm > 10:  # Heavy precipitation
                risk_score += 25
            elif precip_mm > 5:  # Moderate precipitation
                risk_score += 15
            elif precip_mm > 0:  # Light precipitation
                risk_score += 5
            
            # Visibility-based risk
            if visibility_km < 1:  # Very poor visibility
                risk_score += 30
            elif visibility_km < 5:  # Poor visibility
                risk_score += 15
            elif visibility_km < 10:  # Moderate visibility
                risk_score += 5
            
            # Night-time adds risk
            if is_day == 0:  # Night time
                risk_score += 10
            
            # Normalize risk score to 0-100 range
            risk_score = min(max(risk_score, 0), 100)
            
            # Determine risk level
            risk_level = "Low"
            if risk_score > 70:
                risk_level = "High"
            elif risk_score > 40:
                risk_level = "Medium"
            
            return {
                "location": location,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "current_condition": condition,
                "wind_kph": wind_kph,
                "visibility_km": visibility_km,
                "precipitation_mm": precip_mm,
                "is_day": bool(is_day),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating weather risk for {location}: {str(e)}")
            return {"error": str(e), "location": location, "risk_score": 50}
    
    def get_multi_location_weather(self, locations: List[str]) -> Dict[str, Any]:
        """Get weather data for multiple locations"""
        results = {}
        for location in locations:
            results[location] = self.get_current_weather(location)
        
        return results
    
    def _add_to_cache(self, key: str, data: Any) -> None:
        """Add data to cache with timestamp"""
        self.cache[key] = data
        self.cache_timestamps[key] = datetime.utcnow().timestamp()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        if key in self.cache and key in self.cache_timestamps:
            timestamp = self.cache_timestamps[key]
            now = datetime.utcnow().timestamp()
            
            if now - timestamp < self.cache_expiry:
                return self.cache[key]
        
        return None

# Create a global instance for easy import
weather_api_service = WeatherApiService()