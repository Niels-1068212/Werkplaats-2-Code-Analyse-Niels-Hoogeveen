from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    g,
    send_file,
)
import os
from lib.MVC import TestgptNotesModel
from sqlite3 import IntegrityError
from werkzeug.security import check_password_hash
import functools
from lib.testgpt import TestGPT
import csv
import uuid

RANDOM_KEY = str(uuid.uuid4())
currentdirectory = os.path.dirname(os.path.abspath(__file__))
application = Flask(__name__)
application.secret_key = RANDOM_KEY
DB_FILE = "databases/testgpt.db"
template_location = "templates"
MODEL = TestgptNotesModel(DB_FILE)
default_notes_page = {"current_page": 1}
default_admin_page = {"current_page": 1}
filters = {
    "category": "",
    "questions": "",
    "search": "",
    "all_teachers": "",
}

# redirect user if they are not logged in
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect("/login")

        return view(**kwargs)

    return wrapped_view

# redirects user if they are not an admin
def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user["is_admin"] == 0:
            return redirect("/")

        return view(**kwargs)

    return wrapped_view

# Allows admins to register new users
@application.route("/register", methods=("GET", "POST"))
@login_required
@admin_required
def register_teacher():
    if request.method == "POST":
        username = request.form["username"]
        display_name = request.form["display_name"]
        password = request.form["password"]
        admin_check = request.form["is_admin"]
        error = None

        if not username:
            error = "Gebruikersnaam is benodigd."
        elif not display_name:
            error = "Display-naam is benodigd."
        elif not password:
            error = "Wachtwoord is benodigd."

        if admin_check == "True":
            is_admin = 1
        else:
            is_admin = 0

        if error is None:
            try:
                MODEL.set_register_data(
                    username,
                    display_name,
                    password,
                    is_admin
                    )
            except IntegrityError:
                error = f"Gebruiker {username} is al geregistreerd."
            else:
                return redirect("/admin_panel")

        flash(error)

    return render_template("auth/register.html")

# Allows a user to log in
@application.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None
        user = MODEL.get_user_data(username)

        if user is None:
            error = "Incorrecte gebruikersnaam."
        elif not check_password_hash(user["teacher_password"], password):
            error = "Incorrect wachtwoord."

        if error is None:
            session.clear()
            session["user_id"] = user["teacher_id"]
            return redirect("/")

        flash(error)

    return render_template("auth/login.html")

# Checks if there is a user in the session and gets their data.
@application.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = MODEL.get_current_user_data(user_id)

# Checks if the current page is less then 1 or more then the max pages
# And sets them back to min and max respectively
def current_page(default_page, total_pages):
    if default_page["current_page"] < 1:
        default_page["current_page"] = 1

    if default_page["current_page"] > total_pages:
        default_page["current_page"] = total_pages

    return default_page

# Admin that shows other user and allows admin to edit, delete and add users
@application.route("/adminpanel", methods=["GET", "POST"])
@login_required
@admin_required
def admin_panel():
    page_length = 20

    data_teachers = []
    data_teachers_per_page = []
    non_user_notes = MODEL.get_teacher_data(g.user["teacher_id"])

    for row in non_user_notes:
        data_teachers.append(row)

    total_teachers = len(data_teachers)
    if (total_teachers % page_length) == 0:
        total_pages = total_teachers // page_length
    else:
        total_pages = (total_teachers // page_length) + (
            (total_teachers % page_length) > False
        )

    page = current_page(default_admin_page, total_pages)
    if request.method == "POST":
        page_change = request.form
        if "forward" in page_change.keys():
            page["current_page"] = (
                page["current_page"] + int(page_change["forward"])
            )
            return redirect("/adminpanel")
        elif "back" in page_change.keys():
            page["current_page"] = (
                page["current_page"] + int(page_change["back"])
            )
            return redirect("/adminpanel")

    last_teacher_per_page = page_length * page["current_page"]
    first_teacher_per_page = last_teacher_per_page - page_length
    for row in range(first_teacher_per_page, last_teacher_per_page):
        try:
            data_teachers_per_page.append(data_teachers[row])
        except IndexError:
            break

    return render_template(
        "auth/adminoverview.html",
        data_notes=data_teachers_per_page,
        page=page["current_page"],
        total_pages=total_pages,
    )

