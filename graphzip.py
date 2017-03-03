#!/usr/bin/env python3

""" Driver script to run GraphZip direct from the command line

./python3 graphzip.py [-d] fileordirectoryname

GraphZip can also be used as a Python library, see test files for examples

"""

import argparse
from operator import itemgetter
from sys import stderr

from compressor.compress import Compressor


def write_dictionary(model, fout=None):
    """ Print the pattern dictionary in readable .graph format

    If fout == None, print to stdout
    Otherwise, write to fout/file

    """
    model.P = sorted(model.P, key=itemgetter(2), reverse=True)
    for i, (g, c, s) in enumerate(model.P):
        if fout is None:
            print("%% Pattern %d" % (i + 1))
            print("%% Score:  %d" % s)
            print("%% Count:  %d" % c)
            for i, v in enumerate(g.vs):
                print("v %d %d" % (i, v['label']))
            for e in g.es:
                print("e %d %d %d" % (e.source, e.target, e['label']))
        else:
            fout.write("%% Pattern %d\n" % i)
            fout.write("%% Score:  %d\n" % s)
            fout.write("%% Count:  %d\n" % c)
            for i, v in enumerate(g.vs):
                fout.write("v %d %d\n" % (i, v['label']))
            for e in g.es:
                fout.write("e %d %d %d\n" %
                           (e.source, e.target, e['label']))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("graph_file",
                        help="Text file with printer names (one per line)",
                        type=str)

    parser.add_argument("-n", "--num_files",
                        help="Searches for files in directory graph_file",
                        type=int)

    parser.add_argument("-d", "--directed",
                        help="Assume directed graph",
                        action='store_true')

    parser.add_argument("-a", "--alpha",
                        help="Batch size (default 10)",
                        type=int)

    parser.add_argument("-t", "--theta",
                        help="Dictionary size (default inf.)",
                        type=int)

    parser.add_argument("-o", "--outfile",
                        help="Save patterns to file (default stdout)",
                        type=str)

    # parser.add_argument("-v", "--verbose",
    #                     help="Print debug to stdout",
    #                     action='store_true')

    args = parser.parse_args()

    if args.directed:
        use_directed = True
        print("[directed]")
    else:
        use_directed = False
        print("[undirected]")

    # Check range of alpha and theta
    if args.alpha is not None and args.alpha <= 0:
            print("Error: alpha must be > 0", file=stderr)
            exit(1)

    if args.theta is not None and args.theta <= 0:
            print("Error: theta must be > 0", file=stderr)
            exit(1)

    # Initialize model state
    if not args.alpha and not args.theta:
        model = Compressor(directed=use_directed)
    elif not args.alpha and args.theta is not None:
        model = Compressor(dict_size=args.theta,
                           directed=use_directed)
    elif args.alpha is not None and not args.theta:
        model = Compressor(batch_size=args.alpha,
                           directed=use_directed)
    else:
        model = Compressor(batch_size=args.alpha,
                           dict_size=args.theta,
                           directed=use_directed)

    # Compress multiple files (graph stream sequence) in a directory
    if args.num_files is not None:
        if args.num_files <= 0:
                print("Error: num_files must be > 0", file=stderr)
                exit(1)
        graphs_dir = args.graph_file

        # Files range from 1.graph to <num_files>.graph
        for i in range(1, args.num_files + 1):
            filename = "%s/%d.graph" % (graphs_dir, i)
            try:
                model.compress_file(filename)
                # Option to print dictionary at every iteration
                print("\n\nDictionary after processing %d.graph:" % i,
                      file=stderr)
                write_dictionary(model)
            except IOError:
                print("Error: unable to open file %s" % filename, file=stderr)
                exit(1)

    # Compress a single graph file
    else:
        try:
            model.compress_file(args.graph_file)
        except IOError:
            print("Error: unable to open file %s" % args.graph_file,
                  file=stderr)
            exit(1)

    # Writing to output file
    if args.outfile is not None:
        try:
            with open(args.outfile, 'w') as fout:
                write_dictionary(model, fout)
        except IOError:
            print("Error: unable to open file %s" % args.outfile, file=stderr)
            exit(1)

    # Writing to stdout
    else:
        print("\nWriting final pattern dictionary to stdout...\n", file=stderr)
        write_dictionary(model)

    print("\nDone.", file=stderr)
