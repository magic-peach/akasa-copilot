"""Cancellation Cost Prediction Service for Akasa Airlines
Predicts cancellation costs based on timing, airline policies, and booking details.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FareType(Enum):
    """Different fare types with varying cancellation policies"""
    ECONOMY_BASIC = "economy_basic"
    ECONOMY_STANDARD = "economy_standard"
    ECONOMY_FLEX = "economy_flex"
    BUSINESS = "business"
    FIRST = "first"

class CancellationReason(Enum):
    """Reasons for cancellation that might affect fees"""
    VOLUNTARY = "voluntary"
    MEDICAL = "medical"
    WEATHER = "weather"
    AIRLINE_FAULT = "airline_fault"
    SCHEDULE_CHANGE = "schedule_change"

@dataclass
class CancellationPolicy:
    """Represents an airline's cancellation policy"""
    airline: str
    fare_type: FareType
    free_cancellation_hours: int
    cancellation_fee_base: float
    cancellation_fee_percentage: float
    refund_processing_days: int
    no_show_penalty: float

@dataclass
class CancellationCostPrediction:
    """Represents a cancellation cost prediction"""
    total_cost: float
    base_fee: float
    percentage_fee: float
    processing_fee: float
    refund_amount: float
    refund_timeline: str
    cost_breakdown: Dict[str, float]
    recommendations: List[str]
    alternative_options: List[Dict]

