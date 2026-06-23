from rest_framework.decorators import api_view,permission_classes
from rest_framework import status
from rest_framework.response import Response
from .models import Group,User
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .validation import isValid_email, isValid_type,check_pagination
from django.db.models import Q
from django.core.paginator import Paginator,EmptyPage

class GroupView(APIView):
    permission_classes = [IsAuthenticated]

    # create a group and add member who create this group.
    def post(self,request):
        try:
            group_name = request.data.get('name')

            if not group_name:
                return Response({"status":"failed","message":"'name' must be required"},status=status.HTTP_400_BAD_REQUEST)
            
            # handle duplication group name, to check group is already present or not.
            if Group.objects.filter(name = group_name).exists():  
                return Response({"status":"failed","message":f"'{group_name}' already exist, Enter another name"},status=status.HTTP_400_BAD_REQUEST)

            new_group = Group.objects.create(name = group_name, admin = request.user)
            new_group.members.add(request.user)
            return Response({
                "status":"success",
                "message":f"'{group_name}' group created successfully...."
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
    
    # get all group info where authenticated user is a group member.
    def get(self,request):
        try:
            group_id = request.data.get('group_id')
            search = request.data.get('search')
            page_number = request.data.get("page_number")
            page_size = request.data.get('page_size')

            page_number,page_size = check_pagination(page_number,page_size)
            
            # filtr group members by authenticated user
            groups = Group.objects.filter(members = request.user)
           
            if group_id:
                group_id = isValid_type(int,group_id,"integer","group_id")
                if group_id <= 0:
                    return Response({
                        "status":"failed",
                        "message":"'group_id' must be greater than 0"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                    )
                
                groups = groups.filter(id = group_id)

            if search:
                groups = groups.filter(Q(name__icontains=search)|Q(admin__username__icontains = search))

            # set queryset of groups for per page items
            paginator = Paginator(groups,page_size)

            # return a page object of given page number and raise Emptypage error if page has no content
            paginator_data = paginator.page(page_number)
        
            group_info = []
            for group in paginator_data:

                # return values of members
                group_members =  group.members.values("id","username","email")
                group_info.append({
                    "group_id":group.id,
                    "group_name":group.name,
                    "group_admin":group.admin.username,
                    "group_members":group_members,
                    "created_at":group.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                })
           
            return Response({
                "status":"success",
                "message":"Group Info Fetched...",
                "total_pages": paginator.num_pages,
                "current_page": page_number,
                "total_items": paginator.count,
                "group_info":group_info,
                
            },
            status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        except EmptyPage:
            return Response({"status":"failed" ,"message": "Page not found"},status=status.HTTP_404_NOT_FOUND)

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
            
            if group_id <= 0:
                return Response({
                    "status":"failed",
                    "message":"'group_id' must be greater than 0"
                },
                status=status.HTTP_400_BAD_REQUEST
                )
            
            group = Group.objects.get(id = group_id)
            
            if group.admin != request.user:
                return Response({
                    "status":"failed",
                    "message":"Only group admin can update the group"
                },
                status=status.HTTP_403_FORBIDDEN
                )  
                      
            if group_name:
                if Group.objects.filter(name=group_name).exclude(id=group.id).exists():
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

            if group_id <= 0:
                return Response({
                    "status":"failed",
                    "message":"'group_id' must be greater than 0"
                },
                status=status.HTTP_400_BAD_REQUEST
                )
            
            group = Group.objects.get(id = group_id)
            
            if group.admin != request.user:
                return Response({
                    "status":"failed",
                    "message":"Only group admin can delete the group"
                },
                status=status.HTTP_403_FORBIDDEN
                )   
                     
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



# tranfer admin role if admin wants to leave the group
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def transfer_admin(request):
    try:
        group_id = request.data.get('group_id')
        email = request.data.get('email')

        if not group_id or not email:
            return Response({
                "status":"failed",
                "message":"'group_id' and 'email' are required"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        group_id = isValid_type(int,group_id,"integer","group_id")
        if group_id <= 0:
            return Response({
                "status":"failed",
                "message":"'group_id' must be greater than 0"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        group = Group.objects.get(id=group_id)

        # Only admin can transfer role
        if group.admin != request.user:
            return Response({
                "status":"failed",
                "message":"Only admin can transfer admin role",
            },
            status=status.HTTP_403_FORBIDDEN
            )
        
        email = isValid_email(email)  
        if not group.members.filter(email=email).exists():
            return Response({
                "status":"failed",
                "message":"No member with this email address in this group"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        
        new_admin = group.members.get(email=email)

        group.admin = new_admin
        group.save()

        return Response({
            "status":"success",
            "message":f"Admin role transferred to {new_admin.username}"
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
        if group_id <= 0:
            return Response({
                "status":"failed",
                "message":"'group_id' must be greater than 0"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        group = Group.objects.get(id = group_id)

        if not group.members.filter(id = request.user.id).exists():
            return Response({"status":"failed","message":"You are not access this group becuase you are not the member of this group"},status=status.HTTP_403_FORBIDDEN)

        email = isValid_email(email)  
        member = group.members.get(email = email)

        # to check member is exit by it self or removed by any group member.
        if request.user.email == email: 
            
            # before leave the group, group admin assign role to other member
            if group.admin == request.user:
                return Response({
                    "status":"failed",
                    "message":"Group admin cannot leave the group. Transfer admin role first."
                },
                status=status.HTTP_400_BAD_REQUEST
                )
            
            group.members.remove(member)      # remove member from the group
            user = User.objects.get(email=email) 
            return Response({"status":"success","message":f"'{user.username}' exit from '{group.name}' group"},status=status.HTTP_200_OK)
        
        # User is trying to remove another member
        else:
            if group.admin != request.user:
                return Response({
                    "status":"failed",
                    "message":"Only admin can remove members"
                },
                status=status.HTTP_403_FORBIDDEN
                )

            group.members.remove(member)

            return Response({
                "status":"success",
                "message":f"'{member.username}' removed by {group.admin}"
            },
            status=status.HTTP_200_OK
            )
                    
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