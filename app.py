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
        # Gets the data from the form
        username = request.form["username"]
        display_name = request.form["display_name"]
        password = request.form["password"]
        admin_check = request.form["is_admin"]
        error = None

        # Checks if it any are empty
        if not username:
            error = "Gebruikersnaam is benodigd."
        elif not display_name:
            error = "Display-naam is benodigd."
        elif not password:
            error = "Wachtwoord is benodigd."

        # Check is the is admin check box was checked
        if admin_check == "True":
            is_admin = 1
        else:
            is_admin = 0

        # Sent the submitted data to the model to have it sent to the server
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
        # Get username and password from use input
        username = request.form["username"]
        password = request.form["password"]
        error = None
        user = MODEL.get_user_data(username)

        # checks if username exist and if password matches with it
        if user is None:
            error = "Incorrecte gebruikersnaam."
        elif not check_password_hash(user["teacher_password"], password):
            error = "Incorrect wachtwoord."

        # If username and password match, it put the user in a session
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

    # Gets the teachers data from the model to send to the webpage
    data_teachers = []
    data_teachers_per_page = []
    non_user_notes = MODEL.get_teacher_data(g.user["teacher_id"])

    for row in non_user_notes:
        data_teachers.append(row)

    # Determents total amount of pages based on the total amount of notes
    total_teachers = len(data_teachers)
    if (total_teachers % page_length) == 0:
        total_pages = total_teachers // page_length
    else:
        total_pages = (total_teachers // page_length) + (
            (total_teachers % page_length) > False
        )

    # Switches the page after user input
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

    # Determents what teachers to show per page
    last_teacher_per_page = page_length * page["current_page"]
    first_teacher_per_page = last_teacher_per_page - page_length
    for row in range(first_teacher_per_page, last_teacher_per_page):
        try:
            data_teachers_per_page.append(data_teachers[row])
        except IndexError:
            break

    # Sents data to webpage
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

    # Filter system which filter based on the catagory, question or not
    # and input text from user.
    if request.method == "POST":
        # Clears current filter
        if "clear_filter" in request.form.keys():
            filter_category = ""
            filters["category"] = filter_category
            filter_questions = ""
            filters["questions"] = filter_questions
            filter_search = ""
            filters["search"] = filter_search
            filters["all_teachers"] = ""
        else:
            # Checks if filter based on chosen category form list is empty
            # if not sets filter to that category
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

            # Checks if filter based on if a question
            # has generated questions or not, is empty
            # if not sets filter to result
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

            # Checks if search query is empty
            # and if not set filter to the search query
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

            # Check if show from all check is checked
            if "all_teachers" in request.form.keys():
                filters["all_teachers"] = True
            elif (
                "forward" not in request.form.keys()
                and "back" not in request.form.keys()
            ):
                filters["all_teachers"] = ""
    else:
        # Remebers filters incase of page turn or navigating away and back
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

    # Gets the categories to be used in dropdown list on the webpage
    category = MODEL.get_categories()

    # Gets the notes data from the current user from the model
    # to send to the webpage
    result_notes_user = MODEL.filter_query_user(
        g.user["teacher_id"], filter_category, filter_questions, filter_search
    )

    for row in result_notes_user:
        data_notes.append(row)

    # Gets the notes data from the non user from the model to send
    # to the webpage
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

    # Determents total amount of pages based on the total amount of notes
    total_notes = len(data_notes)
    if (total_notes % page_length) == 0:
        total_pages = total_notes // page_length
    else:
        total_pages = (total_notes // page_length) + (
            (total_notes % page_length) > False
        )

    # Switches the page after user input
    page = current_page(default_notes_page, total_pages)
    if request.method == "POST":
        page_change = request.form
        if "forward" in page_change.keys():
            page["current_page"] = (
                page["current_page"] + int(page_change["forward"])
            )
            return redirect("/")
        elif "back" in page_change.keys():
            page["current_page"] = (
                page["current_page"] + int(page_change["back"])
            )
            return redirect("/")
        else:
            page["current_page"] = 1

    # Determents what notes to show per page
    last_note_per_page = page_length * page["current_page"]
    first_note_per_page = last_note_per_page - page_length
    for row in range(first_note_per_page, last_note_per_page):
        try:
            data_notes_per_page.append(data_notes[row])
        except IndexError:
            break

    # Makes a dict for dataconvertion purposes in overview notes
    string_category = {}
    for row in category:
        string_category[row["category_id"]] = str(row["category_id"])

    # Sets up data for to download as an CVS file
    dict_filter_category = [dict(row) for row in data_notes_per_page]
    session["current_data_notes"] = dict_filter_category
    note_id = str(uuid.uuid4())

    # Sents data to webpage
    return render_template(
        "overviewnotes.html.jinja",
        data_notes=data_notes_per_page,
        page=page["current_page"],
        total_pages=total_pages,
        categories=category,
        string_category=string_category,
        filters=filters,
        note_id=note_id,
    )


