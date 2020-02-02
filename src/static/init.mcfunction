# Set up scoreboard
scoreboard objectives remove wasm
scoreboard objectives add wasm dummy {"text":"WebAssembly","color":"green"}
scoreboard objectives setdisplay sidebar wasm
scoreboard players set zero wasm 0

# Set up storage
data modify storage wasm Stack set value []
data modify storage wasm Locals set value []
