from flask import *
import sqlite3

import matplotlib.pyplot as plt



# SQLite3 database file b
DATABASE = 'class_performance.db'

# Create tables if they don't exist
def create_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS gjrades")
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subjects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT ,class_id INTEGER,
    FOREIGN KEY (class_id) REFERENCES classes (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS grades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, subject_id INTEGER, score INTEGER ,class_id INTEGER,timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES classes (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    # Create the teachers table
    c.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        class_id INTEGER,
        FOREIGN KEY (class_id) REFERENCES classes(id)
    )
""")

    conn.commit()
    conn.close()
import secrets

# Generate a secure session key
session_key = secrets.token_hex(16)

print(session_key)
app.secret_key="Qwr@*Thsd?_^6yOe)"
# Login route

@app.route('/all_scores')
def all_scores():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Fetch all scores for all students
    c.execute("SELECT students.name, subjects.name, grades.score FROM students "
              "JOIN grades ON students.id = grades.student_id "
              "JOIN subjects ON subjects.id = grades.subject_id")

    scores = c.fetchall()

    conn.close()

    return render_template('all_scores.html', scores=scores)

@app.route('/teacher_login', methods=['GET', 'POST'])
def tlogin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Authenticate the teacher
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM teachers WHERE username = ? AND password = ?", (username, password))
        teacher = c.fetchone()
        conn.close()

        if teacher:
            session['teacher_id'] = teacher[0]
            session['class_id'] = teacher[3]
            return redirect(url_for('add_scores', teacher_id=session['teacher_id']))
        else:
            error = 'Invalid username or password.'
            return render_template('zeraki/teacher_login.html', error=error)
    else:
        return render_template('zeraki/teacher_login.html')
def get_student_performances(students, subjects):
    performances = []

    for student in students:
        student_performance = {
            'student_id': student[0],
            'name': student[1],
            'scores': []
        }

        for subject in subjects:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT score FROM grades WHERE student_id = ? AND subject_id = ?",
                      (student[0], subject[0]))
            score = c.fetchone()

            if score is not None:
                student_performance['scores'].append(score[0])
            else:
                student_performance['scores'].append(0)

        performances.append(student_performance)

    return performances
@app.route('/insert_scores', methods=['GET', 'POST'])
def insert_scores():
    teacher_id = session.get('teacher_id')
    class_id = session.get('class_id')

    if teacher_id and class_id:
        if request.method == 'POST':
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()

            c.execute("SELECT id, name FROM students WHERE class_id = ?", (class_id,))
            students = c.fetchall()

            c.execute("SELECT id, name FROM subjects WHERE class_id = ?", (class_id,))
            subjects = c.fetchall()

            # Create a set to store the unique student names
            unique_student_names = set()

            for student in students:
                unique_student_names.add(student[1])  # Add the student name to the set

            for student in students:
                for subject in subjects:
                    student_id = student[0]
                    subject_id = subject[0]
                    score_key = f"score_{student_id}_{subject_id}"
                    score = request.form.get(score_key)

                    # Check if the student name already exists in the set
                    if student[1] not in unique_student_names:
                        flash(f"Error: Duplicate entry for student name '{student[1]}'!")
                        return redirect(url_for('insert_scores'))

                    c.execute("INSERT INTO grades (student_id, subject_id, score, timestamp) VALUES (?, ?, ?, datetime('now'))",
                              (student_id, subject_id, score))

            conn.commit()
            conn.close()

            flash('Scores added successfully!')
            return redirect(url_for('insert_scores'))
        else:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()

            c.execute("SELECT id, name FROM students WHERE class_id = ?", (class_id,))
            students = c.fetchall()

            c.execute("SELECT id, name FROM subjects WHERE class_id = ?", (class_id,))
            subjects = c.fetchall()

            conn.close()

            return render_template('zeraki/insert_scores.html', students=students, subjects=subjects)
    else:
        return redirect(url_for('tlogin'))








    
# Registration routes



    
@app.route('/add_scores', methods=['GET', 'POST'])
def add_scores():
    teacher_id = session.get('teacher_id')
    class_id = session.get('class_id')

    if teacher_id and class_id:
        if request.method == 'POST':
            subject_scores = {}
            for subject_id in request.form:
                subject_scores[subject_id] = int(request.form[subject_id])

            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT id FROM students WHERE class_id = ?", (class_id,))
            student_ids = [row[0] for row in c.fetchall()]

            for student_id in student_ids:
                for subject_id, score in subject_scores.items():
                    c.execute("INSERT INTO grades (student_id, subject_id, score) VALUES (?, ?, ?)",
                              (student_id, subject_id, score))

            conn.commit()
            conn.close()

            flash('Scores added successfully!')
            return redirect(url_for('add_scores'))
        else:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT * FROM subjects")
            subjects = c.fetchall()

            c.execute("SELECT id, name FROM students WHERE class_id = ?", (class_id,))
            students = c.fetchall()

            conn.close()

            return render_template('zeraki/add_scores.html', subjects=subjects, students=students)
    else:
        return redirect(url_for('tlogin'))


# Teacher registration route
# Teacher registration route
@app.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        class_id = request.form['class_id']

        # Check if the teacher already exists in the database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM teachers WHERE username = ?", (username,))
        existing_teacher = c.fetchone()

        if existing_teacher:
            error = 'Teacher already exists with the provided username.'
            return render_template('zeraki/register_teacher.html', error=error)
        else:
            c.execute("INSERT INTO teachers (username, password, class_id) VALUES (?, ?, ?)", (username, password, class_id))
            conn.commit()
            conn.close()

            success_message = 'Teacher registered successfully!'
            return render_template('zeraki/register_teacher.html', success_message=success_message)
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM classes")
        classes = c.fetchall()
        conn.close()

        return render_template('zeraki/register_teacher.html', classes=classes)


# Student registration route
@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form['name']
        class_id = request.form['class_id']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO students (name, class_id) VALUES (?, ?)", (name, class_id))
        conn.commit()
        conn.close()

        success_message = 'Student registered successfully!'
        return render_template('zeraki/register_student.html', success_message=success_message)
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM classes")
        classes = c.fetchall()
        conn.close()

        return render_template('zeraki/register_student.html', classes=classes)


# Subject registration route
@app.route('/register_subject', methods=['GET', 'POST'])
def register_subject():
    if request.method == 'POST':
        class_id = session.get('class_id')
        if class_id:
            subject_name = request.form['subject_name']

            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO subjects (name, class_id) VALUES (?, ?)", (subject_name, class_id))
            conn.commit()
            conn.close()

            success_message = 'Subject registered successfully!'
            return render_template('zeraki/register_subject.html', success_message=success_message)
        else:
            return redirect(url_for('tlogin'))
    else:
        return render_template('zeraki/register_subject.html')


# Class registration route
@app.route('/register/class', methods=['GET', 'POST'])
def register_class():
    if request.method == 'POST':
        name = request.form['name']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO classes (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()

        success_message = 'Class registered successfully!'
        return render_template('zeraki/register_class.html', success_message=success_message)
    else:
        return render_template('zeraki/register_class.html')
@app.route('/student_scores')
def student_scores():
    teacher_id = session.get('teacher_id')
    class_id = session.get('class_id')

    if teacher_id and class_id:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        # Get students in the class
        c.execute("SELECT id, name FROM students WHERE class_id = ?", (class_id,))
        students = c.fetchall()

        # Get subjects for the class
        c.execute("SELECT id, name FROM subjects WHERE class_id = ?", (class_id,))
        subjects = c.fetchall()

        # Fetch scores per subject for each student
        student_performances = []
        for student in students:
            student_id = student[0]
            student_name = student[1]

            c.execute("SELECT score FROM grades WHERE student_id = ?", (student_id,))
            scores = c.fetchall()
            scores = [score[0] for score in scores if score[0] is not None]

            total_score = sum(scores)
            mean_score = total_score / len(scores) if len(scores) > 0 else 0
            mean_grade = calculate_grade(mean_score) if mean_score is not None else '-'

            student_scores = []
            for subject in subjects:
                subject_id = subject[0]

                c.execute("SELECT score FROM grades WHERE student_id = ? AND subject_id = ?", (student_id, subject_id))
                subject_score = c.fetchone()
                subject_score = subject_score[0] if subject_score is not None else None

                student_scores.append(subject_score)

            student_performances.append({
                'name': student_name,
                'total_score': total_score,
                'mean_score': mean_score,
                'mean_grade': mean_grade,
                'scores': student_scores
            })

        # Rank students based on mean score
        ranked_students = sorted(student_performances, key=lambda x: x['mean_score'], reverse=True)
        for i, student in enumerate(ranked_students):
            student['rank'] = i + 1

        # Calculate class mean score and grade
        class_mean_score = sum(student['mean_score'] for student in student_performances) / len(student_performances)
        class_mean_grade = calculate_grade(class_mean_score) if class_mean_score is not None else '-'

        conn.close()

        return render_template('zeraki/student_scores.html', ranked_students=ranked_students, class_mean_score=class_mean_score,
                               class_mean_grade=class_mean_grade, subjects=subjects ,calculate_grade=calculate_grade)
    else:
        return redirect(url_for('tlogin'))



def calculate_grade(score):
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
import datetime

@app.route('/get_scores_by_timestamp')
def get_scores_by_timestamp():
    class_id = session.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if class_id and start_date:
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        if end_date:
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

            # Get distinct timestamps within the specified date range
            c.execute("SELECT DISTINCT timestamp FROM grades WHERE timestamp BETWEEN ? AND ?", (start_date, end_date))
            timestamps = [timestamp[0] for timestamp in c.fetchall()]

        else:
            # Get scores for the specified date
            timestamps = [start_date]

        # Get subjects for the class
        c.execute("SELECT id, name FROM subjects WHERE class_id = ?", (class_id,))
        subjects = c.fetchall()

        # Get scores per subject for each timestamp
        scores = []
        for timestamp in timestamps:
            timestamp_scores = []
            for subject in subjects:
                subject_id = subject[0]

                c.execute("SELECT COALESCE(SUM(score), 0) FROM grades WHERE subject_id = ? AND DATE(timestamp) = ?", (subject_id, timestamp))
                score = [row[0] for row in c.fetchall()]

                timestamp_scores.append(score)

            scores.append(timestamp_scores)

        conn.close()

        return render_template('zeraki/scores_by_timestamp.html', subjects=subjects, timestamps=timestamps, scores=scores)

    return jsonify(error='Invalid parameters')




