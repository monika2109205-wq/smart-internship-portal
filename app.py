from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "internship_secret"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def calculate_match(student_skills, required_skills):
    student_set = set(
        skill.strip().lower()
        for skill in student_skills.split(",")
        if skill.strip()
    )

    required_set = set(
        skill.strip().lower()
        for skill in required_skills.split(",")
        if skill.strip()
    )

    if len(required_set) == 0:
        return 0

    matched = student_set.intersection(required_set)

    return int((len(matched) / len(required_set)) * 100)

def auto_evaluate_application(user_id, internship_id):
    conn = get_db()

    user = conn.execute("""
        SELECT skills
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    internship = conn.execute("""
        SELECT skills
        FROM internships
        WHERE id = ?
    """, (internship_id,)).fetchone()

    quiz = conn.execute("""
        SELECT score
        FROM quiz_results
        WHERE user_id = ? AND internship_id = ?
        ORDER BY id DESC
    """, (
        user_id,
        internship_id
    )).fetchone()

    interview = conn.execute("""
        SELECT *
        FROM interviews
        WHERE user_id = ? AND internship_id = ?
    """, (
        user_id,
        internship_id
    )).fetchone()

    match = calculate_match(
        user["skills"] or "",
        internship["skills"] or ""
    )

    quiz_score = quiz["score"] if quiz else 0

    status = "Rejected"

    if match >= 60 and quiz_score >= 1 and interview:
        status = "Accepted"

    conn.execute("""
        UPDATE applications
        SET status = ?
        WHERE user_id = ? AND internship_id = ?
    """, (
        status,
        user_id,
        internship_id
    ))

    conn.commit()
    conn.close()

def evaluate_application(user_id, internship_id):
    conn = get_db()

    user = conn.execute("""
        SELECT skills
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    internship = conn.execute("""
        SELECT skills
        FROM internships
        WHERE id = ?
    """, (internship_id,)).fetchone()

    quiz = conn.execute("""
        SELECT score
        FROM quiz_results
        WHERE user_id = ? AND internship_id = ?
        ORDER BY id DESC
    """, (
        user_id,
        internship_id
    )).fetchone()

    interview = conn.execute("""
        SELECT *
        FROM interviews
        WHERE user_id = ? AND internship_id = ?
    """, (
        user_id,
        internship_id
    )).fetchone()

    match = calculate_match(
        user["skills"] or "",
        internship["skills"] or ""
    )

    quiz_score = quiz["score"] if quiz else 0

    status = "Rejected"

    if match >= 60 and quiz_score >= 1 and interview:
        status = "Accepted"

    conn.execute("""
        UPDATE applications
        SET status = ?
        WHERE user_id = ? AND internship_id = ?
    """, (
        status,
        user_id,
        internship_id
    ))

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

    def calculate_match(student_skills, required_skills):
        student_set = set(
        skill.strip().lower()
        for skill in student_skills.split(",")
        if skill.strip()
    )

    required_set = set(
        skill.strip().lower()
        for skill in required_skills.split(",")
        if skill.strip()
    )

    if len(required_set) == 0:
        return 0

    matched = student_set.intersection(required_set)

    return int((len(matched) / len(required_set)) * 100)


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            skills TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            description TEXT,
            skills TEXT,
            deadline TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            internship_id INTEGER,
            status TEXT DEFAULT 'Applied'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            internship_id INTEGER,
            question TEXT,
            option1 TEXT,
            option2 TEXT,
            option3 TEXT,
            option4 TEXT,
            answer TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            internship_id INTEGER,
            score INTEGER
        )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        internship_id INTEGER,
        question TEXT,
        answer TEXT
        )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        internship_id INTEGER,
        badge_name TEXT
    )
