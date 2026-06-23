from django.core.validators import validate_email
import re      # regular expression to check string pattern

def isValid_email(email):
    try:
        validate_email(email)     # raise error if email is invalid
        return email.lower()
    except:
        raise ValueError("Please enter 'email' in valid format(ex: example@gmail.com)")
    

# type conversion, if invalid type then raise ValueError
def isValid_type(type,value,type_field,value_field):      
    try:
        return type(value)
    except:
        raise ValueError(f"'{value_field}' must be in {type_field}")


# check validation for pagination
def check_pagination(page_number, page_size):
    if not page_number or not page_size:
        raise ValueError("'page_number' and 'page_size' must be required")
    
    page_number = isValid_type(int,page_number,"integer","page_number")
    page_size = isValid_type(int,page_size,"integer","page_size")
    
    if page_number <= 0 or page_size <= 0:
        raise ValueError("'page_number' and 'page_size' must be greater than 0")

    # handle memory usage and database load if thousands of page size given.
    if page_size > 100:
        raise ValueError("maximum 100 'page_size' is allowed")
    
    return (page_number,page_size)
    


# check password validation
def isValid_password(password):
    if " " in password:
        raise ValueError("Password must not contain spaces")
    
    if len(password) != 8:
        raise ValueError("Password must be 8 characters long")

    if not re.search(r'[A-Za-z]', password):
        raise ValueError("Password must contain at least one alphabet")

    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit")

    if not re.search(r'[!@#$%^&*_]', password):
        raise ValueError("Password must contain at least one special character(!,@,#,$,%,^,&,*,_)")

    return password