from collections import defaultdict, namedtuple
from instructions import InstructionTable
import wasm

Function = namedtuple("Function", ["name", "type", "body"])
Export = namedtuple("Export", ["name", "value"])

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

        return Export(
            name=bytearray(export.field_str).decode("UTF-8"),
            # TODO support more types
            value=self.function(i),
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

    def transpile(self, func, namespace):
        outputs = defaultdict(lambda: [])

        instruction_table = InstructionTable(self, func, namespace)
        prologue = instruction_table.prologue()
        if prologue is not None:
            outputs[func.name].append(prologue)

        for instruction in wasm.decode_bytecode(func.body.code):
            out = instruction_table.output[-1]
            commands = instruction_table.handle(instruction)
            outputs[out].append(commands)

        epilogue = instruction_table.epilogue()
        if epilogue is not None:
            outputs[func.name].append(epilogue)

        for out in outputs:
            outputs[out] = "\n".join(outputs[out])

        return outputs
