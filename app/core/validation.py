import re

def validate_email_format(email: str) -> bool:
    """
    Validates the format of an email address using a robust regex pattern.
    Rules:
    - Exactly one '@' symbol
    - Local part can contain letters, numbers, and ._%+-
    - Domain part can contain letters, numbers, hyphens, and periods
    - Extension must be letters-only, minimum 2 characters
    - No spaces allowed
    """
    if not email:
        return False
    
    cleaned_email = str(email).strip()
    if not cleaned_email:
        return False
        
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, cleaned_email))

def validate_cin_format(cin: str) -> bool:
    """
    Validates that CIN is exactly 8 digits.
    """
    if not cin:
        return False
    cleaned_cin = str(cin).strip()
    return bool(re.match(r"^\d{8}$", cleaned_cin))

def validate_phone_format(phone: str) -> bool:
    """
    Validates Tunisian mobile phone numbers:
    - Exactly 8 digits
    - Starts with 20/21/22/50/51/52/53/90/91/92
    """
    if not phone:
        return False
    cleaned_phone = str(phone).strip()
    # Strip optional +216 prefix if the user typed it (for backward compat/flexibility)
    if cleaned_phone.startswith("+216"):
        cleaned_phone = cleaned_phone[4:].strip()
    elif cleaned_phone.startswith("00216"):
        cleaned_phone = cleaned_phone[5:].strip()
        
    pattern = r"^(20|21|22|50|51|52|53|90|91|92)\d{6}$"
    return bool(re.match(pattern, cleaned_phone))
