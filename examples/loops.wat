;; Loops aren't actually supported yet. See README
(module
  (func $mul (param $coefficient i32) (param $term i32) (result i32)
    (local $result i32)
    block  ;; label 0
      loop ;; label 1
        local.get $coefficient
        i32.eqz
        br_if 1

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

        br 0
      end
    end
    (local.get $result))
  (export "mul" (func $mul)))
