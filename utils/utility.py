import maya.api.OpenMaya as om
import maya.cmds as cmds
from rigging.utils import math, common
from rigging.utils.globals import AXIS_STR_TO_MVEC


def create_aim_locator(points, aim_axis='+z', up_axis='+y'):
    basename = points[0].split('.')[0]
    positions = [om.MVector(cmds.xform(vtx, q=True, t=True, ws=True)) for vtx in points]

    position = (positions[0] + positions[1]) / 2

    up_position = position + AXIS_STR_TO_MVEC[up_axis]
<<<<<<< HEAD
    matrix = math.get_translation_matrix(position)
    if len(positions) > 2:
        up_position = position + ((positions[2] - position) ^ (positions[1] - position))
        matrix = math.get_aim_matrix(position, positions[2], up_position, aim_axis=aim_axis, up_axis=up_axis)
    
    common.create_node('locator', basename, matrix=matrix)
=======
    
    if len(positions) == 2:
        positions = [positions[0], up_position, positions[1]]
    elif len(positions) > 2:
        up_position = position + ((positions[2] - position) ^ (positions[1] - position))
    aim_matrix = math.get_aim_matrix(position, positions[2], up_position, aim_axis=aim_axis, up_axis=up_axis)
    
    common.create_node('locator', basename, matrix=aim_matrix)
>>>>>>> 4bf9ea710ed75cc743948e0f93b2d665fac484ad

