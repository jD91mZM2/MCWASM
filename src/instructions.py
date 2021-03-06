from cmds import CmdGenerator
from value_types import Type, Types, Value
import wasm

CONDITION_COUNTER = 0


def InstructionHandler(func):
    def first_invocation(*args):
        def second_invocation(cmd, ins):
            return func(*args, cmd, ins)
        return second_invocation
    return first_invocation


class InstructionTable:
    def __init__(self, ctx, wasm_function, namespace):
        self.wasm_function = wasm_function
        self.conditions = ["if score returned wasm = zero wasm"]
        self.ctx = ctx
        self.namespace = namespace
        self.output = [wasm_function.name]
        self.snippets = 0
        self.types = Types()

        # Set up the initial types. `local_frame_push` and other functions
        # won't touch the type list - they rather rely on the new function
        # setting up the same type list by information from WASM.
        self.types.locals = Type.from_wasm(wasm_function.type.param_types)
        self.types.locals += Type.from_wasm_locals(wasm_function.body.locals)

        # See the spec:
        # https://webassembly.github.io/spec/core/binary/instructions.html
        self.handlers = {
            wasm.OP_GET_LOCAL: self.local_get(),
            wasm.OP_SET_LOCAL: self.local_set(),
            wasm.OP_TEE_LOCAL: self.local_tee(),
            wasm.OP_CALL: self.call(),

            # Conditions & Loops
            wasm.OP_IF: self.if_(),
            wasm.OP_ELSE: self.else_(),
            wasm.OP_RETURN: self.return_(),
            wasm.OP_END: self.end(),

            # Consts
            wasm.OP_I32_CONST: self.const(Type.I32),
            wasm.OP_I64_CONST: self.const(Type.I64),
            wasm.OP_F32_CONST: self.const(Type.F32),
            wasm.OP_F64_CONST: self.const(Type.F64),

            # i32 data types
            wasm.OP_I32_EQZ: self.eqz(),
            wasm.OP_I32_EQ: self.cmp("="),
            wasm.OP_I32_LT_S: self.cmp("<"),
            wasm.OP_I32_GT_S: self.cmp(">"),
            wasm.OP_I32_ADD: self.operation("+="),
            wasm.OP_I32_SUB: self.operation("-="),
            wasm.OP_I32_MUL: self.operation("*="),
            wasm.OP_I32_DIV_U: self.operation("/="),
            wasm.OP_I32_REM_U: self.operation("%="),

            # i64 data types
            wasm.OP_I64_EQZ: self.eqz(),
            wasm.OP_I64_EQ: self.cmp("="),
            wasm.OP_I64_LT_S: self.cmp("<"),
            wasm.OP_I64_GT_S: self.cmp(">"),
            wasm.OP_I64_ADD: self.operation("+="),
            wasm.OP_I64_SUB: self.operation("-="),
            wasm.OP_I64_MUL: self.operation("*="),
            wasm.OP_I64_DIV_U: self.operation("/="),
            wasm.OP_I64_REM_U: self.operation("%="),
        }

    def prologue(self):
        return None

    def epilogue(self):
        cmd = CmdGenerator([])
        cmd.set_scoreboard(f"returned", 0)
        return cmd.output

    def handle(self, instruction):
        default_out = self.output[-1]
        cmd = CmdGenerator(self.conditions[:], types=self.types)
        if instruction.op.id in self.handlers:
            print(instruction.op.mnemonic, self.types.stack)
            cmd.execute(
                'tellraw @a "[WASM] Executing: '
                + wasm.format_instruction(instruction)
                + '"'
            )
            specified_out = self.handlers[instruction.op.id](cmd, instruction)
            if specified_out is not None:
                return cmd.output, specified_out
        else:
            cmd.execute(
                'tellraw @a {"text":"[WASM] TODO: '
                + wasm.format_instruction(instruction)
                + '","color":"red"}'
            )
        return cmd.output, default_out

    @InstructionHandler
    def const(self, type, cmd, ins):
        cmd.stack().push(Value(type, ins.imm.value))

    @InstructionHandler
    def operation(self, op, cmd, _ins):
        cmd.stack().operation(op)

    @InstructionHandler
    def eqz(self, cmd, _ins):
        cmd.stack().load_to_scoreboard("lhs")
        cmd.stack().set(Value.i32(0))
        with cmd.execute_param("if score lhs wasm = zero wasm"):
            cmd.stack().set(Value.i32(1))

    @InstructionHandler
    def cmp(self, op, cmd, _ins):
        cmd.stack().load_to_scoreboard("rhs")
        cmd.stack().drop()
        cmd.stack().load_to_scoreboard("lhs")
        cmd.stack().set(Value.i32(0))
        with cmd.execute_param(f"if score lhs wasm {op} rhs wasm"):
            cmd.stack().set(Value.i32(1))

    @InstructionHandler
    def if_(self, cmd, _ins):
        with cmd.no_execute_params():
            cmd.conditions().push(Value.i32(0))
        cmd.conditions().set_from(cmd.stack())
        cmd.conditions().load_to_scoreboard("condition")
        cmd.stack().drop()

        snippet = f"{self.wasm_function.name}_snippet_{self.snippets}"
        self.snippets += 1

        cmd.comment("Conditional is split into separate function")
        with cmd.execute_param(
                f"unless score condition wasm = zero wasm"
        ):
            cmd.function(self.namespace, snippet)

        self.output.append(snippet)

    @InstructionHandler
    def else_(self, cmd, _ins):
        cmd.conditions().load_to_scoreboard("condition")

        snippet = f"{self.wasm_function.name}_snippet_{self.snippets}"
        self.snippets += 1

        cmd.comment("Else branch is also split into separate function")
        with cmd.execute_param(
                f"if score condition wasm = zero wasm"
        ):
            cmd.function(self.namespace, snippet)

        self.output[-1] = snippet
        return self.output[-2]

    @InstructionHandler
    def end(self, cmd, _ins):
        # Beware: This may be the whole function's end
        if len(self.output) > 1:
            self.output.pop()

            with cmd.no_execute_params():
                cmd.conditions().drop()
            return self.output[-1]

    @InstructionHandler
    def return_(self, cmd, _ins):
        self.types.stack.pop()
        cmd.set_scoreboard(f"returned", 1)

    @InstructionHandler
    def call(self, cmd, ins):
        func = self.ctx.function(ins.imm.function_index)

        # Map stack to local variables
        cmd.local_frame_push(Type.from_wasm(func.type.param_types))
        for i in range(func.type.param_count):
            cmd.local_set(i)
            cmd.stack().drop()

        # Actually execute function
        cmd.function(self.namespace, func.name)

        # Drop the stack frame
        cmd.local_frame_drop()

        # Register return value type
        self.types.stack.append(Type.from_wasm(func.type.return_type))

    @InstructionHandler
    def local_set(self, cmd, ins):
        cmd.local_set(ins.imm.local_index)
        cmd.stack().drop()

    @InstructionHandler
    def local_get(self, cmd, ins):
        cmd.local_get(ins.imm.local_index)

    @InstructionHandler
    def local_tee(self, cmd, ins):
        cmd.local_set(ins.imm.local_index)
