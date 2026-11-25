# Task Manager’ni Render’da ishga tushirish

Backend manzili `https://task-manager-turl.onrender.com`. Frontend alohida Static Site sifatida, Telegram bot esa bitta Python Background Worker sifatida ishlaydi.

## 1. Token va ma’lumotlarni tayyorlash

- Git tarixida saqlangan eski bot tokenini BotFather’da bekor qiling. Yangi `BOT_TOKEN` qiymatini backend va bot worker Environment bo’limlariga bir xil kiriting.
- JWT kalitini `python -c "import secrets; print(secrets.token_urlsafe(48))"` orqali yarating va faqat backend’da `JWT_SECRET` sifatida saqlang.
- Eski bazadagi ma’lumot kerak bo’lsa, yangi deploydan oldin ishlab turgan SQLite bazasidan izchil zaxira oling. Yozuvlarni vaqtincha to’xtatib, ishlayotgan bazaning zaxirasini ishlating. Repo bilan kelgan lokal nusxa production bazasidan farq qilishi mumkin.

## 2. Mavjud backend va PostgreSQL

Render’da mavjud backend bilan bir regionda PostgreSQL yarating. Backend Environment bo’limida quyidagilarni o’rnating.

| O’zgaruvchi | Qiymat |
| --- | --- |
| `DATABASE_URL` | PostgreSQL xizmatining **Internal Database URL** qiymati |
| `BOT_TOKEN` | BotFather bergan yangi token |
| `JWT_SECRET` | Yuqorida yaratilgan kalit |
| `FRONTEND_ORIGINS` | Frontend’ning haqiqiy HTTPS origin’i, masalan `https://task-manager-frontend.onrender.com`. Bir nechta domenni vergul bilan ajrating. |
| `PYTHON_VERSION` | `3.13.15` |

Backend Web Service sozlamalari:

| Sozlama | Qiymat |
| --- | --- |
| Branch | `main` |
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health Check Path | `/health` |

Backend ishga tushganda jadvallarni yaratadi. `/health` PostgreSQL ulanishini ham tekshiradi. Agar SQLite’dan ko’chirish kerak bo’lsa, yangi frontend’ni foydalanuvchilarga ochishdan oldin import qiling. Mahalliy muhitda backend paketlarini o’rnating, `DATABASE_URL` uchun yangi bazaning External Database URL manzilini SSL bilan ishlating va loyiha ildizidan ishga tushiring:

```sh
python backend/import_sqlite.py /path/to/sqlite-backup.db
```

Skript bo’sh PostgreSQL bazasiga foydalanuvchilar va vazifalarni mavjud ID’lari bilan ko’chiradi, so’ng yangi yozuvlar uchun ID ketma-ketligini sozlaydi.

## 3. Frontend va bot

`render.yaml` frontend va bot worker’ni yaratish uchun tayyor. Pushdan keyin Render Dashboard’da **New ’ Blueprint** orqali `main` branchini tanlang. Blueprint’dagi worker `starter` tarifida. Mavjud backend va PostgreSQL yuqoridagi Dashboard sozlamalari orqali boshqariladi.

Agar frontend URL’i oldindan ma’lum bo’lmasa, avval Dashboard orqali Static Site yarating. Keyin bot uchun shu URL’ni kiriting.

| Xizmat | Sozlamalar |
| --- | --- |
| Static Site | Branch `main`, Root Directory `frontend/frontend`, Build Command `npm ci && npm run build`, Publish Directory `dist` |
| Static Site Environment | `VITE_API_URL=https://task-manager-turl.onrender.com`, `NODE_VERSION=24.11.1`, `SKIP_INSTALL_DEPS=true` |
| Background Worker | Branch `main`, Root Directory `bot`, Build Command `pip install -r requirements.txt`, Start Command `python main.py`, bitta instance |
| Worker Environment | `BOT_TOKEN`, frontend’ning HTTPS manzili sifatida `WEBAPP_URL`, `PYTHON_VERSION=3.13.15` |

Worker ishga tushishidan oldin shu token bilan ishlayotgan eski bot jarayonini to’xtating. Worker Telegram long polling’iga o’tishda avvalgi webhook’ni olib tashlaydi. `VITE_API_URL` o’zgarsa frontend’ni qayta build qiling. Frontend’ning yakuniy manzilini backend’dagi `FRONTEND_ORIGINS` va worker’dagi `WEBAPP_URL` bilan moslang.

## 4. Tekshiruv

1. `https://task-manager-turl.onrender.com/health` manzili `200` qaytarishini tekshiring.
2. Telegram’da botga shaxsiy chatda `/start` yuboring va **Open Task Manager** tugmasini bosing.
3. Birinchi ochilishda foydalanuvchi Telegram ID orqali ro’yxatdan o’tadi. Keyingi ochilishda mavjud profil qayta ishlatiladi. Frontend `POST /api/auth/telegram` orqali JWT oladi va vazifa so’rovlarida Bearer token yuboradi.
4. Vazifa yarating, bajarilgan deb belgilang, ilovani qayta ochib yozuv saqlanganini tekshiring, so’ng vazifani o’chiring.

Lokal API testlari uchun backend katalogidan `pip install -r requirements-dev.txt` va `python -m unittest -v` buyruqlarini bajaring. PostgreSQL bilan shu testlarni bajarish uchun `TEST_DATABASE_URL` orqali alohida, bo’sh baza manzilini `postgresql+psycopg://` formatida bering. Lokal brauzerda Telegram’siz ishlab chiqish uchun backend `.env` fayliga `ALLOW_LOCAL_DEV=1` yozing va backend’ni loopback manzilida ishga tushiring.
