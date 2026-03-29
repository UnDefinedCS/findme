from flask import Flask, render_template, request, jsonify
from data_gen import generate_queries, collect_data
from app_types import UserData
from data_analyze import review
import threading
import asyncio

from graphify import generate_graph

app = Flask(__name__)
thread = None
results = None
search_complete = False
search_params = None
graph_data = None

@app.route("/")
def index():
    return render_template("index.html", loading=False)

@app.route("/", methods=["POST"])
def submit_info():
    global thread, results, search_complete, search_params, graph_data
    
    # Reset results for new search
    results = None
    search_complete = False
    graph_data = None
    
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    alias = request.form.getlist('alias')
    combinedSocialAlias = []
    platforms_list = []
    
    for i in range(len(alias)):
        social_media = request.form.getlist('social_media_' + str(i))
        element = []
        if(len(social_media) != 0):
            element = [alias[i], social_media]
            platforms_list.extend(social_media)
        else:
            element = [alias[i], None]
        combinedSocialAlias.append(element)
    
    additionalInfo = request.form['more_context']
    context_list = [c.strip() for c in additionalInfo.split(',') if c.strip()]
    
    # Store search parameters for graph generation
    search_params = {
        'first_name': first_name,
        'last_name': last_name,
        'aliases': alias,
        'platforms': list(set(platforms_list)),
        'context': context_list
    }

    thread = threading.Thread(target=query_trigger, args=(first_name, last_name, combinedSocialAlias, additionalInfo), daemon=True)

    queries = asyncio.run(query_handler(first_name, last_name, social_media, additionalInfo, False))

    rendered_index = render_template("index.html", loading=True, start_thread=start_thread, query_num=len(queries))

    return rendered_index

async def query_handler(first, last, social, additional, collection = True):
    global results, search_complete, graph_data
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
    if collection:
        data = await collect_data(queries)
        data = await review(u, data)
        results = data

        # Generate graph after results are collected
        if search_params:
            generate_graph_data(search_params, data)
        
        search_complete = True
    else:
        return queries

def query_trigger(first, last, social, additional):
    asyncio.run(query_handler(first, last, social, additional))

def generate_graph_data(base_data, results):
    """Generate directed graph from search parameters and results"""
    global graph_data
    graph_data = generate_graph(base_data, results)

def start_thread():
    global thread
    if thread != None:
        thread.start()
    else:
        print("start_thread() ERROR: THREAD IS NONETYPE")
    return ""

@app.route("/get-results")
def get_results():
    global results, search_complete, graph_data
    return jsonify({
        'complete': search_complete,
        'results': results,
        'graph': graph_data
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