@application.route("/newnote", methods=["GET", "POST"])
@login_required
def newnote():
    if request.method == "GET":
        # Get categories for dropdown menu
        categories = MODEL.get_categories()
        return render_template("newnote.html.jinja", categories=categories)
    elif request.method == "POST":
        # Add note to database and link the teacher
        MODEL.draw_form(g.user["teacher_id"])
        teacher = g.user["teacher_id"]
        return redirect(f"/notesubmitted/{teacher}")


@application.route("/viewnote/<uuid:note_id>")
@login_required
def viewnote(note_id):
    # Get note information
    row = MODEL.view_single_note(str(note_id))
    # Get all questions for the note
    gen_que = MODEL.get_questions(str(note_id))
    return render_template("viewnote.html.jinja", rows=row, gen_que=gen_que)


@application.route("/editnote/<uuid:note_id>", methods=["GET"])
@login_required
def editnote(note_id):
    # Get all data to put it inside the forms
    note_content = MODEL.get_note(str(note_id))
    categories = MODEL.get_categories()
    gen_que = MODEL.get_questions(str(note_id))
    return render_template(
        "editnote.html.jinja",
        notes=note_content,
        categories=categories,
        gen_que=gen_que,
    )


@application.route("/editnote/<uuid:note_id>", methods=["POST"])
@login_required
def editnotes(note_id):
    # Save note redirect to the view note page
    MODEL.edit_note(str(note_id))
    return redirect(f"/viewnote/{note_id}")


@application.route("/editquestion/<questions_id>", methods=["GET"])
@login_required
def edit_question_get(questions_id):
    # Get data for questions form
    question = MODEL.get_single_question(questions_id)
    return render_template(
        "edit_question_answer.html.jinja",
        question=question
        )


@application.route("/editquestion/<question_id>", methods=["POST"])
@login_required
def edit_question_post(question_id):
    # Update saved question to database
    MODEL.edit_question(str(question_id))
    # Get the note id from the question
    # so you can redirect to the edit-note page.
    note_id = MODEL.get_note_id(question_id)
    note_id_str = str(note_id[0])
    return redirect(f"/editnote/{note_id_str}")


@application.route("/viewnote/<note_id>/open_question")
@login_required
def open_question(note_id):
    note_content = MODEL.get_note(note_id)
    note = note_content["note"]
    test_gpt = TestGPT()

    # generate the open question
    generated_question = test_gpt.generate_open_question(note)

    # add the note and question to each other
    prompt = (
        "Vraag:" + " " + generated_question + " " + "Notitie:" + " " + note
    )

    # generate open answer based on the new generated question and note
    generated_answer = test_gpt.generate_open_answer(prompt)

    # add question to database and get all questions
    MODEL.add_question(note_id, generated_question, generated_answer)
    return redirect(f"/viewnote/{note_id}")


@application.route("/viewnote/<note_id>/multiple_choice_question")
@login_required
def multiple_choice_question(note_id):
    note_content = MODEL.get_note(note_id)
    note = note_content["note"]
    test_gpt = TestGPT()

    # generate the multiple choice question
    generated_question = test_gpt.generate_multiple_choice_question(note)

    # add the note and question to each other
    prompt = (
        "Vraag:" + " " + generated_question + " " + "Notitie:" + " " + note
    )

    # generate multiple choice answer based
    # on the new generated question and note
    generated_answer = test_gpt.generate_multiple_answer(prompt)

    # add question to database and get all questions
    MODEL.add_question(note_id, generated_question, generated_answer)
    return redirect(f"/viewnote/{note_id}")


