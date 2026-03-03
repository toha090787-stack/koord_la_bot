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
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8534422390:AAHm6z-poKWBCOED8s3NEmQp4tAqzJ-wxsI"

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
    hq_time: str = ""            # HH:MM
    clothes: Optional[str] = None
    take: Set[str] = field(default_factory=set)

    equip_qty: Dict[str, int] = field(default_factory=dict)  # for qty-needed items
    equip_flags: Set[str] = field(default_factory=set)       # inverter/tape/powerbank present

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
    tech: Set[str] = field(default_factory=set)

@dataclass
class UserState:
    tasks: List[Tuple[str, str]] = field(default_factory=list)  # (key, markdownV2_text)
    waiting_input: Optional[str] = None

    gkp_selected: Set[str] = field(default_factory=set)
    gkp_areas: Dict[str, Set[str]] = field(default_factory=dict)

    goo_selected: Set[str] = field(default_factory=set)
    goo_areas: Dict[str, Set[str]] = field(default_factory=dict)
    goo_custom: str = ""

    call_entries: List[CallEntry] = field(default_factory=list)
    call_active: Optional[int] = None
    call_cat: Optional[str] = None

    vyezd: VyezdState = field(default_factory=VyezdState)
    resources: ResourcesState = field(default_factory=ResourcesState)

USERS: Dict[int, UserState] = {}

def st(uid: int) -> UserState:
    if uid not in USERS:
        USERS[uid] = UserState()
    return USERS[uid]

def reset_state(state: UserState):
    state.tasks.clear()
    state.waiting_input = None
    state.gkp_selected.clear()
    state.gkp_areas.clear()
    state.goo_selected.clear()
    state.goo_areas.clear()
    state.goo_custom = ""
    state.call_entries.clear()
    state.call_active = None
    state.call_cat = None
    state.vyezd = VyezdState()
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
    # если ничего не заполнено
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
    # оборудование
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
    # карты (если что-то заполнено в блоке карт)
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
    if r.tech:
        lines.append("🧢 Запрос на технику: " + ", ".join(sorted(r.tech)))
    return md2_escape("\n".join(lines))

def upsert_resources_task(state: UserState):
    md = resources_aggregated_markdown(state)
    if md:
        upsert_task_markdown(state, "RESOURCES_AGG", md)
    else:
        remove_task_by_key(state, "RESOURCES_AGG")

# -------------------- Keyboards helpers --------------------

def kb_start():
    b = InlineKeyboardBuilder()
    b.button(text="📝 Заполнить", callback_data="start_fill")
    return b.as_markup()

def kb_main(state: Optional[UserState] = None):
    b = InlineKeyboardBuilder()
    b.button(text="📋 Задачи для инфоргов", callback_data="main_inforg")
    b.button(text="🚗 Выезд", callback_data="main_vyezd")
    b.button(text="🛠 Запрос на ресурсы", callback_data="main_resources")
    b.button(text="💾 Показать итог", callback_data="show_summary")
    b.adjust(1)
    return b.as_markup()

def kb_after_summary():
    b = InlineKeyboardBuilder()
    b.button(text="🖋 Новый запрос", callback_data="new_request")
    return b.as_markup()

def kb_cancel(cb: str):
    b = InlineKeyboardBuilder()
    b.button(text="Отмена", callback_data=cb)
    return b.as_markup()

def kb_back(cb: str):
    b = InlineKeyboardBuilder()
    b.button(text="👈 Назад", callback_data=cb)
    return b.as_markup()

# -------------------- Inforg menu --------------------

def kb_inforg(state: UserState):
    def mark(key: str) -> str:
        return "✅ " if has_task(state, key) else ""

    b = InlineKeyboardBuilder()
    b.button(text=f"{mark('CALLS_AGG')}📞 Допрозвон", callback_data="inf_call")
    b.button(text=f"{mark('AGG_GOO')}📱 Запрос на ГОО", callback_data="inf_goo")
    b.button(text=f"{mark('AGG_GKP')}☎ Запрос на ГКП", callback_data="inf_gkp")
    b.button(text=f"{mark('peleng')}📌 Запрос Пеленг", callback_data="inf_peleng")
    b.button(text=f"{mark('cam_bg')}🎥 Запрос камеры БГ", callback_data="inf_cam_bg")
    b.button(text=f"{mark('megafon')}📢 Оповещение Мегафон", callback_data="inf_megafon")
    b.button(text=f"{mark('avtonom')}🚨 Поиск автономных групп", callback_data="inf_avtonom")
    b.button(text=f"{mark('LNS')}🔔 Контроль ЛНС", callback_data="inf_LNS")
    b.button(text=f"{mark('custom')}🖌 Пользовательский запрос", callback_data="inf_custom")
    b.button(text="👈 Назад", callback_data="back_main")
    b.adjust(1)
    return b.as_markup()

# -------------------- GKP/GOO keyboards (как было) --------------------

def kb_gkp(state: UserState):
    b = InlineKeyboardBuilder()
    for key, title, _, _ in GKP_ITEMS:
        mark = "✅ " if key in state.gkp_selected else ""
        b.button(text=f"{mark}{title}", callback_data=f"gkp_toggle:{key}")
    b.button(text="👍 Готово", callback_data="gkp_done")
    b.button(text="👈 Назад", callback_data="main_inforg")
    b.adjust(1)
    return b.as_markup()

