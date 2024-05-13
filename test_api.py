import json
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from scrap_vacancy.models import Company, CompanyReview


@pytest.fixture
def authenticated_client():
    user = User.objects.create_user(username='testuser', password='testpassword')
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def unauthenticated_client():
    return APIClient()


@pytest.fixture
def test_company():
    return Company.objects.create(name='Test Company', description='Test Description')


@pytest.mark.django_db
def test_company_list_view(authenticated_client, test_company):
    url = reverse('get_companies_api')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


@pytest.mark.django_db
def test_company_detail_view(authenticated_client, test_company):
    url = reverse('get_company_api', args=[test_company.id])
    response = authenticated_client.get(url)
    print(response.data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['company']['name'] == 'Test Company'


@pytest.mark.django_db
def test_company_review_view(authenticated_client, test_company):
    url = reverse('review_company_api', args=[test_company.id])
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
    response = authenticated_client.post(url, review_data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert CompanyReview.objects.count() == 1


# @pytest.mark.django_db
# def test_company_add_view(authenticated_client):
#     url = reverse('get_company_add_api')
#     company_data = {
#         'name': 'New Company',
#         'description': 'New Description'
#         # Add other required fields here
#     }
#     response = authenticated_client.post(url, company_data, format='json')
#     assert response.status_code == status.HTTP_201_CREATED
#     assert Company.objects.count() == 1  # Assuming only one company is created in the test


@pytest.mark.django_db
def test_company_dashboard_view(authenticated_client):
    url = reverse('get_dashboard_api')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
