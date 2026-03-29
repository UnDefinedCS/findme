from flask import Flask, render_template, request, jsonify
from data_gen import generate_queries, collect_data
from app_types import UserData
import threading
import asyncio
import time

app = Flask(__name__)
thread = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/", methods=["POST"])
def submit_info():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    alias = request.form.getlist('alias')
    combinedSocialAlias = []
    for i in range(len(alias)):
        social_media = request.form.getlist('social_media_' + str(i))
        element = []
        if(len(social_media) != 0):
            element = [alias[i], social_media]
        else:
            element = [alias[i], None]
        combinedSocialAlias.append(element)

    global thread
    thread = threading.Thread(target=query_trigger, args=(first_name, last_name, combinedSocialAlias), daemon=True)

    rendered_index = render_template("index.html", loading=True, start_thread=start_thread)

    return rendered_index

async def query_handler(first, last, social):
    newCombination = []
    for i in range(len(social)):
        if(social[i][1] != None):
            for j in range(len(social[i][1])):
                element = [social[i][0], social[i][1][j]]
                newCombination.append(element)
        else:
            newCombination.append([social[i][0], None])
    u = UserData(
        FirstName = first, 
        LastName = last, 
        Aliases = newCombination)
    queries = generate_queries(u)
    data = await collect_data(queries)
    print(data)


def query_trigger(first, last, social):
    asyncio.run(query_handler(first, last, social))

def start_thread():
    if thread != None:
        thread.start()
    else:
        print("start_thread() ERROR: THREAD IS NONETYPE")
    return ""

@app.route("/about")
def about_page():
    return render_template("about.html", noAbout=True)

#TESTING ONLY
@app.route("/loading")
def animation_test():
    return render_template("loading.html")

if __name__ == '__main__':
    app.run(debug=True)