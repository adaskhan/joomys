import os
import django

# Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joomys.settings')

# Инициализируем Django
django.setup()


from scrap_vacancy.tasks import scrap_now
from scrap_vacancy.models import Vacancy


scrap_now()

vcs = Vacancy.objects.filter(title__icontains="'")
for vc in vcs:
    vc.delete()

vcs = Vacancy.objects.filter(title__icontains='"')
for vc in vcs:
    vc.delete()

vcs = Vacancy.objects.filter(title__icontains='/')
for vc in vcs:
    vc.delete()

vcs = Vacancy.objects.filter(title__icontains='//')
for vc in vcs:
    vc.delete()

vcs = Vacancy.objects.filter(title__icontains='&')
for vc in vcs:
    vc.delete()

vcs = Vacancy.objects.filter(company__icontains="'")
for vc in vcs:
    vc.delete()

vcs = Vacancy.objects.filter(title__icontains='\\')
for vc in vcs:
    vc.delete()
