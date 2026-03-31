from console_feedback import ERR

def generate_graph(base_data, results, max_label_length=20):
    """
    Generates an interactive SVG graph of queries pointing to URLs,
    ensures nodes do not overlap and URL labels are truncated.

    Parameters:
        base_data: dict (API compatibility)
        results: list of tuples (r, s), r contains 'query' and 'url'
        max_label_length: int, max characters displayed for labels

    Returns:
        SVG string
    """
    try:
        nodes = []
        edges = []
        node_map = {}  # URL -> node ID

        # Layout settings
        padding = 60
        vertical_spacing = 50  # base spacing, will scale with node radius
        horizontal_spacing = 350
        min_radius = 30
        char_width = 7

        svg = "<span>Could not generate graphic</span>"

        # Create nodes and edges
        for querys, s in results:
            for r in querys:
                query_label = r['query']
                url_label = r['url']

                # Add query node
                query_id = f"query_{len(nodes)}"
                nodes.append({'id': query_id, 'label': query_label, 'type': 'query'})

                # Add URL node if not present
                if url_label not in node_map:
                    url_id = f"url_{len(nodes)}"
                    nodes.append({'id': url_id, 'label': url_label, 'type': 'url'})
                    node_map[url_label] = url_id
                else:
                    url_id = node_map[url_label]

                # Add edge
                edges.append({'source': query_id, 'target': url_id})

                # Assign positions & dynamic radius, prevent overlaps
                query_y = padding
                url_y_next = padding
                max_x = 0
                max_y = 0

                query_nodes = [n for n in nodes if n['type'] == 'query']
                url_nodes = [n for n in nodes if n['type'] == 'url']

                # Assign query node positions
                for node in query_nodes:
                    node['r'] = max(min_radius, len(node['label']) * char_width // 2)
                    node['x'] = padding + node['r']
                    node['y'] = query_y + node['r']
                    query_y += vertical_spacing + node['r'] * 2
                    max_x = max(max_x, node['x'] + node['r'] + padding)
                    max_y = max(max_y, node['y'] + node['r'] + padding)

                # Assign URL node positions
                for node in url_nodes:
                    node['r'] = max(min_radius, max_label_length * char_width // 2)
                    node['x'] = padding + horizontal_spacing + node['r']
                    node['y'] = url_y_next + node['r']
                    url_y_next += vertical_spacing + node['r'] * 2
                    max_x = max(max_x, node['x'] + node['r'] + padding)
                    max_y = max(max_y, node['y'] + node['r'] + padding)

                # Build SVG with responsive viewBox
                svg = f'<svg width="100%" height="100%" viewBox="0 0 {max_x} {max_y}" '
                svg += 'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">\n'

                # Styles
                svg += '<style>'
                svg += '.edge { stroke: #00ff00; stroke-width: 2; marker-end: url(#arrowhead); opacity: 0.7; }'
                svg += '.query-node { fill: rgba(0, 255, 0, 0.3); stroke: #00ff00; stroke-width: 2; }'
                svg += '.url-node { fill: rgba(0, 200, 100, 0.3); stroke: #00cc00; stroke-width: 2; }'
                svg += '.label { font-size: 11px; fill: #00ff00; text-anchor: middle; font-family: monospace; font-weight: bold; }'
                svg += '</style>\n'

                # Arrow marker
                svg += '''<defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
                        <polygon points="0 0, 10 3, 0 6" fill="#00ff00" />
                    </marker>
                </defs>\n'''

                # Draw edges
                for edge in edges:
                    source_node = next(n for n in nodes if n['id'] == edge['source'])
                    target_node = next(n for n in nodes if n['id'] == edge['target'])
                    svg += f'<line x1="{source_node["x"] + source_node["r"]}" y1="{source_node["y"]}" '
                    svg += f'x2="{target_node["x"] - target_node["r"]}" y2="{target_node["y"]}" class="edge" />\n'

                # Draw nodes with truncated URL labels
                for node in nodes:
                    node_class = 'query-node' if node['type'] == 'query' else 'url-node'
                    label_class = 'label'

                    label_text = node['label']
                    if node['type'] == 'url' and len(label_text) > max_label_length:
                        label_text = label_text[:max_label_length] + '…'

                    if node['type'] == 'url':
                        svg += f'<a xlink:href="{node["label"]}" target="_blank">'
                        svg += f'<circle cx="{node["x"]}" cy="{node["y"]}" r="{node["r"]}" class="{node_class}" />\n'
                        svg += f'<text x="{node["x"]}" y="{node["y"] + 4}" class="{label_class}">{label_text}</text>\n'
                        svg += '</a>\n'
                    else:
                        svg += f'<circle cx="{node["x"]}" cy="{node["y"]}" r="{node["r"]}" class="{node_class}" />\n'
                        svg += f'<text x="{node["x"]}" y="{node["y"] + 4}" class="{label_class}">{label_text}</text>\n'

                svg += '</svg>'

        return svg

    except Exception as e:
        print(f"{ERR} Issue Occurred Generating Graph!")
        import traceback
        traceback.print_exc()
        return None