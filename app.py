from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection function
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Dhana@123",
        database="db_server_inventory"
    )
    return conn

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Redirect root URL to home page
@app.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)", 
                           (first_name, last_name, email, password))
            conn.commit()
            flash("Signup successful! Please log in.", 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred while registering: {str(e)}", 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['username'] = user['first_name']
                flash("Login successful!", 'success')
                return redirect(url_for('index'))
            else:
                flash("Invalid email or password.", 'danger')
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('login.html')

# Add account route
@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)", 
                           (first_name, last_name, email, password))
            conn.commit()
            flash("Account added successfully!", 'success')
            return redirect(url_for('account'))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'error')
        finally:
            cursor.close()
            conn.close()
    return render_template('add_account.html')

# Account route
@app.route('/account')
@login_required
def account():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT first_name, last_name, email FROM users WHERE id = %s", (session['user_id'],))
        user_details = cursor.fetchone()
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        user_details = {'first_name': '', 'last_name': '', 'email': ''}
    finally:
        cursor.close()
        conn.close()
    return render_template('account.html', user_details=user_details)




# Home route
@app.route('/home')
@login_required
def home():
    return redirect(url_for('index'))

# Index route
@app.route('/index')
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Pagination and Search
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    per_page = 10  # Adjust per your need

    try:
        if search_query:
            query = "SELECT * FROM servers WHERE server_name LIKE %s OR ip_address LIKE %s OR dns_name LIKE %s ORDER BY id DESC"
            cursor.execute(query, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        else:
            cursor.execute("SELECT * FROM servers ORDER BY id DESC")
        
        servers = cursor.fetchall()
        total_servers = len(servers)
        total_pages = (total_servers // per_page) + (1 if total_servers % per_page > 0 else 0)

        # Calculate the offset and limit for pagination
        offset = (page - 1) * per_page
        servers = servers[offset:offset + per_page]

        return render_template('index.html', servers=servers, page=page, total_pages=total_pages, search_query=search_query)
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return render_template('index.html', servers=[], page=1, total_pages=1, search_query=search_query)
    finally:
        cursor.close()
        conn.close()

# Create server route
@app.route('/create_server', methods=['GET', 'POST'])
@login_required
def create_server():
    if request.method == 'POST':
        try:
            data = {
                'server_name': request.form['server_name'],
                'cpu_allocated': request.form['cpu_allocated'],
                'memory_allocated': request.form['memory_allocated'],
                'uptime': request.form['uptime'],
                'last_patch': request.form['last_patch'],
                'installed_apps': request.form['installed_apps'],
                'dns_name': request.form['dns_name'],
                'ip_address': request.form['ip_address'],
                'server_owner': request.form['server_owner'],
                'application_owner': request.form['application_owner'],
                'application_description': request.form['application_description'],
                'disk_space_allocated': request.form['disk_space_allocated'],
                'os_version': request.form['os_version'],
                'last_run_time': datetime.strptime(request.form['last_run_time'], '%Y-%m-%dT%H:%M')
            }
            conn = get_db_connection()
            cursor = conn.cursor()
            
            sql = """INSERT INTO servers (server_name, cpu_allocated, memory_allocated, uptime, last_patch, 
                     installed_apps, dns_name, ip_address, server_owner, application_owner,
                     application_description, disk_space_allocated, os_version, last_run_time)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, tuple(data.values()))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Server created successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            if 'conn' in locals():
                cursor.close()
                conn.close()
    return render_template('create_server.html')




# Read servers route
@app.route('/read_servers')
@login_required
def read_servers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM servers ORDER BY id DESC")
        servers = cursor.fetchall()
        return render_template('read_servers.html', servers=servers)
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return render_template('read_servers.html', servers=[])
    finally:
        cursor.close()
        conn.close()
      
# Update server route
 
@app.route('/server/<int:server_id>/update', methods=['GET', 'POST'])
@login_required
def update_server(server_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        data = {
            'server_name': request.form['server_name'],
            'cpu_allocated': request.form['cpu_allocated'],
            'memory_allocated': request.form['memory_allocated'],
            'uptime': request.form['uptime'],
            'last_patch': request.form['last_patch'],
            'installed_apps': request.form['installed_apps'],
            'dns_name': request.form['dns_name'],
            'ip_address': request.form['ip_address'],
            'server_owner': request.form['server_owner'],
            'application_owner': request.form['application_owner'],
            'application_description': request.form['application_description'],
            'disk_space_allocated': request.form['disk_space_allocated'],
            'os_version': request.form['os_version'],
            'last_run_time': datetime.strptime(request.form['last_run_time'], '%Y-%m-%dT%H:%M')
        }
        try:
            sql = """UPDATE servers SET server_name=%s, cpu_allocated=%s, memory_allocated=%s,
                     uptime=%s, last_patch=%s, installed_apps=%s, dns_name=%s, ip_address=%s,
                     server_owner=%s, application_owner=%s, application_description=%s,
                     disk_space_allocated=%s, os_version=%s, last_run_time=%s WHERE id=%s"""
            cursor.execute(sql, tuple(data.values()) + (server_id,))
            conn.commit()
            flash('Server updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
    cursor.execute("SELECT * FROM servers WHERE id = %s", (server_id,))
    server = cursor.fetchone()
    return render_template('edit_server.html', server=server)

# View server route
@app.route('/server/<int:server_id>')
@login_required
def view_server(server_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM servers WHERE id = %s", (server_id,))
    server = cursor.fetchone()
    cursor.close()
    conn.close()
    if not server:
        flash("Server not found.", 'error')
        return redirect(url_for('index'))
    return render_template('view_server.html', server=server)





# Confirm delete server route
@app.route('/server/<int:server_id>/confirm_delete', methods=['GET'])
@login_required
def confirm_delete(server_id):
    return render_template('delete_server.html', server_id=server_id)

# Delete server route
@app.route('/server/<int:server_id>/delete', methods=['POST'])
@login_required
def delete_server(server_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM servers WHERE id = %s", (server_id,))
        conn.commit()
        flash('Server deleted successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

# Contact route
@app.route('/contact')
def contact():
    support_email = "inventroysupport@gmail.com"
    support_phone = "+123-456-7890"
    return render_template('contact.html', support_email=support_email, support_phone=support_phone)

# Logout route
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)