#############################################
# Convenience variables from the schema 
#############################################

proc _set_param { param key } {
  global sc_cfg
  puts [dict exists $sc_cfg $key]
  if { [dict exists $sc_cfg {*}$key] } {
    upvar $param sc_var
    set sc_var [dict get $sc_cfg {*}$key]
    return 1
  }
  return 0
}

set sc_design    [sc_top]

# Arg
set sc_step      [dict get $sc_cfg arg step]
set sc_index     [dict get $sc_cfg arg index]

# Flow
set sc_flow      [dict get $sc_cfg option flow]
set sc_jobname   [dict get $sc_cfg option jobname]
set sc_mode      [dict get $sc_cfg option mode]

# Tool / task specific
if {[_set_param sc_tool "flowgraph $sc_flow $sc_step $sc_index tool"] &&
    [_set_param sc_task "flowgraph $sc_flow $sc_step $sc_index task"] } {
  _set_param sc_refdir "tool $sc_tool task $sc_task refdir"
  _set_param sc_threads "tool $sc_tool task $sc_task threads"
}

# Options
set sc_optmode   [dict get $sc_cfg option optmode]
set sc_uselambda [dict get $sc_cfg option uselambda]
set sc_pdk       [dict get $sc_cfg option pdk]
set sc_stackup   [dict get $sc_cfg option stackup]

# Remove helper proc
rename _set_param ""
