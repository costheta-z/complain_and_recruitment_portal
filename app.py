# personal details in facultyDB, studentDB
# complain oriented information in complainsDB's

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import make_response
from flask_mysqldb import MySQL, MySQLdb
import MySQLdb.cursors
import re
from werkzeug.utils import secure_filename
import os
import urllib
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import pdfkit

app = Flask(__name__)
warning=""

app.secret_key = 'put your secret key here'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'put you password here'
app.config['MYSQL_DB'] = 'put your db name here'

mysql = MySQL(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['pdf'])
who=''

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/stu_or_fac')
def stu_or_fac():
	global who
	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

	cur.execute('''
	CREATE TABLE IF NOT EXISTS studentDB (enrol_no varchar(20) NOT NULL PRIMARY KEY, 
	first_name varchar(50) NOT NULL, last_name varchar(50) NOT NULL default \'\', 
	password varchar(300) NOT NULL, gender varchar(10) DEFAULT \'Other\',
	category varchar(30) NOT NULL, email varchar(100) NOT NULL, department varchar(50), mobile_no varchar(10))
	''')

	cur.execute('''
	CREATE TABLE IF NOT EXISTS stu_complainsDB (complain_id integer primary key auto_increment, 
	enrol_no varchar(20) not null, status integer default 0, complain_type varchar(20),
	complain_details varchar(500))
	''')

	cur.execute('''
	CREATE TABLE IF NOT EXISTS facultyDB (emp_id varchar(20) NOT NULL PRIMARY KEY, 
	first_name varchar(50) NOT NULL, last_name varchar(50) NOT NULL default \'\', 
	password varchar(300) NOT NULL, gender varchar(10) DEFAULT \'Other\',
	category varchar(30) NOT NULL, email varchar(100) NOT NULL, department varchar(50), mobile_no varchar(10))
	''')

	cur.execute('''
	CREATE TABLE IF NOT EXISTS fac_complainsDB (complain_id integer primary key auto_increment, 
	emp_id varchar(20) not null, status integer default 0, complain_type varchar(20),
	complain_details varchar(500), designation varchar(20) NOT NULL)
	''')

	cur.execute('''
	CREATE TABLE IF NOT EXISTS adminDB (email varchar(40) primary key, 
	password varchar(300) not null)
	''')

	adminemail='nandinikapoor24601@gmail.com'
	password='adminpassword'
	password=generate_password_hash(password)

	cur.execute('select * from adminDB where email=%s', (adminemail, ))
	
	adm=cur.fetchone()
	if not adm:
		cur.execute('''
		INSERT INTO adminDB values (%s, %s)
		''', (adminemail, password, ))
		mysql.connection.commit()


	cur.close()
	msg = 'Log in as Student/Faculty/Admin'
	return render_template('sorf.html', msg = msg)

@app.route('/determine', methods =['GET', 'POST'])
def determine():
	global who
	if request.method == 'POST':
		who = request.form['user']
		print('here')
	return redirect(url_for('login'))

@app.route('/login', methods =['GET', 'POST'])
def login():
	global who
	print(who)
	msg = 'Log In'
	if who=='Student':
		msg = 'Student Log In'
	elif who=='Admin':
		msg = 'Admin Log In'
	else:
		msg = 'Faculty Log In'
	if request.method == 'POST' and 'ID' in request.form and 'password' in request.form:
		id = request.form['ID']
		password = request.form['password']
		cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		if who=='Student':
			cur.execute('SELECT * FROM studentDB WHERE enrol_no = % s', (id, ))
		elif who=='Faculty':
			cur.execute('SELECT * FROM facultyDB WHERE emp_id = % s', (id, ))
		else:
			cur.execute('SELECT * FROM adminDB WHERE email = %s', (id, ))
		account = cur.fetchone()
		cur.close()
		if account and check_password_hash (account['password'], password):
			session['loggedin'] = True
			session['id'] = id
			msg = 'Logged in successfully'
			if who!='Admin':
				return redirect(url_for('complain_form'))
			else:
				return redirect(url_for('admin'))
		else:
			msg = 'Incorrect username or password'
	return render_template('login.html', msg = msg)

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('who', None)
	return redirect(url_for('stu_or_fac'))

