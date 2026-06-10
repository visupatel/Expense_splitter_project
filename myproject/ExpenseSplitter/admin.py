from django.contrib import admin
from .models import User,Group,Budget,Expense,ExpenseSplit

admin.site.register(User)
admin.site.register(Group)
admin.site.register(Budget)
admin.site.register(Expense)
admin.site.register(ExpenseSplit)