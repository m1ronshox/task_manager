# Buxoro Avto Magnat

Avtoservisga yozilish, ehtiyot qismlar katalogi va avtomobil texnik tarixini boshqarish uchun Telegram Mini App. Loyiha mavjud FastAPI, React, PostgreSQL va Render xizmatlaridan foydalanadi.

## Lokal ishga tushirish

Backend uchun `backend/.env.example` asosida `backend/.env` yarating. Telegram ichidan kirish uchun `BOT_TOKEN` va kamida 32 belgilik `JWT_SECRET` kerak. Lokal brauzer sinovida `ALLOW_LOCAL_DEV=1` va loopback manzilidan foydalaning. SQLite lokal test uchun standart, Render’da PostgreSQL ishlatiladi.

```sh
cd backend
pip install -r requirements-dev.txt
python -m unittest -v
uvicorn main:app --host 127.0.0.1 --port 8000
```

```sh
cd frontend/frontend
npm ci
npm run dev
npm run lint
npm run build
```

API ishga tushishi bilan Alembic `head` ga o‘tadi. Qo‘lda ishga tushirish uchun backend katalogidan `alembic upgrade head` buyrug‘ini bajaring. Birinchi migratsiya eski `users` va `tasks` jadvallarini saqlaydi, faqat yetishmayotgan jadvallar va boshlang‘ich xizmat kategoriyalarini qo‘shadi. Eski vazifalar API orqali saqlanib qoladi va yangi interfeysda ko‘rsatilmaydi. PostgreSQL testlari uchun `TEST_DATABASE_URL` orqali alohida, bo‘sh test bazasini `postgresql+psycopg://` formatida bering.

## Render sozlamalari

| Xizmat | Sozlama |
| --- | --- |
| Mavjud FastAPI Web Service | `main`, ildiz `backend`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1`, health `/health` |
| Mavjud React Static Site | `main`, ildiz `frontend/frontend`, build `npm ci && npm run build`, publish `dist` |
| Mavjud PostgreSQL | Backend bilan bir region, `DATABASE_URL` uchun Internal Database URL |

Backend Environment bo‘limiga `DATABASE_URL`, `JWT_SECRET`, `BOT_TOKEN`, `FRONTEND_ORIGINS=https://task-manager-1-fn25.onrender.com`, `PYTHON_VERSION=3.13.15` va administratorlarning vergul bilan ajratilgan sonli Telegram ID qiymatlari sifatida `ADMIN_TELEGRAM_IDS` ni kiriting. Administrator bo‘limi faqat tasdiqlangan Telegram sessiyasi va shu ro‘yxatdagi ID orqali ochiladi.

Static Site Environment bo‘limiga `VITE_API_URL=https://task-manager-turl.onrender.com`, `NODE_VERSION=24.11.1` va `SKIP_INSTALL_DEPS=true` kiriting. Mavjud xizmatlar uchun Dashboard sozlamalarini saqlang. `render.yaml` faqat yangi Static Site kerak bo‘lganda ishlatilishi mumkin.

Deploydan oldin production bazasining zaxirasini oling. Agar manba eski SQLite bazasi bo‘lsa, izchil SQLite zaxirasini bo‘sh PostgreSQL bazasiga `python backend/import_sqlite.py /path/to/backup.db` orqali import qiling. Tashqaridan import qilishda PostgreSQL External Database URL va TLS ishlating. Free Render PostgreSQL ishlatilsa, 30 kunlik muddat tugashidan oldin bazani eksport qiling.

Deploydan so‘ng `/health` va `/api/auto/catalog` javoblarini tekshiring. Admin panelida haqiqiy narx, davomiylik, mavjudlik va aloqa ma’lumotlarini kiriting. Profil bildirishnomalarida yaqin 7 kundagi texnik xizmat eslatmalari ko‘rinadi. Boshlang‘ich xizmatlar bron uchun yopiq. Mahsulot va maxsus takliflar tasdiqlangan biznes ma’lumotlari bilan admin tomonidan yaratiladi. Bron bir xizmat yoki bir avtomobil uchun vaqtlar to‘qnashuvini bloklaydi. Mahsulot buyurtmasida ombor kamayadi, buyurtma bekor qilinganda qaytariladi. Tushum ko‘rsatkichi bajarilgan buyurtma va xizmatlar qiymatini jamlaydi.

## Telegram bot

@BuxaraAvtoMagnatBot uchun `bot/.env.example` asosida lokal `bot/.env` yarating. `BOT_TOKEN` backend bilan bir xil bo‘lsin. `WEBAPP_URL=https://task-manager-1-fn25.onrender.com` ni kiriting. BotFather’da Mini App manzilini sozlang. Gitga faqat `.env.example` fayllari kiritiladi.

Bepul usulda bot kompyuterda `pip install -r bot/requirements.txt` va `python bot/main.py` orqali polling bilan ishlaydi. Bir token uchun bitta jarayon ishlating. Render doimiy Background Worker xizmatini pullik tarifda beradi. Repozitoriydagi Blueprint worker yaratmaydi.

Bot bilan shaxsiy chatda `/start` yuboring. Mini App ochilgach xizmatlar, buyurtmalar va aloqa tugmalarini tekshiring. Backend bron yoki buyurtma yaratilganda va holat o‘zgarganda bildirishnomani bazada saqlaydi hamda Telegram Bot API orqali yuborishga urinadi. Telegram yetkazib berishi uchun foydalanuvchi bot bilan suhbatni boshlagan bo‘lishi kerak.
