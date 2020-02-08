class WithGuard:
    def __init__(self, restore):
        self.restore = restore

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        self.restore()


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
        return WithGuard(lambda: self.execute_params.pop())

    # Removes all `execute` parameters temporarily, so this will run regardless
    # of if the function has been returned or anything!
    def no_execute_params(self):
        old = self.execute_params
        self.execute_params = []

        def restore():
            self.execute_params = old
        return WithGuard(restore)

    # Set a static value to the scoreboard
    def set_scoreboard(self, score, value):
        self.execute(f"scoreboard players set {score} wasm {value}")

    # Return the main stack
    def stack(self):
        return Stack(self, "Stack")

    # Return the stack of conditionals
    def conditions(self):
        return Stack(self, "Conditions")

    # Add a new local variable list, setting each value to zero initially
    def local_frame_push(self, new_size):
        self.execute(
            f"data modify storage wasm Locals append value "
            f"[{', '.join(['0L'] * new_size)}]"
        )

    # Drop the top local variable list
    def local_frame_drop(self):
        self.execute("data remove storage wasm Locals[-1]")

    # Reserve extra local variable space
    def local_frame_reserve(self, extra_size):
        for _ in range(extra_size):
            self.execute(
                f"data modify storage wasm Locals[-1] append value 0L"
            )

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

    # Run a function
    def function(self, namespace, func):
        self.execute(f"function {namespace}:{func}")


class Stack:
    def __init__(self, cmd, name):
        self.cmd = cmd
        self.name = name

    # Push a static value to the stack
    def push(self, value):
        self.cmd.execute(
            f"data modify storage wasm {self.name} append value {value}L"
        )

    # Discard the top of the stack
    def drop(self):
        self.cmd.execute(f"data remove storage wasm {self.name}[-1]")

    # Copy the top level value to another stack
    def push_from(self, other):
        self.cmd.execute(
            f"data modify storage wasm {self.name} append from "
            f"storage wasm {other.name}[-1]"
        )

    # Set the top value of the stack
    def set(self, value):
        self.cmd.execute(
            f"data modify storage wasm {self.name}[-1] set value {value}L"
        )

    # Copy the top level value to another stack, and assign it in-place
    def set_from(self, other):
        self.cmd.execute(
            f"data modify storage wasm {self.name}[-1] set from "
            f"storage wasm {other.name}[-1]"
        )

    # Load a value from the stack to the scoreboard, where the index is an
    # offset from the top of the stack.
    def load_to_scoreboard(self, score):
        with self.cmd.execute_param(f"store result score {score} wasm"):
            self.cmd.execute(f"data get storage wasm {self.name}[-1]")

    # Load a value from the scoreboard to the stack, where the index is an
    # offset from the top of the stack.
    def load_from_scoreboard(self, score):
        with self.cmd.execute_param(
                f"store result storage wasm {self.name}[-1] long 1"
        ):
            self.cmd.execute(f"scoreboard players get {score} wasm")

    # Run a mathematical operation on the top two values on the stack
    def operation(self, op):
        # Note: Since it's a stack we want to grab the second operand first!
        self.load_to_scoreboard("rhs")
        self.drop()
        self.load_to_scoreboard("lhs")
        with self.cmd.execute_param(
                f"store result storage wasm Stack[-1] long 1"
        ):
            self.cmd.execute(
                f"scoreboard players operation lhs wasm {op} rhs wasm"
            )
