from value_types import Type, Value


class WithGuard:
    def __init__(self, restore):
        self.restore = restore

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        self.restore()


class CmdGenerator:
    def __init__(self, execute_params, types=None):
        self.output = ""
        self.types = types
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
        return Stack(self, "Stack", self.types.stack)

    # Return the stack of conditionals
    def conditions(self):
        return Stack(self, "Conditions", self.types.conditions)

    # Add a new local variable list, setting each value to zero initially
    #
    # NOTE: Unlike the stack, this does not update the type list. So make sure
    # you don't rely on frames for much more than calling a function.
    def local_frame_push(self, types):
        nbt = map(
            lambda t: (
                f"{t[0].name}: [{', '.join([str(Value(t[0], 0))] * t[1])}]"
            ),
            Type.count(types).items(),
        )
        self.execute(
            f"data modify storage wasm Locals append value "
            f"{{{', '.join(nbt)}}}"
        )

    # Drop the top local variable list.
    #
    # NOTE: Unlike the stack, this does not update the type list. So make sure
    # you don't rely on frames for much more than calling a function.
    def local_frame_drop(self):
        self.execute("data remove storage wasm Locals[-1]")

    # Reserve extra local variable space
    #
    # NOTE: Unlike the stack, this does not update the type list. So make sure
    # you don't rely on frames for much more than calling a function.
    def local_frame_reserve(self, types):
        for ty in types:
            self.execute(
                f"data modify storage wasm Locals[-1].{ty.name} append "
                f"value {Value(ty, 0)}"
            )

    # Get local
    def local_get(self, local_index):
        ty = self.types.locals[local_index]
        self.types.stack.append(ty)
        self.execute(
            f"data modify storage wasm Stack.{ty.name} append "
            f"from storage wasm Locals[-1].{ty.name}[{local_index}]"
        )

    # Set local
    def local_set(self, local_index):
        ty = self.types.stack[-1]
        assert ty == self.types.locals[local_index]
        self.execute(
            f"data modify storage wasm Locals[-1].{ty.name}[{local_index}] "
            f"set from storage wasm Stack.{ty.name}[-1]"
        )

    # Run a function
    def function(self, namespace, func):
        self.execute(f"function {namespace}:{func}")


class Stack:
    def __init__(self, cmd, name, types):
        self.cmd = cmd
        self.name = name
        self.types = types

    # Push a static value to the stack
    def push(self, value):
        self.types.append(value.type)
        self.cmd.execute(
            f"data modify storage wasm {self.name}.{value.tyname} "
            f"append value {value}"
        )

    # Discard the top of the stack
    def drop(self):
        ty = self.types.pop()
        self.cmd.execute(f"data remove storage wasm {self.name}.{ty.name}[-1]")

    # Copy the top level value from another stack
    def push_from(self, other):
        ty = other.types[-1]
        self.types.append(ty)
        self.cmd.execute(
            f"data modify storage wasm {self.name}.{ty.name} append from "
            f"storage wasm {other.name}.{ty.name}[-1]"
        )

    # Set the top value of the stack
    def set(self, value):
        value = value.cast(self.types[-1])
        self.cmd.execute(
            f"data modify storage wasm {self.name}.{value.tyname}[-1] "
            f"set value {value}"
        )

    # Copy the top level value to another stack, and assign it in-place
    def set_from(self, other):
        if self.types[-1] == other.types[-1]:
            self.drop()
            self.push_from(other)
        else:
            ty = self.types[-1]
            self.cmd.execute(
                f"data modify storage wasm {self.name}.{ty.name}[-1] set from "
                f"storage wasm {other.name}.{ty.name}[-1]"
            )

    # Load a value from the stack to the scoreboard, where the index is an
    # offset from the top of the stack.
    def load_to_scoreboard(self, score):
        ty = self.types[-1]
        with self.cmd.execute_param(f"store result score {score} wasm"):
            self.cmd.execute(
                f"data get storage wasm {self.name}.{ty.name}[-1]"
            )

    # Load a value from the scoreboard to the stack, where the index is an
    # offset from the top of the stack.
    def load_from_scoreboard(self, score):
        ty = self.types[-1]
        with self.cmd.execute_param(
                f"store result storage wasm {self.name}.{ty.name}[-1] "
                f"{ty.mc_name} 1"
        ):
            self.cmd.execute(f"scoreboard players get {score} wasm")

    # Run a mathematical operation on the top two values on the stack
    def operation(self, op):
        # Note: Since it's a stack we want to grab the second operand first!
        self.load_to_scoreboard("rhs")
        self.drop()
        self.load_to_scoreboard("lhs")

        ty = self.types[-1]
        with self.cmd.execute_param(
                f"store result storage wasm {self.name}.{ty.name}[-1] "
                f"{ty.mc_name} 1"
        ):
            self.cmd.execute(
                f"scoreboard players operation lhs wasm {op} rhs wasm"
            )
