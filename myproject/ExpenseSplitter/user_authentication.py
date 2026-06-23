from django.utils import timezone
from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.response import Response
from .models import User,Group
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password,check_password
from .token import generate_token,generate_otp
from .validation import isValid_email, isValid_password
from django.core.mail import send_mail
from django.conf import settings
from .email_format import otp_email
from django.utils.html import strip_tags
from django.db import transaction


# register
@api_view(['POST'])
@permission_classes([AllowAny])
def userregister(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.GET.get('email')      # get email directly from the url

        # first check url email
        if not email:
            email = request.data.get('email')

        group_id = request.GET.get('group_id')     # to get group_id directly from the url parameter
        
        if not username or not password:
            return Response({
                "status":"failed",
                "message":"'username' and 'password' must be required",
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        if not email:
            return Response({
                "status":"failed",
                "message":"'email' must be required"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response({
                "status":"failed",
                "message":f"username '{username}' is already exist please enter another 'username'"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        # check email format(validation.py)
        email = isValid_email(email)     

        if User.objects.filter(email=email).exists():
            return Response({
                "status":"failed",
                "message":f"email '{email}' is already exist please enter another 'email'"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        password = isValid_password(password)
        
        #Turn a plain-text password into a hash for database storage
        hashed_password = make_password(password)     

        # prenvent user to register if group_id is invalid or not exist
        with transaction.atomic():
            user = User.objects.create(username=username,password=hashed_password,email=email)

            message = f"User '{username}' registered successfully..."
            
            if group_id:
                group = Group.objects.get(id = group_id)
                group.members.add(user)
                message += f"You are successfully joined in {group.name}"

        return Response({
            "status":"success",
            "message":message,
        },
        status=status.HTTP_201_CREATED
        )
    
    except Group.DoesNotExist:
        return Response({
            "status":"failed",
            "message":"No such group exist."
        },
        status=status.HTTP_400_BAD_REQUEST
        )
    
    except ValueError as e:
        return Response({
            "status":"failed",
            "message":str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR 
        )


# login
@api_view(['POST'])
@permission_classes([AllowAny])
def userlogin(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                "status":"failed",
                "message":"'usename' and 'password' must be required",
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        
        # check_password is convert requested password in hash and compare with user db password.
        if user is None or not check_password(password,user.password):
            return Response({
                "status":"failed",
                "message":"Invalid 'username' or 'password'"
            },
            status=status.HTTP_401_UNAUTHORIZED
            )
        
        # update the last_login date if user logging in.
        user.last_login = timezone.now()

        user.token_version += 1
        user.save()

        # genrate token(token.py)
        token = generate_token(user)
        return Response({
            "status":"success",
            "message":f"User {username} loggin successfully....",
            "refresh":str(token),
            "access":str(token.access_token),      # convert refresh token into access token
        },
        status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# forgot password
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    try:
        email = request.data.get('email')
        if not email:
            return Response({
                "status":"failed",
                "message":"'email' must be required"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        email = isValid_email(email)  

        user = User.objects.get(email=email)

        user = generate_otp(user)      # generate otp(token.py)
        subject = f"{timezone.now().date()} - Forgot Password isValid OTP"
        html_message = otp_email(user,user.otp)

        message = strip_tags(html_message)
       
        # send otp email to the user 
        send_mail(
            subject,
            message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False)
        
        return Response({
            "status":"success",
            "message":"OTP send successfully..",
        },
        status=status.HTTP_200_OK
        )
    
    except User.DoesNotExist:
        return Response({
            "status":"failed",
            "message":"Invalid email address please enter valid email."
        },
        status=status.HTTP_401_UNAUTHORIZED
        )
    
    except ValueError as e:
        return Response({
            "status":"failed",
            "message":str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

# reset password
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    try:
        otp = request.data.get('otp')
        email = request.data.get('email')
        new_password = request.data.get('new_password')

        if not otp:
            return Response({
                "status":"failed",
                "message":"'otp' must be required"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        if not email:
            return Response({
                "status":"failed",
                "message":"'email' must be required"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        if not new_password:
            return Response({
                "status":"failed",
                "message":"'new_password' must be required"
            },
            status=status.HTTP_400_BAD_REQUEST
            )

        email = isValid_email(email)

        user = User.objects.get(email=email)

        if str(otp) != user.otp:        # if otp is not mached.
            return Response({
                "status":"failed",
                "message":"Invalid OTP or email please enter valid OTP and email"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.otp_exp or user.otp_exp < timezone.now():    # if time is greater than 10 minutes then otp is expired.
            return Response({
                "status":"failed",
                "message":"OTP expired.."
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        new_password = isValid_password(new_password)
        
        user.password = make_password(new_password)
        user.token_version += 1    # to make old access token invalid
        user.otp = None       # Again set otp to none in db 
        user.otp_exp = None   
        user.save()

        return Response({
            "status":"success",
            "message":"password reset successfully"
        },
        status=status.HTTP_200_OK
        )
    
    except User.DoesNotExist:
            return Response({
                "status":"failed",
                "message":"Invalid email address please enter valid email."
            },
            status=status.HTTP_401_UNAUTHORIZED
            )
    
    except ValueError as e:
        return Response({
            "status":"failed",
            "message":str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
            )

    
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# logout
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({"status":"failed","message":"'refresh_token' must be required"},status=status.HTTP_400_BAD_REQUEST)

        """requested refresh_token is a plain text string so RefreshToken() isValid
        that token and convert that string into object"""
        token = RefreshToken(refresh_token) 
    
        # if refresh token is not for authenticated user
        if token["user_id"] != request.user.id:
            return Response({
                "status":"failed",
                "message":"Invalid refresh token."
            }, 
            status=status.HTTP_403_FORBIDDEN
            )  

        # store refresh token in db blacklist so user can not generete access token with that refresh token 
        token.blacklist()  

        # to make access token invalid.
        user = User.objects.get(id = request.user.id)
        user.token_version += 1
        user.save()

        return Response({"status":"success","message":"User logged out successfully"},status=status.HTTP_200_OK)
    
    # if refresh token is already expired then raise tokenerror. TokenError catches expired,invalid or tampered tokens
    except TokenError:
        return Response({"status":"success","message":"Token is already invalid,Logged out successfully"},status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )