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


def vectors_to_matrix(row1=(1, 0, 0), row2=(0, 1, 0), row3=(0, 0, 1),
                      row4=(0, 0, 0)):
    """Create matrix for row vectors

    Args:
        row1 (om.MVector | list[float]): Vector for the first row (X Axis Aim)
        row2 (om.MVector | list[float]): Vector for the second row (Y Axis Aim)
        row3 (om.MVector | list[float]): Vector for the third row (Z Axis Aim)
        row4 (om.MVector | list[float]): Vector for the fourth row (Translation)

    Returns:
        om.MMatrix: Return constructed matrix
    """
    row1 = om.MVector(row1)
    row2 = om.MVector(row2)
    row3 = om.MVector(row3)
    row4 = om.MVector(row4)

    val_list = [row1.x, row1.y, row1.z, 0,
                row2.x, row2.y, row2.z, 0,
                row3.x, row3.y, row3.z, 0,
                row4.x, row4.y, row4.z, 1]
    return om.MMatrix(val_list)


def get_aim_matrix(position, aim_position, up_position, aim_axis='+x',
                   up_axis='+z', relative=False):
    """Create a transformation matrix in the way that an aim constraint would

    Args:
        position (om.MVector): Matrix position in world space
        aim_position (om.MVector): Aim position
        up_position (om.MVector): Up position
        aim_axis (str): The axis that will point at the aim position:
            '+x','+y','+z','-x','-y','-z'
        up_axis (str): The axis that will point at the up position:
            '+x','+y','+z','-x','-y','-z'
        relative (bool): Consider the aim and up vectos to be relative to
            position

    Returns:
         om.MMatrix: Return resulting transformaiton matrix
    """
    if aim_axis[-1] == up_axis[-1]:
        raise ValueError("aim_axis '{0}' and up_axis '{1}' need to be different!"
                         .format(aim_axis, up_axis))

    if position is None:
        position = om.MVector.kZeroVector

    if relative:
        aim_vec = aim_position.normal()
        up_vec = up_position.normal()
    else:
        aim_vec = (aim_position - position).normal()
        up_vec = (up_position - position).normal()

    tangent_vec = (aim_vec ^ up_vec).normal()
    up_vec = (tangent_vec ^ aim_vec).normal()

    aim_vec, up_vec, tangent_vec = _reorder_aim_axis(aim_vec, up_vec, tangent_vec,
                                                     aim_axis, up_axis)
    return vectors_to_matrix(aim_vec, up_vec, tangent_vec, position)


def _reorder_aim_axis(aim_vec, up_vec, tangent_vec, aim_axis, up_axis):
    """Reorder rows of a matrix to fit the aim_axis and up_axis criteria

    Args:
        aim_vec (om.MVector): X axis basis vector
        up_vec (om.MVector): Y axis basis vector
        tangent_vec (om.MVector): Z axis basis vector
        aim_axis (str): Aim axis: +x, +y, +z, -x, -y, -z
        up_axis (str): Up axis: +x, +y, +z, -x, -y, -z

    Returns:
        (om.MVector, om.MVector, om.MVector): Return axes in new order
    """
    if aim_axis[-1] != up_axis[-1]:
        if aim_axis[0] == '-':
            aim_vec, tangent_vec = -aim_vec, -tangent_vec
        if up_axis[0] == '-':
            up_vec, tangent_vec = -up_vec, -tangent_vec

        if aim_axis[-1] == 'x':
            if up_axis[-1] == 'y':
                aim_vec, up_vec, tangent_vec = aim_vec, up_vec, tangent_vec
            elif up_axis[-1] == 'z':
                aim_vec, up_vec, tangent_vec = aim_vec, -tangent_vec, up_vec

        elif aim_axis[-1] == 'y':
            if up_axis[-1] == 'x':
                aim_vec, up_vec, tangent_vec = up_vec, aim_vec, -tangent_vec
            if up_axis[-1] == 'z':
                aim_vec, up_vec, tangent_vec = tangent_vec, aim_vec, up_vec

        elif aim_axis[-1] == 'z':
            if up_axis[-1] == 'x':
                aim_vec, up_vec, tangent_vec = up_vec, tangent_vec, aim_vec
            if up_axis[-1] == 'y':
                aim_vec, up_vec, tangent_vec = -tangent_vec, up_vec, aim_vec

    return aim_vec, up_vec, tangent_vec


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
