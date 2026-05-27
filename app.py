from flask import Flask, render_template, request, redirect, jsonify, session
import sqlite3
from datetime import datetime
app = Flask(__name__)
app.secret_key="college_secret"

def init_db():
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    c.execute(''' CREATE TABLE IF NOT EXISTS tips(id INTEGER PRIMARY KEY AUTOINCREMENT,
              senior_name TEXT,
              college TEXT,
              branch TEXT,
              title TEXT,
              description TEXT,
              urgency TEXT,
              credibility INTEGER DEFAULT 0,
              verified INTEGER DEFAULT 0,
              likes INTEGER DEFAULT 0,
              created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password TEXT,
              role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY AUTOINCREMENT,
              tip_id INTEGER,
              username TEXT,
              comment TEXT,
              created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              message TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookmarks(id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT,
              tip_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS liked_tips(id INTEGER PRIMARY KEY AUTOINCREMENT,
              csername TEXT,
              tip_id INTEGER)''')
    conn.commit()
    conn.close()
    
init_db()

@app.route("/")
def home():
    
    college = request.args.get("college")
    branch = request.args.get("branch")
    urgency = request.args.get("urgency")
    keyword = request.args.get("keyword")
    
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    query = "SELECT * FROM tips WHERE 1=1"
    params = []
    
    if college:
        query += " AND college=?"
        params.append(college)
        
    if branch:
        query += " AND branch=?"
        params.append(branch)
        
    if urgency:
        query += " AND urgency=?"
        params.append(urgency)
        
    if keyword:
        query += " AND title LIKE ?"
        params.append("%"+keyword+"%")

    query += " ORDER BY likes DESC"
    c.execute(query, params)
    tips = c.fetchall()
    
    c.execute("SELECT COUNT(*) FROM tips")
    total_tips = c.fetchone()[0]
    
    c.execute("SELECT * FROM comments")
    comments = c.fetchall()
    
    c.execute("SELECT COUNT(*) FROM tips WHERE verified=1")
    verified_tips = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
  
    conn.close()

    return render_template("index.html", tips=tips, total_tips=total_tips,verified_tips = verified_tips, total_users=total_users, comments=comments)

@app.route("/add_tip", methods=["POST"])
def add_tip():
    
    if "user" not in session:
        return redirect("/login")

    senior_name = request.form["senior_name"]
    college = request.form["college"]
    branch = request.form["branch"]
    title = request.form["title"]
    description = request.form["description"]
    urgency = request.form["urgency"]

    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO tips
    (senior_name, college, branch, title, description, urgency, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        senior_name,
        college,
        branch,
        title,
        description,
        urgency,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/signup",methods = ["GET","POST"])
def signup():
    if request.method=="POST":
        
        username=request.form["username"]
        password=request.form["password"]
        role=request.form["role"]
        if role not in ["Fresher", "Senior"]:
            role = "Fresher"

        conn=sqlite3.connect("college_intel.db")
        c=conn.cursor()
        c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",(username,password,role))
        conn.commit()
        conn.close()
        return redirect("/")
    return render_template("signup.html")

@app.route("/login",methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("college_intel.db")
        c = conn.cursor()
        
        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",(username, password)
        )
        user = c.fetchone()
        conn.close()
        if user:
            session["user"] = user[1]
            session["role"] = user[3]
            return redirect("/")
        else:
            return "Invalid Username or Password"
        
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/contributions")
def my_contributions(id):
    if "user" not in session:
        return redirect("/login")
    username = session["user"]
    
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tips WHERE senior_name=?", (username, ))
    
    total_tips = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM comments WHERE username=?", (username, ))
    
    total_comments = c.fetchone()[0]
    
    conn.close()
    
    return render_template(
        "contibution.html",
        total_tips=total_tips,
        total_comments=total_comments
    )

@app.route("/my_tips")
def my_tips():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM tips WHERE senior_name=?",
        (session["user"],)
    )

    tips = c.fetchall()

    conn.close()

    return render_template(
        "mytips.html",
        tips=tips
    )

@app.route("/notifications")
def notifications():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM notifications WHERE username=?",
        (session["user"],)
    )

    data = c.fetchall()

    conn.close()

    return render_template(
        "notifications.html",
        notifications=data
    )

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")
    return render_template(
        "profile.html",
        username=session["user"],
        role=session["role"]
    )

