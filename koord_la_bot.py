# koord_la_bot3.py
# Python 3.10+
# pip install -U aiogram
# python3 koord_la_bot3.py

import asyncio
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BOT_TOKEN = "7867591820:AAGq7yL20aah-Diq4PwhtZMSuQkHr7i-zKU"

# -------------------- Справочники районов --------------------

SPB_DISTRICTS = [
    "Адмиралтейский", "Василеостровский", "Выборгский", "Калининский", "Кировский",
    "Колпинский", "Красногвардейский", "Красносельский", "Кронштадтский", "Курортный",
    "Московский", "Невский", "Петроградский", "Петродворцовый", "Приморский",
    "Пушкинский", "Фрунзенский", "Центральный",
]

LO_DISTRICTS = [
    "Бокситогорский район", "Волосовский район", "Волховский район", "Всеволожский район",
    "Выборгский район", "Гатчинский район", "Кингисеппский район", "Киришский район",
    "Кировский район", "Лодейнопольский район", "Ломоносовский район", "Лужский район",
    "Подпорожский район", "Приозерский район", "Сланцевский район", "Тихвинский район",
    "Тосненский район", "Сосновоборский городской округ",
]

# -------------------- MarkdownV2 --------------------

def md2_escape(s: str) -> str:
    for ch in r"_*[]()~`>#+-=|{}.!":
        s = s.replace(ch, "\\" + ch)
    return s

# -------------------- Area codes --------------------

def spb_code(i: int) -> str:
    return f"spb{i}"

def lo_code(i: int) -> str:
    return f"lo{i}"

def decode_area(code: str) -> str:
    if code == "SPB_ALL":
        return "Весь город"
    if code == "LO_ALL":
        return "Вся область"
    if code.startswith("spb"):
        return SPB_DISTRICTS[int(code[3:])]
    if code.startswith("lo"):
        return LO_DISTRICTS[int(code[2:])]
    return code

def list_area_codes(kind: str) -> List[str]:
    if kind == "spb":
        return [spb_code(i) for i in range(len(SPB_DISTRICTS))]
    if kind == "lo":
        return [lo_code(i) for i in range(len(LO_DISTRICTS))]
    return []

# -------------------- Допрозвон --------------------

CALL_CATEGORIES = [
    ("call_elderly_memory", "Пожилые, инвалиды, потеря памяти"),
    ("call_forest", "Лес"),
    ("call_adults", "Взрослые"),
    ("call_kids_0_10", "Дети (0-10 лет)"),
    ("call_teens_11_17", "Подростки (11-17 лет)"),
    ("call_ras", "Аутизм (РАС)"),
    ("call_police", "Опрос полиции"),
]

CALL_QUESTIONS: Dict[str, List[str]] = {
    "call_ras": [
        "Ребёнок говорит или не говорит",
        "Реагирует на своё имя/слово",
        "Если невербален: использует систему PECS? ABA?",
        "Есть ли протокол или карточка на случай, если ребенок потерялся",
        "Если вербален: в какой форме задать вопрос",
        "Что можно использовать, как значимый стимул",
        "Отношение к зрительному контакту",
        "Отношение к телесному контакту",
        "Доверенное лицо",
        "Есть ли постоянный наблюдающий специалист",
        "Есть ли серьезные хронические заболевания",
        "Принимает ли лекарства на регулярной основе",
        "Склонен к самоагрессии? В какой форме",
        "Аутостимуляции",
        "Гиперакузия",
        "Болезненная реакция на свет",
        "Есть ли особенности пищевого поведения",
        "Когда последний раз ел и пил",
        "Может ли сам купить еду в магазине",
        "Сенсорные проблемы",
        "Ушёл в своей привычной одежде",
        "Снижен ли болевой порог",
        "Снижена ли чувствительность к холоду",
        "Чего боится",
        "Предмет повышенного интереса, увлечения",
        "Зона повышенного интереса",
        "Посещает ли школу",
        "Кружки, секции, прочие внешкольные занятия",
        "Есть ли друзья",
        "Пользуется ли социальными сетями",
        "С кем общался последний раз, о чём конкретно говорили",
        "Что волновало в последнее время",
        "Был ли чем-то сильно огорчен в последние дни",
        "Существенные изменения в семье",
        "Резкая смена планов",
        "Способен ли самостоятельно пользоваться ОТ",
    ],
    "call_adults": [
        "ФИО БВП (любая смена ФИО)",
        "Дата рождения и возраст БВП",
        "Здоровье. Диагнозы/принимает ли какие-либо медикаменты",
        "Приметы",
        "Особые приметы",
        "Одежда/обувь/головной убор",
        "Что с собой",
        "Телефон БВП, на кого зарегистрирована симка, марка, модель и оператор связи",
        "Где и с кем проживает, и где зарегистрирован",
        "Пропадал ли ранее, когда/как и где находили",
        "Заявление в полицию",
        "Семейное положение",
        "Ситуация в семье",
        "Предыдущие браки",
        "Дети от прошлых браков",
        "Близкие родственники",
        "К кому мог поехать",
        "Места жительства текущие и прежние, куда мог поехать",
        "Дача/другая недвижимость",
        "Маршруты обычные/виды транспорта",
        "Есть ли автомобиль/где он/где ключи/документы",
        "Работа: где/кем/график работы",
        "Предыдущие места работы",
        "Отдых/что делает в свободное время/интересы/увлечения",
        "Коллеги/друзья/круг общения",
        "Особенности характера/поведения",
        "Реакция на незнакомых людей/на предложение помощи",
        "Что изменилось накануне пропажи/ссоры/конфликты",
        "Отношение к религии",
        "Вредные привычки",
        "Проблемы с законом",
        "Долги/кредиты",
        "Мысли о суициде",
        "Соцсети",
        "Контакты друзей/знакомых",
        "Согласие на ориентировку",
    ],
    "call_kids_0_10": [
        "ФИО БВП (любая смена ФИО)",
        "Дата рождения и возраст БВП",
        "Дата и точное время пропажи",
        "Приметы",
        "Особые приметы",
        "Одежда (максимально подробно)",
        "Что было с собой (максимально подробно)",
        "Где и с кем проживает",
        "Знает ли ребенок его наизусть адрес",
        "Знает ли ребенок его наизусть телефоны",
        "Заявление в полицию",
        "Здоровье",
        "Семья полная/не полная",
        "Сколько детей в семье",
        "Все ли дети родные",
        "Отношения между членами семьи",
        "С кем из родных наиболее доверительные отношения",
        "Адреса всех родственников",
        "Адреса всех мест, известных ребенку",
        "Какие данные известны ребенку наизусть",
        "Контакты (учителя, воспитатели, классные руководители и т.д.)",
        "Пропадал ли ранее (подробно описать все случаи)",
        "Как реагирует на незнакомых людей",
        "Берет ли предложенные ему вещи от незнакомцев",
        "Может ли сам подойти к незнакомому взрослому",
        "К кому скорее всего подойдет",
        "На что обижается и как часто",
        "Долго ли длятся его обиды",
        "Были ли ссоры перед пропажей",
        "Обстоятельства пропажи",
        "Как вел себя последние дни перед пропажей",
        "Говорил ли о каких-то мечтах или планах",
        "Кто был с ним в момент пропажи",
        "Какие действия были сразу предприняты",
        "Если потерялся на улице, то куда планировали ехать",
        "Распорядок дня",
        "Психологический портрет",
        "Что разрешено ребенку",
        "Что ему было позволено",
        "Как он относился к запретам",
        "Боится ли наказания или своевольный",
        "Интересы",
        "Социальные сети",
        "Если похищение (увели, посадили в машину, свидетели, контакты, цвет и марка авто, время, место, камеры наружного наблюдения)",
        "Что пропало из дома",
    ],
    "call_forest": [
        "ФИО БВП (любая смена ФИО)",
        "Дата рождения и возраст БВП",
        "Дата и точное время пропажи",
        "Как зовут дома (работа на отклик)",
        "Здоровье/медикаменты/что будет, если не принять",
        "Есть ли диагноз/какой/инвалидность",
        "Как проявляется заболевание",
        "Как ориентируется в пространстве",
        "Как слышит/видит/ходит",
        "Использует ли для ходьбы трость",
        "Скорость ходьбы",
        "Сколько может пройти по времени, по расстоянию",
        "Приметы",
        "Особые приметы",
        "Одежда/обувь/головной убор",
        "Размер обуви",
        "Что с собой",
        "Телефон потеряшки марка и модель",
        "На кого зарегистрирована симка",
        "Заряд телефона",
        "Как долго держит зарядку",
        "Как давно не отвечает на звонки или недоступен",
        "Во сколько созванивались в прошлый раз",
        "Что дословно говорил при последнем общении по телефону",
        "Какими мессенджерами пользуется",
        "Точка входа, координаты",
        "Где и с кем проживает",
        "Где зарегистрирован",
        "Пропадал ли ранее, когда/как и где находили",
        "Обстоятельства пропажи",
        "Заявление в полицию",
        "Как добирается до дачи (места входа в лес)",
        "Подробный маршрут/каким транспортом",
        "Марка, номер и цвет автомобиля",
        "Где нашли автомобиль",
        "Навыки выживания",
        "Сможет развести костер, построить шалаш или лежанку",
        "Потеряшке знаком лес",
        "За чем пошел в лес",
        "Известно ли, куда он обычно ходит",
        "Кто есть на месте пропажи и их контакты",
        "Есть ли на въезде в СНТ шлагбаум/свободный ли проезд",
        "Согласие на ориентировку",
    ],
    "call_police": [
        "Заведено ли уже дело",
        "Если да, то какое",
        "Уточнить у кого и до какого числа оно будет находиться на рассмотрении, постараться взять контакты",
        "Как проходит материал? УРС или БВП",
        "Если это УРС, какие есть основания так думать",
        "Что уже предприняли для поиска",
        "Есть ли какие-то свидетельства",
        "Не проходит ли наш пропавший по какой-то статье",
        "Не скрывается ли от правосудия по какой-то своей причине",
        "Как у полиции есть версии пропажи",
        "Выезжала ли полиция на место",
        "Проводился ли опрос граждан на месте",
        "Не помешает ли размещение нашей ориентировки в соц сетях",
        "Не пропадал ли раньше? Где находили",
        "Не отбывал ли ранее наказание за преступление",
    ],
    "call_teens_11_17": [
        "ФИО БВП (любая смена ФИО)",
        "Дата рождения и возраст БВП",
        "Дата и точное время пропажи",
        "Здоровье. Диагнозы/принимает ли какие-либо медикаменты",
        "Приметы",
        "Особые приметы",
        "Одежда/обувь/головной убор",
        "Что с собой",
        "Как часто и сколько дают карманных денег",
        "Пропадало ли что-либо из дома",
        "Телефон БВП, на кого зарегистрирована симка, марка, модель и оператор связи",
        "Где и с кем проживает",
        "Где зарегистрирован",
        "Пропадал ли ранее",
        "Когда/как и где находили",
        "Обстоятельства пропажи",
        "Что предпринимали для поиска",
        "Полиция",
        "Соцсети",
        "Какие отношения с братьями/сестрами/родителями",
        "Что разрешено ребенку",
        "Какие существуют запреты",
        "Родные ли родители",
        "Кому больше всего доверяет",
        "Какой техникой пользуется",
        "Какая осталась дома",
        "Есть ли к ней доступ",
        "Где учится/прошлые места учебы",
        "Как учится",
        "Одноклассники/преподаватели/взаимоотношения",
        "Есть ли парень/девушка",
        "Друзья/подруги/контакты",
        "Маршруты обычные/виды транспорта",
        "Как оплачивает проезд",
        "Как проводит свободное время",
        "Увлечения/интересы/секции/кружки",
        "Обычный распорядок дня",
        "Особенности характера/поведения",
        "Реакция на незнакомых людей",
        "Может ли уйти с незнакомым взрослым человеком",
        "Что изменилось накануне",
        "Вредные привычки",
        "Состоит ли на учете в ОДН",
        "Мысли о суициде",
        "Согласие на ориентировку",
    ],
    "call_elderly_memory": [
        "ФИО БВП (любая смена ФИО)",
        "Дата рождения и возраст БВП",
        "Дата и точное время пропажи",
        "Здоровье. Диагнозы/принимает ли какие-либо медикаменты",
        "Что будет, если не принять",
        "Как проявляется заболевание",
        "Есть ли внешние проявления заболевания",
        "Странности поведения",
        "Есть ли проблемы с памятью",
        "Что помнит, что не помнит",
        "Как ориентируется в пространстве",
        "Как слышит/видит/ходит",
        "Назовет ли себя, фио, адрес, телефон",
        "Приметы",
        "Особые приметы",
        "Одежда/обувь/головной убор",
        "Что с собой",
        "Телефон БВП, на кого зарегистрирована симка, марка, модель и оператор связи",
        "Где и с кем проживает",
        "Где зарегистрирован",
        "Пропадал ли ранее",
        "Когда/как и где находили",
        "Обстоятельства пропажи",
        "Полиция",
        "Кого из родственников знает/помнит",
        "Семейное положение/близкие родственники",
        "К кому мог поехать",
        "Все прежние места жительства",
        "Есть ли дача, знает ли дорогу, как добирается",
        "Передвигается ли самостоятельно",
        "Привычные маршруты",
        "Общественный транспорт: умеет ли пользоваться, каким пользуется, боится/не боится, как ориентируется",
        "Что изменилось накануне пропажи",
        "Прежние места работы",
        "Вспоминает ли о работе",
        "Вспоминает ли кого-то из погибших родственников",
        "Где похоронены, как часто ездит на кладбище, стремится ли туда",
        "Куда стремится/просится/кого зовет/вспоминает",
        "Отдых/что делает в свободное время",
        "Коллеги/друзья/круг общения",
        "Особенности характера/поведения",
        "Реакция на незнакомых людей",
        "Обычный ритм жизни",
        "Отношение к религии",
        "Вредные привычки",
        "Чего боится/страхи",
        "Проблемы с законом",
        "Кредиты/долги",
        "Мысли о суициде",
        "Согласие на ориентировку",
    ],
}
CALL_META = {k: title for k, title in CALL_CATEGORIES}

