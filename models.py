
from pony.orm import Database, Required, Json
# psql -U postgres -d vk_chat_bot
from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Registration(db.Entity):
    phone = Required(str)
    departure = Required(str)
    arrival = Required(str)
    time_of_flight = Required(str)
    comment = Required(str)


db.generate_mapping(create_tables=True)
