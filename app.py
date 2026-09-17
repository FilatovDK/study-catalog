from flask import Flask, render_template_string

app = Flask(__name__)

subjects = [
    {
        "name": "Программирование",
        "desc": "Изучай Python, алгоритмы и основы разработки приложений.",
        "icon": "💻",
        "category": "Разработка",
        "color": "blue"
    },
    {
        "name": "Базы данных",
        "desc": "Освой SQL, проектирование таблиц и управление данными.",
        "icon": "🗄️",
        "category": "Данные",
        "color": "purple"
    },
    {
        "name": "Компьютерные сети",
        "desc": "Узнай, как устроен интернет и работают сетевые протоколы.",
        "icon": "🌐",
        "category": "Инфраструктура",
        "color": "green"
    },
    {
        "name": "Информационные системы",
        "desc": "Изучай архитектуру и проектирование информационных систем.",
        "icon": "📊",
        "category": "Разработка",
        "color": "orange"
    }
]


@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Study Catalog — Учебная платформа</title>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', Arial, sans-serif;
            background: #0b1020;
            color: #ffffff;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: auto;
            padding: 30px 25px;
        }

        /* Навигация */

        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 45px;
            gap: 15px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 23px;
            font-weight: 800;
        }

        .logo-icon {
            background: linear-gradient(135deg, #6366f1, #9333ea);
            padding: 12px;
            border-radius: 15px;
        }

        .status {
            padding: 10px 16px;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #4ade80;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 600;
        }

        /* Главный блок */

        .hero {
            position: relative;
            overflow: hidden;
            background: linear-gradient(
                120deg, #1e3a8a, #4338ca, #7e22ce
            );
            padding: 65px 50px;
            border-radius: 28px;
            margin-bottom: 45px;
        }

        .hero::after {
            content: "";
            position: absolute;
            width: 300px;
            height: 300px;
            right: -90px;
            top: -100px;
            border: 60px solid rgba(255,255,255,0.08);
            border-radius: 50%;
            pointer-events: none;
        }

        .tag {
            display: inline-block;
            background: rgba(255,255,255,0.15);
            padding: 9px 15px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-bottom: 25px;
        }

        h1 {
            font-size: clamp(32px, 5vw, 52px);
            font-weight: 800;
            max-width: 700px;
            line-height: 1.15;
            margin-bottom: 22px;
        }

        .hero p {
            color: #e0e7ff;
            line-height: 1.8;
            font-size: 16px;
            max-width: 550px;
        }

        .hero-info {
            display: flex;
            gap: 25px;
            margin-top: 30px;
            flex-wrap: wrap;
            font-size: 14px;
            font-weight: 600;
        }

        /* Заголовок раздела */

        .section-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            gap: 15px;
            flex-wrap: wrap;
        }

        .section-head h2 {
            font-size: 26px;
            margin-bottom: 8px;
        }

        .section-head p {
            color: #94a3b8;
            font-size: 14px;
        }

        /* Поиск */

        .search {
            background: #151d31;
            border: 1px solid #303b55;
            color: white;
            padding: 15px 20px;
            border-radius: 12px;
            width: 280px;
            outline: none;
            font-size: 14px;
        }

        .search:focus {
            border-color: #818cf8;
        }

        .search::placeholder {
            color: #64748b;
        }

        /* Карточки */

        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .card {
            background: #151d31;
            border: 1px solid #29344f;
            padding: 30px;
            border-radius: 20px;
            transition: 0.3s;
        }

        .card:hover {
            transform: translateY(-6px);
            border-color: #818cf8;
            box-shadow: 0 15px 35px rgba(0,0,0,0.25);
        }

        .card-icon {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 62px;
            height: 62px;
            font-size: 30px;
            border-radius: 17px;
            margin-bottom: 22px;
        }

        .blue {
            background: rgba(56,189,248,0.13);
        }

        .purple {
            background: rgba(167,139,250,0.13);
        }

        .green {
            background: rgba(52,211,153,0.13);
        }

        .orange {
            background: rgba(251,191,36,0.13);
        }

        .category {
            display: inline-block;
            color: #a5b4fc;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 12px;
        }

        .card h3 {
            font-size: 21px;
            margin-bottom: 14px;
        }

        .card p {
            font-size: 14px;
            color: #94a3b8;
            line-height: 1.8;
            min-height: 50px;
        }

        .card-bottom {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid #29344f;
        }

        .course-label {
            color: #64748b;
            font-size: 12px;
        }

        .course-arrow {
            color: #818cf8;
            font-size: 23px;
        }

        /* Информация о сервисе */

        .info {
            background: linear-gradient(135deg, #18243e, #211d43);
            border: 1px solid #34365d;
            padding: 35px;
            border-radius: 22px;
            margin-top: 45px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }

        .info h2 {
            font-size: 24px;
            margin-bottom: 12px;
        }

        .info p {
            color: #94a3b8;
            font-size: 14px;
            line-height: 1.7;
        }

        .button {
            display: inline-block;
            background: #6366f1;
            color: white;
            text-decoration: none;
            padding: 15px 25px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 700;
            transition: 0.2s;
        }

        .button:hover {
            background: #818cf8;
            transform: translateY(-2px);
        }

        /* Подвал */

        footer {
            text-align: center;
            color: #64748b;
            border-top: 1px solid #202b43;
            padding: 30px;
            margin-top: 50px;
            font-size: 13px;
        }

        #empty {
            display: none;
            color: #94a3b8;
            padding: 35px;
            text-align: center;
        }

        /* Адаптация */

        @media (max-width: 700px) {
            .hero {
                padding: 40px 25px;
            }

            .grid {
                grid-template-columns: 1fr;
            }

            .search {
                width: 100%;
            }

            .section-head {
                flex-direction: column;
                align-items: stretch;
            }

            .info {
                padding: 25px;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <nav>
        <div class="logo">
            <div class="logo-icon">🎓</div>
            Study Catalog
        </div>

        <div class="status">● Сервис запущен</div>
    </nav>

    <section class="hero">

        <span class="tag">ОБРАЗОВАТЕЛЬНАЯ ПЛАТФОРМА</span>

        <h1>Твой путь к знаниям начинается здесь.</h1>

        <p>
            Открой для себя учебные дисциплины,
            изучай технологии и развивай навыки
            в области информационных систем.
        </p>

        <div class="hero-info">
            <span>📚 {{ subjects|length }} дисциплины</span>
            <span>🐳 Docker</span>
            <span>⚡ Python + Flask</span>
        </div>

    </section>

    <div class="section-head">
        <div>
            <h2>Каталог дисциплин</h2>
            <p>Выбери интересующее тебя направление</p>
        </div>

        <input
            class="search"
            id="search"
            type="search"
            placeholder="🔍  Поиск дисциплины..."
            oninput="searchSubjects()"
        >
    </div>

    <div class="grid" id="subjects">

        {% for subject in subjects %}

        <div class="card">

            <div class="card-icon {{ subject.color }}">
                {{ subject.icon }}
            </div>

            <span class="category">
                {{ subject.category }}
            </span>

            <h3>{{ subject.name }}</h3>

            <p>{{ subject.desc }}</p>

            <div class="card-bottom">
                <span class="course-label">
                    Учебная дисциплина
                </span>
                <span class="course-arrow">↗</span>
            </div>

        </div>

        {% endfor %}

    </div>

    <p id="empty">По вашему запросу ничего не найдено.</p>

    <section class="info">

        <div>
            <h2>🚀 Приложение работает в Docker</h2>
            <p>
                Веб-приложение разработано на Python Flask
                и запущено внутри Docker-контейнера.
            </p>
        </div>

        <a href="/health" class="button">
            Проверить статус →
        </a>

    </section>

    <footer>
        Study Catalog © 2026 · Лабораторная работа №1
        <br><br>
        Docker + Python + Flask
    </footer>

</div>

<script>
    function searchSubjects() {
        const query = document.getElementById("search")
            .value.toLowerCase().trim();

        const cards = document.querySelectorAll(".card");
        let visible = 0;

        cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            const match = text.includes(query);

            card.style.display = match ? "" : "none";

            if (match) visible++;
        });

        document.getElementById("empty").style.display =
            visible === 0 ? "block" : "none";
    }
</script>

</body>
</html>
    """, subjects=subjects)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)