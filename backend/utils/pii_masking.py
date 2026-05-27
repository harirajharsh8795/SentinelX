import re

# Phase 12: Data Privacy & PII Masking
def mask_pii(text: str) -> str:
    """
    Masks Personally Identifiable Information (PII) before storage or processing.
    Ensures bank compliance with DPDP Act / GDPR data privacy guidelines.
    """
    if not text:
        return text
        
    # Mask Email Addresses
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL_MASKED]', text)
    
    # Mask Indian Phone Numbers (+91 or plain 10 digits)
    text = re.sub(r'(\+91[\-\s]?)?[6-9]\d{9}', '[PHONE_MASKED]', text)
    
    # Mask Aadhaar numbers (12 digits, optional spaces)
    text = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', '[AADHAAR_MASKED]', text)
    
    # Mask PAN Cards (5 letters, 4 digits, 1 letter)
    text = re.sub(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', '[PAN_MASKED]', text)
    
    # Mask Credit Card Numbers (16 digits)
    text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[CC_MASKED]', text)
    
    return text
