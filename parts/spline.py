import maya.cmds as cmds

from rigging.utils import curve, transform, common, attribute
from rigging.utils.name import Name, create_chain_names


class Spline(object):
    """  Class for the creation of a curve driven by given transforms.

        Args:
            name (str): base name.
            drivers (list[str]):
            attr_objs:
            degree:
            bezier:
            aim_axis:
            periodic:
            suffix:
            length_attr:

    """
    def __init__(self,
                 name,
                 drivers=[],
                 attr_objs=None,
                 degree=3,
                 bezier=True,
                 aim_axis='+x',
                 periodic=False,
                 suffix='CRV',
                 length_attr=False):
        self.namer = Name(name)
        self.drivers = drivers
        self.attr_objs = attr_objs
        self.aim_axis = aim_axis
        if not attr_objs:
            self.attr_objs = self.drivers

        self.driver_nodes = self._create_driver_nodes()
        self.positions = self._get_driver_positions()

        self.curve = curve.create(self.namer.name,
                                  self.positions,
                                  degree=degree,
                                  bezier=bezier,
                                  periodic=periodic,
                                  suffix=suffix)
        self.curve_shape = common.get_shape(self.curve)

        self._connect_drivers()
        if length_attr:
            self._add_length_attribute()

    def _create_driver_nodes(self):
        driver_nodes = []
        axis = self.aim_axis[-1]
        for i, driver in enumerate(self.drivers):
            axes = ['{}{}'.format(sign, axis) for sign in '+-']
            attribute.add_header_attribute(self.attr_objs[i], 'TANGENTS')
            if i == 0:
                nodes = transform.create_axis_nodes(driver, axes=[axes[0]])
                self._add_connect_tanget(self.attr_objs[i], nodes[0], 'tangentOut', axis)
                nodes.reverse()
            elif i == len(self.drivers) - 1:
                nodes = transform.create_axis_nodes(driver, axes=[axes[1]])
                self._add_connect_tanget(self.attr_objs[i], nodes[0], 'tangentIn', axis)
            else:
                nodes = transform.create_axis_nodes(driver, axes=axes)
                nodes = [nodes[0], nodes[-1], nodes[1]]
                self._add_connect_tanget(self.attr_objs[i], nodes[0], 'tangentIn', axis)
                self._add_connect_tanget(self.attr_objs[i], nodes[2], 'tangentOut', axis)
            driver_nodes.extend(nodes)
        return driver_nodes

    def _get_driver_positions(self):
        positions = []
        for node in self.driver_nodes:
            attr = '.output'
            if cmds.objectType(node, isType='decomposeMatrix'):
                attr = '.outputTranslate'
            positions.extend(cmds.getAttr(node + attr))
        return positions

    @staticmethod
    def _add_connect_tanget(attr_obj, node, attr_name, axis):
        attr = attribute.add_attribute(attr_obj, attr_name, min=0.0, dv=1.0)
        if attr_name == 'tangentIn':
            mult = common.create_node('multDoubleLinear', attr_obj, add_to_tags='tangent')
            cmds.setAttr(mult + '.input2', -1.0)
            cmds.connectAttr(attr_obj + '.{}'.format(attr), mult + '.input1')
            cmds.connectAttr(mult + '.output', node + '.inPoint{}'.format(axis.upper()))
        else:
            cmds.connectAttr(attr_obj + '.{}'.format(attr), node + '.inPoint{}'.format(axis.upper()))

    def _connect_drivers(self):
        for i in range(len(self.driver_nodes)):
            if cmds.objectType(self.driver_nodes[i], isType='pointMatrixMult'):
                cmds.connectAttr(self.driver_nodes[i] + '.output', self.curve_shape + '.controlPoints[{}]'.format(i))
            else:
                cmds.connectAttr(self.driver_nodes[i] + '.outputTranslate', self.curve_shape + '.controlPoints[{}]'.format(i))

    def _add_length_attribute(self):
        curve_info = common.create_node('curveInfo', self.namer.name, add_to_tags='length')
        mult = common.create_node('multDoubleLinear', self.namer.name, add_to_tags='length')

        cmds.connectAttr(self.curve_shape + '.worldSpace[0]', curve_info + '.inputCurve')
        cmds.connectAttr(curve_info + '.arcLength', mult + '.input1')
        cmds.setAttr(mult + '.input2', 1/curve.get_length(self.curve_shape))
        for obj in self.attr_objs:
            attribute.add_attribute(obj, 'length', keyable=False)
            cmds.connectAttr(mult + '.output', obj + '.length')


class SplineSampler(Spline):
    def __init__(self):
        super(SplineSampler, self).__init__()
        pass
