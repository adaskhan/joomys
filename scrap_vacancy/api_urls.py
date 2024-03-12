from django.urls import path
from . import views

urlpatterns = [
    path('companies/', views.CompanyListView.as_view(), name='get_companies_api'),
    path('company/add/', views.CompanyAddView.as_view(), name='get_company_add_api'),
    path('company/<int:id>/', views.CompanyDetailView.as_view(), name='get_company_api'),
    path('company/<int:id>/review/', views.CompanyReviewAPIView.as_view(), name='review_company_api'),

    path('login/', views.api_login, name='login_api'),
    path('signup/', views.api_signup, name='signup_api'),
    path('logout/', views.logout_view, name='logout_api'),
    path('dashboard/', views.DashboardAPIView.as_view(), name='get_dashboard_api'),
    path('post_vacancy/', views.PostVacancyAPIView.as_view(), name='post_vacancy_api'),
    path('vacancy/<int:id>/', views.VacancyDetailView.as_view(), name='vacancy_detail_api'),
    path('', views.IndexAPIView.as_view(), name='index_api'),
]
