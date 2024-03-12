from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Company, CompanyReview, UserProfile, Vacancy


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = CompanyReview
        fields = ['company', 'user', 'review']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'  # Add other fields as needed

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = instance.user.username  # Example: Serialize user's username
        return representation


class VacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = ['description', 'url', 'salary', 'company', 'city', 'source', 'created_by', 'created_at', 'is_new']


class EmployerSerializer(serializers.Serializer):
    db_name = serializers.CharField()
    shown_name = serializers.CharField()
    logo = serializers.URLField()

    def to_representation(self, instance):
        return {
            'db_name': instance.db_name,
            'shown_name': instance.shown_name,
            'logo': instance.logo
        }
