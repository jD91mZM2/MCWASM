(module
  ;; Types seem to be automagically generated when assembling, but I'm including them here just to
  ;; really understand how everything works.
  (type $add_t (func (param i32 i32) (result i32)))

  (func $add (type $add_t) (param $lhs i32) (param $rhs i32) (result i32)
    local.get $lhs ;; push value to stack
    local.get $rhs ;; push value to stack
    i32.add)       ;; pop both values, push back sum

  (func $sub (param $lhs i32) (param $rhs i32) (result i32)
    local.get $lhs
    local.get $rhs
    i32.sub)

  (func $double_impl (param $n i32) (result i32)
    local.get $n
    local.get $n
    call $add)

  (export "add" (func $add))
  (export "sub" (func $sub))
  (export "double" (func $double_impl)))
