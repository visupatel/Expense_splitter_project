from django.utils import timezone
from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.response import Response
from .models import User,Group
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.db import transaction
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import update_last_login
from django.contrib.auth.hashers import make_password,check_password
from .token import generate_token,generate_otp
from .validation import isValid_email

# register
@api_view(['POST','GET'])
@permission_classes([AllowAny])
def userregister(request):
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
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
        
        if not isValid_email(email):
            return Response({
                "status":"failed",
                "message":" Please enter 'email' in valid format(ex: example@gmail.com)"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response({
                "status":"failed",
                "message":f"username '{username}' is already exist please enter another 'username'"
            },
            status=status.HTTP_208_ALREADY_REPORTED
            )

        if User.objects.filter(email=email).exists():
            return Response({
                "status":"failed",
                "message":f"email '{email}' is already exist please enter another 'email'"
            },
            status=status.HTTP_208_ALREADY_REPORTED
            )
        
        hashed_password = make_password(password)     
        #Turn a plain-text password into a hash for database storage

        user = User.objects.create(username=username,password=hashed_password,email=email)
        token = generate_token(user)   

        group_id = request.GET.get('group_id') 

        if group_id:
            group = Group.objects.get(id = group_id)
            group.members.add(user)
            return Response({
                "status":"success",
                "message":f"You are successfully joined in {group.name}"
            })

        return Response({
            "status":"success",
            "message":f"User '{username}' registered successfully...",
            "refresh":str(token),
            "access":str(token.access_token)
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
        
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR 
        )


# login
@api_view(['POST','GET'])
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

        if user is None or not check_password(password,user.password):
            return Response({
                "status":"failed",
                "message":"Invalid 'username' or 'password'"
            },
            status=status.HTTP_401_UNAUTHORIZED
            )
        update_last_login(None, user)
        token = generate_token(user)
        return Response({
            "status":"success",
            "message":f"User {username} loggin successfully....",
            "refresh":str(token),
            "access":str(token.access_token),
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
            })
        
        user = User.objects.get(email=email)

        user = generate_otp(user)
        return Response({
            "status":"success",
            "message":"OTP generated..",
            "OTP":user.otp,
            "Expired_in":"10 minutes"
        })
    
    except User.DoesNotExist:
        return Response({
            "status":"failed",
            "message":"Invalid email address please enter valid email."
        },
        status=status.HTTP_401_UNAUTHORIZED
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
        
        user = User.objects.get(email=email)

        if str(otp) != user.otp:
            return Response({
                "status":"failed",
                "message":"Invalid OTP please enter valid OTP"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.otp_exp < timezone.now():
            return Response({
                "status":"failed",
                "message":"OTP expired.."
            },
            status=status.HTTP_408_REQUEST_TIMEOUT
            )
        
        user.password = make_password(new_password)
        user.save()

        return Response({
            "status":"success",
            "message":"password reset successfully"
        },
        status=status.HTTP_205_RESET_CONTENT
        )
    
    except User.DoesNotExist:
            return Response({
                "status":"failed",
                "message":"Invalid email address please enter valid email."
            },
            status=status.HTTP_401_UNAUTHORIZED
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
            return Response({"status":"failed","message":"'refresh_token' must be required"})

        token = RefreshToken(refresh_token)
        token.blacklist()          
        return Response({"status":"success","message":"User logged out successfully"},status=status.HTTP_200_OK)
    
    except TokenError:
        return Response({"status":"success","message":"Token is already invalid,Logged out successfully"},status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