class CancellationCostService:
    """Service to predict cancellation costs and provide recommendations"""
    
    def __init__(self):
        self.airline_policies = self._initialize_airline_policies()
        self.base_processing_fee = 200.0  # Base processing fee in INR
    
    def _initialize_airline_policies(self) -> Dict[str, Dict[FareType, CancellationPolicy]]:
        """Initialize cancellation policies for different airlines and fare types"""
        policies = {}
        
        # Akasa Air policies
        policies['Akasa Air'] = {
            FareType.ECONOMY_BASIC: CancellationPolicy(
                airline='Akasa Air',
                fare_type=FareType.ECONOMY_BASIC,
                free_cancellation_hours=24,
                cancellation_fee_base=3000.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=7,
                no_show_penalty=3500.0
            ),
            FareType.ECONOMY_STANDARD: CancellationPolicy(
                airline='Akasa Air',
                fare_type=FareType.ECONOMY_STANDARD,
                free_cancellation_hours=24,
                cancellation_fee_base=2500.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=5,
                no_show_penalty=3000.0
            ),
            FareType.ECONOMY_FLEX: CancellationPolicy(
                airline='Akasa Air',
                fare_type=FareType.ECONOMY_FLEX,
                free_cancellation_hours=24,
                cancellation_fee_base=1500.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=3,
                no_show_penalty=2000.0
            )
        }
        
        # IndiGo policies
        policies['IndiGo'] = {
            FareType.ECONOMY_BASIC: CancellationPolicy(
                airline='IndiGo',
                fare_type=FareType.ECONOMY_BASIC,
                free_cancellation_hours=24,
                cancellation_fee_base=3500.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=10,
                no_show_penalty=4000.0
            ),
            FareType.ECONOMY_STANDARD: CancellationPolicy(
                airline='IndiGo',
                fare_type=FareType.ECONOMY_STANDARD,
                free_cancellation_hours=24,
                cancellation_fee_base=3000.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=7,
                no_show_penalty=3500.0
            )
        }
        
        # Air India policies
        policies['Air India'] = {
            FareType.ECONOMY_BASIC: CancellationPolicy(
                airline='Air India',
                fare_type=FareType.ECONOMY_BASIC,
                free_cancellation_hours=24,
                cancellation_fee_base=3000.0,
                cancellation_fee_percentage=10.0,
                refund_processing_days=14,
                no_show_penalty=4000.0
            ),
            FareType.ECONOMY_STANDARD: CancellationPolicy(
                airline='Air India',
                fare_type=FareType.ECONOMY_STANDARD,
                free_cancellation_hours=24,
                cancellation_fee_base=2500.0,
                cancellation_fee_percentage=5.0,
                refund_processing_days=10,
                no_show_penalty=3500.0
            ),
            FareType.BUSINESS: CancellationPolicy(
                airline='Air India',
                fare_type=FareType.BUSINESS,
                free_cancellation_hours=24,
                cancellation_fee_base=5000.0,
                cancellation_fee_percentage=5.0,
                refund_processing_days=7,
                no_show_penalty=7500.0
            )
        }
        
        # SpiceJet policies
        policies['SpiceJet'] = {
            FareType.ECONOMY_BASIC: CancellationPolicy(
                airline='SpiceJet',
                fare_type=FareType.ECONOMY_BASIC,
                free_cancellation_hours=24,
                cancellation_fee_base=3500.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=10,
                no_show_penalty=4000.0
            ),
            FareType.ECONOMY_STANDARD: CancellationPolicy(
                airline='SpiceJet',
                fare_type=FareType.ECONOMY_STANDARD,
                free_cancellation_hours=24,
                cancellation_fee_base=3000.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=7,
                no_show_penalty=3500.0
            )
        }
        
        # Vistara policies
        policies['Vistara'] = {
            FareType.ECONOMY_BASIC: CancellationPolicy(
                airline='Vistara',
                fare_type=FareType.ECONOMY_BASIC,
                free_cancellation_hours=24,
                cancellation_fee_base=3000.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=7,
                no_show_penalty=3500.0
            ),
            FareType.ECONOMY_STANDARD: CancellationPolicy(
                airline='Vistara',
                fare_type=FareType.ECONOMY_STANDARD,
                free_cancellation_hours=24,
                cancellation_fee_base=2500.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=5,
                no_show_penalty=3000.0
            ),
            FareType.BUSINESS: CancellationPolicy(
                airline='Vistara',
                fare_type=FareType.BUSINESS,
                free_cancellation_hours=24,
                cancellation_fee_base=4000.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=3,
                no_show_penalty=5000.0
            )
        }
        
        # GoAir policies
        policies['GoAir'] = {
            FareType.ECONOMY_BASIC: CancellationPolicy(
                airline='GoAir',
                fare_type=FareType.ECONOMY_BASIC,
                free_cancellation_hours=24,
                cancellation_fee_base=3500.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=10,
                no_show_penalty=4000.0
            ),
            FareType.ECONOMY_STANDARD: CancellationPolicy(
                airline='GoAir',
                fare_type=FareType.ECONOMY_STANDARD,
                free_cancellation_hours=24,
                cancellation_fee_base=3000.0,
                cancellation_fee_percentage=0.0,
                refund_processing_days=7,
                no_show_penalty=3500.0
            )
        }
        
        return policies
    
    def predict_cancellation_cost(
        self,
        airline: str,
        fare_type: str,
        ticket_price: float,
        departure_date: datetime,
        cancellation_date: datetime = None,
        reason: CancellationReason = CancellationReason.VOLUNTARY
    ) -> CancellationCostPrediction:
        """Predict cancellation cost for a given booking"""
        try:
            if cancellation_date is None:
                cancellation_date = datetime.now()
            
            # Get airline policy
            fare_type_enum = FareType(fare_type.lower())
            policy = self._get_policy(airline, fare_type_enum)
            
            if not policy:
                return self._create_default_prediction(ticket_price)
            
            # Calculate time until departure
            time_until_departure = departure_date - cancellation_date
            hours_until_departure = time_until_departure.total_seconds() / 3600
            
            # Calculate costs
            cost_breakdown = self._calculate_cost_breakdown(
                policy, ticket_price, hours_until_departure, reason
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                policy, hours_until_departure, cost_breakdown
            )
            
            # Generate alternative options
            alternatives = self._generate_alternatives(
                airline, departure_date, cancellation_date, ticket_price
            )
            
            return CancellationCostPrediction(
                total_cost=cost_breakdown['total_cost'],
                base_fee=cost_breakdown['base_fee'],
                percentage_fee=cost_breakdown['percentage_fee'],
                processing_fee=cost_breakdown['processing_fee'],
                refund_amount=cost_breakdown['refund_amount'],
                refund_timeline=f"{policy.refund_processing_days} business days",
                cost_breakdown=cost_breakdown,
                recommendations=recommendations,
                alternative_options=alternatives
            )
            
        except Exception as e:
            logger.error(f"Error predicting cancellation cost: {str(e)}")
            return self._create_default_prediction(ticket_price)
    
    def _get_policy(self, airline: str, fare_type: FareType) -> Optional[CancellationPolicy]:
        """Get cancellation policy for airline and fare type"""
        if airline in self.airline_policies:
            return self.airline_policies[airline].get(fare_type)
        return None
    
    def _calculate_cost_breakdown(
        self,
        policy: CancellationPolicy,
        ticket_price: float,
        hours_until_departure: float,
        reason: CancellationReason
    ) -> Dict[str, float]:
        """Calculate detailed cost breakdown"""
        breakdown = {
            'base_fee': 0.0,
            'percentage_fee': 0.0,
            'processing_fee': self.base_processing_fee,
            'total_cost': 0.0,
            'refund_amount': 0.0
        }
        
        # Check if within free cancellation period
        if hours_until_departure >= policy.free_cancellation_hours and reason != CancellationReason.VOLUNTARY:
            # Free cancellation for valid reasons within time limit
            breakdown['base_fee'] = 0.0
            breakdown['percentage_fee'] = 0.0
            breakdown['processing_fee'] = 0.0
        elif hours_until_departure >= policy.free_cancellation_hours:
            # Within free cancellation period but voluntary
            breakdown['base_fee'] = policy.cancellation_fee_base * 0.5  # Reduced fee
            breakdown['percentage_fee'] = (ticket_price * policy.cancellation_fee_percentage / 100)
        else:
            # Standard cancellation fees
            breakdown['base_fee'] = policy.cancellation_fee_base
            breakdown['percentage_fee'] = (ticket_price * policy.cancellation_fee_percentage / 100)
            
            # Increase fees for last-minute cancellations
            if hours_until_departure < 24:
                breakdown['base_fee'] *= 1.5
                breakdown['percentage_fee'] *= 1.2
        
        # Apply no-show penalty if cancellation is after departure
        if hours_until_departure < 0:
            breakdown['base_fee'] = policy.no_show_penalty
            breakdown['percentage_fee'] = 0.0
        
        # Calculate total cost and refund
        breakdown['total_cost'] = (
            breakdown['base_fee'] + 
            breakdown['percentage_fee'] + 
            breakdown['processing_fee']
        )
        
        breakdown['refund_amount'] = max(0, ticket_price - breakdown['total_cost'])
        
        return breakdown
    
    def _generate_recommendations(self, policy: CancellationPolicy, hours_until_departure: float, cost_breakdown: Dict) -> List[str]:
        """Generate recommendations based on cancellation analysis"""
        recommendations = []
        
        if hours_until_departure >= policy.free_cancellation_hours:
            recommendations.append("✅ You're within the free cancellation period - minimal fees apply")
        elif hours_until_departure >= 24:
            recommendations.append("⚠️ Standard cancellation fees apply - consider if travel is necessary")
        elif hours_until_departure >= 2:
            recommendations.append("🚨 High cancellation fees due to short notice - explore alternatives")
        else:
            recommendations.append("❌ Very high fees for last-minute cancellation - consider no-show vs cancellation")
        
        # Cost-based recommendations
        if cost_breakdown['total_cost'] > cost_breakdown['refund_amount']:
            recommendations.append("💡 Consider keeping the booking - cancellation costs exceed refund")
        
        if hours_until_departure > 48:
            recommendations.append("📅 You have time - check if you can reschedule instead of cancelling")
        
        # Refund timeline
        recommendations.append(f"⏱️ Refund will be processed in {policy.refund_processing_days} business days")
        
        return recommendations
    
    def _generate_alternatives(self, airline: str, departure_date: datetime, cancellation_date: datetime, ticket_price: float) -> List[Dict]:
        """Generate alternative options to cancellation"""
        alternatives = []
        
        time_until_departure = departure_date - cancellation_date
        hours_until_departure = time_until_departure.total_seconds() / 3600
        
        # Rescheduling option
        if hours_until_departure > 24:
            reschedule_fee = min(2000.0, ticket_price * 0.1)
            alternatives.append({
                'option': 'Reschedule Flight',
                'cost': reschedule_fee,
                'description': f'Change your flight date for ₹{reschedule_fee:.0f} fee',
                'savings': f'Save ₹{max(0, self.predict_cancellation_cost(airline, "economy_standard", ticket_price, departure_date, cancellation_date).total_cost - reschedule_fee):.0f} compared to cancellation',
                'recommended': reschedule_fee < ticket_price * 0.2
            })
        
        # Travel insurance claim
        if hours_until_departure > 2:
            alternatives.append({
                'option': 'Travel Insurance Claim',
                'cost': 0.0,
                'description': 'Check if your reason qualifies for insurance coverage',
                'savings': 'Potentially full refund if claim is approved',
                'recommended': True
            })
        
        # Credit shell option
        credit_value = ticket_price * 0.9  # 90% of ticket value as credit
        alternatives.append({
            'option': 'Convert to Travel Credit',
            'cost': ticket_price * 0.1,
            'description': f'Get ₹{credit_value:.0f} travel credit valid for 1 year',
            'savings': f'Better than ₹{self.predict_cancellation_cost(airline, "economy_standard", ticket_price, departure_date, cancellation_date).refund_amount:.0f} refund',
            'recommended': credit_value > self.predict_cancellation_cost(airline, "economy_standard", ticket_price, departure_date, cancellation_date).refund_amount
        })
        
        return alternatives
    
    def _create_default_prediction(self, ticket_price: float) -> CancellationCostPrediction:
        """Create default prediction when policy is not found"""
        default_fee = min(3000.0, ticket_price * 0.2)
        processing_fee = self.base_processing_fee
        total_cost = default_fee + processing_fee
        refund_amount = max(0, ticket_price - total_cost)
        
        return CancellationCostPrediction(
            total_cost=total_cost,
            base_fee=default_fee,
            percentage_fee=0.0,
            processing_fee=processing_fee,
            refund_amount=refund_amount,
            refund_timeline="7-10 business days",
            cost_breakdown={
                'base_fee': default_fee,
                'percentage_fee': 0.0,
                'processing_fee': processing_fee,
                'total_cost': total_cost,
                'refund_amount': refund_amount
            },
            recommendations=["⚠️ Using estimated cancellation costs - check airline policy for exact fees"],
            alternative_options=[]
        )
    
    def compare_cancellation_costs_over_time(self, airline: str, fare_type: str, ticket_price: float, departure_date: datetime) -> Dict:
        """Compare cancellation costs at different time points"""
        try:
            time_points = [
                ('Now', datetime.now()),
                ('1 Week Later', datetime.now() + timedelta(weeks=1)),
                ('2 Weeks Later', datetime.now() + timedelta(weeks=2)),
                ('1 Month Later', datetime.now() + timedelta(days=30)),
                ('Day Before Flight', departure_date - timedelta(days=1)),
                ('Day of Flight', departure_date)
            ]
            
            comparisons = []
            
            for label, cancel_date in time_points:
                if cancel_date <= departure_date + timedelta(hours=2):  # Only show realistic scenarios
                    prediction = self.predict_cancellation_cost(
                        airline, fare_type, ticket_price, departure_date, cancel_date
                    )
                    
                    comparisons.append({
                        'timepoint': label,
                        'date': cancel_date.strftime('%Y-%m-%d'),
                        'total_cost': prediction.total_cost,
                        'refund_amount': prediction.refund_amount,
                        'cost_percentage': (prediction.total_cost / ticket_price) * 100
                    })
            
            return {
                'comparisons': comparisons,
                'best_time': min(comparisons, key=lambda x: x['total_cost']),
                'worst_time': max(comparisons, key=lambda x: x['total_cost'])
            }
            
        except Exception as e:
            logger.error(f"Error comparing cancellation costs over time: {str(e)}")
            return {'comparisons': [], 'best_time': None, 'worst_time': None}

# Global cancellation cost service instance
cancellation_service = CancellationCostService()