def kb_goo(state: UserState):
    b = InlineKeyboardBuilder()
    for key, title, _, _ in GOO_ITEMS:
        mark = "✅ " if key in state.goo_selected else ""
        b.button(text=f"{mark}{title}", callback_data=f"goo_toggle:{key}")
    b.button(text="👍 Готово", callback_data="goo_done")
    b.button(text="👈 Назад", callback_data="main_inforg")
    b.adjust(1)
    return b.as_markup()

def kb_area_picker(prefix: str, codes: List[str], selected: Set[str], done_cb: str, back_cb: str, cols: int = 2):
    b = InlineKeyboardBuilder()
    for c in codes:
        label = decode_area(c)
        mark = "✅ " if c in selected else ""
        b.button(text=f"{mark}{label}", callback_data=f"{prefix}:{c}")
    b.button(text="👍 Готово", callback_data=done_cb)
    b.button(text="👈 Назад", callback_data=back_cb)
    b.adjust(cols)
    return b.as_markup()

def kb_goo_areas(key: str, state: UserState):
    chosen = state.goo_areas.get(key, set())
    _title, _needs, kind = GOO_META[key]
    b = InlineKeyboardBuilder()
    if kind == "spb":
        all_code = "SPB_ALL"
        b.button(text=("✅ " if all_code in chosen else "") + "Весь город",
                 callback_data=f"goo_area:{key}:{all_code}")
        for i, name in enumerate(SPB_DISTRICTS):
            code = spb_code(i)
            b.button(text=("✅ " if code in chosen else "") + name,
                     callback_data=f"goo_area:{key}:{code}")
    elif kind == "lo":
        all_code = "LO_ALL"
        b.button(text=("✅ " if all_code in chosen else "") + "Вся область",
                 callback_data=f"goo_area:{key}:{all_code}")
        for i, name in enumerate(LO_DISTRICTS):
            code = lo_code(i)
            b.button(text=("✅ " if code in chosen else "") + name,
                     callback_data=f"goo_area:{key}:{code}")
    b.button(text="👍 Готово", callback_data=f"goo_area_done:{key}")
    b.button(text="👈 Назад", callback_data="inf_goo")
    b.adjust(2)
    return b.as_markup()

# -------------------- Call keyboards (как было) --------------------

def ensure_active_call_entry(state: UserState) -> CallEntry:
    if state.call_active is None or state.call_active < 0 or state.call_active >= len(state.call_entries):
        state.call_entries.append(CallEntry())
        state.call_active = len(state.call_entries) - 1
    return state.call_entries[state.call_active]

def kb_call_categories(state: UserState):
    b = InlineKeyboardBuilder()
    entry = None
    if state.call_active is not None and 0 <= state.call_active < len(state.call_entries):
        entry = state.call_entries[state.call_active]
    for cat_key, title in CALL_CATEGORIES:
        chosen = False
        if entry:
            chosen = bool(entry.selected.get(cat_key)) or bool(entry.manual.get(cat_key))
        b.button(text=("✅ " if chosen else "") + title, callback_data=f"call_cat:{cat_key}")
    b.button(text="➕ Добавить ещё допрозвон", callback_data="call_new_entry")
    b.button(text="👍 Готово", callback_data="call_done")
    b.button(text="👈 Назад", callback_data="main_inforg")
    b.adjust(1)
    return b.as_markup()

def build_questions_hint(cat_key: str, entry: CallEntry, limit: int = 40) -> str:
    qs = CALL_QUESTIONS.get(cat_key, [])
    selected = sorted(entry.selected.get(cat_key, set()))
    manual = entry.manual.get(cat_key, [])
    chosen: List[str] = []
    for i in selected:
        if 0 <= i < len(qs):
            chosen.append(qs[i])
    chosen.extend([t for t in manual if (t or "").strip()])
    if not chosen:
        return "Выбрано: ничего"
    shown = chosen[:limit]
    tail = "" if len(chosen) <= limit else f"\n…и ещё {len(chosen)-limit}."
    return "Выбрано:\n" + "\n".join(f"• {x}" for x in shown) + tail

def kb_call_questions(state: UserState, cat_key: str):
    b = InlineKeyboardBuilder()
    entry = state.call_entries[state.call_active]
    selected = entry.selected.setdefault(cat_key, set())
    for idx, q in enumerate(CALL_QUESTIONS.get(cat_key, [])):
        mark = "✅ " if idx in selected else ""
        b.button(text=f"{mark}{q}", callback_data=f"call_q:{cat_key}:{idx}")
    b.button(text="➕ Ручной ввод", callback_data=f"call_manual:{cat_key}")
    b.button(text="⬅️ Назад к категориям", callback_data="call_back_to_cats")
    b.adjust(1)
    return b.as_markup()

# -------------------- Vyezd keyboards --------------------

def kb_vyezd_clothes(current: Optional[str]):
    b = InlineKeyboardBuilder()
    for opt in VYEZD_CLOTHES:
        mark = "✅ " if current == opt else ""
        b.button(text=f"{mark}{opt}", callback_data=f"vyezd_clothes:{opt}")
    b.adjust(1)
    return b.as_markup()

def kb_vyezd_take(selected: Set[str]):
    b = InlineKeyboardBuilder()
    for opt in VYEZD_TAKE:
        mark = "✅ " if opt in selected else ""
        b.button(text=f"{mark}{opt}", callback_data=f"vyezd_take:{opt}")
    b.button(text="👍 Готово", callback_data="vyezd_take_done")
    b.adjust(1)
    return b.as_markup()

