"""
Royal Mail Click & Drop REST API Service Layer
Handles authentication, shipment creation, label generation and storage.
"""
import base64
import logging
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)


class RoyalMailServiceException(Exception):
    """Base exception for Royal Mail service errors."""
    pass


class RoyalMailBadRequestException(RoyalMailServiceException):
    """Raised when API returns 400 Bad Request (validation error)."""
    pass


class RoyalMailServiceUnavailableException(RoyalMailServiceException):
    """Raised when API returns 503 Service Unavailable."""
    pass


class RoyalMailService:
    """
    Handles all interactions with Royal Mail Click & Drop REST API.
    
    Configuration via environment variables:
    - ROYAL_MAIL_API_URL: Base URL for Royal Mail API
    - ROYAL_MAIL_API_KEY: Bearer token for authentication
    - ROYAL_MAIL_REQUEST_TIMEOUT: Request timeout in seconds (default: 30)
    """
    
    def __init__(self):
        self.api_url = settings.ROYAL_MAIL_API_URL
        self.api_key = settings.ROYAL_MAIL_API_KEY
        self.timeout = getattr(settings, 'ROYAL_MAIL_REQUEST_TIMEOUT', 30)
        
        if not self.api_url or not self.api_key:
            raise RoyalMailServiceException(
                "Royal Mail API configuration missing. "
                "Set ROYAL_MAIL_API_URL and ROYAL_MAIL_API_KEY in settings."
            )
    
    def _get_headers(self):
        """Return HTTP headers with Bearer token authentication."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def _handle_response(self, response):
        """
        Handle HTTP response and raise appropriate exceptions.
        
        Args:
            response: requests.Response object
            
        Raises:
            RoyalMailBadRequestException: For 400 status
            RoyalMailServiceUnavailableException: For 503 status
            RoyalMailServiceException: For other errors
        """
        if response.status_code == 400:
            logger.error(f"Royal Mail Bad Request: {response.text}")
            raise RoyalMailBadRequestException(
                f"Invalid request data: {response.text}"
            )
        elif response.status_code == 503:
            logger.error("Royal Mail Service Unavailable")
            raise RoyalMailServiceUnavailableException(
                "Royal Mail API is temporarily unavailable. Please try again later."
            )
        elif not response.ok:
            logger.error(
                f"Royal Mail API error [{response.status_code}]: {response.text}"
            )
            raise RoyalMailServiceException(
                f"API error [{response.status_code}]: {response.text}"
            )
        
        return response
    
    def create_shipment(self, order):
        """
        Create a shipment in Royal Mail and generate a label.
        
        Args:
            order: Order model instance with validated address and weight data
            
        Returns:
            dict: Response containing shipping_reference and label_base64
            {
                'shipping_reference': str,
                'label_base64': str,
                'tracking_number': str (optional)
            }
            
        Raises:
            RoyalMailBadRequestException: If address/data is invalid
            RoyalMailServiceUnavailableException: If service is down
            RoyalMailServiceException: For other API errors
            RequestException: For network/connection errors
        """
        try:
            # Prepare shipment payload - Royal Mail has strict schema requirements
            payload = self._build_shipment_payload(order)
            
            logger.info(f"Creating Royal Mail shipment for order {order.order_number}")
            
            response = requests.post(
                f"{self.api_url}/shipments",
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            # Handle response and raise appropriate exceptions
            response = self._handle_response(response)
            data = response.json()
            
            logger.info(f"Shipment created successfully: {data.get('shipmentId')}")
            
            return {
                'shipping_reference': data.get('shipmentId'),
                'label_base64': data.get('label'),
                'tracking_number': data.get('trackingNumber', data.get('shipmentId')),
            }
            
        except Timeout:
            logger.error(f"Royal Mail API timeout for order {order.order_number}")
            raise RoyalMailServiceException("API request timed out")
        except ConnectionError as e:
            logger.error(f"Connection error with Royal Mail API: {str(e)}")
            raise RoyalMailServiceException("Failed to connect to Royal Mail API")
        except RequestException as e:
            logger.error(f"Request error with Royal Mail API: {str(e)}")
            raise RoyalMailServiceException(f"Request error: {str(e)}")
    
    def _build_shipment_payload(self, order):
        """
        Build the shipment payload for Royal Mail API.
        Ensures all fields meet Royal Mail's strict character limits and formatting.
        
        Args:
            order: Order model instance
            
        Returns:
            dict: Validated payload for Royal Mail API
        """
        # Royal Mail has strict address line character limits
        # Line 1: max 35 chars, Line 2: max 35 chars, Line 3: max 30 chars
        address_line_1 = self._truncate_string(order.address, 35)
        address_line_2 = self._truncate_string(order.city, 35)
        address_line_3 = self._truncate_string(f"{order.state} {order.postcode}", 30)
        
        # Weight must be an integer in grams
        weight_grams = int(order.get_total_weight_grams())
        
        payload = {
            "recipient": {
                "name": f"{order.first_name} {order.last_name}",
                "address": {
                    "line1": address_line_1,
                    "line2": address_line_2,
                    "line3": address_line_3,
                    "postcode": self._truncate_string(order.postcode, 8),
                    "country": order.country,
                }
            },
            "weight": {
                "value": weight_grams,
                "unit": "grams"
            },
            "reference": order.order_number,
            "serviceCode": self._get_service_code(order),
        }
        
        return payload
    
    @staticmethod
    def _truncate_string(value, max_length):
        """Safely truncate string to max length for Royal Mail API."""
        if not value:
            return ""
        value_str = str(value).strip()
        if len(value_str) > max_length:
            logger.warning(
                f"Truncating address field from {len(value_str)} to {max_length} chars"
            )
            return value_str[:max_length].strip()
        return value_str
    
    @staticmethod
    def _get_service_code(order):
        """
        Determine Royal Mail service code based on order.
        Can be enhanced with order attributes like weight, urgency, etc.
        
        Args:
            order: Order model instance
            
        Returns:
            str: Royal Mail service code (e.g., 'ST1D', 'ST2D', 'RM1', etc.)
        """
        # Default to Royal Mail Special Delivery Guaranteed by 1pm (ST1D)
        # Customize based on your business requirements
        weight_grams = order.get_total_weight_grams()
        
        if weight_grams > 20000:  # > 20kg
            # Requires different service - adjust as needed
            return "SR"  # Special Rate
        
        return "ST1D"  # Default: Special Delivery 1st Class
    
    def decode_and_save_label(self, order, label_base64):
        """
        Decode Base64 label from Royal Mail and save as PDF file.
        
        Args:
            order: Order model instance
            label_base64: Base64 encoded label string from Royal Mail
            
        Returns:
            str: Path/URL of saved label file
            
        Raises:
            RoyalMailServiceException: If decoding or saving fails
        """
        try:
            # Decode Base64 to binary
            label_binary = base64.b64decode(label_base64)
            
            # Create Django ContentFile
            label_file = ContentFile(label_binary, name=f"{order.order_number}_label.pdf")
            
            # Save to order
            order.label_file.save(f"{order.order_number}_label.pdf", label_file)
            order.save(update_fields=['label_file'])
            
            logger.info(f"Label saved for order {order.order_number}")
            
            return order.label_file.url if order.label_file else None
            
        except Exception as e:
            logger.error(f"Failed to decode/save label for order {order.order_number}: {str(e)}")
            raise RoyalMailServiceException(f"Failed to process label: {str(e)}")
    
    def update_order_shipping(self, order, shipping_reference, label_base64):
        """
        Update order with shipping details after successful API call.
        
        Args:
            order: Order model instance
            shipping_reference: Shipment ID from Royal Mail
            label_base64: Base64 encoded label
            
        Raises:
            RoyalMailServiceException: If update fails
        """
        try:
            # Decode and save label
            label_url = self.decode_and_save_label(order, label_base64)
            
            # Update order fields
            order.shipping_reference = shipping_reference
            order.label_url = label_url
            order.shipping_status = 'label_generated'
            order.shipping_created_at = timezone.now()
            order.shipping_error_message = None
            order.save()
            
            logger.info(f"Order {order.order_number} updated with shipping details")
            
        except Exception as e:
            logger.error(f"Failed to update order shipping: {str(e)}")
            raise RoyalMailServiceException(f"Failed to update order: {str(e)}")
    
    def handle_shipment_error(self, order, error_message):
        """
        Update order with error status and message.
        
        Args:
            order: Order model instance
            error_message: Error details
        """
        order.shipping_status = 'failed'
        order.shipping_error_message = error_message
        order.save(update_fields=['shipping_status', 'shipping_error_message'])
        
        logger.error(f"Shipping failed for order {order.order_number}: {error_message}")
