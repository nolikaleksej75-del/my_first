import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
from datetime import datetime
import traceback
import time
import requests

# ============ КОНФИГУРАЦИЯ ============
TOKEN = '8717752281:AAFcE_fNSLQHoFgEY8EYV0dVnp5wlqwZGpU'
ADMIN_ID = 1531814351

bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'zapis.json'
SETTINGS_FILE = 'settings.json'
COMMANDERS_FILE = 'commanders.json'
USERS_FILE = 'users.json'

# Дни недели
DAYS_RU = {
    'monday': 'Понедельник',
    'tuesday': 'Вторник',
    'wednesday': 'Среда',
    'thursday': 'Четверг',
    'friday': 'Пятница',
    'saturday': 'Суббота',
    'sunday': 'Воскресенье'
}

# Взводы
PLATOONS = {
    721: "721 взвод",
    722: "722 взвод",
    723: "723 взвод"
}

# Структура для хранения командиров и старшины
DATA_STRUCTURE = {
    'commanders': {
        721: [],
        722: [],
        723: []
    },
    'starhina': []
}

# ============ ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ============
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_users(users):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except:
        pass

def add_user(user_id, user_info):
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            return
    users.append({
        'id': user_id,
        'first_name': user_info.first_name,
        'username': user_info.username,
        'last_name': user_info.last_name,
        'added_at': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    })
    save_users(users)

