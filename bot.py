import logging, os
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import re
import paramiko
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error
import sys
import docker
import subprocess

TOKEN = os.getenv('TOKEN')

f = 0
str_ph = ''
str_em = ''

LOG_FILE_PATH = "/var/log/postgresql/postgresql.log"

dotenv_path = Path('../.env')
load_dotenv(dotenv_path=dotenv_path)
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')

host_db = os.getenv('DB_HOST')
username_db = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
port_db = os.getenv('DB_PORT')
db_database = os.getenv('DB_DATABASE')

host_ubuntu = '192.168.0.110'
username_ubuntu = 'ubuntu'

connection = None

'''logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)'''

def start(update, context):
    reply_keyboard = [['/help', '/find_phone_number', '/get_release', '/get_uname', '/get_free', '/get_mpstat', '/get_critical', '/get_apt_list', '/get_repl_logs', '/repl_logs'],
                      ['/find_email', '/verify_password', '/get_uptime', '/get_df', '/get_w', '/get_auths', '/get_ps', '/get_ss', '/get_services', '/get_emails', '/get_phone_numbers']]
    update.message.reply_text(
        'Выберите команду:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))

def help_command(update, context):
    update.message.reply_text("Есть всего 13 команд")

def find_phone_number(update, context):
    update.message.reply_text("Введите текст, из которого нужно найти телефонные номера:")
    global f
    f = 1

def find_email(update, context):
    update.message.reply_text("Введите текст, из которого нужно найти email адреса:")
    global f
    f = 2

def verify_password(update, context):
    update.message.reply_text("Введите пароль для проверки:")
    global f
    f = 3

def process_text_for_phone_numbers(text):
    phone_regex = r'(?:(?:\+7|8)[\s-]?)?\(?(?:\d{3})\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}'
    phone_numbers = re.findall(phone_regex, text)
    global str_ph
    str_ph = phone_numbers
    return phone_numbers

def handle_phone_number(update: Update, context: CallbackContext, text) -> None:
    phone_numbers = process_text_for_phone_numbers(text)
    if phone_numbers:
        update.message.reply_text("Найденные телефонные номера:\n" + "\n".join(phone_numbers))
        global f
        f = 5
        update.message.reply_text("Хотите записать в таблицу? Да/Нет")
    else:
        update.message.reply_text("Не найдено телефона")
    logging.info("Команда успешно выполнена.")

def process_text_for_emails(text):
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    global str_em
    str_em = emails
    return emails

def handle_emails(update: Update, context: CallbackContext, text) -> None:
    emails = process_text_for_emails(text)
    if emails:
        update.message.reply_text("Найденные почтовые адреса:\n" + "\n".join(emails))
        global f
        f = 6
        update.message.reply_text("Хотите записать в таблицу? Да/Нет")
    else:
        update.message.reply_text("Не найдено почтовых адресов")
    logging.info("Команда успешно выполнена.")

def proccess_text_for_verify_password(update: Update, context: CallbackContext, text) -> None:
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$'
    if re.match(pattern, text):
        update.message.reply_text("Пароль сложный")
    else:
        update.message.reply_text("Пароль простой")
    logging.info("Команда успешно выполнена.")

def establish_ssh_connection(host, username, password, port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    logging.info("Подключение выполнено.")
    return client

def establish_ssh_connection_db(host_deb, username_deb, password, port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host_ubuntu, username=username_ubuntu, password=password, port=port)
    logging.info("Подключение выполнено.")
    return client

def get_release(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("cat /etc/*-release")
    release_info = stdout.read().decode("utf-8")
    update.message.reply_text(release_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_uname(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("uname -a")
    system_info = stdout.read().decode("utf-8")
    update.message.reply_text(system_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_uptime(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("uptime")
    uptime_info = stdout.read().decode("utf-8")
    update.message.reply_text(uptime_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_df(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("df -h")
    df_info = stdout.read().decode("utf-8")
    update.message.reply_text(df_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_free(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("free -h")
    free_info = stdout.read().decode("utf-8")
    update.message.reply_text(free_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_mpstat(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("mpstat")
    mpstat_info = stdout.read().decode("utf-8")
    update.message.reply_text(mpstat_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_w(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("w")
    w_info = stdout.read().decode("utf-8")
    update.message.reply_text(w_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_auths(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("last -n 10")
    auths_info = stdout.read().decode("utf-8")
    update.message.reply_text(auths_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_critical(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("journalctl -p 0..3 -n 5")
    critical_info = stdout.read().decode("utf-8")
    update.message.reply_text(critical_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_ps(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("ps")
    ps_info = stdout.read().decode("utf-8")
    update.message.reply_text(ps_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_ss(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("ss -tuln")
    ss_info = stdout.read().decode("utf-8")
    update.message.reply_text(ss_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_apt_list(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Введите название пакета или None если всех ')
    global f
    f = 4

def find_apt_list(update: Update, context: CallbackContext, text) -> None:
    client = establish_ssh_connection(host, username, password, port)

    if text != 'None':
        stdin, stdout, stderr = client.exec_command('dpkg -l | grep {}'.format(text))
    else:
        stdin, stdout, stderr = client.exec_command('dpkg-query -Wf \'${Installed-Size}\t${Package}\n\' | sort -nr | head -n20')
    apt_info = stdout.read().decode("utf-8")
    update.message.reply_text(apt_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_services(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection(host, username, password, port)
    stdin, stdout, stderr = client.exec_command("service --status-all")
    services_info = stdout.read().decode("utf-8")
    update.message.reply_text(services_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def get_repl_logs(update: Update, context: CallbackContext) -> None:
    client = establish_ssh_connection_db(host_ubuntu, username_ubuntu, password, port)
    stdin, stdout, stderr = client.exec_command("grep repl_user /var/log/postgresql/postgresql-15-main.log |tail -n 20")
    services_info = stdout.read() + stderr.read()
    services_info = services_info.decode("utf-8")
    update.message.reply_text(services_info)
    client.close()
    logging.info("Команда успешно выполнена.")

def establish_db_connection(username_db, db_password, host_db, port_db, db_database):
    connection = psycopg2.connect(user=username_db,
                                  password=db_password,
                                  host=host_db,
                                  port=port_db,
                                  database=db_database)
    return connection

def establish_ubuntu_connection(host_ubuntu, username_ubuntu, password, port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host_ubuntu, username=username_ubuntu, password=password, port=port)
    logging.info("Подключение выполнено.")
    return client


def get_phone_numbers(update: Update, context: CallbackContext) -> None:
    connection = establish_db_connection(username_db, db_password, host_db, port_db, db_database)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Phones;")
    phones = cursor.fetchall()
    for row in phones:
        update.message.reply_text(str(row))
    logging.info("Команда успешно выполнена")
    cursor.close()
    connection.close()
    logging.info("Соединение с PostgreSQL закрыто")

def get_emails(update: Update, context: CallbackContext) -> None:
    connection = establish_db_connection(username_db, db_password, host_db, port_db, db_database)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Emails;")
    emails = cursor.fetchall()
    for row in emails:
        update.message.reply_text(str(row))
    logging.info("Команда успешно выполнена")
    cursor.close()
    connection.close()
    logging.info("Соединение с PostgreSQL закрыто")

def add_phones(update: Update, context: CallbackContext, str_ph) -> None:
    connection = establish_db_connection(username_db, db_password, host_db, port_db, db_database)
    cursor = connection.cursor()
    try:
        for i in str_ph:
            query = """
                INSERT INTO Phones (phone)
                VALUES (%s)
            """
            cursor.execute(query, (i,))

        connection.commit()
        logging.info("Команда успешно выполнена")
        update.message.reply_text("Запись успешно выполнена")

    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")

def add_emails(update: Update, context: CallbackContext, str_em) -> None:
    connection = establish_db_connection(username_db, db_password, host_db, port_db, db_database)
    cursor = connection.cursor()
    try:
        for i in str_em:
            query = """
                INSERT INTO Emails (email)
                VALUES (%s)
            """
            cursor.execute(query, (i,))

        connection.commit()
        logging.info("Команда успешно выполнена")
        update.message.reply_text("Запись успешно выполнена")

    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")

def repl_logs(update: Update, context: CallbackContext) -> None:
    try:
        # Выполнение команды для получения логов
        result = subprocess.run(
            ["bash", "-c", f"cat {LOG_FILE_PATH} | grep repl | tail -n 20"],
            capture_output=True,
            text=True,
            check=True  # Проверка наличия ошибок выполнения
        )
        logs = result.stdout
        if logs:
            update.message.reply_text(f"Последние репликационные логи:\n{logs}")
        else:
            update.message.reply_text("Репликационные логи не найдены.")
    except subprocess.CalledProcessError as e:
        update.message.reply_text(f"Ошибка при выполнении команды: {e}")
    except Exception as e:
        update.message.reply_text(f"Ошибка при получении логов: {str(e)}")

def handle_text_message(update, context):
    text = update.message.text

    if not text:
        return
    if text == "/help":
        help_command(update, context)
    elif text == "/find_phone_number":
        find_phone_number(update, context)
    elif text == "/find_email":
        find_email(update, context)
    elif text == "/verify_password":
        verify_password(update, context)
    elif text == "/get_release":
        get_release(update, context)
    elif text == "/get_uname":
        get_uname(update, context)
    elif text == "/get_uptime":
        get_uptime(update, context)
    elif text == "/get_df":
        get_df(update, context)
    elif text == "/get_free":
        get_free(update, context)
    elif text == "/get_mpstat":
        get_mpstat(update, context)
    elif text == "/get_w":
        get_w(update, context)
    elif text == "/get_auths":
        get_auths(update, context)
    elif text == "/get_critical":
        get_critical(update, context)
    elif text == "/get_ps":
        get_ps(update, context)
    elif text == "/get_ss":
        get_ss(update, context)
    elif text == "/get_apt_list":
        get_apt_list(update, context)
    elif text == "/get_services":
        get_services(update, context)
    elif text == "/get_rep_logs":
        get_repl_logs(update, context)
    elif text == "/get_phone_numbers":
        get_phone_numbers(update, context)
    elif text == "/get_emails":
        get_emails(update, context)
    elif text == "/repl_logs":
        repl_logs(update, context)
    else:
        if f == 1:
            handle_phone_number(update, context, text)
        elif f == 2:
            handle_emails(update, context, text)
        elif f == 3:
            proccess_text_for_verify_password(update, context, text)
        elif f == 4:
            find_apt_list(update, context, text)
        elif f == 5:
            if text == "Да":
                add_phones(update, context, str_ph)
            else:
                update.message.reply_text("Ваши номера не сохранены.")
        elif f == 6:
            if text == "Да":
                add_emails(update, context, str_em)
            else:
                update.message.reply_text("Ваши адреса не сохранены.")



def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("find_phone_number", find_phone_number))
    dp.add_handler(CommandHandler("find_email", find_email))
    dp.add_handler(CommandHandler("verify_password", verify_password))
    dp.add_handler(CommandHandler('get_release', get_release))
    dp.add_handler(CommandHandler('get_uname', get_uname))
    dp.add_handler(CommandHandler('get_uptime', get_uptime))
    dp.add_handler(CommandHandler('get_df', get_df))
    dp.add_handler(CommandHandler('get_free', get_free))
    dp.add_handler(CommandHandler('get_mpstat', get_mpstat))
    dp.add_handler(CommandHandler('get_w', get_w))
    dp.add_handler(CommandHandler('get_auths', get_auths))
    dp.add_handler(CommandHandler('get_critical', get_critical))
    dp.add_handler(CommandHandler('get_ps', get_ps))
    dp.add_handler(CommandHandler('get_ss', get_ss))
    dp.add_handler(CommandHandler('get_apt_list', get_apt_list, pass_args=True))
    dp.add_handler(CommandHandler('get_services', get_services))
    dp.add_handler(CommandHandler('get_repl_logs', get_repl_logs))
    dp.add_handler(CommandHandler('get_phone_numbers', get_phone_numbers))
    dp.add_handler(CommandHandler('get_emails', get_emails))
    dp.add_handler(CommandHandler('add_phones', add_phones))
    dp.add_handler(CommandHandler('repl_logs', repl_logs))
    dp.add_handler(CommandHandler("logs", repl_logs))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()