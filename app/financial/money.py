"""
Safe Monetary Representation for myCA Financial Engine.
Mandate: Money must NEVER use binary floating point.
Uses Python Decimal with standard 2 decimal places (ROUND_HALF_UP).
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union, Any

# Standard 2-decimal quantizer for Indian Rupee currency
CURRENCY_QUANTIZER = Decimal('0.01')

def to_decimal(val: Any) -> Decimal:
    """
    Converts numbers, strings, or floats into an exact, quantized Decimal.
    Strips currency symbols (₹), commas, spaces, and handles None or empty values safely.
    """
    if val is None or val == "" or val == "—":
        return Decimal('0.00')
    
    if isinstance(val, Decimal):
        return val.quantize(CURRENCY_QUANTIZER, rounding=ROUND_HALF_UP)
    
    if isinstance(val, (int, float)):
        # Convert via str to avoid binary float artifacts
        return Decimal(str(val)).quantize(CURRENCY_QUANTIZER, rounding=ROUND_HALF_UP)
    
    # String cleanup
    clean_str = str(val).replace(',', '').replace('₹', '').replace(' ', '').replace('+', '').strip()
    if not clean_str:
        return Decimal('0.00')
    
    try:
        return Decimal(clean_str).quantize(CURRENCY_QUANTIZER, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError(f"Cannot convert '{val}' to safe monetary Decimal.")

def format_inr(val: Union[Decimal, float, int, str], include_symbol: bool = True) -> str:
    """
    Formats a decimal amount using standard Indian numbering system (Lakhs / Crores).
    Example: Decimal('127500.00') -> '₹1,27,500.00'
    """
    d = to_decimal(val)
    is_negative = d < 0
    d_abs = abs(d)
    
    parts = f"{d_abs:.2f}".split(".")
    integer_part = parts[0]
    decimal_part = parts[1]
    
    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        # Split remaining into groups of 2 from right to left
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last_three
    
    prefix = "-" if is_negative else ""
    sym = "₹" if include_symbol else ""
    return f"{prefix}{sym}{formatted_int}.{decimal_part}"
