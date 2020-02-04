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
   make -C examples
   ```

   and then you can find the binaries in `examples/build/*.wasm`

1. Run the `main.py` script with a few arguments:
   1. Input file. This is your compiled .wasm
   1. Output directory. This is the destination of the datapack. The directory
      should not exist, and look something like `~/.minecraft/saves/My
      World/datapacks/my-wasm-datapack`.
   1. `--namespace` and then the "namespace" of your output. This is the string
      you choose to be `(namespace)` in the previous step. It's used for
      different functions to be able to access each other.

1. Run it in Minecraft. `/reload` if you've changed the datapack while in game,
   and `/function #(namespace):my-exported-function`. That works because
   there's a user-friendly "tag" set up. If you omit the hash, you'll notice a
   few more functions. Just for reference:
   - `func_(x)` are the main function bodies, with numbers ordered after their
     parsing position. You'd be better off not relying on these.
   - `func_(x)_snippet_(y)` are parts of the functions, such as conditionals,
     that needed to be split out for technical reasons. You'd be straight up
     insane if you try to rely on these snippets, the numbers are at this point
     just completely unstable.
   - `init` is the function that runs when you run `/reload` (a part of the
     `#minecraft:load` tag).
