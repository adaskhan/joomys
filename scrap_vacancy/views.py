from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .forms import CompanyForm, CompanyReviewForm
from .models import Company, CompanyReview, User, UserProfile, Vacancy, UserType
from .services import CompanyService, CompanyReviewService, LoginService, get_user_profile, post_vacancy_service, \
    VacancyService, TOP_EMPLOYERS
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
        return render(request, "companies/add_new_company_form.html", {"page_title": "TechHunter - Добавить компанию"})


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
        form = CompanyReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.company_id = id
            review.user = request.user
            review.save()
            # Отправить сообщение в Telegram о новом отзыве
            # telegram_service.send_message_to_private_channel(f"New review for company {id}")
            return HttpResponse("<div>Спасибо за ваш отзыв!</div>")
    else:
        form = CompanyReviewForm()
    return render(request, "companies/company_review_form.html", {'form': form})


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
        return render(request, 'signup/signup.html')


def check_user_type(user_profile, required_type):
    return user_profile.user_type == required_type


@login_required
def dashboard_view(request):
    user_profile = UserProfile.objects.filter(user=request.user).first()
    if not user_profile or not check_user_type(user_profile, 'RECRUITER'):
        print(f"{user_profile}")
        return redirect('/')
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'page_title': 'TechHunter - Кабинет Рекрутера'
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
    all_vacancies = vacancy_service.format_vacancies(all_vacancies)
    top_vacancies_by_company = vacancy_service.get_top_vacancies_by_company(all_vacancies)
    context = {
        "top_employers": TOP_EMPLOYERS.values(),
        "top_vacancies_by_company": top_vacancies_by_company,
        "all_vacancies": all_vacancies
    }
    return render(request, "index.html", context)


@api_view(['POST'])
def api_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, username=email, password=password)

    if user is not None:
        login(request, user)
        return Response({'message': 'User authenticated successfully'})
    else:
        return Response({'error': 'Invalid login credentials'}, status=400)


@csrf_exempt
@api_view(['POST'])
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
            user_type=user_type_enum
        )
        user_profile.save()

        return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': 'A user with that email already exists'}, status=status.HTTP_400_BAD_REQUEST)
