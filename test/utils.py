""" Functions used to parse a variety of graph file formats """

import xml.etree.cElementTree as ET  # for parsing GraphML files

from igraph import Graph


# XXX Graph.Read_GraphML is having trouble with valid .graphml files...
# eg.:
# SystemError: <built-in method Read_GraphML of type object at 0x7fad084f0418>
# returned NULL without setting an error
def import_graphml(fin, color_func=None):
    """ Turns a GraphML file into an iGraph object

    Args:
        fin (str): Full path to the *.graphml file

    Returns:
        Graph: Graph object with name and color fields manually set
               All other fields are directly imported from GraphML's .attrib
    """
    try:
        g = Graph().Read_GraphML(fin)
    except Exception:
        print("\nError reading file %s\n" % fin)
        raise

    # assign the 'name' field so that we can access the nodes by ids
    # note however that now the 'id' and 'name' fields are redundant
    g.vs['name'] = g.vs['id']

    # set the coloring based on IDs
    if color_func:
        g.vs['coloring'] = [color_func(id_str) for id_str in g.vs['id']]

    return g


def import_insts(fin):
    """ Turns a SUBGEN *.insts file into a list of iGraph objects

    Args:
        fin (str): Full path to the *.insts file

    Returns:
        list[Graph]: Graph objects parsed from the *.insts file

    """
    line_err = "Can't parse line: '%s'"
    graphs = []
    curr_graph = None
    graph_count = 0

    with open(fin, 'r') as f:
        for line in f:

            w = line.strip().split()
            if (len(w) == 0 or w[0] == '%'):
                continue

            elif w[0] == 'Instance':
                # Start a new graph object
                if(curr_graph is not None):
                    raise ValueError(line_err % line)
                curr_graph = Graph()
                graph_count += 1

            elif w[0] == 'v':
                name, label = w[1], w[2]
                if label[0] == 'v':
                    # Strip 'e' from label
                    label = int(label[1:])
                else:
                    print('Unknown label: %s' % label)
                curr_graph.add_vertex(
                            name, id=name, label=label)

            elif w[0] == 'e':
                label, v1, v2 = w[1], w[2], w[3]
                if label[0] == 'e':
                    # Strip 'e' from label
                    label = int(label[1:])
                else:
                    print('Unknown label: %s' % label)
                curr_graph.add_edge(v1, v2, label=label)  # XXX add both ways?

            elif w[0] == '}':
                # Save the graph object
                if not curr_graph:
                    raise ValueError(line_err % line)
                graphs.append(curr_graph)
                curr_graph = None

            else:
                raise ValueError(line_err % line)

    if graph_count != len(graphs):
        print("Warning: Expected {} graphs but only got {}".format(
              graph_count, len(graphs)))
    else:
        print("Succesfully imported %d graphs from %s" % (len(graphs), fin))

    return graphs


def parse_subdue_output(fin):
    """ Parse SUBDUE's output to a list of iGraph graphs """
    graphs = []
    with open(fin) as f:
        graph = None
        skip_next = False
        for line in f:
            # '(n)' indicates the beginning of the n'th substructure
            if line[0] == '(':
                if graph is not None:
                    raise IOError(
                        'Started a new graph without finishing the old one')
                graph = Graph()
                skip_next = True
                continue
            # Skip the first line after '(n) Substructure'
            if skip_next:
                skip_next = False
                continue
            # Empty line during a graph read indicates done
            if graph is not None and line.strip() == '':
                graphs.append(graph)
                graph = None
            # If we have an open graph, we should expect a vertex or edge line
            if graph is not None:
                w = line.strip().split()
                # Vertex
                if w[0] == 'v':
                    name, label = w[1], int(w[2])
                    graph.add_vertex(name, label=label)
                # Edge
                elif w[0] == 'd' or w[0] == 'e' or w[0] == 'u':
                    v1, v2, label = w[1], w[2], int(w[3])
                    graph.add_edge(v1, v2, label=label)
                else:
                    raise IOError('Unexpected input: %s' % line)
    print("Succesfully imported %d graphs from %s" % (len(graphs), fin))
    return graphs


# TODO Change to return a list of graphs (general) instead of tuple format
def parse_edges_graphml(fin):
    """ Turns a GraphML (.graphml) file into a list of edges

    Args:
        filename (str): Full path to the *.insts file

    Returns:
        list[Graph]: Graph objects parsed from the *.insts file

    Note: This only expects the file format generated from a specific script
    See: http://www.eecs.wsu.edu/~yyao/DirectedStudyI/Datasets/Facebook

    File format should be (tags):
    {http://graphml.graphdrawing.org/xmlns}key
    {http://graphml.graphdrawing.org/xmlns}key
    {http://graphml.graphdrawing.org/xmlns}key
    {http://graphml.graphdrawing.org/xmlns}graph
        {http://graphml.graphdrawing.org/xmlns}node
        {http://graphml.graphdrawing.org/xmlns}node
        {http://graphml.graphdrawing.org/xmlns}edge
        ...
        {http://graphml.graphdrawing.org/xmlns}node
        {http://graphml.graphdrawing.org/xmlns}node
        {http://graphml.graphdrawing.org/xmlns}edge
    """
    tree = ET.parse(fin)
    root = tree.getroot()

    # XXX just use index=3, safe via standard?
    graph_index = 3
    # graph_index = None
    # for i,child in enumerate(root):
    #     if child.tag == "{http://graphml.graphdrawing.org/xmlns}graph":
    #         graph_index = i
    # if not graph_index:
    #     raise Exception("GraphML file did not contain graph entry")

    edges = []
    graph = root[graph_index]
    for i in range(len(graph)):
        if graph[i].tag != "{http://graphml.graphdrawing.org/xmlns}edge":
            continue
        edge = graph[i]
        # (source,dest,timestamp) tuple
        edges.append((edge.attrib['source'],
                      edge.attrib['target'],
                      edge[0].text))

    return edges
