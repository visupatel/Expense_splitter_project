from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.response import Response
from .models import Group,User
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.mail import send_mail
from .validation import isValid_type


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invitation_link(request):
    try:
        group_id = request.data.get('group_id')
        emails = request.data.get('emails')

        if not group_id:
            return Response({"status":"failed","message":"'group_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
           
        if not emails:
            return Response({"status":"failed","message":"'emails' must be required"},status=status.HTTP_400_BAD_REQUEST)
       
        group_id = isValid_type(int,group_id,"integer","group_id")
        group = Group.objects.get(id = group_id)
        emails = emails.split(",")
        
        if not group.members.filter(id = request.user.id).exists():
            return Response({
                "status": "failed",
                "message": f"You cannot invite people to '{group.name}' because you are not a member of this group."
            }, 
            status=status.HTTP_401_UNAUTHORIZED
            )
    
        inviter_name = request.user.username
        inviter_mail = request.user.email
        subject = f"Invited to join the '{group.name}' group"
    
        for email in emails:
            invitation_link = request.build_absolute_uri(f'/api/invitation_link/{group.id}/{email}/')
            message = f"Hello Dear,\n\n{inviter_name} invited you to join the '{group.name}' group.To join the group please click on below link.\n{invitation_link}"
            send_mail(subject=subject,message=message,from_email=inviter_mail,recipient_list=[email],fail_silently=False)

        return Response({
            "status":"success",
            "message":"Send invitation mail successfully...",
        },
        status=status.HTTP_200_OK
        )
    
    except ValueError as e:
        return Response({
            "status":"failed",
            "message":str(e)
        },
        status=status.HTTP_400_BAD_REQUEST
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



@api_view(['POST','GET'])
@permission_classes([AllowAny])
def join_group(request,group_id,email):

    try:
        group = Group.objects.get(id = group_id)
        user_exist = group.members.filter(email=email).exists()
        if user_exist:
            return Response({
                "status":"failed",
                "message":f"User already in {group.name}"
            },
            status=status.HTTP_208_ALREADY_REPORTED
            )
        
        user = User.objects.get(email=email)
        group.members.add(user)
        return Response({
            "status":"success",
            "message":f"Welcome! You are joined in '{group.name}' group. Now you are member of '{group.name}'"
        },
        status=status.HTTP_202_ACCEPTED
        )
        
    except User.DoesNotExist:
        link = request.build_absolute_uri(f'/api/register/?group_id={group.id}')
        return Response({
            "status":"success",
            "message":f"May be you don't register yet. Please register via below link.\nregister_link:{link}"
        },
        status=status.HTTP_202_ACCEPTED
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

