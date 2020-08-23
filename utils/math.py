import maya.cmds as cmds
import maya.api.OpenMaya as om


def get_matrix(dag_node, world=True):
    return om.MMatrix(cmds.xform(dag_node, query=True, matrix=True, worldSpace=world))


def set_matrix(dag_node, matrix, world=True):
    if isinstance(matrix, om.MTransformationMatrix) or isinstance(matrix, om.MMatrix):
        cmds.xform(dag_node, matrix=matrix_to_list(matrix), worldSpace=world)
    if isinstance(matrix, list) and len(list) == 16:
        cmds.xform(dag_node, matrix=matrix, worldSpace=world)


def set_offset_matrix(dag_node, matrix, world=True):
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
    if isinstance(matrix, list) and len(list) == 16:
        return om.MMatrix(matrix)