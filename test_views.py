import json
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from scrap_vacancy.models import Vacancy, Company
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpassword')


@pytest.fixture
def company(db):
    return Company.objects.create(name='Test Company', description='Test Description')


@pytest.fixture
def vacancy(company):
    return Vacancy.objects.create(title='Test Vacancy', company=company)


@pytest.mark.django_db
def test_index_view(client, user):
    client.force_login(user)
    response = client.get(reverse('index'))
    assert response.status_code == 200
    assert 'index.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_vacancy_view(client, vacancy):
    response = client.get(reverse('vacancy_detail', args=[vacancy.id]))
    assert response.status_code == 200
    assert 'vacancy.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_post_vacancy_view(client, company):
    response = client.post(reverse('post_vacancy'), {'title': 'New Vacancy', 'company': company.id})
    assert response.status_code == 302


@pytest.mark.django_db
def test_dashboard_view_unauthenticated(client):
    response = client.get(reverse('get_dashboard'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_review_company(client, company, user):
    client.force_login(user)
    review_data = {
        'career': 8,
        'salary': 6,
        'projects': 10,
        'equipment': 5,
        'recommend': 5,
        'management': 8,
        'tech_stack': 7,
        'remote_work': 7,
        'work_schedule': 7
    }
    response = client.post(reverse('review_company', args=[company.id]), review_data)
    assert response.status_code == 200
    assert response.json()['message'] == 'Спасибо за ваш отзыв!'


@pytest.mark.django_db
def test_get_company_authenticated(client, company):
    response = client.get(reverse('get_company', args=[company.id]))
    assert response.status_code == 200
    assert 'companies/company.html' in [template.name for template in response.templates]


@pytest.mark.django_db
def test_get_company_unauthenticated(client, company):
    client.logout()
    response = client.get(reverse('get_company', args=[company.id]))
    assert response.status_code == 200
    assert 'companies/company.html' in [template.name for template in response.templates]


@pytest.mark.django_db
def test_get_company_add_authenticated(client):
    response = client.get(reverse('get_company_add'))
    assert response.status_code == 200
    assert 'companies/add_new_company_form.html' in [template.name for template in response.templates]


@pytest.mark.django_db
def test_get_company_add_unauthenticated(client):
    client.logout()
    response = client.get(reverse('get_company_add'))
    assert response.status_code == 200
