from aiogram.dispatcher.filters.state import StatesGroup, State


class RegisterStates(StatesGroup):
    full_name = State()
    phone = State()
    otm = State()
    course = State()


class AppealStates(StatesGroup):
    subject = State()
    writing = State()


class SendFile(StatesGroup):
    student_list = State()
    theme = State()
    send_file = State()


class CabinetStates(StatesGroup):
    edit_name = State()
    edit_phone = State()
    edit_otm = State()
    edit_course = State()


class AdminEventStates(StatesGroup):
    name = State()
    date = State()
    time = State()
    location = State()
    description = State()
    confirm = State()


class AdminBroadcastStates(StatesGroup):
    subject = State()
    text = State()
    confirm = State()


class AdminChatStates(StatesGroup):
    chatting = State()


class AdminAppealReplyStates(StatesGroup):
    reply = State()


class ArizaStates(StatesGroup):
    # Shaxsiy ma'lumotlar
    fish = State()
    tugilgan_sana = State()
    millat = State()
    manzil = State()
    telefon = State()
    email = State()
    # Ta'lim haqida
    otm = State()
    talim_shakli = State()
    yonalish = State()
    kurs = State()
    ilmiy_tadqiqot = State()
    tadqiqot_info = State()
    konferensiya = State()
    maqola = State()
    # Moliya
    oldin_grant = State()
    grant_info = State()
    kontrakt_sum = State()
    # Oila
    oila_soni = State()
    ota_info = State()
    ona_info = State()
    aka_opa_info = State()
    # Yangi savollar (Transkript, Passport, CV, Imtiyoz)
    transkript = State()
    passport_oldi = State()
    passport_orqa = State()
    cv = State()
    imtiyozi = State()
    oqish_joyi = State()
    # Motivatsion xat
    motivatsion_xat = State()
    # Tasdiqlash
    confirm = State()


class AdminArizaStates(StatesGroup):
    reject_reason = State()
    search = State()


class AdminSessionStates(StatesGroup):
    new_session_name = State()


class AdminCMSStates(StatesGroup):
    # Mavjud bo'limni tahrirlash
    edit_title_uz = State()
    edit_title_ru = State()
    edit_text_uz = State()
    edit_text_ru = State()
    edit_image = State()
    # Yangi bo'lim qo'shish
    add_key = State()
    add_title_uz = State()
    add_title_ru = State()
    add_text_uz = State()
    add_text_ru = State()
    add_image = State()
