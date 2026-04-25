"""
Royal Mail Click & Drop REST API Service Layer
Handles authentication, shipment creation, label generation and storage.
"""
import base64
import logging
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from orders.models import Order

logger = logging.getLogger(__name__)


# Country name to ISO code mapping
COUNTRY_CODE_MAP = {
    'united kingdom': 'GB',
    'great britain': 'GB',
    'england': 'GB',
    'scotland': 'GB',
    'wales': 'GB',
    'northern ireland': 'GB',
    'united states': 'US',
    'united states of america': 'US',
    'usa': 'US',
    'france': 'FR',
    'germany': 'DE',
    'spain': 'ES',
    'italy': 'IT',
    'netherlands': 'NL',
    'belgium': 'BE',
    'ireland': 'IE',
    'portugal': 'PT',
    'austria': 'AT',
    'switzerland': 'CH',
    'canada': 'CA',
    'australia': 'AU',
    'new zealand': 'NZ',
    'japan': 'JP',
    'china': 'CN',
    'india': 'IN',
    'brazil': 'BR',
    'south africa': 'ZA',
}

# Package format identifiers
PACKAGE_FORMATS = {
    'small': 'smallParcel',      # < 1kg, small items
    'medium': 'mediumParcel',    # 1-2kg, medium items
    'large': 'largeParcel',      # 2-5kg, large items
    'xlarge': 'xlargeParcel',    # > 5kg, heavy items
}


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
    
    def _get_country_code(self, country_name):
        """
        Convert country name to ISO 2-letter country code.
        
        Args:
            country_name: str - Country name (e.g., "United Kingdom", "GB")
            
        Returns:
            str: ISO country code (e.g., "GB")
        """
        if not country_name:
            return "GB"  # Default to UK
        
        # Check if already a valid 2-letter code
        if len(country_name) == 2:
            return country_name.upper()
        
        # Try to find in mapping
        normalized = country_name.lower().strip()
        if normalized in COUNTRY_CODE_MAP:
            return COUNTRY_CODE_MAP[normalized]
        
        # Log warning and default to GB
        logger.warning(f"Unknown country '{country_name}', defaulting to GB")
        return "GB"
    
    def _smart_split_address(self, address):
        """
        Intelligently split a long address across line1 and line2.
        Avoids cutting words in half - tries to split at logical breakpoints.
        
        Args:
            address: str - Full address string
            
        Returns:
            tuple: (line1, line2) - Split address lines
        """
        max_line_length = 35
        
        if not address:
            return ("", "")
        
        address = address.strip()
        
        # If short enough, no splitting needed
        if len(address) <= max_line_length:
            return (address, "")
        
        # Try to split at logical breakpoints
        split_points = [
            ', ',    # After comma
            '; ',    # After semicolon
            ' - ',   # After hyphen
            ' -',    # Before hyphen
            ' and ', # After "and"
        ]
        
        for split_char in split_points:
            if split_char in address:
                parts = address.split(split_char)
                line1 = parts[0].strip()
                line2 = split_char.join(parts[1:]).strip()
                
                # If first part is reasonable, use it
                if len(line1) <= max_line_length and len(line1) > 0:
                    # Truncate only if still too long
                    if len(line1) > max_line_length:
                        line1 = line1[:max_line_length].strip()
                    return (line1, line2[:35] if line2 else "")
        
        # Fallback: split at word boundary closest to middle
        words = address.split()
        line1_parts = []
        line2_parts = []
        
        for word in words:
            test_line1 = ' '.join(line1_parts)
            if len(test_line1) + len(word) + 1 <= max_line_length:
                line1_parts.append(word)
            else:
                line2_parts.append(word)
        
        line1 = ' '.join(line1_parts)
        line2 = ' '.join(line2_parts)
        
        # Last resort: hard truncate
        if len(line1) > max_line_length:
            line1 = line1[:max_line_length].strip()
        if len(line2) > max_line_length:
            line2 = line2[:max_line_length].strip()
        
        return (line1, line2)
    
    def _get_package_format(self, order):
        """
        Determine package format based on order weight.
        
        Args:
            order: Order model instance
            
        Returns:
            str: Package format identifier for Royal Mail
        """
        weight_kg = order.get_total_weight_kg()
        
        if weight_kg < 1:
            return "smallParcel"
        elif weight_kg < 2:
            return "mediumParcel"
        elif weight_kg < 5:
            return "largeParcel"
        else:
            return "xlargeParcel"
    
    def _build_shipment_payload(self, order):
        """
        Build the shipment payload for Royal Mail API.
        Ensures all fields meet Royal Mail's strict schema requirements.
        
        Args:
            order: Order model instance
            
        Returns:
            dict: Validated payload for Royal Mail API
        """
        # Smart address splitting (Issue #2 fix)
        address_line_1, address_line_2 = self._smart_split_address(order.address)
        
        # City goes to line2 if we have space, otherwise line3
        city = self._truncate_string(order.city, 35)
        state_postcode = self._truncate_string(f"{order.state} {order.postcode}", 30)
        
        # Combine city with state/postcode if line2 is empty
        if not address_line_2 and city:
            address_line_2 = city
        elif address_line_2 and city:
            # Append city to line3 if line2 is used
            state_postcode = f"{city}, {state_postcode}"[:30]
        
        # Weight must be an integer in grams
        weight_grams = int(order.get_total_weight_grams())
        
        # Get country code (Issue #1 fix)
        country_code = self._get_country_code(order.country)
        
        # Get package format (Issue #3 fix)
        package_format = self._get_package_format(order)
        
        payload = {
            "recipient": {
                "name": f"{order.first_name} {order.last_name}",
                "address": {
                    "line1": address_line_1,
                    "line2": address_line_2,
                    "line3": state_postcode,
                    "postcode": self._truncate_string(order.postcode, 8),
                    "countryCode": country_code,  # Use ISO code, not country name
                }
            },
            "weight": {
                "value": weight_grams,
                "unit": "grams"
            },
            "packageFormatIdentifier": package_format,  # Add package format
            "reference": order.order_number,
            "serviceCode": self._get_service_code(order),
        }
        
        logger.info(
            f"Built payload for order {order.order_number}: "
            f"weight={weight_grams}g, country={country_code}, format={package_format}"
        )
        
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
        Determine Royal Mail service code based on order weight.
        Uses product_weight field from Product model for calculations.
        
        Args:
            order: Order model instance
            
        Returns:
            str: Royal Mail service code based on weight category
        """
        weight_grams = order.get_total_weight_grams()
        
        # Royal Mail service codes based on weight
        # Adjust these codes to match your Royal Mail account services
        if weight_grams > 20000:  # > 20kg
            return "SR"  # Special Rate - for heavy items
        elif weight_grams > 5000:  # > 5kg
            return "TDP"  # Tracked Day Priority
        elif weight_grams > 2000:  # > 2kg
            return "TDN"  # Tracked Day/Night
        elif weight_grams > 1000:  # > 1kg
            return "TRN"  # Tracked Returns
        else:
            return "ST1D"  # Special Delivery 1st Class (≤1kg)
    
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
    
    @transaction.atomic
    def update_order_shipping(self, order, shipping_reference, label_base64):
        """
        Update order with shipping details after successful API call.
        Uses database transaction to ensure data consistency.
        
        Args:
            order: Order model instance
            shipping_reference: Shipment ID from Royal Mail
            label_base64: Base64 encoded label
            
        Raises:
            RoyalMailServiceException: If update fails
        """
        # Use select_for_update to prevent race conditions
        order_lock = Order.objects.select_for_update().get(pk=order.pk)
        
        try:
            # Decode and save label first
            label_url = self.decode_and_save_label(order_lock, label_base64)
            
            # Update order fields within the same transaction
            order_lock.shipping_reference = shipping_reference
            order_lock.label_url = label_url
            order_lock.shipping_status = 'label_generated'
            order_lock.shipping_created_at = timezone.now()
            order_lock.shipping_error_message = None
            order_lock.save()
            
            logger.info(f"Order {order_lock.order_number} updated with shipping details")
            
        except Exception as e:
            # If database fails, we want to know about it
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
