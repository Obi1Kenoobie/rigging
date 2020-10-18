import maya.cmds as cmds
import maya.api.OpenMaya as om
from rigging.utils.data_io import Data


ROTATION_ORDER = {'xyz' : om.MEulerRotation.kXYZ,
                  'xzy' : om.MEulerRotation.kXZY,
                  'yxz' : om.MEulerRotation.kYXZ,
                  'yzx' : om.MEulerRotation.kYZX,
                  'zxy' : om.MEulerRotation.kZXY,
                  'zyx' : om.MEulerRotation.kZYX}


def get_matrix(dag_node, world=True):
    return om.MMatrix(cmds.xform(dag_node, query=True, matrix=True, worldSpace=world))


def set_matrix(dag_node, matrix, world=True):
    if isinstance(matrix, om.MTransformationMatrix) or isinstance(matrix, om.MMatrix):
        cmds.xform(dag_node, matrix=matrix_to_list(matrix), worldSpace=world)
    if isinstance(matrix, list) and len(list) == 16:
        cmds.xform(dag_node, matrix=matrix, worldSpace=world)


def get_offset_parent_matrix(dag_node):
    matrix_list = cmds.getAttr(dag_node + '.offsetParentMatrix')
    return to_mmatrix(matrix_list)


def set_offset_parent_matrix(dag_node, matrix, world=False):
    if world:
        matrix = offset_matrix(get_matrix(dag_node), matrix)
    matrix = matrix_to_list(matrix)
    cmds.setAttr(dag_node + '.offsetParentMatrix', matrix, type='matrix')


def matrix_to_list(matrix):
    if isinstance(matrix, om.MTransformationMatrix):
        return [value for value in matrix.asMatrix()]
    if isinstance(matrix, om.MMatrix):
        return [value for value in matrix]
    if isinstance(matrix, list) and len(list) == 16:
        return matrix


def offset_matrix(source, target):
    return target * source.inverse()


def to_tmatrix(matrix):
    if isinstance(matrix, om.MTransformationMatrix):
        return matrix
    if isinstance(matrix, om.MMatrix):
        return om.MTransformationMatrix(matrix)
    if isinstance(matrix, list) and len(list) == 16:
        return om.MTransformationMatrix(to_mmatrix(matrix))


def to_mmatrix(matrix):
    if isinstance(matrix, om.MTransformationMatrix):
        return matrix.asMatrix()
    if isinstance(matrix, om.MMatrix):
        return matrix
    if isinstance(matrix, list) and len(matrix) == 16:
        return om.MMatrix(matrix)


def to_mvector(float_list):
    return om.MVector(float_list)


def to_eulerrotation(rotation, rotation_order='xyz'):
    rotate_order = ROTATION_ORDER[rotation_order]
    x = om.MAngle(rotation[0], om.MAngle.kDegrees).asRadians()
    y = om.MAngle(rotation[1], om.MAngle.kDegrees).asRadians()
    z = om.MAngle(rotation[2], om.MAngle.kDegrees).asRadians()

    return om.MEulerRotation(x, y, z, order=rotate_order)


def create_matrix(translation=[0, 0, 0], rotation=[0, 0, 0], scale=[0, 0, 0], rotation_order='xyz'):
    tmatrix = om.MTransformationMatrix()
    translation = to_mvector(translation)
    rotation = to_eulerrotation(rotation, rotation_order=rotation_order)
    scale = to_mvector(scale)

    tmatrix.setTranslation(translation, om.MSpace.kWorld)
    tmatrix.setRotation(rotation)
    tmatrix.setScale(scale, om.MSpace.kWorld)
    return to_mmatrix(tmatrix)


def matrix_components(matrix, rotation_order='xyz'):
    data = Data()
    tmatrix = to_tmatrix(matrix)
    data.translation = to_mvector(tmatrix.translation(om.MSpace.kWorld))

    data.rotation = to_mvector(rotation_from_matrix(matrix, rotation_order=rotation_order))

    data.scale = to_mvector(tmatrix.scale(om.MSpace.kWorld))

    return data


def rotation_from_matrix(matrix, rotation_order='xyz'):
    tmatrix = to_tmatrix(matrix)
    euler = tmatrix.rotation()
    euler.reorderIt(ROTATION_ORDER[rotation_order])

    return [om.MAngle(euler.x, om.MAngle.kRadians).asDegrees(),
            om.MAngle(euler.y, om.MAngle.kRadians).asDegrees(),
            om.MAngle(euler.z, om.MAngle.kRadians).asDegrees()]


def translation_from_matrix(matrix):
    return om.MVector(matrix[-4], matrix[-3], matrix[-2])


def get_translation_matrix(translation):
    matrix = om.MMatrix()
    matrix[-4] = translation[0]
    matrix[-3] = translation[1]
    matrix[-2] = translation[2]
    return matrix


def get_rotation_matrix(rotation, rotation_order='xyz'):
    euler = to_eulerrotation(rotation, rotation_order=rotation_order)
    return euler.asMatrix()
