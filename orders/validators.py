"""
Validation utilities for Royal Mail API integration.
Ensures order data meets Royal Mail's strict schema requirements before API calls.
"""
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class RoyalMailValidator:
    """Validates order data against Royal Mail API requirements."""
    
    # Royal Mail address field character limits
    ADDRESS_LIMITS = {
        'line1': 35,
        'line2': 35,
        'line3': 30,
        'postcode': 8,
    }
    
    # Royal Mail name field limits
    NAME_LIMIT = 30
    
    # Weight constraints
    MIN_WEIGHT_GRAMS = 1
    MAX_WEIGHT_GRAMS = 20000  # 20kg
    
    @classmethod
    def validate_order_for_shipping(cls, order):
        """
        Comprehensive validation of order data for Royal Mail shipment creation.
        
        Args:
            order: Order model instance
            
        Returns:
            dict: {'valid': bool, 'errors': list, 'warnings': list}
            
        Raises:
            ValidationError: If critical validations fail
        """
        errors = []
        warnings = []
        
        # Validate shipping status fields
        if order.shipping_status != 'pending':
            errors.append(
                f"Order {order.order_number} already has shipping status: {order.shipping_status}"
            )
        
        # Validate recipient name
        full_name = f"{order.first_name} {order.last_name}"
        if not full_name.strip():
            errors.append("First name and last name are required")
        elif len(full_name) > cls.NAME_LIMIT:
            warnings.append(
                f"Recipient name '{full_name}' exceeds {cls.NAME_LIMIT} chars. Will be truncated."
            )
        
        # Validate address
        cls._validate_address(order, errors, warnings)
        
        # Validate weight
        cls._validate_weight(order, errors, warnings)
        
        # Validate required order items
        if not order.items.exists():
            errors.append("Order has no items. Cannot create shipment.")
        
        if errors:
            error_msg = "; ".join(errors)
            logger.error(f"Order {order.order_number} validation failed: {error_msg}")
            raise ValidationError(error_msg)
        
        if warnings:
            logger.warning(f"Order {order.order_number} warnings: {'; '.join(warnings)}")
        
        return {
            'valid': True,
            'errors': errors,
            'warnings': warnings,
        }
    
    @classmethod
    def _validate_address(cls, order, errors, warnings):
        """Validate address fields against Royal Mail limits."""
        address_field = order.address
        city_field = order.city
        state_field = order.state
        postcode_field = order.postcode
        country_field = order.country
        
        # Check required fields
        if not address_field or not address_field.strip():
            errors.append("Address (line 1) is required")
        if not city_field or not city_field.strip():
            errors.append("City is required")
        if not postcode_field or not postcode_field.strip():
            errors.append("Postcode is required")
        if not country_field or not country_field.strip():
            errors.append("Country is required")
        
        # Check length limits and warn if truncation needed
        if address_field and len(address_field) > cls.ADDRESS_LIMITS['line1']:
            warnings.append(
                f"Address line 1 ({len(address_field)} chars) exceeds "
                f"{cls.ADDRESS_LIMITS['line1']} chars. Will be truncated."
            )
        
        if city_field and len(city_field) > cls.ADDRESS_LIMITS['line2']:
            warnings.append(
                f"City ({len(city_field)} chars) exceeds "
                f"{cls.ADDRESS_LIMITS['line2']} chars. Will be truncated."
            )
        
        state_postcode = f"{state_field} {postcode_field}".strip()
        if len(state_postcode) > cls.ADDRESS_LIMITS['line3']:
            warnings.append(
                f"State/Postcode ({len(state_postcode)} chars) exceeds "
                f"{cls.ADDRESS_LIMITS['line3']} chars. Will be truncated."
            )
        
        if postcode_field and len(postcode_field) > cls.ADDRESS_LIMITS['postcode']:
            warnings.append(
                f"Postcode ({len(postcode_field)} chars) exceeds "
                f"{cls.ADDRESS_LIMITS['postcode']} chars. Will be truncated."
            )
    
    @classmethod
    def _validate_weight(cls, order, errors, warnings):
        """Validate order weight is within Royal Mail limits."""
        try:
            weight_grams = int(order.get_total_weight_grams())
        except (ValueError, TypeError):
            errors.append("Cannot calculate order weight")
            return
        
        if weight_grams < cls.MIN_WEIGHT_GRAMS:
            errors.append(f"Order weight ({weight_grams}g) is below minimum {cls.MIN_WEIGHT_GRAMS}g")
        elif weight_grams > cls.MAX_WEIGHT_GRAMS:
            errors.append(
                f"Order weight ({weight_grams}g) exceeds maximum {cls.MAX_WEIGHT_GRAMS}g. "
                "Product may not be eligible for standard Royal Mail services."
            )
    
    @classmethod
    def get_validation_summary(cls, order):
        """
        Get a human-readable validation summary for the order.
        Useful for debugging/logging.
        
        Args:
            order: Order model instance
            
        Returns:
            str: Formatted validation summary
        """
        summary = f"""
        Order: {order.order_number}
        Recipient: {order.first_name} {order.last_name}
        Address: {order.address}, {order.city}, {order.state} {order.postcode}
        Country: {order.country}
        Total Weight: {order.get_total_weight_grams()}g
        Items: {order.items.count()}
        """
        return summary.strip()
