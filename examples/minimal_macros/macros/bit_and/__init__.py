import os
import shutil
import siliconcompiler

macro_top = 'bit_and'

def build():
    # Move into the macro directory to build/package the design.
    cur_dir = os.getcwd()
    os.chdir(os.path.dirname(__file__))

    # Configure a Chip object for the 1-bit and gate.
    and_chip = siliconcompiler.Chip(macro_top)
    and_chip.set('input', 'verilog', 'src/and.v')
    #and_chip.set('input', 'sdc', 'src/and.sdc')
    #and_chip.load_target('freepdk45_demo')
    and_chip.load_target('skywater130_demo')
    #and_chip.set('asic', 'diearea', [(0.0, 0.0), (7.0, 7.0)])
    #and_chip.set('asic', 'corearea', [(1.0, 1.0), (6.0, 6.0)])
    and_chip.set('asic', 'diearea', [(0.0, 0.0), (30.0, 30.0)])
    and_chip.set('asic', 'corearea', [(1.0, 2.72), (29.0, 27.28)])
    and_chip.set('tool', 'openroad', 'var', 'place', '0', 'place_density', ['0.6'])
    and_chip.set('option', 'quiet', True)

    # Sky130: Only route on met1-met3, to leave room for a power grid.
    stackup = and_chip.get('asic', 'stackup')
    and_chip.set('asic', 'maxlayer', 'met3')

    # Build and print a summary
    and_chip.run()
    and_chip.summary()
    #and_chip.show()

    # Package the minimal build artifacts needed to pull the hard IP block into another design.
    build_job_dir = 'build/bit_and/job0'
    pkg_dir = 'pkg'
    os.makedirs(pkg_dir, exist_ok=True)
    shutil.copy2(f'{build_job_dir}/bit_and.pkg.json',             f'{pkg_dir}/bit_and.pkg.json')
    shutil.copy2(f'{build_job_dir}/export/0/inputs/bit_and.lef',  f'{pkg_dir}/bit_and.lef')
    shutil.copy2(f'{build_job_dir}/export/0/outputs/bit_and.gds', f'{pkg_dir}/bit_and.gds')
    # TODO: Include blackbox as unused file during first build?
    shutil.copy2(f'{build_job_dir}/../../../src/and.bb.v', f'{pkg_dir}/and.bb.v')

    # Return to previous working directory.
    os.chdir(cur_dir)

# Smart path resolution supporting env var separators.
# TODO: Move to schema or change how Chip._resolve_env_vars() works?
def scpath_resolve(pth):
    return shutil.which(pth, mode = os.R_OK, path = os.environ['SCPATH'])

def setup(top_chip):
    # Create a library schema from the macro build artifacts.
    macro_chip = siliconcompiler.Chip(macro_top)
    macro_chip.read_manifest(scpath_resolve(f'{macro_top}.pkg.json'))
    stackup = macro_chip.get('asic', 'stackup')
    macro_chip.set('model', 'layout', 'lef', stackup, scpath_resolve('bit_and.lef'))
    macro_chip.set('model', 'layout', 'gds', stackup, scpath_resolve('bit_and.gds'))

    top_chip.add('asic', 'macrolib', macro_top)
    top_chip.import_library(macro_chip)
    top_chip.add('input', 'verilog', scpath_resolve('and.bb.v'))
