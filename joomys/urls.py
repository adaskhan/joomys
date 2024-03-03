from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('scrap_vacancy.urls')),
    path('api/', include('scrap_vacancy.api_urls')),
]