""")

    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        skills = request.form["skills"]

        conn = get_db()
        conn.execute(
    "INSERT INTO users (name, email, password, role, skills) VALUES (?, ?, ?, ?, ?)",
    (name, email, password, role, skills)
)
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    if session["role"] == "student":
        total_applications = conn.execute("""
            SELECT COUNT(*) as count
            FROM applications
            WHERE user_id = ?
        """, (session["user_id"],)).fetchone()["count"]

        total_badges = conn.execute("""
            SELECT COUNT(*) as count
            FROM badges
            WHERE user_id = ?
        """, (session["user_id"],)).fetchone()["count"]

        conn.close()

        return render_template(
            "dashboard.html",
            total_applications=total_applications,
            total_badges=total_badges
        )

    total_internships = conn.execute("""
        SELECT COUNT(*) as count
        FROM internships
    """).fetchone()["count"]

    total_applications = conn.execute("""
        SELECT COUNT(*) as count
        FROM applications
    """).fetchone()["count"]

    applicants = conn.execute("""
        SELECT users.name, users.email, internships.title, applications.status
        FROM applications
        JOIN users ON applications.user_id = users.id
        JOIN internships ON applications.internship_id = internships.id
        ORDER BY applications.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_internships=total_internships,
        total_applications=total_applications,
        applicants=applicants
    )

@app.route("/add_internship", methods=["GET", "POST"])
def add_internship():
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        company = request.form["company"]
        description = request.form["description"]
        skills = request.form["skills"]
        deadline = request.form["deadline"]

        conn = get_db()
        conn.execute("""
            INSERT INTO internships (title, company, description, skills, deadline)
            VALUES (?, ?, ?, ?, ?)
        """, (title, company, description, skills, deadline))
        conn.commit()
        conn.close()

        return redirect("/internships")

    return render_template("add_internship.html")


