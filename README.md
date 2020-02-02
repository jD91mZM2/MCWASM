# MCWASM

*Thanks to [@b3kstudio](https://gitlab.com/b3kstudio) for inspiration and help
with how the generated output should look! It was his idea to use the [data
storage](https://minecraft.gamepedia.com/Commands/data#Storage) feature that
came out in 1.15*

Work-in-progress. Name not decided.

Run [WebAssembly](https://webassembly.org/)-compiled code from Minecraft:

![Screenshot #1](images/screenshot_1.png)
![Screenshot #2](images/screenshot_2.png)

## How it works

It's a transpiler that will turn one basic WebAssembly module into one set of
.mcfunctions ready to be put in a Minecraft datapack.

## Why

Why not? WebAssembly is portable and will run on *everything*. And so it would
make sense that Minecraft can run it too. Now, let's just wait for Mojang to
release a Minecraft version running on WebAssembly, and we'll have Minecraft
inside Minecraft... Like, for real. I'm not kidding. We're not even close to be
there by any means, but it's *actual* progress.

## Usage

1. Compile your WebAssembly file. Since this is a very early project, only
   hand-written WASM files that aren't using any cool features have any chance
   of working.

   You can try files I've written in the `examples` directory:

   ```sh
   wat2wasm examples/add.wat
   ```

1. Create Minecraft datapack. See [Minecraft
   Wiki](https://minecraft.gamepedia.com/Data_pack#Folder_structure). Future
   versions of MCWASM may generate a complete datapack for you, but it doesn't
   for now.

1. Run the `main.py` script with a few arguments:
   1. Input file. This is your compiled .wasm
   1. Output directory. This is your datapack's `data/(namespace)/functions`
      directory.
   1. `--namespace` and then the "namespace" of your output. This is the string
      you choose to be `(namespace)` in the previous step. It's used for
      different functions to be able to access each other.

1. Run it in Minecraft. `/reload` if you've changed the datapack while in game,
   and `/function (namespace):func_#` where `#` is the function you want to
   run. Don't worry - in the future there will be support for actual named
   functions, using Minecraft's tag system.
