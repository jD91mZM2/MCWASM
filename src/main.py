from wasm import (
    # format_instruction,
    # format_lang_type,
    # format_mutability,
    # SEC_DATA,
    # SEC_ELEMENT,
    # SEC_GLOBAL,
    decode_module,
    format_function,
    Section,
    SEC_CODE,
    SEC_EXPORT,
    SEC_FUNCTION,
    SEC_TYPE,
)

with open("add.wasm", "rb") as f:
    raw = f.read()

# Parse sections
sections = iter(decode_module(raw))

# First section is the header
header, header_data = next(sections)
print(header.to_string(header_data))

# Following sections are specified at
# https://webassembly.org/docs/binary-encoding/#module-structure
types = []
signatures = []
implementations = []
exports = []

code_sec = None
type_sec = None
func_sec = None
for section, section_data in sections:
    # Debug print
    print(section.to_string(section_data))

    if type(section) == Section:
        if section_data.id == SEC_CODE:
            code_sec = section_data.payload  # todo remove
            for entry in section_data.payload.bodies:
                implementations.append(entry)
        elif section_data.id == SEC_TYPE:
            type_sec = section_data.payload  # todo remove
            for entry in section_data.payload.entries:
                types.append(entry)
        elif section_data.id == SEC_FUNCTION:
            func_sec = section_data.payload  # todo remove
            signatures.append(*section_data.payload.types)
        elif section_data.id == SEC_EXPORT:
            for entry in section_data.payload.entries:
                exports.append(entry)

print(types)
print(signatures)
print(implementations)
print(exports)

# TODO: Resolve each export as one big type, with signature and impl?

if code_sec is not None:
    for i, func_body in enumerate(code_sec.bodies):
        print('{x} sub_{id:04X} {x}'.format(x='=' * 35, id=i))

        # If we have type info, use it. Look into when we won't have type info!
        func_type = type_sec.entries[func_sec.types[i]] if (
            None not in (type_sec, func_sec)
        ) else None

        print()
        print('\n'.join(format_function(func_body, func_type)))
        print()
