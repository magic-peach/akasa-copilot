
"""
Disruption Prediction System for Akasa Airlines
Combines weather data, historical disruptions, and real-time flight data
to predict disruption risk using ML and rule-based engines
"""

import requests
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from database import db
import logging

logger = logging.getLogger(__name__)

class DisruptionPredictor:
    """GenAI agent for predicting flight disruptions using multiple data sources"""
    
    def __init__(self):
        self.weather_api_key = None  # Mock implementation
        self.risk_threshold_low = 0.3
        self.risk_threshold_medium = 0.6
        self.risk_threshold_high = 0.8
        
        # ML model weights (simplified rule-based approach)
        self.weights = {
            'weather_score': 0.35,
            'historical_score': 0.25,
            'real_time_score': 0.25,
            'route_score': 0.15
        }
    
    def predict_disruption(self, flight_id: str) -> Dict[str, Any]:
        """
        Main prediction function that combines multiple data sources
        
        Args:
            flight_id: Flight identifier
            
        Returns:
            Disruption risk prediction with detailed breakdown
        """
        try:
            logger.info(f"Starting disruption prediction for flight {flight_id}")
            
            # Step 1: Get flight metadata
            flight_metadata = self._get_flight_metadata(flight_id)
            if not flight_metadata:
                return self._create_error_prediction(flight_id, "Flight metadata not found")
            
            # Step 2: Get weather data for origin and destination
            weather_data = self._get_weather_data(
                flight_metadata.get('origin'),
                flight_metadata.get('destination')
            )
            
            # Step 3: Analyze historical disruptions
            historical_data = self._analyze_historical_disruptions(
                flight_metadata.get('flight_number'),
                flight_metadata.get('origin'),
                flight_metadata.get('destination')
            )
            
            # Step 4: Get real-time flight delays
            real_time_data = self._get_real_time_delays(
                flight_metadata.get('origin'),
                flight_metadata.get('destination')
            )
            
            # Step 5: Calculate individual risk scores
            weather_score = self._calculate_weather_risk(weather_data)
            historical_score = self._calculate_historical_risk(historical_data)
            real_time_score = self._calculate_real_time_risk(real_time_data)
            route_score = self._calculate_route_risk(
                flight_metadata.get('origin'),
                flight_metadata.get('destination')
            )
            
            # Step 6: Combine scores using ML weights
            disruption_risk = self._calculate_combined_risk(
                weather_score, historical_score, real_time_score, route_score
            )
            
            # Step 7: Generate risk assessment
            risk_assessment = self._generate_risk_assessment(disruption_risk)
            
            # Step 8: Create comprehensive prediction result
            prediction_result = {
                'flight_id': flight_id,
                'flight_number': flight_metadata.get('flight_number'),
                'origin': flight_metadata.get('origin'),
                'destination': flight_metadata.get('destination'),
                'disruption_risk': round(disruption_risk, 3),
                'risk_level': risk_assessment['level'],
                'risk_factors': {
                    'weather_score': round(weather_score, 3),
                    'historical_score': round(historical_score, 3),
                    'real_time_score': round(real_time_score, 3),
                    'route_score': round(route_score, 3)
                },
                'contributing_factors': risk_assessment['factors'],
                'recommendations': risk_assessment['recommendations'],
                'confidence': self._calculate_prediction_confidence(
                    weather_data, historical_data, real_time_data
                ),
                'timestamp': datetime.utcnow().isoformat(),
                'model_version': '1.0'
            }
            
            logger.info(f"Disruption prediction completed for {flight_id}: risk={disruption_risk:.3f}")
            return prediction_result
            
        except Exception as e:
            logger.error(f"Error predicting disruption for {flight_id}: {str(e)}")
            return self._create_error_prediction(flight_id, str(e))
    
    def _get_flight_metadata(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Get flight metadata from database"""
        try:
            supabase = db.get_client()
            
            # Try by flight_number first (most common case)
            result = supabase.table('flights').select('*').eq('flight_number', flight_id).execute()
            
            if not result.data:
                # Try by UUID if flight_id looks like a UUID
                if len(flight_id) == 36 and '-' in flight_id:
                    result = supabase.table('flights').select('*').eq('id', flight_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting flight metadata: {str(e)}")
            return None
    
    def _get_weather_data(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Get weather data for origin and destination airports (mock implementation)
        In production, this would call OpenWeatherMap or similar API
        """
        try:
            # Mock weather data generation
            weather_conditions = ['clear', 'cloudy', 'rain', 'thunderstorm', 'fog', 'snow']
            wind_speeds = [5, 10, 15, 20, 25, 30, 35, 40]
            visibility_km = [1, 2, 5, 10, 15, 20]
            
            origin_weather = {
                'airport': origin,
                'condition': random.choice(weather_conditions),
                'wind_speed_kmh': random.choice(wind_speeds),
                'visibility_km': random.choice(visibility_km),
                'temperature_c': random.randint(-5, 45),
                'humidity_percent': random.randint(30, 95),
                'pressure_hpa': random.randint(980, 1030)
            }
            
            destination_weather = {
                'airport': destination,
                'condition': random.choice(weather_conditions),
                'wind_speed_kmh': random.choice(wind_speeds),
                'visibility_km': random.choice(visibility_km),
                'temperature_c': random.randint(-5, 45),
                'humidity_percent': random.randint(30, 95),
                'pressure_hpa': random.randint(980, 1030)
            }
            
            return {
                'origin': origin_weather,
                'destination': destination_weather,
                'source': 'mock_weather_api',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting weather data: {str(e)}")
            return {'origin': {}, 'destination': {}, 'error': str(e)}
    
    def _analyze_historical_disruptions(self, flight_number: str, origin: str, destination: str) -> Dict[str, Any]:
        """Analyze historical disruption patterns"""
        try:
            supabase = db.get_client()
            
            # Get historical alerts for this flight number
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            result = supabase.table('alerts').select('*').eq('flight_number', flight_number).gte('created_at', thirty_days_ago).execute()
            
            alerts = result.data or []
            
            # Analyze patterns
            total_alerts = len(alerts)
            delay_alerts = len([a for a in alerts if a.get('alert_type') == 'DELAY'])
            cancellation_alerts = len([a for a in alerts if a.get('alert_type') == 'CANCELLATION'])
            
            # Calculate disruption frequency
            disruption_rate = total_alerts / 30 if total_alerts > 0 else 0
            
            return {
                'total_alerts_30d': total_alerts,
                'delay_alerts': delay_alerts,
                'cancellation_alerts': cancellation_alerts,
                'disruption_rate_per_day': round(disruption_rate, 3),
                'analysis_period_days': 30
            }
            
        except Exception as e:
            logger.error(f"Error analyzing historical disruptions: {str(e)}")
            return {'total_alerts_30d': 0, 'error': str(e)}
    
    def _get_real_time_delays(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get real-time delay information for the route"""
        try:
            supabase = db.get_client()
            
            # Get current flight states for this route
            result = supabase.table('flight_state').select('*').eq('origin', origin).eq('destination', destination).execute()
            
            flight_states = result.data or []
            
            # Analyze current delays
            delayed_flights = [f for f in flight_states if f.get('status') == 'DELAYED']
            total_flights = len(flight_states)
            
            if total_flights > 0:
                delay_percentage = (len(delayed_flights) / total_flights) * 100
            else:
                delay_percentage = 0
            
            return {
                'total_flights_on_route': total_flights,
                'delayed_flights': len(delayed_flights),
                'delay_percentage': round(delay_percentage, 2),
                'route': f"{origin}-{destination}"
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time delays: {str(e)}")
            return {'total_flights_on_route': 0, 'error': str(e)}
    
    def _calculate_weather_risk(self, weather_data: Dict[str, Any]) -> float:
        """Calculate weather-based disruption risk"""
        try:
            origin_weather = weather_data.get('origin', {})
            dest_weather = weather_data.get('destination', {})
            
            risk_score = 0.0
            
            # Check origin weather conditions
            origin_condition = origin_weather.get('condition', 'clear')
            if origin_condition in ['thunderstorm', 'fog']:
                risk_score += 0.4
            elif origin_condition in ['rain', 'snow']:
                risk_score += 0.2
            elif origin_condition == 'cloudy':
                risk_score += 0.1
            
            # Check destination weather conditions
            dest_condition = dest_weather.get('condition', 'clear')
            if dest_condition in ['thunderstorm', 'fog']:
                risk_score += 0.4
            elif dest_condition in ['rain', 'snow']:
                risk_score += 0.2
            elif dest_condition == 'cloudy':
                risk_score += 0.1
            
            # Check wind speeds
            origin_wind = origin_weather.get('wind_speed_kmh', 0)
            dest_wind = dest_weather.get('wind_speed_kmh', 0)
            
            if origin_wind > 35 or dest_wind > 35:
                risk_score += 0.3
            elif origin_wind > 25 or dest_wind > 25:
                risk_score += 0.15
            
            # Check visibility
            origin_visibility = origin_weather.get('visibility_km', 20)
            dest_visibility = dest_weather.get('visibility_km', 20)
            
            if origin_visibility < 2 or dest_visibility < 2:
                risk_score += 0.3
            elif origin_visibility < 5 or dest_visibility < 5:
                risk_score += 0.15
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating weather risk: {str(e)}")
            return 0.5  # Default moderate risk
    
    def _calculate_historical_risk(self, historical_data: Dict[str, Any]) -> float:
        """Calculate risk based on historical disruption patterns"""
        try:
            disruption_rate = historical_data.get('disruption_rate_per_day', 0)
            total_alerts = historical_data.get('total_alerts_30d', 0)
            cancellation_alerts = historical_data.get('cancellation_alerts', 0)
            
            # Base risk from disruption frequency
            risk_score = min(disruption_rate * 0.1, 0.6)  # Cap at 0.6
            
            # Add risk for cancellation history
            if cancellation_alerts > 0:
                risk_score += min(cancellation_alerts * 0.1, 0.3)
            
            # Add risk for high alert volume
            if total_alerts > 10:
                risk_score += 0.2
            elif total_alerts > 5:
                risk_score += 0.1
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating historical risk: {str(e)}")
            return 0.3  # Default low-moderate risk
    
    def _calculate_real_time_risk(self, real_time_data: Dict[str, Any]) -> float:
        """Calculate risk based on real-time delay patterns"""
        try:
            delay_percentage = real_time_data.get('delay_percentage', 0)
            total_flights = real_time_data.get('total_flights_on_route', 0)
            
            # Base risk from delay percentage
            risk_score = delay_percentage / 100
            
            # Adjust for sample size
            if total_flights < 3:
                risk_score *= 0.7  # Reduce confidence for small samples
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating real-time risk: {str(e)}")
            return 0.2  # Default low risk
    
    def _calculate_route_risk(self, origin: str, destination: str) -> float:
        """Calculate risk based on route characteristics"""
        try:
            # High-risk routes (based on typical weather patterns and congestion)
            high_risk_routes = ['DEL-GOA', 'BOM-GOA', 'DEL-BOM']
            medium_risk_routes = ['BOM-BLR', 'DEL-BLR', 'BLR-HYD']
            
            route = f"{origin}-{destination}"
            reverse_route = f"{destination}-{origin}"
            
            if route in high_risk_routes or reverse_route in high_risk_routes:
                return 0.6
            elif route in medium_risk_routes or reverse_route in medium_risk_routes:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Error calculating route risk: {str(e)}")
            return 0.3
    
    def _calculate_combined_risk(self, weather_score: float, historical_score: float,
                               real_time_score: float, route_score: float) -> float:
        """Combine individual risk scores using ML weights"""
        combined_risk = (
            weather_score * self.weights['weather_score'] +
            historical_score * self.weights['historical_score'] +
            real_time_score * self.weights['real_time_score'] +
            route_score * self.weights['route_score']
        )
        
        return min(combined_risk, 1.0)
    
    def _generate_risk_assessment(self, disruption_risk: float) -> Dict[str, Any]:
        """Generate human-readable risk assessment"""
        if disruption_risk < self.risk_threshold_low:
            level = 'LOW'
            factors = ['Favorable weather conditions', 'Low historical disruption rate']
            recommendations = ['Monitor weather updates', 'Standard operations']
        elif disruption_risk < self.risk_threshold_medium:
            level = 'MEDIUM'
            factors = ['Some weather concerns', 'Moderate disruption history']
            recommendations = ['Prepare contingency plans', 'Monitor closely', 'Consider passenger notifications']
        elif disruption_risk < self.risk_threshold_high:
            level = 'HIGH'
            factors = ['Adverse weather conditions', 'High disruption probability']
            recommendations = ['Activate contingency protocols', 'Prepare rebooking options', 'Proactive passenger communication']
        else:
            level = 'CRITICAL'
            factors = ['Severe weather conditions', 'Very high disruption risk']
            recommendations = ['Consider flight cancellation', 'Immediate passenger rebooking', 'Emergency protocols']
        
        return {
            'level': level,
            'factors': factors,
            'recommendations': recommendations
        }
    
    def _calculate_prediction_confidence(self, weather_data: Dict[str, Any],
                                       historical_data: Dict[str, Any],
                                       real_time_data: Dict[str, Any]) -> float:
        """Calculate confidence in the prediction"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on data availability
        if weather_data.get('origin') and weather_data.get('destination'):
            confidence += 0.2
        
        if historical_data.get('total_alerts_30d', 0) > 0:
            confidence += 0.15
        
        if real_time_data.get('total_flights_on_route', 0) > 0:
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _create_error_prediction(self, flight_id: str, error_message: str) -> Dict[str, Any]:
        """Create error response for failed predictions"""
        return {
            'flight_id': flight_id,
            'flight_number': 'Unknown',
            'origin': None,
            'destination': None,
            'disruption_risk': 0.0,
            'risk_level': 'UNKNOWN',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat(),
            'model_version': '1.0'
        }

# Global predictor instance
disruption_predictor = DisruptionPredictor()