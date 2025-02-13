import asyncio
import csv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties


# Функция для загрузки конфигурации из файла
def load_config(filename="config.txt"):
    config = {}
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            key, value = line.strip().split("=", 1)
            config[key] = value
    return config


# Загружаем конфиг
config = load_config()
TOKEN = config.get("BOT_TOKEN")
MANAGER_CHAT_ID = int(config.get("MANAGER_CHAT_ID"))  # Убедитесь, что это правильный ID
REFERRAL_LINK = config.get("TG_CHANNEL")

# Инициализация бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Файл для хранения пользователей
users_file = "/users_data.csv"


# Функция для загрузки данных пользователей из CSV-файла
def load_users():
    users = []
    try:
        with open(users_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                users.append({"user_id": row["user_id"], "username": row["username"]})
    except FileNotFoundError:
        pass
    return users


# Функция для сохранения данных пользователей в CSV-файл
def save_users(users):
    with open(users_file, "w", encoding="utf-8", newline="") as file:
        fieldnames = ["user_id", "username"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)


# Клавиатура с кнопкой для получения бонуса (с использованием callback_data)
bonus_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Получить бонус", callback_data="get_bonus")]  # Заменяем url на callback_data
    ]
)


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Без никнейма"

    # Загружаем существующих пользователей и добавляем нового
    users = load_users()

    # Проверяем, не записан ли уже этот пользователь
    if not any(user["user_id"] == str(user_id) for user in users):
        # Если не записан, добавляем нового пользователя в список
        users.append({"user_id": str(user_id), "username": username})
        save_users(users)  # Сохраняем данные в файл

        # Отправляем сообщение в канал менеджера о новом пользователе
        try:
            await bot.send_message(MANAGER_CHAT_ID, f"👤 Новый пользователь!\n"
                                                    f"🔹 ID: {user_id}\n"
                                                    f"🔹 Никнейм: @{username}")
        except Exception as e:
            print(f"Ошибка при отправке в канал менеджера: {e}")  # Добавляем отладочную информацию

        # Сообщение пользователю о том, что его данные были сохранены
        await message.answer(
            "✅ Вы успешно зарегистрированы!\n"
            "Ваши данные были сохранены, и теперь вы можете получить бонус!\n\n"
            "🎁 Нажмите на кнопку ниже, чтобы получить свой бонус или фрибет.",
            reply_markup=bonus_keyboard  # Отправляем клавиатуру с бонусной ссылкой
        )

        # Пояснение для клиента
        await message.answer(
            "🔍 *Что произошло, когда вы нажали на 'Старт':*\n"
            "1. Ваши данные (ID: {user_id}, Никнейм: @{username}) были записаны в базу данных бота.\n"
            "2. Мы также отправили эти данные в специальный чат для вашего менеджера.\n"
            "3. Эти данные будут храниться в системе и могут быть использованы для различных целей (например, для рассылок, учета бонусов и т.д.).\n\n"
            "📊 Этот процесс помогает вам получить доступ к бонусам, а также улучшить работу с клиентами, так как их данные автоматически сохраняются."
        )
    else:
        # Если пользователь уже зарегистрирован, информируем его
        await message.answer(
            "👋 Привет снова! Вы уже зарегистрированы в системе.\n\n"
            "🎁 Получите свой бонус или фрибет прямо сейчас, нажав на кнопку ниже.",
            reply_markup=bonus_keyboard  # Отправляем клавиатуру с бонусной ссылкой
        )

        # Пояснение для клиента о повторной регистрации
        await message.answer(
            "🔍 *Что произошло, когда вы нажали на 'Старт':*\n"
            "1. Мы проверили, что вы уже зарегистрированы в нашей системе.\n"
            "2. Ваши данные (ID: {user_id}, Никнейм: @{username}) уже были сохранены ранее.\n"
            "3. Эти данные могут быть использованы для рассылок, бонусов и других нужд."
        )


# Обработка нажатия на кнопку "Получить бонус"
@dp.callback_query(lambda c: c.data == "get_bonus")
async def get_bonus(callback_query: types.CallbackQuery):
    # Ответ на нажатие кнопки
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Без никнейма"

    await callback_query.answer()  # Ответ на клик, чтобы не было "крутящегося" индикатора

    await bot.send_message(callback_query.from_user.id, "🔥 Вы перешли по бонусной ссылке! 🎉\n"
                                                        "Теперь зарегистрируйтесь на платформе и получите свой бонус.\n"
                                                        "После регистрации, бонус будет зачислен на ваш аккаунт.")

    # Пояснение для клиента
    await bot.send_message(callback_query.from_user.id,
                           "🔍 *Что происходит, когда вы нажимаете на 'Получить бонус':*\n"
                           "1. Вы переходите по реферальной ссылке, которая может привести на сайт для регистрации или получения бонуса.\n"
                           "2. После регистрации, бонус будет зачислен на ваш аккаунт.\n"
                           "3. Эти данные (ID и Никнейм) уже были сохранены, и вы получите бонус, который будет привязан к вашему аккаунту.")


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
