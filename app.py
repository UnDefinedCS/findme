from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/", methods=["POST"])
def submit_info():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    social_media = request.form['social_media']
    alias = request.form['alias']

    print("First name: " + first_name, "Last name: " + last_name, "Online alias: " + alias, "Alias associated with: " + social_media)
    