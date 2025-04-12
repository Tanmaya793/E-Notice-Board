from flask import Flask, request, render_template, redirect, url_for, flash, session
import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(32)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'tana9861751892@',
    'database': 'notice_board'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        user_type = request.form.get('userType')
        course = request.form.get('course')
        branch = request.form.get('branch')
        phone = request.form.get('phone')
        roll_number = request.form.get('rollNumber')
        designation = request.form.get('designation')
        subject = request.form.get('subject')
        batch = request.form.get('batch')
        recovery_pin = request.form.get('secret')

        if not full_name or not email or not password or not confirm_password or not user_type:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))

        cursor.execute(
            "INSERT INTO users (full_name, email, password, user_type, course, phone, branch, roll_number, designation, subject, batch, recovery_pin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (full_name, email, hashed_password, user_type, course, phone, branch, roll_number, designation, subject, batch, recovery_pin)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_type'] = user['user_type']
            session['email'] = user['email']
            session['full_name'] = user['full_name']
            flash('Login successful!', 'success')
            return redirect(url_for('first')) 
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/first')
def first():
    if 'user_id' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('login'))

    email = session['email']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT full_name, email, user_type, course, branch, phone FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if user:
        return render_template("first.html", user=user) 
    else:
        flash("User not found", "error")
        return redirect(url_for("login"))


@app.route('/all_notices')
def all_notices():
    if 'email' not in session:
        flash('Please log in to view notices.', 'danger')
        return redirect(url_for('login'))

    email = session['email']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get user_id
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('login'))

        user_id = user['id']

        cursor.execute("""
            SELECT n.notice_id, n.title, n.date_posted, n.content, n.exp_date,
            u.user_type AS posted_by_type
            FROM notice n
            JOIN recepient r ON n.notice_id = r.notice_id
            JOIN users u ON n.posted_by = u.id
            WHERE r.user_id = %s
            ORDER BY n.date_posted DESC
        """, (user_id,))

        notices = cursor.fetchall()

        return render_template('all-notices.html', notices=notices)

    except Exception as e:
        print("Error:", e)
        flash("Something went wrong while fetching notices.", "danger")
        return redirect(url_for('first'))

    finally:
        cursor.close()
        conn.close()


@app.route('/create_notice')
def create_notice():
    return render_template('create-notice.html')

@app.route('/create', methods=['POST'])
def create():
    if 'email' not in session:
        flash('You must be logged in to create a notice.', 'danger')
        return redirect(url_for('login'))

    email = session['email']
    title = request.form['title']
    content = request.form['content']
    date_posted = request.form['datePosted']
    exp_date = request.form['expDate']
    selected_roles = request.form.getlist('receivers') 

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('create_notice'))

        user_id = user[0]

        cursor.execute("""
            INSERT INTO notice (title, content, date_posted, exp_date, posted_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, content, date_posted, exp_date, user_id))
        notice_id = cursor.lastrowid 

        # Insert into recipient table (optional - seems like it's just linking notice to sender?)
        # For each selected role, insert into sent and recepient tables
        for role in selected_roles:
            cursor.execute("SELECT id FROM users WHERE user_type = %s", (role.lower(),))
            user_ids = cursor.fetchall()
            for uid in user_ids:
                receiver_id = uid[0]

                # Insert into sent table
                cursor.execute("""
                    INSERT INTO sent (notice_id, sent_to)
                    VALUES (%s, %s)
                """, (notice_id, receiver_id))

                # Insert into recepient table
                cursor.execute("""
                    INSERT INTO recepient (notice_id, user_id, status)
                    VALUES (%s, %s, %s)
                """, (notice_id, receiver_id, 'unread'))


        # For each selected role, insert an entry in the sent table for each user
        for role in selected_roles:
            cursor.execute("SELECT id FROM users WHERE user_type = %s", (role.lower(),))
            user_ids = cursor.fetchall()
            for uid in user_ids:
                cursor.execute("""
                    INSERT INTO sent (notice_id, sent_to)
                    VALUES (%s, %s)
                """, (notice_id, uid[0]))

        conn.commit()
        flash('Notice sent successfully!', 'success')

    except Exception as e:
        print("Error occurred:", str(e))
        flash(f'Error: {str(e)}', 'danger')

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('create_notice'))



@app.route('/recovery')
def recovery():
    return render_template('recovery.html')

@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'POST':
        email = request.form.get('recovery-email')
        recovery = request.form.get('recovery-pin')

        if not email or not recovery:
            flash('Both email and recovery PIN are required', 'error')
            return redirect(url_for('recover'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user != 0:
                if user['recovery_pin'] == int(recovery):
                    session['recovery_email'] = email 
                    flash('Recovery PIN matched! You can now reset your password.', 'success')
                    return redirect(url_for('reset_page')) 
                else:
                    flash('Invalid recovery PIN', 'error')
            else:
                flash('Email not found', 'error')

        except mysql.connector.Error as err:
            flash('An error occurred. Please try again later.', 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('recovery.html', email=recovery)

@app.route('/reset_page')
def reset_page():
    return render_template('reset.html')

@app.route('/notices')
def show_notices():
    if 'email' not in session:
        flash('Please log in to view your notices.', 'danger')
        return redirect(url_for('login'))

    email = session['email']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get current user's ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('login'))

        user_id = user['id']

        # Fetch notices sent to this user
        # Fetch notices sent to this user, showing posted_by as user_type instead of email
        cursor.execute("""
            SELECT n.notice_id, n.title, n.content, n.date_posted, n.exp_date, u.user_type AS posted_by
            FROM notice n
            JOIN sent s ON n.notice_id = s.notice_id
            JOIN users u ON n.posted_by = u.id
            WHERE s.sent_to = %s
            ORDER BY n.date_posted DESC
        """, (user_id,))

        
        notices = cursor.fetchall()
        for n in notices:
            print(n)


    except Exception as e:
        print("Error loading notices:", e)
        flash('Error loading notices.', 'danger')
        notices = []
    finally:
        cursor.close()
        conn.close()

    return render_template('notices.html', notices=notices)

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if 'recovery_email' not in session:
        flash('Please complete the recovery process first.', 'error')
        return redirect(url_for('recover'))

    email = session['recovery_email']

    if request.method == 'POST':
        new_password = request.form.get('new-password')
        confirm_password = request.form.get('confirm-password')

        if not new_password or not confirm_password:
            flash('Both fields are required.', 'error')
            return render_template('reset.html', email=email)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset.html', email=email)

        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
            conn.commit()
            flash('Your password has been successfully reset!', 'success')
            session.pop('recovery_email', None) 
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash('An error occurred. Please try again later.', 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('reset.html', email=email)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('login'))
    return f"Welcome {session['full_name']} to the Dashboard!"

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route("/")
def index():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/home")
def home():
    images = [
        'images/notice1.png',
        'images/notice2.png',
        'images/notice3.png',
        'images/notice4.png'
    ]
    return render_template('home.html',images=images)
if __name__ == '__main__':
    app.run(debug=False)
