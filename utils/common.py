import maya.cmds as cmds
import re

from rigging.utils import globals, math
from rigging.utils.name import Name



def get_parent(dag_node, **kwargs):
    parent = cmds.listRelatives(dag_node, parent=True, **kwargs)
    if parent:
        return parent[0]


def get_children(dag_node, **kwargs):
    return cmds.listRelatives(dag_node, children=True, **kwargs)


def get_shapes(dag_node, **kwargs):
    return cmds.listRelatives(dag_node, shapes=True, **kwargs)


def get_shape(dag_node, **kwargs):
    return cmds.listRelatives(dag_node, shapes=True, **kwargs)[0]


def get_override_color(dag_node, asString=False):
    if cmds.objectType(dag_node) in globals.OVERRIDE_TYPES:
        if cmds.getAttr(dag_node + '.overrideEnabled'):
            color = cmds.getAttr(dag_node + '.overrideColor')
            if color in globals.COLOR_INDEX and asString:
                color = globals.COLOR_INDEX_TO_STR[color]
            return color
        elif cmds.getAttr(dag_node + '.overrideRGBColors'):
            return cmds.getAttr(dag_node + '.overrideColorRGB')
        else:
            return None


def set_override_color(dag_node, color=None, rgb_color=None):
    if isinstance(color, str) and color in globals.COLOR_STR:
        color = globals.COLOR_STR_TO_INDEX[color]

    if cmds.objectType(dag_node) in globals.OVERRIDE_TYPES:
        cmds.setAttr(dag_node + '.overrideEnabled', True)
        cmds.setAttr(dag_node + '.overrideColor', color)
    
    if isinstance(rgb_color, list) and len(rgb_color) == 3:
        cmds.setAttr(dag_node + '.overrideRGBColors', True)
        cmds.setAttr(dag_node + '.overrideColorRGB', rgb_color[0], rgb_color[1], rgb_color[2])


def create_node(node_type, name, matrix=None, parent=None, use_offset_matrix=False, syntax_list=None, add_to_suffix=None, add_to_tags=None, suffix=None):
    node_name = _generate_suffix(name, syntax_list, add_to_tags, suffix, node_type, add_to_suffix)
            
    node = cmds.createNode(node_type)
    if 'Shape' in node:
        node = get_parent(node)
    node = cmds.rename(node, node_name)
    if cmds.objectType(node, isType='transform'):
        if parent:
            cmds.parent(node, parent, relative=True)
        if matrix:
            if use_offset_matrix:
                math.set_offset_parent_matrix(node, matrix)
            else:
                math.set_matrix(node, matrix)
    return node


def _generate_suffix(name, syntax_list, add_to_tags, suffix, node_type, add_to_suffix):
    """returns name and shape-suffix as list

    Args:
        name (str): name of a node
        add_to_tags (str|None): additional tags
        suffix (str|None): suffix
        node_type (str): node_type of node
        add_to_suffix (str|None): additional suffix

    Returns:
       str: name
    """
    
    if not suffix:
        suffix=globals.NODES_SUFFIX[node_type]
    namer = Name(name, add_to_tags=add_to_tags, add_to_suffix=add_to_suffix, suffix=suffix)
    name = namer.create_name(syntax_list=syntax_list)
    return name


def zero(dag_node, translation=True, rotation=True):
    if translation:
        cmds.xform(dag_node, translation=[0.0, 0.0, 0.0])
    if rotation:
        cmds.xform(dag_node, rotation=[0.0, 0.0, 0.0])