@app.route("/internships")
def internships():
    conn = get_db()
    data = conn.execute("SELECT * FROM internships").fetchall()

    internships_list = []
    student_skills = ""

    if "user_id" in session and session.get("role") == "student":
        user = conn.execute(
            "SELECT skills FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()

        if user:
            student_skills = user["skills"] or ""

    print("Student skills:", student_skills)

    for internship in data:
        match = None

        if student_skills.strip():
            match = calculate_match(
                student_skills,
                internship["skills"]
            )

        print("Internship skills:", internship["skills"])
        print("Match:", match)

        internships_list.append({
            "id": internship["id"],
            "title": internship["title"],
            "company": internship["company"],
            "description": internship["description"],
            "skills": internship["skills"],
            "deadline": internship["deadline"],
            "match": match
        })

    conn.close()

    return render_template(
        "internships.html",
        internships=internships_list
    )

@app.route("/apply/<int:id>")
def apply(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    existing = conn.execute("""
        SELECT * FROM applications
        WHERE user_id=? AND internship_id=?
    """, (session["user_id"], id)).fetchone()

    if not existing:
        conn.execute("""
            INSERT INTO applications (user_id, internship_id)
            VALUES (?, ?)
        """, (session["user_id"], id))
        conn.commit()

    conn.close()
    return redirect("/applications")


@app.route("/applications")
def applications():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    if session["role"] == "admin":
        data = conn.execute("""
            SELECT users.name, users.email, internships.title, applications.status
            FROM applications
            JOIN users ON applications.user_id = users.id
            JOIN internships ON applications.internship_id = internships.id
            ORDER BY applications.id DESC
        """).fetchall()

        conn.close()

        return render_template(
            "applications.html",
            applications=data
        )

    data = conn.execute("""
        SELECT internships.title, internships.company, applications.status
        FROM applications
        JOIN internships ON applications.internship_id = internships.id
        WHERE applications.user_id = ?
        ORDER BY applications.id DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "applications.html",
        applications=data
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/add_quiz/<int:internship_id>", methods=["GET", "POST"])
def add_quiz(internship_id):
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    if request.method == "POST":
        question = request.form.get("question")
        option1 = request.form.get("option1")
        option2 = request.form.get("option2")
        option3 = request.form.get("option3")
        option4 = request.form.get("option4")
        answer = request.form.get("answer")

        conn = get_db()

        conn.execute("""
            INSERT INTO quizzes (
                internship_id,
                question,
                option1,
                option2,
                option3,
                option4,
                answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            internship_id,
            question,
            option1,
            option2,
            option3,
            option4,
            answer
        ))

        conn.commit()
        conn.close()

        return redirect("/internships")

    return render_template(
        "add_quiz.html",
        internship_id=internship_id
    )


@app.route("/take_quiz/<int:internship_id>", methods=["GET", "POST"])
def take_quiz(internship_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    questions = conn.execute("""
        SELECT * FROM quizzes
        WHERE internship_id=?
    """, (internship_id,)).fetchall()

    if request.method == "POST":
        score = 0

        for q in questions:
            selected = request.form.get(str(q["id"]))

            if selected == q["answer"]:
                score += 1

        conn.execute("""
            INSERT INTO quiz_results (
                user_id,
                internship_id,
                score
            )
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            internship_id,
            score
        ))

        if score >= 1:
            existing_badge = conn.execute("""
                SELECT * FROM badges
                WHERE user_id=? AND internship_id=?
            """, (
                session["user_id"],
                internship_id
            )).fetchone()

            if not existing_badge:
                conn.execute("""
                    INSERT INTO badges (
                        user_id,
                        internship_id,
                        badge_name
                    )
                    VALUES (?, ?, ?)
                """, (
                    session["user_id"],
                    internship_id,
                    "Assessment Cleared"
                ))

        conn.commit()
        conn.close()

        auto_evaluate_application(
            session["user_id"],
            internship_id
        )

        return f"Quiz submitted. Your score: {score}"

    conn.close()

    return render_template(
        "take_quiz.html",
        questions=questions
    )

@app.route("/mock_interview/<int:internship_id>", methods=["GET", "POST"])
def mock_interview(internship_id):
    if "user_id" not in session:
        return redirect("/login")

    questions = [
        "Tell us about yourself.",
        "Why are you interested in this internship?",
        "What are your technical strengths?",
        "Describe a project you have worked on."
    ]

    if request.method == "POST":
        answers = []

        for index, question in enumerate(questions):
            answer = request.form.get(f"answer_{index}", "").strip()

            if not answer:
                return "Please answer all interview questions."

            answers.append((question, answer))

        conn = get_db()

        for question, answer in answers:
            conn.execute("""
                INSERT INTO interviews (
                    user_id,
                    internship_id,
                    question,
                    answer
                )
                VALUES (?, ?, ?, ?)
            """, (
                session["user_id"],
                internship_id,
                question,
                answer
            ))

        conn.commit()
        conn.close()

        auto_evaluate_application(
            session["user_id"],
            internship_id
        )

        return redirect("/applications")

    return render_template(
        "mock_interview.html",
        questions=questions
    )

@app.route("/badges")
def badges():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    data = conn.execute("""
        SELECT internships.title, badges.badge_name
        FROM badges
        JOIN internships
        ON badges.internship_id = internships.id
        WHERE badges.user_id = ?
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "badges.html",
        badges=data
    )
@app.route("/evaluate_application/<int:internship_id>")
def evaluate_application(internship_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    user = conn.execute("""
        SELECT skills
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    internship = conn.execute("""
        SELECT skills
        FROM internships
        WHERE id = ?
    """, (internship_id,)).fetchone()

    quiz = conn.execute("""
        SELECT score
        FROM quiz_results
        WHERE user_id = ? AND internship_id = ?
        ORDER BY id DESC
    """, (
        session["user_id"],
        internship_id
    )).fetchone()

    interview = conn.execute("""
        SELECT *
        FROM interviews
        WHERE user_id = ? AND internship_id = ?
    """, (
        session["user_id"],
        internship_id
    )).fetchone()

    match = calculate_match(
        user["skills"] or "",
        internship["skills"] or ""
    )

    quiz_score = quiz["score"] if quiz else 0

    status = "Under Review"

    if match >= 60 and quiz_score >= 1 and interview:
        status = "Accepted"

    conn.execute("""
        UPDATE applications
        SET status = ?
        WHERE user_id = ? AND internship_id = ?
    """, (
        status,
        session["user_id"],
        internship_id
    ))

    conn.commit()
    conn.close()

    return redirect("/applications")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)