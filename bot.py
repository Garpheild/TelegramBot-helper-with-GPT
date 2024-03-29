import telebot
from telebot import types
from config import *
import gpt
import logging
import database as db


logging.basicConfig(filename="logs.txt", encoding="utf-8", level=logging.DEBUG, filemode="w",
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(TOKEN)


def add_buttons(buttons):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=["help_with_math"])
def math(message):
    db.insert_user_to_db(message.chat.id)
    db.update_db(chat_id=message.chat.id, columns=("subject", "task", "gpt_answer"), values=("математика", None, None))
    bot.send_message(message.chat.id, "Отправьте задачу")
    bot.register_next_step_handler(message, send_answer)


@bot.message_handler(commands=["help_with_physics"])
def physics(message):
    db.insert_user_to_db(message.chat.id)
    db.update_db(chat_id=message.chat.id, columns=("subject", "task", "gpt_answer"), values=("физика", None, None))
    bot.send_message(message.chat.id, "Отправьте задачу")
    bot.register_next_step_handler(message, send_answer)


@bot.message_handler(commands=["change_difficulty_level"])
def change_level(message):
    def level(message1):
        if message1.text == "Легкий":
            db.update_db(chat_id=message1.chat.id, columns=("level",), values=("легкий",))
            bot.send_message(message.chat.id, "Уровень обновлен на Легкий", reply_markup=add_buttons(["/help_with_math", "/help_with_physics"]))
            logging.info("Уровень сложности изменен на легкий")
        elif message1.text == "Продвинутый":
            db.update_db(chat_id=message1.chat.id, columns=("level",), values=("продвинутый",))
            bot.send_message(message.chat.id, "Уровень обновлен на Продвинутый", reply_markup=add_buttons(["/help_with_math", "/help_with_physics"]))
            logging.info("Уровень сложности изменен на продвинутый")
        else:
            bot.send_message(message.chat.id, "Выберите уровень сложности из списка",
                             reply_markup=add_buttons(["Легкий", "Продвинутый"]))
            bot.register_next_step_handler(message, level)
            return
    db.insert_user_to_db(message.chat.id)
    bot.send_message(message.chat.id, "Выберите уровень сложности объяснения", reply_markup=add_buttons(["Легкий", "Продвинутый"]))
    bot.register_next_step_handler(message, level)


@bot.message_handler(func=lambda message: message.text == "Продолжить ответ")
def continue_answer(message):
    if [_ for _ in db.get_data_from_db(message.chat.id, columns="gpt_answer")]:
        answer = gpt.get_answer(
            subjectlevel="".join([_ for _ in db.get_data_from_db(message.chat.id, "subject, level")][0]),
            assistant_content=f"Продолжи решение задачи {[_ for _ in db.get_data_from_db(message.chat.id, 'task')][0][0]}",
            request=f" {[_ for _ in db.get_data_from_db(message.chat.id, 'gpt_answer')][0][0]}"
        )
        if answer == "":
            bot.send_message(message.chat.id, "Ответ закончен",
                             reply_markup=add_buttons(
                                 ["/help_with_math", "/help_with_physics", "/change_difficulty_level"]))
            logging.info("Ответ нейросети закончен")
        else:
            db.update_db(chat_id=message.chat.id, columns=("gpt_answer",), values=(answer,), replace=False)
            bot.send_message(message.chat.id, answer, reply_markup=add_buttons(["Закончить диалог", "Продолжить ответ"]))
    else:
        bot.send_message(message.chat.id, "Сначала отправьте задачу")
        logging.warning("Бот не может продолжить обьяснение без задачи")
        bot.register_next_step_handler(message, continue_answer)
        return


def send_answer(message):
    if message.content_type != "text":
        bot.send_message(message.chat.id, "Введите текстовый запрос")
        logging.warning("Не текстовый запрос")
        bot.register_next_step_handler(message, send_answer)
        return

    if not gpt.check_prompt_len(message.text):
        bot.send_message(message.chat.id, "Слишком длинный запрос")
        logging.warning("Слишком длинный запрос")
        bot.register_next_step_handler(message, send_answer)
        return

    answer = gpt.get_answer(request=message.text,
                            subjectlevel="".join([_ for _ in db.get_data_from_db(message.chat.id, "subject, level")][0]))
    db.update_db(message.chat.id, columns=("task", "gpt_answer"), values=(message.text, answer))

    bot.send_message(message.chat.id, answer, reply_markup=add_buttons(["Закончить диалог", "Продолжить ответ"]))


@bot.message_handler(func=lambda message: message.text == "Закончить диалог")
def end(message):
    if not [_ for _ in db.get_data_from_db(message.chat.id)]:
        logging.warning("Пользователь пытался закончить диалог не начав его")
        bot.send_message(message.chat.id, "Чтобы закончить диалог его нужно начать")
    else:
        bot.send_message(message.chat.id, "Приятно было пообщаться",
                         reply_markup=add_buttons(["/help_with_math", "/help_with_physics", "/change_difficulty_level"]))
        db.update_db(chat_id=message.chat.id, columns=("task", "gpt_answer"), values=(None, None))


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id,
                     f"Привет, {message.from_user.first_name}",
                     reply_markup=add_buttons(["/help_with_math", "/help_with_physics", "/change_difficulty_level"]))
    db.insert_user_to_db(message.chat.id)


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, "Для запроса к нейросети выберите: /help_with_math /help_with_physics\n"
                                      "Для смены сложности выберите /change_difficulty_level",
                     reply_markup=add_buttons(["/help_with_math", "/help_with_physics", "/change_difficulty_level"]))


@bot.message_handler(commands=["debug"])
def debug(message):
    with open("logs.txt", "rb") as logs:
        bot.send_document(message.chat.id, logs)


@bot.message_handler(func=lambda message: True)
def text_message(message):
    bot.send_message(message.chat.id, "Для запроса к нейросети выберите: /help_with_math /help_with_physics\n"
                                      "Для смены сложности выберите /change_difficulty_level",
                     reply_markup=add_buttons(["/help_with_math", "/help_with_physics", "/change_difficulty_level"]))
    db.insert_user_to_db(message.chat.id)


if __name__ == "__main__":
    bot.infinity_polling()
    logging.info("Бот запущен")