@app.route('/register', methods =['GET', 'POST'])
def register():
	global who
	msg = 'Register'
	if who=='Admin':
		if request.method == 'POST' and 'email' in request.form:
			id=request.form['email']
			password = request.form['password']
			password=generate_password_hash(password)
			cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cur.execute('SELECT * FROM adminDB WHERE email = % s', (id, ))
			account = cur.fetchone()
			cur.close()
			if account:
				msg='This id is already registered'
				return render_template('register.html', msg = msg)
			elif password=='' or id=='':
				msg = 'Please fill out the form completely'
			elif not re.match(r'[^@]+@[^@]+\.[^@]+', id):
				msg = 'Invalid email address'
			else:
				cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
				cur.execute('insert into adminDB values (%s, %s)', (id, password, ))
				mysql.connection.commit()
				cur.close()
		elif request.method == 'POST':
			msg = 'Please fill out the form completely'
		return render_template('register_adm', msg=msg)

	elif request.method == 'POST' and 'ID' in request.form and 'password' in request.form and 'email' in request.form:
		id = request.form['ID']
		password = request.form['password']
		password=generate_password_hash(password)
		fname = request.form['fname']
		lname = request.form['lname']
		gender = request.form['gender']
		category = request.form['category']
		email = request.form['email']
		dept = request.form['department']
		mobile = request.form['mobile']
		cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		if who=='Student':
			cur.execute('SELECT * FROM studentDB WHERE enrol_no = % s', (id, ))
		elif who=='Faculty':
			cur.execute('SELECT * FROM facultyDB WHERE emp_id = % s', (id, ))
		account = cur.fetchone()
		cur.close()
		if account:
		    msg='This id is already registered'
		    return render_template('register.html', msg = msg)
		elif id=='' or password=='' or email=='':
			msg = 'Please fill out the form completely'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address'
		elif not re.match(r'[A-Za-z0-9]+', id):
			msg = 'ID must contain only characters and numbers'
		else:
			cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			if who=='Student':
				cur.execute('''insert into studentDB values 
				(% s, %s, %s, %s, %s, %s, %s, %s, %s)
				''', (id, fname, lname, password, gender, category, email, dept, mobile, ))
			elif who=='Faculty':
				cur.execute('''INSERT INTO facultyDB VALUES 
				(% s, %s, %s, %s, %s, %s, %s, %s, %s)
				''', (id, fname, lname, password, gender, category, email, dept, mobile, ))
			mysql.connection.commit()
			cur.close()
			msg = 'You have successfully registered'
	elif request.method == 'POST':
		msg = 'Please fill out the form completely'
	return render_template('register.html', msg = msg)

@app.route('/admin', methods =['GET', 'POST'])
def admin():
	if 'id' not in session:
		return redirect(url_for('login'))
	ids=[]
	cids=[]
	descs=[]
	types=[]
	statuses=[]
	thru=[]
	sid=[]
	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cur.execute('SELECT * FROM stu_complainsDB JOIN studentDB ON stu_complainsDB.enrol_no=studentDB.enrol_no')
	files_are = cur.fetchall()
	cur.execute('SELECT * FROM fac_complainsDB JOIN facultyDB ON fac_complainsDB.emp_id=facultyDB.emp_id')
	files_are2 = cur.fetchall()
	cur.close()
	for file in files_are:
		cids.append(file['complain_id'])
		descs.append(file['complain_details'])
		types.append(file['complain_type'])
		if(file['status']==1):
			statuses.append('Resolved')
		else:
			statuses.append('Unresolved')
		ids.append(file['enrol_no'])
		thru.append('student')
		sid.append(str(file['complain_id'])+'s')
	for file in files_are2:
		cids.append(file['complain_id'])
		descs.append(file['complain_details'])
		types.append(file['complain_type'])
		if(file['status']==1):
			statuses.append('Resolved')
		else:
			statuses.append('Unresolved')
		ids.append(file['emp_id'])
		thru.append('faculty')
		sid.append(str(file['complain_id'])+'f')
	print(len(files_are2))
	return render_template('index.html', lis=zip(cids, statuses, types, descs, ids, thru, sid))
	

@app.route('/complain_form', methods =['GET', 'POST'])
def complain_form():
	cids=[]
	statuses=[]
	types=[]
	descs=[]
	comb=[]
	global who
	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	if who=='Student':
		cur.execute('SELECT * FROM stu_complainsDB WHERE enrol_no = % s', (session['id'], ))
	else:
		cur.execute('SELECT * FROM fac_complainsDB WHERE emp_id = % s', (session['id'], ))
	files_are = cur.fetchall()
	cur.close()
	for file in files_are:
		cids.append(file['complain_id'])
		descs.append(file['complain_details'])
		types.append(file['complain_type'])
		if(file['status']==1):
			statuses.append('Resolved')
		else:
			statuses.append('Unresolved')
		cids.append(file['complain_id'])
		if who=='Student':
			comb.append(str(file['complain_id'])+'s')
		else:
			comb.append(str(file['complain_id'])+'f')
	return render_template('complain_form.html', lis=zip(cids, statuses, types, descs, comb))


