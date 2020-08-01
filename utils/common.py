import maya.cmds as cmds

from meRig.utils import globals


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