###########################
# Core physical design files.
###########################
write_db "outputs/${sc_design}.odb"
write_sdc "outputs/${sc_design}.sdc"

write_def "outputs/${sc_design}.def"
write_verilog -include_pwr_gnd "outputs/${sc_design}.vg"

###########################
# Automated post-task design screenshot.
###########################
gui::show "source $sc_refdir/sc_screenshot.tcl" false
