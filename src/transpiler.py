from collections import namedtuple
import wasm

Function = namedtuple("Function", ["name", "type", "body"])

condition_counter = 0


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
        total_output = ""
        conditions = []

        for instruction in wasm.decode_bytecode(bytecode):
            comments = []
            prev_conditions = conditions[:]

            def load_to_scoreboard(score, storage):
                return [
                    f"execute store result score {score} wasm run "
                    f"data get storage wasm {storage}",
                ]

            def operation(op):
                return lambda _ins: (
                    load_to_scoreboard("lhs", "Stack[-1]")
                    + load_to_scoreboard("rhs", "Stack[-1]")
                    + [
                        "execute store result storage wasm Stack[-2] "
                        "long 1 run "
                        f"scoreboard players operation lhs wasm {op} rhs wasm",
                    ]
                )

            def call(ins):
                func = self.function(ins.imm.function_index)
                prologue = []
                epilogue = []

                for _param in func.type.param_types:
                    # Push locals
                    prologue += [
                        "data modify storage wasm Locals append "
                        "from storage wasm Stack[-1]",

                        "data remove storage wasm Stack[-1]",
                    ]
                    # Pop locals
                    epilogue += [
                        "data remove storage wasm Locals[-1]",
                    ]

                return (
                    prologue
                    + [f"function {namespace}:{func.name}"]
                    + epilogue
                )

            def const(ins):
                return [
                    "data modify storage wasm Stack append value "
                    + str(ins.imm.value) + "L"
                ]

            def if_(_ins):
                global condition_counter

                number = condition_counter
                condition_counter += 1

                conditions.append(
                    f"unless score condition_{number} wasm = zero wasm"
                )
                comments.append(f"Condition #{number} begin")
                return (
                    load_to_scoreboard("condition_" + str(number), "Stack[-1]")
                    + ["data remove storage wasm Stack[-1]"]
                )

            def end(_ins):
                if conditions:
                    conditions.pop()
                    # also pop from this instruction's conditions
                    prev_conditions.pop()
                    number = len(conditions)
                    comments.append(f"Conditional #{number} end")
                return []

            def eqz(_ins):
                return (
                    load_to_scoreboard("lhs", "Stack[-1]")
                    # Invert lhs: 0 -> 1 ([^0]), [^0] -> 0
                    + [
                        "execute if score lhs wasm = zero wasm run "
                        "scoreboard players set rhs wasm 1",

                        "execute unless score lhs wasm = zero wasm run "
                        "scoreboard players set rhs wasm 0",

                        "execute store result storage wasm Stack[-1] long 1 "
                        "run scoreboard players get rhs wasm",
                    ]
                )

            # See the spec:
            # https://webassembly.github.io/spec/core/binary/instructions.html
            handlers = {
                wasm.OP_GET_LOCAL: lambda ins: [
                    "data modify storage wasm Stack append from storage wasm "
                    f"Locals[{-1 - ins.imm.local_index}]"
                ],
                wasm.OP_CALL: call,

                # Conditions & Loops
                wasm.OP_IF: if_,
                wasm.OP_END: end,

                # Consts
                wasm.OP_I32_CONST: const,
                wasm.OP_I64_CONST: const,

                # i32 data types
                wasm.OP_I32_EQZ: eqz,
                wasm.OP_I32_ADD: operation("+="),
                wasm.OP_I32_SUB: operation("-="),
                wasm.OP_I32_MUL: operation("*="),
                wasm.OP_I32_DIV_U: operation("/="),
                wasm.OP_I32_REM_U: operation("%="),

                # i64 data types
                wasm.OP_I64_EQZ: eqz,
                wasm.OP_I64_ADD: operation("+="),
                wasm.OP_I64_SUB: operation("-="),
                wasm.OP_I64_MUL: operation("*="),
                wasm.OP_I64_DIV_U: operation("/="),
                wasm.OP_I64_REM_U: operation("%="),
            }

            if instruction.op.id in handlers:
                output = [
                    'tellraw @a "[WASM] Executing: '
                    + wasm.format_instruction(instruction)
                    + '"'
                ]
                output += handlers[instruction.op.id](instruction)
            else:
                output = [
                    'tellraw @a {"text":"[WASM] TODO: '
                    + wasm.format_instruction(instruction)
                    + '","color":"red"}'
                ]

            for comment in comments:
                total_output += "# " + comment + "\n"
            for line in output:
                if prev_conditions:
                    total_output += (
                        "execute " + " ".join(prev_conditions) + " run "
                        + line + "\n"
                    )
                else:
                    total_output += line + "\n"
            total_output += "\n"
        return total_output
