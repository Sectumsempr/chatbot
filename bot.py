import logging

import requests
import vk_api
from random import randint

from pony.orm import db_session, pony

import handlers
from models import UserState, Registration
from settings import TOKEN, GROUP_ID
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

try:
    import settings
except ImportError:
    exit('Do cp settings.py.default settings.py and set TOKEN')

log = logging.getLogger("bot")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

file_handler = logging.FileHandler(filename="bot.log", encoding="UTF-8")
file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s", datefmt='%d-%m-%Y %H:%M'))

log.addHandler(stream_handler)
log.addHandler(file_handler)
log.setLevel(logging.DEBUG)
file_handler.setLevel(logging.INFO)
stream_handler.setLevel(logging.INFO)


class Bot:
    """
    Echo bot for vk.com

    Use python3.8.5
    """

    def __init__(self, group_id, token):
        """
        :param group_id: ID of group VK
        :param token: sicret token from group VK
        """
        self.group_id = group_id
        self.token = token

        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(vk=self.vk, group_id=self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """Run the bot"""
        for event in self.long_poller.listen():
            try:
                self.on_event(event=event)
            except Exception as exc:
                log.exception(f'ОШИБКА! {exc}')

    @db_session
    def on_event(self, event):
        """
        Message Handling - Send messages back if the message is text
        :param event: VkBotEventType
        :return:
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.debug(f"Неизвестный {event.type}")
            return

        user_id = event.message['peer_id']
        text = event.object.message['text']

        state = UserState.get(user_id=str(user_id))

        if not self.got_intent(state, text, user_id):
            if state is not None:
                self.continue_scenario(text=text, state=state, user_id=user_id)
            else:
                self.send_text(settings.DEFAULT_ANSWER, user_id)

    def got_intent(self, state, text, user_id):
        for intent in settings.INTENTS:
            log.debug(f"User {state} got an intent {intent}")
            if any(token in text.lower() for token in intent['tokens']):
                if intent['answer']:
                    self.send_text(intent['answer'], user_id)
                else:
                    self.start_scenario(scenario_name=intent['scenario'], user_id=user_id, state=state, text=text)
                return True
        return False

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(
            message=text_to_send,
            random_id=randint(0, 2 ** 10),
            peer_id=user_id
        )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        owner_id = image_data[0]['owner_id']
        photo_id = image_data[0]['id']
        attachments = f"photo{owner_id}_{photo_id}"
        self.api.messages.send(
            attachment=attachments,
            random_id=randint(0, 2 ** 10),
            peer_id=user_id
        )

    def send_step(self, step, user_id, text, context, text_to_send=None):
        if text_to_send:
            self.send_text(text_to_send, user_id)
        elif 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(context, user_id)
            self.send_image(image, user_id)

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            state_deleted = False
            if 'subtotals' in state.context and state.context['subtotals']:
                step_str = steps[state.step_name]['next_step']
                step = steps[step_str]
                state.context['subtotals'] = False

            next_step = steps[step['next_step']]
            if 'try_again' in state.context and state.context['try_again']:
                self.start_scenario(state.scenario_name, user_id, state, text)
                state_deleted = True

            elif 'try_again' in state.context and not state.context['try_again']:
                self.send_text(settings.DEFAULT_ANSWER, user_id)
                state_deleted = True
                state.delete()
            else:
                self.send_step(next_step, user_id, text, state.context)

            if not state_deleted:
                if next_step['next_step']:
                    state.step_name = step['next_step']
                else:
                    log.info('Зарегистрирован: {phone}\nГород отправления: {departure}\nГород назначения: '
                             '{arrival}\nВыбранные вами дата и время отправления: {time_of_flight}. '
                             'Комментарий: {comment}'.format(**state.context))
                    Registration(
                        phone=state.context['phone'],
                        departure=state.context['departure'],
                        arrival=state.context['arrival'],
                        time_of_flight=state.context['time_of_flight'],
                        comment=state.context['comment'],
                    )
                    state.delete()
        else:
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(text_to_send, user_id)

    def start_scenario(self, scenario_name, user_id, state, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        try:
            UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})
            self.send_step(step, user_id, text, context={})
        except pony.orm.core.CacheIndexError:
            state.delete()
            self.start_scenario(scenario_name, user_id, state, text)


if __name__ == '__main__':
    bot = Bot(group_id=GROUP_ID, token=TOKEN)
    bot.run()
