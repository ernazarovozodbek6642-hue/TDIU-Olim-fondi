# TDIU Olim Fondi Telegram Bot — To'liq Qo'llanma

---

## FOYDALANUVCHI UCHUN

### 1. Botni ishga tushirish

Botni birinchi marta ochasiz yoki `/start` buyrug'ini yuborsiz. Bot til tanlashni so'raydi:
- **O'zbek tili** → `🇺🇿 O'zbek`
- **Rus tili** → `🇷🇺 Русский`

Tilni tanlangandan so'ng Asosiy Menyu ochiladi.

---

### 2. Asosiy Menyu tugmalari

| Tugma | Nima qiladi |
|-------|------------|
| 👤 Rahbariyat | Fond rahbariyati haqida ma'lumot |
| ✍️ Murojaat yuborish | Anonim murojaat yuborish |
| 📂 Hujjat yuborish | Hujjat/rasm adminlarga yuborish |
| 📊 Statistika | Fond statistikasi |
| 🏛 Olim fondi haqida | Fond haqida ma'lumot bo'limlari |
| 🗂 Shaxsiy kabinet | Profilingiz va ariza holati |
| 📬 2026/2027 uchun hujjat topshirish | Grant uchun ariza berish |
| 🇺🇿 Tilni o'zgartish 🇷🇺 | Tilni almashtirish |

---

### 3. 👤 Rahbariyat

Fond rahbariyati bo'limlari ko'rsatiladi. Bo'limni tanlang — ma'lumot (matn va/yoki rasm) chiqadi. `⬅️ Ortga` tugmasi orqali orqaga qaytiladi.

---

### 4. ✍️ Murojaat yuborish

1. Tugmani bosing
2. Murojaatingizni matn sifatida yozing
3. "To'g'ri" deb tasdiqlang
4. Murojaat **anonim** tarzda adminlarga yuboriladi

> Murojaat matni adminlarga ko'rinadi, lekin ismingiz ko'rsatilmaydi.

---

### 5. 📂 Hujjat yuborish

1. Tugmani bosing
2. Ro'yxatdan ismingizni toping va tanlang (sahifalar orqali ko'rish mumkin)
3. Hujjat mavzusini yozing (masalan: "Diplom olish uchun so'rovnoma")
4. Hujjat yoki rasmni yuboring
5. Tasdiqlang — hujjat adminlarga yuboriladi

> Hujjat fayllar va rasmlar qabul qilinadi.

---

### 6. 📊 Statistika

Admin tomonidan qo'shilgan statistika bo'limlari ko'rsatiladi. Bo'limni tanlang, matn va rasm bilan ma'lumot chiqadi.

---

### 7. 🏛 Olim fondi haqida

Fond haqida turli bo'limlar: tarix, maqsad, faoliyat va boshqalar. Har bir bo'lim matn va rasm bilan to'ldirilgan.

---

### 8. 📬 Grant uchun ariza (2026/2027)

Bu to'liq anketa bo'lib, quyidagi ma'lumotlar so'raladi:

**Bo'lim 1 — Shaxsiy ma'lumotlar:**
- F.I.Sh (Familiya Ism Sharif)
- Tug'ilgan sana (format: `01.01.2000`)
- Millat
- Doimiy ro'yxat manzili
- Telefon raqami (format: `+998901234567`)

**Bo'lim 2 — Ta'lim ma'lumotlari:**
- Ta'lim shakli: Kunduzgi / Sirtqi / Masofaviy
- Kurs: 1—4 yoki Magistr
- O'qish GPA si (o'rtacha ball)

**Bo'lim 3 — Ilmiy faoliyat:**
- Ilmiy tadqiqot ishlari bor-yo'qligi (Ha/Yo'q)
- Konferensiyalarda ishtirok (Ha/Yo'q)
- Nashr etilgan maqolalar (Ha/Yo'q)

**Bo'lim 4 — Qo'shimcha:**
- Oldin grant olganmisiz (Ha/Yo'q)
- Qo'shimcha ma'lumotlar (ixtiyoriy)

Formani to'ldirib **Yuborish** tugmasini bosganingizdan so'ng:
- Ariza adminlarga Word (.docx) fayl ko'rinishida yuboriladi
- Sizga ariza holati ko'rsatiladi

**Ariza holatlari:**
- ⏳ Ko'rib chiqilmoqda — admin hali qaror qilmagan
- ✅ Tasdiqlangan — arizangiz qabul qilindi
- ❌ Rad etilgan — sabab ko'rsatiladi, qayta yuborish mumkin

> Arizani to'xtatish uchun istalgan vaqt `❌ Arizani to'xtatish` tugmasini bosing.

