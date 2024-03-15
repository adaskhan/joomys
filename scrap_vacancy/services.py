import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from typing import List

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User, Group
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Company, CompanyReview, UserType, UserProfile, Vacancy
from django.db.models import Avg, Count

COMPANY_REVIEW_QUESTIONS = {
    "salary": "Я доволен зарплатой",
    "work_schedule": "Я доволен рабочим графиком в компании",
    "remote_work": "Я могу выбирать откуда работать",
    "equipment": "Компания предоставляет всю необходимую технику для работы",
    "career": "Компания предоставляет возможность карьерного роста",
    "projects": "В компании интересные проекты",
    "tech_stack": "В компании используют современные технологии/стек",
    "management": "Мне нравится менеджмент компании",
    "recommend": "Я готов рекомендовать компанию друзьям"
}


class CompanyService:
    @staticmethod
    def return_all_companies(request):
        companies = Company.objects.all().prefetch_related('companyreview_set')
        print(companies)
        company_reviews_averaged = CompanyReviewService.get_and_calculate_all_companies_reviews_by_company()
        print(company_reviews_averaged)
        # Сортировка компаний по количеству отзывов
        companies_sorted_by_number_of_reviews = sorted(companies,
                                                       key=lambda x: company_reviews_averaged.get(x.id, (0, 0))[0],
                                                       reverse=True)
        print(companies_sorted_by_number_of_reviews)
        print(companies_sorted_by_number_of_reviews[0].id)
        return render(request, "companies/all_companies.html", {
            "companies": companies_sorted_by_number_of_reviews,
            "page_title": "Все IT компании Казахстана",
            "company_reviews_averaged": company_reviews_averaged
        })

    @staticmethod
    def get_company(company_id):
        """Возвращает компанию по ID."""
        return get_object_or_404(Company, pk=company_id)

    @staticmethod
    def add_new_company(company_data):
        """Добавляет новую компанию."""
        company = Company(**company_data)
        company.save()
        # Отправка уведомления в Telegram, если нужно
        return company


class CompanyReviewService:
    @staticmethod
    def save_company_review(company_id, user_id, review_data):
        """Сохраняет отзыв о компании."""
        review, created = CompanyReview.objects.update_or_create(
            company_id=company_id,
            user_id=user_id,
            defaults=review_data,
        )
        return review

    @staticmethod
    def get_and_calculate_company_review(company_id):
        reviews = CompanyReview.objects.filter(company_id=company_id)
        if reviews:
            # Предположим, что у нас есть метод для расчета средних значений отзывов
            # Например, calculate_company_review_average возвращает количество отзывов и среднюю оценку
            return CompanyReviewService.calculate_company_review(reviews)
        else:
            return 0, None

    @staticmethod
    def calculate_company_review(reviews: List[CompanyReview]):
        review = {}
        for key in COMPANY_REVIEW_QUESTIONS.keys():
            review[key] = 0
        for r in reviews:
            for key in COMPANY_REVIEW_QUESTIONS.keys():
                review[key] += r.review[key]
        for key in COMPANY_REVIEW_QUESTIONS.keys():
            review[key] = round(review[key] / len(reviews), 1)
        return len(reviews), review

    @staticmethod
    def calculate_company_review_average(company_id):
        """Рассчитывает средние значения отзывов для компании."""
        reviews = CompanyReview.objects.filter(company_id=company_id)
        average_scores = reviews.aggregate(Avg('rating'))  # Предполагается наличие поля 'rating'
        return average_scores

    @staticmethod
    def get_company_review_questions():
        """Возвращает вопросы для отзывов о компании."""
        # Здесь можно вернуть словарь или список вопросов, если они фиксированы
        return COMPANY_REVIEW_QUESTIONS

    @staticmethod
    def get_and_calculate_all_companies_reviews_by_company():
        company_reviews_aggregated = {}
        companies = Company.objects.all()

        for company in companies:
            reviews = CompanyReview.objects.filter(company=company)
            total_reviews = reviews.count()

            if total_reviews == 0:
                continue

            aggregated_scores = {question: 0 for question in COMPANY_REVIEW_QUESTIONS.keys()}

            for review in reviews:
                for question, score in review.review.items():
                    if question in aggregated_scores:
                        aggregated_scores[question] += score

            # Вычисляем средние значения
            averaged_scores = {question: round(total_score / total_reviews, 1) for question, total_score in
                               aggregated_scores.items()}
            overall_average = round(sum(averaged_scores.values()) / len(averaged_scores), 1)

            company_reviews_aggregated[company.id] = (total_reviews, overall_average)

        return company_reviews_aggregated


class LoginService:

    def render_signup_page(self, request: HttpRequest, user_type: str) -> HttpResponse:
        if request.user.is_authenticated:
            # Перенаправляем авторизованных пользователей
            return redirect('/dashboard' if request.user.user_type == UserType.RECRUITER else '/')
        return render(request, "signup/signup.html", {"user_type": user_type, "request": request})

    def render_login_page(self, request):
        if request.user.is_authenticated:
            return redirect('/dashboard')
        return render(request, "login/login.html", {"request": request})

    @require_http_methods(["POST"])
    def handle_signup(self, request: HttpRequest) -> HttpResponse:
        email = request.POST.get("email")
        password = request.POST.get("password")
        user_type = request.POST.get("user_type")
        if user_type not in [UserType.RECRUITER, UserType.USER]:
            return self.render_signup_page(request, user_type)
        if not email or not password:
            return self.render_signup_page(request, user_type)
        try:
            user = User.objects.create_user(username=email, email=email, password=password)
            user.user_type = user_type  # Предполагаем, что это поле определено в вашей модели пользователя
            user.save()
            login(request, user)  # Аутентификация пользователя и установка сессии
            return redirect('/dashboard' if user_type == UserType.RECRUITER else '/')
        except Exception as e:
            return self.render_signup_page(request, user_type)

    def handle_login(self, request: HttpRequest) -> HttpResponse:
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('get_dashboard')
        else:
            return render(request, "login/login.html", {"error": "Invalid login or password"})

    def handle_logout(self, request):
        logout(request)
        return redirect('/')


