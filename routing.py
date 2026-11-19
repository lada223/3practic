def build_graph(network):
    graph = {}
    for router in network["routers"]:
        graph[router] = []
    for link in network["links"]:
        first = link["from"]
        second = link["to"]
        cost = link["cost"]
        graph[first].append((second, cost))
        graph[second].append((first, cost))
    return graph

def shortest_path(graph, start, end):
    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    unvisited = list(graph.keys())
    distances[start] = 0

    while unvisited:
        current = min(unvisited, key=lambda node: distances[node])
        if current == end or distances[current] == float("inf"):
            break
        unvisited.remove(current)

        for neighbor, cost in graph[current]:
            new_distance = distances[current] + cost
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current

    path = []
    current = end
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path, distances[end]