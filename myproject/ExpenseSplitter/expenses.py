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
from django.db.models import Q
from django.core.paginator import Paginator,EmptyPage
from django.conf import settings
from .email_format import budget_alert_email
from django.utils.html import strip_tags


class ExpenseView(APIView):

    # send alert mail to all group members if their monthly budget limit is crossed.
    def send_alert(self,group,item):

        # if category for that group is exist then fetch it.
        if Budget.objects.filter(group = group,category = item).exists():
            budget = Budget.objects.get(group = group,category = item)

            # fetch query set of category of that group to calculate sum of it's amount
            expense = Expense.objects.filter(group = group, item=item)    
            
            sum = 0
            for amount in expense:
                # check month and year of expense and budget is same(because send mail for monthly limit)
                if (amount.date.month == budget.date.month and amount.date.year == budget.date.year):
                    sum += amount.amount_paid
                
            # if sum of expenses is higher then monthly budget then send mail to all the group members
            if sum >= budget.monthly_budget:
                member_emails = [email['email'] for email in group.members.values("email")]
                
                for email in member_emails:
                    subject = "Alert Message"
                    
                    html_message = budget_alert_email(group,budget.category,budget.monthly_budget,sum)
                    message = strip_tags(html_message)

                    send_mail(
                        subject,
                        message,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=False
                        )

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
                return Response({"status":"failed","message":"You are not access this group because you are not the member of this group"},status=status.HTTP_403_FORBIDDEN)

            # if who paid the amount is not a group member.
            if not group.members.filter(id = paid_by).exists():
                return Response({"status":"failed","message":f"For 'paid_by' {user.username} is not a member of this group"},status=status.HTTP_403_FORBIDDEN)

            members = []
            if skipped_member:
                for member in skipped_member.split(","):

                    # if skipped member is not a group member.
                    if not group.members.filter(id = member).exists():
                        return Response({"status":"failed","message":f"{member} is not a member of this group for 'skipped_members"},status=status.HTTP_400_BAD_REQUEST)
                    
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
            
            """Apply changes to connected database tables in a single transaction. Ensure all operaions succeed together.
            If any operation fails, all changes are rolled back."""
            with transaction.atomic():
                expense = Expense.objects.create(group=group,item=item,amount_paid=amount,paid_by=user,created_by = request.user, date=date,receipt=images)

                # set skipped member for this expense(set --> add member and remove existing one).
                expense.skipped_member.set(members)     

                self.send_alert(group,item)  # if item and group matched then send mail
                return Response({"status":"success","message":"Expense created successfully..."},status=status.HTTP_200_OK)

        except ValueError as e:
            if "time data" in str(e):
                return Response({"status":"failed","message":f"date {date} does not match the format 'YYYY-MM-DD'"},status=status.HTTP_400_BAD_REQUEST)
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        except Group.DoesNotExist:
            return Response({'status':"failed","message":"Group not found"},status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'status':"failed","message":"User not found"},status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self,request):
        try:
            group_id = request.data.get('group_id')
            search = request.data.get('search')
            page_number = request.data.get("page_number")
            page_size = request.data.get('page_size')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')

            if not page_number or not page_size:
                return Response({"status":"failed","meassage":"'page_number' and 'page_size' must be required"},status=status.HTTP_400_BAD_REQUEST)
            
            page_number = isValid_type(int,page_number,"integer","page_number")
            page_size = isValid_type(int,page_size,"integer","page_size")

            if page_number <= 0 or page_size <= 0:
                return Response({"status":"failed" ,"message":"page and page_size must be greater than 0"},status=status.HTTP_400_BAD_REQUEST)
            
            if group_id:
                group_id = isValid_type(int,group_id,'integer','group_id')
                group = Group.objects.get(id = group_id)

                if not group.members.filter(id = request.user.id).exists():
                    return Response({"status":"failed","message":"You can not access this group because you are not the member of this group"},status=status.HTTP_403_FORBIDDEN)

                expenses = Expense.objects.filter(group = group)
            
            else:
                expenses = Expense.objects.filter(group__membres = request.user)

            if search:
                expenses = expenses.filter(Q(item__icontains = search)|Q(amount_paid__icontains = search)|Q(paid_by__username__icontains = search)|Q(skipped_member__id__icontains = search)|Q(created_by__username__icontains=search))
            
            if start_date and end_date:
                start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
                end_date = datetime.strptime(end_date,"%Y-%m-%d").date()

                expenses = expenses.filter(
                    date__range=[start_date, end_date]
                )

            paginator = Paginator(expenses,page_size)

            paginator_data = paginator.page(page_number)
            
            list_expenses = []
            for expense in paginator_data:
                skipped_members = [val['id'] for val in expense.skipped_member.values("id")]
                updated_by = None
                if expense.updated_by is not None:
                    updated_by = expense.updated_by.username

                list_expenses.append({
                        "id":expense.id,
                        "item":expense.item,
                        "total_amount":expense.amount_paid,
                        "paid_by":expense.paid_by.username,
                        "skipped_members":skipped_members,
                        "date":expense.date,
                        "created_by":expense.created_by.username,
                        "updated_by":updated_by,
                        "created_at":expense.created_at,
                        "updated_at":expense.updated_at,
                        "receipt":expense.receipt,
                        "group":expense.group.name,
                    })
                
            return Response({
                "status":"success",
                "message":"Expense fetched",
                "total_pages": paginator.num_pages,
                "current_page": page_number,
                "total_items": paginator.count,
                f"{group.name}":list_expenses
                },
                status=status.HTTP_200_OK
                )
        
        except ValueError as e:
            if "time data" in str(e):
                return Response({"status":"failed","message": f"date does not match the format 'YYYY-MM-DD'"},status=status.HTTP_400_BAD_REQUEST)
            return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
                
        except Group.DoesNotExist:
            return Response({"status":"failed","message":"Group not found"},status=status.HTTP_404_NOT_FOUND)
        
        except EmptyPage:
            return Response({"status":"failed" ,"message": "Page not found"},status=status.HTTP_404_NOT_FOUND)

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
                return Response({"status":"failed","message":"'expense_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
            
            expense_id = isValid_type(int,expense_id,"integer","expese_id")
            expense = Expense.objects.get(id = expense_id)

            if not expense.group.members.filter(id = request.user.id).exists():
                return Response({"status":"failed","message":"You can not access this group because you are not the member of this group"},status=status.HTTP_401_UNAUTHORIZED)

            if item:
                item = item.strip().replace(" ","").capitalize()
                expense.item = item
                expense.save()

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
                    save_path = default_storage.save(f"reciept_images/{expense.item}/{img}",img)
                    new_img = default_storage.url(save_path)
                    images.append(request.build_absolute_uri(new_img))
                expense.receipt = images

            expense.updated_by = request.user
            expense.save()
            
            self.send_alert(group=expense.group,item=expense.item)
            return Response({"status":"success","message":"Expense updated successfully..."},status=status.HTTP_200_OK)

        except ValueError as e:
            if "time data" in str(e):
                return Response({"status":"failed","message": f"date {date} does not match the format 'YYYY-MM-DD'"},status=status.HTTP_400_BAD_REQUEST)
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
            return Response({"status":"failed","message":"Expense not found"},status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
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
        
        # Delete existing expense splits for the group to prevent duplicate records, when the API is called multiple times.
        ExpenseSplit.objects.filter(group=group).delete()     

        members = group.members.all()
        expenses = Expense.objects.filter(group = group)

        total_paid = {}
        total_share = {}

        # first set all members is paid and share 0 amount.
        for member in members:
            total_paid[member.username] = 0.0
            total_share[member.username] = 0.0

        for expense in expenses:

            # if member is paid amount then add the current expense amount.
            if expense.paid_by.username in total_paid.keys():
                total_paid[expense.paid_by.username] += float(expense.amount_paid)

            skipped = expense.skipped_member.all()

            # calculate who paricipates for categories.
            participate = len(members) - len(expense.skipped_member.all())

            # prevent if all members are skipped.
            if participate == 0:
                continue
            
            # calculate member's share
            share = float(expense.amount_paid)/participate

            for member in members:
                if member not in skipped:

                    # add share of member who not skipped.
                    if member.username in total_share.keys():
                        total_share[member.username] += share
        
        balances = {}
        for member in members:
            username = member.username

            # calculate balance of members.
            # if balance is (+) then other member pays to this memebr, 
            # if balance (-) this member need to pay to other.)
            balances[username] = round(total_paid[username] - total_share[username],2)

        result = []
        for user,balance in balances.items():

            # if balance is (+) then other member pays to this memebr.
            if balance > 0:
                new_balance = balance

                for payer,payer_balance in balances.items():

                    # if payer balance is (-) and receiver balance is (+).
                    # find minimum value of them and that amount need to pay by payer to reciever.
                    if payer_balance < 0 and new_balance > 0:

                        # use abs to convert (-) to (+) because(min(-500,200) = 500 which is wrong)
                        amount = min(abs(payer_balance), new_balance)
                        amount = round(amount,2)
                        result.append({
                            "from":payer,
                            "to":user,
                            "amount":amount
                            })
                
                        payer_user = User.objects.get(username=payer)
                        receiver_user = User.objects.get(username=user)

                        ExpenseSplit.objects.create(
                            group=group,
                            payer=payer_user,
                            receiver=receiver_user,
                            amount=amount
                        )
                        
                        # update payer balance because he paid money. 
                        # reduce receiver's amount to receive remaining amount.
                        balances[payer] += amount
                        new_balance -= amount

        return Response({"status":"success","message":"Balance calculated...","data":result},status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

    except Group.DoesNotExist:
        return Response({"status":"failed","message":"Group not found"},status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# calculate total expenses by range of date and specific category.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calculate_expense(request):
    try:
        group_id = request.data.get('group_id')
        category = request.data.get('category')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        if not group_id:
            return Response({"status":"failed","message":"'group_id' must be required"},status=status.HTTP_400_BAD_REQUEST)
        
        group_id = isValid_type(int,group_id,"integer","group_id")
        group = Group.objects.get(id = group_id)

        if not group.members.filter(id = request.user.id).exists():
            return Response({"status":"failed","message":"You can not access this group because you are not the member of this group"})

        expenses = Expense.objects.filter(group = group_id)

        if category:
            category = category.strip().replace(" ","").capitalize()
            expenses = Expense.objects.filter(item = category)

        if start_date and end_date:
            start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
            end_date = datetime.strptime(end_date,"%Y-%m-%d").date()

            expenses = expenses.filter(
                date__range=[start_date, end_date]
            )

        total_expense = 0
        for expense in expenses:
            total_expense += float(expense.amount_paid)

        return Response({"status":"success","message":"Expense calculated...","expense":{"total_expense":round(total_expense,2)}},status=status.HTTP_200_OK)
    
    except ValueError as e:
        if "time data" in str(e):
            return Response({"status":"failed","message":f"date 'start_date' = {start_date} or 'end_date' = {end_date} does not match the format 'YYYY-MM-DD'"},status=status.HTTP_400_BAD_REQUEST)
        return Response({"status":"failed","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
    except Group.DoesNotExist:
            return Response({"status":"failed","message":"Group not found"},status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"status":"error","message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
