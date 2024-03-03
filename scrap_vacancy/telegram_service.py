import os
import telegram
from django.db.models import QuerySet
from .models import Vacancy
#
# BOT_TOKEN = os.getenv("BOT_TOKEN")
# CHANNEL_ID = "-1001918708178"  # Пример ID публичного канала
# PRIVATE_CHANNEL_ID = "-1001836766800"  # Пример ID приватного канала
#
# bot = telegram.Bot(token=BOT_TOKEN)


# def send_message(chat_id, message, parse_mode='HTML', disable_web_page_preview=True, reply_to_message_id=None):
#     try:
#         bot.send_message(chat_id=chat_id, text=message, parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview, reply_to_message_id=reply_to_message_id)
#     except Exception as e:
#         print(f"Error sending message: {e}")


def format_vacancy_with_link(vacancy):
    salary = vacancy.salary or ""
    return f"<a href='{vacancy.url}'>{vacancy.title} {salary}</a>"


def group_vacancies_by_tags(vacancies: QuerySet):
    tags = ["qa", "ios", "android", "frontend", "backend", "fullstack", "data", "design", "product", "python", "java", "javascript"]
    vacancies_by_tags = {tag: [] for tag in tags}
    for vacancy in vacancies:
        for tag in tags:
            if tag in (vacancy.tags or "").split(","):
                vacancies_by_tags[tag].append(vacancy)
    return vacancies_by_tags


# def report_added_vacancies(vacancies: QuerySet, chat_id=CHANNEL_ID):
#     if not vacancies.exists():
#         send_message(chat_id, "Сегодня новых вакансий нет.")
#         return
#     message = "<b>Новые вакансии:</b>\n\n"
#     vacancies_by_tags = group_vacancies_by_tags(vacancies)
#     for tag, vacs in vacancies_by_tags.items():
#         if vacs:
#             message += f"<b>{tag.upper()}:</b> {len(vacs)}\n"
#             for vacancy in vacs[:3]:  # Отображаем только первые 3 вакансии для каждого тега
#                 message += f"- {format_vacancy_with_link(vacancy)}\n"
#             message += "\n"
#     send_message(chat_id, message)
