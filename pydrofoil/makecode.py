from rpython.tool.pairtype import pair

from pydrofoil import parse, types, binaryop
from contextlib import contextmanager

class NameInfo(object):
    def __init__(self, pyname, typ, ast):
        self.pyname = pyname
        self.typ = typ
        self.ast = ast

    def __repr__(self):
        return "NameInfo(%r, %r, %r)" % (self.pyname, self.typ, self.ast)


class Codegen(object):
    def __init__(self):
        self.declarations = []
        self.runtimeinit = []
        self.code = []
        self.level = 0
        self.last_enum = 0
        self.globalnames = {}
        self.namedtypes = {}
        self.declarationcache = {}
        self.gensym = {} # prefix -> number
        self.localnames = None
        self.add_global("false", "False", types.Bool())
        self.add_global("true", "True", types.Bool())
        self.add_global("bitzero", "rarithmetic.r_uint(0)", types.Bit())
        self.add_global("bitone", "rarithmetic.r_uint(1)", types.Bit())
        self.add_global("$zinternal_vector_init", "supportcode.vector_init")
        self.add_global("$zinternal_vector_update", "supportcode.vector_update")
        self.add_global("have_exception", "xxx")
        self.declared_types = set()

    def add_global(self, name, pyname, typ=None, ast=None):
        assert isinstance(typ, types.Type) or typ is None
        assert name not in self.globalnames
        self.globalnames[name] = NameInfo(pyname, typ, ast)

    def add_named_type(self, name, pyname, typ, ast):
        assert isinstance(typ, types.Type)
        assert name not in self.namedtypes
        self.namedtypes[name] = NameInfo(pyname, typ, ast)

    def get_named_type(self, name):
        return self.namedtypes[name].typ

    def update_global_pyname(self, name, pyname):
        self.globalnames[name].pyname = pyname

    def add_local(self, name, pyname, typ, ast):
        assert isinstance(typ, types.Type)
        self.localnames[name] = NameInfo(pyname, typ, ast)

    def getname(self, name):
        if name not in self.localnames:
            return self.globalnames[name].pyname
        return name

    def getinfo(self, name):
        if name in self.localnames:
            return self.localnames[name]
        else:
            return self.globalnames[name]

    def gettarget(self, name):
        return self.getinfo(name).pyname

    def gettyp(self, name):
        return self.getinfo(name).typ

    @contextmanager
    def enter_scope(self, ast):
        old_localnames = self.localnames
        self.localnames = {}
        yield
        ast.localnames = self.localnames
        self.localnames = old_localnames

    @contextmanager
    def emit_indent(self, line):
        self.emit(line)
        self.level += 1
        yield
        self.level -= 1

    @contextmanager
    def emit_code_type(self, attr):
        oldlevel = self.level
        self.level = 0
        oldcode = self.code
        self.code = getattr(self, attr)
        yield
        assert self.level == 0
        self.code = oldcode
        self.level = oldlevel

    def emit(self, line=''):
        if not line.strip():
            self.code.append('')
        else:
            self.code.append("    " * self.level + line)

    def emit_declaration(self, line):
        self.declarations.append(line)

    @contextmanager
    def cached_declaration(self, key, nameprefix):
        tup = key, nameprefix
        if tup in self.declarationcache:
            self.dummy = []
            with self.emit_code_type("dummy"):
                yield self.declarationcache[tup]
        else:
            num = self.gensym.get(nameprefix, 0) + 1
            self.gensym[nameprefix] = num
            name = self.declarationcache[tup] = "%s_%s" % (nameprefix, num)
            with self.emit_code_type("declarations"):
                yield name

    def getcode(self):
        res = ["\n".join(self.declarations)]
        res.append("def model_init():\n    " + "\n    ".join(self.runtimeinit or ["pass"]))
        res.append("\n".join(self.code))
        return "\n\n\n".join(res)


def parse_and_make_code(s):
    ast = parse.parser.parse(parse.lexer.lex(s))
    c = Codegen()
    with c.emit_code_type("declarations"):
        c.emit("from rpython.rlib.rbigint import rbigint")
        c.emit("from rpython.rlib import rarithmetic")
        c.emit("import operator")
        c.emit("from pydrofoil.test import supportcode")
        c.emit("class Registers(object): pass")
        c.emit("r = Registers()")
        c.emit("class Lets(object): pass")
        c.emit("l = Lets()")
    try:
        ast.make_code(c)
    except Exception:
        print c.getcode()
        raise
    return c.getcode()