# Main page with notes list and filter system and
@application.route("/", methods=["GET", "POST"])
@login_required
def index():
    page_length = 20
    data_notes = []
    data_notes_per_page = []

    if request.method == "POST":
        if "clear_filter" in request.form.keys():
            filter_category = ""
            filters["category"] = filter_category
            filter_questions = ""
            filters["questions"] = filter_questions
            filter_search = ""
            filters["search"] = filter_search
            filters["all_teachers"] = ""
        else:
            if "chosen_category" in request.form.keys():
                if (request.form["chosen_category"]) != "":
                    chosen_category = request.form["chosen_category"]
                    filter_category = MODEL.category_filter(chosen_category)
                    filters["category"] = chosen_category
                else:
                    filter_category = ""
                    filters["category"] = filter_category
            elif filters["category"] != "":
                filter_category = MODEL.category_filter(filters["category"])
            else:
                filter_category = ""

            if "questions" in request.form.keys():
                if request.form.get("questions") != "":
                    questions = request.form["questions"]
                    filter_questions = MODEL.questions_filter(questions)
                    filters["questions"] = questions
                else:
                    filter_questions = ""
                    filters["questions"] = filter_questions
            elif filters["questions"] != "":
                filter_questions = MODEL.questions_filter(filters["questions"])
            else:
                filter_questions = ""

            if "search" in request.form.keys():
                if request.form.get("search") != "":
                    search_words = request.form["search"]
                    filter_search = MODEL.search_filter(search_words)
                    filters["search"] = search_words
                else:
                    filter_search = ""
                    filters["search"] = filter_search
            elif filters["search"] != "":
                filter_search = MODEL.search_filter(filters["search"])
            else:
                filter_search = ""

            if "all_teachers" in request.form.keys():
                filters["all_teachers"] = True
            elif (
                "forward" not in request.form.keys()
                and "back" not in request.form.keys()
            ):
                filters["all_teachers"] = ""
    else:
        chosen_category = filters["category"]
        questions = filters["questions"]
        search_words = filters["search"]

        if chosen_category == "" or None:
            filter_category = ""
        else:
            filter_category = MODEL.category_filter(chosen_category)

        if questions == "" or None:
            filter_questions = ""
        else:
            filter_questions = MODEL.questions_filter(questions)

        if search_words == "" or None:
            filter_search = ""
        else:
            filter_search = MODEL.search_filter(search_words)

    category = MODEL.get_categories()

    result_notes_user = MODEL.filter_query_user(
        g.user["teacher_id"], filter_category, filter_questions, filter_search
    )

    for row in result_notes_user:
        data_notes.append(row)

    if filters["all_teachers"] is True:
        if g.user["is_admin"] == 1:
            filter_public = MODEL.public_filter()
        else:
            filter_public = ""

        result_notes_non_user = MODEL.filter_query_non_user(
            g.user["teacher_id"],
            filter_category,
            filter_questions,
            filter_search,
            filter_public,
        )

        for row in result_notes_non_user:
            data_notes.append(row)

    total_notes = len(data_notes)
    if (total_notes % page_length) == 0:
        total_pages = total_notes // page_length
    else:
        total_pages = (total_notes // page_length) + (
            (total_notes % page_length) > False
        )

    page = current_page(default_notes_page, total_pages)
    if request.method == "POST":
        page_change = request.form
        if "forward" in page_change.keys():
            page["current_page"] = (
                page["current_page"] + int(page_change["forward"])
            )
            return redirect("/")
        elif "back" in page_change.keys():
            page["current_page"] = page["current_page"] + int(page_change["back"])
            return redirect("/")

    last_note_per_page = page_length * page["current_page"]
    first_note_per_page = last_note_per_page - page_length
    for row in range(first_note_per_page, last_note_per_page):
        try:
            data_notes_per_page.append(data_notes[row])
        except IndexError:
            break

    return render_template(
        "overviewnotes.html.jinja",
        data_notes=data_notes_per_page,
        category=category,
        filter=filters,
        page=page["current_page"],
        total_pages=total_pages,
    )

# Log out user by removing the user from the session
@application.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Exports a list of selected notes to csv format
@application.route("/export", methods=("GET", "POST"))
@login_required
def export_notes():
    if request.method == "POST":
        note_id = request.form.getlist("select")
        data_notes = []
        csv_path = currentdirectory + "/notes.csv"

        for note in note_id:
            result = MODEL.get_note_data(note)
            data_notes.append(result)

        with open(csv_path, mode="w", newline="") as file:
            writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["Display Naam", "Title", "Categorie", "Text"])
            for row in data_notes:
                writer.writerow([row["display_name"], row["title"], row["category_name"], row["text"]])

        return send_file(csv_path, mimetype="text/csv", download_name="notes.csv", as_attachment=True)

    return redirect("/")


@application.route("/viewnote/<note_id>/open_question")
@login_required
def open_question(note_id):
    note_content = MODEL.get_note(note_id)
    note = note_content["note"]
    test_gpt = TestGPT()

    generated_question = test_gpt.generate_open_question(note)
    prompt = "Vraag:" + " " + generated_question + " " + "Notitie:" + " " + note
    generated_answer = test_gpt.generate_open_answer(prompt)

    MODEL.add_question(note_id, generated_question, generated_answer)
    return redirect(f"/viewnote/{note_id}")


