from rpython.rlib.rbigint import rbigint
from rpython.rlib.rarithmetic import r_uint, intmask

class SmallBitVector(object):
    def __init__(self, size, val):
        self.size = size # number of bits
        self.val = val # r_uint

class GenericBitVector(object):
    def __init__(self, size, rval):
        self.size = size
        self.rval = rval # rbigint
