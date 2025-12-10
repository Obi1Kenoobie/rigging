import maya.cmds as cmds

from rigging.utils import math, common
from rigging.utils.name import Name
from rigging.utils.globals import AXIS_STR_TO_MVEC, AXIS_STR_TO_LONG


def create_axis_nodes(transform, axes=[], position=True, local=False):
    """ Creates a network of nodes that follow the given axis

    Args:
        transform (str): transform object.
        axes (list[str]): list of axes needed.
        position (bool): If True will return the world position and orientation through a decomposeMatrix node.
        local (bool): If True the vectors will be calculated at the origin.

    Returns:
         list[str]: List of nodes holding the axis information.
    """

    nodes = []
    if axes:
        for axis in axes:
            point_mtx = common.create_node('pointMatrixMult', transform, add_to_tags=AXIS_STR_TO_LONG[axis])
            cmds.connectAttr(transform + '.worldMatrix', point_mtx + '.inMatrix')
            cmds.setAttr(point_mtx + '.inPoint', *AXIS_STR_TO_MVEC[axis])
            cmds.setAttr(point_mtx + '.vectorMultiply', local)
            nodes.append(point_mtx)
    if position:
        decomp = common.create_node('decomposeMatrix', transform)
        cmds.connectAttr(transform + '.worldMatrix', decomp + '.inputMatrix')
        nodes.append(decomp)
    return nodes


def parent_locator_shape(transform):
    """ Parent a locator shape under the given transform.

    Args:
        transform (str): transform object.
    Returns:
        str: locator shape.
    """

    locator = common.create_node('locator', transform)
    loc_shape = common.get_shape(locator)
    cmds.parent(loc_shape, transform, relative=True, shape=True)
    cmds.delete(locator)
    return loc_shape
