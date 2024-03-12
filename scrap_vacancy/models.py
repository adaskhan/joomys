from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import enum


class Company(models.Model):
    name = models.TextField(null=False)
    description = models.TextField(null=True, blank=True)
    headcount = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    industry = models.TextField(null=True, blank=True)
    tech_stack = models.TextField(null=True, blank=True)
    logo_url = models.TextField(null=True, blank=True)
    website_url = models.TextField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class UserType(enum.Enum):
    USER = "user"
    RECRUITER = "recruiter"
    EXPERT = "expert"


# class User(models.Model):
#     email = models.TextField(null=False, unique=True)
#     password = models.TextField(null=False)
#     user_type = models.CharField(max_length=10, choices=[(tag.name, tag.value) for tag in UserType], default=UserType.USER)
#     balance = models.IntegerField(default=0)
#     created_at = models.DateTimeField(default=timezone.now)
#
#     def __str__(self):
#         return f"{self.user_type}: {self.email}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.IntegerField(default=0)
    user_type = models.CharField(max_length=10, choices=[(tag.name, tag.value) for tag in UserType])
    created_at = models.DateTimeField(auto_now_add=True)


class CompanyReview(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.company.name


class Vacancy(models.Model):
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    salary = models.TextField(null=True, blank=True)
    company = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    source = models.TextField(null=True, blank=True)
    tags = models.TextField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_new = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.tags = extract_tags(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company}: {self.title}"


def extract_tags(vacancy):
    tags = []
    print('u are here')
    tags += extract_tag_by_keywords(vacancy, ["cтажер", "trainee", "intern"], "intern")
    tags += extract_tag_by_keywords(vacancy, ["junior"], "junior")
    tags += extract_tag_by_keywords(vacancy, ["senior"], "senior")
    tags += extract_tag_by_keywords(vacancy, ["middle"], "middle")
    tags += extract_tag_by_keywords(vacancy, ["lead", "руководитель"], "lead")
    tags += extract_tag_by_keywords(vacancy, ["product", "продакт", "продукт"], "product")
    tags += extract_tag_by_keywords(vacancy, ["analyst", "аналитик"], "analyst")
    tags += extract_tag_by_keywords(vacancy, ["fullstack", "full stack"], "fullstack")
    tags += extract_tag_by_keywords(vacancy, ["frontend", "front end"], "frontend")
    tags += extract_tag_by_keywords(vacancy, ["backend", "back end"], "backend")
    tags += extract_tag_by_keywords(vacancy, ["системный", "sre"], "sysadmin")
    tags += extract_tag_by_keywords(vacancy, ["devops", "dev ops"], "devops")
    tags += extract_tag_by_keywords(vacancy, ["qa", "q/a", "quality assurance", "тестировщик"], "qa")
    tags += extract_tag_by_keywords(vacancy, ["data"], "data")
    tags += extract_tag_by_keywords(vacancy, ["design", "дизайн", "ux", "ui"], "design")
    tags += extract_tag_by_keywords(vacancy, ["ios", "swift"], "ios")
    tags += extract_tag_by_keywords(vacancy, ["android", "kotlin"], "android")
    tags += extract_tag_by_keywords(vacancy, [".net"], ".net")
    tags += extract_tag_by_keywords(vacancy, ["golang", "go"], "golang")
    tags += extract_tag_by_keywords(vacancy, ["python"], "python")
    tags += extract_tag_by_keywords(vacancy, ["java"], "java_")
    tags += extract_tag_by_keywords(vacancy, ["c++"], "c++")
    tags += extract_tag_by_keywords(vacancy, ["c#"], "c#")
    tags += extract_tag_by_keywords(vacancy, ["php"], "php")
    tags += extract_tag_by_keywords(vacancy, ["javascript", "js"], "javascript")
    tags += extract_tag_by_keywords(vacancy, ["react"], "react")
    tags += extract_tag_by_keywords(vacancy, ["node"], "node")
    tags += extract_tag_by_keywords(vacancy, ["sql"], "sql")

    if "javascript" in tags and "java_" in tags:
        tags.remove("java_")
    return tags


def extract_tag_by_keywords(vacancy, keywords: list[str], tag: str):
    if check_words_in_title(vacancy.title, keywords):
        return [tag]
    return []


def check_words_in_title(title: str, words: list[str]):
    if title is None:
        return False
    return any(word in title.lower() for word in words)
