from argparse import ArgumentParser
from pathlib import Path
from wasm import (
    decode_bytecode,
    format_instruction,
    format_lang_type,
    INSN_ENTER_BLOCK,
    INSN_LEAVE_BLOCK,
)

import transpiler

parser = ArgumentParser(description="Convert WASM to .mcfunction")
parser.add_argument("input", help="The .wasm file to input")
parser.add_argument(
    "out_dir",
    type=Path,
    help="The functions directory to pop all functions",
)
parser.add_argument(
    "--namespace",
    help="The datapack's namespace",
    required=True,
)

args = parser.parse_args()

with open(args.input, "rb") as f:
    bytecode = f.read()

ctx = transpiler.Context(bytecode)

# Debug print
for export in ctx.iter_exports():
    if isinstance(export, transpiler.Function):
        print()
        print("--------------------------------")
        print(f"Function name: {export.name}")
        for arg in export.type.param_types:
            print(f"Argument: {format_lang_type(arg)}")
        if export.type.return_type:
            print(f"Return: {format_lang_type(export.type.return_type)}")
        print("Implementation:")

        indent = 0
        for instruction in decode_bytecode(export.body.code):
            if instruction.op.flags & INSN_LEAVE_BLOCK:
                indent -= 2
            print('| ' + ' ' * indent + format_instruction(instruction))
            if instruction.op.flags & INSN_ENTER_BLOCK:
                indent += 2

# Start generation
args.out_dir.mkdir(parents=True, exist_ok=True)

for func in ctx.iter_functions():
    path = args.out_dir.joinpath(func.name + ".mcfunction")

    output = ctx.transpile(func.body.code, args.namespace)

    with path.open("w") as f:
        f.write(output)

for static in Path(__file__).with_name("static").iterdir():
    path = args.out_dir.joinpath(static.name)
    with static.open() as input, path.open("w") as output:
        output.write(input.read())
