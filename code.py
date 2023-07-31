from flask import Flask, render_template, request, redirect
import time

def convert_time(duration_minutes):
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    return f"{hours} hours {minutes} minutes"

app = Flask(__name__)

class Test:
    def __init__(self, test_name, duration_minutes, num_choices):
        self.test_name = test_name
        self.questions = []
        self.questions_points = {}
        self.total_points = 0
        self.duration_minutes = duration_minutes
        self.start_time = None
        self.allowed_users = []
        self.num_choices = num_choices

    def add_question(self, question):
        self.questions.append(question)

class Question:
    def __init__(self, question, answer, question_type, points, choices=None):
        self.question = question
        self.answer = answer
        self.question_type = question_type
        self.points = points
        self.choices = choices

tests = []
students = {}

passing_percentage = 60
total_points_for_test = 0

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in students and students[username] == password:
            return redirect(f"/student/{username}/tests")
        elif username == "admin" and password == "adminpass":
            return redirect("/admin")
        else:
            error = "Invalid username or password"
            return render_template("login.html", error=error)

    return render_template("login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    global passing_percentage, total_points_for_test
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create_user":
            username = request.form["username"]
            password = request.form["password"]
            students[username] = password

        elif action == "create_test":
            test_name = request.form["test_name"]
            duration_minutes = int(request.form["duration_minutes"])
            num_choices = int(request.form["num_choices"])
            test = Test(test_name, duration_minutes, num_choices)
            tests.append(test)
            # Oppretter en kobling mellom test og student
            for student in students.values():
                student.tests.append(test)

        elif action == "set_passing_percentage":
            passing_percentage = int(request.form["passing_percentage"])
            total_points_for_test = int(request.form["total_points_for_test"])

    return render_template("admin.html", tests=tests, students=students, passing_percentage=passing_percentage, total_points_for_test=total_points_for_test)

@app.route("/admin/<test_name>", methods=["GET", "POST"])
def admin_test(test_name):
    test = None
    for t in tests:
        if t.test_name == test_name:
            test = t
            break

    if test is None:
        return "Test not found", 404

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_question":
            question_text = request.form["question"]
            answer_text = request.form["answer"]
            question_type = request.form["question_type"]
            points = int(request.form["points"])
            choices = None
            if question_type == "multiple_choice":
                choices = [request.form[f"choice_{i}"] for i in range(1, test.num_choices + 1)]

            question = Question(question_text, answer_text, question_type, points, choices)
            test.add_question(question)

    return render_template("admin_test.html", test=test)

@app.route("/student/<username>/tests", methods=["GET", "POST"])
def student_tests(username):
    test_to_take = None
    for test in tests:
        if test.test_name == username:
            test_to_take = test
            break

    if test_to_take is None:
        return "Test not found", 404

    return render_template("student_test.html", tests=tests)

@app.route("/student/<username>/take_test/<test_name>", methods=["GET", "POST"])
def student_take_test(username, test_name):
    test_to_take = None
    for test in tests:
        if test.test_name == test_name:
            test_to_take = test
            break

    if test_to_take is None:
        return "Test not found", 404

    remaining_time = None
    if request.method == "POST":
        if test_to_take.start_time is None:
            test_to_take.start_time = time.time()

        elapsed_time = time.time() - test_to_take.start_time
        remaining_time = test_to_take.duration_minutes * 60 - elapsed_time
        if remaining_time <= 0:
            return redirect(f"/result/{username}")

        for i, question in enumerate(test_to_take.questions):
            user_answer = request.form.get(f"answer_{i}")
            if user_answer == question.answer:
                test_to_take.questions_points[i] = question.points
                test_to_take.total_points += question.points

    return render_template("user_test.html", username=username, test_name=test_to_take.test_name, questions=test_to_take.questions, remaining_time=convert_time(int(remaining_time)), passing_percentage=passing_percentage, total_points_for_test=total_points_for_test)

@app.route("/result/<username>")
def result(username):
    test_result = None
    for test in tests:
        if test.test_name == username:
            test_result = test
            break

    if test_result is None:
        return "Test not found", 404

    percentage = (test_result.total_points / total_points_for_test) * 100
    is_passed = percentage >= passing_percentage

    return render_template("user_result.html", test_name=username, total_points=test_result.total_points, percentage=percentage, is_passed=is_passed, questions_answers=test_result.questions)

if __name__ == "__main__":
    app.run(debug=True)
