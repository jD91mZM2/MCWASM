(module
  (func $fac (param $n i32) (result i32)
    local.get $n
    i32.eqz
    if
      i32.const 1
      return
    end

    local.get $n ;; [n]
    i32.const 1  ;; [n, 1]
    i32.sub      ;; [n-1]

    call $fac    ;; [fac(n-1)]

    local.get $n ;; [n-1, n]
    i32.mul)     ;; [fac(n-1) * n]

  (func $fib (param $n i32) (result i32)
    local.get $n
    i32.const 2
    i32.lt_s
    if
      i32.const 1
      return
    end

    ;; fib(n-1)
    local.get $n
    i32.const 1
    i32.sub
    call $fib

    ;; fib(n-2)
    local.get $n
    i32.const 2
    i32.sub
    call $fib

    i32.add)

  (export "fac" (func $fac))
  (export "fib" (func $fib)))
