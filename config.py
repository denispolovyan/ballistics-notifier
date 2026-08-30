# telegram app constants
# https://my.telegram.org/ (log in) -> Api development tools -> create app

API_ID = 111111 # api_id застосунку
API_HASH = "abcdefg1234567" #api_hash застосунку

SESSION_NAME = "ballistics_monitor"

CONTROL_CHAT = "control_chat"

SOUND_DURATION = 15

KEYWORDS = [
    "баллистика на Киев",
    "баллистики на Киев",
    "вихід на Київ",    
    "вихід БР на Київ",
    "вихід БР Київ",    
    "вихід балістики Київ",
    "вихід у напрямку Київ",    
    "Київ балістика",
    "балістика Київ",
    "Київ — спуск балістики",
    "балістика на Київ",
    # реєтр не враховується
]

CHANNELS = [
    "vanek_nikolaev",
    "kpszsu",
    "chyste_nebo",
    "war_monitor",
    "control_chat", # щоб перевіряти роботу програму ключовими словами
]

SOUND_FILE = "sounds/ballistics.mp3" 
# звук що буде програватись

HISTORY_FILE = "history.txt" 
# журнал спрацювань