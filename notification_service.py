"""
Notification service for Akasa Airlines
Handles SMS, email, and push notifications with Twilio and SendGrid integration
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from database import db
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing multi-channel notifications"""
    
    def __init__(self):
        # Mock API credentials (in production, these would be from environment)
        self.twilio_account_sid = None
        self.twilio_auth_token = None
        self.twilio_phone_number = None
        self.sendgrid_api_key = None
        self.sendgrid_from_email = "noreply@akasa.com"
        
    def subscribe_to_alerts(self, user_id: str, channel: str, contact_info: str, 
                          subscription_type: str = 'all_alerts') -> Dict[str, Any]:
        """
        Subscribe user to flight alerts
        
        Args:
            user_id: User identifier
            channel: Notification channel (sms, email, push)
            contact_info: Contact information (phone/email)
            subscription_type: Type of alerts to subscribe to
            
        Returns:
            Subscription result
        """
        try:
            # Validate channel
            valid_channels = ['sms', 'email', 'push']
            if channel not in valid_channels:
                return {
                    'success': False,
                    'error': f'Invalid channel. Must be one of: {", ".join(valid_channels)}'
                }
            
            # Validate contact info based on channel
            if channel == 'sms' and not self._validate_phone_number(contact_info):
                return {
                    'success': False,
                    'error': 'Invalid phone number format for SMS subscription'
                }
            elif channel == 'email' and not self._validate_email(contact_info):
                return {
                    'success': False,
                    'error': 'Invalid email format for email subscription'
                }
            
            # Check if subscription already exists
            supabase = db.get_client()
            existing = supabase.table('alerts_subscriptions').select('*').eq('user_id', user_id).eq('channel', channel).execute()
            
            subscription_data = {
                'user_id': user_id,
                'channel': channel,
                'contact_info': contact_info,
                'subscription_type': subscription_type,
                'active': True,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if existing.data:
                # Update existing subscription
                result = supabase.table('alerts_subscriptions').update(subscription_data).eq('user_id', user_id).eq('channel', channel).execute()
                action = 'updated'
            else:
                # Create new subscription
                subscription_data['created_at'] = datetime.utcnow().isoformat()
                result = supabase.table('alerts_subscriptions').insert(subscription_data).execute()
                action = 'created'
            
            if result.data:
                subscription_id = result.data[0]['id']
                
                # Send confirmation message
                self._send_subscription_confirmation(channel, contact_info, action)
                
                logger.info(f"Alert subscription {action} for user {user_id}: {channel}")
                
                return {
                    'success': True,
                    'subscription_id': subscription_id,
                    'channel': channel,
                    'contact_info': contact_info,
                    'action': action,
                    'message': f'Successfully {action} alert subscription via {channel}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to save subscription to database'
                }
                
        except Exception as e:
            logger.error(f"Error subscribing to alerts: {str(e)}")
            return {
                'success': False,
                'error': f'Subscription failed: {str(e)}'
            }
    
    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS using Twilio (mock implementation)
        In production, this would use actual Twilio API
        """
        try:
            # Mock Twilio SMS sending
            # In production:
            # from twilio.rest import Client
            # client = Client(self.twilio_account_sid, self.twilio_auth_token)
            # message = client.messages.create(
            #     body=message,
            #     from_=self.twilio_phone_number,
            #     to=phone_number
            # )
            
            # Mock successful SMS
            mock_message_sid = f"SM{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            print(f"\n📱 MOCK SMS SENT")
            print(f"To: {phone_number}")
            print(f"Message: {message}")
            print(f"Message SID: {mock_message_sid}")
            print("-" * 40)
            
            logger.info(f"Mock SMS sent to {phone_number}")
            
            return {
                'success': True,
                'message_sid': mock_message_sid,
                'to': phone_number,
                'status': 'sent'
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_email(self, email_address: str, subject: str, message: str) -> Dict[str, Any]:
        """
        Send email using SendGrid (mock implementation)
        In production, this would use actual SendGrid API
        """
        try:
            # Mock SendGrid email sending
            # In production:
            # import sendgrid
            # from sendgrid.helpers.mail import Mail
            # sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            # mail = Mail(
            #     from_email=self.sendgrid_from_email,
            #     to_emails=email_address,
            #     subject=subject,
            #     html_content=message
            # )
            # response = sg.send(mail)
            
            # Mock successful email
            mock_message_id = f"EM{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            print(f"\n📧 MOCK EMAIL SENT")
            print(f"To: {email_address}")
            print(f"Subject: {subject}")
            print(f"Message: {message}")
            print(f"Message ID: {mock_message_id}")
            print("-" * 40)
            
            logger.info(f"Mock email sent to {email_address}")
            
            return {
                'success': True,
                'message_id': mock_message_id,
                'to': email_address,
                'status': 'sent'
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_push_notification(self, user_id: str, title: str, message: str) -> Dict[str, Any]:
        """
        Send push notification (mock implementation)
        In production, this would use Firebase or OneSignal
        """
        try:
            # Mock push notification
            mock_notification_id = f"PN{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            print(f"\n🔔 MOCK PUSH NOTIFICATION SENT")
            print(f"User ID: {user_id}")
            print(f"Title: {title}")
            print(f"Message: {message}")
            print(f"Notification ID: {mock_notification_id}")
            print("-" * 40)
            
            logger.info(f"Mock push notification sent to user {user_id}")
            
            return {
                'success': True,
                'notification_id': mock_notification_id,
                'user_id': user_id,
                'status': 'sent'
            }
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_subscribers(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify all subscribers about an alert
        
        Args:
            alert_data: Alert information to send
            
        Returns:
            Notification results
        """
        try:
            flight_number = alert_data.get('flight_number')
            alert_type = alert_data.get('alert_type')
            message = alert_data.get('message')
            
            # Get all active subscriptions
            supabase = db.get_client()
            result = supabase.table('alerts_subscriptions').select('*').eq('active', True).execute()
            
            subscriptions = result.data or []
            
            notification_results = []
            
            for subscription in subscriptions:
                user_id = subscription['user_id']
                channel = subscription['channel']
                contact_info = subscription['contact_info']
                
                # Format message for channel
                formatted_message = self._format_alert_message(alert_data, channel)
                
                # Send notification based on channel
                if channel == 'sms':
                    result = self.send_sms(contact_info, formatted_message)
                elif channel == 'email':
                    subject = f"Akasa Flight Alert - {flight_number}"
                    result = self.send_email(contact_info, subject, formatted_message)
                elif channel == 'push':
                    title = f"Flight {flight_number} Alert"
                    result = self.send_push_notification(user_id, title, formatted_message)
                else:
                    continue
                
                notification_results.append({
                    'user_id': user_id,
                    'channel': channel,
                    'contact_info': contact_info,
                    'success': result.get('success', False),
                    'error': result.get('error')
                })
            
            successful_notifications = sum(1 for r in notification_results if r['success'])
            
            logger.info(f"Sent {successful_notifications}/{len(notification_results)} notifications for alert {alert_type}")
            
            return {
                'total_subscriptions': len(subscriptions),
                'notifications_sent': successful_notifications,
                'results': notification_results
            }
            
        except Exception as e:
            logger.error(f"Error notifying subscribers: {str(e)}")
            return {
                'total_subscriptions': 0,
                'notifications_sent': 0,
                'error': str(e)
            }
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        import re
        # Basic phone validation (supports Indian numbers)
        phone_pattern = r'^\+?91?[6-9]\d{9}$'
        return bool(re.match(phone_pattern, phone.replace('-', '').replace(' ', '')))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def _send_subscription_confirmation(self, channel: str, contact_info: str, action: str):
        """Send confirmation message for subscription"""
        try:
            confirmation_message = f"Your Akasa flight alert subscription has been {action}. You'll receive updates via {channel}."
            
            if channel == 'sms':
                self.send_sms(contact_info, confirmation_message)
            elif channel == 'email':
                self.send_email(contact_info, "Akasa Alert Subscription Confirmed", confirmation_message)
            elif channel == 'push':
                # For push, we'd need the user_id, but contact_info might not have it
                pass
                
        except Exception as e:
            logger.error(f"Error sending subscription confirmation: {str(e)}")
    
    def _format_alert_message(self, alert_data: Dict[str, Any], channel: str) -> str:
        """Format alert message for specific channel"""
        flight_number = alert_data.get('flight_number', 'Unknown')
        alert_type = alert_data.get('alert_type', 'ALERT')
        message = alert_data.get('message', 'Flight update available')
        
        if channel == 'sms':
            # Short format for SMS
            return f"Akasa Alert: {message}. Check app for details."
        elif channel == 'email':
            # Detailed format for email
            return f"""
            <h2>Akasa Airlines Flight Alert</h2>
            <p><strong>Flight:</strong> {flight_number}</p>
            <p><strong>Alert Type:</strong> {alert_type}</p>
            <p><strong>Message:</strong> {message}</p>
            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p>For more details, please visit the Akasa website or mobile app.</p>
            """
        else:  # push
            return message

# Global notification service instance
notification_service = NotificationService()