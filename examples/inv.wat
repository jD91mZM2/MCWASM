(module
  ;; Returns 1 if $arg is zero, otherwise 0.
  (func $inv (param $arg i32) (result i32)
    local.get $arg
    i32.eqz
    if
      i32.const 1
      return
    end
    i32.const 0)
  (export "inv" (func $inv)))
