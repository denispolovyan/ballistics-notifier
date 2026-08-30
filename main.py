import asyncio
import os
import re
import subprocess
from datetime import datetime, timedelta

from telethon import TelegramClient, events

from config import (
    API_ID,
    API_HASH,
    SESSION_NAME,
    CONTROL_CHAT,
    SOUND_DURATION,
    CHANNELS,
    KEYWORDS,
    SOUND_FILE,
    HISTORY_FILE,
)


# ============================================================
# ГЛОБАЛЬНІ ЗМІННІ
# ============================================================

# До якого часу звук вимкнений через "stop N".
# None = таймер не встановлений.
sound_disabled_until = None

# True = звук вимкнений командою "stop"
# без обмеження часу.
sound_disabled_permanently = False

# True = звук зараз грає.
#
# Якщо True, нові сигнали НЕ ставляться в чергу.
sound_playing = False


# ============================================================
# TELEGRAM CLIENT
# ============================================================

client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH
)


# ============================================================
# WATCHING
# ============================================================

def stop_watching(minutes=None):
    """
    Вимикає звукові сповіщення.

    minutes=None:
        вимкнення без обмеження часу.

    minutes=30:
        вимкнення на 30 хвилин.
    """

    global sound_disabled_until
    global sound_disabled_permanently

    # --------------------------------------------------------
    # БЕЗСТРОКОВИЙ STOP
    # --------------------------------------------------------

    if minutes is None:

        sound_disabled_permanently = True
        sound_disabled_until = None

        print()
        print("=" * 60)
        print("WATCHING ЗУПИНЕНО")
        print("Звукові сповіщення вимкнені безстроково.")
        print("Для відновлення напиши: start")
        print("=" * 60)
        print()

        return

    # --------------------------------------------------------
    # STOP НА N ХВИЛИН
    # --------------------------------------------------------

    if minutes <= 0:
        return

    sound_disabled_permanently = False

    sound_disabled_until = (
        datetime.now()
        + timedelta(minutes=minutes)
    )

    print()
    print("=" * 60)
    print("WATCHING ЗУПИНЕНО")
    print(
        f"Звукові сповіщення вимкнені "
        f"на {minutes} хвилин."
    )
    print(
        "До:",
        sound_disabled_until.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    print("=" * 60)
    print()


def start_watching():
    """
    Повністю вмикає звукові сповіщення.
    """

    global sound_disabled_until
    global sound_disabled_permanently

    sound_disabled_until = None
    sound_disabled_permanently = False

    print()
    print("=" * 60)
    print("WATCHING ВІДНОВЛЕНО")
    print("Звукові сповіщення увімкнені.")
    print("=" * 60)
    print()


def sound_allowed():
    """
    Перевіряє, чи дозволено зараз відтворювати звук.
    """

    global sound_disabled_until
    global sound_disabled_permanently

    # --------------------------------------------------------
    # БЕЗСТРОКОВИЙ STOP
    # --------------------------------------------------------

    if sound_disabled_permanently:
        return False

    # --------------------------------------------------------
    # STOP НЕ АКТИВНИЙ
    # --------------------------------------------------------

    if sound_disabled_until is None:
        return True

    # --------------------------------------------------------
    # ТАЙМЕР ЗАКІНЧИВСЯ
    # --------------------------------------------------------

    if datetime.now() >= sound_disabled_until:

        sound_disabled_until = None

        print(
            "[WATCHING] Час паузи закінчився."
        )

        return True

    # --------------------------------------------------------
    # STOP ЩЕ ДІЄ
    # --------------------------------------------------------

    return False


# ============================================================
# HISTORY.TXT
# ============================================================

def write_history(keyword, channel_name):
    """
    Додає збіг у history.txt.

    Формат:

    2026-08-30 22:10:15 - слово - Назва каналу
    """

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    line = (
        f"{current_time} - "
        f"{keyword} - "
        f"{channel_name}\n"
    )

    try:

        with open(
            HISTORY_FILE,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(line)

    except Exception as e:

        print(
            f"[HISTORY ERROR] {e}"
        )


# ============================================================
# ЗВУК
# ============================================================

async def play_sound():
    """
    Відтворює звук максимум SOUND_DURATION секунд.

    Якщо звук уже грає, новий сигнал
    повністю ігнорується і в чергу не додається.
    """

    global sound_playing

    # --------------------------------------------------------
    # ПЕРЕВІРКА ЧИ ВЖЕ ГРАЄ ЗВУК
    # --------------------------------------------------------

    if sound_playing:

        print(
            "[SOUND] Звук уже грає."
        )

        print(
            "[SOUND] Новий сигнал "
            "не додається в чергу."
        )

        return

    # --------------------------------------------------------
    # ПЕРЕВІРКА ФАЙЛУ
    # --------------------------------------------------------

    if not os.path.exists(SOUND_FILE):

        print(
            "[ERROR] Файл звуку не знайдено:"
        )

        print(
            SOUND_FILE
        )

        return

    # --------------------------------------------------------
    # ПОЗНАЧАЄМО, ЩО ЗВУК ГРАЄ
    # --------------------------------------------------------

    sound_playing = True

    process = None

    print(
        "[SOUND] Початок відтворення:"
    )

    print(
        SOUND_FILE
    )

    try:

        # ----------------------------------------------------
        # AFPLAY
        # ----------------------------------------------------

        process = subprocess.Popen(
            [
                "afplay",
                SOUND_FILE
            ]
        )

        # ----------------------------------------------------
        # ЧЕКАЄМО АБО ЗАВЕРШЕННЯ ФАЙЛУ,
        # АБО SOUND_DURATION СЕКУНД
        # ----------------------------------------------------

        try:

            await asyncio.wait_for(
                asyncio.to_thread(
                    process.wait
                ),
                timeout=SOUND_DURATION
            )

            print(
                "[SOUND] Файл закінчився."
            )

        except asyncio.TimeoutError:

            print(
                f"[SOUND] Минуло "
                f"{SOUND_DURATION} секунд."
            )

            print(
                "[SOUND] Зупиняю."
            )

            if process.poll() is None:

                process.terminate()

                try:

                    await asyncio.to_thread(
                        process.wait,
                        timeout=1
                    )

                except subprocess.TimeoutExpired:

                    process.kill()

    except Exception as e:

        print(
            f"[SOUND ERROR] {e}"
        )

    finally:

        # ----------------------------------------------------
        # ТЕПЕР МОЖНА РЕАГУВАТИ НА НОВИЙ ЗБІГ
        # ----------------------------------------------------

        sound_playing = False

        print(
            "[SOUND] Готовий до нового сигналу."
        )


# ============================================================
# НАЗВА КАНАЛУ
# ============================================================

async def get_channel_name(event):

    try:

        chat = await event.get_chat()

        return getattr(
            chat,
            "title",
            "Невідомий канал"
        )

    except Exception:

        return "Невідомий канал"


# ============================================================
# ПЕРЕВІРКА КОНТРОЛЬНОГО ЧАТУ
# ============================================================

async def is_control_chat(event):
    """
    Перевіряє, чи повідомлення прийшло
    з CONTROL_CHAT.
    """

    try:

        chat = await event.get_chat()

        username = getattr(
            chat,
            "username",
            None
        )

        if not username:
            return False

        return (
            username.lower()
            == CONTROL_CHAT.lower()
        )

    except Exception:

        return False


# ============================================================
# НОВЕ ПОВІДОМЛЕННЯ
# ============================================================

@client.on(
    events.NewMessage(
        chats=CHANNELS
    )
)
async def new_message(event):

    text = event.raw_text

    if not text:
        return

    text_clean = text.strip()

    text_lower = text_clean.lower()


    # ========================================================
    # START
    # ========================================================

    if text_lower == "start":

        if await is_control_chat(event):

            start_watching()

        return


    # ========================================================
    # STOP
    # ========================================================

    if text_lower == "stop":

        if await is_control_chat(event):

            stop_watching()

        return


    # ========================================================
    # STOP N
    # ========================================================

    match = re.fullmatch(
        r"stop\s+(\d+)",
        text_lower
    )

    if match:

        if await is_control_chat(event):

            minutes = int(
                match.group(1)
            )

            if minutes > 0:

                stop_watching(
                    minutes
                )

        return


    # ========================================================
    # НАЗВА КАНАЛУ
    # ========================================================

    channel_name = await get_channel_name(
        event
    )


    # ========================================================
    # ПОШУК КЛЮЧОВИХ СЛІВ
    # ========================================================

    matched_keywords = []

    for keyword in KEYWORDS:

        if keyword.lower() in text_lower:

            matched_keywords.append(
                keyword
            )


    # Якщо збігів немає
    if not matched_keywords:

        return


    # ========================================================
    # ВИВЕДЕННЯ ЗБІГУ
    # ========================================================

    print()
    print("=" * 60)
    print("ЗНАЙДЕНО ЗБІГ")
    print("=" * 60)

    print(
        f"Канал: {channel_name}"
    )

    print(
        "Ключові слова:",
        ", ".join(
            matched_keywords
        )
    )

    print()
    print("Повідомлення:")
    print(text)

    print("=" * 60)


    # ========================================================
    # HISTORY
    # ========================================================

    for keyword in matched_keywords:

        write_history(
            keyword,
            channel_name
        )


    # ========================================================
    # ПЕРЕВІРКА STOP
    # ========================================================

    if not sound_allowed():

        print(
            "[SOUND] Звукові сповіщення "
            "вимкнені."
        )

        return


    # ========================================================
    # ПЕРЕВІРКА ЧИ ВЖЕ ГРАЄ
    # ========================================================

    if sound_playing:

        print(
            "[SOUND] Попередній сигнал "
            "ще грає."
        )

        print(
            "[SOUND] Новий сигнал "
            "ігнорується."
        )

        return


    # ========================================================
    # ЗАПУСК ЗВУКУ
    # ========================================================

    asyncio.create_task(
        play_sound()
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    print()
    print("=" * 60)
    print("TELEGRAM MONITOR")
    print("=" * 60)
    print()


    # --------------------------------------------------------
    # ПІДКЛЮЧЕННЯ ДО TELEGRAM
    # --------------------------------------------------------

    print(
        "Підключення до Telegram..."
    )

    await client.start()


    # --------------------------------------------------------
    # АКАУНТ
    # --------------------------------------------------------

    me = await client.get_me()

    print(
        f"Авторизовано як: "
        f"{me.first_name}"
    )

    if getattr(
        me,
        "username",
        None
    ):

        print(
            f"Username: @{me.username}"
        )


    # --------------------------------------------------------
    # КАНАЛИ
    # --------------------------------------------------------

    print()
    print(
        "Канали для моніторингу:"
    )

    for channel in CHANNELS:

        print(
            f"  - {channel}"
        )


    # --------------------------------------------------------
    # КЛЮЧОВІ СЛОВА
    # --------------------------------------------------------

    print()
    print(
        "Ключові слова:"
    )

    for keyword in KEYWORDS:

        print(
            f"  - {keyword}"
        )


    # --------------------------------------------------------
    # НАЛАШТУВАННЯ
    # --------------------------------------------------------

    print()

    print(
        f"Контрольний чат: "
        f"{CONTROL_CHAT}"
    )

    print(
        f"Назва сесії: "
        f"{SESSION_NAME}"
    )

    print(
        f"Файл історії: "
        f"{HISTORY_FILE}"
    )

    print(
        f"Файл звуку: "
        f"{SOUND_FILE}"
    )

    print(
        f"Тривалість звуку: "
        f"{SOUND_DURATION} секунд"
    )


    # --------------------------------------------------------
    # ГОТОВО
    # --------------------------------------------------------

    print()
    print("=" * 60)

    print(
        "Моніторинг запущено."
    )

    print(
        "Очікування нових повідомлень..."
    )

    print("=" * 60)
    print()


    # --------------------------------------------------------
    # ПОСТІЙНА РОБОТА
    # --------------------------------------------------------

    await client.run_until_disconnected()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print()
        print(
            "Програму зупинено."
        )