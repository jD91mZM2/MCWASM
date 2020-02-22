(module
  (func $fadd (param $lhs f32) (param $rhs f32) (result f32)
    local.get $lhs
    local.get $rhs
    f32.add)
  (export "fadd" (func $fadd)))
