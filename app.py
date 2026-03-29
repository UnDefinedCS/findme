from flask import Flask, render_template, request, jsonify
from data_gen import generate_queries, collect_data
from app_types import UserData
from data_analyze import review
import threading
import asyncio

try:
    from directed_graph_generator import DirectedGraphGenerator
except ImportError:
    # If import fails, try alternative name
    try:
        import directed_graph_generator as dgg
        DirectedGraphGenerator = dgg.DirectedGraphGenerator
    except (ImportError, AttributeError):
        DirectedGraphGenerator = None

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

def generate_graph_data(search_params, results):
    """Generate directed graph from search parameters and results"""
    global graph_data
    
    try:
        # Create an organized SVG-based graph visualization with better spacing
        nodes = []
        edges = []
        node_map = {}
        
        # Calculate layout dimensions based on node count
        input_count = sum([
            1 if search_params['first_name'] else 0,
            1 if search_params['last_name'] else 0,
            len([a for a in search_params['aliases'] if a]),
            len([p for p in search_params['platforms'] if p])
        ])
        
        result_count = len(results)
        max_nodes_per_side = max(input_count, result_count)
        
        # Organized spacing
        padding = 60
        node_radius = 40
        vertical_spacing = 100
        horizontal_spacing = 350
        
        # Calculate SVG dimensions based on nodes
        svg_height = max_nodes_per_side * vertical_spacing + (padding * 2)
        svg_width = horizontal_spacing + (padding * 2) + (node_radius * 2)
        
        # Add input nodes (left side) - centered vertically
        input_y_start = padding + (max_nodes_per_side - input_count) * (vertical_spacing / 2)
        input_y = input_y_start
        
        if search_params['first_name']:
            node_id = f"input_{len(nodes)}"
            nodes.append({
                'id': node_id,
                'label': search_params['first_name'],
                'x': padding + node_radius,
                'y': input_y,
                'type': 'input'
            })
            node_map['first_name'] = node_id
            input_y += vertical_spacing
        
        if search_params['last_name']:
            node_id = f"input_{len(nodes)}"
            nodes.append({
                'id': node_id,
                'label': search_params['last_name'],
                'x': padding + node_radius,
                'y': input_y,
                'type': 'input'
            })
            node_map['last_name'] = node_id
            input_y += vertical_spacing
        
        for idx, alias in enumerate(search_params['aliases']):
            if alias:
                node_id = f"input_{len(nodes)}"
                nodes.append({
                    'id': node_id,
                    'label': f"@{alias}",
                    'x': padding + node_radius,
                    'y': input_y,
                    'type': 'input'
                })
                node_map[f'alias_{idx}'] = node_id
                input_y += vertical_spacing
        
        for idx, platform in enumerate(search_params['platforms']):
            if platform:
                node_id = f"input_{len(nodes)}"
                nodes.append({
                    'id': node_id,
                    'label': platform,
                    'x': padding + node_radius,
                    'y': input_y,
                    'type': 'platform'
                })
                node_map[f'platform_{idx}'] = node_id
                input_y += vertical_spacing
        
        # Add result nodes (right side) - centered vertically, limit to 8
        result_y_start = padding + (max_nodes_per_side - result_count) * (vertical_spacing / 2)
        result_y = result_y_start
        
        if results:
            for idx, result in enumerate(results):
                result_node_id = f"result_{idx}"
                title = result[0].get('site_title', result[0].get('url', 'Unknown'))[:20]
                nodes.append({
                    'id': result_node_id,
                    'label': title,
                    'x': padding + horizontal_spacing + node_radius,
                    'y': result_y,
                    'type': 'result'
                })
                result_y += vertical_spacing
                
                # Create edges
                query = result[0].get('query', '').lower()
                
                if 'first_name' in node_map and search_params['first_name'].lower() in query:
                    edges.append({
                        'source': node_map['first_name'],
                        'target': result_node_id
                    })
                
                if 'last_name' in node_map and search_params['last_name'].lower() in query:
                    edges.append({
                        'source': node_map['last_name'],
                        'target': result_node_id
                    })
                
                for idx_alias, alias in enumerate(search_params['aliases']):
                    if alias and alias.lower() in query:
                        key = f'alias_{idx_alias}'
                        if key in node_map:
                            edges.append({
                                'source': node_map[key],
                                'target': result_node_id
                            })
                
                for idx_platform, platform in enumerate(search_params['platforms']):
                    if platform and platform.lower() in query:
                        key = f'platform_{idx_platform}'
                        if key in node_map:
                            edges.append({
                                'source': node_map[key],
                                'target': result_node_id
                            })
        
        # Generate SVG
        svg = f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">\n'
        svg += '<style>'
        svg += '.edge { stroke: #00ff00; stroke-width: 2; marker-end: url(#arrowhead); opacity: 0.7; }'
        svg += '.input-node { fill: rgba(0, 255, 0, 0.3); stroke: #00ff00; stroke-width: 2; }'
        svg += '.platform-node { fill: rgba(0, 255, 255, 0.3); stroke: #00ffff; stroke-width: 2; }'
        svg += '.result-node { fill: rgba(0, 200, 100, 0.3); stroke: #00cc00; stroke-width: 2; }'
        svg += '.label { font-size: 11px; fill: #00ff00; text-anchor: middle; font-family: monospace; font-weight: bold; }'
        svg += '.label-result { font-size: 10px; fill: #00ff00; text-anchor: middle; font-family: monospace; }'
        svg += '</style>'
        
        # Arrow marker
        svg += '''<defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#00ff00" />
            </marker>
        </defs>'''
        
        # Draw edges first (so they appear behind nodes)
        for edge in edges:
            source_node = next((n for n in nodes if n['id'] == edge['source']), None)
            target_node = next((n for n in nodes if n['id'] == edge['target']), None)
            if source_node and target_node:
                svg += f'<line x1="{source_node["x"] + node_radius}" y1="{source_node["y"]}" x2="{target_node["x"] - node_radius}" y2="{target_node["y"]}" class="edge" />\n'
        
        # Draw nodes
        for node in nodes:
            node_class = f"{node['type']}-node"
            label_class = 'label-result' if node['type'] == 'result' else 'label'
            svg += f'<circle cx="{node["x"]}" cy="{node["y"]}" r="{node_radius}" class="{node_class}" />\n'
            svg += f'<text x="{node["x"]}" y="{node["y"] + 4}" class="{label_class}">{node["label"][:18]}</text>\n'
        
        svg += '</svg>'
        
        graph_data = svg
        
    except Exception as e:
        print(f"Error generating graph: {e}")
        import traceback
        traceback.print_exc()
        graph_data = None

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