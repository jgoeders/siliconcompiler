import siliconcompiler
chip = siliconcompiler.Chip('doe_demo')

syn_strategies = ['DELAY0', 'DELAY1', 'DELAY2', 'DELAY3', 'AREA0', 'AREA1', 'AREA2']

flow = 'synparallel'
chip.node(flow, 'import', 'surelog', 'import')
for index in range(len(syn_strategies)):
    chip.node(flow, 'syn', 'yosys', 'syn_asic', index=str(index))
    chip.edge(flow, 'import', 'syn', head_index=str(index))
    chip.edge(flow, 'syn', 'synmin', tail_index=str(index))
    chip.set('tool', 'yosys', 'var', 'syn', str(index), 'strategy', syn_strategies[index])
    for metric in ('cellarea', 'peakpower', 'standbypower'):
        chip.set('flowgraph', flow, 'syn', str(index), 'weight', metric, 1.0)
chip.node(flow, 'synmin', 'builtin', 'minimum')
chip.set('option', 'flow', flow)
chip.write_flowgraph("flowgraph_doe.svg")
