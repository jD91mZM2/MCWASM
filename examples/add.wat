(module
  ;; Types seem to be automagically generated when assembling, but I'm including them here just to
  ;; really understand how everything works.
  (type $add_t (func (param i32 i32) (result i32)))

  (func $add (type $add_t) (param $lhs i32) (param $rhs i32) (result i32)
    get_local $lhs ;; push value to stack
    get_local $rhs ;; push value to stack
    i32.add) ;; pop both values, push back sum
  (export "add" (func $add)))
