import time

import requests
from celery import shared_task
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import httpx
from django.db import transaction
from .models import Vacancy
from django.utils import timezone

MAX_PAGE = 100
SCRAP_INTERVAL = 60 * 60
START_HOUR = 10
START_MINUTE = 1


@shared_task
def scrap_hhkz_vacancies(query, log_tag, hour, minute):
    scrapper = HHKZVacancyScrapper(query, log_tag, hour, minute)
    scrapper.run()


@shared_task
def check_hhkz_vacancies():
    checker = HHKZVacancyChecker()
    checker.run()


class VacancyScrapperBase:
    def __init__(self, url: str, source: str, log_tag: str, hour: int = 0, minute: int = 0, interval_hours: int = 12):
        self.source: str = source
        self.url_base: str = url
        self.client = httpx.AsyncClient()
        self.log_tag = log_tag
        self.hour = hour
        self.minute = minute
        self.interval_hours = interval_hours
        next_run_time = timezone.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        while next_run_time < timezone.now():
            next_run_time = next_run_time + timedelta(hours=self.interval_hours)
        self.next_run_time = next_run_time

    def _run(self):
        try:
            old_vacancies = Vacancy.objects.filter(source=self.source)
            old_vacancies_urls = set(vacancy.url for vacancy in old_vacancies)
            new_vacancies = self.scrap()  # Вызываем scrap из подкласса
            new_vacancies_dict = {vacancy.url: vacancy for vacancy in new_vacancies}
            new_vacancies_urls = set(vacancy.url for vacancy in new_vacancies)
            added_vacancies_urls = new_vacancies_urls - old_vacancies_urls
            added_vacancies = [new_vacancies_dict[url] for url in added_vacancies_urls]
            for vacancy in added_vacancies:
                vacancy.save()
        except Exception as e:
            ...

    def run(self):
        while True:
            if timezone.now() < self.next_run_time:
                time.sleep(1)
                continue
            self.next_run_time = self.next_run_time + timedelta(hours=self.interval_hours)
            self._run()

    def run_now(self):
        self._run()


class HHKZVacancyScrapper(VacancyScrapperBase):
    def __init__(self, query, log_tag, hour, minute):
        self.query = query
        super().__init__("https://api.hh.ru/vacancies", "hh.kz", log_tag, hour=hour, minute=minute)

    def scrap_page(self, page):
        params = {
            'text': self.query,
            'area': 40,
            'page': page,
            'per_page': 100
        }
        response = requests.get(self.url_base, params=params)
        response.raise_for_status()  # Выбросить исключение, если получен некорректный ответ
        data = response.json()
        vacancies = self.extract_vacancies(data)
        return vacancies

    def scrap(self):
        vacancies = []
        page = 0
        while True:
            try:
                page_vacancies = self.scrap_page(page)
                if not page_vacancies:
                    break
                vacancies.extend(page_vacancies)
                page += 1
                time.sleep(1)
            except Exception as e:
                break
        return vacancies

    def extract_vacancies(self, data):
        vacancies = []
        for item in data['items']:
            title = item['name']
            url = item['alternate_url']
            company = item['employer']['name']
            city = item['area']['name']
            salary = item['salary']
            if salary:
                salary = f"{salary['from']} - {salary['to']} {salary['currency']}"
            else:
                salary = None
            tags = None  # добавьте теги, если нужно
            vacancies.append(Vacancy(title=title, url=url, salary=salary, company=company, city=city, tags=tags, source=self.source, is_new=True))
        return vacancies


class VacancyCheckerBase:
    def __init__(self, source: str):
        self.client = httpx.AsyncClient()
        self.source: str = source

    def run(self):
        while True:
            try:
                with transaction.atomic():
                    all_vacancies = Vacancy.objects.filter(source=self.source)
                    for vacancy in all_vacancies:
                        if self.check_closed(vacancy):
                            vacancy.delete()
                        time.sleep(1)
            except Exception as e:
                ...
            time.sleep(SCRAP_INTERVAL)

    def run_now(self):
        pass

    def check_closed(self, _):
        raise NotImplementedError("Method check_closed is not implemented")


class HHKZVacancyChecker(VacancyCheckerBase):
    def __init__(self):
        super().__init__("hh.kz")

    def check_closed(self, vacancy: Vacancy):
        try:
            response = self.client.get(vacancy.url, follow_redirects=True, timeout=7)
            if response.status_code != 200:
                return False
            soup = BeautifulSoup(response.text, 'html.parser')
            archive_description = soup.find("p", {"class": "vacancy-archive-description"})
            if archive_description:
                return True
            return False
        except Exception as e:
            return False


@shared_task
def scrap_now():
    from .scrappers import ALL_SCRAPPERS
    for scrapper in ALL_SCRAPPERS:
        print(f"Running {scrapper.log_tag}")
        scrapper.run_now()
