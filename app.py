from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/", methods=["POST"])
def submit_info():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    social_media = request.form.getlist('social_media')
    alias = request.form.getlist('alias')

    print("First name: " + first_name)
    print("Last name: " + last_name) 
    print("Online alias(es): ")
    for a in alias:
        print(a + ", ")
    print("Alias(es) associated with: ")
    for media in social_media:
        print(media + ", ")
    

    return render_template("index.html", loading=True)

#TESTING ONLY
@app.route("/loading")
def animation_test():
    return render_template("loading.html")