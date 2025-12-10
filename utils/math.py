import maya.cmds as cmds
import maya.api.OpenMaya as om
from rigging.utils.data_io import Data
<<<<<<< HEAD
from rigging.utils.globals import AXIS_ATTR, AXIS_VEC, AXIS_STR

=======
>>>>>>> 4bf9ea710ed75cc743948e0f93b2d665fac484ad


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


def get_axis_vector(matrix, axis):
    """Get axis vector from matrix

    Args:
        matrix (om.MMatrix): Matrix to get the axis from
        axis (str): Axis to get: '+x','+y','+z','-x','-y','-z'

    Returns:
        om.MVector: Return the axis vector
    """
    if 'x' in axis.lower():
        vec = om.MVector(matrix[0], matrix[1], matrix[2])
    elif 'y' in axis.lower():
        vec = om.MVector(matrix[4], matrix[5], matrix[6])
    elif 'z' in axis.lower():
        vec = om.MVector(matrix[8], matrix[9], matrix[10])
    else:
        raise ValueError("Invalid axis specified '{0}'!".format(axis))

    if axis.startswith('-'):
        return -vec

    return vec


<<<<<<< HEAD
def get_closest_axis_to_vector(aimer_matrix, target_matrix):
    """Get closest axis aligning to the target aim vector
    
    Args:
        aimer_matrix (om.MMatrix): Matrix we want to get the closest axis from
        target_matrix (om.MMatrix): Matrix we are aiming to
    
    Returns:
        (list[om.MVector], str): Axis vector, string name of axis vector
    """
    target_pos = translation_from_matrix(target_matrix)
    aimer_pos = translation_from_matrix(aimer_matrix)

    aim_vec = target_pos - aimer_pos
    aim_vec.normalize()

    axis_vecs = [get_axis_vector(aimer_matrix, axis) for axis in AXIS_STR]

    dot = lambda x: 1 - (aim_vec * x)

    dots = list(map(dot, axis_vecs))
    axis_index = dots.index(min(dots))
    
    return AXIS_VEC[axis_index], AXIS_STR[axis_index]


=======
>>>>>>> 4bf9ea710ed75cc743948e0f93b2d665fac484ad
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


def lerp(start, end, num=10):
    """ For a list of floats linearly interpolated between two given ones.

    Args:
        start (float, int): start value.
        end (float, int): end value.
        num (int): number of samples.

    Returns:
        list[float]: list of values

    """
    return [i for i in lerp_generator(start, end, num=num)]


def lerp_vectors(start_vec, end_vec, num=10):
    """ Returns a list of interpolated vectors between the given ones.

    Args:
        start_vec (om.MVector): start vector.
        end_vec (om.MVector): end vector
        num (int): number of samples.

    Returns:
        list[om.MVector]: list of vectors
    """
    x_gen = lerp_generator(start_vec.x, end_vec.x, num=num)
    y_gen = lerp_generator(start_vec.y, end_vec.y, num=num)
    z_gen = lerp_generator(start_vec.z, end_vec.z, num=num)
    return [om.MVector(x, y, z) for x, y, z in zip(x_gen, y_gen, z_gen)]


def lerp_matrices(start_mtx, end_mtx, num=10, rotation_order='xyz'):
    """ Returns a list of interpolated matrices between the given ones.

    Args:
        start_mtx (om.MMatrix): start matrix.
        end_mtx (om.MMatrix): end matrix.
        num (int): number of samples.
        rotation_order (str): rotation order.

    Returns:
        list[om.MMatrix]: list of matrices
    """
    start_cmp = matrix_components(start_mtx, rotation_order=rotation_order)
    end_cmp = matrix_components(end_mtx, rotation_order=rotation_order)
    
    tx_gen = lerp_generator(start_cmp.translation[0], end_cmp.translation[0], num=num)
    ty_gen = lerp_generator(start_cmp.translation[1], end_cmp.translation[1], num=num)
    tz_gen = lerp_generator(start_cmp.translation[2], end_cmp.translation[2], num=num)
    
    rx_gen = lerp_generator(start_cmp.rotation[0], end_cmp.rotation[0], num=num)
    ry_gen = lerp_generator(start_cmp.rotation[1], end_cmp.rotation[1], num=num)
    rz_gen = lerp_generator(start_cmp.rotation[2], end_cmp.rotation[2], num=num)
    
    sx_gen = lerp_generator(start_cmp.scale[0], end_cmp.scale[0], num=num)
    sy_gen = lerp_generator(start_cmp.scale[1], end_cmp.scale[1], num=num)
    sz_gen = lerp_generator(start_cmp.scale[2], end_cmp.scale[2], num=num)
    
    lerped = []
    for tx, ty, tz, rx, ry, rz, sx, sy, sz in zip(tx_gen, ty_gen, tz_gen, rx_gen, ry_gen, rz_gen, sx_gen, sy_gen, sz_gen):
        lerped.append(create_matrix(translation=[tx, ty, tz], rotation=[rx, ry, rz], scale=[sx, sy, sz], rotation_order=rotation_order))

    return lerped