@app.route("/verify/<int:id>")
def verify(id):
    if session.get("role") != "Admin":
        return "Access Denied"
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    c.execute("UPDATE tips SET verified=1, credibility=credibility+1 WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id):
    if session.get("role") != "Admin":
        return "Access Denied"
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    c.execute("DELETE FROM tips WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/like/<int:id>")
def like(id):

    conn=sqlite3.connect("college_intel.db")
    c=conn.cursor()

    c.execute(
        "UPDATE tips SET likes=likes+1 WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/edit/<int:id>")
def edit(id):
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    
    if request.method=="POST":
        
        title = request.form["title"]
        description = request.form["description"]
        
        c.execute(
            "UPDATE tips SET title=?, WHERE id=?",(title,description,id)
        )
        
        conn.commit()
        conn.close()
        
        return redirect("/")
    
    c.execute(
        "SELECT * FROM tips WHERE id=?",(id, )
    )
    
    tip=c.fetchone()
    
    conn.close()
    
    return render_template(
        "edit.html",
        tip=tip
    )

@app.route("/bookmark/<int:id>")
def bookmark(id):

    if "user" not in session:
        return redirect("/login")

    conn=sqlite3.connect("college_intel.db")
    c=conn.cursor()

    c.execute(
        "INSERT INTO bookmarks(username,tip_id) VALUES(?,?)",
        (
            session["user"],
            id
        )
    )

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/comment/<int:id>", methods=["POST"])
def comment(id):

    if "user" not in session:
        return redirect("/login")

    comment = request.form["comment"]

    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO comments(tip_id,username,comment) VALUES(?,?,?)",
        (
            id,
            session["user"],
            comment
        )
    )

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/saved")
def saved():
    if "user" not in session:
        return redirect("/login")
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    
    c.execute('''SELECT tips.* FROM tips
              JOIN bookmarks
              ON tips.id = bookmarks.tip_id
              WHERE bookmarks.username=?''',(session["user"],))
    
    tips = c.fetchall()
    
    conn.close()
    
    return render_template(
        "saved.html",
        tips=tips
    )
    
@app.route("/recent")
def recent():
    
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    
    c.execute(
        "SELECT * FROM tips ORDER BY created_at DESC LIMIT 5"
    )
    
    tips = c.fetchall()
    
    conn.close()
    
    return render_template(
        "recent.html",
        tips=tips
    )

@app.route("/recommend/<branch>")
def recommend(branch):

    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM tips WHERE branch=?",
        (branch,)
    )

    tips = c.fetchall()

    conn.close()

    return render_template(
        "recommend.html",
        tips=tips,
        branch=branch
    )
    
@app.route("/dashboard")
def dashboard():
    
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    
    c.execute(
        "SELECT COUNT(*) FROM tips"
    )
    total_tips=c.fetchone()[0]
    
    c.execute(
        "SELECT COUNT(*) FROM users"
    )
    total_users=c.fetchone()[0]
    
    c.execute(
        "SELECT SUM(likes) FROM tips"
    )
    total_likes=c.fetchone()[0]
    
    conn.close()
    
    return render_template(
        "dashboard.html",
        total_tips=total_tips,
        total_users=total_users,
        total_likes=total_likes,
    )

@app.route("/tips", methods = ["GET"])
def get_tips():
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    
    c.execute("SELECT * FROM tips")
    rows = c.fetchall()
    conn.close()
    tips = []
    
    for row in rows:
        tips.append({
            "id": row[0],
            "senior_name": row[1],
            "college": row[2],
            "branch": row[3],
            "title": row[4],
            "description": row[5],
            "urgency": row[6],
            "credibility": row[7],
            "created_at": row[8]
        })
    return jsonify(tips)

@app.route("/add_likes_column")
def add_likes_column():
    conn = sqlite3.connect("college_intel.db")
    c = conn.cursor()
    
    c.execute("ALTER TABLE tips ADD COLUMN likes INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()
    
    return "Likes column added"

@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "404.html"
    ),404

if __name__ == "__main__":
    app.run(debug = True)