# ____________________________________________________________
# declarations

class __extend__(parse.File):
    def make_code(self, codegen):
        for decl in self.declarations:
            decl.make_code(codegen)

class __extend__(parse.Declaration):
    def make_code(self, codegen):
        raise NotImplementedError("abstract base class")

class __extend__(parse.Enum):
    def make_code(self, codegen):
        name = "Enum_" + self.name
        self.pyname = name
        with codegen.emit_indent("class %s(object):" % name):
            for index, name in enumerate(self.names, start=codegen.last_enum):
                codegen.add_global(name, "%s.%s" % (self.pyname, name), types.Enum(self), self)
                codegen.emit("%s = %s" % (name, index))
            codegen.last_enum += len(self.names) + 1 # gap of 1
            codegen.add_named_type(self.name, self.pyname, types.Enum(self), self)
        codegen.emit()

class __extend__(parse.Union):
    def make_code(self, codegen):
        name = "Union_" + self.name
        self.pyname = name
        with codegen.emit_indent("class %s(object):" % name):
            codegen.emit("pass")
        self.pynames = []
        codegen.add_named_type(self.name, self.pyname, types.Union(self), self)
        for name, typ in zip(self.names, self.types):
            pyname = self.pyname + "_" + name
            codegen.add_global(name, pyname, types.Union(self), self)
            self.pynames.append(pyname)
            with codegen.emit_indent("class %s(%s):" % (pyname, self.pyname)):
                if isinstance(typ, parse.NamedType) and typ.name == "%unit":
                    codegen.emit("def __init__(self, unit): pass")
                    continue
                # XXX could special-case tuples here
                argtypes = [typ]
                args = inits = ["a"]
                fnarg = 'a'
                with codegen.emit_indent("def __init__(self, %s):" % fnarg):
                    for arg, init, typ in zip(args, inits, argtypes):
                        codegen.emit("self.%s = %s # %s" % (arg, init, typ))
        codegen.emit()

class __extend__(parse.Struct):
    def make_code(self, codegen):
        name = "Struct_" + self.name
        self.pyname = name
        structtyp = types.Struct(self)
        structtyp.fieldtyps = {}
        codegen.add_named_type(self.name, self.pyname, structtyp, self)
        with codegen.emit_indent("class %s(object):" % name):
            with codegen.emit_indent("def __init__(self, %s):" % ", ".join(self.names)):
                for arg, typ in zip(self.names, self.types):
                    codegen.emit("self.%s = %s # %s" % (arg, arg, typ))
                    structtyp.fieldtyps[arg] = typ.resolve_type(codegen)

class __extend__(parse.GlobalVal):
    def make_code(self, codegen):
        if self.definition is not None:
            name = eval(self.definition)
            if name == "not": name = "not_"
            codegen.add_global(self.name, "supportcode.%s" % (name, ), self.typ.resolve_type(codegen), self)
        else:
            codegen.add_global(self.name, None,  self.typ.resolve_type(codegen), self)

class __extend__(parse.Register):
    def make_code(self, codegen):
        codegen.emit("# %s" % (self, ))
        codegen.add_global(self.name, "r.%s" % self.name, self.typ.resolve_type(codegen), self)


class __extend__(parse.Function):
    def make_code(self, codegen):
        pyname = "func_" + self.name
        codegen.update_global_pyname(self.name, pyname)
        typ = codegen.globalnames[self.name].typ
        self.pyname = pyname
        args = self.args
        with codegen.emit_indent("def %s(%s):" % (pyname, ", ".join(args))):
            with codegen.enter_scope(self):
                codegen.add_local('return', 'return_', typ.restype, self)
                for i, arg in enumerate(args):
                    codegen.add_local(arg, arg, typ.argtype.elements[i], self)
                jumptargets = {0}
                for i, op in enumerate(self.body):
                    if isinstance(op, (parse.Goto, parse.ConditionalJump)):
                        jumptargets.add(op.target)
                if len(jumptargets) > 1:
                    codegen.emit("pc = 0")
                    codegen.emit("while 1:")
                    codegen.level += 2
                else:
                    jumptargets = set()
                for i, op in enumerate(self.body):
                    if i in jumptargets:
                        codegen.level -= 1
                        codegen.emit("if pc == %s:" % i)
                        codegen.level += 1
                    codegen.emit("# %s" % (op, ))
                    op.make_op_code(codegen)
                    if i + 1 in jumptargets:
                        # XXX remove two pc assignments
                        codegen.emit("pc = %s" % (i + 1, ))
                    op.make_op_jump(codegen, i)
                if len(jumptargets) > 1:
                    codegen.level -= 2
        codegen.emit()

