""" Test file that """

import cProfile
import os
import unittest
import sys
import time
from operator import itemgetter
from pstats import Stats
from timeit import default_timer as timer
try:
    import cPickle as pickle
except:
    import pickle

from compressor.compress import Compressor
from .utils import import_insts, parse_subdue_output


DEBUG = True  # enable for debug print output
SAVE = False  # save the SVGs from each example
PROFILE = False

GRAPH_DIR = "data/"  # root dir for graph (eg. *.g, *.graph) files
IMAGE_DIR = "images/"  # root dir for SVG images
SUBDUE_DIR = "../SUBDUE/subdue-5.2.2/bin/"  # location of SUBDUE exe
SUBGEN_DIR = "data/SUBGEN/"  # location of SUBGEN .graph and .insts files


def get_gt_patterns_found(groundtruth, patterns):
    """ Returns an error metric using the groundtruth and returned patterns

    Error = #gt_patterns missed / total #gt_patterns

    """
    hits = [0 for g in groundtruth]  # 1 if hit, 0 if miss (on gt)

    # For each ground_truth pattern, check if we found it with our algorithm
    for i, gt in enumerate(groundtruth):
        c1 = gt.vs["label"]
        c1_edge = gt.es["label"]

        for p in patterns:
            if len(p.es) == 0:
                continue
            c2 = p.vs["label"]
            c2_edge = p.es["label"]

            if len(c1) != len(c2) or len(c1_edge) != len(c2_edge):
                continue

            try:
                if gt.isomorphic_vf2(p, color1=c1, color2=c2,
                                     edge_color1=c1_edge, edge_color2=c2_edge):
                    if(hits[i] >= 1):
                        print("Warning: ground-truth pattern already found")
                    else:
                        hits[i] = 1
                        # print("hit:",p)
                    break
            except:
                print('Error')
                print(c1_edge)
                print(c2_edge)

    return (sum(hits), len(hits))  # hits, total


def get_patterns_also_in_gt(groundtruth, patterns):
    """ Returns an error metric using the groundtruth and returned patterns

    Error = #patterns not in gt / total #patterns

    """
    hits = [0 for p in patterns]  # 1 if hit, 0 if miss

    # For each ground_truth pattern, check if we found it with our algorithm
    for i, p in enumerate(patterns):
        if len(p.es) == 0:
            continue
        c1 = p.vs["label"]
        c1_edge = p.es["label"]

        for gt in groundtruth:
            c2 = gt.vs["label"]
            c2_edge = gt.es["label"]

            if len(c1) != len(c2) or len(c1_edge) != len(c2_edge):
                continue

            if gt.isomorphic_vf2(p, color1=c1, color2=c2,
                                 edge_color1=c1_edge, edge_color2=c2_edge):
                if(hits[i] >= 1):
                    print("Warning: ground-truth pattern already found")
                else:
                    hits[i] = 1
                break  # consider multiple instances of same pattern?

    return (sum(hits), len(hits))  # hits,total


def print_top_n_graphs(C, n):
    """ Print (repr) the iGraph representation and count of the top-N patterns

    Args:
        C (Compressor object): Has member field p (list of (Graph,c) tuples)
        n (int): Number of patterns to print

    """
    ps = sorted(C.P, key=itemgetter(2), reverse=True)
    for i in range(n):
        if i >= len(ps):
            break
        p, c, s = ps[i]
        print(p)
        print("Appeared %d times" % c)


