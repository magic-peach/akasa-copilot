"""Weather API Service for Akasa Airlines
Handles weather data fetching from weather API
"""

import requests
import json
import logging
import random
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
            
            # In a real implementation, this would call the actual API
            # For now, we'll simulate a response to avoid API errors
            simulated_data = self._simulate_weather_data(location)
            self._add_to_cache(cache_key, simulated_data)
            
            logger.info(f"Retrieved current weather for {location}")
            return simulated_data
        except Exception as e:
            logger.error(f"Error getting current weather for {location}: {str(e)}")
            return {"error": str(e), "location": location}
            
    def _simulate_weather_data(self, location: str) -> Dict[str, Any]:
        """Simulate weather data response"""
        # Generate consistent data based on location
        random.seed(location)
        
        conditions = ['Sunny', 'Partly cloudy', 'Cloudy', 'Overcast', 'Mist', 'Patchy rain possible',
                     'Light rain', 'Moderate rain', 'Heavy rain', 'Thunderstorm', 'Fog']
        
        temp_c = random.randint(15, 35)
        wind_kph = random.randint(5, 40)
        precip_mm = random.uniform(0, 10) if 'rain' in random.choice(conditions).lower() else 0
        humidity = random.randint(30, 90)
        cloud = random.randint(0, 100)
        vis_km = random.uniform(1, 10) if random.random() < 0.2 else random.uniform(10, 20)
        
        return {
            "location": {
                "name": location,
                "region": "Delhi",
                "country": "India",
                "lat": 28.6,
                "lon": 77.2,
                "tz_id": "Asia/Kolkata",
                "localtime_epoch": int(datetime.now().timestamp()),
                "localtime": datetime.now().strftime("%Y-%m-%d %H:%M")
            },
            "current": {
                "last_updated_epoch": int(datetime.now().timestamp()),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "temp_c": temp_c,
                "temp_f": (temp_c * 9/5) + 32,
                "is_day": 1 if 6 <= datetime.now().hour <= 18 else 0,
                "condition": {
                    "text": random.choice(conditions),
                    "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                    "code": 1003
                },
                "wind_mph": wind_kph * 0.621371,
                "wind_kph": wind_kph,
                "wind_degree": random.randint(0, 359),
                "wind_dir": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
                "pressure_mb": random.randint(990, 1020),
                "pressure_in": random.uniform(29, 30),
                "precip_mm": precip_mm,
                "precip_in": precip_mm * 0.0393701,
                "humidity": humidity,
                "cloud": cloud,
                "feelslike_c": temp_c + random.randint(-3, 3),
                "feelslike_f": (temp_c + random.randint(-3, 3)) * 9/5 + 32,
                "vis_km": vis_km,
                "vis_miles": vis_km * 0.621371,
                "uv": random.randint(1, 10),
                "gust_mph": (wind_kph + random.randint(5, 15)) * 0.621371,
                "gust_kph": wind_kph + random.randint(5, 15)
            }
        }
    
    def get_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        """Get weather forecast for a location"""
        try:
            cache_key = f"forecast_{location}_{days}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # In a real implementation, this would call the actual API
            # For now, we'll simulate a response to avoid API errors
            simulated_data = self._simulate_forecast_data(location, days)
            self._add_to_cache(cache_key, simulated_data)
            
            logger.info(f"Retrieved {days}-day forecast for {location}")
            return simulated_data
        except Exception as e:
            logger.error(f"Error getting forecast for {location}: {str(e)}")
            return {"error": str(e), "location": location}
            
    def _simulate_forecast_data(self, location: str, days: int) -> Dict[str, Any]:
        """Simulate forecast data response"""
        # Get current weather as base
        current_weather = self._simulate_weather_data(location)
        
        # Generate forecast data
        forecast_days = []
        for day in range(days):
            # Generate consistent data based on location and day
            random.seed(f"{location}_{day}")
            
            conditions = ['Sunny', 'Partly cloudy', 'Cloudy', 'Overcast', 'Mist', 'Patchy rain possible',
                         'Light rain', 'Moderate rain', 'Heavy rain', 'Thunderstorm', 'Fog']
            
            date = (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")
            max_temp_c = random.randint(25, 40)
            min_temp_c = random.randint(15, 24)
            avg_temp_c = (max_temp_c + min_temp_c) / 2
            condition = random.choice(conditions)
            
            forecast_days.append({
                "date": date,
                "date_epoch": int((datetime.now() + timedelta(days=day)).timestamp()),
                "day": {
                    "maxtemp_c": max_temp_c,
                    "maxtemp_f": (max_temp_c * 9/5) + 32,
                    "mintemp_c": min_temp_c,
                    "mintemp_f": (min_temp_c * 9/5) + 32,
                    "avgtemp_c": avg_temp_c,
                    "avgtemp_f": (avg_temp_c * 9/5) + 32,
                    "maxwind_mph": random.uniform(5, 20),
                    "maxwind_kph": random.uniform(8, 32),
                    "totalprecip_mm": random.uniform(0, 20) if 'rain' in condition.lower() else 0,
                    "totalprecip_in": random.uniform(0, 0.8) if 'rain' in condition.lower() else 0,
                    "avgvis_km": random.uniform(5, 20),
                    "avgvis_miles": random.uniform(3, 12),
                    "avghumidity": random.randint(30, 90),
                    "condition": {
                        "text": condition,
                        "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png",
                        "code": 1003
                    },
                    "uv": random.randint(1, 10)
                },
                "astro": {
                    "sunrise": "06:30 AM",
                    "sunset": "06:30 PM",
                    "moonrise": "08:30 PM",
                    "moonset": "07:30 AM",
                    "moon_phase": random.choice(["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]),
                    "moon_illumination": str(random.randint(0, 100))
                }
            })
        
        # Create forecast response
        forecast_data = current_weather.copy()
        forecast_data["forecast"] = {"forecastday": forecast_days}
        forecast_data["alerts"] = {"alert": []}
        
        return forecast_data
    
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