def lerp_generator(start, end, num=10):
    """  For a list of floats linearly interpolated between two given ones.

    Args:
        start (float, int): start value.
        end (float, int): end value.
        num (int): number of samples.

    Returns:
        generator: gnerator object holding the interpolations
    """
    step = (float(end) - float(start)) / (num - 1)
    sample = start
    i = 0
    while i < num:
        yield sample
        sample += step
        i += 1


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


def create_matrix(translation=[0, 0, 0], rotation=[0, 0, 0], scale=[1, 1, 1], rotation_order='xyz'):
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


def get_position_matrix(dag_node, world=True):
    matrix = get_matrix(dag_node, world=world)
    return create_matrix(translation=translation_from_matrix(matrix))


def get_position_vector(dag_node, world=True):
    matrix = get_matrix(dag_node, world=world)
    return translation_from_matrix(matrix)


<<<<<<< HEAD
def get_vector_between(start_matrix, end_matrix):
    return translation_from_matrix(end_matrix) - translation_from_matrix(start_matrix)


def get_vector_between_dags(start_dag, end_dag):
    return get_vector_between(get_matrix(end_dag), get_matrix(start_dag))


=======
>>>>>>> 4bf9ea710ed75cc743948e0f93b2d665fac484ad
def rotate_position(position, aim_axis, up_axis):
    """Reorder a position vector to fit the aim_axis and up_axis criteria

    Args:
        position (list/om.MVector): position vector
        aim_axis (str): Aim axis: +x, +y, +z, -x, -y, -z
        up_axis (str): Up axis: +x, +y, +z, -x, -y, -z

    Returns:
        om.MVector: Return rotated position vector
    """

    if isinstance(position, list):
        position = to_mvector(position)

    x = position.x
    y = position.y
    z = position.z

    if aim_axis[-1] != up_axis[-1]:
        if aim_axis[0] == '-':
            x, z = -x, -z
        if up_axis[0] == '-':
            y, z = -y, -z

        if aim_axis[-1] == 'x':
            if up_axis[-1] == 'y':
                x, y, z = x, y, z
            elif up_axis[-1] == 'z':
                x, y, z = x, -z, y

        elif aim_axis[-1] == 'y':
            if up_axis[-1] == 'x':
                x, y, z = y, x, -z
            if up_axis[-1] == 'z':
                x, y, z = z, x, y

        elif aim_axis[-1] == 'z':
            if up_axis[-1] == 'x':
                x, y, z = y, z, x
            if up_axis[-1] == 'y':
                x, y, z = -z, y, x

    return om.MVector(x, y, z)


def get_align_matrix(target_matrix, source_matrix, source_aim='+x', source_up='+y', target_aim='+x', target_up='+y', target_position=False):
    """ Function reutrns a matrix aligned to a target matrix specified axes.
    
    Args:
        target_matrix (om.MMatrix): target matrix for alignment.
        source_aim (str): Source Aim axis: +x, +y, +z, -x, -y, -z
        source_up (str): Source Up axis: +x, +y, +z, -x, -y, -z
        target_aim (str): Target Aim axis: +x, +y, +z, -x, -y, -z
        target_up (str): Target Up axis: +x, +y, +z, -x, -y, -z
        target_position (bool): If true will position the aligned matrix at target position.

    Returns:
        om.MMatrix: aligned matrix.
    """
    aim_vec = get_axis_vector(target_matrix, target_aim)
    up_vec = get_axis_vector(target_matrix, target_up)

    align_mtx = get_aim_matrix(om.MVector(), aim_vec, up_vec, aim_axis=source_aim, up_axis=source_up)
    if target_position:
        align_mtx[-4] = target_matrix[-4]
        align_mtx[-3] = target_matrix[-3]
        align_mtx[-2] = target_matrix[-2]

    else:
        align_mtx[-4] = source_matrix[-4]
        align_mtx[-3] = source_matrix[-3]
        align_mtx[-2] = source_matrix[-2]
    
    return align_mtx


def get_polevector_position_vector(matrices, pv_distance=40.0):
    """ Function used to calculate pole vector position given at least three matrices to form a plane.
    
    Args:
        matrices (list[om.MMatrix]): List of matrices used to calculate plane.
        pv_distance (float): pole vector distance from second last matrices alement.

    Returns:
        om.MVector: pole vector position vector.
    """
    if len(matrices) < 3:
        cmds.warning('Need at least three matrices in order to calculate pole vector position!')
        return om.MVector()
    
    positions = [translation_from_matrix(mtx) for mtx in matrices]
    
    # triangle long side normalized vector
    p0p2n = (positions[-1] - positions[0]).normalize() 
    
    # tirangle first side
    p0p1 = (positions[-2] - positions[0])
    
    # first side projection onto long side vector
    p0p1prj = (p0p1 * p0p2n) * p0p2n + positions[0]
    
    # final pole vector position at set distance from second position
    p0p1prjp1 = ((positions[-2] - p0p1prj).normalize() * pv_distance) + positions[-2]
    
    return p0p1prjp1