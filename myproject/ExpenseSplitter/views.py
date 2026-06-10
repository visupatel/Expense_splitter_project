from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.response import Response
from .models import Group,User
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework.views import APIView
from .validation import isValid_type

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getuser(request):
    try:
        user = request.user

        return Response({
            "status":"success",
            "message":"user data...",
            "user_id":user.id,
            "username":user.username
        },
        status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response({
            "message":str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    


class GroupView(APIView):
    permission_classes = [IsAuthenticated]

    # create a group and add member who create this group.
    def post(self,request):
        try:
            group_name = request.data.get('name')

            if not group_name:
                return Response({"status":"failed","message":"'name' must be required"},status=status.HTTP_400_BAD_REQUEST)
            
            if Group.objects.filter(name = group_name).exists():
                return Response({"status":"failed","message":f"'{group_name}' already exist, Enter another name"},status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                new_group = Group.objects.create(name = group_name)
                new_group.members.add(request.user)
                return Response({
                    "status":"success",
                    "message":f"'{group_name}' created successfully...."
                },
                status=status.HTTP_201_CREATED
                )
            
        except Exception as e:
            return Response({
                "status":"error",
                "message":str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # get group info only by group member.
    def get(self,request):
        try:
            group_id = request.data.get('group_id')
            if not group_id:
                return Response({"status":"failed","message":"'group_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
            
            group_id = isValid_type(int,group_id,"integer","group_id")
            group = Group.objects.get(id = group_id)
            
            if not group.members.filter(id = request.user.id).exists():
                return Response({"status":"failed","message":"You are not access this group becuase you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)
            
            group_members =  group.members.values("id","username","email")
           
            return Response({
                "status":"success",
                "message":"Group Info Fetched...",
                "data":{
                    "group_id":group.id,
                    "group_name":group.name,
                    "group_members":group_members,
                }
            },
            status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

        except Group.DoesNotExist:
            return Response({"status":"failed","message":"Group not found"},status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                "status":"error",
                "message":str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # update group
    def put(self,request):
        try:
            group_id = request.data.get('group_id')
            group_name = request.data.get('group_name')
            if not group_id:
                return Response({"status":"failed","message":"'group_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
            group_id = isValid_type(int,group_id,"integer","group_id")
            group = Group.objects.get(id = group_id)
            
            if not group.members.filter(id = request.user.id).exists():
                return Response({"status":"failed","message":"You are not access this group becuase you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)
            
            if group_name:
                if Group.objects.filter(name=group_name).exists():
                    return Response({"status":"failed","message":f"'{group_name}' already exist please enter another 'group_name'"},status=status.HTTP_400_BAD_REQUEST)
                
                group.name = group_name
                group.save()
            return Response({"status":"success","message":"Group updated successfully..."},status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

        except Group.DoesNotExist:
            return Response({"status":"failed","message":"Group not found"},status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                "status":"error",
                "message":str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # remove group 
    def delete(self,request):
        try:
            group_id = request.data.get('group_id')
            if not group_id:
                return Response({"status":"failed","message":"'group_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
            group_id = isValid_type(int,group_id,"integer","group_id")
            group = Group.objects.get(id = group_id)
            
            if not group.members.filter(id = request.user.id).exists():
                return Response({"status":"failed","message":"You are not access this group becuase you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)
                
            group.delete()
            return Response({"status":"success","message":"Group deleted successfully..."},status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

        except Group.DoesNotExist:
            return Response({"status":"failed","message":"Group not found"},status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                "status":"error",
                "message":str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# Member wants to exit from the group
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def exit_group(request):
    try:
        group_id = request.data.get('group_id')
        email = request.data.get('email')

        if not email:
            return Response({"status":"failed","message":"'email' must be required"},status=status.HTTP_400_BAD_REQUEST)

        if not group_id:
            return Response({"status":"failed","message":"'group_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
        group_id = isValid_type(int,group_id,"integer","group_id")
        group = Group.objects.get(id = group_id)
        
        if not group.members.filter(id = request.user.id).exists():
            return Response({"status":"failed","message":"You are not access this group becuase you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)

        member = group.members.get(email = email)
        group.members.remove(member)

        user = User.objects.get(email=email)
        if request.user.email == email:
            return Response({"status":"success","message":f"'{user.username}' exit from '{group.name}' group"},status=status.HTTP_200_OK)
        else:
            return Response({"status":"success","message":f"'{user.username}' remove by '{request.user}'"},status=status.HTTP_200_OK)
            
    except ValueError as e:
        return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
    except Group.DoesNotExist:
        return Response({"status":"failed","message":"Group not found"},status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        return Response({"status":"failed","message":f"{email} not in this group"},status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            "status":"error",
            "message":str(e)
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