@app.route("/upload",methods=["POST","GET"])
def upload():
	global who
	if request.method == 'POST':
		title = request.form['title']
		desc = request.form['description']
		desig=request.form['designation']
		cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		if who=='Student':
			cur.execute('SELECT * FROM studentDB WHERE enrol_no = % s', (session['id'], ))
		else:
			cur.execute('SELECT * FROM facultyDB WHERE emp_id = % s', (session['id'], ))
		account = cur.fetchone()
		cur.close()
		if who=='Faculty':
			id=account['emp_id']
			cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cur.execute('''INSERT INTO fac_complainsDB (emp_id, status, complain_type, complain_details, 
			designation) VALUES (%s, %s, %s, %s, %s)
			''',(session['id'], 0, title, desc, desig))
			mysql.connection.commit()
			cur.close()
		else:
			id=account['enrol_no']
			cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cur.execute('''INSERT INTO stu_complainsDB (enrol_no, status, complain_type, complain_details) 
			VALUES (%s, %s, %s, %s)''',(session['id'], 0, title, desc))
			mysql.connection.commit()
			cur.close()
		flash('Complain successfully uploaded')
	return redirect(url_for('complain_form'))


@app.route("/download",methods=["POST","GET"])
def download():
	global who
	if request.method == 'POST':
		desig=''
		id=''
		ide=''
		strin=request.form['down']
		scid=''
		for character in strin:
			if character=='f':
				ide='faculty'
				break
			if character=='s':
				ide='student'
				break
			scid+=character
		cid=int(scid)
		cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		if who=='Student':
			cur.execute('SELECT * FROM stu_complainsDB JOIN studentDB ON stu_complainsDB.enrol_no=studentDB.enrol_no WHERE complain_id = % s', (cid, ))
			desig='Student'
		else:
			cur.execute('SELECT * FROM fac_complainsDB JOIN facultyDB ON fac_complainsDB.emp_id=facultyDB.emp_id WHERE complain_id = % s', (cid, ))
		if who=='Admin':
			if ide=='student':
				desig='student'
				cur.execute('SELECT * FROM stu_complainsDB JOIN studentDB ON stu_complainsDB.enrol_no=studentDB.enrol_no WHERE complain_id = % s', (cid, ))
			else:
				cur.execute('SELECT * FROM fac_complainsDB JOIN facultyDB ON fac_complainsDB.emp_id=facultyDB.emp_id WHERE complain_id = % s', (cid, ))
		account=cur.fetchone()
		cur.close()
		if not account:
			flash('Wrong Complain ID')
			if who=='Admin':
				redirect(url_for('admin'))
			else:
				redirect(url_for('complain_form'))
		elif who=='Faculty' or ide=='faculty':
			desig=account['designation']
			id=account['emp_id']
		elif who=='Student' or ide=='student':
			id=account['enrol_no']
		type=account['complain_type']
		desc=account['complain_details']
		fn=account['first_name']
		ln=account['last_name']
		mail=account['email']
		mn=account['mobile_no']
		dept=account['department']
		info=[]
		info.append(cid)
		info.append(type)
		info.append(desc)
		info.append(id)
		info.append(fn)
		info.append(ln)
		info.append(mail)
		info.append(mn)
		info.append(dept)
		info.append(desig)
		config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
		rendered=render_template('form.html', info=info)
		pdf=pdfkit.from_string(rendered, False, configuration=config)
		response=make_response(pdf)
		response.headers['Content-Type']='application/pdf'
		response.headers['Content-Disposition']='attachment; filename=output.pdf'
	return response


@app.route("/resolve",methods=["POST","GET"])
def resolve():
	strin=request.form['resolve']
	scid=''
	ide=''
	for character in strin:
		if character=='f':
			ide='faculty'
			break
		if character=='s':
			ide='student'
			break
		scid+=character
	cid=int(scid)
	cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	if ide=='student':
		cur.execute('update stu_complainsDB set status=1 where complain_id=%s', (cid, ))
	else:
		cur.execute('update fac_complainsDB set status=1 where complain_id=%s', (cid, ))
	mysql.connection.commit()
	cur.close()
	return redirect(url_for('admin'))

