
from siliconcompiler.tools.klayout.klayout import setup as setup_tool

def setup(chip):
    '''
    Generate a GDSII file from an input DEF file
    '''

    # Generic tool setup.
    setup_tool(chip)

    tool = 'klayout'
    refdir = 'tools/'+tool
    step = chip.get('arg','step')
    index = chip.get('arg','index')
    task = 'export'
    clobber = False

    script = 'klayout_export.py'
    option = ['-b', '-r']
    chip.set('tool', tool, 'task', task, 'script', script, step=step, index=index, clobber=clobber)
    chip.set('tool', tool, 'task', task, 'option', option, step=step, index=index, clobber=clobber)

    targetlibs = chip.get('asic', 'logiclib', step=step, index=index)
    stackup = chip.get('option', 'stackup')
    pdk = chip.get('option', 'pdk')
    if bool(stackup) & bool(targetlibs):
        macrolibs = chip.get('asic', 'macrolib', step=step, index=index)

        chip.add('tool', tool, 'task', task, 'require', ",".join(['asic', 'logiclib']), step=step, index=index)
        chip.add('tool', tool, 'task', task, 'require', ",".join(['option', 'stackup']), step=step, index=index)
        chip.add('tool', tool, 'task', task, 'require',  ",".join(['pdk', pdk, 'layermap', 'klayout', 'def','gds', stackup]), step=step, index=index)

        for lib in (targetlibs + macrolibs):
            chip.add('tool', tool, 'task', task, 'require', ",".join(['library', lib, 'output', stackup, 'gds']), step=step, index=index)
            chip.add('tool', tool, 'task', task, 'require', ",".join(['library', lib, 'output', stackup, 'lef']), step=step, index=index)
    else:
        chip.error(f'Stackup and targetlib paremeters required for Klayout.')

    # Input/Output requirements for default flow
    design = chip.top()
    if (not chip.valid('input', 'layout', 'def') or
        not chip.get('input', 'layout', 'def', step=step, index=index)):
        chip.add('tool', tool, 'task', task, 'input', design + '.def', step=step, index=index)
    chip.add('tool', tool, 'task', task, 'output', design + '.gds', step=step, index=index)

    # Export GDS with timestamps by default.
    chip.set('tool', tool, 'task', task, 'var', 'timestamps', 'true', step=step, index=index, clobber=False)
    chip.set('tool', tool, 'task', task, 'var', 'timestamps', 'Export GDSII with timestamps', field='help')
