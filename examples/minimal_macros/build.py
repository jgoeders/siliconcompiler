import siliconcompiler

def main():
    # Configure a Chip object for the 1-bit and gate.
    and_chip = siliconcompiler.Chip('bit_and')
    and_chip.set('input', 'verilog', 'src/and.v')
    and_chip.set('input', 'sdc', 'src/logic.sdc')
    and_chip.load_target('freepdk45_demo')
    and_chip.set('asic', 'diearea', [(0,0), (20, 20)])
    and_chip.set('asic', 'corearea', [(1,1), (19, 19)])
    and_chip.set('option', 'quiet', True)

    # Configure a Chip object for the 1-bit or gate.
    or_chip = siliconcompiler.Chip('bit_or')
    or_chip.set('input', 'verilog', 'src/or.v')
    or_chip.set('input', 'sdc', 'src/logic.sdc')
    or_chip.load_target('freepdk45_demo')
    or_chip.set('asic', 'diearea', [(0,0), (20, 20)])
    or_chip.set('asic', 'corearea', [(1,1), (19, 19)])
    or_chip.set('option', 'quiet', True)

    # Setup pointers to the final results, so the results can be imported easily.
    # TODO: Get these file paths from the schema?
    stackup = and_chip.get('asic', 'stackup')
    and_chip.set('model', 'layout', 'lef', stackup, 'build/bit_and/job0/export/0/inputs/bit_and.lef')
    and_chip.set('model', 'layout', 'gds', stackup, 'build/bit_and/job0/export/0/outputs/bit_and.gds')
    or_chip.set('model', 'layout', 'lef', stackup, 'build/bit_or/job0/export/0/inputs/bit_or.lef')
    or_chip.set('model', 'layout', 'gds', stackup, 'build/bit_or/job0/export/0/outputs/bit_or.gds')

    # Build both designs, and display a summary.
    and_chip.run()
    or_chip.run()

    and_chip.summary()
    or_chip.summary()

    # Uncomment to open the GDS results in KLayout.
    #and_chip.show()
    #or_chip.show()

    # Configure a Chip object for the top-level design.
    andor_chip = siliconcompiler.Chip('andor')
    andor_chip.set('input', 'verilog', 'src/andor.v')
    andor_chip.set('input', 'sdc', 'src/logic.sdc')
    andor_chip.load_target('freepdk45_demo')
    andor_chip.set('asic', 'diearea', [(0,0), (80, 80)])
    andor_chip.set('asic', 'corearea', [(1,1), (79, 79)])

    # Load macros, and place the instances.
    andor_chip.load_macro('bit_and', 'build/bit_and/job0')
    andor_chip.load_macro('bit_or', 'build/bit_or/job0')
    andor_chip.place_macro('and_macro', 'bit_and', (10.0, 10.0), 'R0')
    andor_chip.place_macro('or_macro', 'bit_or', (40.0, 40.0), 'R0')
    # (Blackbox file required for yosys synthesis, else it errors out on missing module definitions)
    andor_chip.add('input', 'verilog', 'src/and.bb.v')
    andor_chip.add('input', 'verilog', 'src/or.bb.v')

    andor_chip.run()
    andor_chip.summary()

    andor_chip.show()

if __name__ == '__main__':
    main()
