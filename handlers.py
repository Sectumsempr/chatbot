import logging
import re
from datetime import datetime
import calendar

import bs4
import requests

from generate_ticket import generate_ticket
from settings import ticket

log = logging.getLogger("bot")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

file_handler = logging.FileHandler(filename="bot.log", encoding="UTF-8")
file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt='%d-%m-%Y %H:%M'))

log.addHandler(stream_handler)
log.addHandler(file_handler)
log.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.DEBUG)

re_towns = {
    "Msc": re.compile(r"\b[Мм]оскв"),
    "Spb": re.compile(r"\b[сС]анкт-[Пп]етербург"),
    "Anapa": re.compile(r"\b[[Аа]нап"),
    "Norilsk": re.compile(r"\b[Нн]орильск")
}
re_phone = re.compile(r'(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$', re.VERBOSE)


def handler_departure(text, context):
    for town, re_town in re_towns.items():
        match = re.match(pattern=re_town, string=text)
        if match:
            context['departure'] = town
            log.debug(f"Выбран город отправления {town}")
            return True
    return False


def handler_arrival_existing(text, context):
    for town, re_town in re_towns.items():
        match = re.match(pattern=re_town, string=text)
        if match:
            context['arrival'] = town
            return True
    return False


def handler_arrival(text, context):
    if handler_arrival_existing(text=text, context=context):
        if not context['arrival'] in ticket[context['departure']]:
            context['cause'] = "Между выбранными городами нет рейса"
            return False
    else:
        context['cause'] = "Для данного города нет авиабилетов. Для большей информации используйте /help"
        return False
    log.debug(f"Выбран город назначения {context['arrival']}")
    return True


def dispatcher(text, context):
    try:
        entered_date = datetime.strptime(text, '%d-%m-%Y')
    except ValueError:
        return False
    if entered_date < datetime.now():
        return False

    calendar_text = calendar.TextCalendar()
    month = entered_date.month
    entered_month = month
    year = entered_date.year
    day = entered_date.day

    for flight_month in range(0, 12):
        day_iterator = calendar_text.itermonthdays2(year=year, month=month)
        for data, weekday in day_iterator:
            if data == 0:
                continue
            if data < day and entered_month == month:
                continue
            if weekday == 0 or weekday == 2:
                date = datetime(year=year, month=month, day=data, hour=10)
                ticket['Spb']['Msc'].append(date.strftime('%d-%m-%Y %H:%M'))
            if weekday == 1 or weekday == 3:
                date = datetime(year=year, month=month, day=data, hour=16)
                ticket['Msc']['Spb'].append(date.strftime('%d-%m-%Y %H:%M'))
            if data == 15:
                date = datetime(year=year, month=month, day=data, hour=10, minute=45)
                ticket['Msc']['Norilsk'].append(date.strftime('%d-%m-%Y %H:%M'))
                date = datetime(year=year, month=month, day=data, hour=5, minute=45)
                ticket['Norilsk']['Msc'].append(date.strftime('%d-%m-%Y %H:%M'))
            if data == 17:
                date = datetime(year=year, month=month, day=data, hour=20, minute=45)
                ticket['Spb']['Norilsk'].append(date.strftime('%d-%m-%Y %H:%M'))
                date = datetime(year=year, month=month, day=data, hour=15, minute=45)
                ticket['Norilsk']['Spb'].append(date.strftime('%d-%m-%Y %H:%M'))
            if month in range(4, 11):
                if data == 1 or data == 15 or data == 27:
                    date = datetime(year=year, month=month, day=data, hour=15)
                    ticket['Msc']['Anapa'].append(date.strftime('%d-%m-%Y %H:%M'))
                    date = datetime(year=year, month=month, day=data, hour=10)
                    ticket['Anapa']['Msc'].append(date.strftime('%d-%m-%Y %H:%M'))
                if data == 5 or data == 10:
                    date = datetime(year=year, month=month, day=data, hour=8)
                    ticket['Anapa']['Spb'].append(date.strftime('%d-%m-%Y %H:%M'))
                if data == 15 or data == 25:
                    date = datetime(year=year, month=month, day=data, hour=14)
                    ticket['Spb']['Anapa'].append(date.strftime('%d-%m-%Y %H:%M'))
        if month == 12:
            month = 0
            year += 1
        month += 1

    context['appropriate_flights'] = ticket[context['departure']][context['arrival']][:5]
    return True


def handler_flight(text, context):
    try:
        if int(text) in range(1, 6):
            context['time_of_flight'] = context['appropriate_flights'][int(text) - 1]
            return True
    except IndexError:
        return False


def handler_places(text, context):
    try:
        if int(text) in range(1, 6):
            context['places_amount'] = int(text)
            return True
        return False
    except TypeError:
        return False


def handler_comment(text, context):
    if text:
        context['comment'] = text
    else:
        context['comment'] = '-'
    return True


def handler_subtotals(text, context):
    if text.lower() == 'да':
        context['subtotals'] = True
        return True
    elif text.lower() == 'нет':
        context['subtotals'] = False
        return True
    else:
        return False


def handler_try_again(text, context):
    if text.lower() == 'да':
        context['try_again'] = True
    else:
        context['try_again'] = False
    return True


def handler_phone(text, context):
    match = re.match(pattern=re_phone, string=text)
    if match:
        context['phone'] = text
        return True
    else:
        return False


def get_name(user_id):
    html = requests.get(f'https://vk.com/id{user_id}').text
    soup = bs4.BeautifulSoup(html, 'html.parser')
    title = soup.find("title").string.split()
    name = title[0] + ' ' + title[1]
    return name


def generate_ticket_handler(context, user_id):
    date_and_time = datetime.strptime(context['time_of_flight'], '%d-%m-%Y %H:%M')
    date = date_and_time.strftime('%d-%m-%Y')
    time = date_and_time.strftime('%H:%M')
    return generate_ticket(
        name=get_name(user_id),
        departure=context['departure'],
        arrival=context['arrival'],
        date=date,
        time=time
    )