class __extend__(parse.Let):
    def make_code(self, codegen):
        codegen.emit("# %s" % (self, ))
        codegen.add_global(self.name, "l.%s" % self.name, self.typ.resolve_type(codegen), self)
        with codegen.emit_code_type("runtimeinit"), codegen.enter_scope(self):
            for i, op in enumerate(self.body):
                codegen.emit("# %s" % (op, ))
                op.make_op_code(codegen)

# ____________________________________________________________
# operations

class __extend__(parse.Statement):
    def make_op_code(self, codegen):
        raise NotImplementedError

    def make_op_jump(self, codegen, i):
        pass


class __extend__(parse.LocalVarDeclaration):
    def make_op_code(self, codegen):
        codegen.emit("# %s: %s" % (self.name, self.typ))
        typ = self.typ.resolve_type(codegen)
        codegen.add_local(self.name, self.name, typ, self)
        if isinstance(typ, types.Tuple):
            assert self.value is None
            # need to make a tuple instance
            result = codegen.gettarget(self.name)
            codegen.emit("%s = %s()" % (result, typ.pyname))
        elif self.value is not None:
            result = codegen.gettarget(self.name)
            othertyp = self.value.gettyp(codegen)
            rhs = pair(othertyp, typ).convert(self.value, codegen)
            codegen.emit("%s = %s" % (result, rhs))

class __extend__(parse.Operation):
    def make_op_code(self, codegen):
        name = self.name
        result = codegen.gettarget(self.result)
        sargs = [arg.to_code(codegen) for arg in self.args]
        argtyps = [arg.gettyp(codegen) for arg in self.args]
        if name.startswith("@"):
            # XXX mess
            if name == "@eq":
                arg1, arg2 = self.args
                sarg1, sarg2 = sargs
                typ1, typ2 = argtyps
                if isinstance(arg2, parse.Number):
                    if isinstance(typ1, types.MachineInt):
                        sarg2 = str(arg2.number)
                    else:
                        assert 0
                assert not isinstance(typ1, (types.Int, types.GenericBitVector))
                codegen.emit("%s = %s == %s" % (result, sarg1, sarg2))
                return
            if name in ("@lt", "@gt", "@gteq", "@lteq"):
                arg1, arg2 = self.args
                sarg1, sarg2 = sargs
                typ1, typ2 = argtyps
                if typ1 is typ2 is types.Int():
                    # codegen.emit("%s = %s.lt(%s)" % (result, sarg1, sarg2))
                    assert 0
                elif typ1 is types.MachineInt():
                    op = {"@lt": "<", "@gt" : ">", "@gteq" : ">=", "@lteq" : "<="}[name]
                    if isinstance(arg2, parse.Number):
                        sarg2 = str(arg2.number)
                    codegen.emit("%s = %s %s %s" % (result, sarg1, op, sarg2))
                else:
                    assert 0
                return
            if name == "@bvaccess":
                arg1, arg2 = self.args
                sarg1, sarg2 = sargs
                typ1, typ2 = argtyps
                sarg2 = pair(typ2, types.MachineInt()).convert(arg2, codegen)
                codegen.emit("%s = rarithmetic.r_uint(1) & (%s >> rarithmetic.r_uint(%s))" % (result, sarg1, sarg2))
                return
            if name.startswith("@bv"):
                bitvectorop = name[len("@bv"):]
                width = None
                for i, (typ, arg) in enumerate(zip(argtyps, self.args)):
                    assert isinstance(typ, types.FixedBitVector)
                    if width is None:
                        width = typ.width
                    else:
                        assert width == typ.width
                mask = "rarithmetic.r_uint(0x%x)" % ((1 << width) - 1)
                if bitvectorop == "not":
                    res = "~%s"
                elif bitvectorop == "add":
                    res = "%s + %s"
                elif bitvectorop == "sub":
                    res = "%s - %s"
                elif bitvectorop == "and":
                    res = "%s & %s"
                elif bitvectorop == "or":
                    res = "%s | %s"
                else:
                    assert 0
                codegen.emit("%s = (%s) & %s" % (result, res % tuple(sargs), mask))
                return
            else:
                op = "XXX_" + name[1:]
        else:
            op = codegen.getname(name)
        if not sargs:
            args = '()'
        else:
            args = ", ".join(sargs)
        codegen.emit("%s = %s(%s)" % (result, op, args))

