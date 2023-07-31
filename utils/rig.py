import maya.cmds as cmds
from rigging.parts.control import Control
from rigging.utils import common, math, attribute, connect


def create(asset_name, type='anim', rig=True, extras=True, geo=True, skeleton=True, lods=['proxy', 'anim', 'render']):
    """ Function used to create rig base hierarchy.

    Args:
        asset_name (str): asset name (eg. chHuman, vhCar, ppProp)
        type (str): type of rig (eg. anim, cfx, muscle, skin)
        rig (bool): if True will create rig_GRP
        extras (bool): if Ture will create extras_GRP
        geo (bool): if True will create geo_GRP
        skeleton (bool): if True will create skeleton_GRP
        lods (list[str]): list of different level of detail groups (created only if geo is True)

    Returns:

    """
    top_group = cmds.createNode('transform', name='{}{}Rig'.format(asset_name, type.capitalize()))

    global_ctrl = Control('global',
                          math.get_matrix(top_group),
                          shape_type='globals',
                          parent=top_group,
                          zero=False,
                          color='yellow')

    main_ctrl = Control('main',
                         math.get_matrix(top_group),
                         shape_type='circle',
                         parent=global_ctrl.obj,
                         zero=False,
                         size=2.2,
                         color='yellow')

    global_space = common.create_node('transform', 'global', suffix='SPACE', parent=top_group)
    main_space = common.create_node('transform', 'main', suffix='SPACE', parent=top_group)

    connect.matrix_constraint(global_ctrl.obj, global_space)
    connect.matrix_constraint(main_ctrl.obj, main_space)
    attribute.add_header_attribute(global_ctrl.obj, 'VISIBILITY')
    if rig:
        rig_group = common.create_node('transform', 'rig', suffix='GRP', parent=top_group)
        attr = attribute.add_switch(global_ctrl.obj, 'controls', keyable=False)
        cmds.connectAttr(global_ctrl.obj + '.{}'.format(attr), rig_group + '.v')
    if skeleton:
        skeleton_group = common.create_node('transform', 'skeleton', suffix='GRP', parent=top_group)
        attr = attribute.add_switch(global_ctrl.obj, 'skeleton', keyable=False)
        cmds.connectAttr(global_ctrl.obj + '.{}'.format(attr), skeleton_group + '.v')
    if geo:
        geo_group = common.create_node('transform', 'geo', suffix='GRP', parent=top_group)
        attr = attribute.add_switch(global_ctrl.obj, 'geo', keyable=False)
        cmds.connectAttr(global_ctrl.obj + '.{}'.format(attr), geo_group + '.v')
        attribute.add_header_attribute(global_ctrl.obj, 'GEOMETRY')
        attribute.add_enum_attribute(global_ctrl.obj, 'LOD', enum_names=lods, keyable=False)
        attribute.add_enum_attribute(global_ctrl.obj, 'status', enum_names=['unlocked', 'template', 'locked'], keyable=False)
        cmds.setAttr(geo_group + '.overrideEnabled', True)
        cmds.connectAttr(global_ctrl.obj + '.status', geo_group + '.overrideDisplayType')
        for i, lod in enumerate(lods):
            group = common.create_node('transform', lod, suffix='GRP', parent=geo_group)
            connect.sdk(global_ctrl.obj + '.LOD', [i-1, i, i+1], group + '.v', [0, 1, 0])
    if extras:
        extras_group = common.create_node('transform', 'extras', suffix='GRP', parent=top_group)