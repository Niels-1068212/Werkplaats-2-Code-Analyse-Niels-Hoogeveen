import sqlite3
from pathlib import Path
from flask import request
from werkzeug.security import generate_password_hash
import uuid


class TestgptNotesModel:
    def __init__(self, db_file):
        db_path = Path(db_file)
        if not db_path.exists():
            raise FileNotFoundError(f"Database file {db_file} does not exist")
        self.dbpath = db_path

    def __get_connection(self):
        connection = sqlite3.connect(self.dbpath)
        return connection

    def __get_cursor(self):
        connection = self.__get_connection()
        cursor = connection.cursor()
        cursor.row_factory = sqlite3.Row
        return cursor

    def set_register_data(self, username, display_name, password, is_admin):
        connection = self.__get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO teachers (username,
                                  display_name,
                                  teacher_password,
                                  is_admin)
            VALUES (?, ?, ?, ?)""",
            (username,
             display_name,
             generate_password_hash(password),
             is_admin,),
        )
        connection.commit()
        connection.close()

    def get_user_data(self, username):
        cursor = self.__get_cursor()
        cursor.execute(
            """
            SELECT * FROM teachers WHERE username = ?
            """,
            (username,),
        )
        return cursor.fetchone()

    def get_current_user_data(self, user_id):
        cursor = self.__get_cursor()
        cursor.execute("""SELECT
                        teachers.teacher_id,
                        teachers.display_name,
                        teachers.username,
                        teachers.is_admin
                       FROM teachers
                       WHERE teacher_id = ?""",
                       (user_id,))
        return cursor.fetchone()

    def get_teacher_data(self, user_id):
        cursor = self.__get_cursor()
        cursor.execute(
            """
            SELECT  teachers.teacher_id,
                    teachers.display_name,
                    teachers.username,
                    teachers.date_created
            FROM teachers
            WHERE teacher_id <> ?""",
            (user_id,),
        )
        return cursor.fetchall()

    def view_teacher(self, teacher_id):
        cursor = self.__get_cursor()
        cursor.execute(
            """
            SELECT  teachers.teacher_id,
                    teachers.display_name,
                    teachers.username,
                    teachers.date_created
            FROM teachers
            WHERE teacher_id = ?""",
            (teacher_id,),
        )
        return cursor.fetchone()

    def draw_form(self, user_id):
        conn = self.__get_connection()
        newnotetitle = request.form["formtitle"]
        newnotenote = request.form["formnote"]
        newnotesource = request.form["formsource"]
        newnoteteacherid = user_id
        newnotecategoryid = request.form["formcategoryid"]
        newnoteid = str(uuid.uuid4())

        # set values from on / off to 1 and 0
        if "formpublic" in request.form:
            getpublic = request.form["formpublic"]
            if getpublic == "off":
                newnotepublic = 0
            else:
                newnotepublic = 1
        else:
            newnotepublic = 0

        # causes the first 20 words to be used for the title if there isn't one
        if not newnotetitle:
            newnotetitle = " ".join(newnotenote.split()[:20])

        query = conn.cursor()
        query.execute(
            """
            INSERT INTO notes
                ('note_id',
                    'title',
                    'note',
                    'note_source',
                    'is_public',
                    'teacher_id',
                    'category_id')
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                newnoteid,
                newnotetitle,
                newnotenote,
                newnotesource,
                newnotepublic,
                newnoteteacherid,
                newnotecategoryid,
            ),
        )
        conn.commit()
        conn.close()

    def view_single_note(self, note_id):
        conn = sqlite3.connect(self.dbpath)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT  teachers.display_name,
                    categories.omschrijving,
                    *
            FROM notes
            JOIN categories ON notes.category_id = categories.category_id
            JOIN teachers ON notes.teacher_id = teachers.teacher_id
            WHERE note_id = ?""",
            (note_id,),
        )
        return cursor.fetchone()

    def get_categories(self):
        conn = sqlite3.connect(self.dbpath)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        return cursor.fetchall()

    def delete_note(self, note_id):
        conn = sqlite3.connect(self.dbpath)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE note_id = ?", (note_id,))
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            conn.close()

    def delete_question(self, questions_id):
        conn = sqlite3.connect(self.dbpath)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM questions WHERE questions_id = ?", (questions_id,)
            )
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            conn.close()

    def delete_teacher(self, teacher_id):
        conn = self.__get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM teachers WHERE teacher_id = ?",
                (teacher_id,)
                )
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            conn.close()

    def edit_teacher_username(self, username, teacher_id):
        connection = self.__get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE teachers
            SET username = ?
            WHERE  teacher_id = ?""",
            (
                username,
                teacher_id,
            ),
        )
        connection.commit()
        connection.close()

    def edit_teacher_password(self, password, teacher_id):
        connection = self.__get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE teachers
            SET teacher_password = ?
            WHERE  teacher_id = ?""",
            (
                generate_password_hash(password),
                teacher_id,
            ),
        )
        connection.commit()
        connection.close()

    def edit_teacher_display_name(self, display_name, teacher_id):
        connection = self.__get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE teachers
            SET display_name = ?
            WHERE  teacher_id = ?""",
            (
                display_name,
                teacher_id,
            ),
        )
        connection.commit()
        connection.close()

    def view_latest_note(self, teacher_id):
        conn = sqlite3.connect(self.dbpath)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT teachers.display_name,
                categories.omschrijving,
                * FROM notes
                JOIN categories ON notes.category_id = categories.category_id
                JOIN teachers ON notes.teacher_id = teachers.teacher_id
            WHERE notes.teacher_id = ?
            ORDER BY date_created DESC
            LIMIT 1
        """,
            (teacher_id,),
        )
        return cursor.fetchone()

    def edit_note(self, note_id):
        conn = sqlite3.connect(self.dbpath)
        if request.method == "POST":
            editnotetitle = request.form["edittitle"]
            editnotenote = request.form["editnote"]
            editnotesource = request.form["editsource"]
            editotecategoryid = request.form["editcategory"]
            editnotepublic = 1 if request.form.get("is_public") is not None else 0
            query_note = conn.cursor()
            query_note.execute(
                """
                          UPDATE notes
                          SET
                          title = ?,
                          note = ?,
                          note_source = ?,
                          category_id = ?,
                          is_public = ?
                          WHERE note_id = ?""",
                (
                    editnotetitle,
                    editnotenote,
                    editnotesource,
                    editotecategoryid,
                    editnotepublic,
                    note_id,
                ),
            )

            conn.commit()

        return query_note.fetchone()

    def edit_question(self, question_id):
        conn = sqlite3.connect(self.dbpath)
        if request.method == "POST":
            editquestion = request.form["editquestion"]
            editanswer = request.form["editanwser"]
            query_question = conn.cursor()
            query_question.execute(
                """UPDATE questions
                                   SET
                                   exam_question = ?,
                                   exam_answer = ?
                                   WHERE questions_id = ?""",
                (editquestion, editanswer, question_id),
            )

            conn.commit()

        return query_question.fetchone()

    def get_note(self, note_id):
        conn = sqlite3.connect(self.dbpath)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
                    SELECT category_id, teachers.display_name, *
                    FROM notes
                    JOIN teachers ON notes.teacher_id = teachers.teacher_id
                    WHERE note_id = ?""",
            (note_id,),
        )
        note = cursor.fetchone()
        conn.close()
        return note

    def get_question(self, questions_id):
        conn = sqlite3.connect(self.dbpath)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
                    SELECT exam_question, note_id
                    FROM questions
                    WHERE questions_id = ?""",
            (questions_id,),
        )

        question = cursor.fetchone()
        conn.close()

        question_dict = dict(question)

        return question_dict

    def get_note_id(self, question_id):
        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT note_id FROM questions WHERE questions_id = ?",
            (question_id,)
        )
        note_id = cursor.fetchone()
        conn.close()
        return note_id

    def get_questions(self, note_id):
        conn = sqlite3.connect(self.dbpath)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
                    SELECT exam_question, questions_id, exam_answer
                    FROM questions
                    WHERE note_id = ?""",
            (note_id,),
        )
        # rows fatch
        rows = cursor.fetchall()

        # make dictionary
        questions = [dict(row) for row in rows]
        return questions

    def get_single_question(self, questions_id):
        conn = sqlite3.connect(self.dbpath)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
                SELECT exam_question,
                       questions_id,
                       date_created,
                       exam_answer,
                       note_id
                FROM questions
                WHERE questions_id = ?""",
            (questions_id,),
        )

        return cursor.fetchone()

    def add_question(self, note_id, question, answer):
        conn = sqlite3.connect(self.dbpath)
        newquestionid = str(uuid.uuid4())
        query = conn.cursor()
        query.execute(
            """
            INSERT INTO questions
                    (questions_id, note_id, exam_question, exam_answer)
            VALUES (?, ?, ?, ?)""",
            (newquestionid, note_id, question, answer),
        )
        conn.commit()
        conn.close()

    def add_answer(self, question_id, answer):
        conn = sqlite3.connect(self.dbpath)
        query = conn.cursor()
        query.execute(
            """
            UPDATE questions
            SET exam_answer = ?
            WHERE questions_id = ?""",
            (answer, question_id),
        )
        conn.commit()
        conn.close()

    def category_filter(self, categorie):
        return f"AND notes.category_id = {categorie}"

    def questions_filter(self, filter_questions):
        if filter_questions == "no_questions":
            return "HAVING question = 0"
        elif filter_questions == "questions":
            return "HAVING question > 0"

    def search_filter(self, search_words):
        return f"""AND (note LIKE '%{search_words}%'
                    OR title LIKE '%{search_words}%')"""

    def public_filter(self):
        return "AND notes.is_public = 1"

    def filter_query_user(
        self, user_id, filter_category, filter_questions, filter_search
    ):
        cursor = self.__get_cursor()
        cursor.execute(
            (
                f"""
        SELECT notes.note_id,
                notes.title,
                notes.note,
                notes.note_source,
                COUNT(questions.exam_question) AS question,
                teachers.display_name,
                categories.omschrijving,
                strftime('%Y-%m-%d %H:%M',notes.date_created) AS date_created
        FROM notes
        LEFT JOIN questions ON notes.note_id = questions.note_id
        JOIN teachers ON notes.teacher_id = teachers.teacher_id
        JOIN categories ON notes.category_id = categories.category_id
        WHERE notes.teacher_id = ? {filter_category} {filter_search}
        GROUP BY notes.note_id
        {filter_questions};
                       """
            ),
            (user_id,),
        )
        return cursor.fetchall()

    def filter_query_non_user(
        self,
        user_id,
        filter_category,
        filter_questions,
        filter_search,
        filter_public
    ):
        cursor = self.__get_cursor()
        cursor.execute(
            (
                f"""
        SELECT notes.note_id,
                notes.title,
                notes.note,
                notes.note_source,
                COUNT(questions.exam_question) AS question,
                teachers.display_name,
                categories.omschrijving,
                strftime('%Y-%m-%d %H:%M',notes.date_created) AS date_created
        FROM notes
        LEFT JOIN questions ON notes.note_id = questions.note_id
        JOIN teachers ON notes.teacher_id = teachers.teacher_id
        JOIN categories ON notes.category_id = categories.category_id
        WHERE notes.teacher_id <> ?
        {filter_public}
        {filter_category}
        {filter_search}
        GROUP BY notes.note_id
        {filter_questions};
                       """
            ),
            (user_id,),
        )
        return cursor.fetchall()
