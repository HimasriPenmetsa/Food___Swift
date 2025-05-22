import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import mysql.connector
import re
from datetime import datetime
import bcrypt

# ---------------- DB Connection ---------------- #
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="hima@772005",  # replace with your actual password
        database="project"
    )

# ---------------- Window Setup ---------------- #
root = tk.Tk()
root.title("Hostel Helpdesk System")
root.geometry("700x500")
root.resizable(False, False)

# ---------------- Background Image (Optional) ---------------- #
def set_background(frame):
    try:
        bg_img = Image.open("background.jpg")  # optional
        bg_img = bg_img.resize((700, 500))
        bg = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(frame, image=bg)
        bg_label.image = bg
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except:
        frame.configure(bg="lightblue")

# ---------------- Frames Setup ---------------- #
home_frame = tk.Frame(root, width=700, height=500)
student_login_frame = tk.Frame(root, width=700, height=500)
student_register_frame = tk.Frame(root, width=700, height=500)
student_dashboard_frame = tk.Frame(root, width=700, height=500)
warden_login_frame = tk.Frame(root, width=700, height=500)
warden_dashboard_frame = tk.Frame(root, width=700, height=500)

for frame in (home_frame, student_login_frame, student_register_frame, student_dashboard_frame, warden_login_frame, warden_dashboard_frame):
    frame.place(x=0, y=0, relwidth=1, relheight=1)
    frame.configure(bg="lightblue")

for frame in (warden_login_frame,):
    frame.place(x=0, y=0, relwidth=1, relheight=1)
    frame.configure(bg="lightgreen")

# ---------------- Home Frame ---------------- #
tk.Label(home_frame, text="Welcome to Hostel Helpdesk", font=("Helvetica", 24, "bold"), bg="lightblue").pack(pady=50)

def open_student_login():
    roll_entry.delete(0, tk.END)
    pass_entry.delete(0, tk.END)
    student_login_frame.tkraise()

def open_warden_login():
    warden_name_entry.delete(0, tk.END)
    warden_pass_entry.delete(0, tk.END)
    warden_login_frame.tkraise()

tk.Button(home_frame, text="Student", font=("Helvetica", 16), width=20, bg="skyblue", command=open_student_login).pack(pady=20)
tk.Button(home_frame, text="Warden", font=("Helvetica", 16), width=20, bg="lightgreen", command=open_warden_login).pack(pady=10)

# ---------------- Validation Functions ---------------- #
def validate_roll(roll):
    return len(roll) == 10 and roll.isalnum()

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

# ---------------- Global State ---------------- #
logged_in_roll = None
logged_in_name = None


# ---------------- Warden Login Frame ---------------- #
form_frame = tk.Frame(warden_login_frame, bg="lightgreen")
form_frame.grid(row=0, column=0)
warden_login_frame.grid_rowconfigure(0, weight=1)
warden_login_frame.grid_columnconfigure(0, weight=1)

tk.Label(form_frame, text="Warden Login", font=("Helvetica", 18, "bold"), bg="lightgreen")\
    .grid(row=0, column=0, columnspan=2, pady=20)

# Warden Name
tk.Label(form_frame, text="Name:", bg="lightgreen")\
    .grid(row=1, column=0, sticky="e", padx=10, pady=5)
warden_name_entry = tk.Entry(form_frame)
warden_name_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(form_frame, text="Password:", bg="lightgreen")\
    .grid(row=2, column=0, sticky="e", padx=10, pady=5)
warden_pass_entry = tk.Entry(form_frame, show="*")
warden_pass_entry.grid(row=2, column=1, padx=10, pady=5)


