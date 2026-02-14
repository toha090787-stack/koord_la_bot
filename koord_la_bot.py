import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    ConversationHandler, MessageHandler, filters
)

# --- ЛОГИРОВАНИЕ ---
# Оставляем INFO для основного бота, но отключаем шум от сетевых запросов
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# Эта строка убирает спам POST запросов:
logging.getLogger("httpx").setLevel(logging.WARNING)


# --- КОНФИГУРАЦИЯ ---
TOKEN = '8534422390:AAHm6z-poKWBCOED8s3NEmQp4tAqzJ-wxsI'

# --- СПИСКИ РАЙОНОВ ---
SPB_DISTRICTS = [
    "Адмиралтейский", "Василеостровский", "Выборгский", "Калининский", "Кировский",
    "Колпинский", "Красногвардейский", "Красносельский", "Кронштадтский", "Курортный",
    "Московский", "Невский", "Петроградский", "Петродворцовый", "Приморский",
    "Пушкинский", "Фрунзенский", "Центральный"
]

LO_DISTRICTS = [
    "Бокситогорский", "Волосовский", "Волховский", "Всеволожский", "Выборгский",
    "Гатчинский", "Кингисеппский", "Киришский", "Кировский", "Лодейнопольский",
    "Ломоносовский", "Лужский", "Подпорожский", "Приозерский", "Сланцевский",
    "Сосновоборский ГО", "Тихвинский", "Тосненский"
]

# Категории ГКП, где список районов НЕ нужен
GKP_NO_DISTRICTS = [
    "Псих. больницы взр. СПб", "Псих. больницы взр. ЛО",
    "Псих. больницы дети СПб", "Псих. больницы дети ЛО",
    "Морги СПб", "Морги ЛО",
    "Паллиативы СПб", "Паллиативы ЛО"
]

# Настройки кнопок количества для оборудования
EQUIP_QTY_BUTTONS = {
    "Фонари": ["15", "30", "45", "60"],
    "Аккумуляторы": ["30", "45", "60", "90", "120"],
    "Рации": ["10", "15", "20", "25", "30", "40"],
    "Навигаторы": ["10", "15", "20", "25", "30", "40"],
    "Компасы": ["15", "30", "45", "60"]
}

# --- СОСТОЯНИЯ (STATES) ---
(
    MAIN_MENU,
    # Инфорги
    INFORG_MENU, INFORG_DOPROZVON, INFORG_USER_REQ,
    # ГКП
    GKP_MENU, GKP_DISTRICT_SELECT,
    # ГОО
    GOO_MENU, GOO_DISTRICT_SELECT, GOO_CUSTOM,
    # Выезд
    DEP_ADDRESS, DEP_COORDS, DEP_TIME, DEP_CLOTHES, DEP_BRING,
    DEP_EQUIP_MENU, DEP_EQUIP_QTY, DEP_STAFF,
    # Ресурсы
    RES_MENU, RES_MAPS_CENTER, RES_MAPS_LIMITS, RES_MAPS_GRID, RES_MAPS_PHONE,
    RES_FLYERS, RES_TECHNIQUE
) = range(24)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def clean_text(text):
    """Убирает галочку и доп. информацию из текста кнопки"""
    text = text.replace("✅ ", "")
    if "(" in text and ")" in text and not text.startswith("Связь"): 
        parts = text.split(" (")
        if parts[0] in EQUIP_QTY_BUTTONS or parts[0] in ["Инвертор", "Скотч", "Power bank"]:
             return parts[0]
    return text

def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return ReplyKeyboardMarkup(menu, resize_keyboard=True)

def get_checkbox_keyboard(options, selected_list, done_text="💾 Готово / Назад"):
    """Генерирует клавиатуру с галочками"""
    buttons = []
    for opt in options:
        if opt in selected_list:
            buttons.append(f"✅ {opt}")
        else:
            buttons.append(opt)
    return build_menu(buttons, 2, footer_buttons=[done_text])

