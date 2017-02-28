*Note: Repository is in the process of being updated.*

# GraphZip

GraphZip is a scalable method for mining interesting patterns in graph streams, based on the Lempel-Ziv class of compression algorithms.

This repository contains a reference implementation of the GraphZip algorithm, written in Python.

For more information, see our paper:
> [*GraphZip: Dictionary-based Compression for Mining Graph Streams. Charles Packer, Lawrence Holder.*](http://cseweb.ucsd.edu/~cpacker/pdfs/graphzip.pdf)

## Dependencies

[Python 3](https://www.python.org/downloads/) and [python-igraph](http://igraph.org/python/) are required.

Once you have a working version of Python 3, install python-igraph with:

`pip3 install python-igraph`

Note: `python-igraph` is not to be confused with the `igraph` package (renamed to `jgraph`).


## Usage

Run GraphZip directly from the command line with:

`python3 graphzip.py graph_file [-n NUM_FILES] [-a ALPHA] [-t THETA] [-o OUTFILE]`

Use flags `-a` and `-t` to set the batch size and dictionary size (hyperparameters of the GraphZip model).

By default, the pattern dictionary is dumped to stdout - use `-o` to save it to a file.

Using `-n NUM_FILES` turns on multi-file mode, and GraphZip will treat `graph_file` as a directory holding `NUM_FILES` sequential graph stream files, labelled `1.graph` to `[NUM_FILES].graph`.


## File format

The correct format for `.graph` files is:

```
% '%' to start comments
v [vertex id (int)] [vertex label (int)]
e [source vertex id (int)] [target vertex id (int)] [edge label (int)]
```

For example:
```
% example 3-clique with vertex labels "100", "999" and edge labels "1", "2", "3"
v 1 100
v 2 999
v 3 100
e 1 2 1
e 1 3 2
e 2 3 3
```

Vertices must be defined prior to being referenced by an edge (or the vertex label would be unknown).

In the case of processing a graph stream over sequential `.graph` files, having `Compressor`'s `label_history_per_file` property set to `False` and `add_implicit_vertices` set to `True` (the default) allows edges to reference vertices declared in previous files. For further details see the inline comments.

### Examples

Run GraphZip on `test.graph` with a batch size of `5` and a dictionary size of `10`:

`python3 graphzip.py test.graph -a 5 -t 10`

Run GraphZip on files `1.graph` through `100.graph` located in directory `test_graphs/`, using a batch size of 5 and the default dictionary size:

`python3 graphzip.py test_graphs -n 100 -a 5`

## Experiments

Several example experiments are located in the unit tests directory under `tests/test_expr.py`.

Run the algorithm on several example graphs (located in `data/`) by navigating to the root project directory then running:

`python3 -m unittest`

To run a specific test use the format:

`python3 -m unittest test.[test_file].[TestSuite].[test_function]`

For example, to run the 3-clique test located in the `TestGraphZipSubgen` suite:

`python3 -m unittest test.test_expr.TestGraphZipSubgen.test_4PATH_20`

For details on specific examples, see the files under the `test/` directory.

<!---
## Citation Policy

If you find our , please consider citing:

> GraphZip: Dictionary-based Compression for Mining Graph Streams. Charles Packer, Lawrence Holder.

```
bibtex
```
--->

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details
