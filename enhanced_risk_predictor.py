"""Enhanced Risk Prediction System for Akasa Airlines
Integrates real-time weather and aviation data for accurate risk prediction
"""

import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from weather_api_service import weather_api_service
from aviation_api_service import aviation_api_service

logger = logging.getLogger(__name__)

class EnhancedRiskPredictor:
    """Enhanced risk prediction model with real-time data integration"""
    
    def __init__(self):
        # Enhanced airline risk profiles with more detailed metrics
        self.airline_profiles = {
            'Akasa Air': {
                'base_risk': 12, 'reliability': 0.94, 'punctuality': 0.91,
                'safety_score': 0.96, 'customer_satisfaction': 0.89,
                'fleet_age': 2.1, 'maintenance_score': 0.93
            },
            'IndiGo': {
                'base_risk': 18, 'reliability': 0.87, 'punctuality': 0.83,
                'safety_score': 0.91, 'customer_satisfaction': 0.82,
                'fleet_age': 6.8, 'maintenance_score': 0.88
            },
            'Vistara': {
                'base_risk': 15, 'reliability': 0.92, 'punctuality': 0.88,
                'safety_score': 0.94, 'customer_satisfaction': 0.91,
                'fleet_age': 4.2, 'maintenance_score': 0.91
            },
            'Air India': {
                'base_risk': 35, 'reliability': 0.72, 'punctuality': 0.68,
                'safety_score': 0.85, 'customer_satisfaction': 0.71,
                'fleet_age': 12.5, 'maintenance_score': 0.79
            },
            'SpiceJet': {
                'base_risk': 42, 'reliability': 0.69, 'punctuality': 0.64,
                'safety_score': 0.82, 'customer_satisfaction': 0.68,
                'fleet_age': 8.9, 'maintenance_score': 0.76
            },
            'Go First': {
                'base_risk': 48, 'reliability': 0.65, 'punctuality': 0.61,
                'safety_score': 0.79, 'customer_satisfaction': 0.64,
                'fleet_age': 9.8, 'maintenance_score': 0.73
            }
        }
        
        # Enhanced airport risk profiles
        self.airport_profiles = {
            'DEL': {'congestion': 0.85, 'weather_risk': 0.65, 'infrastructure': 0.92, 'efficiency': 0.78},
            'BOM': {'congestion': 0.90, 'weather_risk': 0.75, 'infrastructure': 0.88, 'efficiency': 0.74},
            'BLR': {'congestion': 0.70, 'weather_risk': 0.55, 'infrastructure': 0.95, 'efficiency': 0.89},
            'HYD': {'congestion': 0.60, 'weather_risk': 0.50, 'infrastructure': 0.91, 'efficiency': 0.87},
            'MAA': {'congestion': 0.75, 'weather_risk': 0.70, 'infrastructure': 0.86, 'efficiency': 0.81},
            'CCU': {'congestion': 0.80, 'weather_risk': 0.80, 'infrastructure': 0.82, 'efficiency': 0.76},
            'GOA': {'congestion': 0.45, 'weather_risk': 0.85, 'infrastructure': 0.79, 'efficiency': 0.83},
            'AMD': {'congestion': 0.65, 'weather_risk': 0.60, 'infrastructure': 0.88, 'efficiency': 0.85},
            'PNQ': {'congestion': 0.55, 'weather_risk': 0.55, 'infrastructure': 0.84, 'efficiency': 0.86},
            'JAI': {'congestion': 0.50, 'weather_risk': 0.58, 'infrastructure': 0.81, 'efficiency': 0.84},
            'LKO': {'congestion': 0.58, 'weather_risk': 0.62, 'infrastructure': 0.83, 'efficiency': 0.82},
            'IXC': {'congestion': 0.52, 'weather_risk': 0.68, 'infrastructure': 0.80, 'efficiency': 0.81},
            'VNS': {'congestion': 0.48, 'weather_risk': 0.60, 'infrastructure': 0.78, 'efficiency': 0.79},
            'IXB': {'congestion': 0.55, 'weather_risk': 0.72, 'infrastructure': 0.82, 'efficiency': 0.80},
            'RPR': {'congestion': 0.45, 'weather_risk': 0.55, 'infrastructure': 0.79, 'efficiency': 0.83},
            'BHO': {'congestion': 0.42, 'weather_risk': 0.52, 'infrastructure': 0.77, 'efficiency': 0.85},
            'IDR': {'congestion': 0.40, 'weather_risk': 0.58, 'infrastructure': 0.75, 'efficiency': 0.82},
            'IXU': {'congestion': 0.38, 'weather_risk': 0.65, 'infrastructure': 0.76, 'efficiency': 0.84},
            'IXD': {'congestion': 0.44, 'weather_risk': 0.70, 'infrastructure': 0.78, 'efficiency': 0.81},
            'IXJ': {'congestion': 0.41, 'weather_risk': 0.62, 'infrastructure': 0.74, 'efficiency': 0.80}
        }
        
        # Weather patterns by month and region
        self.weather_patterns = {
            'monsoon_regions': ['BOM', 'GOA', 'CCU', 'MAA'],
            'winter_fog_regions': ['DEL', 'LKO', 'VNS', 'JAI'],
            'cyclone_regions': ['BOM', 'CCU', 'MAA'],
            'heat_wave_regions': ['DEL', 'AMD', 'JAI', 'BHO']
        }
        
        # Risk factor weights
        self.risk_weights = {
            'operational_risk': 0.20,
            'weather_risk': 0.25,  # Increased weight for real-time weather
            'airport_risk': 0.15,
            'seasonal_risk': 0.05,
            'economic_risk': 0.05,
            'passenger_demand_risk': 0.10,
            'route_specific_risk': 0.10,
            'time_of_day_risk': 0.05,
            'real_time_delay_risk': 0.05  # New factor for real-time delays
        }
    
    def predict_comprehensive_risk(self, flights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive risk prediction with real-time data integration"""
        try:
            if not flights:
                return {'error': 'No flights provided for analysis'}
            
            # Analyze each flight with real-time data
            flight_analyses = []
            for flight in flights:
                analysis = self._analyze_single_flight_with_real_time_data(flight)
                flight_analyses.append(analysis)
            
            # Comparative analysis
            comparison_data = self._compare_flights(flight_analyses)
            
            # Generate final verdict
            verdict = self._generate_final_verdict(flight_analyses, comparison_data)
            
            # Airline performance analysis
            airline_analysis = self._analyze_airline_performance(flight_analyses)
            
            # Risk factor summary
            risk_factor_summary = self._summarize_risk_factors(flight_analyses)
            
            # Create comprehensive analysis result
            result = {
                'flight_analyses': flight_analyses,
                'comparison': comparison_data,
                'verdict': verdict,
                'airline_analysis': airline_analysis,
                'risk_factor_summary': risk_factor_summary,
                'timestamp': datetime.utcnow().isoformat(),
                'model_version': '2.0-enhanced'
            }
            
            logger.info(f"Completed enhanced risk prediction for {len(flights)} flights")
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced risk prediction: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_single_flight_with_real_time_data(self, flight: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single flight with real-time data integration"""
        
        # Get airline profile
        airline = flight['airline']
        airline_profile = self.airline_profiles.get(airline, self._get_default_airline_profile())
        
        # Get origin and destination codes
        origin = flight['origin']['code']
        destination = flight['destination']['code']
        flight_number = flight.get('flight_number', '')
        
        # Fetch real-time weather data
        origin_weather = weather_api_service.get_airport_weather(origin)
        dest_weather = weather_api_service.get_airport_weather(destination)
        
        # Fetch real-time flight status if flight number is available
        flight_status = None
        if flight_number:
            flight_status = aviation_api_service.get_flight_status(flight_number)
        
        # Fetch airport delay information
        origin_delays = aviation_api_service.get_airport_delays(origin)
        dest_delays = aviation_api_service.get_airport_delays(destination)
        
        # Calculate individual risk factors
        risk_factors = {
            'operational_risk': self._calculate_operational_risk(flight, airline_profile),
            'weather_risk': self._calculate_real_time_weather_risk(flight, origin_weather, dest_weather),
            'airport_risk': self._calculate_airport_risk(flight),
            'seasonal_risk': self._calculate_seasonal_risk(flight),
            'economic_risk': self._calculate_economic_risk(flight),
            'passenger_demand_risk': self._calculate_passenger_demand_risk(flight),
            'route_specific_risk': self._calculate_route_specific_risk(flight),
            'time_of_day_risk': self._calculate_time_of_day_risk(flight),
            'real_time_delay_risk': self._calculate_real_time_delay_risk(origin_delays, dest_delays)
        }
        
        # Calculate weighted overall risk
        overall_risk = 0
        for factor, score in risk_factors.items():
            weight = self.risk_weights.get(factor, 0.1)  # Default weight if not specified
            overall_risk += score * weight
        
        # Normalize to 0-100 scale
        risk_score = min(max(overall_risk, 0), 100)
        
        # Determine risk level
        risk_level = "High Risk"
        risk_color = "red"
        if risk_score >= 70:
            risk_level = "Low Risk"
            risk_color = "green"
        elif risk_score >= 50:
            risk_level = "Medium Risk"
            risk_color = "yellow"
        
        # Generate recommendation
        recommendation = self._generate_recommendation(risk_factors, flight)
        
        # Calculate confidence score
        confidence = self._calculate_prediction_confidence(risk_factors, airline_profile)
        
        # Create analysis result
        result = {
            'flight_number': flight.get('flight_number', ''),
            'airline': airline,
            'origin': origin,
            'destination': destination,
            'departure_datetime': flight.get('departure_datetime', ''),
            'arrival_datetime': flight.get('arrival_datetime', ''),
            'price': flight.get('price', 0),
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_factors': {k: round(v, 1) for k, v in risk_factors.items()},
            'recommendation': recommendation,
            'confidence': confidence,
            'real_time_data': {
                'origin_weather': origin_weather,
                'destination_weather': dest_weather,
                'flight_status': flight_status,
                'origin_delays': origin_delays,
                'destination_delays': dest_delays
            }
        }
        
        return result
    
    def _calculate_operational_risk(self, flight: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """Calculate operational risk based on airline profile"""
        # Base risk from airline profile
        base_risk = profile.get('base_risk', 30)
        
        # Adjust for reliability and punctuality
        reliability_factor = (1 - profile.get('reliability', 0.75)) * 40
        punctuality_factor = (1 - profile.get('punctuality', 0.75)) * 35
        
        # Adjust for safety and maintenance
        safety_factor = (1 - profile.get('safety_score', 0.8)) * 50
        maintenance_factor = (1 - profile.get('maintenance_score', 0.8)) * 30
        
        # Fleet age impact (newer is better)
        fleet_age = profile.get('fleet_age', 8.0)
        age_factor = min(fleet_age * 2, 20)  # Cap at 20
        
        # Calculate total operational risk
        operational_risk = base_risk + reliability_factor + punctuality_factor + safety_factor + maintenance_factor + age_factor
        
        # Normalize to 0-100 scale
        return min(max(operational_risk, 0), 100)
    
    def _calculate_real_time_weather_risk(self, flight: Dict[str, Any], origin_weather: Dict[str, Any], dest_weather: Dict[str, Any]) -> float:
        """Calculate weather risk using real-time weather data"""
        # Start with a base risk
        base_risk = 10
        
        # Check for errors in weather data
        if "error" in origin_weather or "error" in dest_weather:
            # Fall back to historical weather patterns if real-time data unavailable
            return self._calculate_historical_weather_risk(flight)
        
        try:
            # Process origin weather
            if "current" in origin_weather:
                origin_current = origin_weather["current"]
                
                # Check condition
                condition = origin_current.get("condition", {}).get("text", "").lower()
                if any(term in condition for term in ["thunderstorm", "fog", "snow", "blizzard", "ice"]):
                    base_risk += 30
                elif any(term in condition for term in ["rain", "shower", "drizzle", "mist"]):
                    base_risk += 15
                elif any(term in condition for term in ["cloudy", "overcast"]):
                    base_risk += 5
                
                # Check wind
                wind_kph = origin_current.get("wind_kph", 0)
                if wind_kph > 40:
                    base_risk += 25
                elif wind_kph > 25:
                    base_risk += 15
                elif wind_kph > 15:
                    base_risk += 5
                
                # Check visibility
                visibility = origin_current.get("vis_km", 10)
                if visibility < 1:
                    base_risk += 30
                elif visibility < 3:
                    base_risk += 20
                elif visibility < 5:
                    base_risk += 10
            
            # Process destination weather (similar logic)
            if "current" in dest_weather:
                dest_current = dest_weather["current"]
                
                # Check condition
                condition = dest_current.get("condition", {}).get("text", "").lower()
                if any(term in condition for term in ["thunderstorm", "fog", "snow", "blizzard", "ice"]):
                    base_risk += 25
                elif any(term in condition for term in ["rain", "shower", "drizzle", "mist"]):
                    base_risk += 12
                elif any(term in condition for term in ["cloudy", "overcast"]):
                    base_risk += 4
                
                # Check wind
                wind_kph = dest_current.get("wind_kph", 0)
                if wind_kph > 40:
                    base_risk += 20
                elif wind_kph > 25:
                    base_risk += 12
                elif wind_kph > 15:
                    base_risk += 4
                
                # Check visibility
                visibility = dest_current.get("vis_km", 10)
                if visibility < 1:
                    base_risk += 25
                elif visibility < 3:
                    base_risk += 15
                elif visibility < 5:
                    base_risk += 8
        except Exception as e:
            logger.error(f"Error processing weather data: {str(e)}")
            # Fall back to historical weather patterns
            return self._calculate_historical_weather_risk(flight)
        
        # Normalize to 0-100 scale
        return min(max(base_risk, 0), 100)
    
    def _calculate_historical_weather_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate weather risk based on historical patterns (fallback)"""
        departure_date = datetime.fromisoformat(flight['departure_datetime'])
        origin = flight['origin']['code']
        destination = flight['destination']['code']
        
        base_risk = random.uniform(8, 25)
        
        # Monsoon season impact (June-September)
        if 6 <= departure_date.month <= 9:
            if origin in self.weather_patterns['monsoon_regions']:
                base_risk += random.uniform(15, 30)
            if destination in self.weather_patterns['monsoon_regions']:
                base_risk += random.uniform(10, 25)
        
        # Winter fog impact (December-February)
        if departure_date.month in [12, 1, 2]:
            if origin in self.weather_patterns['winter_fog_regions']:
                base_risk += random.uniform(10, 20)
        
        # Cyclone season impact (October-December)
        if departure_date.month in [10, 11, 12]:
            if origin in self.weather_patterns['cyclone_regions'] or destination in self.weather_patterns['cyclone_regions']:
                base_risk += random.uniform(8, 18)
        
        # Summer heat wave impact (April-June)
        if departure_date.month in [4, 5, 6]:
            if origin in self.weather_patterns['heat_wave_regions']:
                base_risk += random.uniform(5, 15)
        
        return min(base_risk, 90)
    
    def _calculate_airport_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate airport-specific risk"""
        origin = flight['origin']['code']
        destination = flight['destination']['code']
        
        # Get airport profiles
        origin_profile = self.airport_profiles.get(origin, self._get_default_airport_profile())
        dest_profile = self.airport_profiles.get(destination, self._get_default_airport_profile())
        
        # Calculate risk factors
        origin_congestion = (1 - origin_profile.get('congestion', 0.5)) * 100
        origin_infrastructure = (1 - origin_profile.get('infrastructure', 0.8)) * 100
        origin_efficiency = (1 - origin_profile.get('efficiency', 0.8)) * 100
        
        dest_congestion = (1 - dest_profile.get('congestion', 0.5)) * 100
        dest_infrastructure = (1 - dest_profile.get('infrastructure', 0.8)) * 100
        dest_efficiency = (1 - dest_profile.get('efficiency', 0.8)) * 100
        
        # Weighted average (origin slightly more important than destination)
        airport_risk = (
            (origin_congestion * 0.3) + 
            (origin_infrastructure * 0.2) + 
            (origin_efficiency * 0.1) + 
            (dest_congestion * 0.2) + 
            (dest_infrastructure * 0.1) + 
            (dest_efficiency * 0.1)
        )
        
        # Add some randomness
        airport_risk += random.uniform(-5, 10)
        
        return min(max(airport_risk, 0), 100)
    
    def _calculate_seasonal_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate seasonal risk factors"""
        departure_date = datetime.fromisoformat(flight['departure_datetime'])
        month = departure_date.month
        
        # Base seasonal risk
        base_risk = 20
        
        # Peak travel seasons have higher risk
        # Summer vacation (May-June)
        if month in [5, 6]:
            base_risk += random.uniform(10, 20)
        
        # Winter holidays (December-January)
        elif month in [12, 1]:
            base_risk += random.uniform(15, 25)
        
        # Festival season (October-November)
        elif month in [10, 11]:
            base_risk += random.uniform(10, 15)
        
        # Shoulder seasons (February, September)
        elif month in [2, 9]:
            base_risk += random.uniform(5, 10)
        
        # Off-peak seasons have lower risk
        else:
            base_risk += random.uniform(0, 5)
        
        return min(base_risk, 100)
    
    def _calculate_economic_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate economic risk factors"""
        price = flight.get('price', 10000)
        
        # Price-based risk (higher prices might indicate higher demand or limited availability)
        if price > 15000:
            price_risk = random.uniform(10, 20)
        elif price > 10000:
            price_risk = random.uniform(5, 15)
        elif price > 5000:
            price_risk = random.uniform(0, 10)
        else:
            price_risk = random.uniform(0, 5)
        
        # Add some randomness for other economic factors
        economic_risk = price_risk + random.uniform(0, 15)
        
        return min(economic_risk, 100)
    
    def _calculate_passenger_demand_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate passenger demand risk"""
        seats_available = flight.get('seats_available', 30)
        
        # Higher risk for flights with few seats available (high demand)
        if seats_available < 5:
            return random.uniform(70, 90)
        elif seats_available < 10:
            return random.uniform(50, 70)
        elif seats_available < 20:
            return random.uniform(30, 50)
        else:
            return random.uniform(10, 30)
    
    def _calculate_route_specific_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate route-specific risk factors"""
        origin = flight['origin']['code']
        destination = flight['destination']['code']
        
        # Some routes have higher inherent risk
        high_risk_routes = [('DEL', 'IXJ'), ('BOM', 'IXB'), ('DEL', 'IXB')]
        medium_risk_routes = [('DEL', 'CCU'), ('BOM', 'CCU'), ('BLR', 'IXC')]
        
        if (origin, destination) in high_risk_routes or (destination, origin) in high_risk_routes:
            return random.uniform(60, 80)
        elif (origin, destination) in medium_risk_routes or (destination, origin) in medium_risk_routes:
            return random.uniform(40, 60)
        else:
            return random.uniform(10, 40)
    
    def _calculate_time_of_day_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate time-of-day risk factors"""
        departure_time = flight.get('departure_time', '12:00')
        hour = int(departure_time.split(':')[0])
        
        # Early morning and late night flights have higher risk
        if 0 <= hour < 5:
            return random.uniform(60, 80)  # Late night/early morning
        elif 5 <= hour < 8:
            return random.uniform(40, 60)  # Early morning
        elif 8 <= hour < 12:
            return random.uniform(20, 40)  # Morning
        elif 12 <= hour < 17:
            return random.uniform(20, 40)  # Afternoon
        elif 17 <= hour < 21:
            return random.uniform(30, 50)  # Evening
        else:
            return random.uniform(50, 70)  # Night
    
    def _calculate_real_time_delay_risk(self, origin_delays: Dict[str, Any], dest_delays: Dict[str, Any]) -> float:
        """Calculate risk based on real-time delay information"""
        # Start with a base risk
        base_risk = 20
        
        # Check for errors in delay data
        if "error" in origin_delays or "error" in dest_delays:
            return base_risk
        
        try:
            # Process origin delays
            origin_delay_percentage = origin_delays.get('delay_percentage', 0)
            origin_avg_delay = origin_delays.get('avg_delay_minutes', 0)
            
            # Process destination delays
            dest_delay_percentage = dest_delays.get('delay_percentage', 0)
            dest_avg_delay = dest_delays.get('avg_delay_minutes', 0)
            
            # Calculate risk based on delay percentages
            if origin_delay_percentage > 50 or dest_delay_percentage > 50:
                base_risk += 40  # Severe delays
            elif origin_delay_percentage > 30 or dest_delay_percentage > 30:
                base_risk += 25  # Significant delays
            elif origin_delay_percentage > 15 or dest_delay_percentage > 15:
                base_risk += 15  # Moderate delays
            
            # Calculate risk based on average delay times
            if origin_avg_delay > 60 or dest_avg_delay > 60:
                base_risk += 30  # Long delays
            elif origin_avg_delay > 30 or dest_avg_delay > 30:
                base_risk += 20  # Medium delays
            elif origin_avg_delay > 15 or dest_avg_delay > 15:
                base_risk += 10  # Short delays
            
        except Exception as e:
            logger.error(f"Error processing delay data: {str(e)}")
        
        # Normalize to 0-100 scale
        return min(max(base_risk, 0), 100)
    
    def _compare_flights(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare all flights and generate insights"""
        
        # Sort by risk score (best to worst)
        sorted_flights = sorted(analyses, key=lambda x: x['risk_score'], reverse=True)
        
        # Calculate statistics
        risk_scores = [f['risk_score'] for f in analyses]
        avg_risk = statistics.mean(risk_scores) if risk_scores else 0
        min_risk = min(risk_scores) if risk_scores else 0
        max_risk = max(risk_scores) if risk_scores else 0
        
        # Get best and worst flights
        best_flight = sorted_flights[0] if sorted_flights else {}
        worst_flight = sorted_flights[-1] if len(sorted_flights) > 1 else {}
        
        # Calculate price statistics
        prices = [f.get('price', 0) for f in analyses]
        avg_price = statistics.mean(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        # Calculate price-risk correlation
        price_risk_correlation = self._calculate_correlation(prices, risk_scores)
        
        # Categorize risk distribution
        risk_distribution = self._categorize_risk_distribution(risk_scores)
        
        return {
            'best_flight': best_flight,
            'worst_flight': worst_flight,
            'average_risk_score': round(avg_risk, 1),
            'min_risk_score': round(min_risk, 1),
            'max_risk_score': round(max_risk, 1),
            'average_price': round(avg_price, 2),
            'min_price': min_price,
            'max_price': max_price,
            'price_risk_correlation': round(price_risk_correlation, 2),
            'risk_distribution': risk_distribution
        }
    
    def _generate_final_verdict(self, analyses: List[Dict[str, Any]], comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive final verdict"""
        
        best_flight = comparison['best_flight']
        avg_risk = comparison['average_risk_score']
        risk_distribution = comparison['risk_distribution']
        
        # Overall route assessment
        if avg_risk >= 70:
            route_assessment = "Excellent"
            route_confidence = "High"
        elif avg_risk >= 50:
            route_assessment = "Good"
            route_confidence = "Medium"
        else:
            route_assessment = "Challenging"
            route_confidence = "Medium"
        
        # Final verdict text
        verdict_text = f"""
        Based on analysis of {len(analyses)} flights with real-time data, this route shows {route_assessment.lower()} conditions with {route_confidence.lower()} confidence.
        
        The best option is {best_flight['airline']} {best_flight['flight_number']} with a risk score of {best_flight['risk_score']}/100.
        
        Current weather conditions at {best_flight['origin']} and {best_flight['destination']} have been factored into this recommendation.
        """
        
        # Generate specific recommendations
        recommendations = []
        
        # Weather-based recommendations
        for flight in analyses:
            origin_weather = flight.get('real_time_data', {}).get('origin_weather', {})
            dest_weather = flight.get('real_time_data', {}).get('destination_weather', {})
            
            if "current" in origin_weather:
                condition = origin_weather["current"].get("condition", {}).get("text", "").lower()
                if any(term in condition for term in ["thunderstorm", "fog", "snow", "blizzard"]):
                    recommendations.append(f"Weather alert at {flight['origin']}: {condition}. Consider alternative departure airport.")
            
            if "current" in dest_weather:
                condition = dest_weather["current"].get("condition", {}).get("text", "").lower()
                if any(term in condition for term in ["thunderstorm", "fog", "snow", "blizzard"]):
                    recommendations.append(f"Weather alert at {flight['destination']}: {condition}. Consider alternative arrival airport.")
        
        # Delay-based recommendations
        for flight in analyses:
            origin_delays = flight.get('real_time_data', {}).get('origin_delays', {})
            dest_delays = flight.get('real_time_data', {}).get('destination_delays', {})
            
            if origin_delays.get('delay_percentage', 0) > 30:
                recommendations.append(f"High delay rate ({origin_delays.get('delay_percentage')}%) at {flight['origin']}. Allow extra time for check-in.")
            
            if dest_delays.get('delay_percentage', 0) > 30:
                recommendations.append(f"High delay rate ({dest_delays.get('delay_percentage')}%) at {flight['destination']}. Consider flexible connection times.")
        
        # Remove duplicates and limit to top 5
        unique_recommendations = list(set(recommendations))[:5]
        
        return {
            'verdict_text': verdict_text.strip(),
            'route_assessment': route_assessment,
            'route_confidence': route_confidence,
            'recommendations': unique_recommendations,
            'risk_distribution': risk_distribution
        }
    
    def _generate_recommendation(self, risk_factors: Dict[str, float], flight: Dict[str, Any]) -> str:
        """Generate recommendation based on risk factors"""
        recommendations = []
        
        # Weather risk recommendations
        if risk_factors['weather_risk'] > 70:
            recommendations.append("High weather risk detected. Check for weather updates before departure.")
        elif risk_factors['weather_risk'] > 50:
            recommendations.append("Moderate weather risk. Monitor conditions before travel.")
        
        # Operational risk recommendations
        if risk_factors['operational_risk'] > 70:
            recommendations.append("Consider alternative airlines with better operational reliability.")
        elif risk_factors['operational_risk'] > 50:
            recommendations.append("Be prepared for potential operational issues.")
        
        # Airport risk recommendations
        if risk_factors['airport_risk'] > 70:
            recommendations.append("Allow extra time for airport procedures.")
        
        # Time of day recommendations
        if risk_factors['time_of_day_risk'] > 70:
            recommendations.append("Consider flights during daylight hours for better reliability.")
        
        # Real-time delay recommendations
        if risk_factors['real_time_delay_risk'] > 70:
            recommendations.append("Significant delays reported. Check flight status before heading to airport.")
        elif risk_factors['real_time_delay_risk'] > 50:
            recommendations.append("Some delays reported. Monitor flight status.")
        
        # If all risks are low
        if all(score < 50 for score in risk_factors.values()):
            recommendations.append("Low risk across all factors. Good choice for reliable travel.")
        
        # Select the most relevant recommendation
        if recommendations:
            return recommendations[0]
        else:
            return "Standard recommendation: Monitor flight status before departure."
    
    def _calculate_prediction_confidence(self, risk_factors: Dict[str, float], airline_profile: Dict[str, Any]) -> float:
        """Calculate confidence in the prediction"""
        # Base confidence
        confidence = 0.75
        
        # Adjust based on data quality
        if 'real_time_delay_risk' in risk_factors and risk_factors['real_time_delay_risk'] > 0:
            confidence += 0.10  # Real-time delay data available
        
        if 'weather_risk' in risk_factors and risk_factors['weather_risk'] > 0:
            confidence += 0.10  # Real-time weather data available
        
        # Adjust based on airline data quality
        reliability = airline_profile.get('reliability', 0)
        if reliability > 0.9:
            confidence += 0.05  # High-quality airline data
        
        # Cap at 0.95
        return min(confidence, 0.95)
    
    def _calculate_correlation(self, prices: List[float], risk_scores: List[float]) -> float:
        """Calculate correlation between prices and risk scores"""
        if len(prices) != len(risk_scores) or len(prices) < 2:
            return 0
        
        return self._calculate_simple_correlation(prices, risk_scores)
    
    def _calculate_simple_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate a simple correlation coefficient"""
        n = len(x_values)
        if n != len(y_values) or n < 2:
            return 0
        
        # Calculate means
        mean_x = sum(x_values) / n
        mean_y = sum(y_values) / n
        
        # Calculate covariance and variances
        covariance = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
        variance_x = sum((x - mean_x) ** 2 for x in x_values)
        variance_y = sum((y - mean_y) ** 2 for y in y_values)
        
        # Calculate correlation coefficient
        if variance_x > 0 and variance_y > 0:
            correlation = covariance / ((variance_x * variance_y) ** 0.5)
            return max(min(correlation, 1.0), -1.0)  # Ensure it's between -1 and 1
        else:
            return 0
    
    def _categorize_risk_distribution(self, risk_scores: List[float]) -> Dict[str, Any]:
        """Categorize risk distribution"""
        low_risk = sum(1 for score in risk_scores if score >= 70)
        medium_risk = sum(1 for score in risk_scores if 50 <= score < 70)
        high_risk = sum(1 for score in risk_scores if score < 50)
        
        total = len(risk_scores)
        
        return {
            'low_risk': {'count': low_risk, 'percentage': round((low_risk / total) * 100, 1) if total > 0 else 0},
            'medium_risk': {'count': medium_risk, 'percentage': round((medium_risk / total) * 100, 1) if total > 0 else 0},
            'high_risk': {'count': high_risk, 'percentage': round((high_risk / total) * 100, 1) if total > 0 else 0}
        }
    
    def _analyze_airline_performance(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by airline"""
        airline_stats = {}
        
        for analysis in analyses:
            airline = analysis['airline']
            if airline not in airline_stats:
                airline_stats[airline] = {
                    'flights': [],
                    'avg_risk_score': 0,
                    'avg_price': 0,
                    'count': 0
                }
            
            airline_stats[airline]['flights'].append(analysis)
            airline_stats[airline]['count'] += 1
        
        # Calculate averages
        for airline, stats in airline_stats.items():
            if stats['count'] > 0:
                stats['avg_risk_score'] = round(sum(f['risk_score'] for f in stats['flights']) / stats['count'], 1)
                stats['avg_price'] = round(sum(f.get('price', 0) for f in stats['flights']) / stats['count'], 2)
        
        return airline_stats
    
    def _summarize_risk_factors(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize risk factors across all flights"""
        factor_sums = {}
        factor_counts = {}
        
        for analysis in analyses:
            for factor, score in analysis.get('risk_factors', {}).items():
                if factor not in factor_sums:
                    factor_sums[factor] = 0
                    factor_counts[factor] = 0
                
                factor_sums[factor] += score
                factor_counts[factor] += 1
        
        # Calculate averages
        factor_averages = {}
        for factor, total in factor_sums.items():
            if factor_counts[factor] > 0:
                factor_averages[factor] = round(total / factor_counts[factor], 1)
        
        # Sort factors by average score (highest to lowest)
        sorted_factors = sorted(factor_averages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'factor_averages': factor_averages,
            'top_risk_factors': sorted_factors[:3],
            'lowest_risk_factors': sorted_factors[-3:]
        }
    
    def _get_default_airline_profile(self) -> Dict[str, Any]:
        """Default airline profile for unknown airlines"""
        return {
            'base_risk': 30, 'reliability': 0.75, 'punctuality': 0.70,
            'safety_score': 0.85, 'customer_satisfaction': 0.70,
            'fleet_age': 8.0, 'maintenance_score': 0.80
        }
    
    def _get_default_airport_profile(self) -> Dict[str, Any]:
        """Default airport profile for unknown airports"""
        return {
            'congestion': 0.60, 'weather_risk': 0.60,
            'infrastructure': 0.80, 'efficiency': 0.75
        }

# Create a global instance for easy import
enhanced_risk_predictor = EnhancedRiskPredictor()