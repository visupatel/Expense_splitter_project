from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
import random

def generate_token(user):
    token = RefreshToken()
    token['user_id'] = user.id
    token['username'] = user.username
    token['email'] = user.email

    return token
    

def generate_otp(user):
    user.otp = random.randint(1000,9999)
    user.otp_exp = timezone.now() + timedelta(minutes=10)
    user.save()
    return user