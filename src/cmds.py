def make_guard(restore):
    class Guard:
        def __init__(self, cmd, *args):
            self.cmd = cmd
            self.args = args

        def __enter__(self):
            pass

        def __exit__(self, type, value, traceback):
            restore(self)
    return Guard

PopParamGuard = make_guard(
    lambda instance: instance.cmd.execute_params.pop(),
)
def RestoreParamGuardExit(instance):
    instance.cmd.execute_params = instance.args[0]
RestoreParamGuard = make_guard(RestoreParamGuardExit)


class CmdGenerator:
    def __init__(self, execute_params):
        self.output = ""
        self.execute_params = execute_params

    # Add a comment to the output, just to keep the output somewhat navigatable
    def comment(self, text):
        self.output += "# " + text + "\n"

    # Execute a raw Minecraft command. For portability reasons with upcoming
    # releases, this should be executed from as few places as possible.
    def execute(self, line):
        params = list(filter(lambda x: x is not None, self.execute_params))
        if params:
            self.output += (
                "execute " + " ".join(params) + " run "
                + line + "\n"
            )
        else:
            self.output += line + "\n"

    # Adds a parameter to the `execute` command that may surround the
    # function. Supposed to be used with a `with` statement which drops the
    # parameter when the with construct is exited.
    def execute_param(self, param):
        self.execute_params.append(param)
        return PopParamGuard(self)

    # Ignores all `execute` parameters. Supposed to be use with a `with`
    # statement, see `execute_param`.
    def ignore_params(self):
        previous = self.execute_params
        self.execute_params = []
        return RestoreParamGuard(self, previous)

    # Load a value from the stack to the scoreboard, where the index is an
    # offset from the top of the stack.
    def load_to_scoreboard(self, stack_index, score):
        with self.execute_param(f"store result score {score} wasm"):
            self.execute(f"data get storage wasm Stack[{-1 - stack_index}]")

    # Load a value from the scoreboard to the stack, where the index is an
    # offset from the top of the stack.
    def load_from_scoreboard(self, score, stack_index):
        with self.execute_param(f"store result storage wasm Stack[{-1 - stack_index}] long 1"):
            self.execute(f"scoreboard players get {score} wasm")

    # Set a static value to the scoreboard
    def set_scoreboard(self, score, value):
        self.execute(f"scoreboard players set {score} wasm {value}")

    # Push a static value to the stack
    def push(self, value):
        self.execute(f"data modify storage wasm Stack append value {value}L")

    # Discard the top of the stack
    def drop(self):
        self.execute("data remove storage wasm Stack[-1]")

    # Run a mathematical operation on the top two values on the stack
    def operation(self, op):
        self.load_to_scoreboard(0, "lhs")
        self.load_to_scoreboard(1, "rhs")
        with self.execute_param(f"store result storage wasm Stack[-2] long 1"):
            self.execute(f"scoreboard players operation lhs wasm {op} rhs wasm")
        self.drop()

    # Add a new local variable list, setting each value to zero initially
    def push_local_frame(self, new_size):
        self.execute(
            f"data modify storage wasm Locals append value [{', '.join(['0L'] * new_size)}]"
        )

    # Drop the top local variable list
    def drop_local_frame(self):
        self.execute("data remove storage wasm Locals[-1]")

    # Get local
    def local_get(self, local_index):
        self.execute(
            "data modify storage wasm Stack append "
            f"from storage wasm Locals[-1][{local_index}]"
        )

    # Set local
    def local_set(self, local_index):
        self.execute(
            f"data modify storage wasm Locals[-1][{local_index}] set "
            "from storage wasm Stack[-1]"
        )