def kb_equip_menu(v: VyezdState):
    def mark_qty(k: str) -> str:
        return f"✅ " if k in v.equip_qty else ""
    def mark_flag(k: str) -> str:
        return f"✅ " if k in v.equip_flags else ""
    b = InlineKeyboardBuilder()
    b.button(text=f"{mark_qty('flashlights')}🔦Фонари", callback_data="eq:flashlights")
    b.button(text=f"{mark_qty('batteries')}🔋Аккумуляторы", callback_data="eq:batteries")
    b.button(text=f"{mark_qty('radios')}📢Рации", callback_data="eq:radios")
    b.button(text=f"{mark_qty('navigators')}🗺️Навигаторы", callback_data="eq:navigators")
    b.button(text=f"{mark_qty('compasses')}🧭Компасы", callback_data="eq:compasses")
    b.button(text=f"{mark_flag('inverter')}🔌Инвертор", callback_data="eq_flag:inverter")
    b.button(text=f"{mark_flag('tape')}📄Скотч", callback_data="eq_flag:tape")
    b.button(text=f"{mark_flag('powerbank')}⚡Power bank", callback_data="eq_flag:powerbank")
    b.button(text="👉 Дальше", callback_data="vyezd_to_hqteam")
    b.button(text="👈 Назад", callback_data="back_main")
    b.adjust(1)
    return b.as_markup()

def kb_equip_qty(kind: str):
    b = InlineKeyboardBuilder()
    for n in EQUIP_PRESETS[kind]:
        b.button(text=str(n), callback_data=f"eq_set:{kind}:{n}")
    b.button(text="Ввести количество", callback_data=f"eq_custom:{kind}")
    b.button(text="👈 Назад", callback_data="vyezd_equip")
    b.adjust(3)
    return b.as_markup()

def kb_hq_team(selected: Set[str]):
    b = InlineKeyboardBuilder()
    for role in HQ_TEAM_ROLES:
        mark = "✅ " if role in selected else ""
        b.button(text=f"{mark}{role}", callback_data=f"hq_team:{role}")
    b.button(text="👍 Готово", callback_data="vyezd_done")
    b.adjust(1)
    return b.as_markup()

# -------------------- Resources keyboards --------------------

def kb_resources_menu(r: ResourcesState):
    def mark_bool(v: bool) -> str:
        return "✅ " if v else ""
    def mark_val(v) -> str:
        return "✅ " if v not in (None, "", set()) else ""
    b = InlineKeyboardBuilder()
    b.button(text=f"{mark_val(r.maps_center or r.maps_limits or r.maps_grid or r.maps_phonekit)}Запрос на Карты", callback_data="res_maps")
    b.button(text=f"{mark_val(r.orient_qty)}🖨Запрос на Ориентировки", callback_data="res_orients")
    b.button(text=f"{mark_bool(r.scooters)}🛴Запрос на самокаты", callback_data="res_scooters")
    b.button(text=f"{mark_bool(r.uav)}🛸Запрос на БПЛА", callback_data="res_uav")
    b.button(text=f"{mark_bool(r.angels)}🚁Запрос на Ангелов", callback_data="res_angels")
    b.button(text=f"{mark_val(r.tech)}🧢Запрос на технику", callback_data="res_tech")
    b.button(text="👍 Готово", callback_data="res_done")
    b.button(text="👈 Назад", callback_data="back_main")
    b.adjust(1)
    return b.as_markup()

def kb_yes_no(cb_yes: str, cb_no: str, back_cb: str):
    b = InlineKeyboardBuilder()
    b.button(text="Да", callback_data=cb_yes)
    b.button(text="Нет", callback_data=cb_no)
    b.button(text="👈 Назад", callback_data=back_cb)
    b.adjust(2)
    return b.as_markup()

def kb_tech_picker(selected: Set[str]):
    b = InlineKeyboardBuilder()
    for opt in TECH_OPTIONS:
        mark = "✅ " if opt in selected else ""
        b.button(text=f"{mark}{opt}", callback_data=f"tech:{opt}")
    b.button(text="👍 Готово", callback_data="tech_done")
    b.adjust(1)
    return b.as_markup()

# -------------------- Safe edit --------------------

async def safe_edit_text(q: CallbackQuery, text: str, reply_markup=None):
    try:
        await q.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        raise

# -------------------- UI helpers --------------------

async def show_main(q: CallbackQuery):
    await safe_edit_text(q, "👆 Выберите раздел:", reply_markup=kb_main())

async def show_inforg_menu(q: CallbackQuery):
    await safe_edit_text(q, "📋 Задачи для инфоргов — выберите пункт:", reply_markup=kb_inforg(st(q.from_user.id)))