# -------------------- Константы: Выезд --------------------

VYEZD_CLOTHES = ["город", "лес", "город/лес"]
VYEZD_TAKE = ["Сменная одежда", "Питание", "Скотч", "Ориентировки"]

EQUIP_PRESETS = {
    "flashlights": [15, 30, 45, 60],
    "batteries": [30, 45, 60, 90, 120],
    "radios": [10, 15, 20, 25, 30, 40],
    "navigators": [10, 15, 20, 25, 30, 40],
    "compasses": [15, 30, 45, 60],
}

EQUIP_TITLES = {
    "flashlights": "Фонари",
    "batteries": "Аккумуляторы",
    "radios": "Рации",
    "navigators": "Навигаторы",
    "compasses": "Компасы",
    "inverter": "Инвертор",
    "tape": "Скотч",
    "powerbank": "Power bank",
}

HQ_TEAM_ROLES = ["Регистратор", "Оперативный картограф", "Связь на ПСР", "Табор"]

# -------------------- Константы: Ресурсы --------------------

TECH_OPTIONS = [
    "Штабной автомобиль",
    "Проходимая техника",
    "Квадроциклы",
    "Снегоступы",
    "Болотоходы",
    "Штабной прицеп",
    "Комплект Шатер большой",
    "Комплект Шатер малый",
]

# -------------------- State --------------------

@dataclass
class CallEntry:
    who: str = ""
    selected: Dict[str, Set[int]] = field(default_factory=dict)
    manual: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class VyezdState:
    hq_address: str = ""
    hq_coords: str = ""
    hq_time: str = ""
    clothes: Optional[str] = None
    take: Set[str] = field(default_factory=set)
    equip_qty: Dict[str, int] = field(default_factory=dict)
    equip_flags: Set[str] = field(default_factory=set)
    hq_team: Set[str] = field(default_factory=set)

@dataclass
class ResourcesState:
    maps_center: str = ""
    maps_limits: str = ""
    maps_grid: str = ""
    maps_phonekit: Optional[bool] = None
    orient_qty: Optional[int] = None
    scooters: bool = False
    uav: bool = False
    angels: bool = False
    pegas: bool = False
    tech: Set[str] = field(default_factory=set)

@dataclass
class UserState:
    tasks: List[Tuple[str, str]] = field(default_factory=list)
    waiting_input: Optional[str] = None
    current_menu: str = "start"
    
    gkp_selected: Set[str] = field(default_factory=set)
    gkp_areas: Dict[str, Set[str]] = field(default_factory=dict)
    gkp_current_key: Optional[str] = None
    
    goo_selected: Set[str] = field(default_factory=set)
    goo_areas: Dict[str, Set[str]] = field(default_factory=dict)
    goo_custom: str = ""
    goo_current_key: Optional[str] = None
    
    call_entries: List[CallEntry] = field(default_factory=list)
    call_active: Optional[int] = None
    call_cat: Optional[str] = None
    call_questions_offset: int = 0
    
    vyezd: VyezdState = field(default_factory=VyezdState)
    vyezd_equip_current: Optional[str] = None
    
    resources: ResourcesState = field(default_factory=ResourcesState)

USERS: Dict[int, UserState] = {}

def st(uid: int) -> UserState:
    if uid not in USERS:
        USERS[uid] = UserState()
    return USERS[uid]

def reset_state(state: UserState):
    state.tasks.clear()
    state.waiting_input = None
    state.current_menu = "start"
    state.gkp_selected.clear()
    state.gkp_areas.clear()
    state.gkp_current_key = None
    state.goo_selected.clear()
    state.goo_areas.clear()
    state.goo_custom = ""
    state.goo_current_key = None
    state.call_entries.clear()
    state.call_active = None
    state.call_cat = None
    state.call_questions_offset = 0
    state.vyezd = VyezdState()
    state.vyezd_equip_current = None
    state.resources = ResourcesState()