**Yuborilgan arizani bekor qilish:** Ariza ko'rib chiqilayotgan bo'lsa, `🗑 Arizani bekor qilish` tugmasi orqali uni qaytarib olishingiz mumkin (faqat "pending" holatida).

---

### 9. 🗂 Shaxsiy kabinet

- Profilingiz ma'lumotlari (ism, til, ro'yxatdan o'tgan sana)
- Arizangiz holati ko'rsatiladi
- Ariza bo'lmasa — yangi ariza boshlash imkoniyati

---

### 10. Tilni o'zgartirish

`🇺🇿 Tilni o'zgartish 🇷🇺` tugmasini bosib tilni almashtirasiz. Barcha matnlar yangi tilda ko'rsatiladi.

---
---

## ADMIN UCHUN

> Admin huquqlari faqat `data/config.py` dagi `ADMINS` ro'yxatidagi foydalanuvchi ID lariga berilgan.

### 1. Admin panelga kirish

`/admin` buyrug'ini yuboring. Admin panel inline tugmalar bilan chiqadi.

---

### 2. Admin panel bo'limlari

| Bo'lim | Nima qiladi |
|--------|------------|
| 📋 Arizalar | Grant arizalarini ko'rish va ko'rib chiqish |
| 📬 Murojaatlar | Foydalanuvchi murojaatlarini ko'rish |
| 📁 Hujjatlar | Yuborilgan hujjatlarni yuklab olish |
| 📅 Tadbirlar | Tadbirlar yaratish va boshqarish |
| 🖊 CMS | Sayt bo'limlarini boshqarish |
| 👥 Foydalanuvchilar | Ro'yxatdan o'tganlar soni va statistika |

---

### 3. 📋 Arizalar boshqaruvi

**Ko'rish:**
- `⏳ Kutilayotganlar` — yangi arizalar
- `✅ Tasdiqlangan` — qabul qilinganlar
- `❌ Rad etilgan` — rad etilganlar

**Ariza tafsilotini ko'rish:**
Ro'yxatdan ariza nomini bosing — to'liq anketa ma'lumotlari chiqadi (F.I.Sh, telefon, GPA, ilmiy faoliyat va boshqalar). Word fayl ham yuboriladi.

**Qaror qabul qilish:**
- `✅ Tasdiqlash` — arizani qabul qilish. Talabaga avtomatik xabar ketadi.
- `❌ Rad etish` — sabab yozing, so'ng yuborish. Talabaga sabab bilan birga xabar ketadi.

**Qidiruv:** F.I.Sh bo'yicha qidirish mumkin — 🔍 Qidirish tugmasi orqali.

---

### 4. 📬 Murojaatlar

