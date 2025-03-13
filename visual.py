import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import psycopg2
from datetime import datetime

# Подключение к базе данных PostgreSQL
def connect_db():
    try:
        dsn = "dbname=postgres user=postgres password=1542 host=localhost port=5432"
        connection = psycopg2.connect(dsn)
        return connection
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        raise

class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление оценками")
        self.user_type = None  # Тип пользователя (ученик, учитель, администратор)
        self.student_id = None  # ID ученика
        self.teacher_id = None  # ID учителя
        self.create_login_interface()

    def create_login_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Авторизация").pack()

        self.login_entry = tk.Entry(self.root)
        self.login_entry.insert(0, "123")
        self.login_entry.pack()

        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.insert(0, "111")
        self.password_entry.pack()

        tk.Button(self.root, text="Войти как Ученик", command=lambda: self.login("student")).pack(pady=5)
        tk.Button(self.root, text="Войти как Учитель", command=lambda: self.login("teacher")).pack(pady=5)
        tk.Button(self.root, text="Войти как Администратор", command=lambda: self.login("admin")).pack(pady=5)

    def login(self, user_type):
        self.user_type = user_type
        login = self.login_entry.get()
        password = self.password_entry.get()

        if not login or not password:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните и логин и пароль.")
            return

        conn = connect_db()
        cur = conn.cursor()

        if user_type == "student":
            cur.execute("SELECT * FROM Students WHERE login = %s AND password = %s", (login, password))
        elif user_type == "teacher":
            cur.execute("SELECT * FROM Teachers WHERE login = %s AND password = %s AND deleted = %s", (login, password, False))
        else:  # admin
            cur.execute("SELECT * FROM Admins WHERE login = %s AND password = %s", (login, password))

        user = cur.fetchone()
        conn.close()

        if user:
            # messagebox.showinfo("Успешно", f"Вы вошли как {user_type.capitalize()}")
            if user_type == "student":
                self.student_id = user[0]  # Сохраняем ID ученика
            elif user_type == "teacher":
                self.teacher_id = user[0]  # Сохраняем ID учителя
            self.create_main_interface()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def create_main_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Главное меню").pack()

        if self.user_type == "student":
            self.create_student_interface()
        elif self.user_type == "teacher":
            self.create_teacher_interface()
        elif self.user_type == "admin":
            self.create_admin_interface()

        tk.Button(self.root, text="Выйти", command=self.logout).pack(pady=5)

    def create_student_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Управление оценками").pack()
        tk.Button(self.root, text="Узнать оценки по предмету", command=self.show_grades_by_subject_interface).pack(pady=5)
        tk.Button(self.root, text="Узнать итоговые оценки", command=self.show_final_grades_interface).pack(pady=5)

    def show_grades_by_subject_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Оценки по предмету").pack()

        tk.Label(self.root, text="Выберите дату начала:").pack()
        self.start_date_entry = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.start_date_entry.pack()

        tk.Label(self.root, text="Выберите дату окончания:").pack()
        self.end_date_entry = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.end_date_entry.pack()

        tk.Label(self.root, text="Выберите предмет:").pack()
        self.subject_combobox = ttk.Combobox(self.root)
        self.load_subjects()
        self.subject_combobox.pack()

        tk.Button(self.root, text="Показать оценки", command=self.get_grades_by_subject).pack()
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def load_subjects(self):
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT subject_id, subject_name FROM Subjects")
        subjects = cur.fetchall()
        self.subject_combobox['values'] = [subject[1] for subject in subjects]
        self.subject_combobox.current(0)  # Выбираем первый предмет по умолчанию
        conn.close()

    def get_grades_by_subject(self):
        start_date = self.start_date_entry.get_date()
        end_date = self.end_date_entry.get_date()

        if not start_date or not end_date:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите обе даты.")
            return

        if start_date >= end_date:
            end_date = start_date


        subject_name = self.subject_combobox.get()

        conn = connect_db()
        cur = conn.cursor()

        # Получаем subject_id по имени предмета
        cur.execute("SELECT subject_id FROM Subjects WHERE subject_name = %s", (subject_name,))
        subject_id = cur.fetchone()[0]

        # Получаем оценки из представления
        cur.execute("""
            SELECT grade, date_lesson
            FROM student_grades
            WHERE student_id = %s AND subject_id = %s AND date_lesson BETWEEN %s AND %s
        """, (self.student_id, subject_id, start_date, end_date))
        grades = cur.fetchall()
        conn.close()

        # Формируем таблицу
        self.show_grades_table(grades)

    def show_grades_table(self, grades):


        if not grades:
            messagebox.showinfo("Результат", "Нет оценок за выбранный период")
            return

        self.clear_frame()
        tk.Label(self.root, text="Оценки по предмету").pack()

        # Создаем таблицу
        table = ttk.Treeview(self.root, columns=("Оценка", "Дата"), show='headings')
        table.heading("Оценка", text="Оценка")
        table.heading("Дата", text="Дата")
        table.pack()

        for grade in grades:
            table.insert("", "end", values=(grade[0], grade[1]))

        tk.Button(self.root, text="Назад", command=self.show_grades_by_subject_interface).pack(pady=5)

    def show_final_grades_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Итоговые оценки").pack()

        # Получаем history_classes
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT history_classes FROM Students WHERE student_id = %s", (self.student_id,))
        history_classes = cur.fetchone()[0].split('$')
        conn.close()

        # Создаем словарь для сопоставления class_id и отображаемого значения
        class_display_values = {}
        for class_id in history_classes:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT class_number, class_letter, EXTRACT(YEAR FROM start_year) AS start_year FROM Classes WHERE class_id = %s",
                (class_id,))
            class_info = cur.fetchone()
            if class_info:
                class_number, class_letter, start_year = class_info
                display_value = f"{class_number}{class_letter} - {int(start_year)} год"
                class_display_values[display_value] = class_id  # Сопоставляем отображаемое значение с class_id
            conn.close()

        # Создаем выпадающий список для выбора класса
        self.class_combobox = ttk.Combobox(self.root, values=list(class_display_values.keys()))
        self.class_combobox.pack()
        tk.Button(self.root, text="Показать итоговые оценки",
                  command=lambda: self.get_final_grades(class_display_values)).pack()
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)


    def get_final_grades(self, class_display_values):
        selected_class_display = self.class_combobox.get()
        if not selected_class_display:
            messagebox.showerror("Ошибка", f"Выберите из списка год обучения")
            return
        class_id = class_display_values[selected_class_display]  # Получаем class_id из словаря
        conn = connect_db()
        cur = conn.cursor()

        print(f'self.student_id {self.student_id} class_id {class_id}')

        # Получаем итоговые оценки по предметам
        cur.execute("""
            SELECT subject_id, grade
            FROM Grades
            WHERE student_id = %s AND class_id = %s
        """, (self.student_id, class_id))


        final_grades = cur.fetchall()
        print(f'final_grades {final_grades}')
        conn.close()

        # Словарь для хранения сумм оценок и количества оценок
        grades_dict = {}

        # Обрабатываем результаты запроса
        for subject_id, grade in final_grades:
            if subject_id not in grades_dict:
                grades_dict[subject_id] = {
                    'total_grades': 0,
                    'count': 0
                }

            grades_dict[subject_id]['total_grades'] += grade
            grades_dict[subject_id]['count'] += 1

        # Подсчитываем средние оценки
        average_grades = {}
        for subject_id, data in grades_dict.items():
            average = round(data['total_grades'] / data['count'], 2)
            average_grades[subject_id] = {
                'average_grade': average
            }

        final_grades = []
        # Выводим средние оценки
        for subject_id, data in average_grades.items():
            # print(f"Студент: {data['first_name']} {data['last_name']}, Средняя оценка: {data['average_grade']:.2f}")
            final_grades.append([subject_id, data['average_grade']])

        print(f'final_grades {final_grades}')

        # Формируем таблицу
        self.show_final_grades_table(final_grades)

    def show_final_grades_table(self, final_grades):



        if not final_grades:
            messagebox.showinfo("Результат", "Нет итоговых оценок для выбранного класса")
            return

        tk.Label(self.root, text="Итоговые оценки").pack()
        self.clear_frame()

        # Создаем таблицу
        table = ttk.Treeview(self.root, columns=("Предмет", "Итоговая оценка"), show='headings')
        table.heading("Предмет", text="Предмет")
        table.heading("Итоговая оценка", text="Итоговая оценка")
        table.pack()

        conn = connect_db()
        cur = conn.cursor()
        for subject_id, avg_grade in final_grades:
            # Получаем название предмета
            cur.execute("SELECT subject_name FROM Subjects WHERE subject_id = %s", (subject_id,))
            subject_name = cur.fetchone()[0]
            # Округляем итоговую оценку
            rounded_grade = round(avg_grade)
            table.insert("", "end", values=(subject_name, rounded_grade))
        conn.close()

        tk.Button(self.root, text="Назад", command=self.show_final_grades_interface).pack(pady=5)

    def create_teacher_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Вы находитесь в меню учителя").pack()
        tk.Button(self.root, text="Оценки", command=self.show_teacher_grades_menu).pack(pady=5)
        tk.Button(self.root, text="Отчеты", command=self.show_reports_menu).pack(pady=5)

    def show_teacher_grades_menu(self):
        self.clear_frame()
        tk.Label(self.root, text="Меню оценок").pack()
        tk.Button(self.root, text="Выставить оценку", command=self.show_set_grade_interface).pack(pady=5)
        tk.Button(self.root, text="Изменить оценку", command=self.show_update_grade_interface).pack(pady=5)
        tk.Button(self.root, text="Посмотреть оценки ученика", command=self.show_teacher_view_student_grades_menu).pack(
            pady=5)
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def show_set_grade_interface(self):
        print('interface')

        self.clear_frame()
        tk.Label(self.root, text="Выставить оценку").pack()

        # Получаем предметы, которые ведет учитель
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
                SELECT s.subject_id, s.subject_name 
                FROM Teacher_Subject ts 
                JOIN Subjects s ON ts.subject_id = s.subject_id 
                WHERE ts.teacher_id = %s
            """, (self.teacher_id,))
        subjects = cur.fetchall()
        subject_display_values_set = {}
        for subject in subjects:
            subject_display_values_set[subject[1]] = subject[0]


        subject_display_values = [subject[1] for subject in subjects]
        self.subject_combobox = ttk.Combobox(self.root, values=subject_display_values)
        self.subject_combobox.pack()
        tk.Label(self.root, text="Выберите класс:").pack()

        # Получаем классы, которые ведет учитель из представления
        cur.execute("SELECT class_id, class_number, class_letter FROM Teacher_Classes_View WHERE teacher_id = %s",
                    (self.teacher_id,))
        classes = cur.fetchall()
        class_display_values_set = {}
        for cls in classes:
            class_display_values_set[f'{cls[1]}{cls[2]}'] = cls[0]

        class_display_values = [f"{cls[1]}{cls[2]}" for cls in classes]
        self.class_combobox = ttk.Combobox(self.root, values=class_display_values)
        self.class_combobox.pack()

        tk.Button(self.root, text="Далее", command=lambda: self.proceed_set_grade(class_display_values_set, subject_display_values_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.show_teacher_grades_menu).pack(pady=5)

    def proceed_set_grade(self, classes, subjects):
        print('interface далее')
        subject_name = self.subject_combobox.get()
        class_name = self.class_combobox.get()

        if not subject_name or not class_name:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите предмет и класс.")
            return

        # Получаем subject_id
        conn = connect_db()
        cur = conn.cursor()
        # cur.execute("SELECT subject_id FROM Teacher_Subject WHERE teacher_id = %s AND subject_id = (SELECT subject_id FROM Subjects WHERE subject_name = %s)", (self.teacher_id, subject_name))
        # subject_id = cur.fetchone()[0]

        subject_id = subjects[subject_name]

        # # Получаем class_id
        # cur.execute("SELECT class_id FROM Classes WHERE class_number || class_letter = %s", (class_name,))
        # class_id = cur.fetchone()[0]

        class_id = classes[class_name]

        # Получаем учеников в классе
        cur.execute("SELECT student_id, first_name, last_name, second_name FROM Students WHERE class_id = %s", (class_id,))
        students = cur.fetchall()
        conn.close()

        # Создаем интерфейс для выбора ученика
        self.clear_frame()
        tk.Label(self.root, text="Выберите ученика").pack()

        students_set = {}

        for student in students:
            students_set[f'{student[1]} {student[2]} {student[3]}'] = student[0]

        self.student_combobox = ttk.Combobox(self.root, values=[f"{student[1]} {student[2]} {student[3]}" for student in students])
        self.student_combobox.pack()

        tk.Label(self.root, text="Номер урока (1-16):").pack()
        self.lesson_number_entry = tk.Entry(self.root)
        self.lesson_number_entry.pack()

        tk.Label(self.root, text="Дата урока:").pack()
        self.date_entry = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.date_entry.pack()

        tk.Label(self.root, text="Оценка:").pack()
        self.grade_combobox = ttk.Combobox(self.root, values=[2, 3, 4, 5])
        self.grade_combobox.pack()

        tk.Button(self.root, text="Добавить оценку", command=lambda: self.add_grade(students_set, subject_id, class_id)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.show_set_grade_interface).pack(pady=5)

    def add_grade(self, students, subject_id, class_id):
        student_name = self.student_combobox.get()
        lesson_number = self.lesson_number_entry.get()
        date_lesson = self.date_entry.get_date()
        grade = self.grade_combobox.get()

        if not student_name or not lesson_number or not date_lesson or not grade:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
            return

        # Получаем student_id
        conn = connect_db()
        cur = conn.cursor()
        # cur.execute("SELECT student_id FROM Students WHERE first_name || ' ' || last_name = %s", (student_name,))
        # student_id = cur.fetchone()[0]
        student_id = students[student_name]
        # Проверка номера урока
        if not lesson_number.isdigit() or not (1 <= int(lesson_number) <= 16):
            messagebox.showerror("Ошибка", "Номер урока должен быть от 1 до 16.")
            return

        # Добавляем оценку
        create_date = datetime.now().date()
        cur.callproc("add_grade", (student_id, class_id, subject_id, self.teacher_id, grade, int(lesson_number), date_lesson, create_date))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успешно", "Оценка добавлена")

    def show_update_grade_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Изменить оценку").pack()

        # Получаем предметы, которые ведет учитель
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
                SELECT s.subject_id, s.subject_name 
                FROM Teacher_Subject ts 
                JOIN Subjects s ON ts.subject_id = s.subject_id 
                WHERE ts.teacher_id = %s
            """, (self.teacher_id,))
        subjects = cur.fetchall()

        subject_display_values_set = {}
        for subject in subjects:
            subject_display_values_set[subject[1]] = subject[0]

        subject_display_values = [subject[1] for subject in subjects]
        self.subject_combobox = ttk.Combobox(self.root, values=subject_display_values)
        self.subject_combobox.pack()
        tk.Label(self.root, text="Выберите класс:").pack()

        # Получаем классы, которые ведет учитель
        # cur.execute("SELECT c.class_id, c.class_number, c.class_letter FROM Teacher_Classes tc JOIN Classes c ON tc.class_id = c.class_id WHERE tc.teacher_id = %s", (self.teacher_id,))
        cur.execute("SELECT class_id, class_number, class_letter FROM Teacher_Classes_View WHERE teacher_id = %s",
                    (self.teacher_id,))
        classes = cur.fetchall()

        class_display_values_set = {}
        for cls in classes:
            class_display_values_set[f'{cls[1]}{cls[2]}'] = cls[0]

        class_display_values = [f"{cls[1]}{cls[2]}" for cls in classes]
        self.class_combobox = ttk.Combobox(self.root, values=class_display_values)
        self.class_combobox.pack()

        tk.Button(self.root, text="Далее", command=lambda: self.proceed_update_grade(class_display_values_set, subject_display_values_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.show_teacher_grades_menu).pack(pady=5)

    def proceed_update_grade(self,classes, subjects):
        subject_name = self.subject_combobox.get()
        class_name = self.class_combobox.get()

        if not subject_name or not class_name:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите предмет и класс.")
            return

        # Получаем subject_id
        conn = connect_db()
        cur = conn.cursor()
        # cur.execute("SELECT subject_id FROM Teacher_Subject WHERE teacher_id = %s AND subject_id = (SELECT subject_id FROM Subjects WHERE subject_name = %s)", (self.teacher_id, subject_name))
        # subject_id = cur.fetchone()[0]

        subject_id = subjects[subject_name]

        # # Получаем class_id
        # cur.execute("SELECT class_id FROM Classes WHERE class_number || class_letter = %s", (class_name,))
        # class_id = cur.fetchone()[0]

        class_id = classes[class_name]

        # Получаем учеников в классе
        cur.execute("SELECT student_id, first_name, last_name, second_name FROM Students WHERE class_id = %s", (class_id,))
        students = cur.fetchall()
        conn.close()

        # Создаем интерфейс для выбора ученика
        self.clear_frame()
        tk.Label(self.root, text="Выберите ученика").pack()

        students_set = {}

        for student in students:
            students_set[f'{student[1]} {student[2]} {student[3]}'] = student[0]

        self.student_combobox = ttk.Combobox(self.root, values=[f"{student[1]} {student[2]} {student[3]}" for student in students])
        self.student_combobox.pack()

        tk.Label(self.root, text="Дата:").pack()
        self.date_entry = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.date_entry.pack()

        tk.Button(self.root, text="Показать оценки", command=lambda: self.show_student_grades_for_update(students_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.show_update_grade_interface).pack(pady=5)

    def show_student_grades_for_update(self, students):
        student_name = self.student_combobox.get()
        date_lesson = self.date_entry.get_date()

        if not student_name or not date_lesson:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите студента и дату.")
            return

        # Получаем student_id
        conn = connect_db()
        cur = conn.cursor()
        # cur.execute("SELECT student_id FROM Students WHERE first_name || ' ' || last_name = %s", (student_name,))
        # student_id = cur.fetchone()[0]
        student_id = students[student_name]

        # Получаем оценки ученика
        cur.execute("SELECT grade_id, grade, number_lesson FROM Grades WHERE student_id = %s AND date_lesson = %s", (student_id, date_lesson,))
        grades = cur.fetchall()
        conn.close()

        if not grades:
            messagebox.showinfo("Ошибка", "Не найдено оценок в данную дату")
            return

        # Создаем интерфейс для выбора оценки
        self.clear_frame()

        grades_set = {}
        for grade in grades:
            grades_set[f"Урок {grade[2]}: {grade[1]}"] = grade[0]


        tk.Label(self.root, text="Выберите оценку для изменения").pack()
        self.grade_combobox = ttk.Combobox(self.root, values=[f"Урок {grade[2]}: {grade[1]}" for grade in grades])
        self.grade_combobox.pack()

        tk.Label(self.root, text="Новая оценка:").pack()
        self.new_grade_combobox = ttk.Combobox(self.root, values=[2, 3, 4, 5])
        self.new_grade_combobox.pack()

        tk.Button(self.root, text="Изменить оценку", command=lambda: self.update_grade(grades_set)).pack(pady=5)
        tk.Button(self.root, text="Удалить оценку", command=lambda: self.delete_grade(grades_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.show_update_grade_interface).pack(pady=5)

    def update_grade(self, grades):
        selected_grade = self.grade_combobox.get()
        new_grade = self.new_grade_combobox.get()

        if not selected_grade or not new_grade:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите оценку и новую оценку.")
            return

        # Получаем grade_id
        # grade_id = int(selected_grade.split(":")[0].split(" ")[1])  # Извлекаем номер оценки
        grade_id = grades[selected_grade]

        # Обновляем оценку
        conn = connect_db()
        cur = conn.cursor()
        cur.callproc("update_grade", (grade_id, new_grade))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успешно", "Оценка изменена")

    def delete_grade(self, grades):
        selected_grade = self.grade_combobox.get()

        if not selected_grade:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите оценку.")
            return

        # Получаем grade_id
        # grade_id = int(selected_grade.split(":")[0].split(" ")[1])  # Извлекаем номер оценки
        grade_id = grades[selected_grade]

        # Удаляем оценку
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM Grades WHERE grade_id = %s", (grade_id,))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успешно", "Оценка удалена")

    def show_teacher_view_student_grades_menu(self):
        self.clear_frame()
        tk.Label(self.root, text="Посмотреть оценки ученика").pack()

        # Получаем предметы, которые ведет учитель
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
                        SELECT s.subject_id, s.subject_name 
                        FROM Teacher_Subject ts 
                        JOIN Subjects s ON ts.subject_id = s.subject_id 
                        WHERE ts.teacher_id = %s
                    """, (self.teacher_id,))
        subjects = cur.fetchall()

        subject_display_values_set = {}
        for subject in subjects:
            subject_display_values_set[subject[1]] = subject[0]

        subject_display_values = [subject[1] for subject in subjects]
        self.subject_combobox = ttk.Combobox(self.root, values=subject_display_values)
        self.subject_combobox.pack()
        tk.Label(self.root, text="Выберите класс:").pack()

        cur.execute("SELECT class_id, class_number, class_letter FROM Teacher_Classes_View WHERE teacher_id = %s",
                    (self.teacher_id,))
        classes = cur.fetchall()

        class_display_values_set = {}
        for cls in classes:
            class_display_values_set[f'{cls[1]}{cls[2]}'] = cls[0]

        class_display_values = [f"{cls[1]}{cls[2]}" for cls in classes]
        self.class_combobox = ttk.Combobox(self.root, values=class_display_values)
        self.class_combobox.pack()

        # Кнопка для получения оценок
        tk.Button(self.root, text="Показать учеников", command=lambda: self.get_student_grades_for_teacher(class_display_values_set, subject_display_values_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.show_teacher_grades_menu).pack(pady=5)

    def get_student_grades_for_teacher(self, classes, subjects):
        class_name = self.class_combobox.get()
        subject_name = self.subject_combobox.get()

        if not class_name or not subject_name:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите класс и предмет.")
            return

        # Получаем class_id
        conn = connect_db()
        cur = conn.cursor()

        subject_id = subjects[subject_name]
        class_id = classes[class_name]

        cur.execute("SELECT student_id, first_name, last_name, second_name FROM Students WHERE class_id = %s",
                    (class_id,))
        students = cur.fetchall()
        conn.close()

        # Создаем интерфейс для выбора ученика
        self.clear_frame()
        tk.Label(self.root, text="Выберите ученика").pack()

        students_set = {}
        for student in students:
            students_set[f'{student[1]} {student[2]} {student[3]}'] = student[0]

        self.student_combobox = ttk.Combobox(self.root,
                                             values=[f"{student[1]} {student[2]} {student[3]}" for student in students])
        self.student_combobox.pack()

        tk.Label(self.root, text="Выберите дату начала:").pack()
        self.start_date_entry = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.start_date_entry.pack()

        tk.Label(self.root, text="Выберите дату окончания:").pack()
        self.end_date_entry = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.end_date_entry.pack()

        tk.Button(self.root, text="Показать оценки", command=lambda: self.show_student_grades(students_set, class_id, subject_id)).pack(
            pady=5)
        tk.Button(self.root, text="Назад", command=self.show_teacher_view_student_grades_menu).pack(pady=5)

    def show_student_grades(self, students_set, class_id, subject_id):
        student_name = self.student_combobox.get()
        start_date = self.start_date_entry.get_date()
        end_date = self.end_date_entry.get_date()

        if not student_name or not start_date or not end_date:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите ученика и обе даты.")
            return

        if start_date >= end_date:
            end_date = start_date

        # Получаем student_id
        student_id = students_set[student_name]

        # Получаем subject_id по имени предмета
        conn = connect_db()
        cur = conn.cursor()

        # Получаем оценки из представления
        cur.execute("""
            SELECT grade, date_lesson
            FROM student_grades
            WHERE student_id = %s AND subject_id = %s AND class_id = %s AND date_lesson BETWEEN %s AND %s
        """, (student_id, subject_id, class_id, start_date, end_date))
        grades = cur.fetchall()
        conn.close()

        # Формируем таблицу
        self.show_grades_table(grades)

    def show_reports_menu(self):
        self.clear_frame()
        tk.Label(self.root, text="Отчеты").pack()

        tk.Button(self.root, text="Табель оценок по предмету",
                  command=self.show_report_grades_by_subject_interface).pack(pady=5)
        tk.Button(self.root, text="Табель итоговых оценок", command=self.show_final_grades_report_interface).pack(
            pady=5)
        tk.Button(self.root, text="Сравнение успеваемости", command=self.show_performance_comparison_interface).pack(
            pady=5)

        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def show_report_grades_by_subject_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Табель оценок по предмету").pack()

        tk.Label(self.root, text="Выберите класс:").pack()
        conn = connect_db()
        cur = conn.cursor()

        # Получаем классы, которые ведет учитель из представления
        cur.execute("SELECT class_id, class_number, class_letter FROM Teacher_Classes_View WHERE teacher_id = %s",
                    (self.teacher_id,))
        classes = cur.fetchall()
        class_display_values_set = {}
        for cls in classes:
            class_display_values_set[f'{cls[1]}{cls[2]}'] = cls[0]

        class_display_values = [f"{cls[1]}{cls[2]}" for cls in classes]
        self.class_combobox = ttk.Combobox(self.root, values=class_display_values)
        self.class_combobox.pack()

        tk.Label(self.root, text="Выберите предмет:").pack()
        cur.execute("""
                SELECT s.subject_id, s.subject_name 
                FROM Teacher_Subject ts 
                JOIN Subjects s ON ts.subject_id = s.subject_id 
                WHERE ts.teacher_id = %s
            """, (self.teacher_id,))
        subjects = cur.fetchall()
        subject_display_values_set = {}
        for subject in subjects:
            subject_display_values_set[subject[1]] = subject[0]

        subject_display_values = [subject[1] for subject in subjects]
        self.subject_combobox = ttk.Combobox(self.root, values=subject_display_values)
        self.subject_combobox.pack()

        tk.Label(self.root, text="Выберите дату начала:").pack()
        self.start_date_entry = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.start_date_entry.pack()

        tk.Label(self.root, text="Выберите дату окончания:").pack()
        self.end_date_entry = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.end_date_entry.pack()

        tk.Button(self.root, text="Показать табель", command=lambda: self.get_report_grades_by_subject(class_display_values_set, subject_display_values_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)


    def get_report_grades_by_subject(self, classes, subjects):
        class_name = self.class_combobox.get()
        subject_name = self.subject_combobox.get()
        start_date = self.start_date_entry.get_date()
        end_date = self.end_date_entry.get_date()

        if not class_name or not subject_name or not start_date or not end_date:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
            return

        conn = connect_db()
        cur = conn.cursor()

        class_id = classes[class_name]
        subject_id = subjects[subject_name]

        # Получаем оценки
        cur.execute("""
            SELECT s.student_id, s.first_name, s.last_name, g.date_lesson, g.grade
            FROM Grades g
            JOIN Students s ON g.student_id = s.student_id
            WHERE g.class_id = %s AND g.subject_id = %s AND g.date_lesson BETWEEN %s AND %s
            ORDER BY s.last_name, g.date_lesson
        """, (class_id, subject_id, start_date, end_date))
        grades = cur.fetchall()
        conn.close()

        self.show_grades_report_table(grades)


    def show_grades_report_table(self, grades):


        if not grades:
            messagebox.showinfo("Результат", "Нет оценок за выбранный период")
            return

        self.clear_frame()
        tk.Label(self.root, text="Табель оценок").pack()

        # Создаем словарь для хранения оценок
        grade_dict = {}
        date_set = set()

        for grade in grades:
            student_id = grade[0]
            full_name = f"{grade[1]} {grade[2]}"
            date = grade[3].strftime("%d.%m")
            score = grade[4]

            if full_name not in grade_dict:
                grade_dict[full_name] = {}
            grade_dict[full_name][date] = score
            date_set.add(date)

        # Сортируем даты
        sorted_dates = sorted(date_set)

        # Создаем таблицу
        table = ttk.Treeview(self.root, columns=["ФИО"] + sorted_dates, show='headings')
        table.heading("ФИО", text="ФИО")
        for date in sorted_dates:
            table.heading(date, text=date)
        table.pack()

        for student, scores in grade_dict.items():
            row = [student] + [scores.get(date, "") for date in sorted_dates]
            table.insert("", "end", values=row)

        tk.Button(self.root, text="Назад", command=self.show_report_grades_by_subject_interface).pack(pady=5)

    def show_final_grades_report_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Табель итоговых оценок").pack()

        conn = connect_db()
        cur = conn.cursor()

        tk.Label(self.root, text="Выберите класс:").pack()

        # Получаем классы, которые ведет учитель из представления
        cur.execute("SELECT class_id, class_number, class_letter FROM Teacher_Classes_View WHERE teacher_id = %s",
                    (self.teacher_id,))
        classes = cur.fetchall()
        class_display_values_set = {}
        for cls in classes:
            class_display_values_set[f'{cls[1]}{cls[2]}'] = cls[0]

        class_display_values = [f"{cls[1]}{cls[2]}" for cls in classes]
        self.class_combobox = ttk.Combobox(self.root, values=class_display_values)
        self.class_combobox.pack()

        tk.Button(self.root, text="Показать итоговые оценки", command=lambda: self.get_final_grades_report(class_display_values_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def get_final_grades_report(self, classes):
        class_name = self.class_combobox.get()

        if not class_name:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите класс.")
            return

        conn = connect_db()
        cur = conn.cursor()

        class_id = classes[class_name]

        # Получаем итоговые оценки
        cur.execute("""
            SELECT s.student_id, s.first_name, s.last_name, sub.subject_name, AVG(g.grade) as avg_grade
            FROM Grades g
            JOIN Students s ON g.student_id = s.student_id
            JOIN Subjects sub ON g.subject_id = sub.subject_id
            WHERE g.class_id = %s
            GROUP BY s.student_id, sub.subject_name
            ORDER BY s.last_name, sub.subject_name
        """, (class_id,))
        final_grades = cur.fetchall()
        conn.close()

        self.show_final_grades_report_table(final_grades)

    def show_final_grades_report_table(self, final_grades):


        if not final_grades:
            messagebox.showinfo("Результат", "Нет итоговых оценок для выбранного класса")
            return

        self.clear_frame()
        tk.Label(self.root, text="Табель итоговых оценок").pack()

        # Создаем словарь для хранения итоговых оценок
        grade_dict = {}

        for grade in final_grades:
            student_id = grade[0]
            full_name = f"{grade[1]} {grade[2]}"
            subject_name = grade[3]
            avg_grade = round(grade[4])  # Округляем итоговую оценку

            if full_name not in grade_dict:
                grade_dict[full_name] = {}
            grade_dict[full_name][subject_name] = avg_grade

        # Получаем все предметы
        subjects = list(set(subject for student in grade_dict.values() for subject in student.keys()))

        # Создаем таблицу
        table = ttk.Treeview(self.root, columns=["ФИО"] + subjects, show='headings')
        table.heading("ФИО", text="ФИО")
        for subject in subjects:
            table.heading(subject, text=subject)
        table.pack()

        for student, scores in grade_dict.items():
            row = [student] + [scores.get(subject, "") for subject in subjects]
            table.insert("", "end", values=row)

        tk.Button(self.root, text="Назад", command=self.show_final_grades_report_interface).pack(pady=5)

    def show_performance_comparison_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Сравнение успеваемости учеников").pack()

        tk.Label(self.root, text="Выберите класс:").pack()

        conn = connect_db()
        cur = conn.cursor()

        # Получаем классы, которые ведет учитель из представления
        cur.execute("SELECT class_id, class_number, class_letter FROM Teacher_Classes_View WHERE teacher_id = %s",
                    (self.teacher_id,))
        classes = cur.fetchall()
        class_display_values_set = {}
        for cls in classes:
            class_display_values_set[f'{cls[1]}{cls[2]}'] = cls[0]

        class_display_values = [f"{cls[1]}{cls[2]}" for cls in classes]
        self.class_combobox = ttk.Combobox(self.root, values=class_display_values)
        self.class_combobox.pack()


        tk.Label(self.root, text="Выберите предмет:").pack()
        cur.execute("""
                SELECT s.subject_id, s.subject_name 
                FROM Teacher_Subject ts 
                JOIN Subjects s ON ts.subject_id = s.subject_id 
                WHERE ts.teacher_id = %s
            """, (self.teacher_id,))
        subjects = cur.fetchall()
        subject_display_values_set = {}
        for subject in subjects:
            subject_display_values_set[subject[1]] = subject[0]


        subject_display_values = [subject[1] for subject in subjects]
        self.subject_combobox = ttk.Combobox(self.root, values=subject_display_values)
        self.subject_combobox.pack()

        tk.Label(self.root, text="Выберите первую дату начала:").pack()
        self.start_date_entry_1 = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.start_date_entry_1.pack()

        tk.Label(self.root, text="Выберите первую дату окончания:").pack()
        self.end_date_entry_1 = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.end_date_entry_1.pack()

        tk.Label(self.root, text="Выберите вторую дату начала:").pack()
        self.start_date_entry_2 = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.start_date_entry_2.pack()

        tk.Label(self.root, text="Выберите вторую дату окончания:").pack()
        self.end_date_entry_2 = DateEntry(self.root, date_pattern='dd-mm-yyyy')
        self.end_date_entry_2.pack()

        tk.Button(self.root, text="Сравнить успеваемость", command=lambda: self.compare_performance(class_display_values_set, subject_display_values_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def compare_performance(self, classes, subjects):
        class_name = self.class_combobox.get()
        subject_name = self.subject_combobox.get()
        start_date_1 = self.start_date_entry_1.get_date()
        end_date_1 = self.end_date_entry_1.get_date()
        start_date_2 = self.start_date_entry_2.get_date()
        end_date_2 = self.end_date_entry_2.get_date()

        if not class_name or not subject_name or not start_date_1 or not end_date_1 or not start_date_2 or not end_date_2:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
            return

        conn = connect_db()
        cur = conn.cursor()

        class_id = classes[class_name]

        subject_id = subjects[subject_name]

        print(f'class_id {class_id} subject_id {subject_id}')

        # Получаем средние оценки за первый период
        cur.execute("""
                    SELECT s.student_id, s.first_name, s.last_name, g.grade
                    FROM Grades g
                    JOIN Students s ON g.student_id = s.student_id
                    WHERE g.class_id = %s AND g.subject_id = %s AND g.date_lesson BETWEEN %s AND %s
                    GROUP BY s.student_id, g.grade
                """, (class_id, subject_id, start_date_1, end_date_1))
        first_period_grades_local = cur.fetchall()
        print(first_period_grades_local)

        # Словарь для хранения сумм оценок и количества оценок для каждого студента
        grades_dict = {}

        # Обрабатываем результаты запроса
        for student_id, first_name, last_name, grade in first_period_grades_local:
            if student_id not in grades_dict:
                grades_dict[student_id] = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'total_grades': 0,
                    'count': 0
                }

            grades_dict[student_id]['total_grades'] += grade
            grades_dict[student_id]['count'] += 1

        # Подсчитываем средние оценки
        average_grades = {}
        for student_id, data in grades_dict.items():
            average = round(data['total_grades'] / data['count'], 2)
            average_grades[student_id] = {
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'average_grade': average
            }

        first_period_grades = []
        # Выводим средние оценки
        for student_id, data in average_grades.items():
            # print(f"Студент: {data['first_name']} {data['last_name']}, Средняя оценка: {data['average_grade']:.2f}")
            first_period_grades.append([student_id, data['first_name'], data['last_name'], data['average_grade']])

        # # Получаем средние оценки за второй период
        # cur.execute("""
        #     SELECT s.student_id, s.first_name, s.last_name, g.grade
        #     FROM Grades g
        #     JOIN Students s ON g.student_id = s.student_id
        #     WHERE g.class_id = %s AND g.subject_id = %s AND g.date_lesson BETWEEN %s AND %s
        #     GROUP BY s.student_id, g.grade
        # """, (class_id, subject_id, start_date_2, end_date_2))
        # second_period_grades_local = cur.fetchall()
        # print(second_period_grades_local)

        # # Получаем средние оценки за первый период
        # cur.execute("""
        #     SELECT s.student_id, s.first_name, s.last_name, AVG(g.grade) as avg_grade
        #     FROM Grades g
        #     JOIN Students s ON g.student_id = s.student_id
        #     WHERE g.class_id = %s AND g.subject_id = %s AND g.date_lesson BETWEEN %s AND %s
        #     GROUP BY s.student_id, s.first_name, s.last_name
        # """, (class_id, subject_id, start_date_1, end_date_1))
        # first_period_grades = cur.fetchall()

        # # Получаем средние оценки за второй период
        # cur.execute("""
        #     SELECT s.student_id, s.first_name, s.last_name, AVG(g.grade) as avg_grade
        #     FROM Grades g
        #     JOIN Students s ON g.student_id = s.student_id
        #     WHERE g.class_id = %s AND g.subject_id = %s AND g.date_lesson BETWEEN %s AND %s
        #     GROUP BY s.student_id, s.first_name, s.last_name
        # """, (class_id, subject_id, start_date_2, end_date_2))
        # second_period_grades = cur.fetchall()

        # Получаем средние оценки за первый период
        cur.execute("""
                        SELECT s.student_id, s.first_name, s.last_name, g.grade
                        FROM Grades g
                        JOIN Students s ON g.student_id = s.student_id
                        WHERE g.class_id = %s AND g.subject_id = %s AND g.date_lesson BETWEEN %s AND %s
                        GROUP BY s.student_id, g.grade
                    """, (class_id, subject_id, start_date_2, end_date_2))
        second_period_grades_local = cur.fetchall()
        print(second_period_grades_local)

        # Словарь для хранения сумм оценок и количества оценок для каждого студента
        grades_dict = {}

        # Обрабатываем результаты запроса
        for student_id, first_name, last_name, grade in second_period_grades_local:
            if student_id not in grades_dict:
                grades_dict[student_id] = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'total_grades': 0,
                    'count': 0
                }

            grades_dict[student_id]['total_grades'] += grade
            grades_dict[student_id]['count'] += 1

        # Подсчитываем средние оценки
        average_grades = {}
        for student_id, data in grades_dict.items():
            average = round(data['total_grades'] / data['count'], 2)
            average_grades[student_id] = {
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'average_grade': average
            }

        second_period_grades = []
        # Выводим средние оценки
        for student_id, data in average_grades.items():
            # print(f"Студент: {data['first_name']} {data['last_name']}, Средняя оценка: {data['average_grade']:.2f}")
            second_period_grades.append([student_id, data['first_name'], data['last_name'], data['average_grade']])
        conn.close()

        self.show_performance_comparison_table(first_period_grades, second_period_grades)

    def show_performance_comparison_table(self, first_period_grades, second_period_grades):
        print(f'first_period_grades {first_period_grades}')
        print(f'second_period_grades {second_period_grades}')

        if not first_period_grades or not second_period_grades:
            messagebox.showinfo("Результат", "Нет оценок за выбранные периоды")
            return

        self.clear_frame()
        tk.Label(self.root, text="Сравнение успеваемости").pack()

        # Создаем таблицу
        table = ttk.Treeview(self.root, columns=("ФИО", "1-й период", "2-й период", "Изменение (%)"), show='headings')
        table.heading("ФИО", text="ФИО")
        table.heading("1-й период", text="1-й период")
        table.heading("2-й период", text="2-й период")
        table.heading("Изменение (%)", text="Изменение (%)")
        table.pack()

        # Сравниваем успеваемость
        performance_changes = {}
        for grade in first_period_grades:
            performance_changes[grade[0]] = [f"{grade[1]} {grade[2]}", grade[3], None]  # Сохраняем ФИО и оценку

        print(f'performance_changes {performance_changes}')

        for grade in second_period_grades:
            if grade[0] in performance_changes:
                performance_changes[grade[0]][2] = grade[3]  # Сохраняем оценку за второй период

        print(f'performance_changes {performance_changes}')

        total_change = 0
        count = 0


        for student_id, data in performance_changes.items():
            first_grade = data[1]
            second_grade = data[2]
            if first_grade is not None and second_grade is not None:
                change = ((second_grade - first_grade) / first_grade) * 100
                total_change += change
                count += 1
                table.insert("", "end", values=(data[0], round(first_grade, 2), round(second_grade, 2), round(change, 2)))

        if count > 0:
            average_change = total_change / count
            table.insert("", "end", values=("Среднее изменение", "", "", round(average_change, 2)))

        tk.Button(self.root, text="Назад", command=self.show_performance_comparison_interface).pack(pady=5)

    def create_admin_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Управление учителями").pack()
        tk.Button(self.root, text="Изменить учителей", command=self.manage_teachers).pack(pady=5)
        tk.Button(self.root, text="Изменить предметы учителям", command=self.manage_teacher_subjects).pack(pady=5)
        tk.Button(self.root, text="Изменить классы учителям", command=self.manage_teacher_classes).pack(pady=5)
        tk.Button(self.root, text="Информация о учителе", command=self.teacher_info).pack(pady=5)

    def manage_teachers(self):
        self.clear_frame()
        tk.Label(self.root, text="Управление учителями").pack()
        tk.Button(self.root, text="Добавить учителя", command=self.add_teacher_interface).pack(pady=5)
        tk.Button(self.root, text="Удалить учителя", command=self.delete_teacher_interface).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def add_teacher_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Добавить учителя").pack()

        tk.Label(self.root, text="Имя:").pack()
        self.first_name_entry = tk.Entry(self.root)
        self.first_name_entry.pack()

        tk.Label(self.root, text="Фамилия:").pack()
        self.last_name_entry = tk.Entry(self.root)
        self.last_name_entry.pack()

        tk.Label(self.root, text="Отчество:").pack()
        self.second_name_entry = tk.Entry(self.root)
        self.second_name_entry.pack()

        tk.Label(self.root, text="Логин:").pack()
        self.login_entry = tk.Entry(self.root)
        self.login_entry.pack()

        tk.Label(self.root, text="Пароль:").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Button(self.root, text="Добавить", command=self.add_teacher).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teachers).pack(pady=5)

    def add_teacher(self):
        first_name = self.first_name_entry.get()
        last_name = self.last_name_entry.get()
        second_name = self.second_name_entry.get()
        login = self.login_entry.get()
        password = self.password_entry.get()

        if not (first_name and last_name and second_name and login and password):
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
            return

        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO Teachers (first_name, last_name, second_name, login, password) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, second_name, login, password))
            conn.commit()
            messagebox.showinfo("Успешно", "Учитель добавлен")
        except psycopg2.IntegrityError:
            conn.rollback()
            messagebox.showerror("Ошибка", "Логин уже существует.")
        finally:
            conn.close()

    def delete_teacher_interface(self):
        self.clear_frame()
        tk.Label(self.root, text="Удалить учителя").pack()

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT teacher_id, first_name, last_name FROM Teachers WHERE deleted = FALSE")

        teachers = cur.fetchall()
        conn.close()

        if not teachers:
            messagebox.showinfo("Информация", "Нет доступных учителей для удаления.")
            self.manage_teachers()
            return

        teachers_set = {}
        for teacher in teachers:
            teachers_set[f"{teacher[1]} {teacher[2]}"] = teacher[0]

        self.teacher_combobox = ttk.Combobox(self.root, values=[f"{teacher[1]} {teacher[2]}" for teacher in teachers])
        self.teacher_combobox.pack()

        tk.Button(self.root, text="Удалить", command=lambda: self.delete_teacher(teachers_set)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teachers).pack(pady=5)

    def delete_teacher(self, teachers):
        selected_teacher = self.teacher_combobox.get()
        if not selected_teacher:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите учителя.")
            return

        teacher_id = teachers[selected_teacher]

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE Teachers SET deleted = TRUE WHERE teacher_id = %s", (teacher_id,))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успешно", "Учитель удален (помечен как удаленный).")

    def manage_teacher_subjects(self):
        self.clear_frame()
        tk.Label(self.root, text="Изменить предметы учителям").pack()
        tk.Button(self.root, text="Добавить предмет", command=self.add_subject_to_teacher).pack(pady=5)
        tk.Button(self.root, text="Удалить предмет", command=self.remove_subject_from_teacher).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def add_subject_to_teacher(self):
        self.clear_frame()
        tk.Label(self.root, text="Добавить предмет учителю").pack()

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT teacher_id, first_name, last_name FROM Teachers WHERE deleted = FALSE")
        teachers = cur.fetchall()
        conn.close()

        teachers_dict = {f"{teacher[1]} {teacher[2]}": teacher[0] for teacher in teachers}
        self.teacher_combobox = ttk.Combobox(self.root, values=list(teachers_dict.keys()))
        self.teacher_combobox.pack()

        tk.Button(self.root, text="Выбрать учителя", command=lambda: self.get_available_subjects(teachers_dict)).pack(
            pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teacher_subjects).pack(pady=5)

    def get_available_subjects(self, teachers_dict):
        selected_teacher = self.teacher_combobox.get()
        if not selected_teacher:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите учителя.")
            return

        self.clear_frame()

        teacher_id = teachers_dict[selected_teacher]
        conn = connect_db()
        cur = conn.cursor()

        # Получаем все доступные предметы
        cur.execute("SELECT subject_id, subject_name FROM Subjects")
        all_subjects = cur.fetchall()

        # Получаем предметы, которые уже есть у учителя
        cur.execute("""
            SELECT s.subject_id, s.subject_name
            FROM Teacher_Subject ts
            JOIN Subjects s ON ts.subject_id = s.subject_id
            WHERE ts.teacher_id = %s
        """, (teacher_id,))
        assigned_subjects = cur.fetchall()

        conn.close()

        tk.Label(self.root, text="Доступные предметы").pack()

        # Формируем список доступных предметов для добавления
        assigned_subject_ids = {subject[0] for subject in assigned_subjects}
        available_subjects = [subject for subject in all_subjects if subject[0] not in assigned_subject_ids]

        # Отображаем доступные предметы
        self.available_subjects_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE)
        for subject in available_subjects:
            self.available_subjects_listbox.insert(tk.END, subject[1])
        self.available_subjects_listbox.pack()



        tk.Button(self.root, text="Добавить", command=lambda: self.add_subject(teacher_id)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teacher_subjects).pack(pady=5)

    def add_subject(self, teacher_id):
        selected_subject_index = self.available_subjects_listbox.curselection()
        if not selected_subject_index:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите предмет для добавления.")
            return

        subject_name = self.available_subjects_listbox.get(selected_subject_index)
        conn = connect_db()
        cur = conn.cursor()

        # Получаем ID предмета
        cur.execute("SELECT subject_id FROM Subjects WHERE subject_name = %s", (subject_name,))
        subject_id = cur.fetchone()[0]

        # Добавляем предмет к учителю
        cur.execute("INSERT INTO Teacher_Subject (teacher_id, subject_id) VALUES (%s, %s)", (teacher_id, subject_id))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успешно", f"Предмет '{subject_name}' добавлен к учителю.")

        self.add_subject_to_teacher()

    def remove_subject_from_teacher(self):
        self.clear_frame()
        tk.Label(self.root, text="Удалить предмет у учителя").pack()

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT teacher_id, first_name, last_name FROM Teachers WHERE deleted = FALSE")
        teachers = cur.fetchall()
        conn.close()

        teachers_dict = {f"{teacher[1]} {teacher[2]}": teacher[0] for teacher in teachers}
        self.teacher_combobox = ttk.Combobox(self.root, values=list(teachers_dict.keys()))
        self.teacher_combobox.pack()

        tk.Button(self.root, text="Выбрать учителя", command=lambda: self.get_assigned_subjects(teachers_dict)).pack(
            pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teacher_subjects).pack(pady=5)

    def get_assigned_subjects(self, teachers_dict):
        selected_teacher = self.teacher_combobox.get()
        if not selected_teacher:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите учителя.")
            return

        self.clear_frame()

        teacher_id = teachers_dict[selected_teacher]
        conn = connect_db()
        cur = conn.cursor()

        # Получаем предметы, которые уже есть у учителя
        cur.execute("""
            SELECT s.subject_id, s.subject_name
            FROM Teacher_Subject ts
            JOIN Subjects s ON ts.subject_id = s.subject_id
            WHERE ts.teacher_id = %s
        """, (teacher_id,))
        assigned_subjects = cur.fetchall()

        conn.close()

        if not assigned_subjects:
            messagebox.showinfo("Информация", "У выбранного учителя нет назначенных предметов.")
            return

        # Отображаем назначенные предметы
        self.assigned_subjects_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE)
        for subject in assigned_subjects:
            self.assigned_subjects_listbox.insert(tk.END, subject[1])
        self.assigned_subjects_listbox.pack()

        tk.Button(self.root, text="Удалить", command=lambda: self.remove_subject(teacher_id)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teacher_subjects).pack(pady=5)

    def remove_subject(self, teacher_id):
        selected_subject_index = self.assigned_subjects_listbox.curselection()
        if not selected_subject_index:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите предмет для удаления.")
            return

        subject_name = self.assigned_subjects_listbox.get(selected_subject_index)
        conn = connect_db()
        cur = conn.cursor()

        # Получаем ID предмета
        cur.execute("SELECT subject_id FROM Subjects WHERE subject_name = %s", (subject_name,))
        subject_id = cur.fetchone()[0]

        # Удаляем предмет у учителя
        cur.execute("DELETE FROM Teacher_Subject WHERE teacher_id = %s AND subject_id = %s", (teacher_id, subject_id))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успешно", f"Предмет '{subject_name}' удален у учителя.")

        self.remove_subject_from_teacher()

    # Аналогично реализуем функции для управления классами
    def manage_teacher_classes(self):
        self.clear_frame()
        tk.Label(self.root, text="Изменить классы учителям").pack()
        tk.Button(self.root, text="Добавить класс", command=self.add_class_to_teacher).pack(pady=5)
        tk.Button(self.root, text="Удалить класс", command=self.remove_class_from_teacher).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def add_class_to_teacher(self):
        self.clear_frame()
        tk.Label(self.root, text="Добавить класс учителю").pack()

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT teacher_id, first_name, last_name FROM Teachers WHERE deleted = FALSE")
        teachers = cur.fetchall()
        conn.close()

        teachers_dict = {f"{teacher[1]} {teacher[2]}": teacher[0] for teacher in teachers}
        self.teacher_combobox = ttk.Combobox(self.root, values=list(teachers_dict.keys()))
        self.teacher_combobox.pack()

        tk.Button(self.root, text="Выбрать учителя", command=lambda: self.get_available_classes(teachers_dict)).pack(
            pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teacher_classes).pack(pady=5)

    def get_available_classes(self, teachers_dict):
        selected_teacher = self.teacher_combobox.get()
        if not selected_teacher:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите учителя.")
            return

        self.clear_frame()

        teacher_id = teachers_dict[selected_teacher]
        conn = connect_db()
        cur = conn.cursor()

        # Получаем все доступные классы
        cur.execute("SELECT class_id, class_number, class_letter FROM Classes")
        all_classes = cur.fetchall()

        # Получаем классы, которые уже есть у учителя
        cur.execute("""
            SELECT c.class_id, c.class_number, c.class_letter
            FROM Teacher_Classes tc
            JOIN Classes c ON tc.class_id = c.class_id
            WHERE tc.teacher_id = %s
        """, (teacher_id,))
        assigned_classes = cur.fetchall()

        conn.close()

        # Формируем список доступных классов для добавления
        assigned_class_ids = {cls[0] for cls in assigned_classes}
        available_classes = [cls for cls in all_classes if cls[0] not in assigned_class_ids]

        # Отображаем доступные классы
        self.available_classes_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE)
        for cls in available_classes:
            self.available_classes_listbox.insert(tk.END, f"{cls[1]}{cls[2]}")
        self.available_classes_listbox.pack()

        tk.Button(self.root, text="Добавить", command=lambda: self.add_class(teacher_id)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teacher_classes).pack(pady=5)

    def add_class(self, teacher_id):
        selected_class_index = self.available_classes_listbox.curselection()
        if not selected_class_index:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите класс для добавления.")
            return

        class_name = self.available_classes_listbox.get(selected_class_index)
        conn = connect_db()
        cur = conn.cursor()

        # Получаем ID класса
        cur.execute("SELECT class_id FROM Classes WHERE class_number || class_letter = %s", (class_name,))
        class_id = cur.fetchone()[0]

        # Добавляем класс к учителю
        cur.execute("INSERT INTO Teacher_Classes (teacher_id, class_id) VALUES (%s, %s)", (teacher_id, class_id))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успешно", f"Класс '{class_name}' добавлен к учителю.")

        self.add_class_to_teacher()

    def remove_class_from_teacher(self):
        self.clear_frame()
        tk.Label(self.root, text="Удалить класс у учителя").pack()

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT teacher_id, first_name, last_name FROM Teachers WHERE deleted = FALSE")
        teachers = cur.fetchall()
        conn.close()

        teachers_dict = {f"{teacher[1]} {teacher[2]}": teacher[0] for teacher in teachers}
        self.teacher_combobox = ttk.Combobox(self.root, values=list(teachers_dict.keys()))
        self.teacher_combobox.pack()

        tk.Button(self.root, text="Выбрать учителя", command=lambda: self.get_assigned_classes(teachers_dict)).pack(
            pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teacher_classes).pack(pady=5)

    def get_assigned_classes(self, teachers_dict):
        selected_teacher = self.teacher_combobox.get()
        if not selected_teacher:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите учителя.")
            return

        self.clear_frame()

        teacher_id = teachers_dict[selected_teacher]
        conn = connect_db()
        cur = conn.cursor()

        # Получаем классы, которые уже есть у учителя
        cur.execute("""
            SELECT c.class_id, c.class_number, c.class_letter
            FROM Teacher_Classes tc
            JOIN Classes c ON tc.class_id = c.class_id
            WHERE tc.teacher_id = %s
        """, (teacher_id,))
        assigned_classes = cur.fetchall()

        conn.close()

        if not assigned_classes:
            messagebox.showinfo("Информация", "У выбранного учителя нет назначенных классов.")
            return

        # Отображаем назначенные классы
        self.assigned_classes_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE)
        for cls in assigned_classes:
            self.assigned_classes_listbox.insert(tk.END, f"{cls[1]}{cls[2]}")
        self.assigned_classes_listbox.pack()

        tk.Button(self.root, text="Удалить", command=lambda: self.remove_class(teacher_id)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.manage_teacher_classes).pack(pady=5)

    def remove_class(self, teacher_id):
        selected_class_index = self.assigned_classes_listbox.curselection()
        if not selected_class_index:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите класс для удаления.")
            return

        class_name = self.assigned_classes_listbox.get(selected_class_index)
        conn = connect_db()
        cur = conn.cursor()

        # Получаем ID класса
        cur.execute("SELECT class_id FROM Classes WHERE class_number || class_letter = %s", (class_name,))
        class_id = cur.fetchone()[0]

        # Удаляем класс у учителя
        cur.execute("DELETE FROM Teacher_Classes WHERE teacher_id = %s AND class_id = %s", (teacher_id, class_id))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успешно", f"Класс '{class_name}' удален у учителя.")

        self.remove_class_from_teacher()

    def teacher_info(self):
        self.clear_frame()
        tk.Label(self.root, text="Информация о учителе").pack()

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT teacher_id, first_name, last_name FROM Teachers WHERE deleted = FALSE")
        teachers = cur.fetchall()
        conn.close()

        teachers_dict = {f"{teacher[1]} {teacher[2]}": teacher[0] for teacher in teachers}

        self.teacher_combobox = ttk.Combobox(self.root, values=list(teachers_dict.keys()))
        self.teacher_combobox.pack()

        tk.Button(self.root, text="Получить информацию", command=lambda: self.get_teacher_info(teachers_dict)).pack(pady=5)
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def get_teacher_info(self, teachers):
        selected_teacher = self.teacher_combobox.get()
        if not selected_teacher:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите учителя.")
            return

        self.clear_frame()  # Очищаем текущий интерфейс

        teacher_id = teachers[selected_teacher]
        conn = connect_db()
        cur = conn.cursor()

        # Получаем информацию о предмете
        cur.execute("""
            SELECT s.subject_name
            FROM Teacher_Subject ts
            JOIN Subjects s ON ts.subject_id = s.subject_id
            WHERE ts.teacher_id = %s
        """, (teacher_id,))
        subjects = cur.fetchall()

        # Получаем информацию о классах
        cur.execute("""
            SELECT c.class_number, c.class_letter, COUNT(s.student_id) AS student_count, EXTRACT(YEAR FROM c.start_year) AS start_year
            FROM Teacher_Classes tc
            JOIN Classes c ON tc.class_id = c.class_id
            LEFT JOIN Students s ON s.class_id = c.class_id
            WHERE tc.teacher_id = %s
            GROUP BY c.class_number, c.class_letter, c.start_year
        """, (teacher_id,))
        classes = cur.fetchall()

        conn.close()

        # Формируем текст с информацией
        info = f"Учитель: {selected_teacher}\n\nПредметы:\n" + "\n".join(
            [subject[0] for subject in subjects]) + "\n\nКлассы:\n"
        for cls in classes:
            info += f"{cls[0]}{cls[1]} - {cls[2]} учеников, год начала: {int(cls[3])}\n"

        # Отображаем информацию в метке
        info_label = tk.Label(self.root, text=info, justify=tk.LEFT)
        info_label.pack(padx=10, pady=10)

        # Кнопка "Назад"
        tk.Button(self.root, text="Назад", command=self.create_main_interface).pack(pady=5)

    def logout(self):
        self.user_type = None
        self.student_id = None
        self.teacher_id = None 
        self.create_login_interface()

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()
