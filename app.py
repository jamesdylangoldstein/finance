from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
import csv
import io
import urllib

from tempfile import gettempdir

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    id = session.get('user_id')

    stock_purchases = db.execute("SELECT * FROM purchases WHERE id = :id", id=id)

    #https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table
    #http://stackoverflow.com/questions/10974937/how-to-set-dynamically-the-width-of-a-html-table-column-according-to-its-text-co
    return render_template("index.html", stock_purchases=stock_purchases)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        #http://stackoverflow.com/questions/32640090/python-flask-keeping-track-of-user-sessions-how-to-get-session-cookie-id
        id = session.get('user_id')

        url_start = 'http://download.finance.yahoo.com/d/quotes.csv?s='
        url_middle = request.form["symbol"]
        url_end = '&f=nsl1d1t1c1ohgv&e=.csv'
        full_url = url_start + url_middle + url_end

        # http://stackoverflow.com/questions/21351882/reading-data-from-a-csv-file-online-in-python-3
        response = urllib.request.urlopen(full_url)

        datareader = csv.reader(io.TextIOWrapper(response))
        quote_list = list(datareader)

        num_shares = request.form["num_shares"]

        name = quote_list[0][0]
        symbol = quote_list[0][1]
        price = float(quote_list[0][2])

        #http://stackoverflow.com/questions/12078571/jinja-templates-format-a-float-as-comma-separated-currency
        total_cost = round((float(price) * 100.0) * float(num_shares) / 100.0,2)

        username = db.execute("SELECT username FROM users WHERE id = :id", id=id)
        username = username[0]
        username = username.get('username')

        db.execute("INSERT INTO purchases (id, symbol, name, shares, price, total) VALUES(:id, :symbol, :name, :shares, :price, :total)",
            id=id, symbol=symbol, name=name, price=price, shares=num_shares, total=total_cost)

        return render_template("bought.html", username=username, id=id, name=name, symbol=symbol, price=price, num_shares=num_shares, total_cost=total_cost)
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    return apology("TODO")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":

        url_start = 'http://download.finance.yahoo.com/d/quotes.csv?s='
        url_middle = request.form["symbol"]
        url_end = '&f=nsl1d1t1c1ohgv&e=.csv'
        full_url = url_start + url_middle + url_end


        # http://stackoverflow.com/questions/21351882/reading-data-from-a-csv-file-online-in-python-3
        response = urllib.request.urlopen(full_url)

        datareader = csv.reader(io.TextIOWrapper(response))
        quote_list = list(datareader)

        name = quote_list[0][0]
        symbol = quote_list[0][1]
        price = quote_list[0][2]

        return render_template("quote_display.html", name=name, symbol=symbol, price=price)
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        my_hash = pwd_context.hash(request.form["hash"])

        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
            username=request.form["username"], hash=my_hash)
        return render_template("login.html")
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        order_num = request.form["order_num"]
        #https://www.w3schools.com/tags/tryit.asp?filename=tryhtml5_input_type_hidden
        #https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table
        #http://stackoverflow.com/questions/10974937/how-to-set-dynamically-the-width-of-a-html-table-column-according-to-its-text-co
        return redirect(url_for("sellselected", order_num=order_num))
    else:
        id = session.get('user_id')

        stock_purchases = db.execute("SELECT * FROM purchases WHERE id = :id", id=id)

        #https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table
        #http://stackoverflow.com/questions/10974937/how-to-set-dynamically-the-width-of-a-html-table-column-according-to-its-text-co
        return render_template("sell.html", stock_purchases=stock_purchases)


@app.route("/sellselected/", methods=["GET", "POST"])
@login_required
def sellselected(order_num):
    stock_to_sell = db.execute("SELECT * FROM purchases WHERE order_num = :order_num", order_num=order_num)
    if request.method == "POST":
        # NOT DONE, WORKING ON GET FIRST
        #order_num = request.form["order_num"]
        #minus_shares = request.form["sell_num"]
        #command = db.execute("UPDATE purchases SET shares=7 WHERE order_num=order_num")

        #https://www.w3schools.com/tags/tryit.asp?filename=tryhtml5_input_type_hidden
        #https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table
        #http://stackoverflow.com/questions/10974937/how-to-set-dynamically-the-width-of-a-html-table-column-according-to-its-text-co
        return redirect(url_for("index"))
    else:
        #NO FORMATTING YET, JUST ATTEMPTING TO PASS STOCK_TO_SELL TO TEMPLATE
        #https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table
        #http://stackoverflow.com/questions/10974937/how-to-set-dynamically-the-width-of-a-html-table-column-according-to-its-text-co
        return render_template("sellselected.html", stock_to_sell=stock_to_sell, order_num=order_num)
