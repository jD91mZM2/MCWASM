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

## Plans

### How to implement loops

The easiest way to keep all state and context, would be to implement loops as
recursion allows stuff to be ran multiple times. WASM loops look like this:

```wasm
block  ;; implicitly gets label 0
  loop ;; implicitly gets label 1
    br 1 ;; in order to break loop
    br 0 ;; in order to continue loop
  end
end
```

which is best thought in these terms:

- break = stop running the code you're currently running
- breaking a loop = stop running the loop's body, but then re-run it
- breaking a block = stop running the block's body, exit the block

or

```c
label_0:
  goto label_1; // break loop
  goto label_0; // continue loop
label_1:
```

Each loop body would get its own "snippet" (just like if-statements currently
work by creating a file `func_X_snippet_Y.mcfunction`). Each line in the body
would have the extra conditional `if score break_N wasm == zero wasm`, similar
to how return works. The loop body would end with a recursive `function` call,
that isn't conditional on `break_N`.

A block would simply create a conditional `if score break_M wasm == zero wasm`,
and then flip it to 1 when breaking the body. The recursive `function` call in
a loop would still be dependent on that variable.

`func_0_snippet_0`:

```mcfunction
if score break_0 wasm == zero wasm if score break_1 wasm == zero wasm run say I'm in your loop

# To `br` loop (continue)
if score break_0 wasm == zero wasm if score break_1 wasm == zero wasm run scoreboard players set break_1 wasm 1

# To `br` block (break)
if score break_0 wasm == zero wasm if score break_1 wasm == zero wasm run scoreboard players set break_0 wasm 1

# Function epilogue: Reset and loop
if score break_0 wasm == zero wasm run scoreboard players set break_1 wasm 0
if score break_0 wasm == zero wasm run function namespace:func_0_snippet_0
```

Nesting functions with loops should in theory be able to be implemented either
by pushing all label break values to the stack, OR just resetting them to zero
(after all, the function is only called if all break variables are zero). At
the end of a function (not a snippet) we could probably count all used loop
variables during the function and unconditionally reset them, similar to how
`return` is reset somewhere.

### How to emulate floating point

Two particularly compelling ideas:

- [Floating Point Numbers in Minecraft 1.12](https://youtu.be/e6OrClOPO_M)
- Write some Rust code to emulate them, and then compile that Rust to WASM and
  then to mcfunction and use it in the transpiler itself :D (the fact that I'm
  soon at the point where missing WASM features can be emulated with WASM is a
  really good sign)
