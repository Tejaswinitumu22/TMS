from flask import flash,Flask,redirect,render_template,url_for,request,jsonify,session,flash,abort
import mysql.connector
from flask_session import Session
from secretconfig import secret_key
from py_mail import mail_sender
from email.message import EmailMessage
from datetime import date
import smtplib
from otp import genotp
from sdmail import sendmail
from tokenreset import token
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

app=Flask(__name__)
app.secret_key='jgjyfjmgjhymgfnb'
app.config['SESSION_TYPE']='filesystem'
mydb=mysql.connector.connect(
    host='localhost',
    user='root',
    password='admin',
    db='task'
    )
Session(app)
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/adminlogin',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('adminpanel'))
    return render_template('adminlogin.html')
@app.route('/create',methods=['GET','POST'])
def create():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT count(*) from admin')
    result=int(cursor.fetchone()[0])
    cursor.close()
    if request.method=='POST':
        secret_key=request.form['key']
        user=request.form['user']
        password=request.form['password']
        admin_email=request.form['admin_email']
        passcode=request.form['p_key']
        secret_key=cursor.fetchall()
        cursor.close()
        if (secret_key,) in secret_key:
            flash('This Security code is alredy taken by Faculty')
            return render_template('adminlogin.html')
        else:
            cursor=mydb.cursor()
            cursor.execute('insert into admin values(%s,%s,%s,%s)',[user,password,passcode,admin_email])
            mydb.commit()
            return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/validation',methods=['POST'])
def validation():
    if request.method=="POST":
        print(request.form)
        user=request.form['user']
        cursor=mydb.cursor()
        cursor.execute('SELECT username from admin')
        users=cursor.fetchall()            
        password=request.form['password']
        cursor.execute('select password from admin where username=%s',[user])
        task=cursor.fetchone()
        cursor.close()
        if (user,) in users:
            if password==task[0]:
                session['user']=user
                print(session['user'])
                return redirect(url_for('adminpanel'))
            else:
                flash('Invalid Password')
                return render_template('adminlogin.html')
        else:
            flash('Invalid user id')
            return render_template('adminlogin.html')
@app.route('/adminlogout')
def logoutadmin():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    return redirect(url_for('home'))
@app.route('/adminpanel')
def adminpanel():
    if session.get('user'):
        cursor=mydb.cursor()
        cursor.execute('SELECT id from task')
        tasks=cursor.fetchall()
        cursor.close()
        return render_template('adminpanel.html',tasks=tasks)
    return redirect(url_for('login'))
@app.route('/create1',methods=['GET','POST'])
def create1():
    cursor=mydb.cursor()
    cursor.execute('SELECT count(*) from empolyee')
    re=int(cursor.fetchone()[0])
    cursor.close()
    if request.method=='POST':
        cursor=mydb.cursor()
        empid=request.form['employeeid']
        cursor.execute('SELECT employeeid from empolyee')
        task=cursor.fetchall()
        cursor.execute('SELECT email from empolyee')
        emails=cursor.fetchall()
        if (empid,) in task:
            flash('Employee id already exists')
            return render_template('signin.html')
        firstname=request.form['firstname']
        lastname=request.form['lastname']
        email=request.form['email']
        if (email,) in emails:
            flash('Email is  already exists')
            return render_template('signin.html')
        password=request.form['password']
        phone=request.form['phonenumber']
        otp=genotp()
        subject='Thanks for registering'
        body = 'your one time password is- '+otp
        sendmail(email,subject,body)
        return render_template('otp.html',otp=otp,empid=empid,firstname=firstname,lastname=lastname,email=email,password=password,phonenumber=phone)
        '''cursor.close()
        cursor=mydb.cursor()
        cursor.execute('insert into empolyee values(%s,%s,%s,%s,%s,%s)',[empid,firstname,lastname,email,password,phonenumber])
        mydb.commit()'''
        return redirect(url_for('home'))
    return render_template('signin.html')

