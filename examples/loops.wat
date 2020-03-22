;; Loops aren't actually supported yet. See README
(module
  (func $block (result i32)
    (local $result i32)
    block
      block
        i32.const 1
        local.set $result
        i32.const 2
        local.set $result
      end
      block
        br 1 ;; outer-most block
      end
      block
        i32.const 3
        local.set $result
        i32.const 4
        local.set $result
      end
    end
    local.get $result)

  (func $mul_recursive (param $coefficient i32) (param $term i32) (result i32)
    (local $result i32)
    i32.const 0
    local.set $result
    block
      local.get $coefficient
      i32.eqz
      br_if 0

      ;; result += term
      local.get $result
      local.get $term
      i32.add
      local.set $result

      ;; coefficient -= 1
      local.get $coefficient
      i32.const 1
      i32.sub
      local.tee $coefficient

      ;; result += mul_recursive(coefficient, term)
      local.get $term
      call $mul_recursive
      local.get $result
      i32.add
      local.set $result
    end
    (local.get $result))

  (func $mul (param $coefficient i32) (param $term i32) (result i32)
    (local $result i32)
    i32.const 0
    local.set $result
    block
      loop
        local.get $coefficient
        i32.eqz
        br_if 1 ;; block

        ;; result += term
        local.get $result
        local.get $term
        i32.add
        local.set $result

        ;; coefficient -= 1
        local.get $coefficient
        i32.const 1
        i32.sub
        local.set $coefficient

        br 0 ;; loop - this shouldn't actually be necessary and will be fixed
      end
    end
    (local.get $result))

  (export "block" (func $block))
  (export "mul_recursive" (func $mul_recursive))
  (export "mul" (func $mul)))
