from django.urls import path
from . import views

urlpatterns = [
    path('companies/', views.get_companies, name='get_companies'),
    path('company/add/', views.get_company_add, name='get_company_add'),
    path('company/<int:id>/', views.get_company, name='get_company'),
    path('company/<int:id>/review/', views.review_company, name='review_company'),

    path('login/', views.login_view, name='get_login'),
    path('login/signup/', views.signup_view, name='get_signup'),
    path('signup/', views.signup_view, name='post_signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='get_dashboard'),
    path('post_vacancy/', views.post_vacancy_view, name='post_vacancy'),
    path('vacancy/<int:id>/', views.vacancy_view, name='vacancy_detail'),
    path('', views.index_view, name='index'),
]
