from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
TEMPLATE_PATH = "files//ticket.png"
FONT_PATH = "files//Roboto-Regular.ttf"
FONT_SIZE = 40

BLACK = (0, 0, 0, 255)
NAME_OFFSET = (1055, 200)
DEPARTURE_OFFSET = (250, 200)
ARRIVAL_OFFSET = (250, 290)
DATE_OFFSET = (275, 440)
TIME_OFFSET = (800, 440)
AVATAR_OFFSET = (1160, 290)
AVATAR_SIZE = 300


def transliterate(name):
    slovar = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
              'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
              'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h',
              'ц': 'c', 'ч': 'cz', 'ш': 'sh', 'щ': 'scz', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e',
              'ю': 'u', 'я': 'ja', 'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
              'Ж': 'ZH', 'З': 'Z', 'И': 'I', 'Й': 'I', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
              'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'H',
              'Ц': 'C', 'Ч': 'CZ', 'Ш': 'SH', 'Щ': 'SCH', 'Ъ': '', 'Ы': 'y', 'Ь': '', 'Э': 'E',
              'Ю': 'U', 'Я': 'YA', ',': '', '?': '', ' ': '+', '~': '', '!': '', '@': '', '#': '',
              '$': '', '%': '', '^': '', '&': '', '*': '', '(': '', ')': '', '-': '', '=': '',
              ':': '', ';': '', '<': '', '>': '', '\'': '', '"': '', '\\': '', '/': '', '№': '',
              '[': '', ']': '', '{': '', '}': '', 'ґ': '', 'ї': '', 'є': '', 'Ґ': 'g', 'Ї': 'i',
              'Є': 'e', '—': ''}
    for key in slovar:
        if key in slovar.keys():
            name = name.replace(key, slovar[key])
    return name


def generate_ticket(name, departure, arrival, date, time):
    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    draw = ImageDraw.Draw(base)
    draw.text(NAME_OFFSET, name, font=font, fill=BLACK)
    draw.text(DEPARTURE_OFFSET, departure, font=font, fill=BLACK)
    draw.text(ARRIVAL_OFFSET, arrival, font=font, fill=BLACK)
    draw.text(DATE_OFFSET, date, font=font, fill=BLACK)
    draw.text(TIME_OFFSET, time, font=font, fill=BLACK)
    response = requests.get(
        f'https://eu.ui-avatars.com/api/?name={transliterate(name)}&background=random&color=fff&size={AVATAR_SIZE}')
    avatar_file_like = BytesIO(response.content)
    avatar = Image.open(avatar_file_like)

    base.paste(avatar, AVATAR_OFFSET)

    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)
    
    return temp_file

