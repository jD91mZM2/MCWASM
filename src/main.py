from argparse import ArgumentParser
from pathlib import Path
from string import Template
import json
import shutil
import sys

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
)
parser.add_argument(
    "--force",
    action="store_true",
    help="Don't prompt before deleting any previous directory",
)

args = parser.parse_args()

with open(args.input, "rb") as f:
    bytecode = f.read()

ctx = transpiler.Context(bytecode)

# Start generation: Copy over template
if args.out_dir.exists():
    if not args.force:
        print(
            "Directory already exists! Are you sure you wish "
            "to delete its contents?"
        )
        print("Pass --force to be noninteractive")
        verification = input("Enter 'yes': ")
        if verification != "yes":
            print("Did not verify")
            sys.exit(1)
    shutil.rmtree(args.out_dir)

shutil.copytree(
    Path(__file__).parent.with_name("template"),
    args.out_dir,
)

if args.namespace is None:
    args.namespace = args.out_dir.name

data_dir = args.out_dir.joinpath("data")
namespace_dir = data_dir.joinpath(args.namespace)
shutil.move(data_dir.joinpath("$namespace"), namespace_dir)

# Substitute tag
load_file = data_dir.joinpath("minecraft", "tags", "functions", "load.json")
with load_file.open("r+") as f:
    original = f.read()
    processed = Template(original).substitute(namespace=args.namespace)
    f.seek(0)
    f.truncate(0)
    f.write(processed)

# Generate functions
functions_dir = namespace_dir.joinpath("functions")
for func in ctx.iter_functions():
    outputs = ctx.transpile(func, args.namespace)

    for out, text in outputs.items():
        path = functions_dir.joinpath(out + ".mcfunction")
        with path.open("w") as f:
            f.write(text)

# Create tags for all exports
tag_dir = namespace_dir.joinpath("tags", "functions")
tag_dir.mkdir(parents=True)
for export in filter(lambda e: e is not None, ctx.iter_exports()):
    path = tag_dir.joinpath(export.name + ".json")
    with path.open("w") as f:
        f.write(json.dumps({
            "values": [
                f"{args.namespace}:{export.value.name}",
                f"{args.namespace}:post_function"
            ]
        }))
