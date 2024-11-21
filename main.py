from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import requests
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse


app = Flask(__name__)
app.secret_key = 'raj'

WEBHOOK_VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN", "tested")
GRAPH_API_TOKEN = os.environ.get("GRAPH_API_TOKEN", "EAAXbZCUeswOkBO2gXsPZC9gXHqMSyGXhvTZAcCRLvLmlSivveAzkMhBtTguHCQSykdNTDj3KP6qOvjyWO7YRCCeBzt0ulyKTjB16MVRv8CZAKedjfeqbSo7hVJCLVY3CYEAbm8QMPaZAmXlS6S52UpB1NZBkpgj0ui8ahXUVj1TlOmR4aTLVCDWb1OOMZC8ZBDUNLgZDZD")  # Replace with actual token
PORT = os.environ.get("PORT", 5000)
phone_number_id = "389016260968767"
media_id = "1262504498532543"  # Media ID from the previous response

user_sessions = {}

departments = {
    "1": {"name": "Cardiology", "doctors": ["Dr.M.S.S.Mukharjee", "Dr.Movva Srinivas", "Dr.Vinod K.Unni", "Dr.R.V.Venkata Rao", "Dr.Vikash Shukla"]},
    # "2": {"name": "Critical Care", "doctors": ["Dr.Nanda Kishore J", "Dr.Chandresh Kumar"]},
    "3": {"name": "Gynaecology", "doctors": ["Dr.Madhuri Movva"]},
    "4": {"name": "Pulmonology", "doctors": ["Dr. Rajesh.A"]},
    "5": {"name": "Cardio-Thoracic Surgery", "doctors": ["Dr.T.Vamshidhar"]},
    "6": {"name": "Orthopedics", "doctors": ["Dr.Sai Chandra"]},
    "7": {"name": "Nephrology", "doctors": ["Dr.J.A.L.Ranganath", "Dr. Rahul Patibandla"]},
    "8": {"name": "Dermatology", "doctors": ["Dr.Sanjusha Kuncha"]},
    "9": {"name": "Neurology", "doctors": ["Dr.Ch.Sita", "Dr.Sasidhar Pamulapati"]},
    "10": {"name": "Urology", "doctors": ["Dr.Rama Sanjay Y", "Dr.Avinash Gottumukkala"]},
    # Add remaining departments and doctors here
}

def get_db_connection():
    connection = psycopg2.connect(
        dbname="whatsapp_hluc",  # Your PostgreSQL database name
        user="whatsapp_hluc_user",  # Your PostgreSQL user
        password="qIZ1rtncfnpgLjWIhTgvlcuTpvgmy8Ax",  # Your PostgreSQL password
        host="dpg-crtph3tds78s73f2gvig-a.oregon-postgres.render.com",  # Your PostgreSQL host
        port="5432"  # Default PostgreSQL port
    )
    return connection

def fetch_available_dates():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM available_dates")
    dates = cursor.fetchall()
    conn.close()
    return dates

