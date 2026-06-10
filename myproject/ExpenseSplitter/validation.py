from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def isValid_email(email):
    try:
        validate_email(email)
        return True
    except:
        return False
    

def isValid_type(type,value,type_field,value_field):
    try:
        return type(value)
    except:
        raise ValueError(f"'{value_field}' must be in {type_field}")