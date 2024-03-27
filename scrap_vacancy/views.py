import json

import requests
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.serializers import serialize
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import CompanyForm, CompanyReviewForm
from .models import Company, CompanyReview, User, UserProfile, Vacancy, UserType
from .serializers import CompanySerializer, CompanyReviewSerializer, UserProfileSerializer, VacancySerializer, \
    EmployerSerializer
from .services import CompanyService, CompanyReviewService, LoginService, get_user_profile, post_vacancy_service, \
    VacancyService, TOP_EMPLOYERS, post_vacancy_service_api
from .models import Company


def get_companies(request):
    company_service = CompanyService()
    return company_service.return_all_companies(request)


def get_company_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        headcount = request.POST.get('headcount', '')
        company_type = request.POST.get('type', '')
        industry = request.POST.get('industry', '')
        tech_stack = request.POST.get('tech_stack', '')
        logo_url = request.POST.get('logo_url', '')
        website_url = request.POST.get('website_url', '')
        reviewed_at = None  # Установите значение по умолчанию или логику для этого поля

        company = Company(
            name=name,
            description=description,
            headcount=headcount,
            type=company_type,
            industry=industry,
            tech_stack=tech_stack,
            logo_url=logo_url,
            website_url=website_url,
            reviewed_at=reviewed_at,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        company.save()

        # Перенаправляем пользователя на страницу со списком компаний после успешного добавления
        return redirect(reverse('get_companies'))
    else:
        # Для GET-запроса отображаем форму добавления компании
        return render(request, "companies/add_new_company_form.html", {"page_title": "Joomys - Добавить компанию"})


def post_company_add(request):
    # Этот метод не нужен, если вы обрабатываете GET и POST в одной view, как показано выше
    ...


# Получить информацию о компании
def get_company(request, id):
    company = get_object_or_404(Company, pk=id)
    if request.user.is_authenticated:
        user = request.user
    else:
        user = None

    own_company_review = CompanyReview.objects.filter(company_id=id, user_id=user.id).first() if user else None
    company_review_questions = CompanyReviewService.get_company_review_questions()
    len_reviews, company_review_summary = CompanyReviewService.get_and_calculate_company_review(id)

    context = {
        "company": company,
        "page_title": f"Профиль IT компании {company.name}",
        "company_review_questions": company_review_questions,
        "own_company_review": own_company_review,
        "len_reviews": len_reviews,
        "company_review_summary": company_review_summary,
    }

    return render(request, "companies/company.html", context)


# Отзыв о компании
def review_company(request, id):
    if request.method == "POST":
        review_data = request.POST.dict()
        review_data.pop('csrfmiddlewaretoken', None)
        for key, value in review_data.items():
            review_data[key] = int(value)

        # Создаем объект CompanyReview
        review = CompanyReview()
        review.company = Company.objects.get(id=id)  # Получаем компанию по id
        review.user = request.user  # Или используйте свой метод для получения пользователя
        review.review = review_data
        review.save()
        return JsonResponse({"message": "Спасибо за ваш отзыв!"}, status=200)
    return JsonResponse({"error": "Что-то пошло не так!"}, status=400)


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest):
    login_service = LoginService()
    if request.method == "POST":
        return login_service.handle_login(request)
    else:
        return login_service.render_login_page(request)


@require_http_methods(["GET", "POST"])
def signup_view(request):
    login_service = LoginService()
    if request.method == "POST":
        return login_service.handle_signup(request)
    else:
        user_type = request.GET.get('user_type')
        return login_service.render_signup_page(request, user_type=user_type)


@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        # Проверяем, допустим ли тип пользователя
        if user_type not in ['recruiter', 'user']:
            messages.error(request, "Invalid user type")
            return render(request, 'signup/signup.html', {'user_type': user_type})

        if not email or not password:
            messages.error(request, "Email and password are required")
            return render(request, 'signup/signup.html')

        hashed_password = make_password(password)

        try:
            # Создаем пользователя и сохраняем его в базу данных
            user = User.objects.create(username=email, email=email, password=hashed_password)
            user.save()
            UserProfile.objects.create(
                user=user,
                user_type=user_type,
            )

            # Аутентифицируем пользователя и перенаправляем его на соответствующую страницу
            login(request, user)
            return redirect('/dashboard' if user_type == 'recruiter' else '/')
        except Exception as e:
            messages.error(request, "A user with that email already exists")
            return render(request, 'signup/signup.html')

    else:
        # Для GET запроса просто отображаем форму регистрации
        user_type = request.GET.get('user_type', None)

        return render(request, 'signup/signup.html', context={'user_type': user_type})


