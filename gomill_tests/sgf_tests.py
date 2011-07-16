"""Tests for sgf.py."""

from textwrap import dedent

from gomill_tests import gomill_test_support

from gomill import ascii_boards
from gomill import sgf

def make_tests(suite):
    suite.addTests(gomill_test_support.make_simple_tests(globals()))


def test_sgf_game_from_string(tc):
    g1 = sgf.sgf_game_from_string("(;)")
    tc.assertEqual(g1.get_size(), 19)
    tc.assertRaisesRegexp(ValueError, "unexpected end of SGF data",
                          sgf.sgf_game_from_string, "(;SZ[9]")
    g2 = sgf.sgf_game_from_string("(;SZ[9])")
    tc.assertEqual(g2.get_size(), 9)
    tc.assertRaisesRegexp(ValueError, "bad SZ property: a",
                          sgf.sgf_game_from_string, "(;SZ[a])")
    tc.assertRaisesRegexp(ValueError, "size out of range: 27",
                          sgf.sgf_game_from_string, "(;SZ[27])")

def test_new_sgf_game(tc):
    g1 = sgf.Sgf_game(9)
    tc.assertEqual(g1.get_size(), 9)
    root = g1.get_root()
    tc.assertEqual(root.get_raw('FF'), '4')
    tc.assertEqual(root.get_raw('GM'), '1')
    tc.assertEqual(root.get_raw('SZ'), '9')
    tc.assertEqual(root.children(), [])
    tc.assertEqual(root.parent, None)
    tc.assertEqual(root.owner, g1)

def test_node(tc):
    sgf_game = sgf.sgf_game_from_string(
        r"(;KM[6.5]C[sample\: comment]AB[ai][bh][ee]AE[];B[dg])")
    node0 = sgf_game.get_root()
    node1 = list(sgf_game.main_sequence_iter())[1]
    tc.assertIs(node0.has_property('KM'), True)
    tc.assertIs(node0.has_property('XX'), False)
    tc.assertIs(node1.has_property('KM'), False)
    tc.assertEqual(node0.get_raw('C'), r"sample\: comment")
    tc.assertEqual(node0.get_raw('AB'), "ai")
    tc.assertEqual(node0.get_raw('AE'), "")
    tc.assertRaises(KeyError, node0.get_raw, 'XX')
    tc.assertEqual(node0.get_raw_list('KM'), ['6.5'])
    tc.assertEqual(node0.get_raw_list('AB'), ['ai', 'bh', 'ee'])
    tc.assertEqual(node0.get_raw_list('AE'), [''])
    tc.assertRaises(KeyError, node0.get_raw_list, 'XX')
    tc.assertRaises(KeyError, node0.get_raw, 'XX')

def test_property_combination(tc):
    sgf_game = sgf.sgf_game_from_string("(;XX[1]YY[2]XX[3]YY[4])")
    node0 = sgf_game.get_root()
    tc.assertEqual(node0.get_raw_list("XX"), ["1", "3"])
    tc.assertEqual(node0.get_raw_list("YY"), ["2", "4"])

