from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class User(AbstractBaseUser):
    id = models.AutoField(primary_key = True)
    username = models.CharField(max_length = 100,unique = True, null = False)
    email = models.EmailField(max_length = 150, unique = True, null = False)
    password = models.CharField(max_length = 128, null = False)
    token_version = models.IntegerField(default = 0)
    otp = models.CharField(max_length=4,blank=True,null=True)
    otp_exp = models.DateTimeField(blank=True,null=True)

    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username

class Group(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250,unique=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_admin")
    members = models.ManyToManyField(User,related_name='members')
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return self.name
    

class Budget(models.Model):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group,on_delete=models.CASCADE,related_name='budget')
    monthly_budget = models.DecimalField(max_digits=7,decimal_places=2)
    category = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return self.category


class Expense(models.Model):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(Group,on_delete=models.CASCADE,related_name='expense')
    item = models.CharField(max_length=200)
    amount_paid = models.DecimalField(max_digits=7,decimal_places=2)
    paid_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name='paid_by')
    skipped_member = models.ManyToManyField(User,related_name='skipped_members')
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='created_expenses')
    updated_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='updated_expenses')
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    date = models.DateField(default=timezone.now)
    receipt = models.JSONField(default=list)


class ExpenseSplit(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    payer = models.ForeignKey(User,on_delete=models.CASCADE,related_name="payer")
    receiver = models.ForeignKey(User,on_delete=models.CASCADE,related_name="receiver")
    amount = models.DecimalField(max_digits=10,decimal_places=2)
