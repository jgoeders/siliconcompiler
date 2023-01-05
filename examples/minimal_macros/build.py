from macros import bit_and, bit_or
import os
import siliconcompiler

def main():
    # Configure a Chip object for the top-level design.
    andor_chip = siliconcompiler.Chip('andor')
    andor_chip.set('input', 'verilog', 'src/andor.v')
    andor_chip.set('input', 'sdc', 'src/logic.sdc')
    andor_chip.load_target('freepdk45_demo')
    andor_chip.set('asic', 'diearea', [(0.0, 0.0), (13.0, 20.0)])
    andor_chip.set('asic', 'corearea', [(0.5, 0.5), (12.5, 19.5)])
    # (The macro areas count as utilized space, and this example has minimal top-level logic)
    andor_chip.set('tool', 'openroad', 'var', 'floorplan', '0', 'place_density', ['0.6'])
    andor_chip.set('tool', 'openroad', 'var', 'place', '0', 'place_density', ['0.6'])

    # [Re-]build the macro designs.
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
    andor_chip.place_macro('and_macro', 'bit_and', (0.5, 0.5), 'R0')
    andor_chip.place_macro('or_macro', 'bit_or', (5.5, 12.5), 'R0')

    # Build the top-level design.
    andor_chip.run()

    # Summarize/show the top-level design.
    andor_chip.summary()
    andor_chip.show()

if __name__ == '__main__':
    main()
