"""
Flight Search Service for Akasa Airlines
Generates multiple flight options based on user criteria with risk scoring
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from src.services.advanced_risk_predictor import advanced_risk_predictor
# Removed unused imports

logger = logging.getLogger(__name__)

class FlightSearchService:
    """Service to search and generate flight options with risk assessment"""
    
    def __init__(self):
        self.airlines = ['Akasa Air', 'IndiGo', 'SpiceJet', 'Air India', 'Vistara', 'Go First']
        self.aircraft_types = ['A320', 'A321', 'B737', 'B738', 'ATR72', 'A319', 'B787']
        
        # Airline risk profiles
        self.airline_risk_profiles = {
            'Akasa Air': {'base_risk': 15, 'reliability': 0.92, 'punctuality': 0.90},
            'IndiGo': {'base_risk': 18, 'reliability': 0.88, 'punctuality': 0.85},
            'SpiceJet': {'base_risk': 30, 'reliability': 0.75, 'punctuality': 0.70},
            'Air India': {'base_risk': 25, 'reliability': 0.80, 'punctuality': 0.75},
            'Vistara': {'base_risk': 17, 'reliability': 0.90, 'punctuality': 0.88},
            'Go First': {'base_risk': 28, 'reliability': 0.78, 'punctuality': 0.72}
        }
        
        # Expanded airport data with 20 major Indian cities
        self.airports = {
            'DEL': {'name': 'Indira Gandhi International Airport', 'city': 'Delhi', 'terminals': ['T1', 'T2', 'T3']},
            'BOM': {'name': 'Chhatrapati Shivaji Maharaj International Airport', 'city': 'Mumbai', 'terminals': ['T1', 'T2']},
            'BLR': {'name': 'Kempegowda International Airport', 'city': 'Bangalore', 'terminals': ['T1', 'T2']},
            'HYD': {'name': 'Rajiv Gandhi International Airport', 'city': 'Hyderabad', 'terminals': ['T1']},
            'GOA': {'name': 'Goa International Airport', 'city': 'Goa', 'terminals': ['T1']},
            'CCU': {'name': 'Netaji Subhas Chandra Bose International Airport', 'city': 'Kolkata', 'terminals': ['T1', 'T2']},
            'MAA': {'name': 'Chennai International Airport', 'city': 'Chennai', 'terminals': ['T1', 'T2']},
            'AMD': {'name': 'Sardar Vallabhbhai Patel International Airport', 'city': 'Ahmedabad', 'terminals': ['T1', 'T2']},
            'PNQ': {'name': 'Pune Airport', 'city': 'Pune', 'terminals': ['T1']},
            'JAI': {'name': 'Jaipur International Airport', 'city': 'Jaipur', 'terminals': ['T1']},
            'LKO': {'name': 'Chaudhary Charan Singh International Airport', 'city': 'Lucknow', 'terminals': ['T1']},
            'IXC': {'name': 'Chandigarh Airport', 'city': 'Chandigarh', 'terminals': ['T1']},
            'VNS': {'name': 'Lal Bahadur Shastri Airport', 'city': 'Varanasi', 'terminals': ['T1']},
            'IXB': {'name': 'Bagdogra Airport', 'city': 'Siliguri', 'terminals': ['T1']},
            'RPR': {'name': 'Swami Vivekananda Airport', 'city': 'Raipur', 'terminals': ['T1']},
            'BHO': {'name': 'Raja Bhoj Airport', 'city': 'Bhopal', 'terminals': ['T1']},
            'IDR': {'name': 'Devi Ahilya Bai Holkar Airport', 'city': 'Indore', 'terminals': ['T1']},
            'IXU': {'name': 'Aurangabad Airport', 'city': 'Aurangabad', 'terminals': ['T1']},
            'IXD': {'name': 'Allahabad Airport', 'city': 'Allahabad', 'terminals': ['T1']},
            'IXJ': {'name': 'Jammu Airport', 'city': 'Jammu', 'terminals': ['T1']}
        }
        
        # Base flight durations (in minutes) - comprehensive route network
        self.flight_durations = {
            # Delhi routes
            ('DEL', 'BOM'): 135, ('BOM', 'DEL'): 135,
            ('DEL', 'BLR'): 165, ('BLR', 'DEL'): 165,
            ('DEL', 'HYD'): 150, ('HYD', 'DEL'): 150,
            ('DEL', 'CCU'): 135, ('CCU', 'DEL'): 135,
            ('DEL', 'MAA'): 165, ('MAA', 'DEL'): 165,
            ('DEL', 'PNQ'): 120, ('PNQ', 'DEL'): 120,
            ('DEL', 'AMD'): 105, ('AMD', 'DEL'): 105,
            ('DEL', 'JAI'): 75, ('JAI', 'DEL'): 75,
            ('DEL', 'GOA'): 150, ('GOA', 'DEL'): 150,
            
            # Mumbai routes
            ('BOM', 'BLR'): 90, ('BLR', 'BOM'): 90,
            ('BOM', 'GOA'): 75, ('GOA', 'BOM'): 75,
            ('BOM', 'CCU'): 150, ('CCU', 'BOM'): 150,
            ('BOM', 'AMD'): 75, ('AMD', 'BOM'): 75,
            ('BOM', 'PNQ'): 45, ('PNQ', 'BOM'): 45,
            ('BOM', 'HYD'): 90, ('HYD', 'BOM'): 90,
            ('BOM', 'MAA'): 105, ('MAA', 'BOM'): 105,
            ('BOM', 'JAI'): 105, ('JAI', 'BOM'): 105,
            
            # Bangalore routes
            ('BLR', 'HYD'): 60, ('HYD', 'BLR'): 60,
            ('BLR', 'MAA'): 60, ('MAA', 'BLR'): 60,
            ('BLR', 'GOA'): 75, ('GOA', 'BLR'): 75,
            ('BLR', 'CCU'): 135, ('CCU', 'BLR'): 135,
            ('BLR', 'AMD'): 105, ('AMD', 'BLR'): 105,
            ('BLR', 'PNQ'): 75, ('PNQ', 'BLR'): 75,
            ('BLR', 'JAI'): 120, ('JAI', 'BLR'): 120,
            
            # Other routes
            ('HYD', 'MAA'): 75, ('MAA', 'HYD'): 75,
            ('HYD', 'CCU'): 120, ('CCU', 'HYD'): 120,
            ('HYD', 'GOA'): 90, ('GOA', 'HYD'): 90,
            ('MAA', 'CCU'): 120, ('CCU', 'MAA'): 120,
            ('MAA', 'GOA'): 90, ('GOA', 'MAA'): 90,
            ('AMD', 'GOA'): 90, ('GOA', 'AMD'): 90,
            ('AMD', 'JAI'): 75, ('JAI', 'AMD'): 75,
            ('PNQ', 'GOA'): 60, ('GOA', 'PNQ'): 60
        }
    
    def search_flights(self, origin: str, destination: str, date: str, budget: int, 
                      passenger_count: int = 1, use_enhanced_prediction: bool = True) -> List[Dict[str, Any]]:
        """
        Search for flights based on criteria and generate multiple options
        
        Args:
            origin: Origin airport code
            destination: Destination airport code  
            date: Travel date in YYYY-MM-DD format
            budget: Maximum budget in INR
            passenger_count: Number of passengers
            use_enhanced_prediction: Whether to use enhanced risk prediction with real-time data
            
        Returns:
            List of flight options with risk scores
        """
        try:
            # Validate inputs
            if not self._validate_search_params(origin, destination, date, budget):
                return []
            
            # Generate flight options
            flights = self._generate_flight_options(origin, destination, date, budget, passenger_count)
            
            # Add basic risk scores to each flight
            for flight in flights:
                flight['risk_analysis'] = self._calculate_risk_score(flight)
            
            if use_enhanced_prediction:
                # Use enhanced risk predictor with real-time data
                logger.info(f"Using enhanced risk prediction with real-time data for {len(flights)} flights")
                comprehensive_analysis = advanced_risk_predictor.predict_comprehensive_risk(flights)
                
                # Update flights with enhanced risk scores
                if 'flight_analyses' in comprehensive_analysis:
                    flight_analyses = comprehensive_analysis['flight_analyses']
                    for i, flight in enumerate(flights):
                        if i < len(flight_analyses):
                            analysis = flight_analyses[i]
                            flight['risk_analysis'].update({
                                'overall_risk_score': analysis['risk_score'],
                                'risk_level': analysis['risk_level'],
                                'risk_color': analysis['risk_color'],
                                'advanced_recommendation': analysis.get('recommendation', ''),
                                'confidence': analysis.get('confidence', 0.7),
                                'real_time_data': True
                            })
                            
                            # Add real-time weather and flight data
                            if 'real_time_data' in analysis:
                                flight['real_time_data'] = analysis['real_time_data']
                    
                    # Add comprehensive analysis to the first flight for access
                    if flights:
                        flights[0]['comprehensive_analysis'] = comprehensive_analysis
                        flights[0]['using_enhanced_prediction'] = True
            else:
                # Use standard advanced risk predictor
                comprehensive_analysis = advanced_risk_predictor.predict_comprehensive_risk(flights)
                
                # Update flights with advanced risk scores if available
                if comprehensive_analysis.get('flight_analyses'):
                    flight_analyses = comprehensive_analysis['flight_analyses']
                    for i, flight in enumerate(flights):
                        if i < len(flight_analyses):
                            analysis = flight_analyses[i]
                            flight['risk_analysis'].update({
                                'overall_risk_score': analysis['risk_score'],
                                'risk_level': analysis['risk_level'],
                                'risk_color': analysis['risk_color'],
                                'advanced_recommendation': analysis.get('recommendation', ''),
                                'confidence': analysis.get('confidence', 0.7),
                                'real_time_data': False
                            })
                    
                    # Add comprehensive analysis to the first flight for access
                    if flights:
                        flights[0]['comprehensive_analysis'] = comprehensive_analysis
                        flights[0]['using_enhanced_prediction'] = False
            
            # Sort by price and risk score
            flights.sort(key=lambda x: (x['price'], x['risk_analysis']['overall_risk_score']))
            
            logger.info(f"Generated {len(flights)} flight options for {origin} to {destination}")
            return flights
            
        except Exception as e:
            logger.error(f"Error searching flights: {str(e)}")
            return []
    
    def _validate_search_params(self, origin: str, destination: str, date: str, budget: int) -> bool:
        """Validate search parameters"""
        try:
            # Check if origin and destination are different
            if origin.upper() == destination.upper():
                return False
            
            # Check date format and future date
            travel_date = datetime.strptime(date, '%Y-%m-%d').date()
            if travel_date < datetime.now().date():
                return False
            
            # Check budget
            if budget < 1000:  # Minimum realistic budget
                return False
            
            return True
            
        except ValueError:
            return False
    
    def _generate_flight_options(self, origin: str, destination: str, date: str, 
                               budget: int, passenger_count: int) -> List[Dict[str, Any]]:
        """Generate multiple flight options"""
        flights = []
        origin = origin.upper()
        destination = destination.upper()
        
        # Generate 8-12 flights across different price ranges
        num_flights = random.randint(8, 12)
        
        # Define price ranges based on budget
        price_ranges = self._get_price_ranges(budget)
        
        for i in range(num_flights):
            # Select price range
            price_range = random.choice(price_ranges)
            base_price = random.randint(price_range['min'], price_range['max'])
            
            # Generate flight details
            flight = self._create_flight_option(origin, destination, date, base_price, i)
            flights.append(flight)
        
        return flights
    
    def _get_price_ranges(self, budget: int) -> List[Dict[str, Any]]:
        """Get price ranges based on budget"""
        ranges = []
        
        # Below 5k range
        if budget >= 5000:
            ranges.append({'min': 3500, 'max': 4999, 'label': 'Below ₹5k'})
        
        # Below 7k range  
        if budget >= 7000:
            ranges.append({'min': 5000, 'max': 6999, 'label': 'Below ₹7k'})
        
        # Below 10k range
        if budget >= 10000:
            ranges.append({'min': 7000, 'max': 9999, 'label': 'Below ₹10k'})
        
        # Below 15k range
        if budget >= 15000:
            ranges.append({'min': 10000, 'max': 14999, 'label': 'Below ₹15k'})
        
        # Premium range
        if budget >= 20000:
            ranges.append({'min': 15000, 'max': min(budget, 25000), 'label': 'Premium'})
        
        # Ensure at least one range exists
        if not ranges:
            ranges.append({'min': 2000, 'max': budget, 'label': f'Below ₹{budget//1000}k'})
        
        return ranges
    
    def _create_flight_option(self, origin: str, destination: str, date: str, 
                            price: int, index: int) -> Dict[str, Any]:
        """Create a single flight option"""
        
        # Generate flight number
        airline_codes = {'Akasa Air': 'QP', 'IndiGo': '6E', 'SpiceJet': 'SG', 'Air India': 'AI', 'Vistara': 'UK', 'Go First': 'G8'}
        airline = random.choice(self.airlines)
        flight_number = f"{airline_codes.get(airline, 'QP')}{random.randint(1000, 9999)}"
        
        # Calculate flight duration
        route_key = (origin, destination)
        base_duration = self.flight_durations.get(route_key, 120)  # Default 2 hours
        duration = base_duration + random.randint(-15, 30)  # Add some variation
        
        # Generate departure time
        travel_date = datetime.strptime(date, '%Y-%m-%d')
        departure_hour = random.randint(6, 22)  # 6 AM to 10 PM
        departure_minute = random.choice([0, 15, 30, 45])
        departure_time = travel_date.replace(hour=departure_hour, minute=departure_minute)
        arrival_time = departure_time + timedelta(minutes=duration)
        
        # Get airport info
        origin_info = self.airports.get(origin, {'name': f'{origin} Airport', 'city': origin, 'terminals': ['T1']})
        dest_info = self.airports.get(destination, {'name': f'{destination} Airport', 'city': destination, 'terminals': ['T1']})
        
        return {
            'id': str(uuid.uuid4()),
            'flight_number': flight_number,
            'airline': airline,
            'aircraft_type': random.choice(self.aircraft_types),
            'origin': {
                'code': origin,
                'name': origin_info['name'],
                'city': origin_info['city'],
                'terminal': random.choice(origin_info['terminals'])
            },
            'destination': {
                'code': destination,
                'name': dest_info['name'], 
                'city': dest_info['city'],
                'terminal': random.choice(dest_info['terminals'])
            },
            'departure_time': departure_time.strftime('%H:%M'),
            'arrival_time': arrival_time.strftime('%H:%M'),
            'seats_available': random.randint(1, 30),
            'duration': f"{duration//60}h {duration%60}m",
            'departure_datetime': departure_time.isoformat(),
            'arrival_datetime': arrival_time.isoformat(),
            'duration': f"{duration // 60}h {duration % 60}m",
            'duration_minutes': duration,
            'price': price,
            'seats_available': random.randint(5, 50),
            'class': 'Economy',
            'stops': 0,  # Direct flights only for now
            'baggage': '15kg',
            'meal': random.choice(['Included', 'Paid', 'Not Available']),
            'wifi': random.choice([True, False]),
            'entertainment': random.choice([True, False]),
            'cancellation_policy': random.choice(['Free', 'Paid', 'Non-refundable']),
            'date': date
        }
    
    def _calculate_risk_score(self, flight: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a flight"""
        
        # Risk factors (0-100 scale, lower is better)
        risk_factors = {
            'weather_risk': self._calculate_weather_risk(flight),
            'operational_risk': self._calculate_operational_risk(flight),
            'airport_risk': self._calculate_airport_risk(flight),
            'seasonal_risk': self._calculate_seasonal_risk(flight),
            'regulatory_risk': self._calculate_regulatory_risk(flight),
            'passenger_risk': self._calculate_passenger_risk(flight),
            'technology_risk': self._calculate_technology_risk(flight),
            'pricing_risk': self._calculate_pricing_risk(flight)
        }
        
        # Calculate weighted overall score
        weights = {
            'weather_risk': 0.20,
            'operational_risk': 0.18,
            'airport_risk': 0.15,
            'seasonal_risk': 0.12,
            'regulatory_risk': 0.10,
            'passenger_risk': 0.10,
            'technology_risk': 0.08,
            'pricing_risk': 0.07
        }
        
        overall_risk = sum(risk_factors[factor] * weights[factor] for factor in risk_factors)
        
        # Convert to 0-100 scale where higher is better (opposite of risk)
        risk_score = max(0, 100 - overall_risk)
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = 'Low Risk'
            risk_color = 'green'
        elif risk_score >= 60:
            risk_level = 'Medium Risk'
            risk_color = 'yellow'
        else:
            risk_level = 'High Risk'
            risk_color = 'red'
        
        return {
            'overall_risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_factors': risk_factors,
            'recommendations': self._generate_recommendations(risk_factors, flight)
        }
    
    def _calculate_weather_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate weather-related risk"""
        # Mock weather risk based on season and route
        base_risk = random.uniform(10, 40)
        
        # Adjust for monsoon season (June-September)
        departure_date = datetime.fromisoformat(flight['departure_datetime'])
        if 6 <= departure_date.month <= 9:
            base_risk += random.uniform(10, 25)
        
        # Adjust for certain routes (coastal areas during monsoon)
        if flight['destination']['code'] in ['BOM', 'GOA', 'CCU'] and 6 <= departure_date.month <= 9:
            base_risk += random.uniform(5, 15)
        
        return min(base_risk, 100)
    
    def _calculate_operational_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate operational/airline risk using airline profiles"""
        airline = flight['airline']
        profile = self.airline_risk_profiles.get(airline, {'base_risk': 25, 'reliability': 0.80, 'punctuality': 0.75})
        
        # Base risk from airline profile with more variation
        base_risk = profile['base_risk']
        
        # Add reliability and punctuality factors
        reliability_penalty = (1 - profile['reliability']) * 40
        punctuality_penalty = (1 - profile['punctuality']) * 35
        
        base_risk += reliability_penalty + punctuality_penalty
        
        # Add significant random variation for diversity
        base_risk += random.uniform(-8, 15)
        
        # Adjust for time of day (early morning and late night have higher risk)
        departure_hour = int(flight['departure_time'].split(':')[0])
        if departure_hour < 7 or departure_hour > 21:
            base_risk += random.uniform(8, 18)
        
        # Aircraft type risk
        aircraft_risk = {
            'A320': random.uniform(0, 5),
            'A321': random.uniform(0, 5),
            'B737': random.uniform(2, 8),
            'B738': random.uniform(2, 8),
            'ATR72': random.uniform(5, 12)
        }
        base_risk += aircraft_risk.get(flight['aircraft_type'], 5)
        
        return min(max(base_risk, 5), 100)
    
    def _calculate_airport_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate airport-specific risk"""
        # Airport congestion risk
        airport_risk = {
            'DEL': random.uniform(20, 35),
            'BOM': random.uniform(25, 40),
            'BLR': random.uniform(15, 25),
            'HYD': random.uniform(10, 20),
            'GOA': random.uniform(5, 15),
            'CCU': random.uniform(15, 30)
        }
        
        origin_risk = airport_risk.get(flight['origin']['code'], 20)
        dest_risk = airport_risk.get(flight['destination']['code'], 20)
        
        return min((origin_risk + dest_risk) / 2, 100)
    
    def _calculate_seasonal_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate seasonal/occasion-based risk"""
        departure_date = datetime.fromisoformat(flight['departure_datetime'])
        base_risk = random.uniform(5, 15)
        
        # Festival seasons (Diwali, Christmas, etc.)
        high_season_months = [10, 11, 12, 1, 4, 5]  # Oct-Jan, Apr-May
        if departure_date.month in high_season_months:
            base_risk += random.uniform(10, 20)
        
        # Weekend travel
        if departure_date.weekday() >= 5:  # Saturday, Sunday
            base_risk += random.uniform(5, 10)
        
        return min(base_risk, 100)
    
    def _calculate_regulatory_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate regulatory & geopolitical risk"""
        # Generally low for domestic flights
        return random.uniform(5, 15)
    
    def _calculate_passenger_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate passenger-specific risk"""
        # Based on seat availability and demand
        seats_available = flight['seats_available']
        if seats_available < 10:
            return random.uniform(20, 35)
        elif seats_available < 25:
            return random.uniform(10, 25)
        else:
            return random.uniform(5, 15)
    
    def _calculate_technology_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate technology & system risk"""
        # Generally low, varies slightly by airline
        return random.uniform(5, 20)
    
    def _calculate_pricing_risk(self, flight: Dict[str, Any]) -> float:
        """Calculate pricing & economic risk"""
        # Lower risk for lower prices
        price = flight['price']
        if price < 5000:
            return random.uniform(5, 15)
        elif price < 10000:
            return random.uniform(10, 20)
        else:
            return random.uniform(15, 30)
    
    def _generate_recommendations(self, risk_factors: Dict[str, float], 
                                flight: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on risk factors"""
        recommendations = []
        
        # Weather recommendations
        if risk_factors['weather_risk'] > 30:
            recommendations.append("Check weather forecast before travel")
            recommendations.append("Consider travel insurance")
        
        # Operational recommendations
        if risk_factors['operational_risk'] > 30:
            recommendations.append("Arrive at airport early")
            recommendations.append("Keep backup flight options ready")
        
        # Airport recommendations
        if risk_factors['airport_risk'] > 30:
            recommendations.append("Expect potential delays at busy airports")
            recommendations.append("Use airport lounges if available")
        
        # Seasonal recommendations
        if risk_factors['seasonal_risk'] > 25:
            recommendations.append("Book early due to high demand season")
            recommendations.append("Consider flexible booking options")
        
        # Passenger recommendations
        if risk_factors['passenger_risk'] > 25:
            recommendations.append("Book soon - limited seats available")
        
        return recommendations[:3]  # Return top 3 recommendations

    def get_pnr_info(self, pnr_number: str) -> Dict[str, Any]:
        """
        Get PNR information for tracking
        
        Args:
            pnr_number: 6-10 digit PNR number
            
        Returns:
            Dictionary containing PNR details and flight information
        """
        try:
            # Validate PNR format
            if not pnr_number or len(pnr_number) < 6 or len(pnr_number) > 10:
                raise ValueError("Invalid PNR format")
            
            # Generate mock PNR data based on the PNR number
            # In production, this would query a real database
            pnr_data = self._generate_pnr_data(pnr_number)
            
            return pnr_data
            
        except Exception as e:
            logger.error(f"Error getting PNR info for {pnr_number}: {str(e)}")
            raise e
    
    def _generate_pnr_data(self, pnr_number: str) -> Dict[str, Any]:
        """Generate mock PNR data for demonstration"""
        import random
        from datetime import datetime, timedelta
        
        # Use PNR as seed for consistent data
        random.seed(hash(pnr_number) % 2**32)
        
        # Generate flight details
        airports = list(self.airports.keys())
        origin = random.choice(airports)
        destination = random.choice([a for a in airports if a != origin])
        
        airline = random.choice(self.airlines)
        flight_number = f"{airline[:2].upper()}{random.randint(100, 999)}"
        
        # Generate booking date (1-30 days ago)
        booking_date = datetime.now() - timedelta(days=random.randint(1, 30))
        
        # Generate flight date (1-60 days from now)
        flight_date = datetime.now() + timedelta(days=random.randint(1, 60))
        
        # Generate departure time
        departure_hour = random.randint(6, 22)
        departure_minute = random.choice([0, 15, 30, 45])
        departure_time = flight_date.replace(hour=departure_hour, minute=departure_minute)
        
        # Calculate arrival time
        route_key = (origin, destination)
        base_duration = self.flight_durations.get(route_key, 120)
        duration = base_duration + random.randint(-15, 30)
        arrival_time = departure_time + timedelta(minutes=duration)
        
        # Generate current status
        status_options = ['On Time', 'Delayed', 'Boarding', 'Departed']
        current_status = random.choice(status_options)
        
        # Generate delay if status is delayed
        delay_minutes = 0
        if current_status == 'Delayed':
            delay_minutes = random.randint(15, 120)
        
        # Generate gate and terminal
        origin_info = self.airports.get(origin, {'terminals': ['T1']})
        dest_info = self.airports.get(destination, {'terminals': ['T1']})
        
        gate = f"Gate {random.randint(1, 50)}"
        terminal = random.choice(origin_info['terminals'])
        
        # Generate seat number
        seat_number = f"{random.randint(1, 30)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
        
        return {
            'pnr': pnr_number,
            'status': 'Confirmed',  # Most bookings are confirmed
            'booking_date': booking_date.strftime('%Y-%m-%d'),
            'flight_details': {
                'airline': airline,
                'flight_number': flight_number,
                'origin': {
                    'code': origin,
                    'city': self.airports[origin]['city'],
                    'name': self.airports[origin]['name']
                },
                'destination': {
                    'code': destination,
                    'city': self.airports[destination]['city'],
                    'name': self.airports[destination]['name']
                },
                'departure_date': flight_date.strftime('%Y-%m-%d'),
                'departure_time': departure_time.strftime('%H:%M'),
                'arrival_time': arrival_time.strftime('%H:%M'),
                'seat_number': seat_number,
                'class': 'Economy'
            },
            'current_status': {
                'status': current_status,
                'gate': gate,
                'terminal': terminal,
                'delay_minutes': delay_minutes,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'using_real_time_data': random.choice([True, False])  # Simulate real-time data availability
        }

# Global flight search service instance
flight_search_service = FlightSearchService()