@application.route("/viewnote/<note_id>/multiple_choice_question")
@login_required
def multiple_choice_question(note_id):
    note_content = MODEL.get_note(note_id)
    note = note_content["note"]
    test_gpt = TestGPT()

    generated_question = test_gpt.generate_multiple_choice_question(note)
    prompt = "Vraag:" + " " + generated_question + " " + "Notitie:" + " " + note
    generated_answer = test_gpt.generate_multiple_answer(prompt)

    MODEL.add_question(note_id, generated_question, generated_answer)
    return redirect(f"/viewnote/{note_id}")


@application.route("/editquestion/<questions_id>/open_answer")
@login_required
def open_answer(questions_id):
    question = MODEL.get_question(questions_id)["exam_question"]
    note_id = MODEL.get_question(questions_id)["note_id"]
    note = MODEL.get_note(note_id)["note"]

    prompt = "Vraag:" + " " + question + " " + "Notitie:" + " " + note

    test_gpt = TestGPT()
    generated_answer = test_gpt.generate_open_answer(prompt)

    MODEL.add_answer(questions_id, generated_answer)
    return redirect(f"/editquestion/{questions_id}")


@application.route("/editquestion/<questions_id>/multiple_choice_answer")
@login_required
def multiple_choice_answer(questions_id):
    question = MODEL.get_question(questions_id)["exam_question"]
    note_id = MODEL.get_question(questions_id)["note_id"]
    note = MODEL.get_note(note_id)["note"]

    prompt = "Vraag:" + " " + question + " " + "Notitie:" + " " + note

    test_gpt = TestGPT()
    generated_answer = test_gpt.generate_multiple_answer(prompt)

    MODEL.add_answer(questions_id, generated_answer)
    return redirect(f"/editquestion/{questions_id}")


@application.route("/deletenote/<note_id>", methods=["POST"])
@login_required
def deletenote(note_id):
    MODEL.delete_note(note_id)
    return redirect(url_for("index"))


@application.route("/deletequestion/<questions_id>", methods=["POST", "GET"])
@login_required
def deletequestion(questions_id):
    note_id = MODEL.get_note_id(questions_id)
    note_id_str = str(note_id[0])

    MODEL.delete_question(questions_id)
    return redirect(f"/viewnote/{note_id_str}")


@application.route("/viewteacher/<teacher_id>", methods=["POST", "GET"])
@login_required
def edit_teacher(teacher_id):
    row = MODEL.view_teacher(teacher_id)
    changes = request.form
    if request.method == "POST":
        if changes["username"] != "":
            MODEL.edit_teacher_username(changes["username"], teacher_id)

        if changes["password"] != "":
            MODEL.edit_teacher_password(changes["password"], teacher_id)

        if changes["display_name"] != "":
            MODEL.edit_teacher_display_name(
                changes["display_name"],
                teacher_id
            )

        return redirect(url_for("edit_teacher", teacher_id=teacher_id))
    return render_template("auth/editteacher.html.jinja", rows=row)


@application.route("/deleteteacher/<int:teacher_id>", methods=["POST", "GET"])
@login_required
@admin_required
def deleteteacher(teacher_id):
    MODEL.delete_teacher(teacher_id)
    return redirect(url_for("admin_panel"))


@application.route("/logout", endpoint="user_logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")


@application.route("/notesubmitted/<teacher_id>")
def viewnote_submitted(teacher_id):
    row = MODEL.view_latest_note(teacher_id)
    return render_template("viewnote.html.jinja", rows=row)


@application.route("/download_csv", methods=["GET", "POST"])
def download_csv():
    data_notes = session.get("current_data_notes", [])

    column_names = [
        "Titel",
        "Notitie",
        "Bron",
        "Categorie",
        "Vragen",
        "Leraar",
        "Datum",
    ]

    with open("test-correct-notes.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_names)
        writer.writeheader()

        for data_note in data_notes:
            dict_data = {
                "Titel": data_note.get("title", ""),
                "Notitie": data_note.get("note", ""),
                "Bron": data_note.get("note_source", ""),
                "Categorie": data_note.get("display_name", ""),
                "Vragen": data_note.get("question", ""),
                "Leraar": data_note.get("display_name", ""),
                "Datum": data_note.get("date_created", ""),
            }
            writer.writerow(dict_data)

    return send_file(
        "test-correct-notes.csv",
        mimetype="text/csv",
        as_attachment=True,
        download_name="test-correct.csv",
    )


@application.route("/download_csv/<uuid:note_id>", methods=["GET", "POST"])
def download_csv_questions(note_id):
    data_notes = MODEL.get_questions(str(note_id))

    column_names = [
        "exam_question",
        "exam_answer",
    ]

    with open("test-correct-questions.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_names)
        writer.writeheader()

        for data_note in data_notes:
            dict_data = {
                "exam_question": data_note.get("exam_question", ""),
                "exam_answer": data_note.get("exam_answer", ""),
            }
            writer.writerow(dict_data)

    return send_file(
        "test-correct-questions.csv",
        mimetype="text/csv",
        as_attachment=True,
        download_name="test-correct-questions.csv",
    )


def run_application(application):
    if __name__ == "__main__":
        application.run(debug=True)


run_application(application)