async def send_summary_separated(chat_id: int, bot: Bot, state: UserState):
    import asyncio
    
    # Выводим обычные задачи из state.tasks БЕЗ нумерации
    if state.tasks:
        await bot.send_message(chat_id, "📋 Список задач:")
        for (_k, text_md) in state.tasks:
            # Пропускаем агрегированные задачи (выезд, оборудование, штаб, ресурсы)
            if _k in ("VYEZD_AGG", "EQUIP_AGG", "HQ_TEAM_AGG", "RESOURCES_AGG"):
                continue
            await bot.send_message(chat_id, text_md, parse_mode=ParseMode.MARKDOWN_V2)
            await asyncio.sleep(0.3)
    
    # Выводим информацию о выезде отдельными сообщениями
    v = state.vyezd
    
    # 1. Основная информация о выезде (одно сообщение)
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
    
    # 2. Запрос на оборудование (отдельное сообщение)
    if any([v.equip_qty, v.equip_flags]):
        equipment_text = vyezd_equipment_markdown(state)
        if equipment_text:
            await bot.send_message(chat_id, equipment_text, parse_mode="MarkdownV2")
            await asyncio.sleep(0.5)
    
    # 3. Запрос штабной команды (отдельное сообщение)
    if v.hq_team:
        hq_team_text = vyezd_hq_team_markdown(state)
        if hq_team_text:
            await bot.send_message(chat_id, hq_team_text, parse_mode="MarkdownV2")
            await asyncio.sleep(0.5)
    
    # 4. Запросы на ресурсы (каждый запрос отдельным сообщением)
    r = state.resources
    
    # 4.1. Карты (отдельное сообщение)
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
    
    # 4.2. Ориентирование (отдельное сообщение)
    if r.orient_qty is not None:
        orient_text = md2_escape(f"🖨 Запрос на Ориентировки: {r.orient_qty} шт.")
        await bot.send_message(chat_id, orient_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    # 4.3. Самокаты (отдельное сообщение)
    if r.scooters:
        scooters_text = md2_escape("🛴 Запрос на самокаты")
        await bot.send_message(chat_id, scooters_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    # 4.4. БПЛА (отдельное сообщение)
    if r.uav:
        uav_text = md2_escape("🛸 Запрос на БПЛА")
        await bot.send_message(chat_id, uav_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    # 4.5. Ангелы (отдельное сообщение)
    if r.angels:
        angels_text = md2_escape("🚁 Запрос на Ангелов")
        await bot.send_message(chat_id, angels_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    # 4.6. Техника (отдельное сообщение)
    if r.tech:
        tech_text = md2_escape("🧢 Запрос на технику:\n" + "\n".join(f"• {t}" for t in sorted(r.tech)))
        await bot.send_message(chat_id, tech_text, parse_mode="MarkdownV2")
        await asyncio.sleep(0.5)
    
    # Если нет ни задач, ни выезда, ни ресурсов
    has_vyezd = main_info_lines or v.equip_qty or v.equip_flags or v.hq_team
    has_resources = (r.maps_center or r.maps_limits or r.maps_grid or 
                    r.maps_phonekit is not None or r.orient_qty is not None or 
                    r.scooters or r.uav or r.angels or r.tech)
    
    if not state.tasks and not has_vyezd and not has_resources:
        await bot.send_message(chat_id, "❗ Список задач пуст.")


# Словарь для перевода названий оборудования на русский
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


def vyezd_equipment_markdown(state: UserState) -> str:
    """Формирует markdown-текст для запроса оборудования"""
    v = state.vyezd
    lines = ["🎒 Запрос оборудования\n"]
    
    # Количественное оборудование
    if v.equip_qty:
        for item, qty in sorted(v.equip_qty.items()):
            # Переводим название на русский, если есть в словаре
            item_ru = EQUIPMENT_NAMES_RU.get(item, item)
            lines.append(f"• {item_ru}: {qty} шт.")
    
    # Флаговое оборудование (инвертор/изолента/павербанк)
    if v.equip_flags:
        for item in sorted(v.equip_flags):
            # Переводим название на русский, если есть в словаре
            item_ru = EQUIPMENT_NAMES_RU.get(item, item)
            lines.append(f"• {item_ru}")
    
    return md2_escape("\n".join(lines))


def vyezd_hq_team_markdown(state: UserState) -> str:
    """Формирует markdown-текст для запроса штабной команды"""
    v = state.vyezd
    if not v.hq_team:
        return ""
    
    lines = ["👥 Запрос штабной команды\n"]
    lines.extend(f"• {name}" for name in sorted(v.hq_team))
    
    return md2_escape("\n".join(lines))

# -------------------- Dispatcher --------------------

dp = Dispatcher()

@dp.message(CommandStart())
async def start(m: Message):
    await m.answer("Нажмите «Заполнить», чтобы начать", reply_markup=kb_start())

@dp.callback_query(F.data == "start_fill")
async def start_fill(q: CallbackQuery):
    reset_state(st(q.from_user.id))
    await show_main(q)

@dp.callback_query(F.data == "new_request")
async def new_request(q: CallbackQuery):
    reset_state(st(q.from_user.id))
    await safe_edit_text(q, "Нажмите «Заполнить», чтобы начать", reply_markup=kb_start())

@dp.callback_query(F.data == "back_main")
async def back_main(q: CallbackQuery):
    st(q.from_user.id).waiting_input = None
    await show_main(q)

@dp.callback_query(F.data == "main_inforg")
async def main_inforg(q: CallbackQuery):
    st(q.from_user.id).waiting_input = None
    await show_inforg_menu(q)

# -------------------- Итог --------------------

@dp.callback_query(F.data == "show_summary")
async def show_summary(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    await show_main(q)
    await send_summary_separated(q.message.chat.id, q.bot, state)
    await q.bot.send_message(q.message.chat.id, "Завершено", reply_markup=kb_after_summary())

# -------------------- Инфорги: простые --------------------

@dp.callback_query(F.data == "inf_peleng")
async def inf_peleng(q: CallbackQuery):
    added = toggle_simple_task(st(q.from_user.id), "peleng", "📌 Запрос Пеленг")
    await q.answer("Добавлено" if added else "Убрано")
    await show_inforg_menu(q)

@dp.callback_query(F.data == "inf_cam_bg")
async def inf_cam_bg(q: CallbackQuery):
    added = toggle_simple_task(st(q.from_user.id), "cam_bg", "🎥 Запрос камеры БГ")
    await q.answer("Добавлено" if added else "Убрано")
    await show_inforg_menu(q)

@dp.callback_query(F.data == "inf_avtonom")
async def inf_megafon(q: CallbackQuery):
    added = toggle_simple_task(st(q.from_user.id), "avtonom", "🚨 Поиск автономных групп")
    await q.answer("Добавлено" if added else "Убрано")
    await show_inforg_menu(q)

@dp.callback_query(F.data == "inf_LNS")
async def inf_megafon(q: CallbackQuery):
    added = toggle_simple_task(st(q.from_user.id), "LNS", "🔔 Контроль ЛНС")
    await q.answer("Добавлено" if added else "Убрано")
    await show_inforg_menu(q)  

@dp.callback_query(F.data == "inf_megafon")
async def inf_megafon(q: CallbackQuery):
    added = toggle_simple_task(st(q.from_user.id), "megafon", "📢 Оповещение Мегафон")
    await q.answer("Добавлено" if added else "Убрано")
    await show_inforg_menu(q)

# -------------------- Пользовательский запрос --------------------

@dp.callback_query(F.data == "inf_custom")
async def inf_custom(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = "custom"
    await safe_edit_text(q, "Введите пользовательский текст (сообщением)", reply_markup=kb_cancel("main_inforg"))

# -------------------- ГКП --------------------

@dp.callback_query(F.data == "inf_gkp")
async def inf_gkp(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    await safe_edit_text(q, "Запрос на ГКП — выберите нужные пункты (можно несколько):", reply_markup=kb_gkp(state))

@dp.callback_query(F.data.startswith("gkp_toggle:"))
async def gkp_toggle(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    key = q.data.split(":", 1)[1]
    title, needs_areas, kind = GKP_META[key]
    if key in state.gkp_selected:
        state.gkp_selected.remove(key)
        state.gkp_areas.pop(key, None)
        await q.message.edit_reply_markup(reply_markup=kb_gkp(state))
        await q.answer()
        return
    state.gkp_selected.add(key)
    if needs_areas:
        state.gkp_areas.setdefault(key, set())
        codes = list_area_codes(kind)
        await safe_edit_text(
            q,
            f"{title} — выберите районы (можно несколько):",
            reply_markup=kb_area_picker(
                prefix=f"gkp_area:{key}",
                codes=codes,
                selected=state.gkp_areas[key],
                done_cb=f"gkp_area_done:{key}",
                back_cb="inf_gkp",
                cols=2,
            ),
        )
        return
    await q.message.edit_reply_markup(reply_markup=kb_gkp(state))
    await q.answer()

@dp.callback_query(F.data.startswith("gkp_area:"))
async def gkp_area(q: CallbackQuery):
    state = st(q.from_user.id)
    _, key, code = q.data.split(":", 2)
    state.gkp_areas.setdefault(key, set())
    if code in state.gkp_areas[key]:
        state.gkp_areas[key].remove(code)
    else:
        state.gkp_areas[key].add(code)
    _title, _needs, kind = GKP_META[key]
    codes = list_area_codes(kind)
    await q.message.edit_reply_markup(
        reply_markup=kb_area_picker(
            prefix=f"gkp_area:{key}",
            codes=codes,
            selected=state.gkp_areas[key],
            done_cb=f"gkp_area_done:{key}",
            back_cb="inf_gkp",
            cols=2,
        )
    )
    await q.answer()

@dp.callback_query(F.data.startswith("gkp_area_done:"))
async def gkp_area_done(q: CallbackQuery):
    await safe_edit_text(q, "Запрос на ГКП — выберите нужные пункты (можно несколько):", reply_markup=kb_gkp(st(q.from_user.id)))

@dp.callback_query(F.data == "gkp_done")
async def gkp_done(q: CallbackQuery):
    state = st(q.from_user.id)
    txt_md = gkp_aggregated_markdown(state)
    if txt_md:
        upsert_task_markdown(state, "AGG_GKP", txt_md)
        await q.answer("Добавлено")
    else:
        remove_task_by_key(state, "AGG_GKP")
        await q.answer("Ничего не выбрано")
    await show_inforg_menu(q)

# -------------------- ГОО --------------------

@dp.callback_query(F.data == "inf_goo")
async def inf_goo(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    await safe_edit_text(q, "Запрос на ГОО — выберите пункты (можно несколько):", reply_markup=kb_goo(state))

@dp.callback_query(F.data.startswith("goo_toggle:"))
async def goo_toggle(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    key = q.data.split(":", 1)[1]
    title, needs_areas, _kind = GOO_META[key]
    if key in state.goo_selected:
        state.goo_selected.remove(key)
        state.goo_areas.pop(key, None)
        if key == "goo_custom":
            state.goo_custom = ""
        await q.message.edit_reply_markup(reply_markup=kb_goo(state))
        await q.answer()
        return
    state.goo_selected.add(key)
    if key == "goo_custom":
        state.waiting_input = "goo_custom"
        await safe_edit_text(q, "Запрос на ГОО → Произвольная информация — впишите текст сообщением.", reply_markup=kb_cancel("inf_goo"))
        return
    if needs_areas:
        state.goo_areas.setdefault(key, set())
        await safe_edit_text(q, f"{title} — выберите (можно несколько):", reply_markup=kb_goo_areas(key, state))
        return
    await q.message.edit_reply_markup(reply_markup=kb_goo(state))
    await q.answer()

@dp.callback_query(F.data.startswith("goo_area:"))
async def goo_area(q: CallbackQuery):
    state = st(q.from_user.id)
    _, key, code = q.data.split(":", 2)
    state.goo_areas.setdefault(key, set())
    if code in state.goo_areas[key]:
        state.goo_areas[key].remove(code)
    else:
        state.goo_areas[key].add(code)
    await q.message.edit_reply_markup(reply_markup=kb_goo_areas(key, state))
    await q.answer()

@dp.callback_query(F.data.startswith("goo_area_done:"))
async def goo_area_done(q: CallbackQuery):
    await safe_edit_text(q, "Запрос на ГОО — выберите пункты (можно несколько):", reply_markup=kb_goo(st(q.from_user.id)))

@dp.callback_query(F.data == "goo_done")
async def goo_done(q: CallbackQuery):
    state = st(q.from_user.id)
    txt_md = goo_aggregated_markdown(state)
    if txt_md:
        upsert_task_markdown(state, "AGG_GOO", txt_md)
        await q.answer("Добавлено")
    else:
        remove_task_by_key(state, "AGG_GOO")
        await q.answer("Ничего не выбрано")
    await show_inforg_menu(q)

# -------------------- Допрозвон --------------------

@dp.callback_query(F.data == "inf_call")
async def inf_call(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = "call_who"
    ensure_active_call_entry(state)
    await safe_edit_text(q, "Допрозвон\n\nКого нужно прозвонить? Напишите текст сообщением.", reply_markup=kb_cancel("main_inforg"))

@dp.callback_query(F.data == "call_new_entry")
async def call_new_entry(q: CallbackQuery):
    state = st(q.from_user.id)
    state.call_entries.append(CallEntry())
    state.call_active = len(state.call_entries) - 1
    state.call_cat = None
    state.waiting_input = "call_who"
    await safe_edit_text(q, "Новый допрозвон\n\nКого нужно прозвонить? Напишите текст сообщением.", reply_markup=kb_cancel("main_inforg"))

@dp.callback_query(F.data == "call_back_to_cats")
async def call_back_to_cats(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    await safe_edit_text(q, "Допрозвон — выберите категорию:", reply_markup=kb_call_categories(state))

@dp.callback_query(F.data.startswith("call_cat:"))
async def call_cat(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    cat_key = q.data.split(":", 1)[1]
    state.call_cat = cat_key
    entry = ensure_active_call_entry(state)
    who_line = f"Кого прозвонить: {entry.who.strip()}" if entry.who.strip() else "Кого прозвонить: (не заполнено)"
    hint = build_questions_hint(cat_key, entry)
    await safe_edit_text(
        q,
        f"Допрозвон → {CALL_META.get(cat_key, cat_key)}\n{who_line}\n\nВыберите нужные вопросы.\n\n{hint}",
        reply_markup=kb_call_questions(state, cat_key)
    )

@dp.callback_query(F.data.startswith("call_q:"))
async def call_q_toggle(q: CallbackQuery):
    state = st(q.from_user.id)
    _, cat_key, idx_s = q.data.split(":", 2)
    idx = int(idx_s)
    entry = ensure_active_call_entry(state)
    selected = entry.selected.setdefault(cat_key, set())
    if idx in selected:
        selected.remove(idx)
    else:
        selected.add(idx)
    who_line = f"Кого прозвонить: {entry.who.strip()}" if entry.who.strip() else "Кого прозвонить: (не заполнено)"
    hint = build_questions_hint(cat_key, entry)
    await safe_edit_text(
        q,
        f"Допрозвон → {CALL_META.get(cat_key, cat_key)}\n{who_line}\n\nВыберите нужные вопросы.\n\n{hint}",
        reply_markup=kb_call_questions(state, cat_key)
    )
    await q.answer()

@dp.callback_query(F.data.startswith("call_manual:"))
async def call_manual(q: CallbackQuery):
    state = st(q.from_user.id)
    state.call_cat = q.data.split(":", 1)[1]
    state.waiting_input = "call_manual"
    await safe_edit_text(q, "Введите свой вопрос/текст (сообщением).", reply_markup=kb_cancel("call_back_to_cats"))

@dp.callback_query(F.data == "call_done")
async def call_done(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    upsert_calls_task(state)
    await q.answer("Готово")
    await show_inforg_menu(q)

# -------------------- Глава «Выезд» --------------------

@dp.callback_query(F.data == "main_vyezd")
async def main_vyezd(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = "vyezd_hq_address"
    await safe_edit_text(q, "Выезд\n\nВведите адрес штаба (сообщением).", reply_markup=kb_cancel("back_main"))

@dp.callback_query(F.data == "vyezd_equip")
async def vyezd_equip(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    await safe_edit_text(q, "Выезд → Запрос оборудования", reply_markup=kb_equip_menu(state.vyezd))

@dp.callback_query(F.data.startswith("vyezd_clothes:"))
async def vyezd_clothes(q: CallbackQuery):
    state = st(q.from_user.id)
    opt = q.data.split(":", 1)[1]
    state.vyezd.clothes = opt
    await q.answer("Выбрано")
    # дальше: взять с собой
    await safe_edit_text(q, "Выезд → Взять с собой (можно несколько):", reply_markup=kb_vyezd_take(state.vyezd.take))

@dp.callback_query(F.data.startswith("vyezd_take:"))
async def vyezd_take_toggle(q: CallbackQuery):
    state = st(q.from_user.id)
    opt = q.data.split(":", 1)[1]
    if opt in state.vyezd.take:
        state.vyezd.take.remove(opt)
    else:
        state.vyezd.take.add(opt)
    await q.message.edit_reply_markup(reply_markup=kb_vyezd_take(state.vyezd.take))
    await q.answer()

@dp.callback_query(F.data == "vyezd_take_done")
async def vyezd_take_done(q: CallbackQuery):
    state = st(q.from_user.id)
    await safe_edit_text(q, "Выезд → Запрос оборудования:", reply_markup=kb_equip_menu(state.vyezd))

@dp.callback_query(F.data.startswith("eq:"))
async def eq_open(q: CallbackQuery):
    state = st(q.from_user.id)
    kind = q.data.split(":", 1)[1]
    await safe_edit_text(q, f"Оборудование → {EQUIP_TITLES[kind]}\nВыберите количество или введите своё:", reply_markup=kb_equip_qty(kind))

@dp.callback_query(F.data.startswith("eq_set:"))
async def eq_set(q: CallbackQuery):
    state = st(q.from_user.id)
    _, kind, n = q.data.split(":", 2)
    state.vyezd.equip_qty[kind] = int(n)
    await q.answer("Установлено")
    await safe_edit_text(q, "Выезд → Запрос оборудования:", reply_markup=kb_equip_menu(state.vyezd))

@dp.callback_query(F.data.startswith("eq_custom:"))
async def eq_custom(q: CallbackQuery):
    state = st(q.from_user.id)
    kind = q.data.split(":", 1)[1]
    state.waiting_input = f"eq_custom:{kind}"
    await safe_edit_text(q, f"Введите количество для «{EQUIP_TITLES[kind]}» (сообщением).", reply_markup=kb_cancel("vyezd_equip"))

@dp.callback_query(F.data.startswith("eq_flag:"))
async def eq_flag_toggle(q: CallbackQuery):
    state = st(q.from_user.id)
    flag = q.data.split(":", 1)[1]
    if flag in state.vyezd.equip_flags:
        state.vyezd.equip_flags.remove(flag)
    else:
        state.vyezd.equip_flags.add(flag)
    await q.message.edit_reply_markup(reply_markup=kb_equip_menu(state.vyezd))
    await q.answer()

@dp.callback_query(F.data == "vyezd_to_hqteam")
async def vyezd_to_hqteam(q: CallbackQuery):
    state = st(q.from_user.id)
    await safe_edit_text(q, "Выезд → Запрос штабной команды (можно несколько):", reply_markup=kb_hq_team(state.vyezd.hq_team))

@dp.callback_query(F.data.startswith("hq_team:"))
async def hq_team_toggle(q: CallbackQuery):
    state = st(q.from_user.id)
    role = q.data.split(":", 1)[1]
    if role in state.vyezd.hq_team:
        state.vyezd.hq_team.remove(role)
    else:
        state.vyezd.hq_team.add(role)
    await q.message.edit_reply_markup(reply_markup=kb_hq_team(state.vyezd.hq_team))
    await q.answer()

@dp.callback_query(F.data == "vyezd_done")
async def vyezd_done(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    upsert_vyezd_task(state)
    await q.answer("Готово")
    await show_main(q)

# -------------------- Глава «Запрос на ресурсы» --------------------

@dp.callback_query(F.data == "main_resources")
async def main_resources(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = None
    await safe_edit_text(q, "Запрос на ресурсы — выберите пункт:", reply_markup=kb_resources_menu(state.resources))

@dp.callback_query(F.data == "res_maps")
async def res_maps(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = "res_maps_center"
    await safe_edit_text(q, "Запрос на Карты\n\nВведите «Центр зоны» (сообщением).", reply_markup=kb_cancel("main_resources"))

@dp.callback_query(F.data == "res_orients")
async def res_orients(q: CallbackQuery):
    state = st(q.from_user.id)
    state.waiting_input = "res_orient_qty"
    await safe_edit_text(q, "Запрос на Ориентировки\n\nУкажите количество (сообщением).", reply_markup=kb_cancel("main_resources"))

@dp.callback_query(F.data == "res_scooters")
async def res_scooters(q: CallbackQuery):
    state = st(q.from_user.id)
    state.resources.scooters = not state.resources.scooters
    upsert_resources_task(state)
    await q.answer("Ок")
    await safe_edit_text(q, "Запрос на ресурсы — выберите пункт:", reply_markup=kb_resources_menu(state.resources))

@dp.callback_query(F.data == "res_uav")
async def res_uav(q: CallbackQuery):
    state = st(q.from_user.id)
    state.resources.uav = not state.resources.uav
    upsert_resources_task(state)
    await q.answer("Ок")
    await safe_edit_text(q, "Запрос на ресурсы — выберите пункт:", reply_markup=kb_resources_menu(state.resources))

@dp.callback_query(F.data == "res_angels")
async def res_angels(q: CallbackQuery):
    state = st(q.from_user.id)
    state.resources.angels = not state.resources.angels
    upsert_resources_task(state)
    await q.answer("Ок")
    await safe_edit_text(q, "Запрос на ресурсы — выберите пункт:", reply_markup=kb_resources_menu(state.resources))

@dp.callback_query(F.data == "res_tech")
async def res_tech(q: CallbackQuery):
    state = st(q.from_user.id)
    await safe_edit_text(q, "Запрос на технику (можно несколько):", reply_markup=kb_tech_picker(state.resources.tech))

@dp.callback_query(F.data.startswith("tech:"))
async def tech_toggle(q: CallbackQuery):
    state = st(q.from_user.id)
    opt = q.data.split(":", 1)[1]
    if opt in state.resources.tech:
        state.resources.tech.remove(opt)
    else:
        state.resources.tech.add(opt)
    await q.message.edit_reply_markup(reply_markup=kb_tech_picker(state.resources.tech))
    await q.answer()

@dp.callback_query(F.data == "tech_done")
async def tech_done(q: CallbackQuery):
    state = st(q.from_user.id)
    upsert_resources_task(state)
    await safe_edit_text(q, "Запрос на ресурсы — выберите пункт:", reply_markup=kb_resources_menu(state.resources))

@dp.callback_query(F.data == "res_done")
async def res_done(q: CallbackQuery):
    state = st(q.from_user.id)
    upsert_resources_task(state)
    await q.answer("Готово")
    await show_main(q)

# -------------------- Текстовые ответы пользователя --------------------

TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

@dp.message()
async def on_text(m: Message):
    state = st(m.from_user.id)
    if not state.waiting_input:
        return
    text = (m.text or "").strip()
    if not text:
        return

    # --- custom (в итогах без "Пользовательский запрос") ---
    if state.waiting_input == "custom":
        remove_task_by_key(state, "custom")
        add_task_plain(state, "custom", text)
        state.waiting_input = None
        await m.answer("Принято.", reply_markup=kb_main())
        return

    # --- goo_custom ---
    if state.waiting_input == "goo_custom":
        state.goo_custom = text
        state.waiting_input = None
        await m.answer("Принято. Вернуться к ГОО:", reply_markup=kb_goo(state))
        return

    # --- call_who ---
    if state.waiting_input == "call_who":
        entry = ensure_active_call_entry(state)
        entry.who = text
        state.waiting_input = None
        await m.answer("Принято. Теперь выберите категорию вопросов:", reply_markup=kb_call_categories(state))
        return

    # --- call_manual ---
    if state.waiting_input == "call_manual":
        cat_key = state.call_cat
        if not cat_key:
            state.waiting_input = None
            await m.answer("Категория не выбрана. Откройте «Допрозвон» заново.", reply_markup=kb_main())
            return
        entry = ensure_active_call_entry(state)
        entry.manual.setdefault(cat_key, []).append(text)
        state.waiting_input = None
        await m.answer("Добавлено.", reply_markup=kb_call_questions(state, cat_key))
        return

    # --- VYEZD flow ---
    if state.waiting_input == "vyezd_hq_address":
        state.vyezd.hq_address = text
        state.waiting_input = "vyezd_hq_coords"
        await m.answer("Введите координаты штаба (сообщением).", reply_markup=kb_cancel("back_main"))
        return

    if state.waiting_input == "vyezd_hq_coords":
        state.vyezd.hq_coords = text
        state.waiting_input = "vyezd_hq_time"
        await m.answer("Введите время штаба в формате HH:MM (24-часовой).", reply_markup=kb_cancel("back_main"))
        return

    if state.waiting_input == "vyezd_hq_time":
        if not TIME_RE.match(text):
            await m.answer("Неверный формат. Нужно HH:MM (например 09:30 или 18:05). Повторите ввод.")
            return
        state.vyezd.hq_time = text
        state.waiting_input = None
        await m.answer("Выберите форму одежды:", reply_markup=kb_vyezd_clothes(state.vyezd.clothes))
        return

    if state.waiting_input.startswith("eq_custom:"):
        kind = state.waiting_input.split(":", 1)[1]
        if not text.isdigit() or int(text) <= 0:
            await m.answer("Введите положительное целое число.")
            return
        state.vyezd.equip_qty[kind] = int(text)
        state.waiting_input = None
        await m.answer("Установлено.", reply_markup=kb_equip_menu(state.vyezd))
        return

    # --- RESOURCES flow ---
    if state.waiting_input == "res_maps_center":
        state.resources.maps_center = text
        state.waiting_input = "res_maps_limits"
        await m.answer("Введите «Ограничители зоны» (сообщением).", reply_markup=kb_cancel("main_resources"))
        return

    if state.waiting_input == "res_maps_limits":
        state.resources.maps_limits = text
        state.waiting_input = "res_maps_grid"
        await m.answer("Введите «Шаг сетки» (сообщением).", reply_markup=kb_cancel("main_resources"))
        return

    if state.waiting_input == "res_maps_grid":
        state.resources.maps_grid = text
        state.waiting_input = None
        await m.answer(
            "Комплект для телефонов?",
            reply_markup=kb_yes_no("res_maps_phonekit:yes", "res_maps_phonekit:no", "main_resources")
        )
        return

    if state.waiting_input == "res_orient_qty":
        if not text.isdigit() or int(text) < 0:
            await m.answer("Введите число (0 или больше).")
            return
        state.resources.orient_qty = int(text)
        state.waiting_input = None
        upsert_resources_task(state)
        await m.answer("Принято.", reply_markup=kb_resources_menu(state.resources))
        return

# --- callback for maps phonekit ---
@dp.callback_query(F.data.startswith("res_maps_phonekit:"))
async def res_maps_phonekit(q: CallbackQuery):
    state = st(q.from_user.id)
    val = q.data.split(":", 1)[1]
    state.resources.maps_phonekit = True if val == "yes" else False
    upsert_resources_task(state)
    await q.answer("Ок")
    await safe_edit_text(q, "Запрос на ресурсы — выберите пункт:", reply_markup=kb_resources_menu(state.resources))

# ----------- main -----------

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Вставьте реальный токен в BOT_TOKEN.")
    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
