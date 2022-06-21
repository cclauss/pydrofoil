from rpython.rlib.rbigint import rbigint
from rpython.rlib.rarithmetic import r_uint, intmask

def from_ruint(size, val):
    if size <= 64:
        return SmallBitVector(size, val, True)
    return GenericBitVector(size, rbigint.fromrarith_int(val), True)

def from_bigint(size, rval):
    if size <= 64:
        return SmallBitVector(size, rval.touint(), True)
    return GenericBitVector(size, rval, True)

class BitVector(object):
    def __init__(self, size):
        self.size = size

class SmallBitVector(BitVector):
    def __init__(self, size, val, normalize=False):
        self.size = size # number of bits
        assert isinstance(val, r_uint)
        if normalize:
            val = val & ((r_uint(1) << size) - 1)
        self.val = val # r_uint

    def __repr__(self):
        return "<SmallBitVector %s 0x%x>" % (self.size, self.val)

    def _check_size(self, other):
        assert other.size == self.size
        assert isinstance(other, SmallBitVector)
        return other

    def add_int(self, i):
        return from_bigint(self.size, self.tobigint().add(i))

    def sub_int(self, i):
        return from_bigint(self.size, self.tobigint().sub(i))

    def print_bits(self):
        print self.__repr__()

    def lshift(self, i):
        return from_ruint(self.size, self.val << i)

    def rshift(self, i):
        return from_ruint(self.size, self.val >> i)

    def lshift_bits(self, other):
        return from_ruint(self.size, self.val << other.touint())

    def rshift_bits(self, other):
        return from_ruint(self.size, self.val >> other.touint())

    def xor(self, other):
        assert isinstance(other, SmallBitVector)
        return from_ruint(self.size, self.val ^ other.val)

    def and_(self, other):
        assert isinstance(other, SmallBitVector)
        return from_ruint(self.size, self.val & other.val)

    def or_(self, other):
        assert isinstance(other, SmallBitVector)
        return from_ruint(self.size, self.val | other.val)

    def invert(self):
        return from_ruint(self.size, ~self.val)

    def subrange(self, n, m):
        width = n - m + 1
        return from_ruint(width, self.val >> m)

    def sign_extend(self, i):
        if i == self.size:
            return self
        assert i > self.size
        highest_bit = (self.val >> (self.size - 1)) & 1
        if not highest_bit:
            return from_ruint(i, self.val)
        else:
            assert i <= 64 # otherwise more complicated
            extra_bits = i - self.size
            bits = ((r_uint(1) << extra_bits) - 1) << self.size
            return from_ruint(i, bits | self.val)

    def update_bit(self, pos, bit):
        mask = r_uint(1) << pos
        if bit:
            return from_ruint(self.size, self.val | mask)
        else:
            return from_ruint(self.size, self.val & ~mask)

    def update_subrange(self, n, m, s):
        width = s.size
        assert width == n - m + 1
        mask = ~(((r_uint(1) << width) - 1) << m)
        return from_ruint(self.size, (self.val & mask) | (s.touint() << m))

    def signed(self):
        n = self.size
        if n == 64:
            return rbigint.fromint(intmask(self.val))
        assert n > 0
        u1 = r_uint(1)
        m = u1 << (n - 1)
        op = self.val & ((u1 << n) - 1) # mask off higher bits to be sure
        return rbigint.fromint(intmask((op ^ m) - m))

    def unsigned(self):
        return rbigint.fromrarith_int(self.val)

    def eq(self, other):
        other = self._check_size(other)
        return self.val == other.val

    def toint(self):
        return intmask(self.val)

    def touint(self):
        return self.val

    def tobigint(self):
        return rbigint.fromrarith_int(self.val)


class GenericBitVector(BitVector):
    def __init__(self, size, rval, normalize=False):
        assert size > 0
        self.size = size
        if normalize:
            rval = self._size_mask(rval)
        self.rval = rval # rbigint

    def __repr__(self):
        return "<GenericBitVector %s %r>" % (self.size, self.rval)

    def _size_mask(self, val):
        return val.and_(rbigint.fromint(1).lshift(self.size).int_sub(1))

    def add_int(self, i):
        return GenericBitVector(self.size, self._size_mask(self.rval.add(i)))

    def sub_int(self, i):
        return GenericBitVector(self.size, self._size_mask(self.rval.sub(i)))

    def print_bits(self):
        print "GenericBitVector<%s, %s>" % (self.size, self.rval.hex())

    def lshift(self, i):
        return GenericBitVector(self.size, self._size_mask(self.rval.lshift(i)))

    def rshift(self, i):
        return GenericBitVector(self.size, self._size_mask(self.rval.rshift(i)))

    def lshift_bits(self, other):
        return GenericBitVector(self.size, self._size_mask(self.rval.lshift(other.toint())))

    def rshift_bits(self, other):
        return GenericBitVector(self.size, self._size_mask(self.rval.rshift(other.toint())))

    def xor(self, other):
        return GenericBitVector(self.size, self._size_mask(self.rval.xor(other.rval)))

    def or_(self, other):
        return GenericBitVector(self.size, self._size_mask(self.rval.or_(other.rval)))

    def and_(self, other):
        return GenericBitVector(self.size, self._size_mask(self.rval.and_(other.rval)))

    def invert(self):
        return GenericBitVector(self.size, self._size_mask(self.rval.invert()))

    def subrange(self, n, m):
        width = n - m + 1
        return GenericBitVector(width, self.rval.rshift(m))

    def sign_extend(self, i):
        if i == self.size:
            return self
        assert i > self.size
        highest_bit = self.rval.rshift(self.size - 1).int_and_(1).toint()
        if not highest_bit:
            return GenericBitVector(i, self.rval)
        else:
            extra_bits = i - self.size
            bits = rbigint.fromint(1).lshift(extra_bits).int_sub(1).lshift(self.size)
            return GenericBitVector(i, bits.or_(self.rval))

    def update_bit(self, pos, bit):
        mask = rbigint.fromint(1).lshift(pos)
        if bit:
            return GenericBitVector(self.size, self.rval.or_(mask))
        else:
            return GenericBitVector(self.size, self._size_mask(self.rval.and_(mask.invert())))

    def update_subrange(self, n, m, s):
        width = s.size
        assert width == n - m + 1
        mask = rbigint.fromint(1).lshift(width).int_sub(1).lshift(m).invert()
        return GenericBitVector(self.size, self.rval.and_(mask).or_(s.tobigint().lshift(m)))

    def signed(self):
        n = self.size
        assert n > 0
        u1 = rbigint.fromint(1)
        m = u1.lshift(n - 1)
        op = self.rval
        op = op.and_((u1.lshift(n)).int_sub(1)) # mask off higher bits to be sure
        return op.xor(m).sub(m)

    def unsigned(self):
        return self.rval

    def eq(self, other):
        return self.rval.eq(other.rval)

    def toint(self):
        return self.rval.toint()

    def touint(self):
        return self.rval.touint()

    def tobigint(self):
        return self.rval
