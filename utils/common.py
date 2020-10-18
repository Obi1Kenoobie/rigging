import maya.cmds as cmds

from rigging.utils import globals, math
from rigging.utils.name import Name


def get_parent(dag_node, **kwargs):
    return cmds.listRelatives(dag_node, parent=True, **kwargs)[0]


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


def create_node(node_type, name, matrix=None, parent=None, use_offset_matrix=False, use_node_type=True):
    node_name = name
    print node_name
    if use_node_type:
        node_name = Name(name, node_type=node_type).create()

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


def zero(dag_node, translation=True, rotation=True):
    if translation:
        cmds.xform(dag_node, translation=[0.0, 0.0, 0.0])
    if rotation:
        cmds.xform(dag_node, rotation=[0.0, 0.0, 0.0])