def add_task_plain(state: UserState, key: str, human_text: str) -> None:
    state.tasks.append((key, md2_escape(human_text)))

def upsert_task_markdown(state: UserState, key: str, markdown_text: str) -> None:
    for i, (k, _) in enumerate(state.tasks):
        if k == key:
            state.tasks[i] = (key, markdown_text)
            return
    state.tasks.append((key, markdown_text))

def remove_task_by_key(state: UserState, key: str) -> None:
    state.tasks = [(k, v) for (k, v) in state.tasks if k != key]

def has_task(state: UserState, key: str) -> bool:
    return any(k == key for k, _ in state.tasks)

def toggle_simple_task(state: UserState, key: str, human_text: str) -> bool:
    if has_task(state, key):
        remove_task_by_key(state, key)
        return False
    add_task_plain(state, key, human_text)
    return True

# -------------------- GKP / GOO models --------------------

GKP_ITEMS = [
    ("gkp_adult_hosp_spb", "Больницы взрослые СПб", True, "spb"),
    ("gkp_adult_hosp_lo",  "Больницы взрослые ЛО", True, "lo"),
    ("gkp_adult_smp_spb",  "СМП взрослые СПб", True, "spb"),
    ("gkp_adult_smp_lo",   "СМП взрослые ЛО", True, "lo"),
    ("gkp_psy_adult_spb",  "Психиатрические больницы взрослые СПб", False, None),
    ("gkp_psy_adult_lo",   "Психиатрические больницы взрослые ЛО", False, None),
    ("gkp_psy_kids_spb",   "Психиатрические больницы дети СПб", False, None),
    ("gkp_psy_kids_lo",    "Психиатрические больницы дети ЛО", False, None),
    ("gkp_kids_hosp_spb",  "Больницы детские СПб", True, "spb"),
    ("gkp_kids_hosp_lo",   "Больницы детские ЛО", True, "lo"),
    ("gkp_kids_smp_spb",   "СМП детские СПб", True, "spb"),
    ("gkp_kids_smp_lo",    "СМП детские ЛО", True, "lo"),
    ("gkp_morg_spb",       "Морги СПб", False, None),
    ("gkp_morg_lo",        "Морги ЛО", False, None),
    ("gkp_pall_spb",       "Паллиативы СПб", False, None),
    ("gkp_pall_lo",        "Паллиативы ЛО", False, None),
]
GKP_META = {k: (title, needs_areas, kind) for k, title, needs_areas, kind in GKP_ITEMS}

GOO_ITEMS = [
    ("goo_big_spb",   "Размещение по крупным в СПб", True, "spb"),
    ("goo_big_lo",    "Размещение по крупным в ЛО", True, "lo"),
    ("goo_dense_spb", "Размещение плотно в СПб", True, "spb"),
    ("goo_dense_lo",  "Размещение плотно в ЛО", True, "lo"),
    ("goo_custom",    "Произвольная информация", False, None),
]
GOO_META = {k: (title, needs_areas, kind) for k, title, needs_areas, kind in GOO_ITEMS}

# -------------------- Aggregators --------------------

def gkp_aggregated_markdown(state: UserState) -> str:
    if not state.gkp_selected:
        return ""
    lines: List[str] = [md2_escape("☎ Запрос на ГКП:")]
    for key, title, needs_areas, _kind in GKP_ITEMS:
        if key not in state.gkp_selected:
            continue
        title_md = f"**{md2_escape(title)}**"
        if needs_areas:
            chosen_codes = sorted(state.gkp_areas.get(key, set()))
            chosen_names = [decode_area(c) for c in chosen_codes]
            areas_txt = ", ".join(chosen_names) if chosen_names else "районы не выбраны"
            lines.append(f"╴ {title_md}: {md2_escape(areas_txt)}")
        else:
            lines.append(f"╴ {title_md}")
    return "\n".join(lines)

def goo_aggregated_markdown(state: UserState) -> str:
    if not state.goo_selected:
        return ""
    lines: List[str] = [md2_escape("📱 Запрос на ГОО:")]
    for key, title, needs_areas, _kind in GOO_ITEMS:
        if key not in state.goo_selected:
            continue
        title_md = f"**{md2_escape(title)}**"
        if key == "goo_custom":
            info = state.goo_custom.strip() or "не заполнено"
            lines.append(f"╴ {title_md}: {md2_escape(info)}")
        elif needs_areas:
            chosen_codes = sorted(state.goo_areas.get(key, set()))
            chosen_names = [decode_area(c) for c in chosen_codes]
            areas_txt = ", ".join(chosen_names) if chosen_names else "не выбрано"
            lines.append(f"╴ {title_md}: {md2_escape(areas_txt)}")
    return "\n".join(lines)

def call_entry_render(entry: CallEntry) -> str:
    lines: List[str] = []
    who = (entry.who or "").strip()
    if who:
        lines.append(f"Кого прозвонить: {who}")
        lines.append("")
    for cat_key, _title in CALL_CATEGORIES:
        idxs = sorted(entry.selected.get(cat_key, set()))
        manual = entry.manual.get(cat_key, [])
        if not idxs and not manual:
            continue
        qs = CALL_QUESTIONS.get(cat_key, [])
        for i in idxs:
            if 0 <= i < len(qs):
                lines.append(f"- {qs[i]}")
        for t in manual:
            t = (t or "").strip()
            if t:
                lines.append(f"- {t}")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines).strip()

def calls_aggregated_markdown(state: UserState) -> str:
    rendered = []
    for e in state.call_entries:
        r = call_entry_render(e)
        if r:
            rendered.append(r)
    if not rendered:
        return ""
    text = "📞 Допрозвон:\n" + "\n\n".join(rendered)
    return md2_escape(text)

def upsert_calls_task(state: UserState):
    md = calls_aggregated_markdown(state)
    if md:
        upsert_task_markdown(state, "CALLS_AGG", md)
    else:
        remove_task_by_key(state, "CALLS_AGG")

def vyezd_aggregated_markdown(state: UserState) -> str:
    v = state.vyezd
    if not any([v.hq_address, v.hq_coords, v.hq_time, v.clothes, v.take, v.equip_qty, v.equip_flags, v.hq_team]):
        return ""
    lines = ["Готовим выезд 🚗"]
    if v.hq_address:
        lines.append(f"🏕 Адрес штаба: {v.hq_address}")
    if v.hq_coords:
        lines.append(f"📍Координаты штаба: {v.hq_coords}")
    if v.hq_time:
        lines.append(f"⏰ Время штаба: {v.hq_time}")
    if v.clothes:
        lines.append(f"🥾 Форма одежды: {v.clothes}")
    if v.take:
        lines.append("🎒 Взять с собой: " + ", ".join(sorted(v.take)))
    eq_lines = []
    for k in ["flashlights", "batteries", "radios", "navigators", "compasses"]:
        if k in v.equip_qty:
            eq_lines.append(f"{EQUIP_TITLES[k]}: {v.equip_qty[k]}")
    for flag in ["inverter", "tape", "powerbank"]:
        if flag in v.equip_flags:
            eq_lines.append(f"{EQUIP_TITLES[flag]}")
    if eq_lines:
        lines.append("🛠 Запрос оборудования: " + "; ".join(eq_lines))
    if v.hq_team:
        lines.append("👥 Запрос штабной команды: " + ", ".join(sorted(v.hq_team)))
    return md2_escape("\n".join(lines))

def upsert_vyezd_task(state: UserState):
    md = vyezd_aggregated_markdown(state)
    if md:
        upsert_task_markdown(state, "VYEZD_AGG", md)
    else:
        remove_task_by_key(state, "VYEZD_AGG")

def resources_aggregated_markdown(state: UserState) -> str:
    r = state.resources
    if not any([r.maps_center, r.maps_limits, r.maps_grid, r.maps_phonekit is not None,
                r.orient_qty is not None, r.scooters, r.uav, r.angels, r.tech]):
        return ""
    lines = ["🛠 Запрос на ресурсы:"]
    if any([r.maps_center, r.maps_limits, r.maps_grid, r.maps_phonekit is not None]):
        lines.append("🗺 Запрос на Карты:")
        if r.maps_center:
            lines.append(f"  Центр зоны: {r.maps_center}")
        if r.maps_limits:
            lines.append(f"  Ограничители зоны: {r.maps_limits}")
        if r.maps_grid:
            lines.append(f"  Шаг сетки: {r.maps_grid}")
        if r.maps_phonekit is not None:
            lines.append(f"  Комплект для телефонов: {'да' if r.maps_phonekit else 'нет'}")
    if r.orient_qty is not None:
        lines.append(f"🖨 Запрос на Ориентировки: {r.orient_qty}")
    if r.scooters:
        lines.append("🛴 Запрос на самокаты")
    if r.uav:
        lines.append("🛸 Запрос на БПЛА")
    if r.angels:
        lines.append("🚁 Запрос на Ангелов")
    if r.pegas:
        lines.append("🐴 Запрос на Пегасов")
    if r.tech:
        lines.append("🧢 Запрос на технику: " + ", ".join(sorted(r.tech)))
    return md2_escape("\n".join(lines))

