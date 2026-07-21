# TDIU Olim Fondi — Sessiyalar va Hujjat Yuborish Qo'llanmasi

Ushbu qo'llanma botga qo'shilgan yangi **Sessiyalar (Kampaniyalar)** va **Xavfsiz Hujjat Yuborish** tizimlarini boshqarish uchun mo'ljallangan.

---

## 1. 📅 Sessiyalarni yaratish va boshqarish

*   **Maqsad:** Yil davomida xohlagancha qabul (sessiya) kampaniyalarini tashkil etish va har bir qabul hujjatlarini alohida arxivlash.
*   **Yo'riqnoma:**
    1. Admin panelga kirib, **«📅 Sessiyalar»** tugmasini bosing.
    2. Yangi sessiya ochish uchun **«➕ Yangi sessiya yaratish»** tugmasini bosing va unga nom bering (masalan: *2026/2027 Bahorgi*).
    3. Ro'yxatdan kerakli sessiyani tanlab, **«🟢 Faollashtirish»** tugmasini bosing. Shunda botdagi barcha yangi keladigan arizalar faqat shu faol sessiyaga bog'lanadi.

> ⚠️ **Muhim:** Botda bir vaqtning o'zida faqat **bitta** sessiya faol bo'lishi mumkin. Yangisi faollashtirilganda, oldingisi avtomatik tarzda nofaol holatga o'tadi.

---

## 2. 📋 Arizalarni sessiya bo'yicha ko'rish

*   **Maqsad:** Kerakli sessiyadagi arizalarni filtrlash va boshqarish.
*   **Yo'riqnoma:**
    1. Admin panelda **«📋 Arizalar»** tugmasini bosing.
    2. Tizim sizdan arizalarni ko'rmoqchi bo'lgan sessiyani tanlashni so'raydi. Kerakli sessiyani bosing.
    3. Sessiya tanlanganidan so'ng, kutilayotgan, tasdiqlangan va rad etilgan arizalar faqat shu sessiya bo'yicha filtrlanadi.

---

## 3. 👥 Foydalanuvchilarni izlash va ruxsat berish

*   **Maqsad:** Ariza to'ldirmagan, lekin hujjat yuborish huquqiga ega foydalanuvchilarni tizimga (hujjat yuborish ro'yxatiga) qo'shish.
*   **Yo'riqnoma:**
    1. Admin panelda **«👥 Foydalanuvchilar»** bo'limiga kiring.
    2. Ro'yxatdan kerakli foydalanuvchini toping (yoki sahifalar orqali o'ting).
    3. Foydalanuvchini tanlaganingizdan so'ng, uning barcha shaxsiy ma'lumotlari ekranga chiqadi.
    4. **«✅ Ruxsat berish»** tugmasini bosib, foydalanuvchiga ruxsat bering.
    5. Agar ruxsatni bekor qilmoqchi bo'lsangiz, **«⏳ Ruxsatni o'chirish»** tugmasini bosing.

---

## 4. 📂 Hujjat yuborish bo'limi va xavfsizlik cheklovlari

*   **Maqsad:** Firibgarlik va xatoliklarning oldini olish.
*   **Xususiyatlar:**
    *   **Maxfiylik:** Botning asosiy menyusidagi **«📂 Hujjat yuborish»** tugmasi faqat ruxsat berilgan (`registered = TRUE` bo'lgan) talabalargagina ko'rinadi. Oddiy arizachilar yoki begonalarga bu tugma ko'rinmaydi.
    *   **Identifikatsiya tekshiruvi:** Talaba hujjat yuborish ro'yxatidan faqat **o'zining Ism-Familiyasini** tanlashi shart. Agar u boshqa birovning ismini tanlasa, bot unga: **«❌ Bu siz emassiz! Iltimos, faqat o'z ismingizni tanlang.»** degan ogohlantirishni chiqaradi va hujjat yuborishga yo'l qo'ymaydi.
