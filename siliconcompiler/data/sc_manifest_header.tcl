#############################################
#!!!! AUTO-GENERATED FILE. DO NOT EDIT!!!!!!
#############################################

#############################################
# Convenience helper functions
#############################################

proc sc_top {} {
    # Refer to global sc_cfg dictionary
    global sc_cfg

    set sc_entrypoint [dict get $sc_cfg option entrypoint]
    if {$sc_entrypoint == ""} {
        return [dict get $sc_cfg design]
    }
    return $sc_entrypoint
}

proc has_task_param { param var } {
    global sc_cfg
    global sc_tool
    global sc_task

    return [dict exists $sc_cfg tool $sc_tool task $sc_task $param $var]
}

proc get_task_param { param var } {
    global sc_cfg
    global sc_tool
    global sc_task

    return [dict get $sc_cfg tool $sc_tool task $sc_task $param $var]
}

#############################################
# SCHEMA
#############################################
