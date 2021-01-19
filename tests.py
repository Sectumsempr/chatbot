import unittest
from copy import deepcopy

from pony.orm import db_session, rollback

import settings
from unittest.mock import patch, Mock

from vk_api.bot_longpoll import VkBotMessageEvent

from bot import Bot
from generate_ticket import generate_ticket
from settings import ticket
import datetime
from handlers import dispatcher


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()

    return wrapper


class BotTest(unittest.TestCase):
    RAW_EVENT = {
        'type': 'message_new',
        'object':
            {'message':
                 {'date': 1601213674, 'from_id': 101932713, 'id': 148, 'out': 0, 'peer_id': 101932713,
                  'text': '123', 'conversation_message_id': 147, 'fwd_messages': [], 'important': False,
                  'random_id': 0, 'attachments': [], 'is_hidden': False},
             'client_info':
                 {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'], 'keyboard': True,
                  'inline_keyboard': True, 'carousel': False, 'lang_id': 0}},
        'group_id': 198678183,
        'event_id': 'f103f467de10fd04333f66c291edde496991859b'}

    def test_run(self):
        count = 5
        obj = {'a': '1'}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                # bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%d-%m-%Y')
    INPUTS = [
        'Здравствуйте',
        '/ticket',
        'Моссква',
        'Москва',
        'Анааа',
        'Анапа',
        '/ticket',
        'Анапа',
        'Норильск',
        'Москва',
        '00-01-2020',
        tomorrow,
        '0',
        '2',
        '0',
        '2',
        '-',
        '+',
        'нет',
        'нет',
        '/ticket',
        'Санкт-Петербург',
        'Норильск',
        tomorrow,
        '1',
        '1',
        '-',
        'нет',
        'да',
        'Санкт-Петербург',
        'Норильск',
        tomorrow,
        '1',
        '1',
        '-',
        'да',
        '01',
        '89777448552',
        '/help'
    ]

    dispatcher(text=tomorrow, context={'departure': 'Msc', 'arrival': 'Anapa'})

    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,  # 'Здравствуйте'
        settings.SCENARIOS['booking_a_ticket']['steps']['step1']['text'],  # '/ticket'
        settings.SCENARIOS['booking_a_ticket']['steps']['step1']['failure_text'],  # 'Моссква'
        settings.SCENARIOS['booking_a_ticket']['steps']['step2']['text'],  # 'Москва'
        settings.SCENARIOS['booking_a_ticket']['steps']['step2']['failure_text'].format(
            cause='Для данного города нет авиабилетов. Для большей информации используйте /help'),  # 'Анааа'
        settings.SCENARIOS['booking_a_ticket']['steps']['step3']['text'],  # 'Анапа'
        settings.SCENARIOS['booking_a_ticket']['steps']['step1']['text'],  # '/ticket'
        settings.SCENARIOS['booking_a_ticket']['steps']['step2']['text'],  # 'Анапа'
        settings.SCENARIOS['booking_a_ticket']['steps']['step2']['failure_text'].format(
            cause='Между выбранными городами нет рейса'),  # 'Норильск'
        settings.SCENARIOS['booking_a_ticket']['steps']['step3']['text'],  # 'Москва'
        settings.SCENARIOS['booking_a_ticket']['steps']['step3']['failure_text'],  # '00-01-2020'
        settings.SCENARIOS['booking_a_ticket']['steps']['step4']['text'].format(
            appropriate_flights=ticket['Anapa']['Msc'][:5],
        ),  # tomorrow
        settings.SCENARIOS['booking_a_ticket']['steps']['step4']['failure_text'],  # '0'
        settings.SCENARIOS['booking_a_ticket']['steps']['step5']['text'],  # '2'
        settings.SCENARIOS['booking_a_ticket']['steps']['step5']['failure_text'],  # '0'
        settings.SCENARIOS['booking_a_ticket']['steps']['step6']['text'],  # '2'
        settings.SCENARIOS['booking_a_ticket']['steps']['step7']['text'].format(
            departure='Anapa', arrival='Msc', time_of_flight=ticket['Anapa']['Msc'][:5][1], comment='-'),  # '-'
        settings.SCENARIOS['booking_a_ticket']['steps']['step7']['failure_text'],  # '+'
        settings.SCENARIOS['booking_a_ticket']['steps']['step_is_ok']['text'],  # 'нет'
        settings.DEFAULT_ANSWER,  # 'нет'
        settings.SCENARIOS['booking_a_ticket']['steps']['step1']['text'],  # '/ticket'
        settings.SCENARIOS['booking_a_ticket']['steps']['step2']['text'],  # 'Санкт-Петербург'
        settings.SCENARIOS['booking_a_ticket']['steps']['step3']['text'],  # 'Норильск'
        settings.SCENARIOS['booking_a_ticket']['steps']['step4']['text'].format(
            appropriate_flights=ticket['Spb']['Norilsk'][:5]
        ),  # tomorrow
        settings.SCENARIOS['booking_a_ticket']['steps']['step5']['text'],  # '1'
        settings.SCENARIOS['booking_a_ticket']['steps']['step6']['text'],  # '1'
        settings.SCENARIOS['booking_a_ticket']['steps']['step7']['text'].format(
            departure='Spb', arrival='Norilsk', time_of_flight=ticket['Spb']['Norilsk'][:5][0], comment='-'
        ),  # '-'
        settings.SCENARIOS['booking_a_ticket']['steps']['step_is_ok']['text'],  # 'нет'
        settings.SCENARIOS['booking_a_ticket']['steps']['step1']['text'],  # 'да'
        settings.SCENARIOS['booking_a_ticket']['steps']['step2']['text'],  # 'Санкт-Петербург'
        settings.SCENARIOS['booking_a_ticket']['steps']['step3']['text'],  # 'Норильск'
        settings.SCENARIOS['booking_a_ticket']['steps']['step4']['text'].format(
            appropriate_flights=ticket['Spb']['Norilsk'][:5]
        ),  # tomorrow
        settings.SCENARIOS['booking_a_ticket']['steps']['step5']['text'],  # '1'
        settings.SCENARIOS['booking_a_ticket']['steps']['step6']['text'],  # '1'
        settings.SCENARIOS['booking_a_ticket']['steps']['step7']['text'].format(
            departure='Spb', arrival='Norilsk', time_of_flight=ticket['Spb']['Norilsk'][:5][0], comment='-'
        ),  # '-'
        settings.SCENARIOS['booking_a_ticket']['steps']['step8']['text'],  # 'да'
        settings.SCENARIOS['booking_a_ticket']['steps']['step8']['failure_text'],  # '01'
        settings.SCENARIOS['booking_a_ticket']['steps']['step9']['text'].format(phone='89777448552'),  # '89777448552'
        settings.DEFAULT_ANSWER  # '/help'
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()
        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []

        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_image_generation(self):
        with open('files//avatar.png', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()

        with patch('requests.get', return_value=avatar_mock):
            ticket_file = generate_ticket('Иван Иванов', 'Лондон', 'Париж', '31-12-2021', '16:00')

        with open('files//ticket_1.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()

        assert ticket_file.read() == expected_bytes