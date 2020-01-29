from wasm import (
    decode_module,
    Section,
    SEC_CODE,
    SEC_EXPORT,
    SEC_FUNCTION,
    SEC_TYPE,
)


class Exports:
    def __init__(self):
        self.functions = []

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.__dict__)


class Function:
    def __init__(self):
        self.name = None
        self.signature = None
        self.code = None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.__dict__)


def parse(bytecode):
    sections = iter(decode_module(bytecode))

    # First section is the header
    header, header_data = next(sections)
    print(header.to_string(header_data))

    # Following sections are specified at
    # https://webassembly.org/docs/binary-encoding/#module-structure
    types = []
    signatures = []
    implementations = []
    exports = []

    for section, section_data in sections:
        # Debug print. TODO remove or use proper logging interface
        print(section.to_string(section_data))

        if type(section) == Section:
            if section_data.id == SEC_CODE:
                for entry in section_data.payload.bodies:
                    implementations.append(entry)
            elif section_data.id == SEC_TYPE:
                for entry in section_data.payload.entries:
                    types.append(entry)
            elif section_data.id == SEC_FUNCTION:
                signatures.append(*section_data.payload.types)
            elif section_data.id == SEC_EXPORT:
                for entry in section_data.payload.entries:
                    exports.append(entry)

    # Resolve each export as one big type, with signature and impl

    assembled = Exports()

    for entry in exports:
        function = Function()
        function.name = bytearray(entry.field_str).decode("UTF-8")
        function.signature = types[signatures[entry.index]]
        function.implementation = implementations[entry.index]
        assembled.functions.append(function)

    return assembled
