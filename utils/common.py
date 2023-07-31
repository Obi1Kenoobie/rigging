import maya.cmds as cmds
import re

from rigging.utils import globals, math


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
        else:
            return None


def set_override_color(dag_node, color=None):
    if isinstance(color, basestring) and color in globals.COLOR_STR:
        color = globals.COLOR_STR_TO_INDEX[color]

    if cmds.objectType(dag_node) in globals.OVERRIDE_TYPES:
        cmds.setAttr(dag_node + '.overrideEnabled', True)
        cmds.setAttr(dag_node + '.overrideColor', color)


def create_node(node_type, name, matrix=None, parent=None, use_offset_matrix=False, add_to_suffix=None, add_to_tags=None, suffix=None):
    node_name = _generate_suffix(name, add_to_tags, suffix, node_type, add_to_suffix)
    if cmds.objExists(node_name):
        return node_name
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


def _generate_suffix(name, add_to_tags, suffix, node_type, add_to_suffix):
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
    # split suffix from name
    suffix_RE = re.compile('(_[_A-Z]+[A-Z])*')
    found = suffix_RE.split(name)

    if len(found) > 1:
        name = found[0]
    if add_to_tags:
        if isinstance(add_to_tags, list):
            add_to_tags = '_'.join(add_to_tags)
        name += '_' + add_to_tags
    if suffix:
        name += '_' + suffix
    else:
        name += '_' + globals.NODES_SUFFIX[node_type]

    if add_to_suffix:
        name += '_' + add_to_suffix.upper()
    return name


def zero(dag_node, translation=True, rotation=True):
    if translation:
        cmds.xform(dag_node, translation=[0.0, 0.0, 0.0])
    if rotation:
        cmds.xform(dag_node, rotation=[0.0, 0.0, 0.0])
