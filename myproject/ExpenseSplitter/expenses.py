from datetime import datetime
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.response import Response
from .models import Group,User,Expense,Budget,ExpenseSplit
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework.views import APIView
from .validation import isValid_type
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework.decorators import api_view,permission_classes
from decimal import Decimal



class ExpenseView(APIView):
    def send_alert(self,group,item):
        if Budget.objects.filter(group = group,category = item).exists():
            budget = Budget.objects.get(group = group,category = item)
            expense = Expense.objects.filter(item=item)
            
            sum = 0
            for amount in expense:
                if (amount.date.month == budget.date.month and amount.date.year == budget.date.year):
                    sum += amount.amount_paid
                    
            if sum >= budget.monthly_budget:
                member_emails = [email['email'] for email in group.members.values("email")]
                for email in member_emails:
                    subject = "Alert Message"
                    message = f"Alert, Budget out of limit.\nYour limit for {budget.category} = {budget.monthly_budget} but now your total amount for {item} = {sum} "
                    send_mail(subject,message,from_email="expense_system@gmail.com",recipient_list=[email],fail_silently=False)

    def post(self,request):
        try:
            group_id = request.data.get('group_id')
            item = request.data.get('item')
            amount = request.data.get('total_amount')
            paid_by = request.data.get('paid_by')
            skipped_member = request.data.get('skipped_members')
            date = request.data.get('date')
            receipt = request.FILES.getlist('receipt')

            if not group_id:
                return Response({"status":"failed","message":"'group_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
            if not item:
                return Response({"status":"failed","message":"'item' must be required"},status=status.HTTP_400_BAD_REQUEST)
            if not amount:
                return Response({"status":"failed","message":"'total_amount' must be required"},status=status.HTTP_400_BAD_REQUEST)
            if not paid_by:
                return Response({"status":"failed","message":"'paid_by' must be required"},status=status.HTTP_400_BAD_REQUEST)
            
            group_id = isValid_type(int,group_id,"integer","group_id")
            amount = isValid_type(float,amount,"decimal or integer","total_amount")
            item = item.strip().replace(" ","").capitalize()
            
            group = Group.objects.get(id = group_id)
            paid_by = isValid_type(int,paid_by,"integer","paid_by")
            user = User.objects.get(id = paid_by)
            
            if not group.members.filter(id = request.user.id).exists():
                return Response({"status":"failed","message":"You are not access this group because you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)

            if not group.members.filter(id = paid_by).exists():
                return Response({"status":"failed","message":f"{user.username} is not a member of this group"},status=status.HTTP_400_BAD_REQUEST)

            members = []
            if skipped_member:
                for member in skipped_member.split(","):
                    if not group.members.filter(id = member).exists():
                        return Response({"status":"failed","message":f"{member} is not a member of this group"},status=status.HTTP_400_BAD_REQUEST)
                    skipped = User.objects.get(id = member)
                    members.append(skipped)

            if date:
                date = datetime.strptime(date,"%Y-%m-%d").date()
            else:
                date = timezone.now()
            
            images = []
            if receipt:
                for img in receipt:
                    save_path = default_storage.save(f"reciept_images/{item}/{img}",img)
                    new_img = default_storage.url(save_path)
                    images.append(new_img)
            
            with transaction.atomic():
                expense = Expense.objects.create(group=group,item=item,amount_paid=amount,paid_by=user,date=date,receipt=images)
                expense.skipped_member.set(members)
                self.send_alert(group,item)
                return Response({"status":"success","message":"Expense created successfully..."},status=status.HTTP_200_OK)

        except ValueError as e:
            if "time data" in str(e):
                return Response({"status":"failed","message":f"date  does not match the format 'YYYY-MM-DD'"},status=status.HTTP_400_BAD_REQUEST)
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        except Group.DoesNotExist:
            return Response({'status':"failed","message":"Group not found"},status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'status':"failed","message":"User not found"},status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self,request):
        try:
            expense_id = request.data.get('expense_id')
            if not expense_id:
                return Response({"status":"failed","message":"'expense_id' must be required"})
            
            expense_id = isValid_type(int,expense_id,'integer','expense_id')
            expense = Expense.objects.get(id = expense_id)
            if not expense.group.members.filter(id = request.user.id).exists():
                return Response({"status":"failed","message":"You can not access this group because you are not the member of this group"})
            
            skipped_members = [val['id'] for val in expense.skipped_member.values("id")]
            return Response({
                "status":"success",
                "message":"Expense fetched",
                "data":{
                    "id":expense.id,
                    "group":expense.group.name,
                    "item":expense.item,
                    "total_amount":expense.amount_paid,
                    "paid_by":expense.paid_by.username,
                    "skipped_members":skipped_members,
                    "date":expense.date,
                    "receipt":expense.receipt
                    }
                },
                status=status.HTTP_200_OK
                )
        
        except ValueError as e:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        except Expense.DoesNotExist:
            return Response({"status":"failed","message":"Expense not found"},status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self,request):
        try:
            expense_id = request.data.get('expense_id')
            item = request.data.get('item')
            amount = request.data.get('total_amount')
            paid_by = request.data.get('paid_by')
            skipped_member = request.data.get('skipped_members')
            date = request.data.get('date')
            reciept = request.FILES.getlist('receipt')

            if not expense_id:
                return Response({"status":"failed","message":"'expense_id' must be required"})
            
            expense_id = isValid_type(int,expense_id,"integer","expese_id")
            expense = Expense.objects.get(id = expense_id)
            if not expense.group.members.filter(id = request.user.id).exists():
                return Response({"status":"failed","message":"You can not access this group because you are not the member of this group"})

            if item:
                item = item.strip().replace(" ","").capitalize()
                expense.item = item

            if amount:
                amount = isValid_type(float,amount,"decimal or integer","total_amount")
                expense.amount_paid = amount
            
            if paid_by:
                if not expense.group.members.filter(id = paid_by).exists():
                    return Response({"status":"failed","message":f"{paid_by} is not a member of this group"},status=status.HTTP_400_BAD_REQUEST)
                user = expense.group.members.get(id = paid_by)
                expense.paid_by = user

            if skipped_member:
                members = []
                for member in skipped_member.split(","):
                    if not expense.group.members.filter(id = member).exists():
                        return Response({"status":"failed","message":f"{member} is not a member of this group"},status=status.HTTP_400_BAD_REQUEST)
                    skipped = User.objects.get(id = member)
                    members.append(skipped)
                expense.skipped_member.set(members)

            if date:
                date = datetime.strptime(date,"%Y-%m-%d").date()
                expense.date = date

            if reciept:
                images = []
                for img in reciept:
                    save_path = default_storage.save(f"reciept_images/{item}/{img}",img)
                    new_img = default_storage.url(save_path)
                    images.append(new_img)
                expense.receipt = images

            with transaction.atomic():
                expense.save()
                self.send_alert(group=expense.group,item=item)
                return Response({"status":"success","message":"Expense updated successfully..."},status=status.HTTP_200_OK)


        except ValueError as e:
            if "time data" in str(e):
                return Response({"status":"failed","message":f"date  does not match the format 'YYYY-MM-DD'"},status=status.HTTP_400_BAD_REQUEST)
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

        except Expense.DoesNotExist:
            return Response({"status":"failed","message":"Expense not found"},status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self,request):
        try:
            expense_id = request.data.get('expense_id')
            if not expense_id:
                return Response({"status":"failed","message":"'expense_id' must be required"})
            
            expense_id = isValid_type(int,expense_id,'integer','expense_id')
            expense = Expense.objects.get(id = expense_id)
            if not expense.group.members.filter(id = request.user.id).exists():
                return Response({"status":"failed","message":"You can not access this group because you are not the member of this group"})
            
            expense.delete()
            return Response({
                "status":"success",
                "message":"Expense deleted successfully...",
                },
                status=status.HTTP_200_OK
                )
        
        except ValueError as e:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        except Expense.DoesNotExist:
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calculate_group_balances(request):
    try:
        group_id = request.data.get('group_id')

        if not group_id:
            return Response({"status":"failed","message":"'group_id' must be required."},status=status.HTTP_400_BAD_REQUEST)
        
        group_id = isValid_type(int,group_id,'integer','group_id')

        group = Group.objects.get(id = group_id)

        if not group.members.filter(id = request.user.id).exists():
            return Response({"status":"failed","message":"You can not access this group because you are not the member of this group"})
        
        ExpenseSplit.objects.filter(group=group).delete()
        members = group.members.all()
        expenses = Expense.objects.filter(group = group)

        total_paid = {}
        total_share = {}
        for member in members:
            total_paid[member.username] = 0.0
            total_share[member.username] = 0.0

        for expense in expenses:
            if  expense.paid_by.username in total_paid.keys():
                total_paid[expense.paid_by.username] += float(expense.amount_paid)

            skipped = expense.skipped_member.all()
            participate = len(members) - len(expense.skipped_member.all())

            if participate == 0:
                continue

            share = float(expense.amount_paid)/participate
            share = share

            for member in members:
                if member not in skipped:
                    if member.username in total_share.keys():
                        total_share[member.username] += share
        
        balances = {}
        for member in members:
            username = member.username
            balances[username] = round(total_paid[username] - total_share[username],2)

        result = []
        for user,balance in balances.items():
            if balance > 0:
                new_balance = balance

                for payer,payer_balance in balances.items():
                    if payer_balance < 0 and new_balance > 0:
                        amount = min(abs(payer_balance), new_balance)
                        amount = round(amount,2)
                        result.append(f"'{payer}' need to pay {amount} to '{user}'")
                
                        payer_user = User.objects.get(username=payer)
                        receiver_user = User.objects.get(username=user)

                        ExpenseSplit.objects.create(
                            group=group,
                            payer=payer_user,
                            receiver=receiver_user,
                            amount=amount
                        )
                        
                        balances[payer] += amount
                        new_balance -= amount

        return Response({"status":"success","message":"Balance calculated...","data":result},status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

    except Group.DoesNotExist:
        return Response({"status":"failed","message":"Group not found"},status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    