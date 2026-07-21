from typing import Union
import asyncpg
import asyncio
from asyncpg import Connection
from asyncpg.pool import Pool
from data import config


class Database:
    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            database=config.DB_NAME,
            min_size=1,
            max_size=5,
            max_inactive_connection_lifetime=300,  # Neon idle connection fix
        )

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(self, command, *args, fetch=False, fetchval=False, fetchrow=False, execute=False):
        last_exc = None
        for attempt in range(3):
            try:
                async with self.pool.acquire() as connection:
                    connection: Connection
                    async with connection.transaction():
                        if execute:
                            result = await connection.execute(command, *args)
                        elif fetch:
                            result = await connection.fetch(command, *args)
                        elif fetchval:
                            result = await connection.fetchval(command, *args)
                        elif fetchrow:
                            result = await connection.fetchrow(command, *args)
                        else:
                            result = None
                    return result
            except (asyncpg.exceptions.ConnectionDoesNotExistError,
                    asyncpg.exceptions.InterfaceError) as e:
                last_exc = e
                if attempt < 2:
                    await asyncio.sleep(0.5)
                    continue
                raise last_exc

    # ─── USERS ───
    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            username VARCHAR(255),
            date_time TIMESTAMP,
            language VARCHAR(10),
            real_name VARCHAR(255),
            phone VARCHAR(20),
            otm VARCHAR(255),
            course VARCHAR(50),
            registered BOOLEAN DEFAULT FALSE
        );
        """
        await self.execute(sql, execute=True)
        for col, coltype in [
            ("real_name", "VARCHAR(255)"),
            ("phone", "VARCHAR(20)"),
            ("otm", "VARCHAR(255)"),
            ("course", "VARCHAR(50)"),
            ("registered", "BOOLEAN DEFAULT FALSE")
        ]:
            try:
                await self.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {coltype}", execute=True)
            except Exception:
                pass

    async def add_user(self, id: str, full_name: str, username: str, date_time, language: str):
        sql = """
        INSERT INTO users (id, full_name, username, date_time, language, registered)
        VALUES ($1, $2, $3, $4, $5, FALSE)
        ON CONFLICT (id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            username = EXCLUDED.username,
            date_time = EXCLUDED.date_time,
            language = EXCLUDED.language
        RETURNING *;
        """
        return await self.execute(sql, id, full_name, username, date_time, language, fetchrow=True)

    async def update_user_registration(self, user_id: str, real_name: str, phone: str, otm: str, course: str):
        sql = """
        UPDATE users SET real_name=$2, phone=$3, otm=$4, course=$5, registered=TRUE WHERE id=$1
        RETURNING *;
        """
        return await self.execute(sql, user_id, real_name, phone, otm, course, fetchrow=True)

    async def update_user_field(self, user_id: str, field: str, value: str):
        allowed = {'real_name', 'phone', 'otm', 'course'}
        if field not in allowed:
            raise ValueError(f"Invalid field: {field}")
        sql = f"UPDATE users SET {field}=$2 WHERE id=$1 RETURNING *;"
        return await self.execute(sql, user_id, value, fetchrow=True)

    async def select_user(self, user_id):
        sql = "SELECT * FROM users WHERE id = $1"
        return await self.execute(sql, user_id, fetchrow=True)

    async def select_all_users(self):
        sql = "SELECT * FROM users ORDER BY date_time DESC"
        return await self.execute(sql, fetch=True)

    async def select_registered_users(self):
        sql = "SELECT * FROM users WHERE registered = TRUE"
        return await self.execute(sql, fetch=True)

    async def count_users(self):
        sql = "SELECT COUNT(*) FROM users"
        return await self.execute(sql, fetchval=True)

    async def count_registered_users(self):
        sql = "SELECT COUNT(*) FROM users WHERE registered = TRUE"
        return await self.execute(sql, fetchval=True)

    async def get_registered_names(self) -> list:
        """registered=True bo'lgan foydalanuvchilarning real_name larini qaytaradi"""
        sql = "SELECT real_name FROM users WHERE registered = TRUE AND real_name IS NOT NULL AND real_name != '' ORDER BY real_name"
        rows = await self.execute(sql, fetch=True)
        return [row['real_name'] for row in rows] if rows else []

    # ─── APPEALS ───
    async def create_table_appeals(self):
        sql = """
        CREATE TABLE IF NOT EXISTS appeals (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR NOT NULL REFERENCES users(id),
            subject VARCHAR(255),
            message TEXT NOT NULL,
            created_at TIMESTAMP,
            answered BOOLEAN DEFAULT FALSE
        );
        """
        await self.execute(sql, execute=True)
        for col, coltype in [
            ("subject", "VARCHAR(255)"),
            ("answered", "BOOLEAN DEFAULT FALSE")
        ]:
            try:
                await self.execute(f"ALTER TABLE appeals ADD COLUMN IF NOT EXISTS {col} {coltype}", execute=True)
            except Exception:
                pass

    async def add_appeal(self, user_id: str, message: str, created_at, subject: str = ''):
        sql = """
        INSERT INTO appeals (user_id, subject, message, created_at, answered)
        VALUES ($1, $2, $3, $4, FALSE)
        RETURNING *;
        """
        return await self.execute(sql, user_id, subject, message, created_at, fetchrow=True)

    async def get_unanswered_appeals(self):
        sql = """
        SELECT a.*, u.real_name, u.full_name, u.username
        FROM appeals a
        JOIN users u ON a.user_id = u.id
        WHERE a.answered = FALSE
        ORDER BY a.created_at DESC;
        """
        return await self.execute(sql, fetch=True)

    async def get_appeal_by_id(self, appeal_id: int):
        sql = """
        SELECT a.*, u.real_name, u.full_name, u.username, u.language
        FROM appeals a
        JOIN users u ON a.user_id = u.id
        WHERE a.id = $1;
        """
        return await self.execute(sql, appeal_id, fetchrow=True)

    async def mark_appeal_answered(self, appeal_id: int):
        sql = "UPDATE appeals SET answered=TRUE WHERE id=$1"
        await self.execute(sql, appeal_id, execute=True)

    async def select_user_appeals(self, user_id: str):
        sql = "SELECT * FROM appeals WHERE user_id = $1 ORDER BY created_at DESC"
        return await self.execute(sql, user_id, fetch=True)

    async def select_all_appeals(self):
        sql = """
        SELECT a.id, a.subject, a.message, a.created_at, a.answered,
               u.full_name, u.language
        FROM appeals a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC;
        """
        return await self.execute(sql, fetch=True)

    # ─── ANSWERS ───
    async def create_table_answers(self):
        sql = """
        CREATE TABLE IF NOT EXISTS answers (
            id SERIAL PRIMARY KEY,
            appeal_id INT NOT NULL REFERENCES appeals(id),
            answer_text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    async def add_answer(self, appeal_id: int, answer_text: str, created_at):
        sql = """
        INSERT INTO answers (appeal_id, answer_text, created_at)
        VALUES ($1, $2, $3)
        RETURNING *;
        """
        return await self.execute(sql, appeal_id, answer_text, created_at, fetchrow=True)

    async def select_appeal_answers(self, appeal_id: int):
        sql = "SELECT * FROM answers WHERE appeal_id = $1 ORDER BY created_at ASC"
        return await self.execute(sql, appeal_id, fetch=True)

    async def select_all_appeals_with_answers(self):
        sql = """
        SELECT a.id AS appeal_id, a.subject, a.message,
               a.created_at AS appeal_created,
               u.full_name, u.language,
               ans.answer_text, ans.created_at AS answer_created
        FROM appeals a
        LEFT JOIN answers ans ON ans.appeal_id = a.id
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC, ans.created_at ASC;
        """
        return await self.execute(sql, fetch=True)

    # ─── DOCUMENTS ───
    async def create_table_documents(self):
        sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR NOT NULL REFERENCES users(id),
            theme TEXT,
            file_id TEXT NOT NULL,
            file_type VARCHAR(20) NOT NULL,
            channel_message_id INTEGER,
            created_at TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)
        try:
            await self.execute(
                "ALTER TABLE documents ADD COLUMN IF NOT EXISTS channel_message_id INTEGER",
                execute=True
            )
        except Exception:
            pass

    async def add_document(self, user_id: str, theme: str, file_id: str, file_type: str,
                           created_at, channel_message_id: int = None):
        sql = """
        INSERT INTO documents (user_id, theme, file_id, file_type, channel_message_id, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *;
        """
        return await self.execute(sql, user_id, theme, file_id, file_type, channel_message_id, created_at, fetchrow=True)

    async def select_user_documents(self, user_id: str):
        sql = "SELECT * FROM documents WHERE user_id = $1 ORDER BY created_at DESC"
        return await self.execute(sql, user_id, fetch=True)

    async def select_all_documents(self):
        sql = """
        SELECT d.id, d.theme, d.file_id, d.file_type, d.channel_message_id, d.created_at,
               u.full_name, u.real_name, u.username, u.language, u.id AS user_id
        FROM documents d
        JOIN users u ON d.user_id = u.id
        ORDER BY d.created_at DESC;
        """
        return await self.execute(sql, fetch=True)

    async def get_document_by_id(self, doc_id: int):
        sql = """
        SELECT d.*, u.real_name, u.full_name
        FROM documents d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = $1;
        """
        return await self.execute(sql, doc_id, fetchrow=True)

    async def get_users_with_documents(self):
        sql = """
        SELECT DISTINCT u.id, u.real_name, u.full_name
        FROM documents d
        JOIN users u ON d.user_id = u.id
        ORDER BY u.real_name;
        """
        return await self.execute(sql, fetch=True)

    # ─── EVENTS ───
    async def create_table_events(self):
        sql = """
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            event_date VARCHAR(20) NOT NULL,
            event_time VARCHAR(10) NOT NULL,
            location TEXT,
            location_lat FLOAT,
            location_lon FLOAT,
            description TEXT,
            created_at TIMESTAMP,
            remind_1day BOOLEAN DEFAULT FALSE,
            remind_2hours BOOLEAN DEFAULT FALSE,
            remind_1hour BOOLEAN DEFAULT FALSE,
            remind_10min BOOLEAN DEFAULT FALSE
        );
        """
        await self.execute(sql, execute=True)

    async def add_event(self, name: str, event_date: str, event_time: str,
                        location: str, description: str, created_at,
                        location_lat: float = None, location_lon: float = None):
        sql = """
        INSERT INTO events (name, event_date, event_time, location, location_lat, location_lon,
                            description, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *;
        """
        return await self.execute(sql, name, event_date, event_time, location,
                                  location_lat, location_lon, description, created_at, fetchrow=True)

    async def update_event(self, event_id: int, name: str, event_date: str, event_time: str,
                           location: str, description: str,
                           location_lat: float = None, location_lon: float = None):
        sql = """
        UPDATE events SET name=$1, event_date=$2, event_time=$3,
                          location=$4, description=$5, location_lat=$6, location_lon=$7
        WHERE id=$8 RETURNING *;
        """
        return await self.execute(sql, name, event_date, event_time, location,
                                  description, location_lat, location_lon, event_id, fetchrow=True)

    async def get_all_events(self):
        sql = "SELECT * FROM events ORDER BY event_date, event_time"
        return await self.execute(sql, fetch=True)

    async def get_event_by_id(self, event_id: int):
        sql = "SELECT * FROM events WHERE id = $1"
        return await self.execute(sql, event_id, fetchrow=True)

    async def delete_event(self, event_id: int):
        sql = "DELETE FROM events WHERE id = $1"
        await self.execute(sql, event_id, execute=True)

    async def update_event_reminder(self, event_id: int, field: str):
        allowed = {'remind_1day', 'remind_2hours', 'remind_1hour', 'remind_10min'}
        if field not in allowed:
            return
        sql = f"UPDATE events SET {field}=TRUE WHERE id=$1"
        await self.execute(sql, event_id, execute=True)

    async def count_appeals(self):
        sql = "SELECT COUNT(*) FROM appeals"
        return await self.execute(sql, fetchval=True)

    async def count_documents(self):
        sql = "SELECT COUNT(*) FROM documents"
        return await self.execute(sql, fetchval=True)

    # ─── SESSIDALAR (SESSIONS) ───
    async def create_table_sessions(self):
        sql = """
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def seed_default_session(self):
        count = await self.execute("SELECT COUNT(*) FROM sessions", fetchval=True)
        if count and count > 0:
            return
        import datetime
        sql = "INSERT INTO sessions (name, is_active, created_at) VALUES ($1, TRUE, $2) RETURNING *;"
        default_sess = await self.execute(sql, "2026/2027 Kuzgi", datetime.datetime.now(), fetchrow=True)
        if default_sess:
            await self.execute("UPDATE arizalar SET session_id=$1 WHERE session_id IS NULL", default_sess['id'], execute=True)

    async def create_session(self, name: str):
        import datetime
        sql = "INSERT INTO sessions (name, is_active, created_at) VALUES ($1, FALSE, $2) ON CONFLICT (name) DO NOTHING RETURNING *;"
        return await self.execute(sql, name, datetime.datetime.now(), fetchrow=True)

    async def activate_session(self, session_id: int):
        await self.execute("UPDATE sessions SET is_active=FALSE", execute=True)
        sql = "UPDATE sessions SET is_active=TRUE WHERE id=$1 RETURNING *;"
        return await self.execute(sql, session_id, fetchrow=True)

    async def get_active_session(self):
        sql = "SELECT * FROM sessions WHERE is_active=TRUE LIMIT 1;"
        active = await self.execute(sql, fetchrow=True)
        if not active:
            sql_first = "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 1;"
            active = await self.execute(sql_first, fetchrow=True)
        return active

    async def get_all_sessions(self):
        sql = "SELECT * FROM sessions ORDER BY created_at DESC;"
        return await self.execute(sql, fetch=True)

    async def get_session_by_id(self, session_id: int):
        sql = "SELECT * FROM sessions WHERE id=$1;"
        return await self.execute(sql, session_id, fetchrow=True)

    # ─── ARIZALAR ───
    async def create_table_arizalar(self):
        sql = """
        CREATE TABLE IF NOT EXISTS arizalar (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR NOT NULL REFERENCES users(id),
            status VARCHAR(20) DEFAULT 'pending',
            fish VARCHAR(255),
            tugilgan_sana VARCHAR(20),
            millat VARCHAR(100),
            manzil TEXT,
            telefon VARCHAR(30),
            email VARCHAR(255),
            otm VARCHAR(255),
            talim_shakli VARCHAR(20),
            yonalish VARCHAR(255),
            kurs VARCHAR(50),
            ilmiy_tadqiqot BOOLEAN DEFAULT FALSE,
            tadqiqot_info TEXT,
            konferensiya BOOLEAN DEFAULT FALSE,
            maqola BOOLEAN DEFAULT FALSE,
            oldin_grant BOOLEAN DEFAULT FALSE,
            grant_info TEXT,
            kontrakt_sum VARCHAR(100),
            oila_soni VARCHAR(20),
            ota_info TEXT,
            ona_info TEXT,
            aka_opa_info TEXT,
            transkript_file_id TEXT,
            passport_oldi_file_id TEXT,
            passport_orqa_file_id TEXT,
            cv_file_id TEXT,
            imtiyozi TEXT,
            oqish_joyi_file_id TEXT,
            session_id INTEGER,
            motivatsion_xat TEXT,
            rejection_reason TEXT,
            admin_msg_ids TEXT DEFAULT '[]',
            created_at TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)
        # Mavjud jadvalga ustun qo'shish (agar yo'q bo'lsa)
        for col, coltype in [
            ("admin_msg_ids", "TEXT DEFAULT '[]'"),
            ("transkript_file_id", "TEXT"),
            ("passport_oldi_file_id", "TEXT"),
            ("passport_orqa_file_id", "TEXT"),
            ("cv_file_id", "TEXT"),
            ("imtiyozi", "TEXT"),
            ("oqish_joyi_file_id", "TEXT"),
            ("session_id", "INTEGER")
        ]:
            try:
                await self.execute(f"ALTER TABLE arizalar ADD COLUMN IF NOT EXISTS {col} {coltype}", execute=True)
            except Exception:
                pass

    async def add_ariza(self, user_id: str, data: dict, created_at):
        sql = """
        INSERT INTO arizalar (
            user_id, status, fish, tugilgan_sana, millat, manzil, telefon, email,
            otm, talim_shakli, yonalish, kurs,
            ilmiy_tadqiqot, tadqiqot_info, konferensiya, maqola,
            oldin_grant, grant_info, kontrakt_sum,
            oila_soni, ota_info, ona_info, aka_opa_info,
            transkript_file_id, passport_oldi_file_id, passport_orqa_file_id, cv_file_id, imtiyozi, oqish_joyi_file_id,
            session_id,
            motivatsion_xat, created_at
        ) VALUES (
            $1, 'pending', $2, $3, $4, $5, $6, $7,
            $8, $9, $10, $11,
            $12, $13, $14, $15,
            $16, $17, $18,
            $19, $20, $21, $22,
            $23, $24, $25, $26, $27, $28,
            $29,
            $30, $31
        ) RETURNING *;
        """
        return await self.execute(
            sql, user_id,
            data['fish'], data['tugilgan_sana'], data['millat'], data['manzil'],
            data['telefon'], data['email'],
            data['otm'], data['talim_shakli'], data['yonalish'], data['kurs'],
            data.get('ilmiy_tadqiqot', False), data.get('tadqiqot_info', ''),
            data.get('konferensiya', False), data.get('maqola', False),
            data.get('oldin_grant', False), data.get('grant_info', ''),
            data['kontrakt_sum'],
            data['oila_soni'], data['ota_info'], data['ona_info'], data['aka_opa_info'],
            data.get('transkript_file_id'), data.get('passport_oldi_file_id'), data.get('passport_orqa_file_id'), data.get('cv_file_id'), data.get('imtiyozi'), data.get('oqish_joyi_file_id'),
            data.get('session_id'),
            data['motivatsion_xat'], created_at,
            fetchrow=True
        )

    async def get_ariza_by_user(self, user_id: str, session_id: int = None):
        if session_id:
            sql = "SELECT * FROM arizalar WHERE user_id=$1 AND session_id=$2 ORDER BY created_at DESC LIMIT 1"
            return await self.execute(sql, user_id, session_id, fetchrow=True)
        sql = "SELECT * FROM arizalar WHERE user_id=$1 ORDER BY created_at DESC LIMIT 1"
        return await self.execute(sql, user_id, fetchrow=True)

    async def select_user_arizalar(self, user_id: str):
        sql = """
        SELECT a.*, s.name as session_name
        FROM arizalar a
        LEFT JOIN sessions s ON a.session_id = s.id
        WHERE a.user_id = $1
        ORDER BY a.created_at DESC
        """
        return await self.execute(sql, user_id, fetch=True)

    async def get_ariza_by_id(self, ariza_id: int):
        sql = """
        SELECT a.*, u.full_name, u.username
        FROM arizalar a
        JOIN users u ON a.user_id = u.id
        WHERE a.id = $1
        """
        return await self.execute(sql, ariza_id, fetchrow=True)

    async def get_all_arizalar(self, status: str = None, session_id: int = None):
        if status and session_id:
            sql = "SELECT * FROM arizalar WHERE status=$1 AND session_id=$2 ORDER BY created_at DESC"
            return await self.execute(sql, status, session_id, fetch=True)
        elif status:
            sql = "SELECT * FROM arizalar WHERE status=$1 ORDER BY created_at DESC"
            return await self.execute(sql, status, fetch=True)
        elif session_id:
            sql = "SELECT * FROM arizalar WHERE session_id=$1 ORDER BY created_at DESC"
            return await self.execute(sql, session_id, fetch=True)
        sql = "SELECT * FROM arizalar ORDER BY created_at DESC"
        return await self.execute(sql, fetch=True)

    async def update_ariza_status(self, ariza_id: int, status: str, rejection_reason: str = None):
        sql = "UPDATE arizalar SET status=$2, rejection_reason=$3 WHERE id=$1 RETURNING *"
        return await self.execute(sql, ariza_id, status, rejection_reason, fetchrow=True)

    async def cancel_ariza(self, user_id: str):
        sql = "UPDATE arizalar SET status='cancelled' WHERE user_id=$1 AND status='pending'"
        await self.execute(sql, user_id, execute=True)

    async def search_arizalar(self, query: str, session_id: int = None):
        if session_id:
            sql = "SELECT * FROM arizalar WHERE fish ILIKE $1 AND session_id=$2 ORDER BY created_at DESC"
            return await self.execute(sql, f'%{query}%', session_id, fetch=True)
        sql = "SELECT * FROM arizalar WHERE fish ILIKE $1 ORDER BY created_at DESC"
        return await self.execute(sql, f'%{query}%', fetch=True)

    async def count_arizalar(self, status: str = None, session_id: int = None):
        if status and session_id:
            sql = "SELECT COUNT(*) FROM arizalar WHERE status=$1 AND session_id=$2"
            return await self.execute(sql, status, session_id, fetchval=True)
        elif status:
            sql = "SELECT COUNT(*) FROM arizalar WHERE status=$1"
            return await self.execute(sql, status, fetchval=True)
        elif session_id:
            sql = "SELECT COUNT(*) FROM arizalar WHERE session_id=$1"
            return await self.execute(sql, session_id, fetchval=True)
        sql = "SELECT COUNT(*) FROM arizalar"
        return await self.execute(sql, fetchval=True)

    async def save_ariza_admin_msgs(self, ariza_id: int, msgs: list):
        """msgs = [{"chat_id": "123", "msg_id": 456}, ...]"""
        import json
        sql = "UPDATE arizalar SET admin_msg_ids=$2 WHERE id=$1"
        await self.execute(sql, ariza_id, json.dumps(msgs), execute=True)

    async def get_ariza_admin_msgs(self, ariza_id: int) -> list:
        import json
        sql = "SELECT admin_msg_ids FROM arizalar WHERE id=$1"
        raw = await self.execute(sql, ariza_id, fetchval=True)
        try:
            return json.loads(raw or '[]')
        except Exception:
            return []

    # ─── BOT CHATS (guruh/kanallar) ───
    async def create_table_bot_chats(self):
        sql = """
        CREATE TABLE IF NOT EXISTS bot_chats (
            chat_id BIGINT PRIMARY KEY,
            chat_title VARCHAR(255),
            chat_type VARCHAR(20)
        );
        """
        await self.execute(sql, execute=True)

    async def add_bot_chat(self, chat_id: int, chat_title: str, chat_type: str):
        sql = """
        INSERT INTO bot_chats (chat_id, chat_title, chat_type)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id) DO UPDATE SET
            chat_title = EXCLUDED.chat_title,
            chat_type = EXCLUDED.chat_type;
        """
        await self.execute(sql, chat_id, chat_title, chat_type, execute=True)

    async def remove_bot_chat(self, chat_id: int):
        sql = "DELETE FROM bot_chats WHERE chat_id = $1"
        await self.execute(sql, chat_id, execute=True)

    async def get_bot_chats(self):
        sql = "SELECT * FROM bot_chats"
        return await self.execute(sql, fetch=True)

    # ─── BOT SECTIONS (CMS) ───
    async def create_table_sections(self):
        sql = """
        CREATE TABLE IF NOT EXISTS bot_sections (
            id SERIAL PRIMARY KEY,
            section_key VARCHAR(100) UNIQUE NOT NULL,
            parent_key VARCHAR(100) DEFAULT NULL,
            title_uz VARCHAR(300),
            title_ru VARCHAR(300),
            text_uz TEXT,
            text_ru TEXT,
            image TEXT,
            order_num INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE
        );
        """
        await self.execute(sql, execute=True)
        # Eski DB da VARCHAR(200) bo'lsa TEXT ga o'tkazamiz
        await self.execute(
            "ALTER TABLE bot_sections ALTER COLUMN image TYPE TEXT",
            execute=True
        )

    async def seed_sections_if_empty(self):
        """Jadval bo'sh bo'lsa boshlang'ich ma'lumotlarni yuklaydi."""
        count = await self.execute("SELECT COUNT(*) FROM bot_sections", fetchval=True)
        if count and count > 0:
            return

        sections = [
            # Top-level
            ("about", None, "🏛 Olim fondi haqida", "🏛 Об Олим фонде", None, None, None, 1),
            ("stat",  None, "📊 Statistika",        "📊 Статистика",     None, None, None, 2),

            # --- ABOUT sub-sections ---
            ("about:info", "about",
             "📖 Fond haqida", "📖 О фонде",
             """📖 <b>BIZ HAQIMIZDA</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>OLIM FONDI</b> — iqtidorli yoshlarni qo\'llab-quvvatlash, ta\'limda teng imkoniyatlar yaratish va mamlakatning intellektual salohiyatini rivojlantirishga xizmat qiluvchi nodavlat xayriya fondi.

Fond o\'z faoliyati orqali har bir iqtidorli va bilimga intiluvchi talabaga o\'z orzularini ro\'yobga chiqarish uchun imkoniyat yaratishni maqsad qiladi.

Biz ishonamizki, ta\'limga kiritilgan sarmoya — jamiyat kelajagiga kiritilgan eng muhim sarmoyadir.

⸻
<b>Bizning orzumiz:</b>
Hech bir iqtidorli talaba moddiy qiyinchiliklar sababli ta\'limdan chetda qolmasligi, har bir iqtidor esa o\'z imkoniyatini to\'liq namoyon qilishi uchun munosib muhit yaratish.""",
             """📖 <b>О НАС</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>OLIM FONDI</b> — негосударственный благотворительный фонд, созданный для поддержки талантливой молодёжи, создания равных возможностей в образовании и развития интеллектуального потенциала страны.

Мы убеждены: инвестиции в образование — важнейшие инвестиции в будущее общества.

⸻
<b>Наша мечта:</b>
Создать достойную среду, в которой ни один талантливый студент не останется за бортом образования.""",
             "about1.jpg", 1),

            ("about:mission", "about",
             "🎯 Missiya, maqsad va qadriyatlar", "🎯 Миссия, цель и ценности",
             """🎯 <b>BIZNING MISSIYAMIZ</b>
━━━━━━━━━━━━━━━━━━━━━━
Yoshlarning ta\'lim olish imkoniyatlarini kengaytirish, iqtidor va salohiyatni rivojlantirish hamda ijtimoiy tenglikni ta\'minlash orqali kelajak <b>liderlari, olimlari va mutaxassislarini tarbiyalash.</b>

⸻
🎯 <b>BIZNING MAQSADIMIZ</b>
━━━━━━━━━━━━━━━━━━━━━━
Talabalarning bilim olishi, shaxsiy va kasbiy rivojlanishi uchun munosib shart-sharoitlar yaratish hamda ularning jamiyat taraqqiyotiga munosib <b>hissa qo\'shishiga ko\'maklashish.</b>

⸻
👁 <b>BIZNING QARASIMIZ (VISION)</b>
━━━━━━━━━━━━━━━━━━━━━━
Iqtidor va mehnat har qanday to\'siqlardan ustun keladigan, har bir yosh o\'z bilim va qobiliyatini <b>erkin rivojlantira oladigan</b> jamiyatni shakllantirish.

⸻
⚖️ <b>BIZNING QADRIYATLARIMIZ</b>
━━━━━━━━━━━━━━━━━━━━━━
• Ta\'lim – eng katta boylik.
• Inson qadri – eng oliy qadriyat.
• Teng imkoniyatlar – har bir yosh uchun adolat.
• Shaffoflik – ishonchning asosi.
• Mas\'uliyat – kelajak oldidagi burch.
• Innovatsiya va taraqqiyot – barqaror kelajak garovi.""",
             """🎯 <b>НАША МИССИЯ</b>
━━━━━━━━━━━━━━━━━━━━━━
Расширение возможностей молодёжи для получения образования, раскрытие и развитие таланта, обеспечение социального равенства для воспитания <b>будущих лидеров, учёных и специалистов.</b>

⸻
⚖️ <b>НАШИ ЦЕННОСТИ</b>
━━━━━━━━━━━━━━━━━━━━━━
• Образование – главное богатство.
• Достоинство человека – высшая ценность.
• Равные возможности – справедливость для каждого.
• Прозрачность – основа доверия.
• Ответственность – долг перед будущим.""",
             "about2.jpg", 2),

            ("about:opportunities", "about",
             "🚀 Faoliyat yo\'nalishlari", "🚀 Направления деятельности",
             """🚀 <b>FOND FAOLIYATINING ASOSIY YO\'NALISHLARI</b>
━━━━━━━━━━━━━━━━━━━━━━
🔵 <b>60% — Ijtimoiy imkoniyati cheklangan talabalar</b>
Moddiy yoki ijtimoiy qiyinchiliklarga duch kelgan, ammo ta\'lim olishga intilayotgan talabalar.

🟢 <b>40% — Iqtidorli va yuqori salohiyatli talabalar</b>
Yuqori akademik natijalarga erishgan, innovatsion g\'oyalarga ega talabalar.

⸻
📚 <b>Ta\'lim</b> • 🤝 <b>Xayriya</b> • 🌱 <b>Yoshlar rivoji</b> • 🏛 <b>Ma\'naviy meros</b>

<i>Fondning shiori: "Ilm bilan yuksamiz, ezgulik bilan birlahamiz."</i>""",
             """🚀 <b>ОСНОВНЫЕ НАПРАВЛЕНИЯ</b>
━━━━━━━━━━━━━━━━━━━━━━
🔵 <b>60%</b> — Студенты с ограниченными социальными возможностями
🟢 <b>40%</b> — Талантливые и высокопотенциальные студенты

📚 Образование • 🤝 Благотворительность • 🌱 Развитие молодёжи • 🏛 Духовное наследие

<i>Девиз: "Возвышаемся знаниями, объединяемся добродетелью."</i>""",
             "about3.jpg", 3),

            ("about:history", "about",
             "📅 Fond tarixi va ta\'sischi", "📅 История фонда и основатель",
             """📝 <b>TA\'SISCHI MUROJAAT</b>
━━━━━━━━━━━━━━━━━━━━━━
<i>Aziz yoshlar!</i>

<i>Har bir buyuk yutuq ortida bilim, mehnat va imkoniyat turadi. OLIM FONDI aynan shu yoshlarni qo\'llab-quvvatlash maqsadida tashkil etildi.</i>

<i>Bizning orzumiz — hech bir iqtidorli yosh imkoniyatsiz qolmasligi va har bir mehnatkash talaba o\'z salohiyatini to\'liq namoyon eta olishi.</i>

⸻
<b>Fondning strategik maqsadi:</b>
Yoshlarning sifatli ta\'lim olishi uchun teng imkoniyatlar yaratish, iqtidorli talabalarni rag\'batlantirish hamda ijtimoiy himoyaga muhtoj talabalarni qo\'llab-quvvatlash.""",
             """📝 <b>ОБРАЩЕНИЕ ОСНОВАТЕЛЯ</b>
━━━━━━━━━━━━━━━━━━━━━━
<i>Дорогие молодые люди!</i>

<i>OLIM FONDI создан для поддержки талантливых молодых людей. Наша мечта — чтобы ни один талантливый юноша не остался без возможностей.</i>

⸻
<b>Стратегическая цель фонда:</b>
Создание равных возможностей для получения качественного образования и поддержка нуждающихся студентов.""",
             "about4.jpg", 4),

            # --- STAT sub-sections ---
            ("stat:stats", "stat",
             "📊 Yillik ariza statistikasi", "📊 Статистика заявок",
             """📊 <b>YILLIK ARIZA KELIB TUSHISH</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>Topshiruvchilar:</b>
  2021: 60  |  2022: 80  |  2023: 150  |  2024: 162  |  2025: 1000

<b>2-bosqichga o\'tganlar:</b>
  2021: 48  |  2022: 61  |  2023: 90  |  2024: 137  |  2025: 100

<b>3-bosqichga o\'tganlar:</b>
  2021: 17  |  2022: 33  |  2023: 33  |  2024: 52  |  2025: 50

<b>Stipendiyant bo\'lganlar:</b>
  2021: 6  |  2022: 15  |  2023: 16  |  2024: 14  |  2025: 14""",
             """📊 <b>ЕЖЕГОДНОЕ ПОСТУПЛЕНИЕ ЗАЯВОК</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>Подавших заявки:</b>
  2021: 60  |  2022: 80  |  2023: 150  |  2024: 162  |  2025: 1000

<b>Ставших стипендиатами:</b>
  2021: 6  |  2022: 15  |  2023: 16  |  2024: 14  |  2025: 14""",
             "stat1.jpg", 1),

            ("stat:graduates", "stat",
             "🎓 Bitirgan stipendiyantlar", "🎓 Выпускники-стипендиаты",
             """🎓 <b>BITIRGAN STIPENDIYANTLAR NATIJALARI</b>
━━━━━━━━━━━━━━━━━━━━━━

🏛 Vazirliklar — <b>36.6%</b>
🏢 Davlat tashkilotlari — <b>24.4%</b>
🌐 Xalqaro kompaniyalar — <b>14.6%</b>
🎓 OTM — <b>12.2%</b>
🌍 Xalqaro universitetlar magistranti — <b>12.2%</b>""",
             """🎓 <b>РЕЗУЛЬТАТЫ ВЫПУСКНИКОВ</b>
━━━━━━━━━━━━━━━━━━━━━━

🏛 Министерства — <b>36.6%</b>
🏢 Государственные организации — <b>24.4%</b>
🌐 Международные компании — <b>14.6%</b>
🎓 ВУЗы — <b>12.2%</b>""",
             "stat2.jpg", 2),

            # --- MGMT top-level ---
            ("mgmt", None, "👤 Rahbariyat", "👤 Руководство", None, None, None, 3),

            # --- MGMT sections ---
            ("mgmt:fondrah", "mgmt", "💼 Fond ta'sischisi", "💼 Основатель фонда", None, None, None, 1),
            ("mgmt:kuzatuv", "mgmt", "👔 Kuzatuv kengashi a'zolari", "👔 Члены Наблюдательного совета", None, None, None, 2),
            ("mgmt:kuratorlar", "mgmt", "🤝 Kuratorlar", "🤝 Кураторы", None, None, None, 3),
            ("mgmt:ekspertlar", "mgmt", "🧠 Ekspertlar", "🧠 Эксперты", None, None, None, 4),
            ("mgmt:volontyorlar", "mgmt", "🙌 Volontyorlar", "🙌 Волонтёры", None, None, None, 5),

            # --- Persons ---
            ("mgmt:zuhra", "mgmt:fondrah", "ZUHRA SHARIPOVA", "ZUHRA SHARIPOVA",
             "💼 <b>Fond ta'sischisi</b>\n\n<b>ZUHRA SHARIPOVA</b>",
             "💼 <b>Основатель фонда</b>\n\n<b>ZUHRA SHARIPOVA</b>", "mgmt_zuhra.jpg", 1),

            ("mgmt:odil", "mgmt:kuzatuv", "ODIL XASANOV", "ОДИЛ ХАСАНОВ",
             "👔 <b>Kuzatuv kengashi a'zosi</b>\n\n<b>ODIL XASANOV</b>",
             "👔 <b>Член Наблюдательного совета</b>\n\n<b>ОДИЛ ХАСАНОВ</b>", "mgmt_odil.jpg", 1),
            ("mgmt:xasan", "mgmt:kuzatuv", "XASAN XASANOV", "ХАСАН ХАСАНОВ",
             "👔 <b>Kuzatuv kengashi a'zosi</b>\n\n<b>XASAN XASANOV</b>",
             "👔 <b>Член Наблюдательного совета</b>\n\n<b>ХАСАН ХАСАНОВ</b>", "mgmt_xasan.jpg", 2),

            ("mgmt:zebo", "mgmt:kuratorlar", "ZEBO SHARIPOVA", "ЗЕБО ШАРИПОВА",
             "🤝 <b>Kurator</b>\n\n<b>ZEBO SHARIPOVA</b>",
             "🤝 <b>Куратор</b>\n\n<b>ЗЕБО ШАРИПОВА</b>", "mgmt_zebo.jpg", 1),
            ("mgmt:bekzod", "mgmt:kuratorlar", "BEKZOD ISTAMOV", "БЕКЗОД ИСТАМОВ",
             "🤝 <b>Kurator</b>\n\n<b>BEKZOD ISTAMOV</b>",
             "🤝 <b>Куратор</b>\n\n<b>БЕКЗОД ИСТАМОВ</b>", "mgmt_bekzod.jpg", 2),
            ("mgmt:ozodbek", "mgmt:kuratorlar", "OZODBEK YO'LDOSHEV", "OZODBEK YO'LDOSHEV",
             "🤝 <b>Kurator</b>\n\n<b>OZODBEK YO'LDOSHEV</b>",
             "🤝 <b>Куратор</b>\n\n<b>OZODBEK YO'LDOSHEV</b>", "mgmt_ozodbek.jpg", 3),
            ("mgmt:shaxzoda", "mgmt:kuratorlar", "SHAXZODA ABBOSOVA", "ШАХЗОДА АББОСОВА",
             "🤝 <b>Kurator</b>\n\n<b>SHAXZODA ABBOSOVA</b>",
             "🤝 <b>Куратор</b>\n\n<b>ШАХЗОДА АББОСОВА</b>", "mgmt_shaxzoda.jpg", 4),

            ("mgmt:zarifa", "mgmt:ekspertlar", "ZARIFA MUMINOVA", "ЗАРИФА МУМИНОВА",
             "🧠 <b>Akademik faoliyat eksperti</b>\n\n<b>ZARIFA MUMINOVA</b>",
             "🧠 <b>Эксперт по академической деятельности</b>\n\n<b>ЗАРИФА МУМИНОВА</b>", "mgmt_zarifa.jpg", 1),
            ("mgmt:azamat", "mgmt:ekspertlar", "AZAMAT AKBAROV", "АЗАМАТ АКБАРОВ",
             "🧠 <b>Strategik rivojlantirish eksperti</b>\n\n<b>AZAMAT AKBAROV</b>",
             "🧠 <b>Эксперт по стратегическому развитию</b>\n\n<b>АЗАМАТ АКБАРОВ</b>", "mgmt_azamat.jpg", 2),
            ("mgmt:javohir", "mgmt:ekspertlar", "JAVOHIR BATIROV", "ЖАВОХИР БАТИРОВ",
             "🧠 <b>Moliyaviy ishlar eksperti</b>\n\n<b>JAVOHIR BATIROV</b>",
             "🧠 <b>Эксперт по финансовым вопросам</b>\n\n<b>ЖАВОХИР БАТИРОВ</b>", "mgmt_javohir.jpg", 3),

            ("mgmt:faxriddin", "mgmt:volontyorlar", "FAXRIDDIN BURXONOV", "ФАХРИДДИН БУРХОНОВ",
             "🙌 <b>Volontyor</b>\n\n<b>FAXRIDDIN BURXONOV</b>",
             "🙌 <b>Волонтёр</b>\n\n<b>ФАХРИДДИН БУРХОНОВ</b>", "mgmt_faxriddin.jpg", 1),
            ("mgmt:jurabek", "mgmt:volontyorlar", "JURABEK SODIKOV", "ЖУРАБЕК СОДИКОВ",
             "🙌 <b>Volontyor</b>\n\n<b>JURABEK SODIKOV</b>",
             "🙌 <b>Волонтёр</b>\n\n<b>ЖУРАБЕК СОДИКОВ</b>", "mgmt_jurabek.jpg", 2),

            ("stat:achievements", "stat",
             "🏆 Stipendiyantlar yutuqlari", "🏆 Достижения стипендиатов",
             """🏆 <b>STIPENDIYANTLARIMIZ YUTUQLARI</b>
━━━━━━━━━━━━━━━━━━━━━━

🥇 Nomdor va atoqli stipendiyatlar — <b>18 ta</b>
📝 Maqolalar va ilmiy izlanishlar — <b>300 dan oshiq</b>
🌟 Xalqaro tanlovlar g\'oliblari — <b>7 ta</b>
📜 Nufuzli sertifikat egalari — <b>20 ta</b>""",
             """🏆 <b>ДОСТИЖЕНИЯ СТИПЕНДИАТОВ</b>
━━━━━━━━━━━━━━━━━━━━━━

🥇 Именных стипендий — <b>18</b>
📝 Научных статей — <b>более 300</b>
🌟 Победителей конкурсов — <b>7</b>
📜 Обладателей сертификатов — <b>20</b>""",
             "stat3.jpg", 3),
        ]

        for row in sections:
            key, parent, tuz, tru, textuz, textru, img, order = row
            await self.execute(
                """INSERT INTO bot_sections
                   (section_key, parent_key, title_uz, title_ru, text_uz, text_ru, image, order_num)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                   ON CONFLICT (section_key) DO NOTHING""",
                key, parent, tuz, tru, textuz, textru, img, order,
                execute=True
            )

    async def get_section(self, section_key: str):
        return await self.execute(
            "SELECT * FROM bot_sections WHERE section_key=$1", section_key, fetchrow=True
        )

    async def get_children(self, parent_key, admin=False):
        """parent_key ga tegishli sub-bo'limlarni order_num bo'yicha qaytaradi.
        admin=True bo'lsa yashirilgan bo'limlar ham ko'rsatiladi."""
        if admin:
            return await self.execute(
                "SELECT * FROM bot_sections WHERE parent_key=$1 ORDER BY order_num",
                parent_key, fetch=True
            )
        return await self.execute(
            "SELECT * FROM bot_sections WHERE parent_key=$1 AND is_active=TRUE ORDER BY order_num",
            parent_key, fetch=True
        )

    async def get_top_sections(self, admin=False):
        """Top-level bo'limlar (parent_key IS NULL).
        admin=True bo'lsa yashirilgan bo'limlar ham ko'rsatiladi."""
        if admin:
            return await self.execute(
                "SELECT * FROM bot_sections WHERE parent_key IS NULL ORDER BY order_num",
                fetch=True
            )
        return await self.execute(
            "SELECT * FROM bot_sections WHERE parent_key IS NULL AND is_active=TRUE ORDER BY order_num",
            fetch=True
        )

    async def update_section_field(self, section_key: str, field: str, value):
        allowed = {'title_uz', 'title_ru', 'text_uz', 'text_ru', 'image', 'order_num', 'is_active'}
        if field not in allowed:
            raise ValueError(f"Invalid field: {field}")
        sql = f"UPDATE bot_sections SET {field}=$2 WHERE section_key=$1"
        await self.execute(sql, section_key, value, execute=True)

    async def add_section(self, section_key: str, parent_key, title_uz: str, title_ru: str,
                          text_uz: str, text_ru: str, image: str, order_num: int = 0):
        sql = """
        INSERT INTO bot_sections (section_key, parent_key, title_uz, title_ru, text_uz, text_ru, image, order_num)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        ON CONFLICT (section_key) DO NOTHING
        RETURNING *;
        """
        return await self.execute(sql, section_key, parent_key, title_uz, title_ru,
                                  text_uz, text_ru, image, order_num, fetchrow=True)

    async def delete_section(self, section_key: str):
        """Bo'lim va barcha avlodlarini (rekursiv) o'chirish."""
        # Avval barcha sub-bo'limlarni rekursiv o'chirish
        children = await self.execute(
            "SELECT section_key FROM bot_sections WHERE parent_key=$1",
            section_key, fetch=True
        )
        for child in (children or []):
            await self.delete_section(child['section_key'])
        # So'ng o'zini o'chirish
        await self.execute(
            "DELETE FROM bot_sections WHERE section_key=$1", section_key, execute=True
        )

    async def swap_section_order(self, key1: str, key2: str):
        row1 = await self.get_section(key1)
        row2 = await self.get_section(key2)
        if not row1 or not row2:
            return
        await self.update_section_field(key1, 'order_num', row2['order_num'])
        await self.update_section_field(key2, 'order_num', row1['order_num'])

    async def ensure_service_sections(self):
        """
        Xizmat bo'limlari (hujjat yuborish, ariza, murojaat) DBda yo'q bo'lsa qo'shadi.
        Bu bo'limlar CMS orqali faol/nofaol qilinadi va asosiy menyuga ta'sir qiladi.
        """
        services = [
            ('svc:hujjat',   '📂 Hujjat yuborish',         '📂 Отправить документ',      90),
            ('svc:ariza',    '📬 Ariza topshirish',          '📬 Подача документов',        91),
            ('svc:murojaat', '✍️ Murojaat yuborish',         '✍️ Отправить обращение',      92),
        ]
        for key, title_uz, title_ru, order in services:
            existing = await self.get_section(key)
            if not existing:
                await self.add_section(
                    section_key=key,
                    parent_key=None,
                    title_uz=title_uz,
                    title_ru=title_ru,
                    text_uz='',
                    text_ru='',
                    image=None,
                    order_num=order
                )

    async def is_service_active(self, key: str) -> bool:
        """svc:* bo'limi aktiv ekanini tekshiradi. DB da yo'q bo'lsa True qaytaradi."""
        section = await self.get_section(key)
        if not section:
            return True
        return bool(section['is_active'])