@application.route("/editquestion/<questions_id>/open_answer")
@login_required
def open_answer(questions_id):
    # get question and note data
    question = MODEL.get_question(questions_id)["exam_question"]
    note_id = MODEL.get_question(questions_id)["note_id"]
    note = MODEL.get_note(note_id)["note"]

    # add question and note next to each other
    prompt = "Vraag:" + " " + question + " " + "Notitie:" + " " + note

    # generate open answer
    test_gpt = TestGPT()
    generated_answer = test_gpt.generate_open_answer(prompt)

    # rewrite answer in database
    MODEL.add_answer(questions_id, generated_answer)
    return redirect(f"/editquestion/{questions_id}")


@application.route("/editquestion/<questions_id>/multiple_choice_answer")
@login_required
def multiple_choice_answer(questions_id):
    # get question and note data
    question = MODEL.get_question(questions_id)["exam_question"]
    note_id = MODEL.get_question(questions_id)["note_id"]
    note = MODEL.get_note(note_id)["note"]

    # add question and note next to each other
    prompt = "Vraag:" + " " + question + " " + "Notitie:" + " " + note

    # generate multiple choise answer
    test_gpt = TestGPT()
    generated_answer = test_gpt.generate_multiple_answer(prompt)

    # add answer to database
    MODEL.add_answer(questions_id, generated_answer)
    return redirect(f"/editquestion/{questions_id}")


@application.route("/deletenote/<note_id>", methods=["POST"])
@login_required
def deletenote(note_id):
    # delete note from database with note_id
    MODEL.delete_note(note_id)
    return redirect(url_for("index"))


@application.route("/deletequestion/<questions_id>", methods=["POST", "GET"])
@login_required
def deletequestion(questions_id):
    # get note_id for the redirect
    note_id = MODEL.get_note_id(questions_id)
    note_id_str = str(note_id[0])

    # delete question from the database
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


# Clears user from session and redirect them to the login page.
@application.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")


# when the note is submitted redirect to this page and
# see the latest note that the teacher added
@application.route("/notesubmitted/<teacher_id>")
def viewnote_submitted(teacher_id):
    row = MODEL.view_latest_note(teacher_id)
    return render_template("viewnote.html.jinja", rows=row)


@application.route("/download_csv", methods=["GET", "POST"])
def download_csv():
    # get data from the rows
    data_notes = session.get("current_data_notes", [])

    # add titles to the columns
    column_names = [
        "Titel",
        "Notitie",
        "Bron",
        "Categorie",
        "Vragen",
        "Leraar",
        "Datum",
    ]

    # write csv and put the session data inside
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

    # send the file to the user so they can download it
    return send_file(
        "test-correct-notes.csv",
        mimetype="text/csv",
        as_attachment=True,
        download_name="test-correct.csv",
    )


# Allows user to download the question and answer of a related note.
@application.route("/download_csv/<uuid:note_id>", methods=["GET", "POST"])
def download_csv_questions(note_id):

    # Gets data from selected note
    data_notes = MODEL.get_questions(str(note_id))

    # Adds names to the columns
    column_names = [
        "exam_question",
        "exam_answer",
    ]

    # Opens CSV file and writes data into it
    with open("test-correct-questions.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_names)
        writer.writeheader()

        for data_note in data_notes:
            dict_data = {
                "exam_question": data_note.get("exam_question", ""),
                "exam_answer": data_note.get("exam_answer", ""),
            }
            writer.writerow(dict_data)

    # Sends filled CSV to the user through the webpage
    return send_file(
        "test-correct-questions.csv",
        mimetype="text/csv",
        as_attachment=True,
        download_name="test-correct-questions.csv",
    )


# Starts application
def run_application(application):
    if __name__ == "__main__":
        application.run(debug=True)


run_application(application)
