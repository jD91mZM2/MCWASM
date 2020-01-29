from wasm import (
    decode_bytecode,
    format_instruction,
    format_lang_type,
    INSN_ENTER_BLOCK,
    INSN_LEAVE_BLOCK,
)

import ty

with open("add.wasm", "rb") as f:
    bytecode = f.read()

# Parse sections
exports = ty.parse(bytecode)

for func in exports.functions:
    print()
    print("--------------------------------")
    print(f"Function name: {func.name}")
    for arg in func.signature.param_types:
        print(f"Argument: {format_lang_type(arg)}")
    if func.signature.return_type:
        print(f"Return: {format_lang_type(func.signature.return_type)}")
    print("Implementation:")

    indent = 0
    for instruction in decode_bytecode(func.implementation.code):
        if instruction.op.flags & INSN_LEAVE_BLOCK:
            indent -= 2
        print('| ' + ' ' * indent + format_instruction(instruction))
        if instruction.op.flags & INSN_ENTER_BLOCK:
            indent += 2
