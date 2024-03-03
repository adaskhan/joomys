from django import forms
from .models import Company, CompanyReview


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'headcount', 'type', 'industry', 'tech_stack', 'logo_url', 'website_url']


class CompanyReviewForm(forms.ModelForm):
    class Meta:
        model = CompanyReview
        fields = ['company', 'review']  # Предполагается, что у вас есть такие поля
