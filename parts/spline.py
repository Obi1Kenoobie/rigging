import maya.cmds as cmds

from rigging.utils import curve, transform, common, attribute
from rigging.utils.math import lerp
from rigging.utils.name import Name, create_chain_names
from rigging.utils.globals import AXIS_STR_TO_MVEC, AXIS_STR_TO_ATTR


class Spline(object):
    """  Class for the creation of a curve driven by given transforms.

        Args:
            name (str): base name.
            drivers (list[str]): list of transforms that will drive the curve.
            attr_objs (list[str]): list of objects that will hold the tangents attributes len(drivers) == len(attr_obj)!
            degree (int): curve degree.
            bezier (bool): if False it will create a simple spline curve.
            aim_axis (str): transforms aim axis (eg: +x)
            periodic (bool): if True it will create a closed and periodic curve.
            add_to_tags (list[str]|str): additional tags.
            suffix (str): curve suffix.
            length_attr (bool): if True will create a normalised length attribute on the attr_objs.

    """
    def __init__(self,
                 name,
                 drivers=[],
                 attr_objs=None,
                 degree=3,
                 bezier=True,
                 aim_axis='+x',
                 periodic=False,
                 add_to_tags=None,
                 suffix='CRV',
                 length_attr=False):
        self.namer = Name(name)
        self.drivers = drivers
        self.attr_objs = attr_objs
        self.degree = degree
        self.bezier = bezier
        self.aim_axis = aim_axis
        self.periodic = periodic
        self.add_to_tags = add_to_tags
        self.suffix = suffix
        self.length_attr = length_attr
        if not attr_objs:
            self.attr_objs = self.drivers
        self.driver_nodes = None
        self.position_nodes = None
        self.positions = None
        self.curve = None
        self.curve_shape = None
        self.curve_info = None
        self.default_length = None
        self.spline = self

    def build_spline(self):
        self.driver_nodes = self.create_driver_nodes()
        self.position_nodes = [node for node in self.driver_nodes if cmds.objectType(node, isType='decomposeMatrix')]
        self.positions = self.get_driver_positions()

        self.curve = curve.create(self.namer.name,
                                  self.positions,
                                  degree=self.degree,
                                  bezier=self.bezier,
                                  periodic=self.periodic,
                                  add_to_tags=self.add_to_tags,
                                  suffix=self.suffix)
        self.curve_shape = common.get_shape(self.curve)
        self.default_length = curve.get_length(self.curve_shape)

        self._connect_drivers(self.driver_nodes, self.curve_shape)

        if self.length_attr:
            self.curve_info = add_length_attribute(self.curve, self.attr_objs)

    def create_driver_nodes(self):
        driver_nodes = []
        axis = self.aim_axis[-1]
        for i, driver in enumerate(self.drivers):
            axes = ['{}{}'.format(sign, axis) for sign in '+-']
            if not cmds.attributeQuery('TANGENTS', node=self.attr_objs[i], exists=True):
                attribute.add_header_attribute(self.attr_objs[i], 'TANGENTS')
            if i == 0:
                nodes = transform.create_axis_nodes(driver, axes=[axes[0]])
                self._add_connect_tangent(self.attr_objs[i], nodes[0], 'tangentOut', axis)
                nodes.reverse()
            elif i == len(self.drivers) - 1:
                nodes = transform.create_axis_nodes(driver, axes=[axes[1]])
                self._add_connect_tangent(self.attr_objs[i], nodes[0], 'tangentIn', axis)
            else:
                nodes = transform.create_axis_nodes(driver, axes=axes)
                nodes = [nodes[0], nodes[-1], nodes[1]]
                self._add_connect_tangent(self.attr_objs[i], nodes[0], 'tangentIn', axis)
                self._add_connect_tangent(self.attr_objs[i], nodes[2], 'tangentOut', axis)
            driver_nodes.extend(nodes)
        return driver_nodes

    def get_driver_positions(self):
        positions = []
        for node in self.driver_nodes:
            attr = '.output'
            if cmds.objectType(node, isType='decomposeMatrix'):
                attr = '.outputTranslate'
            positions.extend(cmds.getAttr(node + attr))
        return positions

    @staticmethod
    def _add_connect_tangent(attr_obj, node, attr_name, axis):
        attr = attr_name
        if not cmds.attributeQuery(attr, node=attr_obj, exists=True):
            attr = attribute.add_attribute(attr_obj, attr_name, min=0.0, dv=1.0)
        if attr_name == 'tangentIn':
            mult = common.create_node('multDoubleLinear', attr_obj, add_to_tags='tangent')
            cmds.setAttr(mult + '.input2', -1.0)
            cmds.connectAttr(attr_obj + '.{}'.format(attr), mult + '.input1')
            cmds.connectAttr(mult + '.output', node + '.inPoint{}'.format(axis.upper()))
        else:
            cmds.connectAttr(attr_obj + '.{}'.format(attr), node + '.inPoint{}'.format(axis.upper()))

    @staticmethod
    def _connect_drivers(driver_nodes, curve_shape):
        for i in range(len(driver_nodes)):
            if cmds.objectType(driver_nodes[i], isType='pointMatrixMult'):
                cmds.connectAttr(driver_nodes[i] + '.output', curve_shape + '.controlPoints[{}]'.format(i))
            else:
                cmds.connectAttr(driver_nodes[i] + '.outputTranslate', curve_shape + '.controlPoints[{}]'.format(i))


