
"""
GenAI Agent for intelligent flight status retrieval and analysis
Integrates multiple data sources and provides confidence-scored responses
"""

import requests
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from database import db
import logging

logger = logging.getLogger(__name__)

class FlightStatusAgent:
    """GenAI Agent for intelligent flight status retrieval"""
    
    def __init__(self):
        self.flightaware_api_key = None  # Mock implementation
        self.confidence_threshold = 0.7
        
    def get_flight_status(self, flight_id: str) -> Dict[str, Any]:
        """
        Main method to retrieve comprehensive flight status
        
        Args:
            flight_id: Flight identifier (can be flight number or internal ID)
            
        Returns:
            Comprehensive flight status with confidence scoring
        """
        try:
            # Step 1: Check Supabase flights table for metadata
            flight_metadata = self._get_flight_metadata(flight_id)
            
            # Step 2: Call external FlightAware API (mock implementation)
            external_data = self._call_flightaware_api(flight_id, flight_metadata)
            
            # Step 3: Merge results and calculate confidence
            merged_result = self._merge_flight_data(flight_metadata, external_data)
            
            # Step 4: Store response in chatbot_sessions
            session_id = self._store_chatbot_session(flight_id, merged_result)
            
            # Add session tracking
            merged_result['session_id'] = session_id
            merged_result['timestamp'] = datetime.utcnow().isoformat()
            
            return merged_result
            
        except Exception as e:
            logger.error(f"Error retrieving flight status for {flight_id}: {str(e)}")
            return self._create_error_response(flight_id, str(e))
    
    def _get_flight_metadata(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve flight metadata from Supabase flights table"""
        try:
            supabase = db.get_client()
            
            # Try by flight_number first (most common case)
            result = supabase.table('flights').select('*').eq('flight_number', flight_id).execute()
            
            if not result.data:
                # Try by UUID if flight_id looks like a UUID
                if len(flight_id) == 36 and '-' in flight_id:
                    result = supabase.table('flights').select('*').eq('id', flight_id).execute()
            
            if result.data and len(result.data) > 0:
                metadata = result.data[0]
                logger.info(f"Retrieved flight metadata for {flight_id}")
                return metadata
            else:
                logger.warning(f"No flight metadata found for {flight_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving flight metadata: {str(e)}")
            return None
    
    def _call_flightaware_api(self, flight_id: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Call FlightAware API for real-time flight data (mock implementation)
        In production, this would make actual API calls to FlightAware
        """
        try:
            # Mock FlightAware API response
            # In production, you would use:
            # headers = {'x-apikey': self.flightaware_api_key}
            # response = requests.get(f'https://aeroapi.flightaware.com/aeroapi/flights/{flight_id}', headers=headers)
            
            # Generate realistic mock data
            mock_response = self._generate_mock_flightaware_data(flight_id, metadata)
            
            logger.info(f"Retrieved external flight data for {flight_id}")
            return {
                'source': 'flightaware_mock',
                'data': mock_response,
                'confidence': random.uniform(0.85, 0.95),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calling FlightAware API: {str(e)}")
            return {
                'source': 'flightaware_mock',
                'data': None,
                'confidence': 0.0,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _generate_mock_flightaware_data(self, flight_id: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate realistic mock FlightAware API response"""
        
        # Use metadata if available, otherwise generate random data
        if metadata:
            flight_number = metadata.get('flight_number', flight_id)
            origin = metadata.get('origin', 'DEL')
            destination = metadata.get('destination', 'BOM')
        else:
            flight_number = flight_id if flight_id.startswith('QP') else f'QP{random.randint(1000, 9999)}'
            origin = random.choice(['DEL', 'BOM', 'BLR', 'HYD', 'GOA', 'CCU'])
            destination = random.choice(['DEL', 'BOM', 'BLR', 'HYD', 'GOA', 'CCU'])
        
        # Generate realistic flight status
        statuses = ['ON_TIME', 'DELAYED', 'BOARDING', 'DEPARTED', 'ARRIVED']
        status = random.choice(statuses)
        
        # Generate times based on status
        now = datetime.utcnow()
        if status == 'DEPARTED':
            departure_time = now - timedelta(minutes=random.randint(30, 180))
            arrival_time = departure_time + timedelta(hours=2, minutes=random.randint(0, 30))
        elif status == 'ARRIVED':
            arrival_time = now - timedelta(minutes=random.randint(10, 60))
            departure_time = arrival_time - timedelta(hours=2, minutes=random.randint(0, 30))
        else:
            departure_time = now + timedelta(minutes=random.randint(-30, 120))
            arrival_time = departure_time + timedelta(hours=2, minutes=random.randint(0, 30))
        
        return {
            'flight_number': flight_number,
            'status': status,
            'origin': {
                'code': origin,
                'name': self._get_airport_name(origin)
            },
            'destination': {
                'code': destination,
                'name': self._get_airport_name(destination)
            },
            'scheduled_departure': departure_time.isoformat() + 'Z',
            'estimated_departure': (departure_time + timedelta(minutes=random.randint(-15, 45))).isoformat() + 'Z',
            'scheduled_arrival': arrival_time.isoformat() + 'Z',
            'estimated_arrival': (arrival_time + timedelta(minutes=random.randint(-15, 45))).isoformat() + 'Z',
            'gate': f"G{random.randint(1, 25)}",
            'terminal': random.choice(['T1', 'T2', 'T3']),
            'aircraft_type': random.choice(['A320', 'B737', 'A321', 'B738']),
            'altitude': random.randint(35000, 42000) if status == 'DEPARTED' else None,
            'speed': random.randint(450, 550) if status == 'DEPARTED' else None,
            'last_updated': now.isoformat() + 'Z'
        }
    
    def _get_airport_name(self, code: str) -> str:
        """Get airport name from code"""
        airport_names = {
            'DEL': 'Indira Gandhi International Airport',
            'BOM': 'Chhatrapati Shivaji Maharaj International Airport',
            'BLR': 'Kempegowda International Airport',
            'HYD': 'Rajiv Gandhi International Airport',
            'GOA': 'Goa International Airport',
            'CCU': 'Netaji Subhas Chandra Bose International Airport'
        }
        return airport_names.get(code, f'{code} Airport')
    
    def _merge_flight_data(self, metadata: Optional[Dict[str, Any]], external_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge flight metadata and external data with intelligent conflict resolution
        """
        try:
            # Start with external data as base (usually more current)
            if external_data.get('data'):
                merged = external_data['data'].copy()
            else:
                merged = {}
            
            # Calculate base confidence from external source
            external_confidence = external_data.get('confidence', 0.5)
            
            # Merge with metadata if available
            if metadata:
                # Use metadata for missing fields or as fallback
                for key in ['flight_number', 'origin', 'destination', 'aircraft_type']:
                    if key not in merged or not merged[key]:
                        if key in metadata:
                            merged[key] = metadata[key]
                
                # Check for conflicts and adjust confidence
                conflicts = self._detect_data_conflicts(metadata, merged)
                if conflicts:
                    external_confidence *= 0.9  # Reduce confidence for conflicts
                    logger.warning(f"Data conflicts detected: {conflicts}")
            
            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(
                external_confidence,
                metadata is not None,
                external_data.get('data') is not None
            )
            
            # Format final response
            final_response = {
                'flight_number': merged.get('flight_number', 'Unknown'),
                'status': merged.get('status', 'UNKNOWN'),
                'gate': merged.get('gate'),
                'terminal': merged.get('terminal'),
                'eta': merged.get('estimated_arrival'),
                'etd': merged.get('estimated_departure'),
                'scheduled_arrival': merged.get('scheduled_arrival'),
                'scheduled_departure': merged.get('scheduled_departure'),
                'origin': merged.get('origin'),
                'destination': merged.get('destination'),
                'aircraft_type': merged.get('aircraft_type'),
                'altitude': merged.get('altitude'),
                'speed': merged.get('speed'),
                'confidence_score': round(confidence_score, 2),
                'data_sources': {
                    'metadata_available': metadata is not None,
                    'external_data_available': external_data.get('data') is not None,
                    'external_source': external_data.get('source', 'unknown')
                },
                'last_updated': merged.get('last_updated', datetime.utcnow().isoformat() + 'Z')
            }
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error merging flight data: {str(e)}")
            return self._create_error_response('unknown', f"Data merge error: {str(e)}")
    
    def _detect_data_conflicts(self, metadata: Dict[str, Any], external_data: Dict[str, Any]) -> List[str]:
        """Detect conflicts between metadata and external data"""
        conflicts = []
        
        # Check for conflicts in key fields
        conflict_fields = ['flight_number', 'origin', 'destination']
        
        for field in conflict_fields:
            if field in metadata and field in external_data:
                if str(metadata[field]).upper() != str(external_data[field]).upper():
                    conflicts.append(f"{field}: metadata='{metadata[field]}' vs external='{external_data[field]}'")
        
        return conflicts
    
    def _calculate_confidence_score(self, external_confidence: float, has_metadata: bool, has_external: bool) -> float:
        """Calculate overall confidence score based on available data sources"""
        
        base_confidence = 0.0
        
        if has_external:
            base_confidence += external_confidence * 0.7  # External data weighted 70%
        
        if has_metadata:
            base_confidence += 0.3  # Metadata adds 30%
        
        # Boost confidence if we have both sources
        if has_external and has_metadata:
            base_confidence *= 1.1
        
        # Cap at 1.0
        return min(base_confidence, 1.0)
    
    def _store_chatbot_session(self, flight_id: str, response_data: Dict[str, Any]) -> str:
        """Store the agent response in chatbot_sessions table"""
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            supabase = db.get_client()
            
            session_data = {
                'id': session_id,
                'flight_id': flight_id,
                'query_type': 'flight_status',
                'request_data': {'flight_id': flight_id},
                'response_data': response_data,
                'confidence_score': response_data.get('confidence_score', 0.0),
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = supabase.table('chatbot_sessions').insert(session_data).execute()
            
            if result.data:
                logger.info(f"Stored chatbot session {session_id} for flight {flight_id}")
                return session_id
            else:
                logger.error(f"Failed to store chatbot session for flight {flight_id}")
                return session_id  # Return ID anyway for tracking
                
        except Exception as e:
            logger.error(f"Error storing chatbot session: {str(e)}")
            return str(uuid.uuid4())  # Return a UUID anyway
    
    def _create_error_response(self, flight_id: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'flight_number': flight_id,
            'status': 'ERROR',
            'gate': None,
            'terminal': None,
            'eta': None,
            'etd': None,
            'scheduled_arrival': None,
            'scheduled_departure': None,
            'origin': None,
            'destination': None,
            'aircraft_type': None,
            'altitude': None,
            'speed': None,
            'confidence_score': 0.0,
            'error': error_message,
            'data_sources': {
                'metadata_available': False,
                'external_data_available': False,
                'external_source': 'none'
            },
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }

# Global agent instance
flight_status_agent = FlightStatusAgent()