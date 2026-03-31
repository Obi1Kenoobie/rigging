import maya.cmds as cmds

from rigging.utils import common, math
from rigging.utils.globals import AXIS_STR_TO_VEC, AXIS_PREV, NODES_SUFFIX
from rigging.utils.name import Name
from rigging.utils.attribute import set_attribute_dict


# dictionary used to store connection information
conn_dict = {'type' : None,
             'attributes' : [],
             'nodes' :[]}


def connect(source, destination, attr='srt', axis='xyz', store=False):
    for at in attr:
        for ax in axis:
            cmds.connectAttr(source + '.{}{}'.format(at, ax), destination + '.{}{}'.format(at, ax), f=True)


def connect_rotateorder(source, destination, store=False):
    cmds.connectAttr(source + '.rotateOrder', destination + '.rotateOrder', f=True)


def connect_visibility(source_attr, destination, store=False):
    cmds.connectAttr(source_attr, destination + '.v', f=True)


def matrix_constraint(driver, driven, snap=False, attr='srt', store=False):
    conn_dict['type'] = 'matrix_constraint'
    conn_dict['attributes'] = [driver, driven, snap, attr, store]
    
    mult = common.create_node('multMatrix', driver, add_to_tags=['cnst'])
    decomp = common.create_node('decomposeMatrix', driver, add_to_tags=['cnst'])
    conn_dict['nodes'] = [mult, decomp]
    
    
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
    
    if store:
        set_attribute_dict(conn_dict['attributes'][0], 
                           '{}_{}_to_{}_{}_cnst'.format(conn_dict['type'], 
                                                        conn_dict['attributes'][0], 
                                                        conn_dict['attributes'][1], 
                                                        attr), 
                           conn_dict)


def aim_matrix_constraint(aim_obj, dag_node, up_obj=None, aim='+x', up='+y', skip_rotate='', use_up_obj=False, snap=True, store=False):
    conn_dict['type'] = 'aim_matrix_constraint'
    conn_dict['attributes'] = [dag_node, aim_obj, up_obj, aim, up, use_up_obj, snap, store]
    aim_vec = AXIS_STR_TO_VEC[aim]
    up_vec = AXIS_STR_TO_VEC[up]
    aim_node = common.create_node('aimMatrix', aim_obj, add_to_tags=['aim', 'cnst'])
    decomp = common.create_node('decomposeMatrix', aim_obj, add_to_tags=['aim', 'cnst'])
    mult = common.create_node('multMatrix', aim_obj, add_to_tags=['aim', 'cnst'])
    conn_dict['nodes'] = [aim_node, decomp, mult]
    
    skip = [i for i in skip_rotate]
    
    cmds.setAttr(aim_node + '.secondaryMode', 1)
    
    for axis in ['x', 'y', 'z']:
        if not axis in skip:
            cmds.connectAttr(decomp + '.outputRotate{}'.format(axis.upper()), dag_node + '.r{}'.format(axis))

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
    if store:
        set_attribute_dict(conn_dict['attributes'][0], '{}_cnst'.format(conn_dict['type']), conn_dict)
    
    return aim_node

def sdk(driver_attr, driver_values, driven_attr, driven_values, interpolation='linear', store=False):
    if driver_values and driven_values and len(driver_values) == len(driven_values):
        for i in range(len(driven_values)):
            cmds.setDrivenKeyframe(driven_attr,
                                   cd=driver_attr,
                                   dv=driver_values[i],
                                   v=driven_values[i],
                                   itt=interpolation,
                                   ott=interpolation)


def connect_decompose(driver_matrix, driven, attr='srt', axis='xyz', store=False, **kwargs):
    decompose_node = common.create_node('decomposeMatrix', name=driven, **kwargs)
    cmds.connectAttr(driver_matrix, '{}.inputMatrix'.format(decompose_node))
    output_attr_dict = {'s' : 'outputScale',
                        'r' : 'outputRotate',
                        't' : 'outputTranslate'}
    for at in attr:
        for ax in axis:
            cmds.connectAttr('{}.{}{}'.format(decompose_node, output_attr_dict[at], ax.upper()),
                             '{}.{}{}'.format(driven, at, ax))

    return decompose_node