class SplineSampler(Spline):
    def __init__(self,
                 name,
                 drivers=[],
                 driven=None,
                 attr_objs=None,
                 sample_params=None,
                 degree=3,
                 bezier=True,
                 aim_axis='+x',
                 up_axis='+y',
                 offset_matrix=True,
                 twist=True,
                 object_up=None,
                 scale=True,
                 periodic=False,
                 add_to_tags=None,
                 suffix='CRV',
                 lock_stretch=True,
                 length_attr=False
                 ):
        super(SplineSampler, self).__init__(name,
                                            drivers=drivers,
                                            attr_objs=attr_objs,
                                            degree=degree,
                                            bezier=bezier,
                                            aim_axis=aim_axis,
                                            periodic=periodic,
                                            add_to_tags=add_to_tags,
                                            suffix=suffix,
                                            length_attr=length_attr)
        self.driven = driven
        self.up_axis = up_axis
        self.object_up = object_up
        self.offset_matrix = offset_matrix
        self.sample_params = sample_params
        if not self.sample_params:
            self.sample_params = lerp(0.001, .999, num=len(driven))
        self.sample_base_names = create_chain_names(len(self.sample_params), name=self.namer.name, add_to_tags='sample')
        self.motion_paths, self.sample_matrices = self._create_samples()

        if driven:
            self._connect_driven()
        if twist:
            self._twist_setup()
        if not twist:
            self._connect_up_vector()

    def _create_samples(self):
        motion_paths = []
        sample_matrices = []
        for i, obj in enumerate(self.sample_params):
            mpath = common.create_node('motionPath', self.sample_base_names[i], add_to_tags='percent')
            cmds.setAttr(mpath + '.uValue', self.sample_params[i])
            cmds.setAttr(mpath + '.fractionMode', True)
            cmds.setAttr(mpath + '.worldUpVector', *AXIS_STR_TO_MVEC[self.up_axis])
            cmds.setAttr(mpath + '.frontAxis', AXIS_STR_TO_ATTR[self.aim_axis])
            cmds.setAttr(mpath + '.upAxis', AXIS_STR_TO_ATTR[self.up_axis])
            cmds.setAttr(mpath + '.worldUpType', 3)
            cmds.connectAttr(self.curve_shape + '.worldSpace[0]', mpath + '.geometryPath')
            comp_mtx = common.create_node('composeMatrix', self.sample_base_names[i])
            cmds.connectAttr(mpath + '.allCoordinates', comp_mtx + '.inputTranslate')
            cmds.connectAttr(mpath + '.rotate', comp_mtx + '.inputRotate')
            motion_paths.append(mpath)
            sample_matrices.append(comp_mtx)
        return motion_paths, sample_matrices

    def _connect_driven(self):
        for i, obj in enumerate(self.driven):
            parent = common.get_parent(obj)
            if parent:
                mult_matrix = common.create_node('multMatrix', self.sample_matrices[i], add_to_tags='offset')
                cmds.connectAttr(self.sample_matrices[i] + '.outputMatrix', mult_matrix + '.matrixIn[0]')
                cmds.connectAttr(parent + '.worldInverseMatrix[0]', mult_matrix + '.matrixIn[1]')
                if self.offset_matrix:
                    cmds.connectAttr(mult_matrix + '.matrixSum', obj + '.offsetParentMatrix')
                else:
                    decomp = common.create_node('decomposeMatrix', obj)
                    cmds.connectAttr(mult_matrix + '.matrixSum', decomp + '.inputMatrix')
                    cmds.connectAttr(decomp + '.outputTranslate', obj + '.translate')
                    cmds.connectAttr(decomp + '.outputRotate', obj + '.rotate')
                    cmds.connectAttr(decomp + '.outputScale', obj + '.scale')
            else:
                if self.offset_matrix:
                    cmds.connectAttr(self.sample_matrices[i] + '.outputMatrix', obj + '.offsetParentMatrix')
                else:
                    decomp = common.create_node('decomposeMatrix', obj)
                    cmds.connectAttr(self.sample_matrices[i] + '.outputMatrix', decomp + '.inputMatrix')
                    cmds.connectAttr(decomp + '.outputTranslate', obj + '.translate')
                    cmds.connectAttr(decomp + '.outputRotate', obj + '.rotate')
                    cmds.connectAttr(decomp + '.outputScale', obj + '.scale')

    def _connect_up_vector(self):
        up_node = transform.create_axis_nodes(self.object_up, axes=[self.up_axis], position=False, local=True)[0]
        for mpath in self.motion_paths:
            cmds.connectAttr(up_node + '.output', mpath + '.worldUpVector')

    def _twist_setup(self):
        driver_nearest_nodes = []
        rotate_axis = self.aim_axis[-1].upper()
        for i, driver in enumerate(self.drivers):
            nearest_node = common.create_node('nearestPointOnCurve', driver, add_to_tags='twist')
            cmds.connectAttr(self.position_nodes[i] + '.outputTranslate', nearest_node + '.inPosition')
            cmds.connectAttr(self.curve_shape + '.worldSpace[0]', nearest_node + '.inputCurve')
            driver_nearest_nodes.append(nearest_node)
        driven_nearest_nodes = []
        for mpath in self.motion_paths:
            remap = common.create_node('remapValue', mpath, add_to_tags='twist')
            comp = common.create_node('composeMatrix', mpath, add_to_tags='twist')
            nearest_node = common.create_node('nearestPointOnCurve', mpath, add_to_tags='twist')
            point_mtx = common.create_node('pointMatrixMult', mpath, add_to_tags='twist')
            cmds.connectAttr(remap + '.outValue', comp + '.inputRotate' + rotate_axis)
            cmds.connectAttr(mpath + '.allCoordinates', nearest_node + '.inPosition')
            cmds.connectAttr(self.curve_shape + '.worldSpace[0]', nearest_node + '.inputCurve')
            cmds.connectAttr(nearest_node + '.parameter', remap + '.inputValue')
            cmds.connectAttr(comp + '.outputMatrix', point_mtx + '.inMatrix')
            cmds.setAttr(point_mtx + '.inPoint', *AXIS_STR_TO_MVEC[self.up_axis])
            cmds.setAttr(point_mtx + '.vectorMultiply', True)
            for i, driver in enumerate(self.drivers):
                cmds.connectAttr(self.attr_objs[i] + '.rotate' + rotate_axis, remap + '.value[{}].value_FloatValue'.format(i))
                cmds.connectAttr(driver_nearest_nodes[i] + '.parameter', remap + '.value[{}].value_Position'.format(i))
            cmds.connectAttr(point_mtx + '.output', mpath + '.worldUpVector')
            driven_nearest_nodes.append(nearest_node)


def add_length_attribute(crv, attr_objs):
    curve_shape = common.get_shape(crv)
    curve_info = common.create_node('curveInfo', crv, add_to_tags='length')
    mult = common.create_node('multDoubleLinear', crv, add_to_tags='length')

    cmds.connectAttr(curve_shape + '.worldSpace[0]', curve_info + '.inputCurve')
    cmds.connectAttr(curve_info + '.arcLength', mult + '.input1')
    cmds.setAttr(mult + '.input2', 1/curve.get_length(curve_shape))
    for obj in attr_objs:
        attribute.add_attribute(obj, 'length', keyable=False)
        cmds.connectAttr(mult + '.output', obj + '.length')
    return curve_info