def test_node_get(tc):
    sgf_game = sgf.sgf_game_from_string(dedent(r"""
    (;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]PB[Black engine]
    PL[B]PW[White engine]RE[W+R]SZ[9]AB[ai][bh][ee]AW[fd][gc]AE[]BM[2]VW[]
    EV[Test
    event]
    C[123:\)
    abc]
    YY[none
    sense]
    ;B[dg]KO[]AR[ab:cd][de:fg]FG[515:first move]
    LB[ac:lbl][bc:lbl2])
    """))
    root = sgf_game.get_root()
    node1 = list(sgf_game.main_sequence_iter())[1]
    tc.assertRaises(KeyError, root.get, 'XX')
    tc.assertEqual(root.get('C'), "123:)\nabc")          # Text
    tc.assertEqual(root.get('EV'), "Test event")         # Simpletext
    tc.assertEqual(root.get('BM'), 2)                    # Double
    tc.assertEqual(root.get('YY'), "none\nsense")        # unknown (Text)
    tc.assertIs(node1.get('KO'), True)                   # None
    tc.assertEqual(root.get('KM'), 7.5)                  # Real
    tc.assertEqual(root.get('GM'), 1)                    # Number
    tc.assertEqual(root.get('PL'), 'b')                  # Color
    tc.assertEqual(node1.get('B'), (2, 3))               # Point
    tc.assertEqual(root.get('AB'),
                   set([(0, 0), (1, 1), (4, 4)]))        # List of Point
    tc.assertEqual(root.get('VW'), set())                # Empty elist
    tc.assertEqual(root.get('AP'), ("testsuite", "0"))   # Application
    tc.assertEqual(node1.get('AR'),
                   [((7, 0), (5, 2)), ((4, 3), (2, 5))]) # Arrow
    tc.assertEqual(node1.get('FG'), (515, "first move")) # Figure
    tc.assertEqual(node1.get('LB'),
                   [((6, 0), "lbl"), ((6, 1), "lbl2")])  # Label
    # Check we (leniently) treat lists like elists on read
    tc.assertEqual(root.get('AE'), set())

def test_text_values(tc):
    def check(s):
        sgf_game = sgf.sgf_game_from_string(s)
        return sgf_game.get_root().get("C")
    # Round-trip check of Text values through tokeniser, parser, and
    # text_value().
    tc.assertEqual(check(r"(;C[abc]KO[])"), r"abc")
    tc.assertEqual(check(r"(;C[a\\bc]KO[])"), r"a\bc")
    tc.assertEqual(check(r"(;C[a\\bc\]KO[])"), r"a\bc]KO[")
    tc.assertEqual(check(r"(;C[abc\\]KO[])"), r"abc" + "\\")
    tc.assertEqual(check(r"(;C[abc\\\]KO[])"), r"abc\]KO[")
    tc.assertEqual(check(r"(;C[abc\\\\]KO[])"), r"abc" + "\\\\")
    tc.assertEqual(check(r"(;C[abc\\\\\]KO[])"), r"abc\\]KO[")
    tc.assertEqual(check(r"(;C[xxx :\) yyy]KO[])"), r"xxx :) yyy")
    tc.assertEqual(check("(;C[ab\\\nc])"), "abc")
    tc.assertEqual(check("(;C[ab\nc])"), "ab\nc")


SAMPLE_SGF = """\
(;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]PB[Black engine]
PL[B]PW[White engine]RE[W+R]SZ[9]AB[ai][bh][ee]AW[fd][gc];B[dg];W[ef]C[comment
on two lines];B[];W[tt]C[Final comment])
"""

SAMPLE_SGF_VAR = """\
(;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]PB[Black engine]
PL[B]PW[White engine]RE[W+R]SZ[9]AB[ai][bh][ee]AW[fd][gc]VW[]
;B[dg]
;W[ef]C[comment
on two lines]
;B[]
;C[Nonfinal comment]VW[aa:bb]
(;B[ia];W[ib];B[ic])
(;B[ib];W[ic]
  (;B[id])
  (;B[ie])
))
"""

def test_node_string(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF)
    node = sgf_game.get_root()
    tc.assertMultiLineEqual(str(node), dedent("""\
    AB[ai][bh][ee]
    AP[testsuite:0]
    AW[fd][gc]
    CA[utf-8]
    DT[2009-06-06]
    FF[4]
    GM[1]
    KM[7.5]
    PB[Black engine]
    PL[B]
    PW[White engine]
    RE[W+R]
    SZ[9]
    """))

def test_node_get_move(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF)
    nodes = list(sgf_game.main_sequence_iter())
    tc.assertEqual(nodes[0].get_move(), (None, None))
    tc.assertEqual(nodes[1].get_move(), ('b', (2, 3)))
    tc.assertEqual(nodes[2].get_move(), ('w', (3, 4)))
    tc.assertEqual(nodes[3].get_move(), ('b', None))
    tc.assertEqual(nodes[4].get_move(), ('w', None))

