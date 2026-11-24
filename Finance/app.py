from flask import Flask, render_template, request, redirect, session
import sqlite3
import joblib
import pandas as pd
import datetime
from functools import wraps

# PDF
from reportlab.platypus import SimpleDocTemplate, Table

app = Flask(__name__)
app.secret_key = "finance_ai_secret"

# -----------------------
# Load Models
# -----------------------
try:
    rf, vectorizer = joblib.load("models/category_model.pkl")
    reg = joblib.load("models/regression_model.pkl")
    anomaly = joblib.load("models/anomaly_model.pkl")
except:
    rf, vectorizer, reg, anomaly = None, None, None, None


# -----------------------
# DB
# -----------------------
def connect_db():
    return sqlite3.connect("finance.db")


# -----------------------
# LOGIN REQUIRED
# -----------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


# -----------------------
# HOME
# -----------------------
@app.route("/")
def home():
    return render_template("login.html")


# -----------------------
# REGISTER
# -----------------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = connect_db()
        conn.execute(
            "INSERT INTO users(username,email,password) VALUES (?,?,?)",
            (request.form["username"], request.form["email"], request.form["password"])
        )
        conn.commit()
        conn.close()
        return redirect("/")
    return render_template("register.html")


# -----------------------
# LOGIN
# -----------------------
@app.route("/login", methods=["POST"])
def login():
    conn = connect_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (request.form["email"], request.form["password"])
    ).fetchone()
    conn.close()

    if user:
        session["user"] = user[0]
        return redirect("/dashboard")
    return "Invalid Login"


# -----------------------
# LOGOUT
# -----------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -----------------------
# DASHBOARD
# -----------------------
@app.route("/dashboard")
@login_required
def dashboard():

    conn = connect_db()

    df = pd.read_sql_query(
        "SELECT * FROM transactions WHERE user_id=?",
        conn,
        params=(session["user"],)
    )

    conn.close()

    prediction = 0
    if len(df) > 0 and reg:
        prediction = reg.predict([[len(df)+1]])[0]

    return render_template(
        "dashboard.html",
        data=df.to_dict(orient="records"),
        prediction=prediction
    )


# -----------------------
# ADD TRANSACTION
# -----------------------
@app.route("/add", methods=["GET","POST"])
@login_required
def add():

    if request.method == "POST":

        desc = request.form["description"]
        amount = float(request.form["amount"])

        # Category
        category = "Other"
        if rf and vectorizer:
            X = vectorizer.transform([desc])
            category = rf.predict(X)[0]

        # Fraud
        alert = ""
        if anomaly:
            if anomaly.predict([[amount]])[0] == -1:
                alert = "⚠ Unusual transaction detected!"

        conn = connect_db()
        conn.execute(
            "INSERT INTO transactions(user_id,description,amount,category,date) VALUES (?,?,?,?,?)",
            (session["user"], desc, amount, category, str(datetime.date.today()))
        )
        conn.commit()
        conn.close()

        return render_template("add_transaction.html", alert=alert)

    return render_template("add_transaction.html")


# -----------------------
# DELETE
# -----------------------
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    conn = connect_db()
    conn.execute(
        "DELETE FROM transactions WHERE id=? AND user_id=?",
        (id, session["user"])
    )
    conn.commit()
    conn.close()
    return redirect("/dashboard")


# -----------------------
# EDIT
# -----------------------
@app.route("/edit/<int:id>", methods=["GET","POST"])
@login_required
def edit(id):

    conn = connect_db()

    if request.method == "POST":
        conn.execute("""
        UPDATE transactions
        SET description=?, amount=?
        WHERE id=? AND user_id=?
        """, (request.form["description"], request.form["amount"], id, session["user"]))

        conn.commit()
        conn.close()
        return redirect("/dashboard")

    data = conn.execute(
        "SELECT * FROM transactions WHERE id=? AND user_id=?",
        (id, session["user"])
    ).fetchone()

    conn.close()

    return render_template("edit.html", data=data)


# -----------------------
# REPORTS (REAL DATA)
# -----------------------
@app.route("/reports")
@login_required
def reports():

    conn = connect_db()

    # Category chart
    df = pd.read_sql_query(
        "SELECT category, SUM(amount) as total FROM transactions WHERE user_id=? GROUP BY category",
        conn,
        params=(session["user"],)
    )

    # Monthly chart
    df_month = pd.read_sql_query("""
        SELECT strftime('%m', date) as month, SUM(amount) as total
        FROM transactions
        WHERE user_id=?
        GROUP BY month
        ORDER BY month
    """, conn, params=(session["user"],))

    conn.close()

    return render_template(
        "reports.html",
        labels=df["category"].tolist(),
        values=df["total"].tolist(),
        months=df_month["month"].tolist(),
        monthly_expenses=df_month["total"].tolist(),
        income=50000,
        expense=sum(df["total"]) if len(df)>0 else 0
    )


# -----------------------
# EXPORT EXCEL
# -----------------------
@app.route("/export_excel")
@login_required
def export_excel():

    conn = connect_db()
    df = pd.read_sql_query(
        "SELECT * FROM transactions WHERE user_id=?",
        conn,
        params=(session["user"],)
    )
    conn.close()

    path = "static/transactions.xlsx"
    df.to_excel(path, index=False)

    return redirect("/" + path)


# -----------------------
# EXPORT PDF
# -----------------------
@app.route("/export_pdf")
@login_required
def export_pdf():

    conn = connect_db()
    df = pd.read_sql_query(
        "SELECT * FROM transactions WHERE user_id=?",
        conn,
        params=(session["user"],)
    )
    conn.close()

    path = "static/transactions.pdf"

    pdf = SimpleDocTemplate(path)
    table = Table([df.columns.tolist()] + df.values.tolist())
    pdf.build([table])

    return redirect("/" + path)


# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)