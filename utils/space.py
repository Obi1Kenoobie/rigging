import maya.cmds as cmds

from rigging.utils import attribute, connect
from rigging.utils.math import get_matrix
from rigging.utils.common import get_parent, create_node


conn_dict = {'type' : 'space',
             'attributes' : [],
             'nodes' :[]}

def add_space(dag_node, space_drivers=[], space_names=[], attr_obj=None, split_channels=False, store=False):
    if not attr_obj:
        attr_obj = dag_node
    
    space_drivers = list(space_drivers)
    
    space_names = list(space_names)
    conn_dict['attributes'] = [dag_node, space_drivers, space_names, attr_obj, split_channels, store]
    
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

    conn_dict['nodes'].extend(decomp_nodes)
    conn_dict['nodes'].extend(blends)

    attribute.add_header_attribute(attr_obj, 'SPACES')
    for i, space in enumerate(space_names):
        space_transform = create_node('transform', dag_node, parent=parent, matrix=matrix, add_to_tags=space, suffix='SPACE')
        conn_dict['nodes'].append(space_transform)
        connect.matrix_constraint(space_drivers[i], space_transform, attr='rt')
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
    
    if store:
        attribute.set_attribute_dict(dag_node, 'space_dict', conn_dict)


def rebuild_space(conn_dict, isStorable=True):
    cmds.delete(conn_dict['nodes'])

    add_space(conn_dict['attributes'][0], 
              conn_dict['attributes'][1], 
              conn_dict['attributes'][2], 
              conn_dict['attributes'][3], 
              conn_dict['attributes'][4], 
              isStorable)
