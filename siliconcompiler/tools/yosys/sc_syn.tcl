###############################
# Reading SC Schema
###############################

source ./sc_manifest.tcl

yosys echo on

###############################
# Schema Adapter
###############################

set sc_tool   yosys
set sc_step   [dict get $sc_cfg arg step]
set sc_index  [dict get $sc_cfg arg index]
set sc_flow   [dict get $sc_cfg option flow]
set sc_task   [dict get $sc_cfg flowgraph $sc_flow $sc_step $sc_index task]
set sc_refdir [dict get $sc_cfg tool $sc_tool task $sc_task refdir]

####################
# DESIGNER's CHOICE
####################

set sc_design      [sc_top]
set sc_mode        [dict get $sc_cfg option mode]
set sc_flow        [dict get $sc_cfg option flow]
set sc_optmode     [dict get $sc_cfg option optmode]
set sc_pdk         [dict get $sc_cfg option pdk]

########################################################
# Design Inputs
########################################################

# TODO: the original OpenFPGA synth script used read_verilog with -nolatches. Is
# that a flag we might want here?

# If UHDM, ilang, or Verilog inputs exist, read them in (this allows mixed
# inputs in designs). UHDM requires a version of Yosys built with this support.

set read_verilog_args [list "-sv"]
if {$sc_task eq "syn_vpr"} {
    #TODO: the nolatches option can be a flag set by the user depending on the input arch file
    lappend read_verilog_args "-nolatches"
}

if { [file exists "inputs/$sc_design.uhdm"] } {
    yosys read_uhdm "inputs/$sc_design.uhdm"
} elseif { [file exists "inputs/$sc_design.ilang"] } {
    yosys read_ilang "inputs/$sc_design.ilang"
} elseif { [file exists "inputs/$sc_design.v"] } {
    yosys read_verilog {*}$read_verilog_args "inputs/$sc_design.v"
} else {
    foreach idir [dict get $sc_cfg option idir] {
        lappend read_verilog_args "-I${idir}"
    }
    foreach def [dict get $sc_cfg option define] {
        lappend read_verilog_args "-D${def}"
    }
    foreach vfile [dict get $sc_cfg input rtl verilog] {
        yosys read_verilog -defer {*}$read_verilog_args $vfile
    }
}

########################################################
# Override top level parameters
########################################################

yosys chparam -list
if {[dict exists $sc_cfg option param]} {
    dict for {key value} [dict get $sc_cfg option param] {
	if !{[string is integer $value]} {
	    set value [concat \"$value\"]
	}
	yosys chparam -set $key $value $sc_design
   }
}

yosys hierarchy -check -top $sc_design

########################################################
# Synthesis based on mode
########################################################

if {$sc_mode eq "fpga"} {
    source "$sc_refdir/syn_fpga.tcl"
} else {
    source "$sc_refdir/syn_asic.tcl"
}

########################################################
# Write Netlist
########################################################
yosys write_verilog -noattr -noexpr -nohex -nodec "outputs/$sc_design.vg"
if {$sc_mode eq "fpga"} {
    yosys write_blif "outputs/$sc_design.blif"
    yosys write_json "outputs/${sc_design}_netlist.json"
}
