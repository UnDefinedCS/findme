from flask import Flask, render_template, request, jsonify
from data_gen import generate_queries, collect_data
from app_types import UserData
import threading
import asyncio

app = Flask(__name__)
thread = None
results = None
search_complete = False

@app.route("/")
def index():
    return render_template("index.html", loading=False)

@app.route("/", methods=["POST"])
def submit_info():
    global thread, results, search_complete
    
    # Reset results for new search
    results = None
    search_complete = False
    
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
    additionalInfo = request.form['more_context']

    thread = threading.Thread(target=query_trigger, args=(first_name, last_name, combinedSocialAlias, additionalInfo), daemon=True)

    rendered_index = render_template("index.html", loading=True, start_thread=start_thread)

    return rendered_index

async def query_handler(first, last, social, additional):
    global results, search_complete
    newCombination = []
    for i in range(len(social)):
        if(social[i][1] != None):
            for j in range(len(social[i][1])):
                element = [social[i][0], social[i][1][j]]
                newCombination.append(element)
        else:
            newCombination.append([social[i][0], None])

    separatedContext = additional.split(',', 0)

    u = UserData(
        FirstName = first, 
        LastName = last, 
        Aliases = newCombination,
        Context = separatedContext
    )
    queries = generate_queries(u)
    data = await collect_data(queries)
    results = data
    search_complete = True
    print(data)

def query_trigger(first, last, social, additional):
    asyncio.run(query_handler(first, last, social, additional))

def start_thread():
    if thread != None:
        thread.start()
    else:
        print("start_thread() ERROR: THREAD IS NONETYPE")
    return ""

@app.route("/get-results")
def get_results():
    global results, search_complete
    return jsonify({
        'complete': search_complete,
        'results': results
    })

@app.route("/about")
def about_page():
    return render_template("about.html", noAbout=True)

#TESTING ONLY
@app.route("/loading")
def animation_test():
    return render_template("loading.html")

if __name__ == '__main__':
    app.run(debug=True)