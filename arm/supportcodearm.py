from rpython.rlib import jit
from pydrofoil import mem as mem_mod
from pydrofoil.supportcode import *
from pydrofoil.supportcode import Globals as BaseGlobals

# globals etc

def get_main(outarm):
    Machine = outarm.Machine

    def main(argv):
        from rpython.rlib.rarithmetic import r_uint, intmask, ovfcheck
        from arm import supportcodearm
        machine = Machine()
        print "loading Linux kernel"
        supportcodearm.load_raw(machine, [r_uint(0x80000000), r_uint(0x81000000), r_uint(0x82080000)], ["arm/bootloader.bin", "arm/sail.dtb", "arm/Image"])
        armmain.mod.func_z__SetConfig(machine, "cpu.cpu0.RVBAR", bitvector.Integer.fromint(0x80000000))
        armmain.mod.func_z__SetConfig(machine, "cpu.has_tlb", bitvector.Integer.fromint(0x0))
        print "done, starting main"
        outarm.func_zmain(machine, ())
        return 0
    main.mod = outarm
    return main


class Globals(BaseGlobals):
    def __init__(self):
        BaseGlobals.__init__(self)
        self.cycle_count = 0


def make_dummy(name):
    def dummy(machine, *args):
        if objectmodel.we_are_translated():
            print "not implemented!", name
            raise ValueError
        import pdb; pdb.set_trace()
        return 123
    dummy.func_name += name
    globals()[name] = dummy


def platform_branch_announce(machine, *args):
    return ()

def reset_registers(machine, *args):
    return ()

def load_raw(machine, offsets, filenames):
    machine.g = Globals()
    assert len(offsets) == len(filenames)
    for i in range(len(offsets)):
        offset = offsets[i]
        fn = filenames[i]
        f = open(fn, 'rb')
        content = f.read()
        for i, byte in enumerate(content):
            machine.g.mem.write(offset + i, 1, r_uint(ord(byte)))

def elf_entry(machine, _):
    return bitvector.Integer.fromint(0x80000000)

def cycle_count(machine, _):
    machine.g.cycle_count += 1
    return ()

cyclecount = 0

def get_cycle_count(machine, _):
    return bitvector.Integer.fromint(machine.g.cycle_count)

def sail_get_verbosity(machine, _):
    return r_uint(0xffff)