def get_user_profile(user):
    return UserProfile.objects.filter(user=user).first()


def post_vacancy_service(request, user_profile):
    title = request.data.get("title")
    description = request.data.get("description")
    salary = request.data.get("salary")
    company = request.data.get("company")
    city = request.data.get("city")
    tags = request.data.get("tags")
    source = "joomys.kz"

    vacancy = Vacancy(
        title=title,
        description=description,
        salary=salary,
        company=company,
        city=city,
        tags=tags,
        created_by=user_profile.user.id,
        source=source
    )
    vacancy.save()
    vacancy.url = f"/vacancy/{vacancy.id}"
    vacancy.save()
    user_profile.balance -= 10000
    user_profile.save()

    # Здесь можно добавить код для отправки сообщения в Telegram, если это необходимо

    return redirect('vacancy_detail_api', id=vacancy.id)


@dataclass
class Employer:
    db_name: str
    shown_name: str
    logo: str


TOP_EMPLOYERS = {
    "Kaspi.kz": Employer("Kaspi.kz", "Kaspi", "https://upload.wikimedia.org/wikipedia/ru/a/aa/Logo_of_Kaspi_bank.png"),
    "Публичная Компания «Freedom Finance Global PLC»": Employer("Публичная Компания «Freedom Finance Global PLC»", "Freedom Finance", "https://i.postimg.cc/L4wRBbnR/imageedit-2-4305611673.png"),
    "Яндекс": Employer("Яндекс", "Yandex", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Yandex_icon.svg/2048px-Yandex_icon.svg.png"),
    # "АО\xa0Колеса": Employer("АО\xa0Колеса", "Колеса", "https://avatars.dzeninfra.ru/get-zen-logos/246004/pub_5b8f90f730712100ab841ac1_5b8f919f78944e00aa281d9e/xxh"),
    # "ТОО\xa0inDrive": Employer("ТОО\xa0inDrive", "inDrive", "https://is1-ssl.mzstatic.com/image/thumb/Purple126/v4/50/94/ab/5094ab3d-0a81-7c5d-0311-4205a7fa6821/AppIcon-0-0-1x_U007emarketing-0-5-0-0-85-220.png/1200x630wa.png"),
    # "ТОО\xa0AVIATA.KZ": Employer("ТОО\xa0AVIATA.KZ", "Aviata.kz", "https://play-lh.googleusercontent.com/OL3avfQvT_bmskEIkuqeopTHfcP5PosPf8ndu_vs2X8hvG3uDclVcbL-FYJS6D46ZFI=w480-h960-rw")
}

job_tag_to_localized_job_title = {
    "frontend": "Frontend",
    "backend": "Backend",
    "fullstack": "Fullstack",
    "qa": "QA",
    "ios": "iOS",
    "android": "Android",
    "product": "Product",
    "data": "Data",
    "design": "Design",
    "analyst": "Analyst",
    "sysadmin": "Системный Администратор",
    "devops": "DevOps",
    "golang": "Golang",
    "python": "Python",
    "java_": "Java",
    "php": "PHP",
    "javascript": "JavaScript",
    "react": "React"
}

city_tag_to_localized_city_title = {
    "almaty": "Алматы",
    "astana": "Астана"
}


class VacancyService:

    def get_all_vacancies_sorted(self):
        # if cache.get("all_vacancies"):
        #     return cache.get("all_vacancies")
        all_vacancies = Vacancy.objects.all()
        all_vacancies = sorted(all_vacancies, key=lambda vacancy: (
                    self.calculate_promotion(vacancy) + self.convert_salary_to_int(vacancy.salary)), reverse=True)
        # cache.set("all_vacancies", all_vacancies, timeout=3600)  # Кэшируем на 1 час
        return all_vacancies

    def get_top_vacancies_by_company(self, all_vacancies):
        top_vacancies = defaultdict(list)
        for vacancy in all_vacancies:
            if vacancy.company in TOP_EMPLOYERS:
                top_vacancies[vacancy.company].append(vacancy)
        return top_vacancies

    def format_vacancies(self, vacancies):
        # if cache.get("formatted_vacancies"):
        #     return cache.get("formatted_vacancies")
        for vacancy in vacancies:
            if vacancy.source == "joomys.kz":
                vacancy.title = "🔥 " + vacancy.title
            if vacancy.created_at > timezone.now() - timedelta(days=1):
                vacancy.title = "🆕 " + vacancy.title
                if vacancy.tags:
                    vacancy.tags += ",new"
                else:
                    vacancy.tags = "new"
        # cache.set("formatted_vacancies", vacancies, timeout=3600)  # Кэшируем на 1 час
        return vacancies

    def convert_salary_to_int(self, salary):
        if not salary:
            return 0
        try:
            salary = salary.replace(' ', '').replace('\xa0', '').replace('\u202f', '')
            numbers = re.findall(r'\d+', salary)
            average_salary = sum(map(int, numbers)) // len(numbers)
            currency_symbol = salary[-1]
            currency_rates = {'₸': 0.0021, '₽': 0.011, '€': 1.17}
            if currency_symbol in currency_rates:
                average_salary *= currency_rates[currency_symbol]
            return average_salary
        except Exception as e:
            return 0

    def calculate_promotion(self, vacancy):
        if vacancy.source == "joomys.kz" or vacancy.created_by:
            return 10 ** 10
        return 0