def test_node_setup_commands(tc):
    sgf_game = sgf.sgf_game_from_string(
        r"(;KM[6.5]SZ[9]C[sample\: comment]AB[ai][bh][ee]AE[bb];B[dg])")
    node0 = sgf_game.get_root()
    node1 = list(sgf_game.main_sequence_iter())[1]
    tc.assertIs(node0.has_setup_commands(), True)
    tc.assertIs(node1.has_setup_commands(), False)
    tc.assertEqual(node0.get_setup_commands(),
                   (set([(0, 0), (1, 1), (4, 4)]), set(), set([(7, 1)])))
    tc.assertEqual(node1.get_setup_commands(),
                   (set(), set(), set()))

def test_sgf_game(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    nodes = list(sgf_game.main_sequence_iter())
    tc.assertEqual(sgf_game.get_size(), 9)
    tc.assertEqual(sgf_game.get_komi(), 7.5)
    tc.assertIs(sgf_game.get_handicap(), None)
    tc.assertEqual(sgf_game.get_player('b'), "Black engine")
    tc.assertEqual(sgf_game.get_player('w'), "White engine")
    tc.assertEqual(sgf_game.get_winner(), 'w')
    tc.assertEqual(nodes[2].get('C'), "comment\non two lines")
    tc.assertEqual(nodes[4].get('C'), "Nonfinal comment")


_setup_expected = """\
9  .  .  .  .  .  .  .  .  .
8  .  .  .  .  .  .  .  .  .
7  .  .  .  .  .  .  o  .  .
6  .  .  .  .  .  o  .  .  .
5  .  .  .  .  #  .  .  .  .
4  .  .  .  .  .  .  .  .  .
3  .  .  .  .  .  .  .  .  .
2  .  #  .  .  .  .  .  .  .
1  #  .  .  .  .  .  .  .  .
   A  B  C  D  E  F  G  H  J\
"""

def test_tree_view(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    root = sgf_game.get_root()
    tc.assertIsInstance(root, sgf.Tree_node)
    tc.assertIs(root.parent, None)
    tc.assertIs(root.owner, sgf_game)
    tc.assertEqual(len(root.children()), 1)
    tc.assertEqual(len(root), 1)
    tc.assertEqual(root.children()[0].get_raw('B'), "dg")
    tc.assertIsNot(root.children(), root.children())
    tc.assertTrue(root)

    branchnode = root[0][0][0][0]
    tc.assertIsInstance(branchnode, sgf.Tree_node)
    tc.assertIs(branchnode.parent, root[0][0][0])
    tc.assertIs(branchnode.owner, sgf_game)
    tc.assertEqual(len(branchnode), 2)
    tc.assertIs(branchnode.children()[0], branchnode[0])
    tc.assertIs(branchnode.children()[1], branchnode[1])
    tc.assertIsNot(branchnode.children(), branchnode.children())
    tc.assertIs(branchnode[1], branchnode[-1])
    tc.assertEqual(branchnode[:1], [branchnode[0]])
    tc.assertEqual([node for node in branchnode], branchnode.children())
    with tc.assertRaises(IndexError):
        branchnode[2]
    tc.assertEqual(branchnode[0].get_raw('B'), "ia")
    tc.assertEqual(branchnode[1].get_raw('B'), "ib")

    tc.assertEqual(len(branchnode[1][0]), 2)

    leaf = branchnode[1][0][1]
    tc.assertIs(leaf.parent, branchnode[1][0])
    tc.assertEqual(len(leaf), 0)
    tc.assertFalse(leaf)

    # check nothing breaks when first retrieval is by index
    game2 = sgf.sgf_game_from_string(SAMPLE_SGF)
    root2 = game2.get_root()
    tc.assertIs(root2[0], root2.children()[0])

def test_tree_mutation(tc):
    sgf_game = sgf.Sgf_game(9)
    root = sgf_game.get_root()
    n1 = root.new_child()
    n1.set("N", "n1")
    n2 = root.new_child()
    n2.set("N", "n2")
    n3 = n1.new_child()
    n3.set("N", "n3")
    tc.assertEqual(sgf.serialise_sgf_game(sgf_game),
                   "(;CA[utf-8]FF[4]GM[1]SZ[9](;N[n1];N[n3])(;N[n2]))\n")
    tc.assertEqual(
        [node.get_raw_property_map() for node in sgf_game.main_sequence_iter()],
        [node.get_raw_property_map() for node in root, root[0], n3])

def test_tree_mutation_from_parsed_game(tc):
    sgf_game = sgf.sgf_game_from_string("(;SZ[9](;N[n1];N[n3])(;N[n2]))")
    root = sgf_game.get_root()
    n4 = root.new_child()
    n4.set("N", "n4")
    n3 = root[0][0]
    tc.assertEqual(n3.get("N"), "n3")
    n5 = n3.new_child()
    n5.set("N", "n5")
    tc.assertEqual(sgf.serialise_sgf_game(sgf_game),
                   "(;SZ[9](;N[n1];N[n3];N[n5])(;N[n2])(;N[n4]))\n")
    # FIXME: find a better test than property-map identity?
    tc.assertEqual(
        [node.get_raw_property_map() for node in sgf_game.main_sequence_iter()],
        [node.get_raw_property_map() for node in root, root[0], n3, n5])

def test_get_sequence_above(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    root = sgf_game.get_root()
    branchnode = root[0][0][0][0]
    leaf = branchnode[1][0][1]
    tc.assertEqual(sgf_game.get_sequence_above(root), [])

    tc.assertEqual(sgf_game.get_sequence_above(branchnode),
                   [root, root[0], root[0][0], root[0][0][0]])

    tc.assertEqual(sgf_game.get_sequence_above(leaf),
                   [root, root[0], root[0][0], root[0][0][0],
                    branchnode, branchnode[1], branchnode[1][0]])

    sgf_game2 = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    tc.assertRaisesRegexp(ValueError, "node doesn't belong to this game",
                          sgf_game2.get_sequence_above, leaf)

def test_get_main_sequence_below(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    root = sgf_game.get_root()
    branchnode = root[0][0][0][0]
    leaf = branchnode[1][0][1]
    tc.assertEqual(sgf_game.get_main_sequence_below(leaf), [])

    tc.assertEqual(sgf_game.get_main_sequence_below(branchnode),
                   [branchnode[0], branchnode[0][0], branchnode[0][0][0]])

    tc.assertEqual(sgf_game.get_main_sequence_below(root),
                   [root[0], root[0][0], root[0][0][0], branchnode,
                    branchnode[0], branchnode[0][0], branchnode[0][0][0]])

    sgf_game2 = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    tc.assertRaisesRegexp(ValueError, "node doesn't belong to this game",
                          sgf_game2.get_main_sequence_below, branchnode)

def test_main_sequence(tc):
    # FIXME: find a better test than property-map identity?
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    root = sgf_game.get_root()

    nodes = list(sgf_game.main_sequence_iter())
    tc.assertEqual(len(nodes), 8)
    tc.assertIs(root.get_raw_property_map(),
                nodes[0].get_raw_property_map())
    with tc.assertRaises(AttributeError):
        nodes[1].parent

    tree_nodes = sgf_game.get_main_sequence()
    tc.assertEqual(len(tree_nodes), 8)
    tc.assertIs(root.get_raw_property_map(),
                tree_nodes[0].get_raw_property_map())
    tc.assertIs(tree_nodes[0], root)
    tc.assertIs(tree_nodes[2].parent, tree_nodes[1])

    tree_node = root
    for node in nodes:
        tc.assertIs(tree_node.get_raw_property_map(),
                    node.get_raw_property_map())
        if tree_node:
            tree_node = tree_node[0]

def test_get_setup_and_moves(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF)
    board, moves = sgf.get_setup_and_moves(sgf_game)
    tc.assertDiagramEqual(ascii_boards.render_board(board), _setup_expected)
    tc.assertEqual(moves,
                   [('b', (2, 3)), ('w', (3, 4)), ('b', None), ('w', None)])

def test_find(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    root = sgf_game.get_root()
    branchnode = root[0][0][0][0]
    leaf = branchnode[1][0][1]

    tc.assertEqual(root.get("VW"), set())
    tc.assertIs(root.find("VW"), root)
    tc.assertRaises(KeyError, root[0].get, "VW")
    tc.assertEqual(root[0].find_property("VW"), set())
    tc.assertIs(root[0].find("VW"), root)

    tc.assertEqual(branchnode.get("VW"),
                   set([(7, 0), (7, 1), (8, 0), (8, 1)]))
    tc.assertIs(branchnode.find("VW"), branchnode)
    tc.assertEqual(branchnode.find_property("VW"),
                   set([(7, 0), (7, 1), (8, 0), (8, 1)]))

    tc.assertRaises(KeyError, leaf.get, "VW")
    tc.assertIs(leaf.find("VW"), branchnode)
    tc.assertEqual(leaf.find_property("VW"),
                   set([(7, 0), (7, 1), (8, 0), (8, 1)]))

    tc.assertIs(leaf.find("XX"), None)
    tc.assertRaises(KeyError, leaf.find_property, "XX")

def test_node_set_raw(tc):
    sgf_game = sgf.sgf_game_from_string(dedent(r"""
    (;AP[testsuite:0]CA[utf-8]DT[2009-06-06]FF[4]GM[1]KM[7.5]
    PB[Black engine]PW[White engine]RE[W+R]SZ[9]
    AB[ai][bh][ee]AW[fd][gc]BM[2]VW[]
    PL[B]
    C[123abc]
    ;B[dg]C[first move])
    """))
    root = sgf_game.get_root()
    tc.assertEqual(root.get_raw('RE'), "W+R")
    root.set_raw('RE', "W+2.5")
    tc.assertEqual(root.get_raw('RE'), "W+2.5")
    tc.assertRaises(KeyError, root.get_raw, 'XX')
    root.set_raw('XX', "xyz")
    tc.assertEqual(root.get_raw('XX'), "xyz")

    root.set_raw_list('XX', ("abc", "def"))
    tc.assertEqual(root.get_raw('XX'), "abc")
    tc.assertEqual(root.get_raw_list('XX'), ["abc", "def"])

    tc.assertRaisesRegexp(ValueError, "empty property list",
                          root.set_raw_list, 'B', [])

    values = ["123", "456"]
    root.set_raw_list('YY', values)
    tc.assertEqual(root.get_raw_list('YY'), ["123", "456"])
    values.append("789")
    tc.assertEqual(root.get_raw_list('YY'), ["123", "456"])

    tc.assertRaisesRegexp(ValueError, "ill-formed property identifier",
                          root.set_raw, 'Black', "aa")
    tc.assertRaisesRegexp(ValueError, "ill-formed property identifier",
                          root.set_raw_list, 'Black', ["aa"])

    root.set_raw('C', "foo\\]bar")
    tc.assertEqual(root.get_raw('C'), "foo\\]bar")
    root.set_raw('C', "abc\\\\")
    tc.assertEqual(root.get_raw('C'), "abc\\\\")
    tc.assertRaisesRegexp(ValueError, "ill-formed raw property value",
                          root.set_raw, 'C', "foo]bar")
    tc.assertRaisesRegexp(ValueError, "ill-formed raw property value",
                          root.set_raw, 'C', "abc\\")
    tc.assertRaisesRegexp(ValueError, "ill-formed raw property value",
                          root.set_raw_list, 'C', ["abc", "de]f"])

    root.set_raw('C', "foo\\]bar\\\nbaz")
    tc.assertEqual(root.get('C'), "foo]barbaz")


def test_node_aliasing(tc):
    # Check that node objects retrieved by different means use the same
    # property map.

    sgf_game = sgf.sgf_game_from_string(dedent(r"""
    (;C[root];C[node 1])
    """))
    root = sgf_game.get_root()
    tree_node = root[0]
    plain_node = list(sgf_game.main_sequence_iter())[1]
    tc.assertIsNot(tree_node, plain_node)
    tc.assertIs(tree_node.__class__, sgf.Tree_node)
    tc.assertIs(plain_node.__class__, sgf.Node)

    tc.assertEqual(tree_node.get_raw('C'), "node 1")
    tree_node.set_raw('C', r"test\value")
    tc.assertEqual(tree_node.get_raw('C'), r"test\value")
    tc.assertEqual(plain_node.get_raw('C'), r"test\value")

    plain_node.set_raw_list('XX', ["1", "2", "3"])
    tc.assertEqual(tree_node.get_raw_list('XX'), ["1", "2", "3"])

def test_node_set(tc):
    sgf_game = sgf.sgf_game_from_string("(;FF[4]GM[1]SZ[9])")
    root = sgf_game.get_root()
    root.set("KO", True)
    root.set("KM", 0.5)
    root.set('DD', [(3, 4), (5, 6)])
    root.set('AB', set([(0, 0), (1, 1), (4, 4)]))
    root.set('TW', set())
    root.set('XX', "nonsense [none]sense more n\\onsens\\e")

    tc.assertEqual(sgf.serialise_sgf_game(sgf_game), dedent("""\
    (;AB[ai][bh][ee]DD[ef][gd]FF[4]GM[1]KM[0.5]KO[]SZ[9]TW[]
    XX[nonsense [none\\]sense more n\\\\onsens\\\\e])
    """))

def test_node_unset(tc):
    sgf_game = sgf.sgf_game_from_string("(;FF[4]GM[1]SZ[9]HA[3])")
    root = sgf_game.get_root()
    tc.assertEqual(root.get('HA'), 3)
    root.unset('HA')
    tc.assertRaises(KeyError, root.unset, 'PL')
    tc.assertEqual(sgf.serialise_sgf_game(sgf_game),
                   "(;FF[4]GM[1]SZ[9])\n")

def test_serialiser_round_trip(tc):
    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    serialised = sgf.serialise_sgf_game(sgf_game)
    tc.assertEqual(serialised, dedent("""\
    (;AB[ai][bh][ee]AP[testsuite:0]AW[fd][gc]CA[utf-8]DT[2009-06-06]FF[4]GM[1]
    KM[7.5]PB[Black engine]PL[B]PW[White engine]RE[W+R]SZ[9]VW[];B[dg];
    C[comment
    on two lines]W[ef];B[];C[Nonfinal comment]VW[aa:bb](;B[ia];W[ib];
    B[ic])(;B[ib];W[ic](;B[id])(;B[ie])))
    """))
    sgf_game2 = sgf.sgf_game_from_string(serialised)
    tc.assertEqual(map(str, sgf_game.get_main_sequence()),
                   map(str, sgf_game2.get_main_sequence()))


# FIXME: these belong in a different test module?

def test_serialise_game_tree(tc):
    from gomill import sgf_parser
    from gomill import sgf_serialiser
    serialised = ("(;AB[aa][ab][ac]C[comment];W[ab];C[];C[]"
                  "(;B[bc])(;B[bd];W[ca](;B[da])(;B[db];\n"
                  "W[ea])))\n")
    parsed_game = sgf_parser.parse_sgf_game(serialised)
    tc.assertEqual(sgf_serialiser.serialise_game_tree(parsed_game), serialised)

def test_make_serialisable_tree(tc):
    from gomill import sgf_serialiser

    def shapetree(game_tree):
        return (
            len(game_tree.sequence),
            [shapetree(pg) for pg in game_tree.children])

    sgf_game = sgf.sgf_game_from_string(SAMPLE_SGF_VAR)
    game_tree = sgf_serialiser.make_serialisable_tree(
        sgf_game.get_root(), lambda node:node, sgf.Node.get_raw_property_map)
    tc.assertEqual(shapetree(game_tree),
                   (5, [(3, []), (2, [(1, []), (1, [])])]))