def load_commanders_data():
    global DATA_STRUCTURE
    if os.path.exists(COMMANDERS_FILE):
        try:
            with open(COMMANDERS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    if 'commanders' in loaded and 'starhina' in loaded:
                        DATA_STRUCTURE = loaded
                    else:
                        DATA_STRUCTURE = {'commanders': {721: [], 722: [], 723: []}, 'starhina': []}
                        for key, value in loaded.items():
                            if str(key).isdigit() and int(key) in DATA_STRUCTURE['commanders']:
                                if isinstance(value, list):
                                    DATA_STRUCTURE['commanders'][int(key)] = value
                                elif isinstance(value, dict) and 'id' in value:
                                    if value['id']:
                                        DATA_STRUCTURE['commanders'][int(key)].append(value['id'])
                save_commanders_data()
        except Exception as e:
            print(f"Ошибка загрузки командиров: {e}")
            DATA_STRUCTURE = {'commanders': {721: [], 722: [], 723: []}, 'starhina': []}
            save_commanders_data()
    else:
        save_commanders_data()

def save_commanders_data():
    try:
        with open(COMMANDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DATA_STRUCTURE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения командиров: {e}")

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_starhina(user_id):
    return user_id in DATA_STRUCTURE.get('starhina', [])

def is_commander(user_id):
    commanders = DATA_STRUCTURE.get('commanders', {})
    for platoon, lst in commanders.items():
        if user_id in lst:
            return platoon
    return None

def has_commander_permissions(user_id):
    if is_admin(user_id):
        return True
    if is_starhina(user_id):
        return True
    if is_commander(user_id) is not None:
        return True
    return False

def get_user_role_string(user_id):
    if is_admin(user_id):
        return "👑 Главный администратор"
    if is_starhina(user_id):
        return "⭐ Старшина курса"
    platoon = is_commander(user_id)
    if platoon and platoon in PLATOONS:
        return f"🎖️ Командир {PLATOONS[platoon]}"
    return "👤 Пользователь"

def get_available_platoons_for_user(user_id):
    if is_admin(user_id):
        return list(PLATOONS.keys())
    if is_starhina(user_id):
        return list(PLATOONS.keys())
    platoon = is_commander(user_id)
    if platoon:
        return [platoon]
    return []

def can_manage_platoon(user_id, platoon):
    if is_admin(user_id):
        return True
    if is_starhina(user_id):
        return True
    return is_commander(user_id) == platoon

def is_day_enabled(day_key):
    settings = load_settings()
    return settings.get(day_key, True)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {day: [] for day in DAYS_RU.keys()}
    return {day: [] for day in DAYS_RU.keys()}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {day: True for day in DAYS_RU.keys()}
    return {day: True for day in DAYS_RU.keys()}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except:
        pass

# ============ ФУНКЦИИ РАССЫЛКИ ============
def send_broadcast(message_text, sender_id):
    """Отправляет сообщение всем пользователям"""
    users = load_users()
    success_count = 0
    fail_count = 0
    
    for user in users:
        try:
            bot.send_message(user['id'], message_text, parse_mode='Markdown')
            success_count += 1
            time.sleep(0.05)  # Задержка чтобы не превысить лимиты Telegram
        except Exception as e:
            fail_count += 1
            print(f"Не удалось отправить пользователю {user['id']}: {e}")
    
    # Отправляем отчет администратору
    report = (
        f"✅ **Рассылка завершена!**\n\n"
        f"📨 **Отправлено:** {success_count} пользователям\n"
        f"❌ **Не доставлено:** {fail_count} пользователям\n"
        f"📊 **Всего в базе:** {len(users)} пользователей"
    )
    bot.send_message(sender_id, report, parse_mode='Markdown')
    return success_count, fail_count

# ============ ОПОВЕЩЕНИЯ ============
def notify_commander_about_new_record(platoon, record_info):
    commanders = DATA_STRUCTURE.get('commanders', {}).get(platoon, [])
    starhinas = DATA_STRUCTURE.get('starhina', [])
    all_to_notify = commanders + starhinas
    if not all_to_notify:
        return
    message_text = (
        f"🔔 **НОВАЯ ЗАПИСЬ В ВАШЕМ ВЗВОДЕ!** 🔔\n\n"
        f"👤 **Курсант:** {record_info['surname']}\n"
        f"📅 **День:** {record_info['day_name']}\n"
        f"🕐 **Время записи:** {record_info['time']}\n"
        f"🆔 **ID курсанта:** `{record_info['user_id']}`\n\n"
        f"💡 /commander – управление записями"
    )
    for cid in all_to_notify:
        try:
            bot.send_message(cid, message_text, parse_mode='Markdown')
            time.sleep(0.05)
        except:
            pass

def notify_all_users_about_close(day_name):
    users = load_users()
    message_text = (
        f"🔔 **ОПОВЕЩЕНИЕ О ЗАКРЫТИИ ЗАПИСИ** 🔔\n\n"
        f"📅 Запись на **{day_name}** завершена!\n\n"
        f"⏰ **Через 30 минут списки будут готовы.**\n\n"
        f"🎖️ **Командиры и старшина!**\nУ вас есть время почистить записи.\n\n"
        f"/commander – управление"
    )
    success = 0
    for user in users:
        try:
            bot.send_message(user['id'], message_text, parse_mode='Markdown')
            success += 1
            time.sleep(0.05)
        except:
            pass
    return success

# ============ КЛАВИАТУРЫ ============
def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📝 Записаться", callback_data="new_zapis"),
        InlineKeyboardButton("ℹ️ О боте", callback_data="about_bot")
    )
    kb.add(
        InlineKeyboardButton("🆔 Мой ID", callback_data="show_my_id"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return kb

def days_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    btns = []
    for dk, dn in DAYS_RU.items():
        if is_day_enabled(dk):
            btns.append(InlineKeyboardButton(f"✅ {dn}", callback_data=f"day_{dk}"))
        else:
            btns.append(InlineKeyboardButton(f"❌ {dn}", callback_data="disabled_day"))
    for i in range(0, len(btns), 2):
        if i+1 < len(btns):
            kb.add(btns[i], btns[i+1])
        else:
            kb.add(btns[i])
    kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return kb

def platoon_keyboard():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("721 взвод", callback_data="platoon_721"),
        InlineKeyboardButton("722 взвод", callback_data="platoon_722"),
        InlineKeyboardButton("723 взвод", callback_data="platoon_723")
    )
    kb.add(InlineKeyboardButton("🔙 Назад к дням", callback_data="back_to_days"))
    kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return kb

def commander_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📋 Список записей взвода", callback_data="commander_list"),
        InlineKeyboardButton("❌ Удалить запись", callback_data="commander_remove")
    )
    kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return kb

def admin_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📅 Управление днями", callback_data="admin_days"),
        InlineKeyboardButton("📊 Все записи", callback_data="admin_list"),
        InlineKeyboardButton("🗑 Очистить записи", callback_data="admin_clear"),
        InlineKeyboardButton("👥 Управление командирами", callback_data="admin_commanders"),
        InlineKeyboardButton("⭐ Управление старшиной", callback_data="admin_starhina"),
        InlineKeyboardButton("🔔 Закрыть запись на день", callback_data="admin_close_day"),
        InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_broadcast")  # НОВАЯ КНОПКА
    )
    kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return kb

