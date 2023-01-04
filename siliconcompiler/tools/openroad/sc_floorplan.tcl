########################################################
# FLOORPLANNING
########################################################

# Functon adapted from OpenROAD:
# https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/ca3004b85e0d4fbee3470115e63b83c498cfed85/flow/scripts/macro_place.tcl#L26
proc design_has_macros {} {
  set db [::ord::get_db]
  set block [[$db getChip] getBlock]
  foreach inst [$block getInsts] {
    set inst_master [$inst getMaster]

    # BLOCK means MACRO cells
    if { [string match [$inst_master getType] "BLOCK"] } {
        return true
    }
  }
  return false
}

# Auto-generate floorplan if not defined yet
if {[expr ! [dict exists $sc_cfg "input" "floorplan.def"]]} {

    #########################
    #Init Floorplan
    #########################
    #NOTE: assuming a two tuple value as lower left, upper right
    set sc_diearea   [dict get $sc_cfg asic diearea]
    set sc_corearea  [dict get $sc_cfg asic corearea]
    set sc_diesize "[lindex $sc_diearea 0] [lindex $sc_diearea 1]"
    set sc_coresize "[lindex $sc_corearea 0] [lindex $sc_corearea 1]"

    initialize_floorplan -die_area $sc_diesize \
	-core_area $sc_coresize \
	-site $sc_site

    ###########################
    # Track Creation
    ###########################

    set metal_list ""
    dict for {key value} [dict get $sc_cfg pdk $sc_pdk grid $sc_stackup] {
	lappend metal_list $key
    }

    # source tracks from file if found, else else use schema entries
    if [dict exists $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype tracks] {
	source [lindex [dict get $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype tracks]]
    } else {
	make_tracks
    }

    ###########################
    # Automatic Pin Placement
    ###########################
    if [dict exists $sc_cfg tool $sc_tool var $sc_step $sc_index pin_thickness_h] {
        set h_mult [lindex [dict get $sc_cfg tool $sc_tool var $sc_step $sc_index pin_thickness_h] 0]
        set_pin_thick_multiplier -hor_multiplier $h_mult
    }
    if [dict exists $sc_cfg tool $sc_tool var $sc_step $sc_index pin_thickness_v] {
        set v_mult [lindex [dict get $sc_cfg tool $sc_tool var $sc_step $sc_index pin_thickness_v] 0]
        set_pin_thick_multiplier -ver_multiplier $v_mult
    }

    place_pins -hor_layers $sc_hpinmetal \
	-ver_layers $sc_vpinmetal \
	-random \

    # Set macro placements specified in the schema early, so that the following automatic
    # floorplanning commands will not move them.
    if [dict exists $sc_cfg asic var] {
        dict for {key value} [dict get $sc_cfg asic var] {
            set mp_len [string length macroplace_]
            set mp_pre [string range $key 0 $mp_len-1]
            set mp_post [string range $key $mp_len end]
            if [string equal $mp_pre macroplace_] {
                set macro_loc [dict get $sc_cfg asic var $key location]
                set macro_rot [dict get $sc_cfg asic var $key rotation]
                place_cell -inst_name $mp_post -origin $macro_loc -orient $macro_rot -status FIRM
            }
        }
    }

    # Need to check if we have any macros before performing macro placement,
    # since we get an error otherwise.
    if {[design_has_macros] || \
        [dict exists $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype macroplace]} {
        ###########################
        # TDMS Placement
        ###########################

        global_placement -density $openroad_place_density \
            -pad_left $openroad_pad_global_place \
            -pad_right $openroad_pad_global_place

        ###########################
        # Macro placement
        ###########################

        if [dict exists $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype macroplace] {
            # Manual macro placement
            source [lindex [dict get $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype macroplace] 0]
        } else {
            macro_placement \
                -halo $openroad_macro_place_halo \
                -channel $openroad_macro_place_channel
        }

        # Note: some platforms set a "macro blockage halo" at this point, but the
        # technologies we support do not, so we don't include that step for now.
    }

    ###########################
    # Power Network (not good)
    ###########################
    #pdngen $::env(PDN_CFG) -verbose

} else {
    ###########################
    # Add power nets
    ###########################
    set block [ord::get_db_block]
    foreach pin $sc_pins {
        if {[set net [$block findNet $pin]] == "NULL"} {
            set type [dict get $sc_cfg datasheet $sc_design pin $pin type global]
            if {$type == "power" || $type == "ground"} {
                set net [odb::dbNet_create $block $pin]
                $net setSpecial
                $net setSigType [string toupper $type]
            }
        }
    }

    ###########################
    # Initialize floorplan
    ###########################
    set def [dict get $sc_cfg "input" "floorplan.def"]
    read_def -floorplan_initialize $def

    if [dict exists $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype macroplace] {
        ###########################
        # TDMS Placement
        ###########################
        global_placement -density $openroad_place_density \
            -pad_left $openroad_pad_global_place \
            -pad_right $openroad_pad_global_place

        ###########################
        # Manual macro placement
        ###########################
        source [lindex [dict get $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype macroplace] 0]
    }
}

###########################
# Power Network (if defined)
###########################
if [dict exists $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype pdngen] {
    source [lindex [dict get $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype pdngen] 0]
}

###########################
# Tap Cells
###########################

if [dict exists $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype tapcells] {
    source [lindex [dict get $sc_cfg pdk $sc_pdk aprtech openroad $sc_stackup $sc_libtype tapcells] 0]
}

remove_buffers
