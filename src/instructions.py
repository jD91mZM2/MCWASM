from cmds import CmdGenerator
import wasm

CONDITION_COUNTER = 0
FUNCTION_COUNTER = 0


def InstructionHandler(func):
    def first_invocation(*args):
        def second_invocation(cmd, ins):
            func(*args, cmd, ins)
        return second_invocation
    return first_invocation


class InstructionTable:
    def __init__(self, ctx, namespace):
        self.conditions = []
        self.ctx = ctx
        self.namespace = namespace

        # See the spec:
        # https://webassembly.github.io/spec/core/binary/instructions.html
        self.handlers = {
            wasm.OP_GET_LOCAL: self.local_get(),
            wasm.OP_SET_LOCAL: self.local_set(),
            wasm.OP_TEE_LOCAL: self.local_tee(),
            wasm.OP_CALL: self.call(),

            # Conditions & Loops
            wasm.OP_IF: self.if_(),
            wasm.OP_RETURN: self.return_(),
            wasm.OP_END: self.end(),

            # Consts
            wasm.OP_I32_CONST: self.const(),
            wasm.OP_I64_CONST: self.const(),

            # i32 data types
            wasm.OP_I32_EQZ: self.eqz(),
            wasm.OP_I32_ADD: self.operation("+="),
            wasm.OP_I32_SUB: self.operation("-="),
            wasm.OP_I32_MUL: self.operation("*="),
            wasm.OP_I32_DIV_U: self.operation("/="),
            wasm.OP_I32_REM_U: self.operation("%="),

            # i64 data types
            wasm.OP_I64_EQZ: self.eqz(),
            wasm.OP_I64_ADD: self.operation("+="),
            wasm.OP_I64_SUB: self.operation("-="),
            wasm.OP_I64_MUL: self.operation("*="),
            wasm.OP_I64_DIV_U: self.operation("/="),
            wasm.OP_I64_REM_U: self.operation("%="),
        }

    def prologue(self):
        global FUNCTION_COUNTER
        self.id = FUNCTION_COUNTER
        FUNCTION_COUNTER += 1

        cmd = CmdGenerator(self.conditions)
        cmd.set_scoreboard(f"returned_{self.id}", 0)

        self.conditions += [None]

        return cmd.output

    def handle(self, instruction):
        cmd = CmdGenerator(self.conditions[:])
        if instruction.op.id in self.handlers:
            cmd.execute(
                'tellraw @a "[WASM] Executing: '
                + wasm.format_instruction(instruction)
                + '"'
            )
            self.handlers[instruction.op.id](cmd, instruction)
        else:
            cmd.execute(
                'tellraw @a {"text":"[WASM] TODO: '
                + wasm.format_instruction(instruction)
                + '","color":"red"}'
            )
        return cmd.output

    @InstructionHandler
    def const(self, cmd, ins):
        cmd.push(ins.imm.value)

    @InstructionHandler
    def operation(self, op, cmd, _ins):
        cmd.operation(op)
        return cmd

    @InstructionHandler
    def eqz(self, cmd, _ins):
        cmd.load_to_scoreboard(0, "lhs")
        cmd.set_scoreboard("rhs", 0)
        with cmd.execute_param("if score lhs wasm = zero wasm"):
            cmd.set_scoreboard("rhs", 1)
        cmd.load_from_scoreboard("rhs", 0)

    @InstructionHandler
    def if_(self, cmd, _ins):
        global CONDITION_COUNTER
        number = CONDITION_COUNTER
        CONDITION_COUNTER += 1

        cmd.load_to_scoreboard(0, f"condition_{number}")
        cmd.drop()
        cmd.comment(f"Condition #{number} begin")

        self.conditions.append(
            f"unless score condition_{number} wasm = zero wasm"
        )

    @InstructionHandler
    def end(self, cmd, _ins):
        # Beware: This may be the whole function's end
        if self.conditions:
            self.conditions.pop()
            cmd.comment(f"Condition #{len(self.conditions)} end")

    @InstructionHandler
    def return_(self, cmd, _ins):
        self.conditions[0] = f"if score returned_{self.id} wasm = zero wasm"
        cmd.set_scoreboard(f"returned_{self.id}", 1)

    @InstructionHandler
    def call(self, cmd, ins):
        func = self.ctx.function(ins.imm.function_index)

        # Map stack to local variables
        cmd.push_local_frame(len(func.type.param_types))
        for i, _ in enumerate(func.type.param_types):
            cmd.local_set(i)
            cmd.drop()

        with cmd.ignore_params():
            # Push return status to stack. All non-return conditionals should,
            # in the future, be split into their own channels.
            cmd.comment("Preserve return status")
            cmd.push(0)
            cmd.load_from_scoreboard(f"returned_{self.id}", 0)

        # Actually execute function
        cmd.execute(f"function {self.namespace}:{func.name}")

        with cmd.ignore_params():
            # Pop return status. See the note above.
            cmd.comment("Restore return status")
            cmd.load_to_scoreboard(0, f"returned_{self.id}")
            cmd.drop()

        # Drop the stack frame
        cmd.drop_local_frame()

    @InstructionHandler
    def local_set(self, cmd, ins):
        cmd.local_set(ins.imm.local_index)
        cmd.drop()

    @InstructionHandler
    def local_get(self, cmd, ins):
        cmd.local_get(ins.imm.local_index)

    @InstructionHandler
    def local_tee(self, cmd, ins):
        cmd.local_set(ins.imm.local_index)
