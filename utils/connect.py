import maya.cmds as cmds
from rigging.utils import common, math


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


def sdk(driver_attr, driver_values, driven_attr, driven_values, interpolation='linear'):
    if driver_values and driven_values and len(driver_values) == len(driven_values):
        for i in range(len(driven_values)):
            cmds.setDrivenKeyframe(driven_attr, cd=driver_attr, dv=driver_values[i], v=driven_values[i], itt=interpolation, ott=interpolation)
    
    
    
    