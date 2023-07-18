from pydrofoil import parse
from pydrofoil.parse import *
from pydrofoil.optimize import (find_decl_defs_uses, identify_replacements,
        do_replacements)

def test_find_used_vars_exprs():
    v = parse.Var("abc")
    assert v.find_used_vars() == {"abc"}
    n = parse.Number(123)
    assert n.find_used_vars() == set()
    f = parse.FieldAccess(v, 'abc')
    assert v.find_used_vars() == {"abc"}
    c = parse.Cast(v, 'abc')
    assert c.find_used_vars() == {"abc"}
    r = parse.Cast(v, 'abc')
    assert r.find_used_vars() == {"abc"}

    v2 = parse.Var("def")
    s = parse.StructConstruction("S", ['x', 'y'], [v, v2])
    assert s.find_used_vars() == {"abc", "def"}

def test_find_used_vars_statements():
    v = parse.Var("abc")
    l = parse.LocalVarDeclaration("x", "dummy", v)
    assert l.find_used_vars() == {'abc'}
    
    a = parse.Assignment("x", v)
    assert l.find_used_vars() == {'abc'}

    v2 = parse.Var("def")
    s = parse.Operation("x", "dummyop", [v, v2])
    assert s.find_used_vars() == {"abc", "def"}

    v2 = parse.Var("def")
    s = parse.StructElementAssignment(v, "field", v2)
    assert s.find_used_vars() == {"abc", "def"}

def test_find_used_vars_condition():
    v = parse.Var("abc")
    v2 = parse.Var("def")
    l = parse.ExprCondition(v)
    assert l.find_used_vars() == {'abc'}
    
    s = parse.Comparison("@eq", [v, v2])
    assert s.find_used_vars() == {"abc", "def"}

    u = parse.UnionVariantCheck("abc", "X")
    assert u.find_used_vars() == {"abc"}

# __________________________________________________

vector_subrange_example = [
LocalVarDeclaration(name='bv32', typ=NamedType('%bv32'), value=None),
Assignment(result='bv32', value=Var(name='zargz3')),
LocalVarDeclaration(name='subrange_result_bv7', typ=NamedType('%bv7'), value=None),
LocalVarDeclaration(name='num6', typ=NamedType('%i'), value=None),
Operation(args=[Number(number=6)], name='zz5i64zDzKz5i', result='num6'),
LocalVarDeclaration(name='num0', typ=NamedType('%i'), value=None),
Operation(args=[Number(number=0)], name='zz5i64zDzKz5i', result='num0'),
LocalVarDeclaration(name='bvusedonce', typ=NamedType('%bv'), value=None),
Assignment(result='bvusedonce', value=Var(name='bv32')),
LocalVarDeclaration(name='subrange_result', typ=NamedType('%bv'), value=None),
Operation(args=[Var(name='bvusedonce'), Var(name='num6'), Var(name='num0')], name='zsubrange_bits', result='subrange_result'),
Assignment(result='subrange_result_bv7', value=Var(name='subrange_result')),
LocalVarDeclaration(name='cond', typ=NamedType('%bool'), value=None),
Operation(args=[Var(name='subrange_result_bv7')], name='zencdec_uop_backwards_matches', result='cond'),
ConditionalJump(condition=Comparison(args=[Var(name='cond')], operation='@not'), target=17),
End()
    ]

def test_find_defs_uses():
    block = vector_subrange_example
    decls, defs, uses = find_decl_defs_uses([block])
    assert uses['bv32'] == [(block, 8)]
    assert uses['subrange_result_bv7'] == [(block, 13)]
    assert defs['num6'] == [(block, 4)]
    assert defs['subrange_result_bv7'] == [(block, 11)]
    for var, uses in uses.iteritems():
        for bl, index in uses:
            assert bl is block
            assert var in block[index].find_used_vars()
            for i, op in enumerate(block):
                if i != index:
                    assert var not in block[i].find_used_vars()


def test_identify_replacements():
    replacements = identify_replacements([vector_subrange_example])
    assert replacements['bvusedonce'] == (vector_subrange_example, 7, 8, 10)

def test_do_replacements():
    block = vector_subrange_example[:]
    replacements = identify_replacements([block])
    do_replacements(replacements)
    assert block[2] == ConditionalJump(
        condition=Comparison(
            args=[OperationExpr(
                    args=[CastExpr(expr=OperationExpr(
                        args=[
                            CastExpr(expr=Var(name='bv32'), typ=NamedType('%bv')),
                            OperationExpr(args=[Number(number=6)], name='zz5i64zDzKz5i'),
                            OperationExpr(args=[Number(number=0)], name='zz5i64zDzKz5i')],
                        name='zsubrange_bits'), typ=NamedType('%bv7'))],
                    name='zencdec_uop_backwards_matches')],
            operation='@not'),
        sourcepos=None,
        target=17)