# Fetch times for a specific date
def fetch_available_times(date_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM available_times WHERE date_id = %s", (date_id,))
    times = cursor.fetchall()
    conn.close()
    return times
@app.route('/view_schedule')
def view_schedule():
    dates = fetch_available_dates()
    selected_date_id = request.args.get('date_id') if request.args.get('date_id') else (dates[0]['id'] if dates else None)
    times = fetch_available_times(selected_date_id) if selected_date_id else []
    return render_template('view_schedule.html', dates=dates, times=times, selected_date_id=selected_date_id)

@app.route('/get_times_for_date/<int:date_id>')
def get_times_for_date(date_id):
    times = fetch_available_times(date_id)
    return jsonify(times=[{'id': time['id'], 'available_time': time['available_time']} for time in times])

# Route to manage available dates and times
@app.route('/manage_schedule', methods=['GET', 'POST'])
def manage_schedule():
    selected_date_id = None
    times = []

    if request.method == 'POST':
        # Handle adding a new date
        if 'new_date' in request.form:
            new_date = request.form['new_date']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO available_dates (available_date) VALUES (%s) RETURNING id", (new_date,))
            new_date_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()

        # Handle adding a new time linked to a date
        elif 'new_time' in request.form and 'date_id' in request.form:
            new_time = request.form['new_time']
            date_id = request.form['date_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO available_times (available_time, date_id) VALUES (%s, %s)", (new_time, date_id))
            conn.commit()
            conn.close()

            selected_date_id = date_id  # Keep selected date for times display

        # If a date is selected from dropdown, update the selected date
        elif 'date_id' in request.form:
            selected_date_id = request.form['date_id']
    
    # Fetch all dates and their associated times
    dates = fetch_available_dates()

    # If a specific date is selected, fetch its times
    if selected_date_id:
        times = fetch_available_times(selected_date_id)
    else:
        selected_date_id = dates[0]['id'] if dates else None
        times = fetch_available_times(selected_date_id) if selected_date_id else []

    return render_template('manage_schedule.html', dates=dates, times=times, selected_date_id=selected_date_id)
# Route to delete a date
@app.route('/delete_date/<int:date_id>')
def delete_date(date_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM available_dates WHERE id = %s", (date_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_schedule'))

# Route to delete a time
@app.route('/delete_time/<int:time_id>')
def delete_time(time_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM available_times WHERE id = %s", (time_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_schedule'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hardcoded credentials for now, replace with PostgreSQL authentication later if needed
        if username == 'pulse' and password == 'pulse@123':
            session['logged_in'] = True
            return redirect(url_for('appointments'))

    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Appointments management page
@app.route('/appointments')
def appointments():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT * FROM appointments ORDER BY created_at DESC")
    appointments = cursor.fetchall()
    
    cursor.close()  # Close the cursor after the operation
    conn.close()  # Close the database connection
    
    return render_template('appointments.html', appointments=appointments)



# API to update appointment status
@app.route('/update_status', methods=['POST'])
def update_status():
    appointment_id = request.form.get('appointment_id')
    new_status = request.form.get('status')
    
    if not appointment_id or not new_status:
        return jsonify({"error": "Missing appointment ID or status"}), 400

    # Update the appointment status in your database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE appointments SET status = %s WHERE id = %s", (new_status, appointment_id))
        conn.commit()
        return jsonify({"message": "Status updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('view_appointments'))

# Route to store appointments
@app.route('/submitappointment', methods=['POST'])
def submit_appointment():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    age = data.get('age')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')
    department = data.get('department')
    doctor = data.get('doctor')
    gender = data.get('gender')
    phone_number = data.get('sender')
    language = data.get('language')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
    INSERT INTO appointments (name, email, age, appointment_date, appointment_time, department, doctor, gender, phone_number, language)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    # Execute the query with the provided values
    cursor.execute(query, (
        name, email, age, appointment_date, appointment_time, department, doctor, gender, phone_number, language
    ))

    # Commit the changes and close the cursor and connection
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Appointment saved successfully!'})




# Route to retrieve all appointments

@app.route('/appointments')
def view_appointments():
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Fetch appointments with different statuses
    cursor.execute("SELECT * FROM appointments WHERE status = 'Pending'")
    new_appointments = cursor.fetchall()

    cursor.execute("SELECT * FROM appointments WHERE status = 'Confirmed'")
    confirmed_appointments = cursor.fetchall()

    cursor.execute("SELECT * FROM appointments WHERE status = 'Postponed'")
    postponed_appointments = cursor.fetchall()

    cursor.execute("SELECT * FROM appointments WHERE status = 'Deleted'")
    deleted_appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('appointments.html',
                           new_appointments=new_appointments,
                           confirmed_appointments=confirmed_appointments,
                           postponed_appointments=postponed_appointments,
                           deleted_appointments=deleted_appointments)

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    print("Incoming webhook message:", data)

    message = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
    sender = message.get("from")

    if "interactive" in message:
        interactive = message["interactive"]
        if "button_reply" in interactive:
            button_reply = interactive["button_reply"]["id"]
            handle_button_response(sender, button_reply)
        elif "list_reply" in interactive:
            list_reply = interactive["list_reply"]["id"]
            handle_list_response(sender, list_reply)
    else:
        text = message.get("text", {}).get("body")
        if text:
            handle_text_message(sender, text)

    return jsonify({"status": "received"}), 200

def handle_list_response(sender, list_reply_id):
    session = user_sessions.get(sender, {})
    if not session:
        send_message(sender, "Session expired. Please start over.")
        return

    step = session.get("step")

    # Handling department selection
    if step == "department" and list_reply_id in departments:
        selected_department = departments[list_reply_id]
        user_sessions[sender]["step"] = "doctor"
        user_sessions[sender]["department"] = list_reply_id
        user_sessions[sender]["department_name"] = selected_department["name"]
        send_doctor_list(sender, selected_department["doctors"])

    # Handling doctor selection
    elif step == "doctor" and "department" in session:
        department_id = session.get("department")
        selected_department = departments.get(department_id)

        if selected_department:
            doctors = selected_department.get("doctors", [])
            if list_reply_id in [str(i + 1) for i in range(len(doctors))]:
                selected_doctor = doctors[int(list_reply_id) - 1]
                user_sessions[sender]["doctor"] = selected_doctor
                user_sessions[sender]["step"] = "name"
                send_message(sender, get_translated_text("Please provide your name:", session["language"]))
            else:
                send_message(sender, get_translated_text("Invalid doctor selection. Please try again.", session["language"]))
        else:
            send_message(sender, get_translated_text("Department not found.", session["language"]))

    # Handling date selection
    # Handle date selection and proceed to time selection
    elif step == "date" and list_reply_id in fetch_available_dates_for_whatsapp():
        selected_date = list_reply_id  # Store selected date from user response
        user_sessions[sender]["selected_date"] = selected_date  # Save selected date in session
    
    # Log for debugging
        print(f"Selected Date: {selected_date}")
    
    # Fetch available times for the selected date and send them
        available_times = fetch_available_times_for_whatsapp(selected_date)

    
        send_appointment_summary(sender)
        user_sessions[sender]["step"] = "confirm"  # Move directly to confirmation step
    
#         if available_times:  # Check if times are fetched correctly
#             send_time_list(sender, available_times)  # Send the available times list
#             user_sessions[sender]["step"] = "time"  # Move to the time selection step
#         else:
#             # Log if no times are found for the selected date
#             print(f"No times found for selected date: {selected_date}")
#             send_message(sender, "Sorry, no times are available for this date. Please select another date.")

# # Handle time selection and proceed to confirmation
#     elif step == "time" and list_reply_id in fetch_available_times_for_whatsapp(user_sessions[sender]["selected_date"]):
#         selected_time = list_reply_id  # Store selected time from user response
#         user_sessions[sender]["selected_time"] = selected_time  # Save selected time in session
    
#     # Log for debugging
#         print(f"Selected Time: {selected_time}")
    
#     # Send appointment summary and move to confirmation step
#         send_appointment_summary(sender)
#         user_sessions[sender]["step"] = "confirm"

    else:
        send_message(sender, get_translated_text("Invalid selection. Please try again.", session["language"]))

def handle_text_message(sender, text):

    session = user_sessions.get(sender, {})
    print(f"Session for {sender}: {session}")

    if not session:
        # Start by sending language selection buttons
        send_button_message(sender, "Kindly select your preferred language:/దయచేసి మీకు నచ్చిన భాషను ఎంచుకోండి:", [
            {"id": "english", "title": "English"},
            {"id": "telugu", "title": "తెలుగు"},
        ])
        user_sessions[sender] = {"step": "language"}
    else:
        step = session.get("step")
        if step == "name":
            user_sessions[sender]["name"] = text
            send_message(sender, get_translated_text("Please provide your email:", session["language"]))
            user_sessions[sender]["step"] = "email"
        elif step == "email":
            if "@" in text and "." in text:
                user_sessions[sender]["email"] = text
                send_button_message(sender, get_translated_text("Please select your gender:", session["language"]), [
                    {"id": "male", "title": get_translated_text("Male", session["language"])},
                    {"id": "female", "title": get_translated_text("Female", session["language"])},
                ])
                user_sessions[sender]["step"] = "gender"
            else:
                send_message(sender, get_translated_text("Invalid email format. Please provide a valid email.", session["language"]))
        elif step == "age":
            try:
                age = int(text)
                user_sessions[sender]["age"] = age
                send_date_list(sender)
                user_sessions[sender]["step"] = "date"
            except ValueError:
                send_message(sender, get_translated_text("Please enter a valid age.", session["language"]))

        elif step == "confirm":
            if text.lower() == "confirm":
                if session["department_name"] == "Cardiology":
                    send_message(sender, f""" Dear {session['name']},
                
        

Congratulations! Your appointment with  {session['doctor']} is confirmed for  {session['selected_date']} and you will get the call for time slot with in 10 minutes from our side.

Please note that hospital visits usually take about 2 hours, and delays may occur due to emergencies.

At Pulse Heart Center, your condition will be thoroughly evaluated, and treatment options will be provided. Please bring all medical files, current medications, and, if applicable, angiogram CDs or past reports.

For emergencies, you can visit our ER, open 24/7.

Location: https://maps.app.goo.gl/bjWGKqGK4kAcNvxT9

Thank you, and we look forward to seeing you!
Team Pulse Heart
""")
                else:
                    send_message(sender, get_translated_text("Your appointment has been successfully booked!",
                                                             session["language"]))
                del user_sessions[sender]
            elif step == "confirm":
                if text.lower() == "confirm":
                    send_message(sender,get_translated_text("Your appointment has been successfully booked!",session["language"]))
            elif text.lower() == "edit":
                send_message(sender, get_translated_text("Please provide your name:", session["language"]))
                user_sessions[sender]["step"] = "name"
            else:
                send_message(sender, get_translated_text("Invalid response. Please reply 'Confirm' or 'Edit'.", session["language"]))

def handle_button_response(sender, button_id):
    session = user_sessions.get(sender, {})
    if not session:
        send_message(sender, "Session expired. Please start over.")
        return

    step = session.get("step")

    if button_id == "english" or button_id == "telugu":
        # Handle language selection
        user_sessions[sender]["language"] = button_id
        send_image(sender)
        send_button_message(sender, get_translated_text("Welcome to Pulse Heart Super Speciality Hospital! How may we assist you today?", button_id), [
            {"id": "book_appointment", "title": get_translated_text("Book Appointment", button_id)},
            {"id": "location", "title": get_translated_text("Location", button_id)},
        ])
        user_sessions[sender]["step"] = "start"
    elif button_id == "book_appointment":
        user_sessions[sender]["step"] = "department"
        send_department_list(sender)
    elif button_id == "location":
        send_message(sender, get_translated_text("https://maps.app.goo.gl/bjWGKqGK4kAcNvxT9", session["language"]))
    elif step == "department" and button_id in departments:
        selected_department = departments[button_id]
        user_sessions[sender]["step"] = "doctor"
        user_sessions[sender]["department"] = button_id
        user_sessions[sender]["department_name"] = selected_department["name"]
        send_doctor_list(sender, selected_department["doctors"])
    elif step == "gender":
        user_sessions[sender]["gender"] = button_id
        send_message(sender, get_translated_text("Please provide your age:", session["language"]))
        user_sessions[sender]["step"] = "age"

def send_message(sender, text):
    url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "text": {"body": text},
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Sent message to {sender}: {response.json()}")

def send_button_message(sender, text, buttons):
    url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": [{"type": "reply", "reply": button} for button in buttons]}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Sent button message to {sender}: {response.json()}")

def send_image(sender):
    url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "image",
        "image": {"id": media_id}
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Sent image to {sender}: {response.json()}")

def send_department_list(sender):
    url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    sections = [{
        "title": get_translated_text("Departments", user_sessions[sender]["language"]),
        "rows": [{"id": dept_id, "title": dept_info["name"]} for dept_id, dept_info in departments.items()]
    }]
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "list",
            # "header": {"type": "text", "text": get_translated_text("Select Department", user_sessions[sender]["language"])},
            "body": {"text": get_translated_text("Please choose a department:", user_sessions[sender]["language"])},
            "action": {"button": get_translated_text("Select", user_sessions[sender]["language"]), "sections": sections}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Sent department list to {sender}: {response.json()}")

def send_doctor_list(sender, doctors):
    url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    sections = [{
        "title": get_translated_text("Doctors", user_sessions[sender]["language"]),
        "rows": [{"id": str(i + 1), "title": doctor} for i, doctor in enumerate(doctors)]
    }]
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "list",
            # "header": {"type": "text", "text": get_translated_text("Select Doctor", user_sessions[sender]["language"])},
            "body": {"text": get_translated_text("Please choose a doctor:", user_sessions[sender]["language"])},
            "action": {"button": get_translated_text("Select", user_sessions[sender]["language"]), "sections": sections}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Sent doctor list to {sender}: {response.json()}")

def send_date_list(sender):
    url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    sections = [{
        "title": get_translated_text("Available Dates", user_sessions[sender]["language"]),
        "rows": [{"id": date, "title": date} for date in fetch_available_dates_for_whatsapp()]
    }]
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "list",
            # "header": {"type": "text", "text": get_translated_text("Select Date", user_sessions[sender]["language"])},
            "body": {"text": get_translated_text("Please choose a date:", user_sessions[sender]["language"])},
            "action": {"button": get_translated_text("Select", user_sessions[sender]["language"]), "sections": sections}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Sent date list to {sender}: {response.json()}")

def send_time_list(sender, times):
    url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {GRAPH_API_TOKEN}"}
    sections = [{
        "title": get_translated_text("Available Times", user_sessions[sender]["language"]),
        "rows": [{"id": time, "title": time} for time in times]
    }]
    payload = {
        "messaging_product": "whatsapp",
        "to": sender,
        "type": "interactive",
        "interactive": {
            "type": "list",
            # "header": {"type": "text", "text": get_translated_text("Select Time", user_sessions[sender]["language"])},
            "body": {"text": get_translated_text("Please choose a time:", user_sessions[sender]["language"])},
            "action": {"button": get_translated_text("Select", user_sessions[sender]["language"]), "sections": sections}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Sent time list to {sender}: {response.json()}")

def send_appointment_summary(sender):
    session = user_sessions[sender]
    connection = get_db_connection()
    cursor = connection.cursor()

    # Insert the appointment data into the database with the updated fields (without selected_time)
    insert_query = """
        INSERT INTO appointments (sender, name, email, age, gender, department_name, doctor, selected_date, language, created_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'Pending')
    """
    
    # Appointment data tuple with the new fields included (no selected_time)
    appointment_data = (
        sender,                              # Phone Number
        session['name'],                     # Name
        session['email'],                    # Email
        session['age'],                      # Age
        session['gender'],                   # Gender
        session['department_name'],          # Department
        session['doctor'],                   # Doctor
        session['selected_date'],            # Appointment Date
        session['language']                  # Language
    )

    # Execute the query and commit the transaction
    try:
        cursor.execute(insert_query, appointment_data)
        connection.commit()  # Commit the transaction
        print("Appointment data inserted successfully")
    except Exception as e:
        print(f"Error inserting appointment data: {e}")
        connection.rollback()  # Rollback the transaction in case of error
    finally:
        cursor.close()
        connection.close()

    # Prepare and send the appointment summary without the time field
    summary = (
        f"{get_translated_text('Appointment Summary:', session['language'])}\n"
        f"{get_translated_text('Name:', session['language'])} {session['name']}\n"
        f"{get_translated_text('Email:', session['language'])} {session['email']}\n"
        f"{get_translated_text('Age:', session['language'])} {session['age']}\n"
        f"{get_translated_text('Gender:', session['language'])} {session['gender']}\n"
        f"{get_translated_text('Department:', session['language'])} {session['department_name']}\n"
        f"{get_translated_text('Doctor:', session['language'])} {session['doctor']}\n"
        f"{get_translated_text('Date:', session['language'])} {session['selected_date']}\n"
    )
    
    # Send the summary to the user
    send_message(sender, summary)
    send_message(sender, get_translated_text("Please confirm your appointment by replying 'Confirm' or reply 'Edit' to make changes.", session['language']))




def fetch_available_dates_for_whatsapp():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT  available date FROM available_dates ORDER BY available_date DESC")
    available_dates = [row[0].strftime("%Y-%m-%d") for row in cursor.fetchall()]  # Convert to strings
    conn.close()
    return available_dates

def fetch_available_times_for_whatsapp(selected_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the date_id based on the selected date
    cursor.execute("SELECT id FROM available_dates WHERE available_date = %s", (selected_date,))
    result = cursor.fetchone()

    if result:
        date_id = result[0]

        # Fetch the available times using the date_id
        cursor.execute("SELECT available_time FROM available_times WHERE date_id = %s", (date_id,))
        available_times = [row[0] for row in cursor.fetchall()]  # Already stored as strings
    else:
        # No date_id found for the selected_date, return an empty list
        available_times = []

    conn.close()
    return available_times



def get_translated_text(text, language):
    translations = {
        "english": {
            "Please provide your name:": "Please provide your name:",
            "Please provide your email:": "Please provide your email:",
            "Please select your gender:": "Please select your gender:",
            "Male": "Male",
            "Female": "Female",
            "Please provide your age:": "Please provide your age:",
            "Appointment Summary:": "Appointment Summary:",
            "Name:": "Name:",
            "Email:": "Email:",
            "Department:": "Department:",
            "Doctor:": "Doctor:",
            "Date:": "Date:",
            "Time:": "Time:",
            "Please confirm your appointment by replying 'Confirm' or reply 'Edit' to make changes.":
                "Please confirm your appointment by replying 'Confirm' or reply 'Edit' to make changes.",
            "Select Department": "Select Department",
            "Please choose a department:": "Please choose a department:",
            "Select": "Select",
            "Departments": "Departments",
            "Doctors": "Doctors",
            "Select Doctor": "Select Doctor",
            "Please choose a doctor:": "Please choose a doctor:",
            "Available Dates": "Available Dates",
            "Select Date": "Select Date",
            "Please choose a date:": "Please choose a date:",
            "Available Times": "Available Times",
            "Select Time": "Select Time",
            "Please choose a time:": "Please choose a time:",
        },
        "telugu": {
            "Welcome to Pulse Heart Super Speciality Hospital! How may we assist you today?": "పల్స్ హార్ట్ సూపర్ స్పెషాలిటీ ఆసుపత్రికి స్వాగతం! ఈరోజు మేము మీకు ఎలా సహాయం చేయవచ్చు?",
            "Book Appointment": "అపాయింట్‌మెంట్ బుక్ చేయండి",
            "Location": "స్థానం",
            "Please provide your name:": "మీ పేరు అందించండి:",
            "Please provide your email:": "మీ ఈమెయిల్ అందించండి:",
            "Please select your gender:": "దయచేసి మీ లింగాన్ని ఎంచుకోండి:",
            "Male": "పురుషుడు",
            "Female": "స్త్రీ",
            "Please provide your age:": "మీ వయసును అందించండి:",
            "Appointment Summary:": "అపాయింట్‌మెంట్ సారాంశం:",
            "Name:": "పేరు:",
            "Email:": "ఈమెయిల్:",
            "Department:": "విభాగం:",
            "Doctor:": "డాక్టర్:",
            "Date:": "తేదీ:",
            "Time:": "సమయం:",
            "Please confirm your appointment by replying 'Confirm' or reply 'Edit' to make changes.":
                "దయచేసి మీ అపాయింట్‌మెంట్‌ని 'Confirm' అని ప్రతిస్పందించండి లేదా మార్పులు చేయడానికి 'Edit' అని ప్రతిస్పందించండి.",
            "Select Department": "విభాగాన్ని ఎంచుకోండి",
            "Please choose a department:": "దయచేసి విభాగాన్ని ఎంచుకోండి:",
            "Select": "ఎంచుకోండి",
            "Departments": "విభాగాలు",
            "Doctors": "డాక్టర్లు",
            "Select Doctor": "డాక్టర్‌ని ఎంచుకోండి",
            "Please choose a doctor:": "దయచేసి డాక్టర్‌ని ఎంచుకోండి:",
            "Available Dates": "అందుబాటులో ఉన్న తేదీలు",
            "Select Date": "తేదీని ఎంచుకోండి",
            "Please choose a date:": "దయచేసి తేదీని ఎంచుకోండి:",
            "Available Times": "అందుబాటులో ఉన్న సమయాలు",
            "Select Time": "సమయాన్ని ఎంచుకోండి",
            "Please choose a time:": "దయచేసి సమయాన్ని ఎంచుకోండి:",
            "Your appointment has been successfully booked!": "మీ అపాయింట్‌మెంట్ విజయవంతంగా బుక్ చేయబడింది!",
        }
    }
    return translations.get(language, {}).get(text, text)

if __name__ == "__main__":
    app.run(port=PORT, debug=True)
