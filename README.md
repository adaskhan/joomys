### Установка проекта локально

#### 1. Клонирование репозитория
```
git clone https://github.com/adaskhan/joomys.git
```

#### 2. Открытие проекта
- Откройте склонированный проект в вашей любимой среде разработки, такой как PyCharm или VS Code.

#### 3. Создание виртуального окружения
```bash
python -m venv myenv
```
где `myenv` - имя вашего виртуального окружения.

#### 4. Активация виртуального окружения
```bash
source myenv/bin/activate   # для MacOS и Linux
myenv\Scripts\activate      # для Windows
```

#### 5. Установка зависимостей
```bash
pip install -r requirements.txt
```

#### 6. Выполнение миграций базы данных
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 7. Запуск парсера для заполнения базы данных (если необходимо)
```bash
python scrap.py
```

#### 8. Создание суперпользователя
```bash
python manage.py createsuperuser
```

#### 9. Запуск сервера разработки Django
```bash
python manage.py runserver
```

Теперь ваш проект должен быть доступен по адресу `http://127.0.0.1:8000/`. Вы можете войти в административный интерфейс Django, перейдя по адресу `http://127.0.0.1:8000/admin/` и использовав учетные данные созданного суперпользователя.