@app.route('/otp/<otp>/<empid>/<firstname>/<lastname>/<email>/<password>/<phonenumber>',methods=['POST','GET'])
def getotp(otp,empid,firstname,lastname,email,password,phonenumber):
    if request.method == 'POST':
        OTP=request.form['otp']
        if otp == OTP:
            cursor=mydb.cursor() 
            cursor.execute('insert into empolyee values(%s,%s,%s,%s,%s,%s)',[empid,firstname,lastname,email,password,phonenumber])
            mydb.commit()
            cursor.close()
            flash('Details registered successfully')
            return redirect(url_for('login'))
        else:
            flash('wrong OTP')

    return render_template('otp.html',otp=otp,empid=empid,firstname=firstname,lastname=lastname,email=email,password=password,phonenumber=phonenumber)


@app.route('/taskemployee',methods=['GET','POST'])
def taskemployee():
    if session.get('email'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT employeeid  from empolyee where email=%s',[session['email']])
        data=cursor.fetchone()
        id1=data[0]
        cursor.execute('SELECT * from task where assign_to=%s',[id1])
        tasks=cursor.fetchall()
        print(tasks)
        cursor.close()
        
        return render_template('taskemployee.html',id1=id1,task=tasks)
    return redirect(url_for('employeelogin'))
@app.route('/taskemploye')
def ourteam():
    return render_template('ourteam.html')
@app.route('/employeelogin',methods=['GET','POST'])
def employeelogin():
    if session.get("email"):
        return redirect(url_for('taskemployee'))
    if request.method=="POST":
        email=request.form['email']
        cursor=mydb.cursor()
        cursor.execute('SELECT email from empolyee')
        emails=cursor.fetchall()
        password=request.form['password']
        cursor.execute('select password from empolyee where email=%s',[email])
        task=cursor.fetchone()
        cursor.close()
        if (email,) in emails:
            if password==task[0]:
                session["email"]=email
                return redirect(url_for('taskemployee'))
            else:
                flash('Invalid Password')
                return render_template('employeelogin.html')
        else:
            flash('Invalid employee id')
            return render_template('employeelogin.html')
    
    return render_template('employeelogin.html')
@app.route('/logoutemp')
def logout():
    if session.get('email'):
        session.pop('email')
        return redirect(url_for('home'))
    return redirect(url_for('home'))
@app.route('/addsuggestion',methods=['GET','POST'])
def suggestions():
    cursor=mydb.cursor()
    cursor.execute('SELECT * from announcements')
    suggestions=cursor.fetchall()
    if request.method=="POST":
        emp_id=request.form['id']
        name=request.form['name']
        field=request.form['field']
        announcement=request.form['text']
        cursor=mydb.cursor()
        cursor.execute('INSERT INTO announcements values(%s,%s,%s,%s)',[emp_id,name,field,announcement])
        mydb.commit()
        return render_template('announcements.html',suggestions=suggestions)
    return render_template('announcements.html')
    
@app.route('/delete',methods=['POST'])
def delete():
    if request.method=='POST':
        print(request.form)
        s=request.form['option'].split()
        cursor=mydb.cursor()
        cursor.execute('delete from task where id=%s',[s[0]])
        mydb.commit()
        cursor.close()
        return redirect(url_for('adminpanel'))
@app.route('/addtask',methods=['GET','POST'])
def addtask():
    if request.method=='POST':
        id1=request.form['id']
        name=request.form['name']        
        assign_to=request.form['assign_to']
        date=request.form['date']        
        duedate=request.form['duedate']
        cursor=mydb.cursor()
        id2=session.get('user')
        print(id2)
        
        cursor.execute('insert into task(id,name,assigning,status,assign_to,date,duedate) values(%s,%s,%s,%s,%s,%s,%s)',[id1,name,id2,'NOT STARTED',assign_to,date,duedate])
        cursor=mydb.cursor(buffered=True)
        
        cursor.execute('SELECT PASSCODE from admin')
        passcode=cursor.fetchone()[0]
        cursor.execute('SELECT admin_email from admin')
        email_from=cursor.fetchone()[0]
        cursor.execute('SELECT email from empolyee where employeeid=%s',[assign_to])
        email_to=cursor.fetchone()[0]
        mydb.commit()
        subject=f'Due date for task submission {name}'
        body=f'\n completed the task \n\n\nDue date for submit your work {duedate}'
        cursor.close()
        
        try:
            mail_sender(email_from,email_to,subject,body,passcode)
            print(mail_sender)
        except Exception as e:
            print(e)
        
        return redirect(url_for('adminpanel'))
    return render_template('addtask.html')
@app.route('/viewtask')
def view():
    cursor=mydb.cursor()
    cursor.execute('SELECT * from task order by date')
    tasks=cursor.fetchall()
    cursor.close()
    return render_template('alltasktable.html',tasks=tasks)

@app.route('/forgetpassword',methods=['GET','POST'])
def password():
    if request.method=='POST':
        print(request.form)
        key=request.form['key']
        password=request.form['password']
        email=request.form['email']
        passcode=request.form['p_key']
        if key==secret_key:
            cursor=mydb.cursor()
            cursor.execute('update admin set password=%s,email=%s,passcode=%s',[password,email,passcode])
            mydb.commit()
            cursor.close()
            return redirect(url_for('home'))
        else:
            return redirect(url_for('password'))
    return render_template('secret.html')
@app.route('/changestatus/<tid>',methods=['GET','POST'])
def changestatus(tid):
    if request.method=='POST':
        option=request.form['option']
        comment=request.form['text']
        cursor=mydb.cursor()
        cursor.execute('update task set status=%s,comment=%s where id=%s',[option,comment,tid])
        mydb.commit()
        return redirect(url_for('taskemployee'))
        
    return render_template('taskempstatus.html')

    
@app.route('/password1',methods=['GET','POST'])
def password1():
    if request.method=='POST':
        print(request.form)
        email=request.form['email']
        password=request.form['password']
        if key==secret_key:
            cursor=mydb.cursor()
            cursor.execute('update empolyee set password=%s,email=%s',[password,email])
            mydb.commit()
            cursor.close()
            return redirect(url_for('home'))
        else:
            return redirect(url_for('password1'))
    return render_template('empforgetpass.html')



@app.route('/update',methods=['POST'])
def update1():
    option1=request.form['id1'].split()[0]
    return redirect(url_for('update',id1=option1))
@app.route('/update/<id1>',methods=['GET','POST'])
def update(id1):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT * FROM task where id=%s',[id1])
    option=cursor.fetchall()
    id1=option[0][0]
    name=option[0][1]
    print(option)
    assign_to=option[0][5]
    print(assign_to)
    date=option[0][3]
    duedate=option[0][6]
    cursor.close()
    if request.method=='POST':
        
        name2=request.form['name']
        assign_to2=request.form['assign_to']
        date2=request.form['date']
        duedate2=request.form['duedate']
        cursor=mydb.cursor()
        cursor.execute('SELECT assigning,assign_to from task where id=%s',[id1])
        task=cursor.fetchone()
    
        cursor=mydb.cursor(buffered=True)
        
        cursor.execute('SELECT PASSCODE from admin')
        passcode=cursor.fetchone()[0]
        cursor.execute('SELECT admin_email from admin')
        email_from=cursor.fetchone()[0]
        cursor.execute('update task set name=%s,date=%s,assign_to=%s,duedate=%s where id=%s',[name2,date2,assign_to2,duedate2,id1])
        cursor.execute('SELECT email from empolyee where employeeid=%s',[assign_to])
        email_to=cursor.fetchone()[0]
        mydb.commit()
        subject=f'Task is updated'
        body=f'\nYou completed the task with in time due date for your task {duedate}'
        cursor.close()
        try:
            mail_sender(email_from,email_to,subject,body,passcode)
            print(mail_sender)
        except Exception as e:
            print(e)
            #return render_template('check.html')
        return redirect(url_for('adminpanel'))
    
    return render_template('update.html',name=name,assign_to=assign_to,date=date,id1=id1)
app.run(debug=True,use_reloader=True)
#if __name__ == "__main__":
#app.run(debug=True)