def admin_days_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    sets = load_settings()
    btns = []
    for dk, dn in DAYS_RU.items():
        status = "✅" if sets[dk] else "❌"
        btns.append(InlineKeyboardButton(f"{status} {dn}", callback_data=f"toggle_{dk}"))
    for i in range(0, len(btns), 2):
        if i+1 < len(btns):
            kb.add(btns[i], btns[i+1])
        else:
            kb.add(btns[i])
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    return kb

def admin_close_day_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    for dk, dn in DAYS_RU.items():
        kb.add(InlineKeyboardButton(dn, callback_data=f"close_day_{dk}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    return kb

def admin_commanders_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    for pl, name in PLATOONS.items():
        cnt = len(DATA_STRUCTURE['commanders'].get(pl, []))
        kb.add(InlineKeyboardButton(f"📌 {name} ({cnt} ком.)", callback_data=f"manage_platoon_{pl}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    return kb

def manage_platoon_keyboard(platoon):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ Добавить командира", callback_data=f"add_commander_{platoon}"))
    for cid in DATA_STRUCTURE['commanders'].get(platoon, []):
        try:
            u = bot.get_chat(cid)
            name = u.first_name
        except:
            name = str(cid)
        kb.add(InlineKeyboardButton(f"❌ Удалить {name}", callback_data=f"remove_commander_{platoon}_{cid}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_commanders"))
    return kb

def admin_starhina_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ Добавить старшину", callback_data="add_starhina"))
    for sid in DATA_STRUCTURE.get('starhina', []):
        try:
            u = bot.get_chat(sid)
            name = u.first_name
        except:
            name = str(sid)
        kb.add(InlineKeyboardButton(f"❌ Удалить {name}", callback_data=f"remove_starhina_{sid}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    return kb

def confirm_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ ДА", callback_data="confirm_clear"),
        InlineKeyboardButton("❌ НЕТ", callback_data="admin_back")
    )
    return kb

# ============ ОБРАБОТЧИКИ КОМАНД ============
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        add_user(message.from_user.id, message.from_user)
        role = get_user_role_string(message.from_user.id)
        text = (
            f"🌟 **Добро пожаловать в бот записи!** 🌟\n\n"
            f"⭐ **Ваша роль:** {role}\n\n"
            "📌 **Как записаться:**\n"
            "1️⃣ Выберите день\n"
            "2️⃣ Выберите взвод\n"
            "3️⃣ Введите фамилию\n\n"
            "🎖️ **Командиры:** /commander\n"
            "👑 **Админ:** /admin\n"
            "🆔 **Мой ID:** /myid\n\n"
            "⬇️ Кнопки внизу"
        )
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu_keyboard())
    except Exception as e:
        print(f"Ошибка в start: {e}")
        traceback.print_exc()

@bot.message_handler(commands=['myid'])
def myid_command(message):
    try:
        role = get_user_role_string(message.from_user.id)
        text = (
            f"🆔 **Ваш ID:** `{message.from_user.id}`\n"
            f"👤 **Имя:** {message.from_user.first_name}\n"
            f"📱 **Username:** @{message.from_user.username or 'нет'}\n"
            f"⭐ **Роль:** {role}"
        )
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu_keyboard())
    except Exception as e:
        print(f"Ошибка в myid: {e}")

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ Доступ запрещен!")
        return
    bot.send_message(message.chat.id, "👑 **Панель администратора**", parse_mode='Markdown', reply_markup=admin_keyboard())

@bot.message_handler(commands=['commander'])
def commander_command(message):
    if not has_commander_permissions(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ Вы не командир и не старшина.")
        return
    role = get_user_role_string(message.from_user.id)
    bot.send_message(message.chat.id, f"🎖️ **Панель {role}**", parse_mode='Markdown', reply_markup=commander_keyboard())

@bot.message_handler(commands=['set_commander'])
def set_commander_command(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ Только админ")
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.send_message(message.chat.id, "❌ Формат: `/set_commander 721 123456789`", parse_mode='Markdown')
        return
    try:
        platoon = int(parts[1])
        cid = int(parts[2])
        if platoon not in PLATOONS:
            bot.send_message(message.chat.id, "❌ Неверный взвод (721/722/723)")
            return
        if cid not in DATA_STRUCTURE['commanders'][platoon]:
            DATA_STRUCTURE['commanders'][platoon].append(cid)
            save_commanders_data()
            try:
                bot.send_message(cid, f"🎖️ Вы назначены командиром {PLATOONS[platoon]}!\n/commander")
            except:
                pass
            bot.send_message(message.chat.id, f"✅ Командир добавлен! ID: `{cid}`", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "⚠️ Уже командир")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка ввода")

# ============ ОБРАБОТЧИК ДЛЯ РАССЫЛКИ ============
@bot.message_handler(content_types=['text'])
def broadcast_message_handler(message):
    """Обработчик для получения текста рассылки от администратора"""
    if not is_admin(message.from_user.id):
        return
    
    # Проверяем, находится ли админ в режиме рассылки
    if not hasattr(broadcast_message_handler, 'waiting_for_broadcast'):
        return
    
    if broadcast_message_handler.waiting_for_broadcast.get(message.from_user.id):
        # Получаем текст сообщения
        msg_text = message.text
        broadcast_message_handler.waiting_for_broadcast[message.from_user.id] = False
        
        # Отправляем подтверждение
        confirm_kb = InlineKeyboardMarkup(row_width=2)
        confirm_kb.add(
            InlineKeyboardButton("✅ ДА, ОТПРАВИТЬ", callback_data=f"confirm_broadcast_{message.message_id}"),
            InlineKeyboardButton("❌ ОТМЕНА", callback_data="admin_back")
        )
        
        # Сохраняем текст для отправки
        broadcast_message_handler.pending_broadcast = {
            'user_id': message.from_user.id,
            'text': msg_text,
            'msg_id': message.message_id
        }
        
        bot.send_message(
            message.chat.id,
            f"📢 **Предпросмотр сообщения для рассылки:**\n\n{msg_text}\n\n"
            f"⚠️ **Внимание!** Сообщение получат ВСЕ пользователи бота.\n\n"
            f"Отправить?",
            parse_mode='Markdown',
            reply_markup=confirm_kb
        )

# Инициализация словаря для ожидания рассылки
broadcast_message_handler.waiting_for_broadcast = {}
broadcast_message_handler.pending_broadcast = None

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
def add_commander(msg, platoon, orig_msg):
    try:
        if not is_admin(msg.from_user.id):
            return
        cid = int(msg.text.strip())
        if cid not in DATA_STRUCTURE['commanders'][platoon]:
            DATA_STRUCTURE['commanders'][platoon].append(cid)
            save_commanders_data()
            try:
                bot.send_message(cid, f"🎖️ Вы командир {PLATOONS[platoon]}! /commander")
            except:
                pass
            bot.send_message(msg.chat.id, f"✅ Командир добавлен: `{cid}`", parse_mode='Markdown')
        else:
            bot.send_message(msg.chat.id, "❌ Уже командир")
        bot.send_message(orig_msg.chat.id, f"👥 **Управление {PLATOONS[platoon]}**", parse_mode='Markdown', reply_markup=manage_platoon_keyboard(platoon))
    except:
        bot.send_message(msg.chat.id, "❌ Ошибка: нужно число")

def add_starhina(msg, orig_msg):
    try:
        if not is_admin(msg.from_user.id):
            return
        sid = int(msg.text.strip())
        if sid not in DATA_STRUCTURE['starhina']:
            DATA_STRUCTURE['starhina'].append(sid)
            save_commanders_data()
            try:
                bot.send_message(sid, "⭐ Вы назначены старшиной курса!\n/commander")
            except:
                pass
            bot.send_message(msg.chat.id, f"✅ Старшина добавлен: `{sid}`", parse_mode='Markdown')
        else:
            bot.send_message(msg.chat.id, "❌ Уже старшина")
        bot.send_message(orig_msg.chat.id, "⭐ **Управление старшиной**", parse_mode='Markdown', reply_markup=admin_starhina_keyboard())
    except:
        bot.send_message(msg.chat.id, "❌ Ошибка: нужно число")

def process_surname(message):
    try:
        surname = message.text.strip()
        if not surname:
            bot.send_message(message.chat.id, "❌ Введите фамилию:")
            bot.register_next_step_handler(message, process_surname)
            return
        add_user(message.from_user.id, message.from_user)
        temp_file = f'temp_zapis_{message.from_user.id}.json'
        if not os.path.exists(temp_file):
            bot.send_message(message.chat.id, "❌ Ошибка! Начните заново /start")
            return
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        day_key = data['day_key']
        day_name = data['day_name']
        platoon = data['platoon']
        if not is_day_enabled(day_key):
            bot.send_message(message.chat.id, f"❌ День {day_name} закрыт")
            return
        all_data = load_data()
        record = {
            'surname': surname,
            'user_id': message.from_user.id,
            'username': message.from_user.username or '',
            'first_name': message.from_user.first_name or '',
            'platoon': platoon,
            'day_name': day_name,
            'time': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
        all_data[day_key].append(record)
        save_data(all_data)
        total = len([r for r in all_data[day_key] if isinstance(r, dict) and r.get('platoon') == platoon])
        notify_commander_about_new_record(platoon, {
            'surname': surname, 'day_name': day_name,
            'time': record['time'], 'user_id': message.from_user.id,
            'username': message.from_user.username or '', 'total_in_platoon': total
        })
        os.remove(temp_file)
        if os.path.exists(f'temp_{message.from_user.id}.json'):
            os.remove(f'temp_{message.from_user.id}.json')
        bot.send_message(
            message.chat.id,
            f"✅ **Запись оформлена!**\n📅 {day_name}\n👤 {surname}\n📌 {PLATOONS[platoon]}\n🕐 {record['time']}",
            parse_mode='Markdown', reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        print(f"Ошибка в process_surname: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка, попробуйте /start")

def process_remove_reason(message):
    try:
        reason = message.text.strip()
        if not reason:
            reason = "Не указана"
        with open(f'remove_selected_{message.from_user.id}.json', 'r', encoding='utf-8') as f:
            sel = json.load(f)
        day_key = sel['day_key']
        idx = sel['index']
        record = sel['record']
        data = load_data()
        if day_key in data and idx < len(data[day_key]):
            data[day_key].pop(idx)
            save_data(data)
            try:
                bot.send_message(record['user_id'], f"⚠️ **Ваша запись удалена!**\n📅 {sel['day_name']}\n❌ Причина: {reason}", parse_mode='Markdown')
            except:
                pass
            bot.send_message(message.chat.id, f"✅ Запись удалена!\nПричина: {reason}", reply_markup=commander_keyboard())
        for f in [f'commander_records_{message.from_user.id}.json', f'remove_selected_{message.from_user.id}.json']:
            if os.path.exists(f):
                os.remove(f)
    except Exception as e:
        print(f"Ошибка удаления: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при удалении")

# ============ CALLBACK ============
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        def safe_edit(text, markup=None):
            try:
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                      parse_mode='Markdown', reply_markup=markup)
            except Exception as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise

        # Главное меню
        if call.data == "main_menu":
            role = get_user_role_string(call.from_user.id)
            safe_edit(f"🌟 **Главное меню**\n\n⭐ **Ваша роль:** {role}", main_menu_keyboard())

        elif call.data == "about_bot":
            safe_edit("ℹ️ **О боте**\n\n🤖 Версия 3.0\n📅 Запись по дням и взводам\n👥 Командиры, старшина, админ\n\n📢 Есть функция массовой рассылки", main_menu_keyboard())

        elif call.data == "show_my_id":
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, f"🆔 Ваш ID: `{call.from_user.id}`", parse_mode='Markdown', reply_markup=main_menu_keyboard())

        elif call.data == "new_zapis":
            safe_edit("📅 **Выберите день недели:**", days_keyboard())

        elif call.data == "back_to_days":
            safe_edit("📅 **Выберите день недели:**", days_keyboard())

        elif call.data.startswith('day_') and call.data != "disabled_day":
            day_key = call.data.replace('day_', '')
            if not is_day_enabled(day_key):
                bot.answer_callback_query(call.id, "❌ День закрыт", show_alert=True)
                return
            day_name = DAYS_RU[day_key]
            with open(f'temp_{call.from_user.id}.json', 'w', encoding='utf-8') as f:
                json.dump({'day_key': day_key, 'day_name': day_name}, f)
            safe_edit(f"✅ Вы выбрали: {day_name}\n\n📌 **Выберите взвод:**", platoon_keyboard())

        elif call.data.startswith('platoon_'):
            platoon = int(call.data.replace('platoon_', ''))
            temp_file = f'temp_{call.from_user.id}.json'
            if not os.path.exists(temp_file):
                bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
                return
            with open(temp_file, 'r', encoding='utf-8') as f:
                tmp = json.load(f)
            day_key = tmp['day_key']
            day_name = tmp['day_name']
            with open(f'temp_zapis_{call.from_user.id}.json', 'w', encoding='utf-8') as f:
                json.dump({'day_key': day_key, 'day_name': day_name, 'platoon': platoon}, f)
            safe_edit(f"✅ Вы выбрали: {PLATOONS[platoon]}\n\n✏️ **Введите фамилию:**")
            bot.register_next_step_handler(call.message, process_surname)

        elif call.data == "disabled_day":
            bot.answer_callback_query(call.id, "❌ День закрыт для записи", show_alert=True)

        # ============ РАССЫЛКА ============
        elif call.data == "admin_broadcast":
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "⛔ Доступ запрещен!")
                return
            
            bot.answer_callback_query(call.id)
            broadcast_message_handler.waiting_for_broadcast[call.from_user.id] = True
            bot.send_message(
                call.message.chat.id,
                "📢 **Режим рассылки**\n\n"
                "Отправьте текст сообщения, которое хотите разослать ВСЕМ пользователям бота.\n\n"
                "⚠️ **Внимание!** Сообщение получат все, кто когда-либо писал /start.\n\n"
                "📝 Просто напишите текст сообщения в этот чат.\n\n"
                "❌ Для отмены отправьте /cancel"
            )

        # Подтверждение рассылки
        elif call.data.startswith("confirm_broadcast_"):
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "⛔ Доступ запрещен!")
                return
            
            if broadcast_message_handler.pending_broadcast:
                msg_text = broadcast_message_handler.pending_broadcast['text']
                user_id = broadcast_message_handler.pending_broadcast['user_id']
                
                bot.edit_message_text(
                    "📢 **Начинаю рассылку...**\n\n⏳ Пожалуйста, подождите.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
                
                # Отправляем рассылку
                send_broadcast(msg_text, user_id)
                
                # Очищаем ожидание
                broadcast_message_handler.waiting_for_broadcast[call.from_user.id] = False
                broadcast_message_handler.pending_broadcast = None
                
                # Возвращаемся в админ-панель
                bot.send_message(call.message.chat.id, "👑 **Панель администратора**", parse_mode='Markdown', reply_markup=admin_keyboard())
                bot.answer_callback_query(call.id, "✅ Рассылка завершена!")

        # ---- Командир ----
        elif call.data == "commander_list":
            if not has_commander_permissions(call.from_user.id):
                bot.answer_callback_query(call.id, "⛔ Нет прав")
                return
            plats = get_available_platoons_for_user(call.from_user.id)
            data = load_data()
            text = "📋 **Записи:**\n\n"
            found = False
            for dk, dn in DAYS_RU.items():
                for rec in data[dk]:
                    if isinstance(rec, dict) and rec.get('platoon') in plats:
                        found = True
                        text += f"📌 **{dn}:** {rec['surname']}\n   🕐 {rec['time']}\n   🆔 `{rec['user_id']}`\n\n"
            if not found:
                text += "Нет записей"
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=commander_keyboard())
            bot.answer_callback_query(call.id)

        elif call.data == "commander_remove":
            if not has_commander_permissions(call.from_user.id):
                bot.answer_callback_query(call.id, "⛔ Нет прав")
                return
            plats = get_available_platoons_for_user(call.from_user.id)
            data = load_data()
            records = []
            for dk, dn in DAYS_RU.items():
                for idx, rec in enumerate(data[dk]):
                    if isinstance(rec, dict) and rec.get('platoon') in plats:
                        records.append({'day_key': dk, 'day_name': dn, 'index': idx, 'record': rec})
            if not records:
                bot.answer_callback_query(call.id, "Нет записей для удаления", show_alert=True)
                return
            with open(f'commander_records_{call.from_user.id}.json', 'w', encoding='utf-8') as f:
                json.dump(records, f)
            kb = InlineKeyboardMarkup(row_width=1)
            for i, r in enumerate(records):
                kb.add(InlineKeyboardButton(f"{r['day_name']} - {r['record']['surname']}", callback_data=f"remove_select_{i}"))
            kb.add(InlineKeyboardButton("🔙 Назад", callback_data="commander_back"))
            safe_edit("❌ **Выберите запись для удаления:**", kb)

        elif call.data.startswith('remove_select_'):
            if not has_commander_permissions(call.from_user.id):
                bot.answer_callback_query(call.id, "⛔ Нет прав")
                return
            idx = int(call.data.split('_')[-1])
            with open(f'commander_records_{call.from_user.id}.json', 'r', encoding='utf-8') as f:
                recs = json.load(f)
            sel = recs[idx]
            with open(f'remove_selected_{call.from_user.id}.json', 'w', encoding='utf-8') as f:
                json.dump(sel, f)
            safe_edit(
                f"❌ **Удаление записи**\n\n👤 {sel['record']['surname']}\n📅 {sel['day_name']}\n\n✏️ **Введите причину удаления:**"
            )
            bot.register_next_step_handler(call.message, process_remove_reason)

        elif call.data == "commander_back":
            role = get_user_role_string(call.from_user.id)
            safe_edit(f"🎖️ **Панель {role}**", commander_keyboard())

        # ---- Админ ----
        elif call.data == "admin_days":
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "⛔")
                return
            safe_edit("📅 **Управление днями**\nНажмите на день для переключения:", admin_days_keyboard())

        elif call.data.startswith('toggle_'):
            if not is_admin(call.from_user.id):
                return
            dk = call.data.replace('toggle_', '')
            sets = load_settings()
            sets[dk] = not sets[dk]
            save_settings(sets)
            bot.answer_callback_query(call.id, f"✅ День {DAYS_RU[dk]} {'включен' if sets[dk] else 'отключен'}")
            safe_edit("📅 **Управление днями**", admin_days_keyboard())

        elif call.data == "admin_list":
            if not is_admin(call.from_user.id):
                return
            data = load_data()
            text = "📊 **Все записи:**\n\n"
            total = 0
            for dk, dn in DAYS_RU.items():
                if data[dk]:
                    text += f"📌 **{dn}:**\n"
                    for rec in data[dk]:
                        if isinstance(rec, dict):
                            text += f"   • {rec['surname']} ({PLATOONS.get(rec['platoon'], '?')})\n     🕐 {rec['time']}\n"
                            total += 1
                    text += "\n"
            if total == 0:
                text += "Нет записей"
            else:
                text += f"📊 Итого: {total}"
            bot.send_message(call.message.chat.id, text, parse_mode='Markdown', reply_markup=admin_keyboard())
            bot.answer_callback_query(call.id)

        elif call.data == "admin_clear":
            if not is_admin(call.from_user.id):
                return
            safe_edit("⚠️ **Очистить все записи?**", confirm_keyboard())

        elif call.data == "confirm_clear":
            if not is_admin(call.from_user.id):
                return
            empty = {day: [] for day in DAYS_RU.keys()}
            save_data(empty)
            safe_edit("✅ **Все записи очищены!**", admin_keyboard())
            bot.answer_callback_query(call.id)

        elif call.data == "admin_commanders":
            if not is_admin(call.from_user.id):
                return
            safe_edit("👥 **Управление командирами**\nВыберите взвод:", admin_commanders_keyboard())

        elif call.data.startswith("manage_platoon_"):
            if not is_admin(call.from_user.id):
                return
            pl = int(call.data.split('_')[-1])
            safe_edit(f"👥 **Управление {PLATOONS[pl]}**", manage_platoon_keyboard(pl))

        elif call.data.startswith("add_commander_"):
            if not is_admin(call.from_user.id):
                return
            pl = int(call.data.split('_')[-1])
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id,
                                   f"➕ **Добавить командира для {PLATOONS[pl]}**\nОтправьте ID (только цифры):",
                                   parse_mode='Markdown')
            bot.register_next_step_handler(msg, lambda m: add_commander(m, pl, call.message))

        elif call.data.startswith("remove_commander_"):
            if not is_admin(call.from_user.id):
                return
            parts = call.data.split('_')
            pl = int(parts[2])
            cid = int(parts[3])
            if cid in DATA_STRUCTURE['commanders'][pl]:
                DATA_STRUCTURE['commanders'][pl].remove(cid)
                save_commanders_data()
                bot.answer_callback_query(call.id, "✅ Командир удален")
                safe_edit(f"👥 **Управление {PLATOONS[pl]}**", manage_platoon_keyboard(pl))
            else:
                bot.answer_callback_query(call.id, "❌ Не найден", show_alert=True)

        elif call.data == "admin_starhina":
            if not is_admin(call.from_user.id):
                return
            safe_edit("⭐ **Управление старшиной**\nСтаршина управляет всеми взводами", admin_starhina_keyboard())

        elif call.data == "add_starhina":
            if not is_admin(call.from_user.id):
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id, "⭐ **Добавить старшину**\nОтправьте ID:", parse_mode='Markdown')
            bot.register_next_step_handler(msg, lambda m: add_starhina(m, call.message))

        elif call.data.startswith("remove_starhina_"):
            if not is_admin(call.from_user.id):
                return
            sid = int(call.data.split('_')[-1])
            if sid in DATA_STRUCTURE['starhina']:
                DATA_STRUCTURE['starhina'].remove(sid)
                save_commanders_data()
                bot.answer_callback_query(call.id, "✅ Старшина удален")
                safe_edit("⭐ **Управление старшиной**", admin_starhina_keyboard())
            else:
                bot.answer_callback_query(call.id, "❌ Не найден", show_alert=True)

        elif call.data == "admin_close_day":
            if not is_admin(call.from_user.id):
                return
            safe_edit("🔔 **Закрыть запись на день**\nВыберите день:", admin_close_day_keyboard())

        elif call.data.startswith("close_day_"):
            if not is_admin(call.from_user.id):
                return
            dk = call.data.replace('close_day_', '')
            day_name = DAYS_RU[dk]
            bot.send_message(call.message.chat.id, f"📢 Оповещение о закрытии записи на {day_name}...")
            cnt = notify_all_users_about_close(day_name)
            safe_edit(f"✅ **Оповещение отправлено!**\n📅 {day_name}\n📨 Получили: {cnt} чел.", admin_keyboard())
            bot.answer_callback_query(call.id)

        elif call.data == "admin_back":
            if not is_admin(call.from_user.id):
                return
            safe_edit("👑 **Панель администратора**", admin_keyboard())

        else:
            bot.answer_callback_query(call.id, "Неизвестная команда")
    except Exception as e:
        print(f"Ошибка в callback: {e}")
        traceback.print_exc()
        try:
            bot.answer_callback_query(call.id, "Произошла ошибка", show_alert=True)
        except:
            pass

# ============ ЗАПУСК ============
if __name__ == '__main__':
    try:
        print("🔄 Запуск бота...")
        bot.remove_webhook()
        time.sleep(1)

        if not os.path.exists(SETTINGS_FILE):
            save_settings({day: True for day in DAYS_RU.keys()})
        if not os.path.exists(DATA_FILE):
            save_data({day: [] for day in DAYS_RU.keys()})
        if not os.path.exists(USERS_FILE):
            save_users([])

        load_commanders_data()

        print("=" * 50)
        print("🤖 БОТ ЗАПУЩЕН")
        print(f"👑 Админ ID: {ADMIN_ID}")
        print("=" * 50)
        print("\n📢 Новая функция: массовая рассылка сообщений всем пользователям")
        print("   В админ-панели: кнопка '📢 Сделать рассылку'")
        print("=" * 50)
        
        bot.infinity_polling(timeout=60)
    except KeyboardInterrupt:
        print("\nБот остановлен")
    except Exception as e:
        print(f"Ошибка: {e}")
        traceback.print_exc()