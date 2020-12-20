import maya.cmds as cmds

from rigging.utils import attribute, connect
from rigging.utils.math import get_matrix
from rigging.utils.common import get_parent, create_node


def add_space(dag_node, space_drivers=[], space_names=[], attr_obj=None, split_channels=False):
    if not attr_obj:
        attr_obj = dag_node
    
    if not len(space_drivers) == len(space_names):
        return cmds.warning('You need to provide the same number of space drivers and space names')

    matrix = get_matrix(dag_node)
    parent = get_parent(dag_node)
    
    decomp_nodes = []
    blends = []
    if split_channels:
        blends.append(create_node('blendMatrix', dag_node, add_to_tags=['space', 'translate']))
        blends.append(create_node('blendMatrix', dag_node, add_to_tags=['space', 'rotate']))

        decomp_nodes.append(create_node('decomposeMatrix', dag_node, add_to_tags=['space', 'translate']))
        decomp_nodes.append(create_node('decomposeMatrix', dag_node, add_to_tags=['space', 'rotate']))
        
        cmds.connectAttr(blends[0] + '.outputMatrix', decomp_nodes[0] + '.inputMatrix')
        cmds.connectAttr(blends[1] + '.outputMatrix', decomp_nodes[1] + '.inputMatrix')
        cmds.connectAttr(decomp_nodes[0] + '.outputTranslate', dag_node + '.translate')
        cmds.connectAttr(decomp_nodes[1] + '.outputRotate', dag_node + '.rotate')
    else:
        blends.append(create_node('blendMatrix', dag_node, add_to_tags='space'))
        decomp_nodes.append(create_node('decomposeMatrix', dag_node, add_to_tags='space'))

        cmds.connectAttr(blends[0] + '.outputMatrix', decomp_nodes[0] + '.inputMatrix')
        cmds.connectAttr(decomp_nodes[0] + '.outputTranslate', dag_node + '.translate')
        cmds.connectAttr(decomp_nodes[0] + '.outputRotate', dag_node + '.rotate')
    
    attribute.add_header_attribute(dag_node, 'SPACES')
    for i, space in enumerate(space_names):
        space_transform = create_node('transform', space, parent=parent, matrix=matrix)
        space_transform = cmds.rename(space_transform, dag_node + '_' + space + '_SPACE')
        connect.matrix_constraint(space_drivers[i], space_transform)
        if split_channels:
            t_attr = attribute.add_blend_attribute(attr_obj, space + '_translate')
            r_attr = attribute.add_blend_attribute(attr_obj, space + '_rotate')
            cmds.connectAttr(attr_obj + '.{}'.format(t_attr), blends[0] + '.target[{}].weight'.format(i))
            cmds.connectAttr(attr_obj + '.{}'.format(r_attr), blends[1] + '.target[{}].weight'.format(i))
            cmds.connectAttr(space_transform + '.matrix', blends[0] + '.target[{}].targetMatrix'.format(i))
            cmds.connectAttr(space_transform + '.matrix', blends[1] + '.target[{}].targetMatrix'.format(i))
        else:
            attr = attribute.add_blend_attribute(attr_obj, space)
            cmds.connectAttr(attr_obj + '.{}'.format(attr), blends[0] + '.target[{}].weight'.format(i))
            cmds.connectAttr(space_transform + '.matrix', blends[0] + '.target[{}].targetMatrix'.format(i))