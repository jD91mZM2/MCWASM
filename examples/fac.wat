(module
  (func $fac (param $n i32) (result i32)
    local.get $n
    if
      i32.const 1
      return
    end

    local.get $n ;; [n]
    i32.const 1  ;; [n, 1]
    i32.sub      ;; [n-1]

    local.get $n ;; [n-1, n]
    call $fac    ;; [fac(n-1), n]
    i32.mul)     ;; [fac(n-1) * n]

  (export "fac" (func $fac)))
