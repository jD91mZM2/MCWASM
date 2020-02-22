from collections import defaultdict, namedtuple
from enum import Enum
import wasm

from cmds import CmdGenerator
from instructions import InstructionTable
from value_types import Type


class ExportKind(Enum):
    FUNCTION = 0x0
    TABLE = 0x1
    MEMORY = 0x2
    GLOBAL = 0x3


Function = namedtuple("Function", ["name", "type", "body"])
Export = namedtuple("Export", ["name", "kind", "value"])

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
                    self.functions += section_data.payload.bodies
                elif section_data.id == wasm.SEC_TYPE:
                    self.types += section_data.payload.entries
                elif section_data.id == wasm.SEC_FUNCTION:
                    self.func_types += section_data.payload.types
                elif section_data.id == wasm.SEC_EXPORT:
                    self.exports += section_data.payload.entries

    def export(self, i):
        export = self.exports[i]

        # TODO support more types?
        if export.kind == ExportKind.FUNCTION.value:
            return Export(
                name=bytearray(export.field_str).decode("UTF-8"),
                kind=ExportKind.FUNCTION,
                value=self.function(export.index),
            )

    def iter_exports(self):
        return map(self.export, range(len(self.exports)))

    def function(self, i):
        return Function(
            name="func_" + str(i),
            type=self.types[self.func_types[i]],
            body=self.functions[i],
        )

    def iter_functions(self):
        return map(self.function, range(len(self.functions)))

    def transpile(self, func, namespace):
        outputs = defaultdict(lambda: [])

        if func.body.local_count > 0:
            cmd = CmdGenerator([])
            cmd.comment("Reserve space for local variables (other than args)")
            cmd.local_frame_reserve(Type.from_wasm(func.body.local_count))
            outputs[func.name].append(cmd.output)

        instruction_table = InstructionTable(self, func, namespace)
        prologue = instruction_table.prologue()
        if prologue is not None:
            outputs[func.name].append(prologue)

        for instruction in wasm.decode_bytecode(func.body.code):
            commands, out = instruction_table.handle(instruction)
            outputs[out].append(commands)

        epilogue = instruction_table.epilogue()
        if epilogue is not None:
            outputs[func.name].append(epilogue)

        for out in outputs:
            outputs[out] = "\n".join(outputs[out])

        return outputs
