from pydrofoil import parse, makecode, types, supportcode
from collections import defaultdict



class CollectSourceVisitor(parse.Visitor):
    def __init__(self):
        self.seen = set()

    def default_visit(self, ast):
        sourcepos = getattr(ast, "sourcepos", None)
        sourcepos = self._parse(sourcepos)
        if sourcepos:
            self.seen.add(sourcepos)
        for key, value in ast.__dict__.items():
            if isinstance(value, parse.BaseAst):
                self.visit(value)
            elif (
                isinstance(value, list)
                and value
                and isinstance(value[0], parse.BaseAst)
            ):
                for i, item in enumerate(value):
                    self.visit(item)

    def _parse(self, sourcepos):
        if sourcepos is None:
            return None
        sourcepos = sourcepos.lstrip("`")
        l = sourcepos.split(" ", 1)
        if len(l) == 1:
            return None
        filenum, rest = l
        from_, to = rest.split("-", 1)
        fromline, frompos = from_.split(":", 1)
        toline, topos = to.split(":", 1)
        return int(filenum), int(fromline), int(frompos), int(toline), int(topos)


def _get_successors(block):
    result = set()
    for op in block:
        if not hasattr(op, "target"):
            continue
        result.add(op.target)
    return result


def compute_predecessors(G):
    result = defaultdict(list)
    for num, succs in G.iteritems():
        for succ in succs:
            result[succ].append(num)
        result[num].append(num)
    return result


def _compute_dominators(G, start=0):
    preds = compute_predecessors(G)
    # initialize
    dominators = {}
    for node in G:
        dominators[node] = set(G)
    dominators[start] = {start}

    # fixpoint
    changed = True
    while changed:
        changed = False
        for node in G:
            if node == start:
                continue
            dom = set(G).intersection(*[dominators[x] for x in preds[node]])
            dom.add(node)
            if dom != dominators[node]:
                changed = True
                dominators[node] = dom
    return dominators


def immediate_dominators(G, start=0):
    if start not in G:
        return {}
    res = {}
    dominators = _compute_dominators(G, start)
    for node in G:
        if node == start:
            continue
        doms = dominators[node]
        for candidate in doms:
            if candidate == node:
                continue
            for otherdom in doms:
                if otherdom == node or otherdom == candidate:
                    continue
                if candidate in dominators[otherdom]:
                    break
            else:
                break
        res[node] = candidate
    return res

def _extract_graph(blocks):
    return {num: _get_successors(block) for (num, block) in blocks.iteritems()}

def immediate_dominators_blocks(blocks):
    G = _extract_graph(blocks)
    return immediate_dominators(G)

def bfs_graph(G, start=0):
    from collections import deque
    todo = deque([start])
    seen = set()
    res = []
    while todo:
        node = todo.popleft()
        if node in seen:
            continue
        seen.add(node)
        todo.extend(G[node])
        res.append(node)
    return res

def bfs_edges(G, start=0):
    from collections import deque
    todo = deque([start])
    seen = set()
    res = []
    while todo:
        node = todo.popleft()
        if node in seen:
            continue
        seen.add(node)
        successors = G[node]
        todo.extend(successors)
        for succ in successors:
            res.append((node, succ))
    return res

def view_blocks(blocks):
    from rpython.translator.tool.make_dot import DotGen
    from dotviewer import graphclient
    import pytest
    dotgen = DotGen('G')
    G = {num: _get_successors(block) for (num, block) in blocks.iteritems()}
    idom = immediate_dominators(G)
    for num, block in blocks.iteritems():
        label = [str(num)] + [str(op)[:100] for op in block]
        dotgen.emit_node(str(num), label="\n".join(label), shape="box")

    for start, succs in G.iteritems():
        for finish in succs:
            color = "green"
            dotgen.emit_edge(str(start), str(finish), color=color)
    for finish, start in idom.iteritems():
        color = "red"
        dotgen.emit_edge(str(start), str(finish), color=color)

    p = pytest.ensuretemp("pyparser").join("temp.dot")
    p.write(dotgen.generate(target=None))
    graphclient.display_dot_file(str(p))


# graph splitting

class CantSplitError(Exception):
    pass

def split_graph(blocks, min_size=6, start_node=0):
    G = _extract_graph(blocks)
    preds = compute_predecessors(G)
    # split graph, starting from exit edges (ie an edge going to a block
    # ending with End)
    graph1 = {}
    for source, target in bfs_edges(G, start_node):
        if not isinstance(blocks[target][-1], parse.End):
            continue
        # approach: from the edge going to the 'End' node, extend by adding
        # predecessors up to fixpoint
        graph1[target] = blocks[target]
        todo = [source]
        while todo:
            node = todo.pop()
            if node in graph1:
                continue
            graph1[node] = blocks[node]
            todo.extend(preds[node])
        # add all end nodes that are reachable from the nodes in graph1.
        # also compute nodes where we need to transfer from graph1 to graph2
        transfer_nodes = set()
        for node in list(graph1):
            for succ in G[node]:
                if succ in graph1:
                    continue
                block = blocks[succ]
                if isinstance(block[-1], parse.FunctionEndingStatement):
                    graph1[succ] = block
                else:
                    transfer_nodes.add(succ)
        # try to remove some transfer nodes, if they are themselves only a
        # single block away from an end block (happens with exceptions)
        for node in list(transfer_nodes):
            successors = G[node]
            if len(successors) > 1:
                continue
            succ, = successors
            block = blocks[succ]
            if not isinstance(block[-1], parse.FunctionEndingStatement):
                continue
            graph1[node] = blocks[node]
            graph1[succ] = block
            transfer_nodes.remove(node)

        # if we only have a single transfer_node left, we have a potential
        # split
        if len(transfer_nodes) == 1:
            if len(graph1) > min_size:
                break
        if len(graph1) == len(blocks):
            # didn't manage to split
            raise CantSplitError
    else:
        raise CantSplitError
    # compute graph2
    graph2 = {}
    for node in G:
        if node not in graph1:
            graph2[node] = blocks[node]
    # add reachable end nodes
    for node in list(graph2):
        for succ in G[node]:
            block = blocks[succ]
            if isinstance(block[-1], parse.FunctionEndingStatement):
                graph2[succ] = block
    # consistency check:
    for num, block in blocks.iteritems():
        assert num in graph1 or num in graph2
        if num in graph1 and num in graph2:
            assert isinstance(blocks[num][-1], parse.FunctionEndingStatement)
    transferpc, = transfer_nodes
    assert transferpc not in graph1
    assert transferpc in graph2
    return graph1, graph2, transferpc
