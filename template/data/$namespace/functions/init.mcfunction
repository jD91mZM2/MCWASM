# Set up scoreboard
scoreboard objectives remove wasm
scoreboard objectives add wasm dummy {"text":"WebAssembly","color":"green"}
scoreboard objectives setdisplay sidebar wasm
scoreboard players set zero wasm 0
scoreboard players set returned wasm 0

# Set up storage
data modify storage wasm Stack set value {}
data modify storage wasm Conditions set value {}
data modify storage wasm Locals set value [{}]

# Display an interactive thing
tellraw @a {"text":"Loaded WebAssembly functions","color":"green"}
tellraw @a {"text":"- Prepare a function call","color":"gray","clickEvent":{"action":"suggest_command","value":"/data modify storage wasm Locals set value [{i32: [1, 2]}]"}}