def upsert_resources_task(state: UserState):
    md = resources_aggregated_markdown(state)
    if md:
        upsert_task_markdown(state, "RESOURCES_AGG", md)
    else:
        remove_task_by_key(state, "RESOURCES_AGG")

def vyezd_equipment_markdown(state: UserState) -> str:
    v = state.vyezd
    lines = ["🎒 Запрос оборудования\n"]
    
    EQUIPMENT_NAMES_RU = {
        "flashlights": "Фонари",
        "radios": "Рации",
        "batteries": "Аккумуляторы",
        "navigators": "Навигаторы",
        "compasses": "Компасы",
        "powerbanks": "Павербанки",
        "inverter": "Инвертор",
        "tape": "Скотч",
    }
    
    if v.equip_qty:
        for item, qty in sorted(v.equip_qty.items()):
            item_ru = EQUIPMENT_NAMES_RU.get(item, item)
            lines.append(f"• {item_ru}: {qty} шт.")
    
    if v.equip_flags:
        for item in sorted(v.equip_flags):
            item_ru = EQUIPMENT_NAMES_RU.get(item, item)
            lines.append(f"• {item_ru}")
    
    return md2_escape("\n".join(lines))

def vyezd_hq_team_markdown(state: UserState) -> str:
    v = state.vyezd
    if not v.hq_team:
        return ""
    
    lines = ["👥 Запрос штабной команды\n"]
    lines.extend(f"• {name}" for name in sorted(v.hq_team))
    
    return md2_escape("\n".join(lines))

# -------------------- Keyboards --------------------

def kb_start():
    b = ReplyKeyboardBuilder()
    b.button(text="📝 Заполнить")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_main():
    b = ReplyKeyboardBuilder()
    b.button(text="📋 Задачи для инфоргов")
    b.button(text="🚗 Выезд")
    b.button(text="🛠 Запрос на ресурсы")
    b.button(text="💾 Показать итог")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_after_summary():
    b = ReplyKeyboardBuilder()
    b.button(text="🖋 Новый запрос")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_cancel():
    b = ReplyKeyboardBuilder()
    b.button(text="❌ Отмена")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_back(back_text: str = "👈 Назад"):
    b = ReplyKeyboardBuilder()
    b.button(text=back_text)
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_inforg(state: UserState):
    def mark(key: str) -> str:
        return "✅ " if has_task(state, key) else ""

    b = ReplyKeyboardBuilder()
    b.button(text=f"{mark('CALLS_AGG')}📞 Допрозвон")
    b.button(text=f"{mark('AGG_GOO')}📱 Запрос на ГОО")
    b.button(text=f"{mark('AGG_GKP')}☎ Запрос на ГКП")
    b.button(text=f"{mark('peleng')}📌 Запрос Пеленг")
    b.button(text=f"{mark('cam_bg')}🎥 Запрос камеры БГ")
    b.button(text=f"{mark('megafon')}📢 Оповещение Мегафон")
    b.button(text=f"{mark('avtonom')}🚨 Поиск автономных групп")
    b.button(text=f"{mark('LNS')}🔔 Контроль ЛНС")
    b.button(text=f"{mark('custom')}🖌 Пользовательский запрос")
    b.button(text="👈 Назад в главное меню")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_gkp(state: UserState):
    b = ReplyKeyboardBuilder()
    for key, title, _, _ in GKP_ITEMS:
        mark = "✅ " if key in state.gkp_selected else ""
        b.button(text=f"{mark}{title}")
    b.button(text="✔️ Готово")
    b.button(text="👈 Назад")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_goo(state: UserState):
    b = ReplyKeyboardBuilder()
    for key, title, _, _ in GOO_ITEMS:
        mark = "✅ " if key in state.goo_selected else ""
        b.button(text=f"{mark}{title}")
    b.button(text="✔️ Готово")
    b.button(text="👈 Назад")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_areas(kind: str, selected: Set[str]):
    b = ReplyKeyboardBuilder()
    
    if kind == "spb":
        all_code = "SPB_ALL"
        mark = "✅ " if all_code in selected else ""
        b.button(text=f"{mark}Весь город")
        for i, name in enumerate(SPB_DISTRICTS):
            code = spb_code(i)
            mark = "✅ " if code in selected else ""
            b.button(text=f"{mark}{name}")
    elif kind == "lo":
        all_code = "LO_ALL"
        mark = "✅ " if all_code in selected else ""
        b.button(text=f"{mark}Вся область")
        for i, name in enumerate(LO_DISTRICTS):
            code = lo_code(i)
            mark = "✅ " if code in selected else ""
            b.button(text=f"{mark}{name}")
    
    b.button(text="✔️ Готово")
    b.button(text="👈 Назад")
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)

def kb_call_categories(state: UserState):
    b = ReplyKeyboardBuilder()
    entry = None
    if state.call_active is not None and 0 <= state.call_active < len(state.call_entries):
        entry = state.call_entries[state.call_active]
    
    for cat_key, title in CALL_CATEGORIES:
        chosen = False
        if entry:
            chosen = bool(entry.selected.get(cat_key)) or bool(entry.manual.get(cat_key))
        mark = "✅ " if chosen else ""
        b.button(text=f"{mark}{title}")
    
    b.button(text="➕ Добавить ещё допрозвон")
    b.button(text="✔️ Готово")
    b.button(text="👈 Назад")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_call_questions(cat_key: str, selected: Set[int], offset: int = 0):
    b = ReplyKeyboardBuilder()
    questions = CALL_QUESTIONS.get(cat_key, [])
    
    # Показываем 20 вопросов начиная с offset
    page_size = 20
    start_idx = offset
    end_idx = min(start_idx + page_size, len(questions))
    
    for idx in range(start_idx, end_idx):
        q = questions[idx]
        mark = "✅ " if idx in selected else ""
        short_q = q[:40] + "..." if len(q) > 40 else q
        b.button(text=f"{mark}{short_q}")
    
    # Кнопки навигации
    if end_idx < len(questions):
        b.button(text="➡️ Показать ещё вопросы")
    if offset > 0:
        b.button(text="⬅️ Показать предыдущие")
    
    b.button(text="✏️ Ручной ввод")
    b.button(text="👈 Назад к категориям")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_vyezd_clothes(current: Optional[str]):
    b = ReplyKeyboardBuilder()
    for opt in VYEZD_CLOTHES:
        mark = "✅ " if current == opt else ""
        b.button(text=f"{mark}{opt}")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_vyezd_take(selected: Set[str]):
    b = ReplyKeyboardBuilder()
    for opt in VYEZD_TAKE:
        mark = "✅ " if opt in selected else ""
        b.button(text=f"{mark}{opt}")
    b.button(text="✔️ Готово")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_equip_menu(v: VyezdState):
    def mark_qty(k: str) -> str:
        return f"✅ " if k in v.equip_qty else ""
    def mark_flag(k: str) -> str:
        return f"✅ " if k in v.equip_flags else ""
    
    b = ReplyKeyboardBuilder()
    b.button(text=f"{mark_qty('flashlights')}🔦 Фонари")
    b.button(text=f"{mark_qty('batteries')}🔋 Аккумуляторы")
    b.button(text=f"{mark_qty('radios')}📢 Рации")
    b.button(text=f"{mark_qty('navigators')}🗺️ Навигаторы")
    b.button(text=f"{mark_qty('compasses')}🧭 Компасы")
    b.button(text=f"{mark_flag('inverter')}🔌 Инвертор")
    b.button(text=f"{mark_flag('tape')}📄 Скотч")
    b.button(text=f"{mark_flag('powerbank')}⚡ Power bank")
    b.button(text="👉 Дальше")
    b.button(text="👈 Назад")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_equip_qty(kind: str):
    b = ReplyKeyboardBuilder()
    for n in EQUIP_PRESETS[kind]:
        b.button(text=str(n))
    b.button(text="✏️ Ввести количество")
    b.button(text="👈 Назад")
    b.adjust(3)
    return b.as_markup(resize_keyboard=True)

def kb_hq_team(selected: Set[str]):
    b = ReplyKeyboardBuilder()
    for role in HQ_TEAM_ROLES:
        mark = "✅ " if role in selected else ""
        b.button(text=f"{mark}{role}")
    b.button(text="✔️ Готово")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_resources_menu(r: ResourcesState):
    def mark_bool(v: bool) -> str:
        return "✅ " if v else ""
    def mark_val(v) -> str:
        return "✅ " if v not in (None, "", set()) else ""
    
    b = ReplyKeyboardBuilder()
    b.button(text=f"{mark_val(r.maps_center or r.maps_limits or r.maps_grid or r.maps_phonekit)}🗺 Запрос на Карты")
    b.button(text=f"{mark_val(r.orient_qty)}🖨 Запрос на Ориентировки")
    b.button(text=f"{mark_bool(r.scooters)}🛴 Запрос на самокаты")
    b.button(text=f"{mark_bool(r.uav)}🛸 Запрос на БПЛА")
    b.button(text=f"{mark_bool(r.angels)}🚁 Запрос на Ангелов")
    b.button(text=f"{mark_bool(r.pegas)}🐴 Запрос на Пегасов")
    b.button(text=f"{mark_val(r.tech)}🧢 Запрос на технику")
    b.button(text="✔️ Готово")
    b.button(text="👈 Назад")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