Foydalanuvchilardan kelgan anonim murojaatlar ro'yxati. Har bir murojaat uchun yuboruvchi ID si ko'rsatiladi (ism ko'rsatilmaydi).

---

### 5. 📁 Hujjatlar

Talabalar yuborgan hujjatlar. Ikkita rejim:
- **Talaba bo'yicha** — bitta talabaning barcha hujjatlari
- **Mavzu bo'yicha** — ma'lum mavzudagi barcha hujjatlar

ZIP fayl sifatida yuklab olish mumkin.

---

### 6. 📅 Tadbirlar boshqaruvi

- Yangi tadbir yaratish: sarlavha, sana, tavsif kiriting
- Tadbir haqida barcha foydalanuvchilarga bildirishnoma yuboriladi (guruhlar va kanallar ham)
- Tadbirni o'chirish mumkin

---

### 7. 🖊 CMS — Kontent boshqarish

Bu eng kuchli bo'lim. Bot ichidagi barcha ma'lumot bo'limlari shu yerdan boshqariladi: **Rahbariyat**, **Statistika**, **Fond haqida**.

#### Bo'limlar tuzilishi

Bot 3 ta asosiy bo'limga ega:
- `about` — "🏛 Olim fondi haqida"
- `stat` — "📊 Statistika"
- `mgmt` — "👤 Rahbariyat"

Har bir bo'lim ichida **sub-bo'limlar** (bolalar) bo'lishi mumkin. Sub-bo'limlar ham o'z navbatida sub-bo'limlarga ega bo'lishi mumkin.

#### Bo'lim qo'shish

1. CMS ga kiring
2. Kerakli asosiy bo'limni oching
3. `➕ Sub-bo'lim qo'shish` tugmasini bosing
4. Quyidagilarni kiriting:
   - **Key** — noyob identifikator (masalan: `about:tarix`). Ota bo'lim key si `:` bilan boshlanishi shart.
   - **Sarlavha (UZ)** — O'zbek tilida sarlavha
   - **Sarlavha (RU)** — Rus tilida sarlavha
   - **Matn (UZ)** — O'zbek tilida mazmun
   - **Matn (RU)** — Rus tilida mazmun
   - **Rasm** — ixtiyoriy, Telegram orqali yuboriladi

#### Bo'limni tahrirlash

Bo'limni ochasiz → `✏️ Tahrirlash` tugmasi. Quyidagilarni o'zgartirish mumkin:
- `✏️ Matn (UZ)` — o'zbek matni
- `✏️ Matn (RU)` — rus matni
- `🖼 Rasm yuklash` — yangi rasm yuklash
- `✅ Ko'rsatish / 🚫 Yashirish` — bo'limni faol/nofaol qilish
- `⬆️` / `⬇️` — bo'limni ro'yxatda yuqori/pastga siljitish
- `🗑 O'chirish` — bo'limni va barcha sub-bo'limlarini o'chirish

#### Rasm yuklash tartibi

1. `🖼 Rasm yuklash` tugmasini bosing
2. Rasmni Telegram orqali yuboring
3. Rasm avtomatik ravishda saqlash kanaliga yuboriladi va bo'limga biriktiriladi
4. Foydalanuvchilarga ko'rsatilganda rasm avtomatik chiqadi

> Rasm saqlash kanali: `STORAGE_CHANNEL`. Agar bot token o'zgarsa ham rasmlar o'chib ketmaydi — kanal ID va message ID orqali qayta yuklanadi.

#### Bo'limni yashirish

`🚫 Yashirish` tugmasini bosing — bo'lim foydalanuvchilarga ko'rinmay qoladi, lekin ma'lumotlar saqlanib qoladi. Qayta `✅ Ko'rsatish` bilan ochiladi.

#### Tartibni o'zgartirish

Har bir sub-bo'lim yonida `⬆️` va `⬇️` tugmalari bor. Shu tugmalar orqali bo'limlar tartibini o'zgartirasiz.

---

### 8. Muhim eslatmalar

**Rahbariyat bo'limida bitta shaxs:**
Agar bir bo'limda faqat bitta sub-bo'lim bo'lsa, bot avtomatik o'sha shaxsni ko'rsatadi (ro'yxat chiqmaydi). "Ortga" tugmasi ota bo'limga emas, bobo bo'limga qaytadi — bu to'g'ri ishlash.

**Bot qayta ishga tushirilganda:**
Eski inline tugmalar (bot to'xtab turgan vaqtda bosilgan) `InvalidQueryID` xatosi beradi — bu normal. Bot ularni e'tiborsiz qoldiradi va davom etadi.

**Til o'zgarishi:**
Foydalanuvchi tilni o'zgartirsa, barcha keyingi xabarlar yangi tilda keladi.

---

### 9. Texnik ma'lumotlar (IT uchun)

| Parametr | Qiymat |
|----------|--------|
| Framework | aiogram 2.25.2 |
| Ma'lumotlar bazasi | PostgreSQL (Neon) |
| Rasm saqlash | Telegram kanal (STORAGE_CHANNEL) |
| Rasm formati | `file_id\|channel_id\|message_id` |
| Admin ID lar | `data/config.py` — `ADMINS` ro'yxati |
| Bot token | `data/config.py` — `BOT_TOKEN` |

**Botni ishga tushirish:**
```bash
python app.py
```

**Muhit o'zgaruvchilari (`.env`):**
```
BOT_TOKEN=...
DATABASE_URL=postgresql://...
STORAGE_CHANNEL=-100...
```
