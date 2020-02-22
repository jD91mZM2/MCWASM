from collections import defaultdict, namedtuple
import wasm


class Type(namedtuple(
        "Type",
        ["name", "python_type", "format_spec", "mc_name"]
)):
    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def from_wasm(type_ids):
        if not isinstance(type_ids, list):
            return {
                wasm.LANG_TYPE_I32: Type.I32,
                wasm.LANG_TYPE_I64: Type.I64,
                wasm.LANG_TYPE_F32: Type.F32,
                wasm.LANG_TYPE_F64: Type.F64,
            }[type_ids]
        else:
            return list(map(Type.from_wasm, type_ids))

    def count(types):
        counted = defaultdict(lambda: 0)
        for ty in types:
            counted[ty] += 1
        return counted


Type.I32 = Type("i32", int, "{}", "int")
Type.I64 = Type("i64", int, "{}l", "long")
Type.F32 = Type("f32", float, "{}f", "float")
Type.F64 = Type("f64", float, "{}d", "double")


class Types:
    def __init__(self):
        self.stack = []
        self.conditions = []
        self.locals = []


class Value:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def i32(value):
        return Value(Type.I32, value)

    def i64(value):
        return Value(Type.I64, value)

    def f32(value):
        return Value(Type.F32, value)

    def f64(value):
        return Value(Type.F64, value)

    @property
    def tyname(self):
        return self.type.name

    def cast(self, type):
        return Value(type, type.python_type(self.value))

    def __str__(self):
        return self.type.format_spec.format(self.value)

    def __repr__(self):
        return self.__str__()
