from django.core.validators import validate_email

def isValid_email(email):
    try:
        validate_email(email)     # raise error if email is invalid
        return True
    except:
        return False
    

# type conversion, if invalid type then raise valueerror
def isValid_type(type,value,type_field,value_field):      
    try:
        return type(value)
    except:
        raise ValueError(f"'{value_field}' must be in {type_field}")
    
