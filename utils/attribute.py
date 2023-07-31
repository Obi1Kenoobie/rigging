import maya.cmds as cmds


def add_attribute(dag_node, attribute_name, attr_type='float', keyable=True, channel_box=True, lock=False, **kwargs):
    cmds.addAttr(dag_node, longName=attribute_name, attributeType=attr_type, **kwargs)
    cmds.setAttr('{}.{}'.format(dag_node, attribute_name), lock=lock, channelBox=channel_box)
    cmds.setAttr('{}.{}'.format(dag_node, attribute_name), channelBox=channel_box)
    cmds.setAttr('{}.{}'.format(dag_node, attribute_name), keyable=keyable)
    return attribute_name


def add_switch(dag_node, attribute_name, keyable=False, lock=False, default=True):
    return add_attribute(dag_node, attribute_name, attr_type='bool', keyable=keyable, lock=lock, defaultValue=default)


def add_blend_attribute(dag_node, attribute_name, min=0.0, max=1.0, default=0.0, keyable=True, lock=False):
    return add_attribute(dag_node, attribute_name, keyable=keyable, lock=lock, min=min, max=max, defaultValue=default)


def add_enum_attribute(dag_node, attribute_name, enum_names=[], keyable=True, lock=False):
    add_attribute(dag_node, attribute_name, attr_type='enum', keyable=keyable, lock=lock, enumName=':'.join(enum_names))


def add_header_attribute(dag_node, attribute_name):
    add_attribute(dag_node, attribute_name, attr_type='enum', keyable=False, lock=True, niceName='_', enumName='{}:'.format(attribute_name))


def add_proxy_attribute(dag_nodes, attribute_name, attr_type='float', keyable=True, channel_box=True, lock=False, **kwargs):
    attr = add_attribute(dag_nodes[0],
                         attribute_name,
                         attr_type=attr_type,
                         keyable=keyable,
                         channel_box=channel_box,
                         lock=lock,
                         **kwargs)
    for dag_node in dag_nodes[1:]:
        cmds.addAttr(dag_node, longName=attr, proxy=attr)

    return attr


def lock_srt(dag_node, translate='xyz', rotate='xyz', scale='xyz', hide=True, visibility=False):
    attrs = {'t': translate.lower(),
             'r': rotate.lower(),
             's': scale.lower()}

    for key in attrs:
        for elem in attrs[key]:
            cmds.setAttr('{}.{}{}'.format(dag_node, key, elem), lock=True, keyable=not hide)
    
    if visibility:
        cmds.setAttr('{}.visibility'.format(dag_node), lock=True, keyable=not hide)


def unlock_srt(dag_node, channels='srt', visibility=False):
    for channel in channels:
        for axis in 'xyz':
            cmds.setAttr('{}.{}{}'.format(dag_node, channel, axis), lock=False, keyable=True)
    if visibility:
        cmds.setAttr('{}.visibility'.format(dag_node), lock=False, keyable=True)


def display_rotate_order(dag_node):
    cmds.setAttr(dag_node + '.rotateOrder', channelBox=True, keyable=False)