class __extend__(parse.ConditionalJump):
    def make_op_code(self, codegen):
        pass

    def make_op_jump(self, codegen, i):
        with codegen.emit_indent("if %s:" % (self.condition.to_code(codegen))):
            codegen.emit("pc = %s" % (self.target, ))
            codegen.emit("continue")

class __extend__(parse.Goto):
    def make_op_code(self, codegen):
        pass

    def make_op_jump(self, codegen, i):
        codegen.emit("pc = %s" % (self.target, ))

class __extend__(parse.Assignment):
    def make_op_code(self, codegen):
        result = codegen.gettarget(self.result)
        typ = codegen.gettyp(self.result)
        othertyp = self.value.gettyp(codegen)
        rhs = pair(othertyp, typ).convert(self.value, codegen)
        codegen.emit("%s = %s" % (result, rhs))

class __extend__(parse.TupleElementAssignment):
    def make_op_code(self, codegen):
        codegen.emit("%s.ztup%s = %s" % (self.tup, self.index, self.value.to_code(codegen)))

class __extend__(parse.StructElementAssignment):
    def make_op_code(self, codegen):
        codegen.emit("%s.%s = %s" % (self.obj, self.field, self.value.to_code(codegen)))

class __extend__(parse.RefAssignment):
    def make_op_code(self, codegen):
        # XXX think long and hard about refs!
        codegen.emit("%s = %s # XXX ref assignment!" % (self.ref, self.value.to_code(codegen)))

class __extend__(parse.End):
    def make_op_code(self, codegen):
        codegen.emit("return return_")

    def make_op_jump(self, codegen, i):
        pass

class __extend__(parse.Failure):
    def make_op_code(self, codegen):
        codegen.emit("raise TypeError")

    def make_op_jump(self, codegen, i):
        pass

class __extend__(parse.Arbitrary):
    def make_op_code(self, codegen):
        codegen.emit("raise ValueError")

    def make_op_jump(self, codegen, i):
        pass

class __extend__(parse.TemplatedOperation):
    def make_op_code(self, codegen):
        if self.name == "@slice":
            arg, num = self.args
            typ = arg.gettyp(codegen)
            assert isinstance(typ, types.FixedBitVector)
            assert isinstance(num, parse.Number)
            assert isinstance(self.templateparam, parse.Number)
            width = self.templateparam.number
            restyp = codegen.gettyp(self.result)
            assert isinstance(restyp, types.FixedBitVector)
            result = codegen.gettarget(self.result)
            assert restyp.width == width
            codegen.emit("%s = (%s >> %s) & rarithmetic.r_uint(0x%x)" % (result, arg.to_code(codegen), num.number, (1 << width) - 1))
        elif self.name == "@signed":
            arg, = self.args
            typ = arg.gettyp(codegen)
            assert isinstance(typ, types.FixedBitVector)
            assert isinstance(self.templateparam, parse.Number)
            width = self.templateparam.number
            restyp = codegen.gettyp(self.result)
            assert isinstance(restyp, types.MachineInt) and width == 64
            result = codegen.gettarget(self.result)
            codegen.emit("%s = supportcode.fast_signed(%s, %s)" % (result, arg.to_code(codegen), typ.width))
        else:
            codegen.emit("XXX")

# ____________________________________________________________
# expressions

class __extend__(parse.Expression):
    def to_code(self, codegen):
        raise NotImplementedError

    def gettyp(self, codegen):
        raise NotImplementedError


class __extend__(parse.Var):
    def to_code(self, codegen):
        return codegen.getname(self.name)

    def gettyp(self, codegen):
        return codegen.gettyp(self.name)

class __extend__(parse.Number):
    def to_code(self, codegen):
        return "rbigint.fromint(%s)" % (self.number, )

    def gettyp(self, codegen):
        return types.Int()

class __extend__(parse.BitVectorConstant):
    def to_code(self, codegen):
        return self.constant

    def gettyp(self, codegen):
        if self.constant.startswith("0b"):
            return types.FixedBitVector(len(self.constant) - 2)
        assert self.constant.startswith("0x")
        return types.FixedBitVector((len(self.constant) - 2) * 4)

class __extend__(parse.Unit):
    def to_code(self, codegen):
        return '()'

    def gettyp(self, codegen):
        return types.Unit()