def load_warden_requests(warden_name, hostel):
    for widget in warden_dashboard_frame.winfo_children():
        widget.destroy()

    tk.Label(warden_dashboard_frame, text=f"Warden: {warden_name} ({hostel})",
             font=("Helvetica", 14, "bold"), bg="lightblue").pack(pady=10)

    # Search & Filter Section
    filter_frame = tk.Frame(warden_dashboard_frame, bg="lightblue")
    filter_frame.pack(pady=5)

    tk.Label(filter_frame, text="Search:", bg="lightblue").grid(row=0, column=0, padx=5)
    search_var = tk.StringVar()
    search_entry = tk.Entry(filter_frame, textvariable=search_var, width=25)
    search_entry.grid(row=0, column=1, padx=5)

    tk.Label(filter_frame, text="Filter by Status:", bg="lightblue").grid(row=0, column=2, padx=5)
    status_var = tk.StringVar(value="All")
    status_menu = ttk.Combobox(filter_frame, textvariable=status_var, values=["All", "Pending", "Approved", "Rejected"], state="readonly")
    status_menu.grid(row=0, column=3, padx=5)

    tk.Button(filter_frame, text="Apply", command=lambda: refresh_requests()).grid(row=0, column=4, padx=10)

    # Scrollable request display
    canvas = tk.Canvas(warden_dashboard_frame, bg="lightblue")
    scrollbar = tk.Scrollbar(warden_dashboard_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="lightblue")

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def refresh_requests():
        # Clear current list
        for widget in scroll_frame.winfo_children():
            widget.destroy()

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
                SELECT hi.id, ud.Name, ud.Roll, ud.Room, hi.Issue, hi.Status, hi.Date
                FROM health_issues hi
                JOIN user_details ud ON hi.Roll = ud.Roll
                WHERE ud.Hostel = %s
                ORDER BY hi.Date DESC
            """
            cursor.execute(query, (hostel,))
            results = cursor.fetchall()
            conn.close()

            keyword = search_var.get().strip().lower()
            selected_status = status_var.get()

            for row in results:
                req_id, name, roll, room, issue, status, date = row
                combined_text = f"{name} {roll} {issue}".lower()

                if (keyword in combined_text) and (selected_status == "All" or status == selected_status):
                    row_frame = tk.Frame(scroll_frame, bg="white", bd=1, relief="solid", padx=10, pady=5)
                    row_frame.pack(fill="x", padx=10, pady=5)

                    info_text = f"{name} | {roll} | Room: {room} | Issue: {issue}"
                    tk.Label(row_frame, text=info_text, bg="white", anchor="w", font=("Helvetica", 10, "bold"))\
                        .grid(row=0, column=0, columnspan=4, sticky="w")

                    status_text = f"Status: {status} | Date: {date.strftime('%b %d, %Y %I:%M %p')}"
                    tk.Label(row_frame, text=status_text, bg="white", anchor="w", fg="#333333", font=("Helvetica", 9))\
                        .grid(row=1, column=0, columnspan=2, sticky="w", pady=2)

                    def make_btn(label, color):
                        return tk.Button(row_frame, text=label, bg=color, fg="white", width=10,
                                         command=lambda rid=req_id: update_status(rid, label))

                    make_btn("Approve", "green").grid(row=1, column=2, padx=2)
                    make_btn("Reject", "red").grid(row=1, column=3, padx=2)

            if not scroll_frame.winfo_children():
                tk.Label(scroll_frame, text="No matching requests found.", bg="lightblue", font=("Helvetica", 12)).pack(pady=20)

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def update_status(req_id, new_status):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE health_issues SET Status=%s, Date=NOW() WHERE id=%s",
                (new_status, req_id)
            )
            conn.commit()
            conn.close()
            messagebox.showinfo("Updated", f"Request changed to {new_status}")
            refresh_requests()
        except Exception as e:
            messagebox.showerror("Update Error", str(e))

    refresh_requests()  # Initial load
    # Bottom frame for Logout button
    bottom_frame = tk.Frame(warden_dashboard_frame, bg="lightblue")
    bottom_frame.pack(fill="x", side="bottom", pady=10, padx=10)

    def clear_warden_login_fields():
        warden_name_entry.delete(0, tk.END)
        warden_pass_entry.delete(0, tk.END)

    logout_button = tk.Button(bottom_frame, text="Logout", bg="red", fg="white",
                          command=lambda: (clear_warden_login_fields(), warden_login_frame.tkraise()))
    logout_button.pack(side="right")


def warden_login_action():
        name = warden_name_entry.get()
        pwd = warden_pass_entry.get()

        if name == "" or pwd == "":
            messagebox.showerror("Error", "Please fill all fields")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM warden WHERE username=%s AND password=%s", (name, pwd))
            result = cursor.fetchone()
            conn.close()

            if result:
                hostel = result[2]
                messagebox.showinfo("Success", f"Welcome, {name}!")
                load_warden_requests(name, hostel)  # call the dashboard loader
                warden_dashboard_frame.tkraise()
            else:
                messagebox.showerror("Invalid", "Incorrect Roll or Password")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

tk.Button(form_frame, text="Login", command=warden_login_action, bg="lightgreen")\
    .grid(row=3, column=0, columnspan=2, pady=15)

tk.Button(form_frame, text="Back", command=lambda: home_frame.tkraise())\
    .grid(row=6, column=0, columnspan=2, pady=10)


# ---------------- Student Login Frame ---------------- #
form_frame = tk.Frame(student_login_frame, bg="lightblue")
form_frame.grid(row=0, column=0)
student_login_frame.grid_rowconfigure(0, weight=1)
student_login_frame.grid_columnconfigure(0, weight=1)

# Heading (spanning both columns)
tk.Label(form_frame, text="Student Login", font=("Helvetica", 18, "bold"), bg="lightblue")\
    .grid(row=0, column=0, columnspan=2, pady=20)

# Roll Number
tk.Label(form_frame, text="Roll Number:", bg="lightblue")\
    .grid(row=1, column=0, sticky="e", padx=10, pady=5)
roll_entry = tk.Entry(form_frame)
roll_entry.grid(row=1, column=1, padx=10, pady=5)

# Password
tk.Label(form_frame, text="Password:", bg="lightblue")\
    .grid(row=2, column=0, sticky="e", padx=10, pady=5)
pass_entry = tk.Entry(form_frame, show="*")
pass_entry.grid(row=2, column=1, padx=10, pady=5)

def login_action():
    global logged_in_roll, logged_in_name
    roll = roll_entry.get()
    pwd = pass_entry.get()

    if not roll or not pwd:
        messagebox.showerror("Error", "Please fill all fields")
        return

    if not validate_roll(roll):
        messagebox.showerror("Error", "Roll number must be exactly 10 alphanumeric characters")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Only fetch the Name and hashed password for the given roll number
        cursor.execute("SELECT Name, pwd FROM user_details WHERE Roll=%s", (roll,))
        result = cursor.fetchone()
        conn.close()

        if result:
            name_from_db, hashed_pwd = result
            # Compare entered password with stored hashed password
            if bcrypt.checkpw(pwd.encode('utf-8'), hashed_pwd.encode('utf-8')):
                logged_in_roll = roll
                logged_in_name = name_from_db
                messagebox.showinfo("Success", f"Welcome {logged_in_name}!")
                welcome_label.config(text=f"Welcome, {logged_in_name} ({logged_in_roll})")
                load_health_issues()
                student_dashboard_frame.tkraise()
                return

        messagebox.showerror("Login Failed", "Invalid roll number or password")

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

# Login Button
tk.Button(form_frame, text="Login", command=login_action, bg="lightblue")\
    .grid(row=3, column=0, columnspan=2, pady=15)

# "Not a member?" and Register link
tk.Label(form_frame, text="Not a member?", bg="lightblue")\
    .grid(row=4, column=0, columnspan=2)
tk.Button(form_frame, text="Register here", fg="blue", bg="lightblue", bd=0,
          command=lambda: student_register_frame.tkraise())\
    .grid(row=5, column=0, columnspan=2)

# Back button
tk.Button(form_frame, text="Back", command=lambda: home_frame.tkraise())\
    .grid(row=6, column=0, columnspan=2, pady=10)


# ---------------- Student Register Frame ---------------- #
form_frame = tk.Frame(student_register_frame, bg="lightblue")
form_frame.place(relx=0.5, rely=0.5, anchor="center") 

tk.Label(form_frame, text="Student Registration", font=("Helvetica", 18, "bold"), bg="lightblue").grid(row=0, column=0, columnspan=2, pady=20)

tk.Label(form_frame, text="Name:", bg="lightblue").grid(row=1, column=0, sticky="e", padx=5, pady=5)
name_entry = tk.Entry(form_frame)
name_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Roll Number:", bg="lightblue").grid(row=2, column=0, sticky="e", padx=5, pady=5)
roll_reg_entry = tk.Entry(form_frame)
roll_reg_entry.grid(row=2, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Phone Number:", bg="lightblue").grid(row=3, column=0, sticky="e", padx=5, pady=5)
phone_entry = tk.Entry(form_frame)
phone_entry.grid(row=3, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Department:", bg="lightblue").grid(row=4, column=0, sticky="e", padx=5, pady=5)
dept_options = ["CSE", "AIDS", "AIML", "CSE-CS", "ECE", "EEE", "CIVIL", "MECH"]
dept_entry = ttk.Combobox(form_frame, values=dept_options, state="readonly")
dept_entry.set("Select Department")
dept_entry.grid(row=4, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Hostel:", bg="lightblue").grid(row=5, column=0, sticky="e", padx=5, pady=5)
hostel_options = ["Medha", "Vaishnavi", "Ganga", "Vaidehi", "Sarada", "Nirmala", "Manasa"]
hostel_entry = ttk.Combobox(form_frame, values=hostel_options, state="readonly")
hostel_entry.set("Select Hostel")
hostel_entry.grid(row=5, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Room Number:", bg="lightblue").grid(row=6, column=0, sticky="e", padx=5, pady=5)
room_entry = tk.Entry(form_frame)
room_entry.grid(row=6, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Password:", bg="lightblue").grid(row=7, column=0, sticky="e", padx=5, pady=5)
pwd_entry = tk.Entry(form_frame, show="*")
pwd_entry.grid(row=7, column=1, padx=5, pady=5)

def register_action():
    name = name_entry.get()
    dept = dept_entry.get()
    roll = roll_reg_entry.get()
    pwd = pwd_entry.get()
    hostel = hostel_entry.get()
    phone = phone_entry.get()
    room = room_entry.get()

    if not all([name, dept, roll, pwd, hostel, phone, room]) or dept == "Select Department" or hostel == "Select Hostel":
        messagebox.showerror("Error", "All fields are required")
        return

    if not validate_roll(roll):
        messagebox.showerror("Invalid Roll", "Roll number must be exactly 10 alphanumeric characters")
        return

    valid_pwd, msg = validate_password(pwd)
    if not valid_pwd:
        messagebox.showerror("Invalid Password", msg)
        return
    
    if not phone.isdigit() or len(phone) != 10:
        messagebox.showerror("Invalid Phone", "Phone number must be exactly 10 digits")
        return
    
    if not room.isdigit() or len(room) != 3:
        messagebox.showerror("Invalid Room Number", "Room number must be exactly 3 digits")
        return

    # Hash the password using bcrypt
    hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_details (Name, Dept, Roll, pwd, Hostel, phone, room) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (name, dept, roll, hashed_pwd, hostel, phone, room))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Registration successful! You can now login.")
        student_login_frame.tkraise()
    except mysql.connector.IntegrityError:
        messagebox.showerror("Error", "User already exists!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

tk.Button(form_frame, text="Register", command=register_action, bg="lightgreen").grid(row=8, column=0, columnspan=2, pady=15)
tk.Button(form_frame, text="Back", command=lambda: student_login_frame.tkraise()).grid(row=9, column=0, columnspan=2, pady=5)


# ------------------- Student Dashboard UI ------------------- #
tk.Label(student_dashboard_frame, text="Student Dashboard", font=("Helvetica", 18, "bold"), bg="lightblue").pack(pady=10)

welcome_label = tk.Label(student_dashboard_frame, text="", font=("Helvetica", 14), bg="lightblue")
welcome_label.pack(pady=(0, 10))

# ---------------- Health Issue Section ---------------- #
common_issues = ["Fever", "Cold/Cough", "Headache", "Stomach Pain", "Allergy", "Injury", "Other"]

issue_frame = tk.Frame(student_dashboard_frame, bg="lightblue")
issue_frame.pack(pady=5)

tk.Label(issue_frame, text="Select Health Issue:", font=("Helvetica", 12), bg="lightblue").pack()

issue_combo = ttk.Combobox(issue_frame, values=common_issues, state="readonly")
issue_combo.set("Select Issue")
issue_combo.pack()

custom_issue_text = tk.Text(issue_frame, height=2, width=50)
custom_issue_text.pack(pady=(10, 5))
custom_issue_text.pack_forget()

def on_issue_selected(event):
    if issue_combo.get() == "Other":
        custom_issue_text.pack(pady=5)
        custom_issue_text.pack(before=submit_button)
    else:
        custom_issue_text.pack_forget()

issue_combo.bind("<<ComboboxSelected>>", on_issue_selected)

# ---------------- Meal Selection ---------------- #
tk.Label(student_dashboard_frame, text="Select Meals (if applicable):", font=("Helvetica", 12), bg="lightblue").pack()

meal_frame = tk.Frame(student_dashboard_frame, bg="lightblue")
meal_frame.pack()

meal_vars = {
    "Breakfast": tk.IntVar(),
    "Lunch": tk.IntVar(),
    "Dinner": tk.IntVar()
}

for meal, var in meal_vars.items():
    tk.Checkbutton(meal_frame, text=meal, variable=var, bg="lightblue").pack(side="left", padx=10)

# ---------------- Submit/Update Logic ---------------- #
def submit_health_issue():
    selected_issue = issue_combo.get()

    if selected_issue == "Select Issue":
        messagebox.showerror("Error", "Please select a health issue.")
        return

    if selected_issue == "Other":
        issue = custom_issue_text.get("1.0", "end").strip()
        if not issue:
            messagebox.showerror("Error", "Please describe your health issue.")
            return
    else:
        issue = selected_issue

    selected_meals = [meal for meal, var in meal_vars.items() if var.get()]
    meals_str = ', '.join(selected_meals) if selected_meals else "None"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        # Check if today's request exists
        cursor.execute("""
            SELECT Status FROM health_issues
            WHERE Roll=%s AND DATE(Date)=%s
        """, (logged_in_roll, today))
        existing = cursor.fetchone()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if existing:
            status = existing[0].lower()
            if status != "pending":
                messagebox.showwarning("Not Allowed", f"You cannot update today's request. Status is already '{status.capitalize()}'.")
                return

            # Update existing pending request
            cursor.execute("""
                UPDATE health_issues
                SET Issue=%s, Meals=%s, Date=%s
                WHERE Roll=%s AND DATE(Date)=%s AND Status='Pending'
            """, (issue, meals_str, now, logged_in_roll, today))
            messagebox.showinfo("Updated", "Your issue has been updated for today.")
        else:
            # Insert new request
            cursor.execute("""
                INSERT INTO health_issues (Roll, Issue, Meals, Date, Status)
                VALUES (%s, %s, %s, %s, %s)
            """, (logged_in_roll, issue, meals_str, now, "Pending"))
            messagebox.showinfo("Submitted", "Your issue has been submitted.")

        conn.commit()
        conn.close()

        issue_combo.set("Select Issue")
        custom_issue_text.delete("1.0", "end")
        custom_issue_text.pack_forget()
        for var in meal_vars.values():
            var.set(0)

        load_health_issues()
        apply_editability_controls()  # <-- refresh editability based on updated status

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

submit_button = tk.Button(student_dashboard_frame, text="Submit / Update Issue", command=submit_health_issue, bg="lightgreen")
submit_button.pack(pady=(10, 10))

# ---------------- Issue List ---------------- #
tk.Label(student_dashboard_frame, text="Your Reported Health Issues:", bg="lightblue", font=("Helvetica", 12, "bold")).pack()

issues_listbox = tk.Listbox(student_dashboard_frame, width=100, height=8)
issues_listbox.pack(pady=5)

def load_health_issues():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Issue, Meals, Date, Status FROM health_issues WHERE Roll=%s ORDER BY Date DESC", (logged_in_roll,))
        issues = cursor.fetchall()
        conn.close()

        issues_listbox.delete(0, tk.END)
        for issue, meals, date, status in issues:
            display = f"{date}: {issue} (Meals: {meals}) - Status: {status}"
            issues_listbox.insert(tk.END, display)

            # Color the line based on status
            if status.lower() == "pending":
                issues_listbox.itemconfig(tk.END, {'fg': 'orange'})
            elif status.lower() == "approve" or status.lower() == "approved":
                issues_listbox.itemconfig(tk.END, {'fg': 'green'})
            elif status.lower() == "reject" or status.lower() == "rejected":
                issues_listbox.itemconfig(tk.END, {'fg': 'red'})
    except Exception as e:
        messagebox.showerror("Error", str(e))

def apply_editability_controls():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT Status FROM health_issues WHERE Roll=%s AND DATE(Date)=%s", (logged_in_roll, today))
        row = cursor.fetchone()
        conn.close()

        if row:
            status = row[0].lower()
            if status.lower() != "pending":
                issue_combo.config(state='disabled')
                custom_issue_text.config(state='disabled')
                for meal_cb in meal_vars.values():
                    meal_cb.set(0)
                for child in meal_frame.winfo_children():
                    child.config(state='disabled')
                submit_button.config(state='disabled')
            else:
                issue_combo.config(state='readonly')
                custom_issue_text.config(state='normal')
                for child in meal_frame.winfo_children():
                    child.config(state='normal')
                submit_button.config(state='normal')
        else:
            # No request today, allow submission
            issue_combo.config(state='readonly')
            custom_issue_text.config(state='normal')
            for child in meal_frame.winfo_children():
                child.config(state='normal')
            submit_button.config(state='normal')

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ---------------- Initial Load ---------------- #
load_health_issues()
apply_editability_controls()


def logout_action():
    global logged_in_roll, logged_in_name
    logged_in_roll = None
    logged_in_name = None
    home_frame.tkraise()

# ---------------- Logout Button ---------------- #
tk.Button(student_dashboard_frame, text="Logout", command=logout_action, bg="red", fg="white").pack(pady=10)


# ---------------- Start Application ---------------- #
home_frame.tkraise()
root.mainloop()
