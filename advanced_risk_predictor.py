"""
Advanced Risk Prediction Model for Akasa Airlines
Core prediction engine with sophisticated risk analysis and flight comparison
"""

import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedRiskPredictor:
    """Advanced risk prediction model with machine learning-inspired algorithms"""
    
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
    
    def predict_comprehensive_risk(self, flights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive risk prediction for all flights to a destination
        Returns detailed analysis with final verdict
        """
        try:
            if not flights:
                return {'error': 'No flights provided for analysis'}
            
            # Analyze each flight
            flight_analyses = []
            for flight in flights:
                analysis = self._analyze_single_flight(flight)
                flight_analyses.append(analysis)
            
            # Comparative analysis
            comparison_data = self._compare_flights(flight_analyses)
            
            # Generate final verdict
            verdict = self._generate_final_verdict(flight_analyses, comparison_data)
            
            return {
                'success': True,
                'route': f"{flights[0]['origin']['code']} → {flights[0]['destination']['code']}",
                'total_flights_analyzed': len(flights),
                'flight_analyses': flight_analyses,
                'comparison_data': comparison_data,
                'final_verdict': verdict,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive risk prediction: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_single_flight(self, flight: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single flight with advanced risk modeling"""
        
        # Get airline profile
        airline = flight['airline']
        airline_profile = self.airline_profiles.get(airline, self._get_default_airline_profile())
        
        # Calculate individual risk factors
        risk_factors = {
            'operational_risk': self._calculate_advanced_operational_risk(flight, airline_profile),
            'weather_risk': self._calculate_advanced_weather_risk(flight),
            'airport_risk': self._calculate_advanced_airport_risk(flight),
            'seasonal_risk': self._calculate_advanced_seasonal_risk(flight),
            'economic_risk': self._calculate_advanced_economic_risk(flight),
            'passenger_demand_risk': self._calculate_passenger_demand_risk(flight),
            'route_specific_risk': self._calculate_route_specific_risk(flight),
            'time_of_day_risk': self._calculate_time_of_day_risk(flight)
        }
        
        # Calculate weighted overall risk
        weights = {
            'operational_risk': 0.25,
            'weather_risk': 0.20,
            'airport_risk': 0.15,
            'seasonal_risk': 0.12,
            'economic_risk': 0.10,
            'passenger_demand_risk': 0.08,
            'route_specific_risk': 0.06,
            'time_of_day_risk': 0.04
        }
        
        weighted_risk = sum(risk_factors[factor] * weights[factor] for factor in risk_factors)
        
        # Convert to 0-100 scale (higher = better)
        risk_score = max(0, min(100, 100 - weighted_risk))
        
        # Determine risk category
        if risk_score >= 70:
            risk_level = 'Low Risk'
            risk_color = 'green'
            recommendation = 'Highly recommended for travel'
        elif risk_score >= 40:
            risk_level = 'Medium Risk'
            risk_color = 'yellow'
            recommendation = 'Suitable with minor precautions'
        else:
            risk_level = 'High Risk'
            risk_color = 'red'
            recommendation = 'Consider alternative options'
        
        return {
            'flight_id': flight['id'],
            'flight_number': flight['flight_number'],
            'airline': airline,
            'price': flight['price'],
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_factors': risk_factors,
            'airline_profile': airline_profile,
            'recommendation': recommendation,
            'confidence': self._calculate_prediction_confidence(risk_factors, airline_profile)
        }
    
    def _calculate_advanced_operational_risk(self, flight: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """Advanced operational risk calculation"""
        base_risk = profile['base_risk']
        
        # Reliability factor (more impact)
        reliability_penalty = (1 - profile['reliability']) * 50
        
        # Punctuality factor
        punctuality_penalty = (1 - profile['punctuality']) * 40
        
        # Fleet age factor
        fleet_age_penalty = min(profile['fleet_age'] * 2, 20)
        
        # Maintenance score factor
        maintenance_penalty = (1 - profile['maintenance_score']) * 30
        
        # Time of day factor
        departure_hour = int(flight['departure_time'].split(':')[0])
        time_penalty = 0
        if departure_hour < 6 or departure_hour > 22:
            time_penalty = 15
        elif departure_hour < 8 or departure_hour > 20:
            time_penalty = 8
        
        total_risk = base_risk + reliability_penalty + punctuality_penalty + fleet_age_penalty + maintenance_penalty + time_penalty
        
        # Add controlled randomness for diversity
        total_risk += random.uniform(-10, 15)
        
        return min(max(total_risk, 5), 95)
    
    def _calculate_advanced_weather_risk(self, flight: Dict[str, Any]) -> float:
        """Advanced weather risk calculation"""
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
    
    def _calculate_advanced_airport_risk(self, flight: Dict[str, Any]) -> float:
        """Advanced airport risk calculation"""
        origin = flight['origin']['code']
        destination = flight['destination']['code']
        
        origin_profile = self.airport_profiles.get(origin, self._get_default_airport_profile())
        dest_profile = self.airport_profiles.get(destination, self._get_default_airport_profile())
        
        # Calculate origin risk
        origin_risk = (
            origin_profile['congestion'] * 30 +
            origin_profile['weather_risk'] * 20 +
            (1 - origin_profile['infrastructure']) * 25 +
            (1 - origin_profile['efficiency']) * 25
        )
        
        # Calculate destination risk
        dest_risk = (
    
    def _calculate_simple_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate simple correlation coefficient without numpy"""
        if len(x_values) < 2 or len(y_values) < 2:
            return 0.0
        
        try:
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x_values[i] * y_values[i] for i in range(n))
            sum_x2 = sum(x * x for x in x_values)
            sum_y2 = sum(y * y for y in y_values)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
            
            if denominator == 0:
                return 0.0
            
            return round(numerator / denominator, 3)
        except:
            return 0.0
            dest_profile['congestion'] * 25 +
            dest_profile['weather_risk'] * 15 +
            (1 - dest_profile['infrastructure']) * 20 +
            (1 - dest_profile['efficiency']) * 20
        )
        
        # Average with slight origin bias (departure delays more critical)
        total_risk = (origin_risk * 0.6 + dest_risk * 0.4)
        
        return min(total_risk, 85)
    
    def _calculate_advanced_seasonal_risk(self, flight: Dict[str, Any]) -> float:
        """Advanced seasonal risk calculation"""
        departure_date = datetime.fromisoformat(flight['departure_datetime'])
        
        base_risk = random.uniform(5, 15)
        
        # Festival seasons with specific dates
        high_demand_periods = [
            (10, 15, 11, 15),  # Diwali season
            (12, 20, 1, 5),    # Christmas/New Year
            (3, 15, 4, 15),    # Holi/Spring break
            (8, 10, 8, 20),    # Independence Day
            (1, 20, 1, 30)     # Republic Day
        ]
        
        for start_month, start_day, end_month, end_day in high_demand_periods:
            if self._is_date_in_period(departure_date, start_month, start_day, end_month, end_day):
                base_risk += random.uniform(15, 25)
                break
        
        # Weekend premium
        if departure_date.weekday() >= 5:  # Saturday, Sunday
            base_risk += random.uniform(8, 15)
        
        # Holiday premium
        if departure_date.weekday() == 4:  # Friday
            base_risk += random.uniform(5, 10)
        
        return min(base_risk, 80)
    
    def _calculate_advanced_economic_risk(self, flight: Dict[str, Any]) -> float:
        """Advanced economic and pricing risk"""
        price = flight['price']
        
        # Price-based risk (very low or very high prices are risky)
        if price < 3000:
            price_risk = 25  # Too cheap, quality concerns
        elif price < 5000:
            price_risk = 8   # Good value
        elif price < 8000:
            price_risk = 5   # Standard pricing
        elif price < 12000:
            price_risk = 10  # Premium pricing
        else:
            price_risk = 20  # Very expensive, economic risk
        
        # Market volatility factor
        volatility_risk = random.uniform(3, 12)
        
        # Fuel price impact
        fuel_risk = random.uniform(2, 8)
        
        return min(price_risk + volatility_risk + fuel_risk, 75)
    
    def _calculate_passenger_demand_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate passenger demand-based risk"""
        seats_available = flight['seats_available']
        
        if seats_available < 5:
            return random.uniform(35, 50)  # Very high demand, overbooking risk
        elif seats_available < 15:
            return random.uniform(20, 35)  # High demand
        elif seats_available < 30:
            return random.uniform(8, 20)   # Moderate demand
        else:
            return random.uniform(5, 15)   # Low demand, good availability
    
    def _calculate_route_specific_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate route-specific risk factors"""
        origin = flight['origin']['code']
        destination = flight['destination']['code']
        
        # High-traffic routes have different risk profiles
        high_traffic_routes = [
            ('DEL', 'BOM'), ('BOM', 'DEL'),
            ('DEL', 'BLR'), ('BLR', 'DEL'),
            ('BOM', 'BLR'), ('BLR', 'BOM')
        ]
        
        if (origin, destination) in high_traffic_routes:
            return random.uniform(8, 18)  # Higher competition, better service
        else:
            return random.uniform(12, 25)  # Less frequent, potentially higher risk
    
    def _calculate_time_of_day_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate time-of-day specific risks"""
        departure_hour = int(flight['departure_time'].split(':')[0])
        
        # Risk by time slots
        if 6 <= departure_hour <= 9:    # Early morning
            return random.uniform(5, 12)
        elif 10 <= departure_hour <= 16: # Daytime
            return random.uniform(3, 8)
        elif 17 <= departure_hour <= 20: # Evening
            return random.uniform(8, 15)
        elif 21 <= departure_hour <= 23: # Night
            return random.uniform(15, 25)
        else:                            # Late night/very early
            return random.uniform(20, 35)
    
    def _compare_flights(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare all flights and generate insights"""
        
        # Sort by risk score (best to worst)
        sorted_flights = sorted(analyses, key=lambda x: x['risk_score'], reverse=True)
        
        # Calculate statistics
        risk_scores = [f['risk_score'] for f in analyses]
        prices = [f['price'] for f in analyses]
        
        stats = {
            'best_flight': sorted_flights[0],
            'worst_flight': sorted_flights[-1],
            'average_risk_score': round(statistics.mean(risk_scores), 1),
            'risk_score_range': {
                'min': min(risk_scores),
                'max': max(risk_scores),
                'std_dev': round(statistics.stdev(risk_scores), 1)
            },
            'price_analysis': {
                'cheapest': min(prices),
                'most_expensive': max(prices),
                'average': round(statistics.mean(prices), 0),
                'price_vs_risk_correlation': self._calculate_correlation(prices, risk_scores)
            },
            'airline_performance': self._analyze_airline_performance(analyses),
            'risk_distribution': self._categorize_risk_distribution(risk_scores)
        }
        
        return stats
    
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
            route_confidence = "Low"
        
        # Generate recommendations
        recommendations = []
        
        if best_flight['risk_score'] >= 70:
            recommendations.append(f"Book {best_flight['airline']} {best_flight['flight_number']} for optimal experience")
        
        if risk_distribution['high_risk'] > 50:
            recommendations.append("Consider flexible booking options due to higher risk factors")
        
        if comparison['price_analysis']['price_vs_risk_correlation'] < -0.3:
            recommendations.append("Higher-priced flights show better reliability on this route")
        
        recommendations.append("Monitor weather conditions 24 hours before departure")
        recommendations.append("Arrive at airport 2 hours early for domestic flights")
        
        # Final verdict text
        verdict_text = f"""
        Based on analysis of {len(analyses)} flights, this route shows {route_assessment.lower()} conditions with {route_confidence.lower()} confidence.
        
        The best option is {best_flight['airline']} {best_flight['flight_number']} with a risk score of {best_flight['risk_score']}/100.
        
        Overall route risk assessment: {avg_risk}/100 ({route_assessment})
        
        Key factors: {', '.join([f for f, v in best_flight['risk_factors'].items() if v < 20][:3])} show favorable conditions.
        """
        
        return {
            'overall_score': round(avg_risk, 1),
            'route_assessment': route_assessment,
            'confidence_level': route_confidence,
            'recommended_flight': {
                'flight_number': best_flight['flight_number'],
                'airline': best_flight['airline'],
                'risk_score': best_flight['risk_score'],
                'price': best_flight['price']
            },
            'verdict_text': verdict_text.strip(),
            'recommendations': recommendations[:5],
            'risk_factors_summary': self._summarize_risk_factors(analyses)
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
            flights = stats['flights']
            stats['avg_risk_score'] = round(statistics.mean([f['risk_score'] for f in flights]), 1)
            stats['avg_price'] = round(statistics.mean([f['price'] for f in flights]), 0)
            stats['best_flight'] = max(flights, key=lambda x: x['risk_score'])
        
        return airline_stats
    
    def _categorize_risk_distribution(self, risk_scores: List[float]) -> Dict[str, Any]:
        """Categorize risk distribution"""
        low_risk = sum(1 for score in risk_scores if score >= 70)
        medium_risk = sum(1 for score in risk_scores if 40 <= score < 70)
        high_risk = sum(1 for score in risk_scores if score < 40)
        total = len(risk_scores)
        
        return {
            'low_risk': round((low_risk / total) * 100, 1),
            'medium_risk': round((medium_risk / total) * 100, 1),
            'high_risk': round((high_risk / total) * 100, 1),
            'total_flights': total
        }
    
    def _calculate_correlation(self, prices: List[float], risk_scores: List[float]) -> float:
        """Calculate price vs risk correlation"""
        if len(prices) < 2:
            return 0.0
        return round(self._calculate_simple_correlation(prices, risk_scores), 3)
    
    def _summarize_risk_factors(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize risk factors across all flights"""
        all_factors = {}
        
        for analysis in analyses:
            for factor, value in analysis['risk_factors'].items():
                if factor not in all_factors:
                    all_factors[factor] = []
                all_factors[factor].append(value)
        
        summary = {}
        for factor, values in all_factors.items():
            summary[factor] = {
                'average': round(statistics.mean(values), 1),
                'min': round(min(values), 1),
                'max': round(max(values), 1),
                'impact_level': 'High' if statistics.mean(values) > 30 else 'Medium' if statistics.mean(values) > 15 else 'Low'
            }
        
        return summary
    
    def _calculate_prediction_confidence(self, risk_factors: Dict[str, float], airline_profile: Dict[str, Any]) -> float:
        """Calculate confidence in the prediction"""
        base_confidence = 0.75
        
        # Higher confidence for well-known airlines
        if airline_profile['reliability'] > 0.85:
            base_confidence += 0.1
        
        # Lower confidence for extreme risk values
        extreme_factors = sum(1 for v in risk_factors.values() if v > 70 or v < 10)
        if extreme_factors > 2:
            base_confidence -= 0.15
        
        return min(max(base_confidence, 0.5), 0.95)
    
    def _is_date_in_period(self, date: datetime, start_month: int, start_day: int, 
                          end_month: int, end_day: int) -> bool:
        """Check if date falls within a specific period"""
        try:
            start_date = date.replace(month=start_month, day=start_day)
            end_date = date.replace(month=end_month, day=end_day)
            
            if start_month > end_month:  # Period crosses year boundary
                return date >= start_date or date <= end_date
            else:
                return start_date <= date <= end_date
        except:
            return False
    
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

# Global advanced risk predictor instance
advanced_risk_predictor = AdvancedRiskPredictor()