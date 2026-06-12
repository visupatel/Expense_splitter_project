from datetime import datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from .models import Group,Budget
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework.views import APIView
from .validation import isValid_type


class BudgetView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        try:
            group_id = request.data.get('group_id')
            category = request.data.get('category')
            amount = request.data.get('budget')
            date = request.data.get('date')

            if not group_id:
                return Response({"status":"failed","message":"'group_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
            if not category:
                return Response({"status":"failed","message":"'category' must be required"},status=status.HTTP_400_BAD_REQUEST)
            if not amount:
                return Response({"status":"failed","message":"'budget' must be required"},status=status.HTTP_400_BAD_REQUEST)
            if date:
                # check requested date is in (YYYY-MM-DD) format. If it is not then raise valueerror.
                date = datetime.strptime(date,"%Y-%m-%d").date()      # .date() give the date only not add time.
            else:
                date = timezone.now().date()         # current date

            date = date.replace(day=1)        # reaplace day into 1 date( ex: 2026-06-25 --> 2026-06-01)

            group_id = isValid_type(int,group_id,'integer',"group_id")
            group = Group.objects.get(id = group_id)
            
            if not group.members.filter(id = request.user.id).exists():    # to check authenticated user is in this group or not.
                return Response({
                "status": "failed",
                "message": "You cannot manage the budget because you are not a member of this group."
            }, 
            status=status.HTTP_401_UNAUTHORIZED
            )

            amount = isValid_type(float,amount,"decimal or integer","budget")
            if amount <= 0:
                return Response({"status":"failed","message":"'budget' amount must be greater than 0"},status=status.HTTP_400_BAD_REQUEST)
            
            category = category.strip().replace(" ","").capitalize()    # convert category in same format for all(ex:    luNCh  FoOD   -->Lunchfood)

            # If category for that group is already present then update only amount and date.
            """outside default fields are checked with and operators(group and category) if both is already 
            present then updated default fields only."""

            Budget.objects.update_or_create(group=group,category=category,defaults={"monthly_budget":amount,"date":date})
            return Response({"status":"success","message":"Budget created successfully..."},status=status.HTTP_200_OK)
    
        except ValueError as e:
            if "time data" in str(e):      # ValueError for date format
                return Response({"status":"failed","message":f"date '{date}' does not match the format 'YYYY-MM-DD'"},status=status.HTTP_400_BAD_REQUEST)

            # for type conversion
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        except Group.DoesNotExist:
            return Response({'status':"failed","message":"Group not found"},status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
    def get(self,request):
        try:
            budget_id = request.data.get('budget_id')
            if not budget_id:
                return Response({"status":"failed","message":"'budget_id' must be required"},status=status.HTTP_400_BAD_REQUEST)

            budget_id = isValid_type(int,budget_id,"integer","budget_id")

            budget = Budget.objects.get(id = budget_id)
            is_member = budget.group.members.filter(username = request.user.username).exists()
            if not is_member:
                return Response({"status":"failed","message":"You are not access this group becuase you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "status":"success",
                "message":"Budget info fetched....",
                "data":{
                    "id":budget.id,
                    "category":budget.category,
                    "monthly_budget":budget.monthly_budget,
                    "date":budget.date,
                    },
                },
                status=status.HTTP_200_OK
                )
        except ValueError as e:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        except Budget.DoesNotExist:
            return Response({'status':"failed","message":"Budget not found"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({str(e)})

    def put(self,request):
        try:
            budget_id = request.data.get('budget_id')
            category = request.data.get('category')
            amount = request.data.get('budget')
            date = request.data.get('date')

            if not budget_id:
                return Response({"status":"failed","message":"'budget_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
            
            budget_id = isValid_type(int,budget_id,'integer',"group_id")
            budget = Budget.objects.get(id = budget_id)
            
            is_member = budget.group.members.filter(username = request.user.username).exists()
            if not is_member:
                return Response({"status":"failed","message":"You are not access this group becuase you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)
            
            if category:
                category = category.strip().replace(" ","").capitalize()
                
                # check if the category is already exist for group and exclude current budget to being updated.
                if Budget.objects.filter(group = budget.group, category=category).exclude(id=budget.id).exists():
                    return Response({"status":"failed","message":f"'{category}' category name is aready exists try another cateory name."},status=status.HTTP_400_BAD_REQUEST)
                budget.category = category

            if amount:
                amount = isValid_type(float,amount,"decimal or integer","budget")
                if amount <= 0:
                    return Response({"status":"failed","message":"'budget' amount must be greater than 0"},status=status.HTTP_400_BAD_REQUEST)

                budget.monthly_budget = amount

            if date:
                date = datetime.strptime(date,'%Y-%m-%d')
                budget.date = date
            
            budget.save()
            return Response({"status":"success","message":"Budget updated successfully..."},status=status.HTTP_200_OK)
        
        except ValueError as e:
            if "time data" in str(e):
                return Response({"status":"failed","message":f"date '{date}' does not match the format 'YYYY-MM-DD'"},status=status.HTTP_400_BAD_REQUEST)

            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        except Group.DoesNotExist:
            return Response({'status':"failed","message":"Group not found"},status=status.HTTP_400_BAD_REQUEST)
        except Budget.DoesNotExist:
            return Response({'status':"failed","message":"Budget not found"},status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
    def delete(self,request):
        try:
            budget_id = request.data.get('budget_id')
            if not budget_id:
                return Response({"status":"failed","message":"'budget_id' must be required"},status=status.HTTP_400_BAD_REQUEST)

            budget_id = isValid_type(int,budget_id,"integer","budget_id")
            budget = Budget.objects.get(id = budget_id)
            
            is_member = budget.group.members.filter(username = request.user.username).exists()
            if not is_member:
                return Response({"status":"failed","message":"You are not access this group becuase you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)

            budget.delete()
            return Response({"status":"success","message":f"'{budget.category}' Budget deleted successfully.."},status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        except Budget.DoesNotExist:
            return Response({'status':"failed","message":"Budget not found"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)