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

  ;; Returns 1 if $arg is "meaningful", aka if it's equal to 42.
  (func $meaningful (param $arg i32) (result i32)
    local.get $arg
    i32.const 42
    i32.eq
    if
      i32.const 1
      return
    end
    i32.const 0)

  ;; Returns 1 if $arg is "big", aka if it's over 9000.
  (func $big (param $arg i32) (result i32)
    local.get $arg
    i32.const 9000
    i32.gt_s
    if
      i32.const 1
      return
    end
    i32.const 0)

  (func $abs (param $val i32) (result i32)
    (local $return i32)
    local.get $val
    i32.const 0
    i32.lt_s
    if
      i32.const 0
      local.get $val
      i32.sub
      local.set $return
    else
      local.get $val
      local.set $return
    end
    local.get $return)

  (export "inv" (func $inv))
  (export "meaningful" (func $meaningful))
  (export "big" (func $big))
  (export "abs" (func $abs)))
