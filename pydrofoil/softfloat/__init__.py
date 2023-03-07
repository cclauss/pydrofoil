import os
from rpython.rtyper.lltypesystem import rffi
from rpython.translator.tool.cbuild import ExternalCompilationInfo

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
INC_DIR = os.path.join(CUR_DIR, "SoftFloat-3e/source/include/")
LIB_DIR = os.path.join(CUR_DIR, "SoftFloat-3e/build/Linux-x86_64-GCC/")

SRC_FILE = os.path.join(CUR_DIR, "pydrofoil_softfloat.c")
LIB_FILE = ":softfloat.a"

with open(SRC_FILE, "r") as f:
    SRC = f.read()
 
info = ExternalCompilationInfo(
    includes=["pydrofoil_softfloat.h"],
    include_dirs=[CUR_DIR, INC_DIR],
    libraries=[LIB_FILE],
    library_dirs=[LIB_DIR],
    separate_module_sources=[SRC],
)

get_exception_flags = rffi.llexternal("get_exception_flags", [], rffi.ULONGLONG, compilation_info=info)

f16sqrt = rffi.llexternal("f16sqrt", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32sqrt = rffi.llexternal("f32sqrt", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64sqrt = rffi.llexternal("f64sqrt", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16tof32 = rffi.llexternal("f16tof32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16tof64 = rffi.llexternal("f16tof64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16toi32 = rffi.llexternal("f16toi32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16toi64 = rffi.llexternal("f16toi64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16toui32 = rffi.llexternal("f16toui32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16toui64 = rffi.llexternal("f16toui64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32tof16 = rffi.llexternal("f32tof16", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32tof64 = rffi.llexternal("f32tof64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32toi32 = rffi.llexternal("f32toi32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32toi64 = rffi.llexternal("f32toi64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32toui32 = rffi.llexternal("f32toui32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32toui64 = rffi.llexternal("f32toui64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64tof16 = rffi.llexternal("f64tof16", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64tof32 = rffi.llexternal("f64tof32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64toui64 = rffi.llexternal("f64toui64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64toi32 = rffi.llexternal("f64toi32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64toi64 = rffi.llexternal("f64toi64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64toui32 = rffi.llexternal("f64toui32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
i32tof16 = rffi.llexternal("i32tof16", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
i32tof32 = rffi.llexternal("i32tof32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
i32tof64 = rffi.llexternal("i32tof64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
i64tof16 = rffi.llexternal("i64tof16", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
i64tof32 = rffi.llexternal("i64tof32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
i64tof64 = rffi.llexternal("i64tof64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
ui32tof16 = rffi.llexternal("ui32tof16", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
ui32tof32 = rffi.llexternal("ui32tof32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
ui32tof64 = rffi.llexternal("ui32tof64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
ui64tof16 = rffi.llexternal("ui64tof16", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
ui64tof32 = rffi.llexternal("ui64tof32", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
ui64tof64 = rffi.llexternal("ui64tof64", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16add = rffi.llexternal("f16add", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16sub = rffi.llexternal("f16sub", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16mul = rffi.llexternal("f16mul", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16div = rffi.llexternal("f16div", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32add = rffi.llexternal("f32add", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32sub = rffi.llexternal("f32sub", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32mul = rffi.llexternal("f32mul", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32div = rffi.llexternal("f32div", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64add = rffi.llexternal("f64add", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64sub = rffi.llexternal("f64sub", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64mul = rffi.llexternal("f64mul", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64div = rffi.llexternal("f64div", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16eq = rffi.llexternal("f16eq", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16le = rffi.llexternal("f16le", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16lt = rffi.llexternal("f16lt", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32eq = rffi.llexternal("f32eq", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32le = rffi.llexternal("f32le", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32lt = rffi.llexternal("f32lt", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64eq = rffi.llexternal("f64eq", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64le = rffi.llexternal("f64le", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64lt = rffi.llexternal("f64lt", [rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f16muladd = rffi.llexternal("f16muladd", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f32muladd = rffi.llexternal("f32muladd", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)
f64muladd = rffi.llexternal("f64muladd", [rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG, rffi.ULONGLONG], rffi.ULONGLONG, compilation_info=info)

