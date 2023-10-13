import maya.cmds as cmds
import re

import rigging.utils.globals as globals
from rigging.utils.connect import constraint


def ik(name, start_joint, end_effector, parent=None, add_to_suffix=None, add_to_tags=None, suffix=None, solver='ikSCsolver', pole_vector=None, **kwargs):
    handle_name = _generate_suffix(name, add_to_tags, suffix, 'ikHandle', add_to_suffix)
    effector_name = _generate_suffix(name, add_to_tags, suffix, 'ikEffector', add_to_suffix)

    ik_list = cmds.ikHandle(name=handle_name, startJoint=start_joint, endEffector=end_effector, solver=solver, **kwargs)

    ik_handle = ik_list[0]
    ik_effector = cmds.rename(ik_list[1], effector_name)

    if parent:
        cmds.parent(ik_handle, parent, absolute=True)

    if solver == 'ikRPsolver' and pole_vector:
        constraint(pole_vector, ik_handle, type='poleVectorConstraint')

    return [ik_handle, ik_effector]


def _generate_suffix(name, add_to_tags, suffix, node_type, add_to_suffix):
    """returns name and shape-suffix as list

    Args:
        name (str): name of a node
        add_to_tags (str|None): additional tags
        suffix (str|None): suffix
        node_type (str): node_type of node
        add_to_suffix (str|None): additional suffix

    Returns:
       str: name
    """
    # split suffix from name
    suffix_RE = re.compile('(_[_A-Z]+[A-Z])')
    found = suffix_RE.split(name)
    if len(found) > 1:
        name = found[0]
    if add_to_tags:
        if isinstance(add_to_tags, list):
            add_to_tags = '_'.join(add_to_tags)
        name += '_' + add_to_tags
    if suffix:
        name += '_' + suffix
    else:
        name += '_' + globals.NODES_SUFFIX[node_type]

    if add_to_suffix:
        name += '_' + add_to_suffix.upper()
    return name