import string 
import secrets

def generate_short_code(length = 6):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))