def check_user_type(user_profile, required_type):
    return user_profile.user_type == required_type


@login_required
def dashboard_view(request):
    user_profile = UserProfile.objects.filter(user=request.user).first()
    if not user_profile or not check_user_type(user_profile, 'recruiter'):
        return redirect('/')
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'page_title': 'Joomys - Кабинет Рекрутера'
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def post_vacancy_view(request):
    if request.method == 'POST':
        user_profile = get_user_profile(request.user)
        if not user_profile or user_profile.balance < 10000:
            messages.error(request, "Недостаточно средств, пожалуйста пополните баланс")
            return redirect('get_dashboard')
        response = post_vacancy_service(request, user_profile)
        return response
    else:
        return render(request, 'vacancy/vacancy_form.html')


def vacancy_view(request, id):
    vacancy = get_object_or_404(Vacancy, pk=id)
    return render(request, 'vacancy.html', {'vacancy': vacancy})


def index_view(request):
    vacancy_service = VacancyService()

    all_vacancies = vacancy_service.get_all_vacancies_sorted()
    # all_vacancies = vacancy_service.format_vacancies(all_vacancies)
    top_vacancies_by_company = vacancy_service.get_top_vacancies_by_company(all_vacancies)

    all_vacancies_json = serializers.serialize('json', all_vacancies, ensure_ascii=False)
    all_vacancies_list = json.loads(all_vacancies_json)
    for vacancy_dict in all_vacancies_list:
        tags_str = vacancy_dict["fields"]["tags"]
        if 'new' not in tags_str:
            parsed_list = eval(tags_str)
        else:
            parsed_list = eval(tags_str[:-4])

        tags_string = ", ".join(parsed_list)
        vacancy_dict["fields"]["tags"] = tags_string

    vacancy_json = json.dumps(all_vacancies_list, ensure_ascii=False)
    context = {
        "request": request,
        "top_employers": TOP_EMPLOYERS.values(),
        "top_vacancies_by_company": top_vacancies_by_company,
        "all_vacancies": all_vacancies,
        "all_vacancies_json": vacancy_json
    }
    return render(request, "index.html", context)


def logout_view(request):
    response = redirect('/')
    response.delete_cookie('access_token')  # Замените 'your_cookie_name' на имя вашей куки
    logout(request)
    return response


