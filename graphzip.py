""" Driver script to run GraphZip direct from the command-line

./python graphzip.py [-d] fileordirectoryname

GraphZip can also be used as a Python library, see test files for examples

"""

import argparse

from compressor.compress import Compressor


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("graph_file",
                        help="Text file with printer names (one per line)",
                        type=str)

    parser.add_argument("-n", "--num_files",
                        help="Searches for files in directory graph_file",
                        type=int)

    parser.add_argument("-a", "--alpha",
                        help="Batch size (default 10)",
                        type=int)

    parser.add_argument("-t", "--theta",
                        help="Dictionary size (default inf.)",
                        type=int)

    parser.add_argument("-v", "--verbose",
                        help="Print debug to stdout",
                        action='store_true')

    args = parser.parse_args()

    # Check range of alpha and theta
    if args.alpha is not None and args.alpha <= 0:
            print("Error: alpha must be > 0")
            exit(1)

    if args.theta is not None and args.theta <= 0:
            print("Error: theta must be > 0")
            exit(1)

    model = Compressor(args.alpha, args.theta)

    # Compress multiple files (graph stream sequence) in a directory
    if args.num_files is not None:
        if args.num_files <= 0:
                print("Error: num_files must be > 0")
                exit(1)
        graphs_dir = args.graph_file

        # Files range from 1.graph to <num_files>.graph
        for i in range(1, args.num_files + 1):
            filename = "%s/%d.graph" % (graphs_dir, i)
            try:
                model.compress_file(filename)
            except IOError:
                print("Error: was unable to open file %s" % filename)

    # Compress a single graph file
    else:
        model.compress_file(filename)

    print("Done.")
