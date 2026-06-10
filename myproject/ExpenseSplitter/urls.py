from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .authentication import *
from .views import *
from .invitation import *
from .budget import *
from .expenses import *

urlpatterns = [
    path('register/',userregister),
    path('getuser/',getuser),
    path('login/',userlogin),
    path('logout/',logout),
    path('forgot_password/',forgot_password),
    path('reset_password/',reset_password),
    path('token/refresh/',TokenRefreshView.as_view()),
    path('create_group/',GroupView.as_view()),
    path('invite/members/',send_invitation_link),
    path('invitation_link/<int:group_id>/<str:email>/',join_group),
    path('exit_group/',exit_group),
    path('manage_budget/',BudgetView.as_view()),
    path('add_expenses/',ExpenseView.as_view()),
    path('calculate_balance/',calculate_group_balances)
]