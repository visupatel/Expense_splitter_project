from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.response import Response
from .models import Group,User
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.mail import send_mail
from .validation import isValid_type
from django.conf import settings
from .email_format import invitation_email,registration_email,welcome_email
from django.utils.html import strip_tags


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
        
        if group.admin != request.user:
            return Response(
                {
                    "status":"failed",
                    "message":"Only group admin can invite the people"
                },
                status=status.HTTP_403_FORBIDDEN
            )
    
        subject = f"Invited to join the '{group.name}' group"
    
        for email in emails:

            # create url for invitation
            invitation_link = request.build_absolute_uri(f'/api/invitation_link/{group.id}/{email}/')
            html_message = invitation_email(group, group.admin.username, invitation_link)
            
            # Remove all html tags and return plain text.
            message = strip_tags(html_message)     

            send_mail(
                subject=subject,
                message=message,      # If html not suppoted or for backup
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False        # fail_silently is used to prevent email to fail silently
            )

            
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
            "message":"Group not found."
        },
        status=status.HTTP_404_NOT_FOUND
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

        # if user is already member of the group
        if user_exist:
            return Response({
                "status":"failed",
                "message":f"User already in {group.name}"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        # if user is already rgistered in the app then add directly
        user = User.objects.get(email=email)
        group.members.add(user)
        
        html_message = welcome_email(user,group)
        message = strip_tags(html_message)

        send_mail(
            subject=f"Welcome to {group.name}",
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            html_message=html_message,
            recipient_list=[email],
            fail_silently=False

        )

        return Response({
            "status":"success",
            "message":"Welcome email send successfully..."
        },
        status=status.HTTP_200_OK
        )
    
    # if user is not registered in the app then send link for registration.
    except User.DoesNotExist:
        link = request.build_absolute_uri(f'/api/register/?group_id={group.id}&email={email}')
        html_message = registration_email(group,email,link)
        message = strip_tags(html_message)

        send_mail(
            subject=f"Welcome to {group.name}",
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            html_message=html_message,
            recipient_list=[email],
            fail_silently=False

        )
        return Response({
            "status":"success",
            "message":"Registered email send successfully..."
        },
        status=status.HTTP_200_OK
        )
        
    except Group.DoesNotExist:
        return Response({
            "status":"failed",
            "message":"Group not found"
        },
        status=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )






