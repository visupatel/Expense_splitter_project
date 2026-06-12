from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
import random

def generate_token(user):
    token = RefreshToken()         # generate refreshtoken
    token['user_id'] = user.id
    token['username'] = user.username
    token['email'] = user.email
    token["token_version"] = user.token_version

    return token
    

def generate_otp(user):
    user.otp = random.randint(1000,9999)     # generate otp in 4 digit randomly
    user.otp_exp = timezone.now() + timedelta(minutes=10)      # otp valid for 10 minutes(current time + 10 min)
    user.save()
    return user