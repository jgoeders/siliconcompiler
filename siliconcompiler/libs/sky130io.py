import os
import siliconcompiler

def setup(chip):
    '''
    Skywater130 I/O library.
    '''
    process = 'skywater130'
    libname = 'sky130io'
    stackup = '5M1LI'
    corner = 'typical'

    lib = siliconcompiler.Library(chip, libname)

    libdir = os.path.join('..',
                          'third_party',
                          'pdks',
                          'skywater',
                          process,
                          'libs',
                          libname,
                          'v0_0_2',
                          'io')

    # pdk
    lib.set('option', 'pdk', 'skywater130')

    lib.set('output', corner, 'nldm', os.path.join(libdir, 'sky130_dummy_io.lib'))
    lib.set('output', stackup, 'lef', os.path.join(libdir, 'sky130_ef_io.lef'))

    # Need both GDS files: ef relies on fd one
    lib.add('output', stackup, 'gds', os.path.join(libdir, 'sky130_ef_io.gds'))
    lib.add('output', stackup, 'gds', os.path.join(libdir, 'sky130_fd_io.gds'))
    lib.add('output', stackup, 'gds', os.path.join(libdir, 'sky130_ef_io__gpiov2_pad_wrapped.gds'))

    return lib

#########################
if __name__ == "__main__":
    lib = setup(siliconcompiler.Chip('<lib>'))
    lib.write_manifest(f'{lib.top()}.json')