def constraint(driver, driven, snap=False, skip_translate='', skip_rotate='', skip_scale='', aim_vector=[1.0, 0.0, 0.0], 
               up_vector=[0.0, 1.0, 0.0], world_up_object=None, world_up_type='', world_up_vector=[0.0, 1.0, 0.0], type='parentConstraint', store=False):
    conn_dict['type'] = 'constraint'
    conn_dict['attributes'] = [driver, driven, snap, skip_translate, skip_rotate, skip_scale, aim_vector, 
                               up_vector, world_up_object, world_up_type, world_up_vector, type, store]
    name = Name(driven, add_to_suffix=NODES_SUFFIX[type]).name
    constraint_node = None
    if type == 'parentConstraint':
        constraint_node = cmds.parentConstraint(driver,
                                               driven,
                                               name=name,
                                               maintainOffset=not snap,
                                               skipTranslate=list(skip_translate),
                                               skipRotate=list(skip_rotate))

    if type == 'orientConstraint':
        constraint_node = cmds.orientConstraint(driver,
                                               driven,
                                               name=name,
                                               maintainOffset=not snap,
                                               skip=list(skip_rotate))

    if type == 'pointConstraint':
        constraint_node = cmds.pointConstraint(driver,
                                               driven,
                                               name=name,
                                               maintainOffset=not snap,
                                               skip=list(skip_translate))

    if type == 'scaleConstraint':
        constraint_node = cmds.scaleConstraint(driver,
                                                driven,
                                                name=name,
                                                maintainOffset=not snap,
                                                skip=list(skip_scale))

    if type == 'poleVectorConstraint':
        constraint_node = cmds.poleVectorConstraint(driver,
                                                    driven,
                                                    name=name)

    if type == 'aimConstraint':
       constraint_node = cmds.aimConstraint(driver, 
                                            driven , 
                                            aimVector=aim_vector, 
                                            maintainOffset=not snap, 
                                            name=name, 
                                            skip=skip_rotate.split(), 
                                            upVector=up_vector, 
                                            worldUpObject=world_up_object, 
                                            worldUpType=world_up_type, 
                                            worldUpVector=world_up_vector)

    conn_dict['nodes'] = [constraint_node[0]]
    if store:
        attr = ''
        if skip_translate:
            attr += '{}_'.format(skip_translate)
        if skip_rotate:
            attr += '{}_'.format(skip_rotate)
        if skip_scale:
            attr += '{}_'.format(skip_scale)
        set_attribute_dict(conn_dict['attributes'][0], 
                           '{}_{}_to_{}_{}_cnst'.format(type, 
                                                        conn_dict['attributes'][0], 
                                                        conn_dict['attributes'][1], 
                                                        attr), 
                           conn_dict)

    return constraint_node[0]


def rebuild_connection(conn_dict, isStorable=True):
    # deleting old nodes
    for node in conn_dict['nodes']:
        if cmds.objExists(node):
            cmds.delete(node)

    if conn_dict['type'] == 'matrix_constraint':
        return matrix_constraint(conn_dict['attributes'][0], 
                                 conn_dict['attributes'][1], 
                                 conn_dict['attributes'][2], 
                                 conn_dict['attributes'][3], 
                                 isStorable)

    if conn_dict['type'] == 'aim_matrix_constraint':
       return  aim_matrix_constraint(conn_dict['attributes'][0], 
                                     conn_dict['attributes'][1], 
                                     conn_dict['attributes'][2], 
                                     conn_dict['attributes'][3], 
                                     conn_dict['attributes'][4], 
                                     conn_dict['attributes'][5], 
                                     conn_dict['attributes'][6], 
                                     isStorable)
    if conn_dict['type'] == 'constraint':
        return constraint(conn_dict['attributes'][0], 
                          conn_dict['attributes'][1], 
                          conn_dict['attributes'][2], 
                          conn_dict['attributes'][3], 
                          conn_dict['attributes'][4], 
                          conn_dict['attributes'][5], 
                          conn_dict['attributes'][6],
                          conn_dict['attributes'][7], 
                          conn_dict['attributes'][8], 
                          conn_dict['attributes'][9], 
                          conn_dict['attributes'][10], 
                          conn_dict['attributes'][11],  
                          isStorable)