import os
from pathlib import Path
from dotenv import load_dotenv


env_path = Path('.env')
load_dotenv(dotenv_path=env_path)
SECRET_KEY = os.getenv("SECRET_KEY")
PGDATABASE = os.getenv("PGDATABASE", "postgres")
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "2667")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "password")

settings = {
    'token': SECRET_KEY,
    'bot': 'Hydrargyrum',
    'id': 723535015811481663,
    'prefix': '$'
}

# Moderation
WHITELIST = [724727558847070379, 726787647627853854, 726782615230742549, 726779488947666987]
owner_role_id = 724727558847070379
deputy_role_id = 726787647627853854
admin_role_id = 726782615230742549  # Elixir
moder_role_id = 726779488947666987  # Polizei

# Channels
WELCOME_CHANNEL = 723636661334048768
COMMAND_CHANNEL = 723539840796328051
CHAT_CHANNEL = 723649994443456603
IDEAS_CHANNEL = 723650807022616586

# Message
REACTION_MESSAGE = 731602150261653515

desc_errors = {
    'manage_roles': 'У вас нет соответствующих прав для использование этой команды!\n'
                    'Необходимые права: `Управлять ролями`',
    'manage_messages': 'У вас нет соответствующих прав для использование этой команды!\n'
                       'Необходимые права: `Управлять сообщениями`',
    'miss_any_roles': 'У вас нет соответствующих прав для использование этой команды!',
    'miss_req_arg': 'Вы не определили необходимые аргументы.',
    'need_more': 'Укажите корректные данные.\n'
                 'Название должно содержать больше 2 символов.',
    'need_more+': 'Укажите корректные данные.\n'
                  'Название должно содержать больше 2 символов. \n'
                  'Стоимость должна быть больше 0 или должна быть числом.',
    'shop_not_found': 'Укажите корректные данные.\n'
                      'Данного магазина не существует.'
}