class LoginAPIView(APIView):

    @extend_schema(
        description="Authenticate user and get JWT tokens.",
        request={"application/json": {"example": {"email": "example@example.com", "password": "yourpassword"}}},
        responses={200: "Success", 401: "Unauthorized"}
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({'error': 'Invalid login credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
@api_view(['POST'])
@extend_schema(
    description="Register a new user.",
    request={"application/json": {"example": {"email": "example@example.com", "password": "yourpassword", "user_type": "USER"}}},
    responses={201: "User registered successfully", 400: "Bad request"}
)
def api_signup(request):
    email = request.data.get('email')
    password = request.data.get('password')
    user_type = request.data.get('user_type')

    print(email, password, user_type)

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if user_type not in [tag.value for tag in UserType]:
        return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

    hashed_password = make_password(password)

    if user_type:
        user_type_enum = UserType[user_type.upper()]  # Convert string to enum
    else:
        user_type_enum = UserType.USER

    try:
        # Создаем пользователя и сохраняем его в базе данных
        user = User.objects.create(username=email, email=email, password=hashed_password)
        user.save()

        user_profile = UserProfile.objects.create(
            user=user,
            user_type=user_type
        )
        user_profile.save()

        return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': 'A user with that email already exists'}, status=status.HTTP_400_BAD_REQUEST)


class CompanyListView(APIView):

    @extend_schema(
        description="Retrieve a list of companies along with their reviews.",
        responses={200: "Success"},
    )
    def get(self, request):
        companies = Company.objects.all().prefetch_related('companyreview_set')
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyAddView(APIView):
    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description', '')
        headcount = request.data.get('headcount', '')
        company_type = request.data.get('type', '')
        industry = request.data.get('industry', '')
        tech_stack = request.data.get('tech_stack', '')
        logo_url = request.data.get('logo_url', '')
        website_url = request.data.get('website_url', '')
        reviewed_at = None  # Set default value or logic for this field

        company = Company(
            name=name,
            description=description,
            headcount=headcount,
            type=company_type,
            industry=industry,
            tech_stack=tech_stack,
            logo_url=logo_url,
            website_url=website_url,
            reviewed_at=reviewed_at,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        company.save()

        # Return a success response with the newly created company data
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CompanyDetailView(APIView):
    permission_classes = [AllowAny, ]

    @extend_schema(
        description="Retrieve details of a specific company including its reviews.",
        responses={200: "Success"},
    )
    def get(self, request, id):
        company = get_object_or_404(Company, pk=id)
        serializer = CompanySerializer(company)

        # Assuming you have logic to get user data based on authentication
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None

        # Assuming CompanyReviewService.get_company_review_questions() returns appropriate data
        company_review_questions = CompanyReviewService.get_company_review_questions()
        len_reviews, company_review_summary = CompanyReviewService.get_and_calculate_company_review(id)

        response_data = {
            "company": serializer.data,
            "page_title": f"Профиль IT компании {company.name}",
            "company_review_questions": company_review_questions,
            "own_company_review": self.get_own_company_review(id, user),
            "len_reviews": len_reviews,
            "company_review_summary": company_review_summary,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def get_own_company_review(self, company_id, user):
        if user:
            own_company_review = CompanyReview.objects.filter(company_id=company_id, user_id=user.id).first()
            return own_company_review
        return None


class CompanyReviewAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    @extend_schema(
        description="Submit a review for a specific company.",
        request={"application/json": {"example": {"review": "Your review content"}}},
        responses={201: "Review submitted successfully", 400: "Bad request"}
    )
    def post(self, request, id):
        review_data = request.data
        company = Company.objects.get(id=id).id
        user = request.user.id
        data = {
            'company': company,
            'user': user,
            'review': review_data
        }
        serializer = CompanyReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Спасибо за ваш отзыв!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    @extend_schema(
        description="Get dashboard data for recruiters.",
        responses={200: "Success", 403: "Access denied"}
    )
    def get(self, request):

        user_profile = UserProfile.objects.filter(user=request.user).first()

        if not user_profile or not check_user_type(user_profile, 'RECRUITER'):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostVacancyAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        user_profile = get_user_profile(request.user)
        if not user_profile or user_profile.balance < 10000:
            return Response({"error": "Insufficient funds, please top up your balance"}, status=status.HTTP_400_BAD_REQUEST)
        response = post_vacancy_service_api(request, user_profile)
        return response


class VacancyDetailView(APIView):
    def get(self, request, id):
        vacancy = get_object_or_404(Vacancy, pk=id)
        serializer = VacancySerializer(vacancy)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IndexAPIView(APIView):

    @extend_schema(
        description="Retrieve top employers, top vacancies by company, and all vacancies sorted.",
        responses={200: "Success"},
    )
    def get(self, request):
        """
            Retrieve top employers, top vacancies by company, and all vacancies sorted.

            This endpoint returns data including top employers, top vacancies by company,
            and all vacancies sorted by some criteria.

            ---
            # Serializer Class
            # Assuming VacancySerializer and EmployerSerializer are defined.

            response_serializer:
                top_employers: EmployerSerializer(many=True)
                top_vacancies_by_company: VacancySerializer(many=True)
                all_vacancies: VacancySerializer(many=True)
        """
        vacancy_service = VacancyService()

        all_vacancies = vacancy_service.get_all_vacancies_sorted()
        top_vacancies_by_company = vacancy_service.get_top_vacancies_by_company(all_vacancies)

        all_vacancies_serializer = VacancySerializer(all_vacancies, many=True)
        top_vacancies_by_company_serializer = VacancySerializer(top_vacancies_by_company, many=True)
        top_employers_serializer = EmployerSerializer(TOP_EMPLOYERS.values(), many=True)

        data = {
            "top_employers": top_employers_serializer.data,  # Assuming TOP_EMPLOYERS is defined somewhere
            "top_vacancies_by_company": top_vacancies_by_company_serializer.data,
            "all_vacancies": all_vacancies_serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)
