import re

def validate_phone(phone: str) -> bool:
    """
    Basic phone number validation.
    """
    pattern = re.compile(r"^\+?[1-9]\d{1,14}$")
    return bool(pattern.match(phone))

def validate_email_domain(email: str, allowed_domains: list[str]) -> bool:
    """
    Check if email belongs to allowed domains (e.g., college domains).
    """
    domain = email.split('@')[-1]
    return domain in allowed_domains
