from django.urls import path
from . import views

urlpatterns = [
    path('companies/', views.get_companies, name='get_companies'),
    path('company/add/', views.get_company_add, name='get_company_add'),
    path('company/<int:id>/', views.get_company, name='get_company'),
    path('company/<int:id>/review/', views.review_company, name='review_company'),

    path('login/', views.api_login, name='login_api'),
    path('signup/', views.api_signup, name='signup_api'),
    # path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard_view, name='get_dashboard'),
    path('post_vacancy/', views.post_vacancy_view, name='post_vacancy'),
    path('vacancy/<int:id>/', views.vacancy_view, name='vacancy_detail'),
    path('', views.index_view, name='index'),
]
