from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Vacancy, UserProfile, Company, CompanyReview
import json


class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.company = Company.objects.create(name='Test Company', description='Test Description')
        self.vacancy = Vacancy.objects.create(title='Test Vacancy', company=self.company)

    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_vacancy_view(self):
        response = self.client.get(reverse('vacancy_detail', args=[self.vacancy.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vacancy.html')

    def test_post_vacancy_view(self):
        response = self.client.post(reverse('post_vacancy'), {'title': 'New Vacancy', 'company': self.company.id})
        self.assertEqual(response.status_code, 302)  # Assuming successful redirect after posting

    def test_dashboard_view_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('get_dashboard'))
        self.assertEqual(response.status_code, 302)  # Assuming redirect to login page

    def test_review_company(self):
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
        response = self.client.post(reverse('review_company', args=[self.company.id]), review_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Спасибо за ваш отзыв!')

    def test_get_company_authenticated(self):
        response = self.client.get(reverse('get_company', args=[self.company.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'companies/company.html')

    def test_get_company_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('get_company', args=[self.company.id]))
        self.assertEqual(response.status_code, 200)  # Assuming company details are still accessible
        self.assertTemplateUsed(response, 'companies/company.html')

    def test_get_company_add_authenticated(self):
        response = self.client.get(reverse('get_company_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'companies/add_new_company_form.html')

    def test_get_company_add_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('get_company_add'))
        self.assertEqual(response.status_code, 200)  # Assuming redirect to login page
