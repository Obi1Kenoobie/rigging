import maya.cmds as cmds

from rigging.utils.name import Name
from rigging.utils.common import create_node
from rigging.utils.connect import connect_decompose
from rigging.utils.attribute import add_attribute
from rigging.parts.base import BaseChain


class IKFK(object):
    def __init__(self,
                 name,
                 matrices,
                 attr_obj=None,
                 blend_attr='blend',
                 parent=None,
                 driverA_tags='driver_fk',
                 driverB_tags='driver_ik',
                 driven_tags='result_ikfk'):

        self.driverA = BaseChain(Name(name, add_to_tags=driverA_tags).name,
                                 matrices,
                                 zero=False,
                                 parent=parent)

        self.driverB = BaseChain(Name(name, add_to_tags=driverB_tags).name,
                                 matrices,
                                 zero=False,
                                 parent=parent)

        self.driven = BaseChain(Name(name, add_to_tags=driven_tags).name,
                                matrices,
                                zero=False,
                                parent=parent)

        self.blend_nodes=[]
        for i, driven in enumerate(self.driven.objs):
            blend_node = create_node('blendMatrix', name=driven, add_to_tags=driven_tags)
            self.blend_nodes.append(blend_node)
            driverA = self.driverA.objs[i]
            driverB = self.driverB.objs[i]

            cmds.connectAttr('{}.matrix'.format(driverA), '{}.inputMatrix'.format(blend_node))
            cmds.connectAttr('{}.matrix'.format(driverB), '{}.target[0].targetMatrix'.format(blend_node))

            connect_decompose('{}.outputMatrix'.format(blend_node), driven)

        if attr_obj:
            self.blend_attribute = '{}.{}'.format(attr_obj, blend_attr)
            add_attribute(attr_obj, blend_attr, max=1.0, min=0.0)
            for blend_node in self.blend_nodes:
                cmds.connectAttr(self.blend_attribute, '{}.envelope'.format(blend_node))