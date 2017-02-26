import unittest
from collections import defaultdict

from igraph import Graph


class TestiGraph(unittest.TestCase):
    """
    Basic tests to make sure iGraph is working the way we expect for the
    purposes of compress.py
    """

    def setUp(self):
        """
        Simple example graph:

        1010,A ----- 1011,B
           |      /
           |     /
           |    /
           |   /
           |  /
           | /
        1100,C ----- 1101,D
        """
        G = Graph()
        G.add_vertex("1010", id=1010, label="A")  # index 0
        G.add_vertex("1011", id=1011, label="B")  # index 1
        G.add_vertex("1100", id=1100, label="C")  # index 2
        G.add_vertex("1101", id=1101, label="D")  # index 3
        G.add_edge("1010", "1100")
        G.add_edge("1010", "1011")
        G.add_edge("1011", "1100")
        G.add_edge("1100", "1101")

        Gs = Graph()
        # Add the vertices in a different order so we get different indices
        Gs.add_vertex("1011", label="B")  # index 0
        Gs.add_vertex("1010", label="A")  # index 1
        Gs.add_edge("1010", "1011")

        self.G = G
        self.Gs = Gs

    def test_subisomorphisms(self):
        G = self.G
        Gs = self.Gs

        c1 = [int(v["name"]) for v in G.vs]
        c2 = [int(v["name"]) for v in Gs.vs]
        vmap = G.get_subisomorphisms_vf2(Gs, color1=c1, color2=c2)

        # Check that we get an isomorphism
        # Graph Gs:    index     ->   element     :Graph G
        #           vertex 0 (B) -> vertex 1 (B)
        #           vertex 1 (A) -> vertex 0 (A)
        # Graph G:                                :Graph Gs
        #           vertex 0 (A) -> vertex 1 (A)
        #           vertex 1 (B) -> vertex 0 (A)
        self.assertEqual(vmap, [[1, 0]])

    def test_isomorphic(self):
        self.assertFalse(self.G.isomorphic_vf2(self.Gs))

        # basic isomorphism w/o coloring
        self.Gs.add_vertex("1100")
        self.Gs.add_vertex("1101_wrong")
        self.Gs.add_edge("1010", "1100")
        self.Gs.add_edge("1011", "1100")
        self.Gs.add_edge("1100", "1101_wrong")
        self.assertTrue(self.G.isomorphic_vf2(self.Gs))

        # check that isomorphic checks using coloring works
        # (by using a field called id which is name (str) casted as (int))
        G2 = Graph()
        # add the vertices in a different order so they have differnet
        # underlying indices
        G2.add_vertex("1100", id=1100)  # index 2
        G2.add_vertex("1101", id=1101)  # index 3
        G2.add_vertex("1010", id=1010)  # index 0
        G2.add_vertex("1011", id=1011)  # index 1
        # add some of the edges in the other direction
        G2.add_edge("1100", "1011")
        G2.add_edge("1101", "1100")
        G2.add_edge("1010", "1100")
        G2.add_edge("1010", "1011")
        c1 = self.G.vs["id"]
        c2 = G2.vs["id"]
        self.assertTrue(self.G.isomorphic_vf2(G2, color1=c1, color2=c2))
        self.assertTrue(self.G.isomorphic_vf2(G2))  # sanity check

    def test_are_connected(self):
        G = self.G
        Gs = self.Gs
        # try referencing via vertex names instead of indexes
        self.assertTrue(G.are_connected("1011", "1100"))
        self.assertTrue(G.are_connected("1100", "1011"))
        self.assertTrue(Gs.are_connected("1011", "1010"))
        self.assertTrue(Gs.are_connected("1010", "1011"))

    def test_indexing(self):
        G = self.G
        Gs = self.Gs
        # accessing VS
        self.assertEqual(G.vs.find("1100")["name"], "1100")
        self.assertEqual(G.vs[2]["name"], "1100")
        # accessing ES
        self.assertEqual(G.es[0].source, G.vs.find("1010").index)
        self.assertEqual(G.es[0].source, 0)
        self.assertEqual(G.es[0].target, G.vs.find("1100").index)
        self.assertEqual(G.es[0].target, 2)

    def test_names(self):
        G = self.G
        Gs = self.Gs
        # pulling the names out via a property of the graph should be an
        # effecient alternative to list comprehension when we need to color
        # edges before the VF2 algorithm
        color_str = G.vs["name"]
        color_int = G.vs["id"]
        self.assertEqual(color_str, ["1010", "1011", "1100", "1101"])
        self.assertEqual(color_int, [int(v["name"]) for v in G.vs])

    # Won't work unless we implement canonical ordering for the hash function
    # Currently just uses default (memory addresses)
    @unittest.expectedFailure
    def test_hashable(self):
        d = defaultdict(Graph)
        # Two identical graphs with the same vertices and labels should hash
        # to the same string
        d[G] = 1
        print("hash g: %s\n hash g2: %s\n" % (hash(G), hash(G2)))
        self.assertEqual((G2 in d), True)


if __name__ == '__main__':
    unittest.main()
