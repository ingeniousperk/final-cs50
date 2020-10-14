from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from hashids import Hashids
from functools import wraps
import pymysql
import os


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure encoder
hashids = Hashids()

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_pass = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_conn = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
unix_socket = f"/cloudsql/{db_conn}"

def SQL(query, *args):
    print(args)
    connection = pymysql.connect(
        user=db_user,
        password=db_pass,
        db=db_name,
        unix_socket=unix_socket
    )
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query, args)
        if query[:6] in ('INSERT', 'DELETE','UPDATE'):
            connection.commit()
            cursor.close()
            connection.close()
            return
        result = cursor.fetchall()
    connection.close()
    return result

# Reserved keyword
reservedkey = ["","freeshort","login","register","logout","dashboard","create","edit","reserve"]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def long_isfree(longurl, user_id):
    if SQL("SELECT sh_id FROM shortened WHERE original = %s AND user_id = %s", longurl, user_id):
        return False
    return True

def truncate_url(weburl):
    if weburl[:7] == "http://":
        return weburl[7:]
    if weburl[:8] == "https://":
        return weburl[8:]
    return weburl

def custom_isfree(customurl):
    if SQL("SELECT sh_id FROM shortened WHERE BINARY short = %s", customurl):
        return False
    return True


@app.route("/")
def index():

    if not session.get("user_id"):
        flash("You haven't signed in. You can shorten only 5 URLs")
        return render_template("index.html", type='alert-warning')
    # is logged in
    return redirect("/dashboard")


@app.route("/freeshort", methods=["GET","POST"])
def freeshort():
    '''Shortened urls page for un-signedin users'''

    ip_add = request.remote_addr

    if request.method == "POST":
        weburl = request.form.get("weburl")
        weburl = truncate_url(weburl)
        sh_id = SQL("SELECT MAX(sh_id) FROM shortened")[0]["MAX(sh_id)"] + 1
        shortened = hashids.encode(sh_id)

        freecnt = SQL("SELECT COUNT(sh_id) FROM shortened WHERE ip_add = %s", ip_add)[0]["COUNT(sh_id)"]
        if freecnt < 5:
            SQL("INSERT INTO shortened (ip_add, original, short, datetime, reserved) VALUES(%s, %s, %s, NOW(), 0)",
                ip_add, weburl, shortened)
            return redirect("/freeshort")
        # else
        flash("You have exceeded maximum requests. Please login or register to gain unlimited")
        return redirect(url_for('login',type='alert-danger'))

    if session.get("user_id"):
        return redirect("/dashboard")

    hisdata = SQL("SELECT original, short FROM shortened WHERE ip_add = %s ORDER BY datetime DESC", ip_add)

    # show him his usage
    if not request.args.get("fromnoip"):
        flash("You haven't signed in. You can shorten only 5 URLs")
        return render_template("freeshort.html", hisdata=hisdata, type='alert-warning')
    # from button in un-signed in dashboard
    if request.args.get("action") == "delete":
        shorturl = request.args.get("shorturl")
        SQL("DELETE FROM shortened WHERE ip_add = %s AND BINARY short = %s", ip_add, shorturl)
        flash("Successful")
        return render_template("freeshort.html", hisdata=hisdata, type='alert-success')