class TestExamples(unittest.TestCase):
    """ Test the main compression algorithm using small example graphs

    The following tests only test that (>0) patterns are captured, ensuring
    basic functionality of the compressor

    """

    def setUp(self):
        batch_size = 50
        dict_size = 5000
        if DEBUG:
            print("Setting up compressor with batch_size=%d, dict_size=%d ..."
                  % (batch_size, dict_size))
        self.c = Compressor(batch_size, dict_size)
        if PROFILE:
            self.pr = cProfile.Profile()
            self.pr.enable()

    def tearDown(self):
        if PROFILE:
            p = Stats(self.pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()
            if DEBUG:
                print('\n{}>>>'.format('-'*77))

    def test_nonempty_basic(self):
        if DEBUG:
            print("Running compression on basic1.graph ...")
        self.c.compress_file(GRAPH_DIR + "basic1.graph")
        # No "correct" patterns, however we should extract at least ONE pattern
        self.assertNotEqual(self.c.P, [])

    def test_nonempty_groups(self):
        if DEBUG:
            print("Running compression on groups.graph ...")
        self.c.compress_file(GRAPH_DIR + "groups.graph")
        self.assertNotEqual(self.c.P, [])

    def test_nonempty_diabetes(self):
        if DEBUG:
            print("Running compression on diabetes_0.graph ...")
        self.c.compress_file(GRAPH_DIR + "diabetes_0.graph")
        self.assertNotEqual(self.c.P, [])


@unittest.skip("Non-standard test")
class TestGraphZipSubgen(unittest.TestCase):
    """ Test GraphZip on graphs and ground-truth files created via Subgen

    Idea is to test GraphZip on synthetic graphs containing:
    cliques, cycles, paths and trees

    The synthetic graphs are created via Subgen.

    Each Subgen graph has a certain pattern embedded in it (i.e. 3-cliques) and
    the specific instances of those patterns are specified in the *.insts files
    Subgen generates.

    For each test, we check how many of the patterns from the .insts file were
    captured in the compressor dictionary.

    """

    def setUp(self):
        batch_size = 10
        dict_size = 1000
        if DEBUG:
            print("Setting up compressor with batch_size=%d, dict_size=%d ..."
                  % (batch_size, dict_size))
        self.c = Compressor(batch_size, dict_size)
        self.c.add_implicit_vertices = True  # since batch_size < file_size
        if PROFILE:
            self.pr = cProfile.Profile()
            self.pr.enable()

    def tearDown(self):
        if DEBUG:
            print("\nCompression was run on a total of %d times\n"
                  % self.c._compress_count)
        if PROFILE:
            p = Stats(self.pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()
            if(DEBUG):
                print('\n{}>>>'.format('-'*77))

    def _test_graphzip_subgen(self, fin_graphzip, fin_insts, n=None):
        """ Run compress on the Subgen file, then checks against GT """
        print('Running compression on %s...' % fin_graphzip)
        start = time.perf_counter()
        # run compression to get pattern dictionary
        self.c.compress_file(GRAPH_DIR + fin_graphzip)
        elapsed = time.perf_counter()-start
        print('Compression took:')
        print(elapsed)

        # collect y and y_hat
        gt_gs = import_insts(GRAPH_DIR + fin_insts)
        graphzip_gs = [g for (g, _, _) in self.c.P]

        # trim the pattern dictionary e.g. to match the #patterns Subdue found
        if n is not None:
            graphzip_gs = graphzip_gs[:n]
        print('Succesfully imported %d graphs from the pattern dictionary'
              % len(graphzip_gs))

        # error metric 1
        hits1, total1 = get_gt_patterns_found(gt_gs, graphzip_gs)
        print('%d/%d GT patterns in the insts file were found by GraphZip.' %
              (hits1, total1))

        # error metric 2
        hits2, total2 = get_patterns_also_in_gt(gt_gs, graphzip_gs)
        print('%d/%d patterns in the dictionary were in the insts file.' %
              (hits2, total2))

    def _test_multiple(self, fin_graphzip, fin_insts, T, n=None):
        """ Run the test multiple times to get iterative pattern growth """
        for t in range(T+1)[1:]:
            self._test_graphzip_subgen(fin_graphzip, fin_insts, n)

    def test_3CLIQ_20(self):
        print('20pc coverage:')
        self._test_multiple("%s3CLIQ/3CLIQ_1_5_20cx.graph" % SUBGEN_DIR,
                            "%s3CLIQ/3CLIQ_1_5_20c.insts" % SUBGEN_DIR,
                            1)

    def test_3CLIQ_50(self):
        print('50pc coverage:')
        self._test_multiple("%s3CLIQ/3CLIQ_1_5_50cx.graph" % SUBGEN_DIR,
                            "%s3CLIQ/3CLIQ_1_5_50c.insts" % SUBGEN_DIR,
                            1)

    def test_3CLIQ_80(self):
        print('80pc coverage:')
        self._test_multiple("%s3CLIQ/3CLIQ_1_5_80cx.graph" % SUBGEN_DIR,
                            "%s3CLIQ/3CLIQ_1_5_80c.insts" % SUBGEN_DIR,
                            1)

    def test_4PATH_20(self):
        print('20pc coverage:')
        self._test_multiple("%s4PATH/4PATH_1_5_20cx.graph" % SUBGEN_DIR,
                            "%s4PATH/4PATH_1_5_20c.insts" % SUBGEN_DIR,
                            1)

    def test_4PATH_50(self):
        print('50pc coverage:')
        self._test_multiple("%s4PATH/4PATH_1_5_50cx.graph" % SUBGEN_DIR,
                            "%s4PATH/4PATH_1_5_50c.insts" % SUBGEN_DIR,
                            1)

    def test_4PATH_80(self):
        print('80pc coverage:')
        self._test_multiple("%s4PATH/4PATH_1_5_80cx.graph" % SUBGEN_DIR,
                            "%s4PATH/4PATH_1_5_80c.insts" % SUBGEN_DIR,
                            1)

    def test_4STAR_20(self):
        print('20pc coverage:')
        self._test_multiple("%s4STAR/4STAR_1_5_20cx.graph" % SUBGEN_DIR,
                            "%s4STAR/4STAR_1_5_20c.insts" % SUBGEN_DIR,
                            1)

    def test_4STAR_50(self):
        print('50pc coverage:')
        self._test_multiple("%s4STAR/4STAR_1_5_50cx.graph" % SUBGEN_DIR,
                            "%s4STAR/4STAR_1_5_50c.insts" % SUBGEN_DIR,
                            1)

    def test_4STAR_80(self):
        print('80pc coverage:')
        self._test_multiple("%s4STAR/4STAR_1_5_80cx.graph" % SUBGEN_DIR,
                            "%s4STAR/4STAR_1_5_80c.insts" % SUBGEN_DIR,
                            1)

    def test_5PATH_20(self):
        print('20pc coverage:')
        self._test_multiple("%s5PATH/5PATH_1_5_20cx.graph" % SUBGEN_DIR,
                            "%s5PATH/5PATH_1_5_20c.insts" % SUBGEN_DIR,
                            1)

    def test_5PATH_50(self):
        print('50pc coverage:')
        self._test_multiple("%s5PATH/5PATH_1_5_50cx.graph" % SUBGEN_DIR,
                            "%s5PATH/5PATH_1_5_50c.insts" % SUBGEN_DIR,
                            1)

    def test_5PATH_80(self):
        print('80pc coverage:')
        self._test_multiple("%s5PATH/5PATH_1_5_80cx.graph" % SUBGEN_DIR,
                            "%s5PATH/5PATH_1_5_80c.insts" % SUBGEN_DIR,
                            1)

    def test_8TREE_20(self):
        print('20pc coverage:')
        self._test_multiple("%s8TREE/8TREE_1_5_20cx.graph" % SUBGEN_DIR,
                            "%s8TREE/8TREE_1_5_20c.insts" % SUBGEN_DIR,
                            1)

    def test_8TREE_50(self):
        print('50pc coverage:')
        self._test_multiple("%s8TREE/8TREE_1_5_50cx.graph" % SUBGEN_DIR,
                            "%s8TREE/8TREE_1_5_50c.insts" % SUBGEN_DIR,
                            1)

    def test_8TREE_80(self):
        print('80pc coverage:')
        self._test_multiple("%s8TREE/8TREE_1_5_80cx.graph" % SUBGEN_DIR,
                            "%s8TREE/8TREE_1_5_80c.insts" % SUBGEN_DIR,
                            1)

    def test_4CLIQ_20(self):
        print('20pc coverage:')
        self._test_multiple("%s4CLIQ/4CLIQ_1_5_20cx.graph" % SUBGEN_DIR,
                            "%s4CLIQ/4CLIQ_1_5_20c.insts" % SUBGEN_DIR,
                            1)

    def test_4CLIQ_50(self):
        print('50pc coverage:')
        self._test_multiple("%s4CLIQ/4CLIQ_1_5_50cx.graph" % SUBGEN_DIR,
                            "%s4CLIQ/4CLIQ_1_5_50c.insts" % SUBGEN_DIR,
                            1)

    def test_4CLIQ_80(self):
        print('80pc coverage:')
        self._test_multiple("%s4CLIQ/4CLIQ_1_5_80cx.graph" % SUBGEN_DIR,
                            "%s4CLIQ/4CLIQ_1_5_80c.insts" % SUBGEN_DIR,
                            1)


@unittest.skip("Non-standard test")
class TestSubdueSubgen(unittest.TestCase):
    """ Test SUBDUE on graphs and ground-truth files created via Subgen """

    def _test_subdue_subgen(self, fin_subdue, fin_insts, n=100):
        """
        Use GraphZip and Subdue on the same example graph to compare the error
        rates and runtime on each

        When comparing run-time, we only count the runtime of the compression
        part, as opposed to the overall time for the entire test (reported by
        the profiler). This means starting and stopping the clock before and
        after the Compressor.compress_file() method and the `./subdue' system
        call.

        Subdue outputs its patterns to a file in the .graph format. After Subdue
        is finished running we can parse the file into iGraph objects then
        compare with the ground-truth using the same functions.

        Iterate once (no compression) to find bottom-level structures in the
        graph
        """
        if not SUBDUE_DIR:
            pass

        # fout = "subdue_patterns_output_latest.out"
        fout = "subdue_patterns_output_{}.out".format(fin_subdue[-20:-6])

        # XXX change to subprocess.call
        # e.g. './subdue -nsubs 100 ../data/3clique.graph > example_out.txt'
        cmd = "{}subdue -nsubs {} {} > {}".format(
              SUBDUE_DIR, n, GRAPH_DIR + fin_subdue, fout)
        print(cmd)

        start = time.perf_counter()
        status = os.system(cmd)  # run cmd
        elapsed = time.perf_counter()-start
        if status:
            raise Exception("Error occured while attempting to run Subdue")
        print(elapsed)

        gt_gs = import_insts(GRAPH_DIR+fin_insts)
        subdue_gs = parse_subdue_output(fout)

        # error metric 1
        hits1, total1 = get_gt_patterns_found(gt_gs, subdue_gs)
        print('%d/%d GT patterns in the insts file were found by Subdue.' %
              (hits1, total1))

        # error metric 2
        hits2, total2 = get_patterns_also_in_gt(gt_gs, subdue_gs)
        print('%d/%d patterns found by Subdue were in the insts file.' %
              (hits2, total2))

    def test_3CLIQ_20(self):
        print('20pc coverage:')
        self._test_subdue_subgen("%s3CLIQ/3CLIQ_1_5_20cx.graph" % SUBGEN_DIR,
                                 "%s3CLIQ/3CLIQ_1_5_20c.insts" % SUBGEN_DIR)

    def test_3CLIQ_50(self):
        print('50pc coverage:')
        self._test_subdue_subgen("%s3CLIQ/3CLIQ_1_5_50cx.graph" % SUBGEN_DIR,
                                 "%s3CLIQ/3CLIQ_1_5_50c.insts" % SUBGEN_DIR)

    def test_3CLIQ_80(self):
        print('80pc coverage:')
        self._test_subdue_subgen("%s3CLIQ/3CLIQ_1_5_80cx.graph" % SUBGEN_DIR,
                                 "%s3CLIQ/3CLIQ_1_5_80c.insts" % SUBGEN_DIR)

    def test_4PATH_20(self):
        print('20pc coverage:')
        self._test_subdue_subgen("%s4PATH/4PATH_1_5_20cx.graph" % SUBGEN_DIR,
                                 "%s4PATH/4PATH_1_5_20c.insts" % SUBGEN_DIR)

    def test_4PATH_50(self):
        print('50pc coverage:')
        self._test_subdue_subgen("%s4PATH/4PATH_1_5_50cx.graph" % SUBGEN_DIR,
                                 "%s4PATH/4PATH_1_5_50c.insts" % SUBGEN_DIR)

    def test_4PATH_80(self):
        print('80pc coverage:')
        self._test_subdue_subgen("%s4PATH/4PATH_1_5_80cx.graph" % SUBGEN_DIR,
                                 "%s4PATH/4PATH_1_5_80c.insts" % SUBGEN_DIR)

    def test_4STAR_20(self):
        print('20pc coverage:')
        self._test_subdue_subgen("%s4STAR/4STAR_1_5_20cx.graph" % SUBGEN_DIR,
                                 "%s4STAR/4STAR_1_5_20c.insts" % SUBGEN_DIR)

    def test_4STAR_50(self):
        print('50pc coverage:')
        self._test_subdue_subgen("%s4STAR/4STAR_1_5_50cx.graph" % SUBGEN_DIR,
                                 "%s4STAR/4STAR_1_5_50c.insts" % SUBGEN_DIR)

    def test_4STAR_80(self):
        print('80pc coverage:')
        self._test_subdue_subgen("%s4STAR/4STAR_1_5_80cx.graph" % SUBGEN_DIR,
                                 "%s4STAR/4STAR_1_5_80c.insts" % SUBGEN_DIR)

    def test_5PATH_20(self):
        print('20pc coverage:')
        self._test_subdue_subgen("%s5PATH/5PATH_1_5_20cx.graph" % SUBGEN_DIR,
                                 "%s5PATH/5PATH_1_5_20c.insts" % SUBGEN_DIR)

    def test_5PATH_50(self):
        print('50pc coverage:')
        self._test_subdue_subgen("%s5PATH/5PATH_1_5_50cx.graph" % SUBGEN_DIR,
                                 "%s5PATH/5PATH_1_5_50c.insts" % SUBGEN_DIR)

    def test_5PATH_80(self):
        print('80pc coverage:')
        self._test_subdue_subgen("%s5PATH/5PATH_1_5_80cx.graph" % SUBGEN_DIR,
                                 "%s5PATH/5PATH_1_5_80c.insts" % SUBGEN_DIR)

    def test_8TREE_20(self):
        print('20pc coverage:')
        self._test_subdue_subgen("%s8TREE/8TREE_1_5_20cx.graph" % SUBGEN_DIR,
                                 "%s8TREE/8TREE_1_5_20c.insts" % SUBGEN_DIR)

    def test_8TREE_50(self):
        print('50pc coverage:')
        self._test_subdue_subgen("%s8TREE/8TREE_1_5_50cx.graph" % SUBGEN_DIR,
                                 "%s8TREE/8TREE_1_5_50c.insts" % SUBGEN_DIR)

    def test_8TREE_80(self):
        print('80pc coverage:')
        self._test_subdue_subgen("%s8TREE/8TREE_1_5_80cx.graph" % SUBGEN_DIR,
                                 "%s8TREE/8TREE_1_5_80c.insts" % SUBGEN_DIR)

    def test_4CLIQ_20(self):
        print('20pc coverage:')
        self._test_subdue_subgen("%s4CLIQ/4CLIQ_1_5_20cx.graph" % SUBGEN_DIR,
                                 "%s4CLIQ/4CLIQ_1_5_20c.insts" % SUBGEN_DIR)

    def test_4CLIQ_50(self):
        print('50pc coverage:')
        self._test_subdue_subgen("%s4CLIQ/4CLIQ_1_5_50cx.graph" % SUBGEN_DIR,
                                 "%s4CLIQ/4CLIQ_1_5_50c.insts" % SUBGEN_DIR)

    def test_4CLIQ_80(self):
        print('80pc coverage:')
        self._test_subdue_subgen("%s4CLIQ/4CLIQ_1_5_80cx.graph" % SUBGEN_DIR,
                                 "%s4CLIQ/4CLIQ_1_5_80c.insts" % SUBGEN_DIR)


@unittest.skip("Non-standard test")
class TestLarge(unittest.TestCase):
    """ GraphZip with larger (real-world) .graph datasets """

    def setUp(self):
        batch_size = 5
        dict_size = 50
        if DEBUG:
            print("Setting up compressor with batch_size=%d, dict_size=%d ..."
                  % (batch_size, dict_size))
        self.c = Compressor(batch_size, dict_size)
        if PROFILE:
            self.pr = cProfile.Profile()
            self.pr.enable()

    def tearDown(self):
        if DEBUG:
            print("\nCompression was run a total of %d times\n"
                  % self.c._compress_count)
            print("%d lines read" % self.c._lines_read)
            print("Dictionary trimmed %d times" % self.c._dict_trimmed)
            print("Compressor: batch_size=%d, dict_size=%d ..."
                  % (self.c.batch_size, self.c.dict_size))
        if PROFILE:
            p = Stats(self.pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()
            if(DEBUG):
                print('\n{}>>>'.format('-'*77))

    def testHetRec(self):
        times = []
        try:
            for i in range(1, 99):
                f = '../datasets/HetRec/hetrec_year_vfirst/%d.graph' % i
                start = timer()
                self.c.compress_file(f)
                end = timer()
                elapsed = end - start
                times.append((i, elapsed))
                print('\nTook %.2f seconds' % elapsed)
        finally:
            self.c.P = sorted(self.c.P, key=itemgetter(2), reverse=True)
            print('Printing top 50 patterns for reference:')
            for g, c, s in self.c.P[:49]:
                print('\ncount: %d, score: %d\n' % (c, s))
                print(g)
                print(g.vs['label'])

            # Save the dictionary, etc.
            print('Saving the latest state of GraphZip..')
            self.c.save_state('latest_HetRec_state.p')

            # Save the time measurements for plotting
            print('Saving time measurements..')
            print(times)
            with open('latest_HetRec_times.p', 'wb') as pfile:
                pickle.dump((times), pfile)

    def testHiggs(self):
        times = []
        try:
            for i in range(1, 169):
                # f = '../datasets/Twitter_Higgs/higgs_hour_vfirst/%d.g' % i
                f = '../datasets/Twitter_Higgs/higgs_hour_vfirst_unilabel/%d.g' % i
                start = timer()
                self.c.compress_file(f)
                end = timer()
                elapsed = end - start
                times.append((i, elapsed))
                print('\nTook %.2f seconds' % elapsed)
        finally:
            self.c.P = sorted(self.c.P, key=itemgetter(2), reverse=True)
            print('Printing top 50 patterns for reference:')
            for g, c, s in self.c.P[:49]:
                print('\ncount: %d, score: %d\n' % (c, s))
                print(g)
                print('Vertex labels:')
                print(g.vs['label'])
                print('Edge labels:')
                print(g.es['label'])
            # Save the dictionary, etc
            print('Saving the latest state of GraphZip..')
            self.c.save_state('latest_Higgs_state.p')
            # Save the time measurements for plotting
            print('Saving time measurements..')
            print(times)
            with open('latest_Higgs_times.p', 'wb') as pfile:
                pickle.dump((times), pfile)

    def testNBER(self):
        times = []
        try:
            for i in range(1, 301):
                f = '../datasets/NBER/cite75_99_month_clabels/%d.graph' % i
                #f = '../datasets/NBER/cite75_99_month_clabels_v0/%d.graph' % i
                # f = '../datasets/NBER/cite75_99_month_clabels_v0_vfirst/%d.graph' % i
                start = timer()
                self.c.compress_file(f)
                end = timer()
                elapsed = end - start
                times.append((i, elapsed))
                print('\nTook %d seconds' % elapsed)
        finally:
            self.c.P = sorted(self.c.P, key=itemgetter(2), reverse=True)
            for g, c, s in self.c.P[:49]:
                print('\ncount: %d, score: %d\n' % (c, s))
                print(g)
                print(g.vs['label'])
            # Save the dictionary, etc
            print('Saving the latest state of GraphZip..')
            self.c.save_state('latest_NBER_state.p')
            # Save the time measurements for plotting
            print('Saving time measurements..')
            print(times)
            with open('latest_NBER_times.p', 'wb') as pfile:
                pickle.dump((times), pfile)


def main(out=sys.stderr, verbosity=2):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(out, verbosity=verbosity).run(suite)

if __name__ == '__main__':
    with open('testing.out', 'w') as f:
        main(f)
