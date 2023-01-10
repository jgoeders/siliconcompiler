from macros import bit_and, bit_or
import os
import siliconcompiler

def main():
    # Configure a Chip object for the top-level design.
    andor_chip = siliconcompiler.Chip('andor')
    andor_chip.set('input', 'verilog', 'src/andor.v')
    #andor_chip.set('input', 'sdc', 'src/logic.sdc')
    #andor_chip.load_target('freepdk45_demo')
    andor_chip.load_target('skywater130_demo')
    #andor_chip.set('asic', 'diearea', [(0.0, 0.0), (13.0, 20.0)])
    #andor_chip.set('asic', 'corearea', [(0.5, 0.5), (12.5, 19.5)])
    andor_chip.set('asic', 'diearea', [(0.0, 0.0), (70.0, 70.0)])
    andor_chip.set('asic', 'corearea', [(2.0, 2.72), (68.0, 67.28)])
    # (The macro areas count as utilized space, and this example has minimal top-level logic)
    andor_chip.set('tool', 'openroad', 'var', 'floorplan', '0', 'place_density', ['0.6'])
    andor_chip.set('tool', 'openroad', 'var', 'place', '0', 'place_density', ['0.6'])
    andor_chip.set('tool', 'openroad', 'var', 'route', '0', 'grt_allow_congestion', ['true'])

    # Build the macro designs. (Optional if already done)
    bit_and.build()
    bit_or.build()

    # Add the macro package directories to the search path.
    new_scpath = os.environ['SCPATH'].split(os.pathsep) if 'SCPATH' in os.environ else []
    new_scpath.append(os.path.abspath("macros/bit_or/pkg/"))
    new_scpath.append(os.path.abspath("macros/bit_and/pkg/"))
    os.environ['SCPATH'] = os.pathsep.join(new_scpath)

    # Import the macros.
    # TODO: Find a way to integrate '[macro].setup()' with existing 'setup_[tool|lib|pdk]' methodology,
    # to automate these calls and delay their execution until later in the flow (for remote/etc).
    bit_and.setup(andor_chip)
    bit_or.setup(andor_chip)

    # Place the macros.
    andor_chip.place_macro('and_macro', 'bit_and', (1.5, 2.72), 'R0')
    andor_chip.place_macro('or_macro', 'bit_or', (35.5, 35.36), 'R0')

    # Build the top-level design.
    andor_chip.run()

    # Summarize/show the top-level design.
    andor_chip.summary()
    andor_chip.show()

if __name__ == '__main__':
    main()