def kb_yes_no():
    b = ReplyKeyboardBuilder()
    b.button(text="Да")
    b.button(text="Нет")
    b.button(text="👈 Назад")
    b.adjust(2)
    return b.as_markup(resize_keyboard=True)

def kb_tech_picker(selected: Set[str]):
    b = ReplyKeyboardBuilder()
    for opt in TECH_OPTIONS:
        mark = "✅ " if opt in selected else ""
        b.button(text=f"{mark}{opt}")
    b.button(text="✔️ Готово")
    b.adjust(1)
    return b.as_markup(resize_keyboard=True)

# -------------------- Summary --------------------

async def send_summary_separated(chat_id: int, bot: Bot, state: UserState):
    if state.tasks:
        await bot.send_message(chat_id, "📋 Список задач:")
        for (_k, text_md) in state.tasks:
            if _k in ("VYEZD_AGG", "EQUIP_AGG", "HQ_TEAM_AGG", "RESOURCES_AGG"):
                continue
            await bot.send_message(chat_id, text_md, parse_mode=ParseMode.MARKDOWN_V2)
            await asyncio.sleep(0.3)
    
    v = state.vyezd
    
    main_info_lines = []
    
    if v.hq_address:
        main_info_lines.append(f"🏕 Адрес штаба: {v.hq_address}")
    
    if v.hq_coords:
        main_info_lines.append(f"📍 Координаты штаба: {v.hq_coords}")
    
    if v.hq_time:
        main_info_lines.append(f"⏰ Время штаба: {v.hq_time}")
    
    if v.clothes:
        main_info_lines.append(f"🥾 Форма одежды: {v.clothes}")
    
    if v.take:
        main_info_lines.append("🎒 Взять с собой: " + ", ".join(sorted(v.take)))
    
    if main_info_lines:
        main_text = md2_escape("🚗 Готовим выезд\n\n" + "\n".join(main_info_lines))
        await bot.send_message(chat_id, main_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    if any([v.equip_qty, v.equip_flags]):
        equipment_text = vyezd_equipment_markdown(state)
        if equipment_text:
            await bot.send_message(chat_id, equipment_text, parse_mode="MarkdownV2")
            await asyncio.sleep(0.5)
    
    if v.hq_team:
        hq_team_text = vyezd_hq_team_markdown(state)
        if hq_team_text:
            await bot.send_message(chat_id, hq_team_text, parse_mode="MarkdownV2")
            await asyncio.sleep(0.5)
    
    r = state.resources
    
    if r.maps_center or r.maps_limits or r.maps_grid or r.maps_phonekit is not None:
        maps_lines = ["🗺 Запрос на Карты\n"]
        if r.maps_center:
            maps_lines.append(f"Центр зоны: {r.maps_center}")
        if r.maps_limits:
            maps_lines.append(f"Ограничители зоны: {r.maps_limits}")
        if r.maps_grid:
            maps_lines.append(f"Шаг сетки: {r.maps_grid}")
        if r.maps_phonekit is not None:
            maps_lines.append(f"Комплект для телефонов: {'Да' if r.maps_phonekit else 'Нет'}")
        
        maps_text = md2_escape("\n".join(maps_lines))
        await bot.send_message(chat_id, maps_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    if r.orient_qty is not None:
        orient_text = md2_escape(f"🖨 Запрос на Ориентировки: {r.orient_qty} шт.")
        await bot.send_message(chat_id, orient_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    if r.scooters:
        scooters_text = md2_escape("🛴 Запрос на самокаты")
        await bot.send_message(chat_id, scooters_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    if r.uav:
        uav_text = md2_escape("🛸 Запрос на БПЛА")
        await bot.send_message(chat_id, uav_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    if r.angels:
        angels_text = md2_escape("🚁 Запрос на Ангелов")
        await bot.send_message(chat_id, angels_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)

    if r.pegas:
        pegas_text = md2_escape("🐴 Запрос на Пегасов")
        await bot.send_message(chat_id, pegas_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    if r.tech:
        tech_text = md2_escape("🧢 Запрос на технику:\n" + "\n".join(f"• {t}" for t in sorted(r.tech)))
        await bot.send_message(chat_id, tech_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    has_vyezd = main_info_lines or v.equip_qty or v.equip_flags or v.hq_team
    has_resources = (r.maps_center or r.maps_limits or r.maps_grid or 
                    r.maps_phonekit is not None or r.orient_qty is not None or 
                    r.scooters or r.uav or r.angels or r.tech)
    
    if not state.tasks and not has_vyezd and not has_resources:
        await bot.send_message(chat_id, "❗ Список задач пуст.")

# -------------------- Handlers --------------------

dp = Dispatcher()

@dp.message(CommandStart())
async def start(m: Message):
    reset_state(st(m.from_user.id))
    await m.answer("Нажмите «Заполнить», чтобы начать", reply_markup=kb_start())

@dp.message(F.text == "📝 Заполнить")
async def start_fill(m: Message):
    state = st(m.from_user.id)
    reset_state(state)
    state.current_menu = "main"
    await m.answer("👆 Выберите раздел:", reply_markup=kb_main())

@dp.message(F.text == "🖋 Новый запрос")
async def new_request(m: Message):
    state = st(m.from_user.id)
    reset_state(state)
    await m.answer("Нажмите «Заполнить», чтобы начать", reply_markup=kb_start())

@dp.message(F.text.in_(["👈 Назад в главное меню", "👈 Назад"]))
async def back_to_main(m: Message):
    state = st(m.from_user.id)
    
    if state.current_menu == "inforg":
        state.current_menu = "main"
        state.waiting_input = None
        await m.answer("👆 Выберите раздел:", reply_markup=kb_main())
    elif state.current_menu == "gkp":
        state.current_menu = "inforg"
        state.waiting_input = None
        await m.answer("📋 Задачи для инфоргов — выберите пункт:", reply_markup=kb_inforg(state))
    elif state.current_menu == "gkp_areas":
        state.current_menu = "gkp"
        state.waiting_input = None
        await m.answer("Запрос на ГКП — выберите нужные пункты (можно несколько):", reply_markup=kb_gkp(state))
    elif state.current_menu == "goo":
        state.current_menu = "inforg"
        state.waiting_input = None
        await m.answer("📋 Задачи для инфоргов — выберите пункт:", reply_markup=kb_inforg(state))
    elif state.current_menu == "goo_areas":
        state.current_menu = "goo"
        state.waiting_input = None
        await m.answer("Запрос на ГОО — выберите пункты (можно несколько):", reply_markup=kb_goo(state))
    elif state.current_menu == "call_categories":
        state.current_menu = "inforg"
        state.waiting_input = None
        await m.answer("📋 Задачи для инфоргов — выберите пункт:", reply_markup=kb_inforg(state))
    elif state.current_menu == "call_questions":
        state.current_menu = "call_categories"
        state.waiting_input = None
        state.call_questions_offset = 0
        await m.answer("Допрозвон — выберите категорию:", reply_markup=kb_call_categories(state))
    elif state.current_menu == "vyezd_equip":
        state.current_menu = "main"
        state.waiting_input = None
        await m.answer("👆 Выберите раздел:", reply_markup=kb_main())
    elif state.current_menu == "vyezd_equip_qty":
        state.current_menu = "vyezd_equip"
        state.waiting_input = None
        await m.answer("Выезд → Запрос оборудования", reply_markup=kb_equip_menu(state.vyezd))
    elif state.current_menu == "resources_menu":
        state.current_menu = "main"
        state.waiting_input = None
        await m.answer("👆 Выберите раздел:", reply_markup=kb_main())
    else:
        state.current_menu = "main"
        state.waiting_input = None
        await m.answer("👆 Выберите раздел:", reply_markup=kb_main())

# -------------------- Main Menu --------------------

@dp.message(F.text == "📋 Задачи для инфоргов")
async def main_inforg(m: Message):
    state = st(m.from_user.id)
    state.current_menu = "inforg"
    state.waiting_input = None
    await m.answer("📋 Задачи для инфоргов — выберите пункт:", reply_markup=kb_inforg(state))

@dp.message(F.text == "💾 Показать итог")
async def show_summary(m: Message):
    state = st(m.from_user.id)
    state.waiting_input = None
    await send_summary_separated(m.chat.id, m.bot, state)
    await m.answer("Завершено", reply_markup=kb_after_summary())

# -------------------- Inforg Simple Tasks --------------------

@dp.message(F.text.regexp(r"^✅?\s*📌 Запрос Пеленг"))
async def inf_peleng(m: Message):
    state = st(m.from_user.id)
    toggle_simple_task(state, "peleng", "📌 Запрос Пеленг")
    await m.answer("Задача обновлена", reply_markup=kb_inforg(state))

@dp.message(F.text.regexp(r"^✅?\s*🎥 Запрос камеры БГ"))
async def inf_cam_bg(m: Message):
    state = st(m.from_user.id)
    toggle_simple_task(state, "cam_bg", "🎥 Запрос камеры БГ")
    await m.answer("Задача обновлена", reply_markup=kb_inforg(state))

@dp.message(F.text.regexp(r"^✅?\s*🚨 Поиск автономных групп"))
async def inf_avtonom(m: Message):
    state = st(m.from_user.id)
    toggle_simple_task(state, "avtonom", "🚨 Поиск автономных групп")
    await m.answer("Задача обновлена", reply_markup=kb_inforg(state))

@dp.message(F.text.regexp(r"^✅?\s*🔔 Контроль ЛНС"))
async def inf_lns(m: Message):
    state = st(m.from_user.id)
    toggle_simple_task(state, "LNS", "🔔 Контроль ЛНС")
    await m.answer("Задача обновлена", reply_markup=kb_inforg(state))

@dp.message(F.text.regexp(r"^✅?\s*📢 Оповещение Мегафон"))
async def inf_megafon(m: Message):
    state = st(m.from_user.id)
    toggle_simple_task(state, "megafon", "📢 Оповещение Мегафон")
    await m.answer("Задача обновлена", reply_markup=kb_inforg(state))

# -------------------- Custom Task --------------------

@dp.message(F.text.regexp(r"^✅?\s*🖌 Пользовательский запрос"))
async def inf_custom(m: Message):
    state = st(m.from_user.id)
    state.waiting_input = "custom"
    await m.answer("Введите пользовательский текст (сообщением)", reply_markup=kb_cancel())

# -------------------- GKP --------------------

@dp.message(F.text.regexp(r"^✅?\s*☎ Запрос на ГКП"))
async def inf_gkp(m: Message):
    state = st(m.from_user.id)
    state.current_menu = "gkp"
    state.waiting_input = None
    await m.answer("Запрос на ГКП — выберите нужные пункты (можно несколько):", reply_markup=kb_gkp(state))

@dp.message(F.text == "✔️ Готово")
async def gkp_goo_done(m: Message):
    state = st(m.from_user.id)
    
    if state.current_menu == "gkp":
        txt_md = gkp_aggregated_markdown(state)
        if txt_md:
            upsert_task_markdown(state, "AGG_GKP", txt_md)
        else:
            remove_task_by_key(state, "AGG_GKP")
        state.current_menu = "inforg"
        await m.answer("Готово", reply_markup=kb_inforg(state))
        
    elif state.current_menu == "goo":
        txt_md = goo_aggregated_markdown(state)
        if txt_md:
            upsert_task_markdown(state, "AGG_GOO", txt_md)
        else:
            remove_task_by_key(state, "AGG_GOO")
        state.current_menu = "inforg"
        await m.answer("Готово", reply_markup=kb_inforg(state))
        
    elif state.current_menu == "gkp_areas":
        state.current_menu = "gkp"
        await m.answer("Запрос на ГКП — выберите нужные пункты:", reply_markup=kb_gkp(state))
        
    elif state.current_menu == "goo_areas":
        state.current_menu = "goo"
        await m.answer("Запрос на ГОО — выберите пункты:", reply_markup=kb_goo(state))
        
    elif state.current_menu == "call_categories":
        upsert_calls_task(state)
        state.current_menu = "inforg"
        await m.answer("Готово", reply_markup=kb_inforg(state))
        
    elif state.current_menu == "vyezd_take":
        state.current_menu = "vyezd_equip"
        await m.answer("Выезд → Запрос оборудования:", reply_markup=kb_equip_menu(state.vyezd))
        
    elif state.current_menu == "vyezd_hq_team":
        upsert_vyezd_task(state)
        state.current_menu = "main"
        await m.answer("Готово", reply_markup=kb_main())
        
    elif state.current_menu == "resources_menu":
        upsert_resources_task(state)
        state.current_menu = "main"
        await m.answer("Готово", reply_markup=kb_main())
        
    elif state.current_menu == "tech_picker":
        upsert_resources_task(state)
        state.current_menu = "resources_menu"
        await m.answer("Запрос на ресурсы — выберите пункт:", reply_markup=kb_resources_menu(state.resources))

# -------------------- GOO --------------------

@dp.message(F.text.regexp(r"^✅?\s*📱 Запрос на ГОО"))
async def inf_goo(m: Message):
    state = st(m.from_user.id)
    state.current_menu = "goo"
    state.waiting_input = None
    await m.answer("Запрос на ГОО — выберите пункты (можно несколько):", reply_markup=kb_goo(state))

# -------------------- Call --------------------

@dp.message(F.text.regexp(r"^✅?\s*📞 Допрозвон"))
async def inf_call(m: Message):
    state = st(m.from_user.id)
    state.current_menu = "call_who"
    state.waiting_input = "call_who"
    
    if not state.call_entries:
        state.call_entries.append(CallEntry())
        state.call_active = 0
    
    await m.answer("Допрозвон\n\nКого нужно прозвонить? Напишите текст сообщением.", reply_markup=kb_cancel())

@dp.message(F.text == "➕ Добавить ещё допрозвон")
async def call_new_entry(m: Message):
    state = st(m.from_user.id)
    state.call_entries.append(CallEntry())
    state.call_active = len(state.call_entries) - 1
    state.call_cat = None
    state.waiting_input = "call_who"
    await m.answer("Новый допрозвон\n\nКого нужно прозвонить? Напишите текст сообщением.", reply_markup=kb_cancel())

@dp.message(F.text == "👈 Назад к категориям")
async def call_back_to_cats(m: Message):
    state = st(m.from_user.id)
    state.current_menu = "call_categories"
    state.waiting_input = None
    state.call_questions_offset = 0
    await m.answer("Допрозвон — выберите категорию:", reply_markup=kb_call_categories(state))

@dp.message(F.text == "✏️ Ручной ввод")
async def call_manual(m: Message):
    state = st(m.from_user.id)
    if state.current_menu == "call_questions":
        state.waiting_input = "call_manual"
        await m.answer("Введите свой вопрос/текст (сообщением).", reply_markup=kb_cancel())

@dp.message(F.text == "➡️ Показать ещё вопросы")
async def call_show_more(m: Message):
    state = st(m.from_user.id)
    if state.current_menu == "call_questions" and state.call_cat:
        state.call_questions_offset += 20
        entry = state.call_entries[state.call_active]
        selected = entry.selected.setdefault(state.call_cat, set())
        await m.answer("Допрозвон → Следующие вопросы:", 
                      reply_markup=kb_call_questions(state.call_cat, selected, state.call_questions_offset))

@dp.message(F.text == "⬅️ Показать предыдущие")
async def call_show_prev(m: Message):
    state = st(m.from_user.id)
    if state.current_menu == "call_questions" and state.call_cat:
        state.call_questions_offset = max(0, state.call_questions_offset - 20)
        entry = state.call_entries[state.call_active]
        selected = entry.selected.setdefault(state.call_cat, set())
        await m.answer("Допрозвон → Предыдущие вопросы:", 
                      reply_markup=kb_call_questions(state.call_cat, selected, state.call_questions_offset))

# -------------------- Vyezd --------------------

@dp.message(F.text == "🚗 Выезд")
async def main_vyezd(m: Message):
    state = st(m.from_user.id)
    state.current_menu = "vyezd_hq_address"
    state.waiting_input = "vyezd_hq_address"
    await m.answer("Выезд\n\nВведите адрес штаба (сообщением).", reply_markup=kb_cancel())

@dp.message(F.text == "👉 Дальше")
async def vyezd_to_hqteam(m: Message):
    state = st(m.from_user.id)
    if state.current_menu == "vyezd_equip":
        state.current_menu = "vyezd_hq_team"
        await m.answer("Выезд → Запрос штабной команды (можно несколько):", reply_markup=kb_hq_team(state.vyezd.hq_team))

# -------------------- Resources --------------------

@dp.message(F.text == "🛠 Запрос на ресурсы")
async def main_resources(m: Message):
    state = st(m.from_user.id)
    state.current_menu = "resources_menu"
    state.waiting_input = None
    await m.answer("Запрос на ресурсы — выберите пункт:", reply_markup=kb_resources_menu(state.resources))

@dp.message(F.text.regexp(r"^✅?\s*🗺 Запрос на Карты"))
async def res_maps(m: Message):
    state = st(m.from_user.id)
    state.waiting_input = "res_maps_center"
    await m.answer("Запрос на Карты\n\nВведите «Центр зоны» (сообщением).", reply_markup=kb_cancel())

@dp.message(F.text.regexp(r"^✅?\s*🖨 Запрос на Ориентировки"))
async def res_orients(m: Message):
    state = st(m.from_user.id)
    state.waiting_input = "res_orient_qty"
    await m.answer("Запрос на Ориентировки\n\nУкажите количество (сообщением).", reply_markup=kb_cancel())

@dp.message(F.text.regexp(r"^✅?\s*🛴 Запрос на самокаты"))
async def res_scooters(m: Message):
    state = st(m.from_user.id)
    state.resources.scooters = not state.resources.scooters
    upsert_resources_task(state)
    await m.answer("Обновлено", reply_markup=kb_resources_menu(state.resources))

@dp.message(F.text.regexp(r"^✅?\s*🛸 Запрос на БПЛА"))
async def res_uav(m: Message):
    state = st(m.from_user.id)
    state.resources.uav = not state.resources.uav
    upsert_resources_task(state)
    await m.answer("Обновлено", reply_markup=kb_resources_menu(state.resources))

@dp.message(F.text.regexp(r"^✅?\s*🚁 Запрос на Ангелов"))
async def res_angels(m: Message):
    state = st(m.from_user.id)
    state.resources.angels = not state.resources.angels
    upsert_resources_task(state)
    await m.answer("Обновлено", reply_markup=kb_resources_menu(state.resources))

@dp.message(F.text.regexp(r"^✅?\s*🐴 Запрос на Пегасов"))
async def res_pegas(m: Message):
    state = st(m.from_user.id)
    state.resources.pegas = not state.resources.pegas
    upsert_resources_task(state)
    await m.answer("Обновлено", reply_markup=kb_resources_menu(state.resources))

@dp.message(F.text.regexp(r"^✅?\s*🧢 Запрос на технику"))
async def res_tech(m: Message):
    state = st(m.from_user.id)
    state.current_menu = "tech_picker"
    await m.answer("Запрос на технику (можно несколько):", reply_markup=kb_tech_picker(state.resources.tech))

# -------------------- Text Input Handler --------------------

TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

@dp.message(F.text)
async def on_text(m: Message):
    state = st(m.from_user.id)
    text = (m.text or "").strip()
    
    if not text:
        return
    
    # Обработка отмены
    if text == "❌ Отмена":
        state.waiting_input = None
        if state.current_menu in ["inforg", "gkp", "goo", "call_categories"]:
            await m.answer("Отменено", reply_markup=kb_inforg(state))
        else:
            state.current_menu = "main"
            await m.answer("Отменено", reply_markup=kb_main())
        return
    
    # --- ВАЖНО: Сначала проверяем waiting_input ---
    if state.waiting_input:
        # custom
        if state.waiting_input == "custom":
            remove_task_by_key(state, "custom")
            add_task_plain(state, "custom", text)
            state.waiting_input = None
            state.current_menu = "inforg"
            await m.answer("Принято.", reply_markup=kb_inforg(state))
            return
        
        # goo_custom
        if state.waiting_input == "goo_custom":
            state.goo_custom = text
            state.waiting_input = None
            state.current_menu = "goo"
            await m.answer("Принято. Вернуться к ГОО:", reply_markup=kb_goo(state))
            return
        
        # call_who
        if state.waiting_input == "call_who":
            if not state.call_entries:
                state.call_entries.append(CallEntry())
                state.call_active = 0
            entry = state.call_entries[state.call_active]
            entry.who = text
            state.waiting_input = None
            state.current_menu = "call_categories"
            await m.answer("Принято. Теперь выберите категорию вопросов:", 
                         reply_markup=kb_call_categories(state))
            return
        
        # call_manual
        if state.waiting_input == "call_manual":
            cat_key = state.call_cat
            if not cat_key:
                state.waiting_input = None
                await m.answer("Категория не выбрана. Откройте «Допрозвон» заново.", reply_markup=kb_main())
                return
            entry = state.call_entries[state.call_active]
            entry.manual.setdefault(cat_key, []).append(text)
            state.waiting_input = None
            state.current_menu = "call_questions"
            selected = entry.selected.setdefault(cat_key, set())
            await m.answer("Добавлено.", reply_markup=kb_call_questions(cat_key, selected, state.call_questions_offset))
            return
        
        # vyezd_hq_address
        if state.waiting_input == "vyezd_hq_address":
            state.vyezd.hq_address = text
            state.waiting_input = "vyezd_hq_coords"
            await m.answer("Введите координаты штаба (сообщением).", reply_markup=kb_cancel())
            return
        
        # vyezd_hq_coords
        if state.waiting_input == "vyezd_hq_coords":
            state.vyezd.hq_coords = text
            state.waiting_input = "vyezd_hq_time"
            await m.answer("Введите время штаба в формате HH:MM (24-часовой).", reply_markup=kb_cancel())
            return
        
        # vyezd_hq_time
        if state.waiting_input == "vyezd_hq_time":
            if not TIME_RE.match(text):
                await m.answer("Неверный формат. Нужно HH:MM (например 09:30 или 18:05). Повторите ввод.")
                return
            state.vyezd.hq_time = text
            state.waiting_input = None
            state.current_menu = "vyezd_clothes"
            await m.answer("Выберите форму одежды:", reply_markup=kb_vyezd_clothes(state.vyezd.clothes))
            return
        
        # eq_custom
        if state.waiting_input.startswith("eq_custom:"):
            kind = state.waiting_input.split(":", 1)[1]
            if not text.isdigit() or int(text) <= 0:
                await m.answer("Введите положительное целое число.")
                return
            state.vyezd.equip_qty[kind] = int(text)
            state.waiting_input = None
            state.current_menu = "vyezd_equip"
            await m.answer("Установлено.", reply_markup=kb_equip_menu(state.vyezd))
            return
        
        # res_maps_center
        if state.waiting_input == "res_maps_center":
            state.resources.maps_center = text
            state.waiting_input = "res_maps_limits"
            await m.answer("Введите «Ограничители зоны» (сообщением).", reply_markup=kb_cancel())
            return
        
        # res_maps_limits
        if state.waiting_input == "res_maps_limits":
            state.resources.maps_limits = text
            state.waiting_input = "res_maps_grid"
            await m.answer("Введите «Шаг сетки» (сообщением).", reply_markup=kb_cancel())
            return
        
        # res_maps_grid
        if state.waiting_input == "res_maps_grid":
            state.resources.maps_grid = text
            state.waiting_input = "res_maps_phonekit"
            state.current_menu = "res_maps_phonekit"
            await m.answer("Комплект для телефонов?", reply_markup=kb_yes_no())
            return
        
        # res_maps_phonekit
        if state.waiting_input == "res_maps_phonekit":
            if text == "Да":
                state.resources.maps_phonekit = True
            elif text == "Нет":
                state.resources.maps_phonekit = False
            else:
                await m.answer("Выберите Да или Нет", reply_markup=kb_yes_no())
                return
            state.waiting_input = None
            state.current_menu = "resources_menu"
            upsert_resources_task(state)
            await m.answer("Принято.", reply_markup=kb_resources_menu(state.resources))
            return
        
        # res_orient_qty
        if state.waiting_input == "res_orient_qty":
            if not text.isdigit() or int(text) < 0:
                await m.answer("Введите число (0 или больше).")
                return
            state.resources.orient_qty = int(text)
            state.waiting_input = None
            state.current_menu = "resources_menu"
            upsert_resources_task(state)
            await m.answer("Принято.", reply_markup=kb_resources_menu(state.resources))
            return
    
    # --- Теперь проверяем current_menu ---
    
    # --- GKP Selection ---
    if state.current_menu == "gkp":
        for key, title, needs_areas, kind in GKP_ITEMS:
            if text.replace("✅ ", "") == title:
                if key in state.gkp_selected:
                    state.gkp_selected.remove(key)
                    state.gkp_areas.pop(key, None)
                    await m.answer("Убрано", reply_markup=kb_gkp(state))
                else:
                    state.gkp_selected.add(key)
                    if needs_areas:
                        state.gkp_current_key = key
                        state.gkp_areas.setdefault(key, set())
                        state.current_menu = "gkp_areas"
                        await m.answer(f"{title} — выберите районы (можно несколько):", 
                                     reply_markup=kb_areas(kind, state.gkp_areas[key]))
                    else:
                        await m.answer("Добавлено", reply_markup=kb_gkp(state))
                return
        return
    
    # --- GKP Areas Selection ---
    if state.current_menu == "gkp_areas" and state.gkp_current_key:
        key = state.gkp_current_key
        _, _, kind = GKP_META[key]
        
        if kind == "spb" and text.replace("✅ ", "") == "Весь город":
            code = "SPB_ALL"
            if code in state.gkp_areas[key]:
                state.gkp_areas[key].remove(code)
            else:
                state.gkp_areas[key].add(code)
            await m.answer("Обновлено", reply_markup=kb_areas(kind, state.gkp_areas[key]))
            return
        elif kind == "lo" and text.replace("✅ ", "") == "Вся область":
            code = "LO_ALL"
            if code in state.gkp_areas[key]:
                state.gkp_areas[key].remove(code)
            else:
                state.gkp_areas[key].add(code)
            await m.answer("Обновлено", reply_markup=kb_areas(kind, state.gkp_areas[key]))
            return
        
        clean_text = text.replace("✅ ", "")
        if kind == "spb":
            for i, name in enumerate(SPB_DISTRICTS):
                if clean_text == name:
                    code = spb_code(i)
                    if code in state.gkp_areas[key]:
                        state.gkp_areas[key].remove(code)
                    else:
                        state.gkp_areas[key].add(code)
                    await m.answer("Обновлено", reply_markup=kb_areas(kind, state.gkp_areas[key]))
                    return
        elif kind == "lo":
            for i, name in enumerate(LO_DISTRICTS):
                if clean_text == name:
                    code = lo_code(i)
                    if code in state.gkp_areas[key]:
                        state.gkp_areas[key].remove(code)
                    else:
                        state.gkp_areas[key].add(code)
                    await m.answer("Обновлено", reply_markup=kb_areas(kind, state.gkp_areas[key]))
                    return
        return
    
    # --- GOO Selection ---
    if state.current_menu == "goo":
        for key, title, needs_areas, kind in GOO_ITEMS:
            if text.replace("✅ ", "") == title:
                if key in state.goo_selected:
                    state.goo_selected.remove(key)
                    state.goo_areas.pop(key, None)
                    if key == "goo_custom":
                        state.goo_custom = ""
                    await m.answer("Убрано", reply_markup=kb_goo(state))
                else:
                    state.goo_selected.add(key)
                    if key == "goo_custom":
                        state.waiting_input = "goo_custom"
                        await m.answer("Запрос на ГОО → Произвольная информация — впишите текст сообщением.", 
                                     reply_markup=kb_cancel())
                    elif needs_areas:
                        state.goo_current_key = key
                        state.goo_areas.setdefault(key, set())
                        state.current_menu = "goo_areas"
                        await m.answer(f"{title} — выберите (можно несколько):", 
                                     reply_markup=kb_areas(kind, state.goo_areas[key]))
                    else:
                        await m.answer("Добавлено", reply_markup=kb_goo(state))
                return
        return
    
    # --- GOO Areas Selection ---
    if state.current_menu == "goo_areas" and state.goo_current_key:
        key = state.goo_current_key
        _, _, kind = GOO_META[key]
        
        if kind == "spb" and text.replace("✅ ", "") == "Весь город":
            code = "SPB_ALL"
            if code in state.goo_areas[key]:
                state.goo_areas[key].remove(code)
            else:
                state.goo_areas[key].add(code)
            await m.answer("Обновлено", reply_markup=kb_areas(kind, state.goo_areas[key]))
            return
        elif kind == "lo" and text.replace("✅ ", "") == "Вся область":
            code = "LO_ALL"
            if code in state.goo_areas[key]:
                state.goo_areas[key].remove(code)
            else:
                state.goo_areas[key].add(code)
            await m.answer("Обновлено", reply_markup=kb_areas(kind, state.goo_areas[key]))
            return
        
        clean_text = text.replace("✅ ", "")
        if kind == "spb":
            for i, name in enumerate(SPB_DISTRICTS):
                if clean_text == name:
                    code = spb_code(i)
                    if code in state.goo_areas[key]:
                        state.goo_areas[key].remove(code)
                    else:
                        state.goo_areas[key].add(code)
                    await m.answer("Обновлено", reply_markup=kb_areas(kind, state.goo_areas[key]))
                    return
        elif kind == "lo":
            for i, name in enumerate(LO_DISTRICTS):
                if clean_text == name:
                    code = lo_code(i)
                    if code in state.goo_areas[key]:
                        state.goo_areas[key].remove(code)
                    else:
                        state.goo_areas[key].add(code)
                    await m.answer("Обновлено", reply_markup=kb_areas(kind, state.goo_areas[key]))
                    return
        return
    
    # --- Call Categories ---
    if state.current_menu == "call_categories":
        for cat_key, title in CALL_CATEGORIES:
            if text.replace("✅ ", "") == title:
                state.call_cat = cat_key
                state.current_menu = "call_questions"
                state.call_questions_offset = 0
                entry = state.call_entries[state.call_active]
                selected = entry.selected.setdefault(cat_key, set())
                await m.answer(f"Допрозвон → {title}\n\nВыберите нужные вопросы.", 
                             reply_markup=kb_call_questions(cat_key, selected, 0))
                return
        return
    
    # --- Call Questions ---
    if state.current_menu == "call_questions" and state.call_cat:
        cat_key = state.call_cat
        questions = CALL_QUESTIONS.get(cat_key, [])
        entry = state.call_entries[state.call_active]
        selected = entry.selected.setdefault(cat_key, set())
        
        clean_text = text.replace("✅ ", "")
        
        # Проверяем все вопросы (не только текущую страницу)
        for idx, q in enumerate(questions):
            short_q = q[:40] + "..." if len(q) > 40 else q
            if clean_text == short_q or clean_text == q:
                if idx in selected:
                    selected.remove(idx)
                else:
                    selected.add(idx)
                await m.answer("Обновлено", reply_markup=kb_call_questions(cat_key, selected, state.call_questions_offset))
                return
        return
    
    # --- Vyezd Clothes ---
    if state.current_menu == "vyezd_clothes":
        for opt in VYEZD_CLOTHES:
            if text.replace("✅ ", "") == opt:
                state.vyezd.clothes = opt
                state.current_menu = "vyezd_take"
                await m.answer("Выезд → Взять с собой (можно несколько):", 
                             reply_markup=kb_vyezd_take(state.vyezd.take))
                return
        return
    
    # --- Vyezd Take ---
    if state.current_menu == "vyezd_take":
        for opt in VYEZD_TAKE:
            if text.replace("✅ ", "") == opt:
                if opt in state.vyezd.take:
                    state.vyezd.take.remove(opt)
                else:
                    state.vyezd.take.add(opt)
                await m.answer("Обновлено", reply_markup=kb_vyezd_take(state.vyezd.take))
                return
        return
    
    # --- Vyezd Equipment Menu ---
    if state.current_menu == "vyezd_equip":
        equip_map = {
            "🔦 Фонари": "flashlights",
            "🔋 Аккумуляторы": "batteries",
            "📢 Рации": "radios",
            "🗺️ Навигаторы": "navigators",
            "🧭 Компасы": "compasses",
        }
        clean_text = text.replace("✅ ", "")
        for label, kind in equip_map.items():
            if clean_text == label:
                state.vyezd_equip_current = kind
                state.current_menu = "vyezd_equip_qty"
                await m.answer(f"Оборудование → {EQUIP_TITLES[kind]}\nВыберите количество или введите своё:", 
                             reply_markup=kb_equip_qty(kind))
                return
        
        # Flags
        if clean_text == "🔌 Инвертор":
            flag = "inverter"
            if flag in state.vyezd.equip_flags:
                state.vyezd.equip_flags.remove(flag)
            else:
                state.vyezd.equip_flags.add(flag)
            await m.answer("Обновлено", reply_markup=kb_equip_menu(state.vyezd))
            return
        elif clean_text == "📄 Скотч":
            flag = "tape"
            if flag in state.vyezd.equip_flags:
                state.vyezd.equip_flags.remove(flag)
            else:
                state.vyezd.equip_flags.add(flag)
            await m.answer("Обновлено", reply_markup=kb_equip_menu(state.vyezd))
            return
        elif clean_text == "⚡ Power bank":
            flag = "powerbank"
            if flag in state.vyezd.equip_flags:
                state.vyezd.equip_flags.remove(flag)
            else:
                state.vyezd.equip_flags.add(flag)
            await m.answer("Обновлено", reply_markup=kb_equip_menu(state.vyezd))
            return
        return
    
    # --- Vyezd Equipment Quantity ---
    if state.current_menu == "vyezd_equip_qty" and state.vyezd_equip_current:
        kind = state.vyezd_equip_current
        
        if text == "✏️ Ввести количество":
            state.waiting_input = f"eq_custom:{kind}"
            await m.answer(f"Введите количество для «{EQUIP_TITLES[kind]}» (сообщением).", 
                         reply_markup=kb_cancel())
            return
        
        # Check presets
        if text.isdigit():
            n = int(text)
            if n in EQUIP_PRESETS[kind]:
                state.vyezd.equip_qty[kind] = n
                state.current_menu = "vyezd_equip"
                await m.answer("Установлено", reply_markup=kb_equip_menu(state.vyezd))
                return
        return
    
    # --- HQ Team ---
    if state.current_menu == "vyezd_hq_team":
        for role in HQ_TEAM_ROLES:
            if text.replace("✅ ", "") == role:
                if role in state.vyezd.hq_team:
                    state.vyezd.hq_team.remove(role)
                else:
                    state.vyezd.hq_team.add(role)
                await m.answer("Обновлено", reply_markup=kb_hq_team(state.vyezd.hq_team))
                return
        return
    
    # --- Tech Picker ---
    if state.current_menu == "tech_picker":
        for opt in TECH_OPTIONS:
            if text.replace("✅ ", "") == opt:
                if opt in state.resources.tech:
                    state.resources.tech.remove(opt)
                else:
                    state.resources.tech.add(opt)
                await m.answer("Обновлено", reply_markup=kb_tech_picker(state.resources.tech))
                return
        return

# -------------------- Main --------------------

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Вставьте реальный токен в BOT_TOKEN.")
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