# --- ГЛАВНОЕ МЕНЮ И СТАРТ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['tasks'] = {
        'inforg': [], 'gkp': {}, 'goo': {}, 'departure': {}, 'resources': []
    }
    await update.message.reply_text(
        "Бот планирования задач.\nНажмите «Заполнить» для начала.",
        reply_markup=ReplyKeyboardMarkup([["Заполнить"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if 'tasks' not in context.user_data:
        context.user_data['tasks'] = {'inforg': [], 'gkp': {}, 'goo': {}, 'departure': {}, 'resources': []}

    keyboard = [
        ["Задачи для инфоргов"],
        ["Выезд", "Запрос на ресурсы"],
        ["🏁 Сформировать список"]
    ]

    if text == "Заполнить" or text == "Назад":
        await update.message.reply_text("Выберите раздел:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return MAIN_MENU

    if text == "Задачи для инфоргов":
        return await inforg_menu_show(update, context)
    elif text == "Выезд":
        await update.message.reply_text("Введите **Адрес штаба**:", reply_markup=ReplyKeyboardRemove())
        return DEP_ADDRESS
    elif text == "Запрос на ресурсы":
        return await res_menu_show(update, context)
    elif text == "🏁 Сформировать список":
        return await finish_list(update, context)
    
    # Если пришел неизвестный текст, просто показываем меню
    await update.message.reply_text("Главное меню:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return MAIN_MENU

# ================= ГЛАВА 1: ИНФОРГИ =================

async def inforg_menu_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        "Допрозвон", "Запрос на ГОО",
        "Запрос на ГКП", "Запрос Пеленг",
        "Запрос камеры БГ", "Оповещение Мегафон",
        "Пользовательский запрос", "Назад"
    ]
    await update.message.reply_text("Меню инфоргов:", reply_markup=build_menu(buttons, 2))
    return INFORG_MENU

async def inforg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Назад":
        return await main_menu(update, context)
    
    if text == "Допрозвон":
        await update.message.reply_text("Кого нужно прозвонить?", reply_markup=ReplyKeyboardRemove())
        return INFORG_DOPROZVON
    
    if text == "Пользовательский запрос":
        await update.message.reply_text("Введите текст задачи:", reply_markup=ReplyKeyboardRemove())
        return INFORG_USER_REQ
    
    if text == "Запрос на ГКП":
        return await gkp_menu_show(update, context)
    
    if text == "Запрос на ГОО":
        return await goo_menu_show(update, context)

    if text in ["Запрос Пеленг", "Запрос камеры БГ", "Оповещение Мегафон"]:
        context.user_data['tasks']['inforg'].append(text)
        await update.message.reply_text(f"✅ Добавлено: {text}")
        return INFORG_MENU
    
    return INFORG_MENU

async def save_doproznvon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tasks']['inforg'].append(f"Допрозвон: {update.message.text}")
    return await inforg_menu_show(update, context)

async def save_user_req(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tasks']['inforg'].append(f"Польз. запрос: {update.message.text}")
    return await inforg_menu_show(update, context)

# --- ГКП ---
async def gkp_menu_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options = [
        "Больницы взрослые СПб", "Больницы взрослые ЛО",
        "СМП взрослые СПб", "СМП взрослые ЛО",
        "Псих. больницы взр. СПб", "Псих. больницы взр. ЛО",
        "Псих. больницы дети СПб", "Псих. больницы дети ЛО",
        "Больницы детские СПб", "Больницы детские ЛО",
        "СМП детские СПб", "СМП детские ЛО",
        "Морги СПб", "Морги ЛО",
        "Паллиативы СПб", "Паллиативы ЛО",
        "Назад"
    ]
    await update.message.reply_text("Запрос на ГКП:", reply_markup=build_menu(options, 2))
    return GKP_MENU

async def gkp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Назад":
        return await inforg_menu_show(update, context)

    if text in GKP_NO_DISTRICTS:
        if text not in context.user_data['tasks']['gkp']:
            context.user_data['tasks']['gkp'][text] = ["(список не нужен)"]
            await update.message.reply_text(f"✅ Добавлено: {text}")
        else:
            await update.message.reply_text(f"ℹ️ Уже есть: {text}")
        return GKP_MENU

    context.user_data['current_gkp_cat'] = text
    districts = SPB_DISTRICTS if "СПб" in text else LO_DISTRICTS
    
    if text not in context.user_data['tasks']['gkp']:
        context.user_data['tasks']['gkp'][text] = []
    
    selected = context.user_data['tasks']['gkp'][text]
    await update.message.reply_text(
        f"Выберите районы для: {text}",
        reply_markup=get_checkbox_keyboard(districts, selected)
    )
    return GKP_DISTRICT_SELECT

async def gkp_district_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💾 Готово / Назад":
        return await gkp_menu_show(update, context)
    
    cat = context.user_data.get('current_gkp_cat')
    clean_name = clean_text(text)
    selected = context.user_data['tasks']['gkp'][cat]
    
    if clean_name in selected:
        selected.remove(clean_name)
    else:
        selected.append(clean_name)
    
    districts = SPB_DISTRICTS if "СПб" in cat else LO_DISTRICTS
    await update.message.reply_text(f"Выбрано: {clean_name}", reply_markup=get_checkbox_keyboard(districts, selected))
    return GKP_DISTRICT_SELECT

# --- ГОО ---
async def goo_menu_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options = [
        "Размещение по крупным в СПб", "Размещение по крупным в ЛО",
        "Размещение плотно в СПб", "Размещение плотно в ЛО",
        "Произвольная информация", "Назад"
    ]
    await update.message.reply_text("Запрос на ГОО:", reply_markup=build_menu(options, 1))
    return GOO_MENU

async def goo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Назад":
        return await inforg_menu_show(update, context)
    
    if text == "Произвольная информация":
        await update.message.reply_text("Введите текст для ГОО:", reply_markup=ReplyKeyboardRemove())
        return GOO_CUSTOM

    context.user_data['current_goo_cat'] = text
    districts = (["Весь город"] + SPB_DISTRICTS) if "СПб" in text else (["Вся область"] + LO_DISTRICTS)
    
    if text not in context.user_data['tasks']['goo']:
        context.user_data['tasks']['goo'][text] = []
        
    selected = context.user_data['tasks']['goo'][text]
    await update.message.reply_text(
        f"Выберите зоны для: {text}",
        reply_markup=get_checkbox_keyboard(districts, selected)
    )
    return GOO_DISTRICT_SELECT

async def goo_district_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💾 Готово / Назад":
        return await goo_menu_show(update, context)
    
    cat = context.user_data.get('current_goo_cat')
    clean_name = clean_text(text)
    selected = context.user_data['tasks']['goo'][cat]
    
    if clean_name in selected:
        selected.remove(clean_name)
    else:
        selected.append(clean_name)
    
    districts = (["Весь город"] + SPB_DISTRICTS) if "СПб" in cat else (["Вся область"] + LO_DISTRICTS)
    await update.message.reply_text(f"Выбрано: {clean_name}", reply_markup=get_checkbox_keyboard(districts, selected))
    return GOO_DISTRICT_SELECT

async def goo_custom_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "Произвольная" not in context.user_data['tasks']['goo']:
        context.user_data['tasks']['goo']["Произвольная"] = []
    context.user_data['tasks']['goo']["Произвольная"].append(update.message.text)
    return await goo_menu_show(update, context)

# ================= ГЛАВА 2: ВЫЕЗД =================

async def dep_address_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tasks']['departure']['address'] = update.message.text
    await update.message.reply_text("Введите **Координаты штаба**:")
    return DEP_COORDS

async def dep_coords_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tasks']['departure']['coords'] = update.message.text
    await update.message.reply_text("Введите **Время сбора** (формат 24ч):")
    return DEP_TIME

async def dep_time_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tasks']['departure']['time'] = update.message.text
    await update.message.reply_text("Форма одежды:", reply_markup=build_menu(["Город", "Лес", "Город/Лес"], 2))
    return DEP_CLOTHES

async def dep_clothes_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tasks']['departure']['clothes'] = update.message.text
    if 'bring' not in context.user_data['tasks']['departure']:
        context.user_data['tasks']['departure']['bring'] = []
    await show_dep_bring_menu(update, context)
    return DEP_BRING

async def show_dep_bring_menu(update, context):
    options = ["Сменная одежда", "Питание", "Скотч", "Ориентировки"]
    selected = context.user_data['tasks']['departure']['bring']
    await update.message.reply_text(
        "Что взять с собой?",
        reply_markup=get_checkbox_keyboard(options, selected, "Далее: Оборудование")
    )

async def dep_bring_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Далее: Оборудование":
        if 'equipment' not in context.user_data['tasks']['departure']:
            context.user_data['tasks']['departure']['equipment'] = {}
        return await show_dep_equip_menu(update, context)
    
    clean_name = clean_text(text)
    selected = context.user_data['tasks']['departure']['bring']
    if clean_name in selected:
        selected.remove(clean_name)
    else:
        selected.append(clean_name)
    await show_dep_bring_menu(update, context)
    return DEP_BRING

# --- Оборудование ---
async def show_dep_equip_menu(update, context):
    items_with_qty = ["Фонари", "Аккумуляторы", "Рации", "Навигаторы", "Компасы"]
    items_toggle = ["Инвертор", "Скотч", "Power bank"]
    
    equip_data = context.user_data['tasks']['departure']['equipment']
    
    buttons = []
    for item in items_with_qty:
        qty = equip_data.get(item)
        if qty:
            buttons.append(f"{item} ({qty})")
        else:
            buttons.append(item)
    
    for item in items_toggle:
        if item in equip_data:
            buttons.append(f"✅ {item}")
        else:
            buttons.append(item)
            
    await update.message.reply_text(
        "Запрос оборудования (Нажмите для выбора):",
        reply_markup=build_menu(buttons, 2, footer_buttons=["Далее: Штаб"])
    )
    return DEP_EQUIP_MENU

async def dep_equip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Далее: Штаб":
        if 'staff' not in context.user_data['tasks']['departure']:
            context.user_data['tasks']['departure']['staff'] = []
        return await show_dep_staff_menu(update, context)
    
    clean_name = clean_text(text)
    equip_data = context.user_data['tasks']['departure']['equipment']
    
    if clean_name in EQUIP_QTY_BUTTONS:
        context.user_data['current_equip_item'] = clean_name
        qty_options = EQUIP_QTY_BUTTONS[clean_name]
        await update.message.reply_text(
            f"Выберите или введите количество для: {clean_name}",
            reply_markup=build_menu(qty_options, 3)
        )
        return DEP_EQUIP_QTY
    
    if clean_name in ["Инвертор", "Скотч", "Power bank"]:
        if clean_name in equip_data:
            del equip_data[clean_name]
        else:
            equip_data[clean_name] = "Да"
        return await show_dep_equip_menu(update, context)
        
    return DEP_EQUIP_MENU

async def dep_equip_qty_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = context.user_data['current_equip_item']
    qty = update.message.text
    context.user_data['tasks']['departure']['equipment'][item] = qty
    return await show_dep_equip_menu(update, context)

# --- Штабная команда ---
async def show_dep_staff_menu(update, context):
    options = ["Регистратор", "Оперативный картограф", "Связь на ПСР", "Табор"]
    selected = context.user_data['tasks']['departure']['staff']
    await update.message.reply_text(
        "Запрос штабной команды:",
        reply_markup=get_checkbox_keyboard(options, selected, "💾 Завершить выезд")
    )
    return DEP_STAFF

async def dep_staff_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
    if text == "💾 Завершить выезд":
        keyboard = [
            ["Задачи для инфоргов"],
            ["Выезд", "Запрос на ресурсы"],
            ["🏁 Сформировать список"]
        ]
        await update.message.reply_text("Выезд сохранен. Главное меню:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return MAIN_MENU
    # --------------------------
    
    clean_name = clean_text(text)
    selected = context.user_data['tasks']['departure']['staff']
    if clean_name in selected:
        selected.remove(clean_name)
    else:
        selected.append(clean_name)
    await show_dep_staff_menu(update, context)
    return DEP_STAFF

# ================= ГЛАВА 3: РЕСУРСЫ =================

async def res_menu_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        "Запрос на Карты", "Запрос на Ориентировки",
        "Запрос на БПЛА", "Запрос на Ангелов",
        "Запрос на технику", "Назад"
    ]
    await update.message.reply_text("Меню ресурсов:", reply_markup=build_menu(buttons, 2))
    return RES_MENU

async def res_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Назад":
        return await main_menu(update, context)
    
    if text == "Запрос на Карты":
        await update.message.reply_text("Введите **Центр зоны**:", reply_markup=ReplyKeyboardRemove())
        return RES_MAPS_CENTER
    
    if text == "Запрос на Ориентировки":
        await update.message.reply_text("Укажите количество:", reply_markup=ReplyKeyboardRemove())
        return RES_FLYERS
    
    if text == "Запрос на технику":
        if 'technique' not in context.user_data['tasks']['resources']:
             context.user_data['temp_tech_list'] = []
        return await show_tech_menu(update, context)
        
    if text in ["Запрос на БПЛА", "Запрос на Ангелов"]:
        context.user_data['tasks']['resources'].append(text)
        await update.message.reply_text(f"✅ Добавлено: {text}")
        return RES_MENU
        
    return RES_MENU

async def maps_center_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_map'] = {'center': update.message.text}
    await update.message.reply_text("Введите **Ограничители зоны**:")
    return RES_MAPS_LIMITS

async def maps_limits_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_map']['limits'] = update.message.text
    await update.message.reply_text("Введите **Шаг сетки**:")
    return RES_MAPS_GRID

async def maps_grid_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_map']['grid'] = update.message.text
    await update.message.reply_text("Комплект для телефонов? (Да/Нет)", reply_markup=build_menu(["Да", "Нет"], 2))
    return RES_MAPS_PHONE

async def maps_phone_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = context.user_data['temp_map']
    kit = update.message.text
    result = f"Карты: Центр {m['center']}, Границы {m['limits']}, Шаг {m['grid']}, Телефон: {kit}"
    context.user_data['tasks']['resources'].append(result)
    return await res_menu_show(update, context)

async def flyers_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tasks']['resources'].append(f"Ориентировки: {update.message.text}")
    return await res_menu_show(update, context)

async def show_tech_menu(update, context):
    options = [
        "Штабной автомобиль", "Проходимая техника", "Квадроциклы", 
        "Снегоступы", "Болотоходы", "Штабной прицеп", 
        "Комплект Шатер большой", "Комплект Шатер малый"
    ]
    selected = context.user_data.get('temp_tech_list', [])
    await update.message.reply_text(
        "Выберите технику:",
        reply_markup=get_checkbox_keyboard(options, selected, "💾 Готово")
    )
    return RES_TECHNIQUE

async def tech_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💾 Готово":
        selected = context.user_data.get('temp_tech_list', [])
        if selected:
            context.user_data['tasks']['resources'].append(f"Техника: {', '.join(selected)}")
        return await res_menu_show(update, context)
    
    clean_name = clean_text(text)
    selected = context.user_data.get('temp_tech_list', [])
    if clean_name in selected:
        selected.remove(clean_name)
    else:
        selected.append(clean_name)
    context.user_data['temp_tech_list'] = selected
    await show_tech_menu(update, context)
    return RES_TECHNIQUE

# ================= ФИНАЛ =================

async def finish_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data.get('tasks', {})
    report = ["📋 СПИСОК ЗАДАЧ\n"]
    
    if data.get('inforg') or data.get('gkp') or data.get('goo'):
        report.append("📢 ЗАДАЧИ")
        for item in data['inforg']:
            report.append(f"- {item}")
        
        if data.get('gkp'):
            report.append("\n*Запрос на ГКП:*")
            for cat, details in data['gkp'].items():
                if len(details) == 1 and details[0] == "(список не нужен)":
                     report.append(f"- {cat}")
                elif details:
                     report.append(f"- {cat}: {', '.join(details)}")
        
        if data.get('goo'):
            report.append("\n*Запрос на ГОО:*")
            for cat, details in data['goo'].items():
                if details:
                    report.append(f"- {cat}: {', '.join(details)}")
        report.append("")
    
    dep = data.get('departure', {})
    if dep:
        report.append("🚗 ГОТОВИМ ВЫЕЗД")
        if 'address' in dep: report.append(f"📍 Адрес: {dep['address']}")
        if 'coords' in dep: report.append(f"🌐 Координаты: {dep['coords']}")
        if 'time' in dep: report.append(f"⏰ Время: {dep['time']}")
        if 'clothes' in dep: report.append(f"👕 Одежда: {dep['clothes']}")
        if 'bring' in dep and dep['bring']: report.append(f"🎒 С собой: {', '.join(dep['bring'])}")
        
        if 'equipment' in dep and dep['equipment']:
            eq_list = []
            for k, v in dep['equipment'].items():
                if v == "Да":
                    eq_list.append(k)
                else:
                    eq_list.append(f"{k} ({v})")
            report.append(f"🧰 Оборудование: {', '.join(eq_list)}")
            
        if 'staff' in dep and dep['staff']:
            report.append(f"👥 Штабная команда: {', '.join(dep['staff'])}")
        report.append("")

    if data.get('resources'):
        report.append("⛺ ЗАПРОС НА РЕСУРСЫ")
        for item in data['resources']:
            report.append(f"- {item}")
            
    final_text = "\n".join(report)
    await update.message.reply_text(final_text, parse_mode='Markdown')
    
    context.user_data.clear()
    await update.message.reply_text("Сформировано. Нажмите «Заполнить» для нового списка.", reply_markup=ReplyKeyboardMarkup([["Заполнить"]], resize_keyboard=True))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardMarkup([["Заполнить"]], resize_keyboard=True))
    return ConversationHandler.END

# --- ЗАПУСК ---
if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex('^Заполнить$'), start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT, main_menu)],
            
            INFORG_MENU: [MessageHandler(filters.TEXT, inforg_handler)],
            INFORG_DOPROZVON: [MessageHandler(filters.TEXT, save_doproznvon)],
            INFORG_USER_REQ: [MessageHandler(filters.TEXT, save_user_req)],
            
            GKP_MENU: [MessageHandler(filters.TEXT, gkp_handler)],
            GKP_DISTRICT_SELECT: [MessageHandler(filters.TEXT, gkp_district_select)],
            
            GOO_MENU: [MessageHandler(filters.TEXT, goo_handler)],
            GOO_DISTRICT_SELECT: [MessageHandler(filters.TEXT, goo_district_select)],
            GOO_CUSTOM: [MessageHandler(filters.TEXT, goo_custom_save)],
            
            DEP_ADDRESS: [MessageHandler(filters.TEXT, dep_address_save)],
            DEP_COORDS: [MessageHandler(filters.TEXT, dep_coords_save)],
            DEP_TIME: [MessageHandler(filters.TEXT, dep_time_save)],
            DEP_CLOTHES: [MessageHandler(filters.TEXT, dep_clothes_save)],
            DEP_BRING: [MessageHandler(filters.TEXT, dep_bring_handler)],
            DEP_EQUIP_MENU: [MessageHandler(filters.TEXT, dep_equip_handler)],
            DEP_EQUIP_QTY: [MessageHandler(filters.TEXT, dep_equip_qty_save)],
            DEP_STAFF: [MessageHandler(filters.TEXT, dep_staff_handler)],
            
            RES_MENU: [MessageHandler(filters.TEXT, res_handler)],
            RES_MAPS_CENTER: [MessageHandler(filters.TEXT, maps_center_save)],
            RES_MAPS_LIMITS: [MessageHandler(filters.TEXT, maps_limits_save)],
            RES_MAPS_GRID: [MessageHandler(filters.TEXT, maps_grid_save)],
            RES_MAPS_PHONE: [MessageHandler(filters.TEXT, maps_phone_save)],
            RES_FLYERS: [MessageHandler(filters.TEXT, flyers_save)],
            RES_TECHNIQUE: [MessageHandler(filters.TEXT, tech_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    print("Бот запущен...")
    application.run_polling()
