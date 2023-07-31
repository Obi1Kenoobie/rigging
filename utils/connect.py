import maya.cmds as cmds
from rigging.utils import common, math
from rigging.utils.globals import AXIS_STR_TO_VEC, AXIS_PREV


def connect(source, destination, attr='srt', axis='xyz'):
    for at in attr:
        for ax in axis:
            cmds.connectAttr(source + '.{}{}'.format(at, ax), destination + '.{}{}'.format(at, ax), f=True)


def connect_rotateorder(source, destination):
    cmds.connectAttr(source + '.rotateOrder', destination + '.rotateOrder', f=True)


def connect_visibility(source_attr, destination):
    cmds.connectAttr(source_attr, destination + '.v', f=True)


def matrix_constraint(driver, driven, snap=False, attr='srt'):
    mult = common.create_node('multMatrix', driver, add_to_tags=['cnst'])
    decomp = common.create_node('decomposeMatrix', driver, add_to_tags=['cnst'])

    attrs = {'t': 'outputTranslate',
             'r': 'outputRotate',
             's': 'outputScale'}

    driver_matrix = math.get_matrix(driver)
    driven_matrix = math.get_matrix(driven)

    if not snap:
        offset_matrix = math.offset_matrix(driver_matrix, driven_matrix)
        cmds.setAttr(mult + '.matrixIn[0]', offset_matrix, type='matrix')
        cmds.connectAttr(driver + '.worldMatrix[0]', mult + '.matrixIn[1]')
        cmds.connectAttr(driven + '.parentInverseMatrix[0]', mult + '.matrixIn[2]')
    else:
        cmds.connectAttr(driver + '.worldMatrix[0]', mult + '.matrixIn[0]')
        cmds.connectAttr(driven + '.parentInverseMatrix[0]', mult + '.matrixIn[1]')

    cmds.connectAttr(mult + '.matrixSum', decomp + '.inputMatrix')

    for at in attr:
        cmds.connectAttr(decomp + '.{}'.format(attrs[at]), driven + '.{}'.format(at))


def aim_matrix_constraint(dag_node, aim_obj, up_obj=None, aim='+x', up='+y', use_up_obj=False, snap=True):
    aim_vec = AXIS_STR_TO_VEC[aim]
    up_vec = AXIS_STR_TO_VEC[up]
    aim_node = common.create_node('aimMatrix', aim_obj, add_to_tags=['aim', 'cnst'])
    decomp = common.create_node('decomposeMatrix', aim_obj, add_to_tags=['aim', 'cnst'])
    mult = common.create_node('multMatrix', aim_obj, add_to_tags=['aim', 'cnst'])

    cmds.setAttr(aim_node + '.secondaryMode', 1)
    cmds.connectAttr(decomp + '.outputRotate', dag_node + '.rotate')
    cmds.connectAttr(dag_node + '.parentMatrix', aim_node + '.inputMatrix')
    cmds.connectAttr(aim_obj + '.worldMatrix[0]', aim_node + '.primaryTargetMatrix')
    cmds.setAttr(aim_node + '.primaryInputAxis', *aim_vec, type='double3')
    cmds.setAttr(aim_node + '.secondaryInputAxis', *up_vec, type='double3')
    cmds.setAttr(aim_node + '.primaryTargetVector', *aim_vec, type='double3')
    cmds.setAttr(aim_node + '.secondaryTargetVector', *up_vec, type='double3')
    if use_up_obj and up_obj:
        cmds.connectAttr(up_obj + '.worldMatrix[0]', aim_node + '.secondaryTargetMatrix')
    else:
        cmds.setAttr(aim_node + '.secondaryTargetVector', *AXIS_STR_TO_VEC[AXIS_PREV[up]], type='double3')
        cmds.setAttr(aim_node + '.secondaryMode', 2)

    if not snap:
        aim_matrix = math.to_mmatrix(cmds.getAttr(aim_node + '.outputMatrix'))
        offset_matrix = math.offset_matrix(aim_matrix, math.get_matrix(dag_node))
        cmds.setAttr(mult + '.matrixIn[0]', offset_matrix, type='matrix')
        cmds.connectAttr(aim_node + '.outputMatrix', mult + '.matrixIn[1]')
        cmds.connectAttr(dag_node + '.parentInverseMatrix[0]', mult + '.matrixIn[2]')
    else:
        cmds.connectAttr(aim_node + '.outputMatrix', mult + '.matrixIn[0]')
        cmds.connectAttr(dag_node + '.parentInverseMatrix[0]', mult + '.matrixIn[1]')

    cmds.connectAttr(mult + '.matrixSum', decomp + '.inputMatrix')


def sdk(driver_attr, driver_values, driven_attr, driven_values, interpolation='linear'):
    if driver_values and driven_values and len(driver_values) == len(driven_values):
        for i in range(len(driven_values)):
            cmds.setDrivenKeyframe(driven_attr,
                                   cd=driver_attr,
                                   dv=driver_values[i],
                                   v=driven_values[i],
                                   itt=interpolation,
                                   ott=interpolation)
