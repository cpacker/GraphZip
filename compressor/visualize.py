""" Functions for visualizing lists of iGraph objects as SVG images

Filenames for SVGs:

When saving a single graphs (one graph per SVG):
    [fout]_c[count].svg

Where fout is a function parameter (str) and count is retrieved from the list

when saving a grid (square) of graphs:
    combined_[fout].svg

Where fout is a function parameter (str)

"""

import os
from operator import itemgetter

from igraph import Graph

import svgutils.transform as sg  # Needed for combining SVG files


def visualize_separate(fout, graphs, top=True, n=None):
    """ Save the graphs in a list of graphs as separate SVG files

    Args:
        fout (str): Filename prefix to save SVG to (appended by count info)
        graphs (list[tuple[Graph,int,float]]):
            List of graphs in format of (graph,count,score) tuples
            Technically only graph and count are needed
        n (int): The number of patterns to save (save the top-n)
    """
    if not n:
        n = len(graphs)
    if (n > len(graphs)):
        raise ValueError("N (%d) is greater than list size (%d)"
                         % (n, len(graphs)))
    graphs = sorted(graphs, key=itemgetter(2), reverse=top)  # sort first
    for i in range(n):
        g, c, s = graphs[i]
        fname = "{}_c{}_i{}.svg".format(fout, c, i)
        print("Saving pattern #{} to {}..".format(i+1, fname), end='\r')
        g.write_svg(fname, labels="label")


def visualize_grid(fout, graphs, top=True, n=None, delete_singles=True):
    """ Visualize a list of graphs in a square grid format SVG file

    Args:
        fout (str): Filename to save SVG to
        graphs (list[tuple[Graph,int,float]]):
            List of graphs in format of (graph,count,score) tuples
            Technically only graph and score are needed
        n (int): The dimensions of the grid (nXn square)
                 If no 'n' is provided then the smallest square (that can
                 fit all graphs in the list) is used
        delete_singles (bool): True to delete intermediate single SVG files

    Warning: Function creates temporary files, which are cleaned up on exit

    Note: the final SVG can be easily converted to PNG, e.g. w/ inkscape via
          inkscape --export-pdf=fig_final.pdf fig_final.svg
          inkscape --export-png=fig_final.png fig_final.svg
    """
    if len(graphs) == 0:
        return

    # find a square size that captures all items in the list
    if not n:
        n = 1
        while(n*n < len(graphs)):
            n = n+1
    # grid dimensions are: n x n, so we have n*n total elements
    N = n*n

    # generate the separate SVGs before we combine them
    # we need to generate N SVGs
    n_graphs = min(len(graphs), N)  # number of graphs on the grid - blank spaces
    visualize_separate(fout, graphs, top, n_graphs)

    # Load the saved figures into memory
    graphs = sorted(graphs, key=itemgetter(2), reverse=top)  # sort first
    fnames = ["{}_c{}_i{}.svg".format(
              fout, c, i) for i, (g, c, s) in enumerate(graphs[:N])]
    figs = [sg.fromfile(f) for f in fnames]
    # get the plot objects
    plots = [fig.getroot() for fig in figs]
    # create the captions
    caps = ["Appeared {} times".format(c) for g, c, s in graphs[:N]]

    width, height = figs[0].get_size()
    width, height = int(width[:-2]), int(height[:-2])  # strip 'px' from '400px'
    padding = 100

    # organize into n x n grid
    i = 0
    for r in range(n):
        for c in range(n):
            # leave a blank space in the grid if we're out of graphs
            if i >= len(graphs):
                continue
            x = padding + r*(height+padding)
            y = padding + c*(width+padding)
            plots[i].moveto(x, y)
            # add text labels
            caps[i] = sg.TextElement(x, y+height+(padding/2),
                                     caps[i], size=25, weight="bold")
            i += 1

    # create new combined SVG figure
    fig = sg.SVGFigure("{}px".format(padding + n*(height+padding)),
                       "{}px".format(padding + n*(width+padding)))

    # append plots and labels to figure
    fig.append(plots)
    fig.append(caps)

    fname = "combined_{}.svg".format(fout)
    print("Saving combined SVG to {}...".format(fname))
    fig.save(fname)

    # clear the independent SVG files, leaving only the combined file
    if delete_singles:
        print("Clearing leftover SVG files...")
        for f in fnames:
            os.remove(f)
