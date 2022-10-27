# <img src="https://github.com/StasKrut/hw05_final/blob/master/yatube/static/img/logo.png" width="100"> atube project


### Описание
Проект Yatube представляет собой социальную сеть для публикации личных дневников. Это сайт, на котором пользователь может создать свою личную страницу. Если на нее зайти, то можно посмотреть все записи автора. Пользователи могут заходить на чужие страницы, подписываться на авторов и комментировать их записи. 
Записи можно отправить в сообщество и посмотреть там записи разных авторов.

В проекте предусмотрена модерация записей и блокировка пользователей, отправляющих спам.

### Стек технологий, использованный в проекте:

Python 3.7

Django 2.2.28

ORM

HTML 5

### Запуск проекта в dev-режиме:

- Клонировать репозиторий и перейти в него в командной строке.
- Установите и активируйте виртуальное окружение c учетом версии Python 3.7 (выбираем python не ниже 3.7):

```py -3.7 -m venv venv```

```source venv/Scripts/activate```
- Затем нужно установить все зависимости из файла requirements.txt

```python -m pip install --upgrade pip```

```pip install -r requirements.txt```
- Выполняем миграции:

```python manage.py migrate```
- Создаем суперпользователя:

```python manage.py createsuperuser```
- Запускаем проект:

```python manage.py runserver```
- Открываем ссылку http://127.0.0.1:8000/ в любом браузере.

### Автор в рамках учебного курса ЯП Python - разработчик бекенда:

✅ [Stanislav Krutskikh](https://github.com/StasKrut)