class __extend__(parse.Undefined):
    def to_code(self, codegen):
        return 'xxx'

    def gettyp(self, codegen):
        return self.typ.resolve_type(codegen)

class __extend__(parse.FieldAccess):
    def to_code(self, codegen):
        return "%s.%s" % (self.obj.to_code(codegen), self.element)

    def gettyp(self, codegen):
        objtyp = self.obj.gettyp(codegen)
        if isinstance(objtyp, types.Tuple):
            assert self.element.startswith("ztup")
            return objtyp.elements[int(self.element[len('ztup'):])]
        return objtyp.fieldtyps[self.element]

class __extend__(parse.Cast):
    def to_code(self, codegen):
        expr = self.expr.to_code(codegen)
        return "(%s.a if isinstance(%s, %s) else supportcode.raise_type_error())" % (expr, expr, codegen.getname(self.variant))

    def gettyp(self, codegen):
        # XXX clean up
        unionast = self.expr.gettyp(codegen).ast
        index = unionast.names.index(self.variant)
        typ = unionast.types[index].resolve_type(codegen)
        return typ

class __extend__(parse.RefOf):
    def to_code(self, codegen):
        expr = self.expr.to_code(codegen)
        assert isinstance(self.expr.gettyp(codegen), types.Struct)
        return expr

    def gettyp(self, codegen):
        return types.Ref(self.expr.gettyp(codegen))

class __extend__(parse.String):
    def to_code(self, codegen):
        return self.string

    def gettyp(self, codegen):
        return types.String()

# ____________________________________________________________
# conditions

class __extend__(parse.Condition):
    def to_code(self, codegen):
        raise NotImplementedError

class __extend__(parse.ExprCondition):
    def to_code(self, codegen):
        return self.expr.to_code(codegen)

class __extend__(parse.Comparison):
    def to_code(self, codegen):
        op = self.operation
        if op.startswith("@"):
            if op == "@not":
                arg, = self.args
                return "not %s" % (arg.to_code(codegen), )
            if op == "@neq":
                arg1, arg2 = self.args
                typ1 = arg1.gettyp(codegen)
                assert isinstance(typ1, types.Enum)
                return "%s != %s" % (arg1.to_code(codegen), arg2.to_code(codegen))
            op = "XXX_cmp_" + op[1:]
        return "%s(%s)" % (op, ", ".join([arg.to_code(codegen) for arg in self.args]))

class __extend__(parse.UnionVariantCheck):
    def to_code(self, codegen):
        return "type(%s) is not %s" % (self.var.to_code(codegen), codegen.getname(self.variant))

# ____________________________________________________________
# types


class __extend__(parse.Type):
    def resolve_type(self, codegen):
        raise NotImplementedError

class __extend__(parse.NamedType):
    def resolve_type(self, codegen):
        name = self.name
        if name == "%bool":
            return types.Bool()
        if name == "%i":
            return types.Int()
        if name == "%bv":
            return types.GenericBitVector()
        if name.startswith("%bv"):
            return types.FixedBitVector(int(name[3:]))
        if name == "%unit":
            return types.Unit()
        if name == "%i64":
            return types.MachineInt()
        if name == "%bit":
            return types.Bit()
        if name == "%string":
            return types.String()
        if name.startswith("%sbv"):
            return types.SmallBitVector(int(name[len("%sbv"):]))
        xxx

class __extend__(parse.EnumType):
    def resolve_type(self, codegen):
        return codegen.get_named_type(self.name)

class __extend__(parse.UnionType):
    def resolve_type(self, codegen):
        return codegen.get_named_type(self.name)

class __extend__(parse.StructType):
    def resolve_type(self, codegen):
        return codegen.get_named_type(self.name)

class __extend__(parse.FunctionType):
    def resolve_type(self, codegen):
        return types.Function(self.argtype.resolve_type(codegen), self.restype.resolve_type(codegen))

class __extend__(parse.RefType):
    def resolve_type(self, codegen):
        return types.Ref(self.refto.resolve_type(codegen))

class __extend__(parse.VecType):
    def resolve_type(self, codegen):
        return types.Vec(self.of.resolve_type(codegen))

class __extend__(parse.TupleType):
    def resolve_type(self, codegen):
        typ = types.Tuple(tuple([e.resolve_type(codegen) for e in self.elements]))
        with codegen.cached_declaration(typ, "Tuple") as pyname:
            codegen.emit("class %s(object): pass # %s" % (pyname, self))
            typ.pyname = pyname
        return typ
