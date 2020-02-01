from collections import namedtuple
import wasm

Function = namedtuple("Function", ["name", "type", "body"])


class Context:
    def __init__(self, bytecode):
        sections = iter(wasm.decode_module(bytecode))

        # First section is the header
        header, header_data = next(sections)
        print(header.to_string(header_data))  # TODO remove
        self.header = header
        self.header_data = header_data

        # Following sections are specified at
        # https://webassembly.github.io/spec/core/binary/modules.html#sections
        self.types = []
        self.func_types = []
        self.functions = []
        self.exports = []

        for section, section_data in sections:
            # Debug print. TODO remove or use proper logging interface
            print(section.to_string(section_data))

            if type(section) == wasm.Section:
                if section_data.id == wasm.SEC_CODE:
                    for entry in section_data.payload.bodies:
                        self.functions.append(entry)
                elif section_data.id == wasm.SEC_TYPE:
                    for entry in section_data.payload.entries:
                        self.types.append(entry)
                elif section_data.id == wasm.SEC_FUNCTION:
                    self.func_types += section_data.payload.types
                elif section_data.id == wasm.SEC_EXPORT:
                    for entry in section_data.payload.entries:
                        self.exports.append(entry)

    def export(self, i):
        export = self.exports[i]

        # TODO support more types
        return Function(
            name=bytearray(export.field_str).decode("UTF-8"),
            type=self.types[self.func_types[export.index]],
            body=self.functions[export.index],
        )

    def iter_exports(self):
        for i, _ in enumerate(self.exports):
            yield self.export(i)

    def function(self, i):
        return Function(
            name="func_" + str(i),
            type=self.types[self.func_types[i]],
            body=self.functions[i],
        )

    def iter_functions(self):
        for i, _ in enumerate(self.functions):
            # TODO support more types
            yield self.function(i)

    def transpile(self, bytecode, namespace):
        output = ""
        for instruction in wasm.decode_bytecode(bytecode):
            if instruction.op.flags & wasm.INSN_LEAVE_BLOCK:
                pass  # TODO

            def operation(op):
                return lambda _ins: (
                    "execute store result score lhs wasm run "
                    "data get storage wasm Stack[-2]\n"

                    "execute store result score rhs wasm run "
                    "data get storage wasm Stack[-1]\n"

                    "execute store result storage wasm Stack[-2] long 1 run "
                    f"scoreboard players operation lhs wasm {op} rhs wasm\n"

                    "data remove storage wasm Stack[-1]\n"
                )

            def call(ins):
                func = self.function(ins.imm.function_index)
                prologue = ""
                epilogue = ""

                for _param in func.type.param_types:
                    # Push locals
                    prologue += (
                        "data modify storage wasm Locals append "
                        "from storage wasm Stack[-1]\n"

                        "data remove storage wasm Stack[-1]\n"
                    )
                    # Pop locals
                    epilogue += (
                        "data remove storage wasm Locals[-1]\n"
                    )

                return (
                    prologue
                    + f"function {namespace}:{func.name}\n"
                    + epilogue
                )

            handlers = {
                wasm.OP_GET_LOCAL: lambda ins: (
                    "data modify storage wasm Stack append from storage wasm "
                    f"Locals[{-1 - ins.imm.local_index}]\n"
                ),
                wasm.OP_CALL: call,

                # i32 data types
                wasm.OP_I32_ADD: operation("+="),
                wasm.OP_I32_SUB: operation("-="),
                wasm.OP_I32_MUL: operation("*="),
                wasm.OP_I32_DIV_U: operation("/="),
                wasm.OP_I32_REM_U: operation("%="),

                # i64 data types
                wasm.OP_I64_ADD: operation("+="),
                wasm.OP_I64_SUB: operation("-="),
                wasm.OP_I64_MUL: operation("*="),
                wasm.OP_I64_DIV_U: operation("/="),
                wasm.OP_I64_REM_U: operation("%="),
            }

            if instruction.op.id in handlers:
                output += (
                    'tellraw @a "[WASM] Executing: '
                    + wasm.format_instruction(instruction)
                    + '"\n'
                )
                output += handlers[instruction.op.id](instruction)
                output += "\n"
            else:
                output += (
                    'tellraw @a {"text":"[WASM] TODO: '
                    + wasm.format_instruction(instruction)
                    + '","color":"red"}\n'
                )

            if instruction.op.flags & wasm.INSN_ENTER_BLOCK:
                pass  # TODO
        return output