@app.route("/login", methods=["GET","POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    session.permanent = True

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = SQL("SELECT * FROM users WHERE username = %s",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1:
            return render_template("error.html", code=403, message="you haven't registered yet.")
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Wrong password")
            return render_template("login.html", type="alert-danger")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/dashboard")

    # User reached route via GET (as by clicking a link or via redirect)
    alerttype = request.args.get("type")
    # From un-signedin user button "customize"
    if request.args.get("fromnoip"):
        flash("You must be logged in to customize links.")
        alerttype = 'alert-danger'
    return render_template("login.html", type=alerttype)

@app.route("/register", methods=["GET","POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        if SQL("SELECT id FROM users WHERE username = %s", username):
            flash("Sorry, that username has taken already.")
            return render_template("register.html", type="alert-danger")

        SQL("INSERT INTO users(username, hash) VALUES(%s, %s)",
        username, generate_password_hash(request.form.get("password")))

        flash("Register Successful!")
        return redirect(url_for('login',type="alert-success"))

    # User reached via GET
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session.get("user_id")
    linkdata = SQL("SELECT original, short FROM shortened WHERE user_id = %s AND reserved = 0 ORDER BY datetime DESC", user_id)
    resdata = SQL("SELECT original, short FROM shortened WHERE user_id = %s AND reserved = 1 ORDER BY datetime DESC", user_id)
    alerttype = request.args.get("type")
    return render_template("dashboard.html", linkdata=linkdata, resdata=resdata, type=alerttype)


@app.route("/create", methods=["GET","POST"])
@login_required
def create():
    if request.method == "POST":
        user_id = session.get("user_id")
        weburl = request.form.get("weburl")
        weburl = truncate_url(weburl)

        if not long_isfree(weburl, user_id):
            flash("Sorry, you have that url shortened already.")
            return redirect(url_for('/dashboard', type='alert-danger'))

        sh_id = SQL("SELECT MAX(sh_id) FROM shortened")[0]["MAX(sh_id)"] + 1
        shortened = hashids.encode(sh_id)

        SQL("INSERT INTO shortened (user_id, original, short, datetime, reserved) VALUES (%s, %s, %s, NOW(), 0)",
            user_id, weburl, shortened)
        flash("Link created. You can now customize it or later")
        return redirect(url_for('edit', new=True, longurl=weburl, shorturl=shortened))

    return render_template("create.html")


@app.route("/edit", methods=["GET","POST"])
@login_required
def edit():
    if request.method == "POST":
        user_id = session.get("user_id")

        # if accessed from edit.html
        if not request.args.get("foreign"):
            longurl = request.form.get("longurl")
            customurl = request.form.get("customurl")
            if custom_isfree(customurl):
                SQL("UPDATE shortened SET short = %s, datetime = NOW() WHERE user_id = %s AND original = %s",
                    customurl, user_id, longurl)
            else:
                flash("Sorry, that custom name has already taken")
                return redirect(url_for('edit', longurl=longurl, shorturl=customurl, type='alert-danger'))

        else: # from dashboard reserved links
            action = request.args.get("action")
            if action == 'custom':
                # if to customize
                customurl = request.form.get(request.args.get("customname"))
                longurl = request.form.get(request.args.get("longname"))
                longurl = truncate_url(longurl)
                if long_isfree(customurl, user_id):
                    SQL("UPDATE shortened SET original = %s, datetime = NOW(), reserved = 0 WHERE user_id = %s AND BINARY short = %s",
                        longurl, user_id, customurl)
                else:
                    flash("Sorry, you have that url shortened already.")
                    return redirect(url_for('edit', longurl=longurl, shorturl=customurl, type='alert-danger'))

            elif action == 'delete':
                # if to delete
                customurl = request.args.get("customname")
                if request.form.get(customurl):
                    customurl = request.form.get(customurl)
                SQL("DELETE FROM shortened WHERE user_id = %s AND BINARY short = %s", user_id, customurl)

        flash("Successful!")
        return redirect(url_for('dashboard',type='alert-success'))

    # if freshly created
    if request.args.get("new"):
        longurl = request.args.get("longurl")
        shorturl = request.args.get("shorturl")
        return render_template("edit.html", longurl=longurl, shorturl=shorturl, type='alert-success')

    # got from the dashboard summary links or redirected from failed customization
    alerttype = request.args.get('type')
    longurl = request.args.get("longurl")
    customurl = request.args.get("customurl")
    return render_template("edit.html", longurl=longurl, shorturl=customurl, type=alerttype)


@app.route("/reserve", methods=["GET","POST"])
@login_required
def reserve():
    if request.method == "POST":
        user_id = session.get("user_id")
        if SQL("SELECT COUNT(sh_id) FROM shortened WHERE user_id = %s AND reserved = 1", user_id)[0]['COUNT(sh_id)'] >= 5:
            flash("You have reached max amount of reservation. Complete or delete others first.")
            return redirect(url_for('dashboard', type='alert-danger'))

        customurl = request.form.get("reserveurl")
        if SQL("SELECT original FROM shortened WHERE BINARY short = %s", customurl):
            flash("That url has been taken. Try again")
            return redirect("/reserve")

        # voila, it's available
        SQL("INSERT INTO shortened (user_id, short, datetime, reserved) VALUES (%s, %s, NOW(), 1)",
            user_id, customurl)

        return redirect("/dashboard")

    return render_template("reserve.html", type='alert-danger')


@app.route('/<short>')
def geturl(short):
    longurl = SQL("SELECT original FROM shortened WHERE BINARY short = %s", short)
    if not longurl:
        return render_template("error.html", code=404, message="no such url in our server")

    longurl = longurl[0]['original']
    if longurl in reservedkey:
        return redirect(longurl)

    return redirect("http://"+longurl)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        code = 500
        message = "Internal Server Error. Mungkin free trial Google Cloud sudah berakhir."
    return render_template("error.html", code=code, message=message)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)