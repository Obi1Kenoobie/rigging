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
                 use_tangents=True,
                 aim_axis='+x',
                 periodic=False,
                 add_to_tags=None,
                 suffix='crv',
                 length_attr=False):
        self.namer = Name(name)
        self.drivers = drivers
        self.attr_objs = attr_objs
        self.degree = degree
        self.bezier = bezier
        self.use_tangets = use_tangents
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
        self.length_mult = None
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
                                  normalize=True,
                                  suffix=self.suffix)
        self.curve_shape = common.get_shape(self.curve)
        self.default_length = curve.get_length(self.curve_shape)

        self._connect_drivers(self.driver_nodes, self.curve_shape)

        if self.length_attr:
            nodes = add_length_attribute(self.curve, self.attr_objs)
            self.curve_info = nodes[0]
            self.length_mult = nodes[1]

    def create_driver_nodes(self):
        driver_nodes = []
        axis = self.aim_axis[-1]
        for i, driver in enumerate(self.drivers):
            if self.use_tangets:
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
            else:
                decomp = common.create_node('decomposeMatrix', driver)
                cmds.connectAttr(driver + '.worldMatrix', decomp + '.inputMatrix')
                driver_nodes.append(decomp)
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
                 use_tangents=True,
                 aim_axis='+x',
                 up_axis='+y',
                 offset_matrix=True,
                 twist=True,
                 object_up=None,
                 scale=True,
                 periodic=False,
                 add_to_tags=None,
                 suffix='crv',
                 stretch=True,
                 length_attr=False
                 ):
        super(SplineSampler, self).__init__(name,
                                            drivers=drivers,
                                            attr_objs=attr_objs,
                                            degree=degree,
                                            bezier=bezier,
                                            use_tangents=use_tangents,
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

        if not self.sample_params and self.driven:
            self.sample_params = lerp(0.0001, 0.9999, num=len(driven))
        self.sample_base_names = create_chain_names(len(self.sample_params), name=self.namer.name, add_to_tags='sample')

        self.build_spline()

        self.motion_paths, self.sample_matrices = self._create_samples()
        
        if stretch:
            if not length_attr:
                nodes = add_length_attribute(self.curve, self.drivers)
                self.curve_info = nodes[0]
                self.length_mult = nodes[1]
            self._stretch_setup()
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
            # add sample param attribute to curve
            attribute.add_attribute(self.curve_shape, f'sample{i:02d}', dv=self.sample_params[i])
            mpath = common.create_node('motionPath', self.sample_base_names[i], add_to_tags='percent')
            cmds.setAttr(mpath + '.fractionMode', True)
            cmds.setAttr(mpath + '.worldUpVector', *AXIS_STR_TO_MVEC[self.up_axis])
            cmds.setAttr(mpath + '.frontAxis', AXIS_STR_TO_ATTR[self.aim_axis])
            cmds.setAttr(mpath + '.upAxis', AXIS_STR_TO_ATTR[self.up_axis])
            cmds.setAttr(mpath + '.worldUpType', 3)
            cmds.connectAttr(self.curve_shape + f'.sample{i:02d}', mpath + '.uValue')
            cmds.connectAttr(self.curve_shape + '.worldSpace[0]', mpath + '.geometryPath')
            comp_mtx = common.create_node('composeMatrix', self.sample_base_names[i])
            cmds.connectAttr(mpath + '.allCoordinates', comp_mtx + '.inputTranslate')
            cmds.connectAttr(mpath + '.rotate', comp_mtx + '.inputRotate')
            motion_paths.append(mpath)
            sample_matrices.append(comp_mtx)
        return motion_paths, sample_matrices

    def _connect_driven(self):
        for i, obj in enumerate(self.driven):
            if obj:
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
    
    def _stretch_setup(self):
        # add proxy attributes to drivers
        attribute.add_proxy_attribute(self.drivers, 'stretch', min=0.0, max=1.0, dv=1.0)
        attribute.add_proxy_attribute(self.drivers, 'compress', min=0.0, max=1.0, dv=1.0)
        attribute.add_proxy_attribute(self.drivers, 'spline_scale', min=0.0, dv=1.0)
        attribute.add_proxy_attribute(self.drivers, 'spline_offset', dv=0.0)
        
        # scaling spline offset based on arc length
        lengthdiv = common.create_node('multiplyDivide', self.namer.name, add_to_tags=['length', 'rec'])
        offset_mult = common.create_node('multDoubleLinear', self.namer.name, add_to_tags=['spline', 'offset'])
        
        cmds.setAttr(lengthdiv + '.operation', 2)
        cmds.setAttr(lengthdiv + '.input1X', 1.0)
        
        cmds.connectAttr(self.curve_info + '.arcLength', lengthdiv + '.input2X')
        
        cmds.connectAttr(self.drivers[0] + '.spline_offset', offset_mult + '.input1')
        cmds.connectAttr(lengthdiv + '.outputX', offset_mult + '.input2')
        
        # attribute blending setup
        multdiv = common.create_node('multiplyDivide', self.namer.name, add_to_tags=['length', 'factor'])
        compress_blend = common.create_node('blendTwoAttr', self.namer.name, add_to_tags=['compress', 'blend'])
        stretch_blend = common.create_node('blendTwoAttr', self.namer.name, add_to_tags=['stretch', 'blend'])
        length_cond = common.create_node('condition', self.namer.name, add_to_tags=['length', 'factor'])
        
        cmds.setAttr(multdiv + '.operation', 2)
        cmds.setAttr(multdiv + '.input1X', 1.0)
        
        cmds.setAttr(compress_blend + '.input[1]', 1.0)
        
        cmds.setAttr(stretch_blend + '.input[1]', 1.0)
        
        cmds.setAttr(length_cond + '.operation', 2)
        cmds.setAttr(length_cond + '.secondTerm', 1.0)
        
        cmds.connectAttr(self.length_mult + '.output', multdiv + '.input2X')
        cmds.connectAttr(multdiv + '.outputX', compress_blend + '.input[0]')
        cmds.connectAttr(multdiv + '.outputX', stretch_blend + '.input[0]')
        
        cmds.connectAttr(self.drivers[0] + '.compress', compress_blend + '.attributesBlender')
        cmds.connectAttr(self.drivers[0] + '.stretch', stretch_blend + '.attributesBlender')
        
        cmds.connectAttr(self.length_mult + '.output', length_cond + '.firstTerm')
        cmds.connectAttr(compress_blend + '.output', length_cond + '.colorIfFalseR')
        cmds.connectAttr(stretch_blend + '.output', length_cond + '.colorIfTrueR')
        
        sample_blends = []
        # setting up stretch compress for each sample
        for i, mpath in enumerate(self.motion_paths):
            base_name = self.sample_base_names[i]
            
            scale_mult = common.create_node('multDoubleLinear', base_name, add_to_tags=['spline', 'scale'])
            offset_add = common.create_node('addDoubleLinear', base_name, add_to_tags=['spline', 'offset'])
            offset_neg = common.create_node('addDoubleLinear', base_name, add_to_tags=['spline', 'offset', 'neg'])
            offset_comp = common.create_node('composeMatrix', base_name, add_to_tags=['spline', 'offset'])
            offset_mmtx = common.create_node('multMatrix', base_name, add_to_tags=['spline', 'offset'])
            offset_cond = common.create_node('condition', base_name, add_to_tags=['spline', 'offset'])
            factor_mult = common.create_node('multDoubleLinear', base_name, add_to_tags=['length', 'factor'])
            compress_cond = common.create_node('condition', base_name, add_to_tags=['compress'])
            compress_add = common.create_node('addDoubleLinear', base_name, add_to_tags=['compress'])
            compress_mult = common.create_node('multDoubleLinear', base_name, add_to_tags=['compress'])
            compress_comp = common.create_node('composeMatrix', base_name, add_to_tags=['compress'])
            compress_mmtx = common.create_node('multMatrix', base_name, add_to_tags=['compress'])
            compress_blmtx = common.create_node('blendMatrix', base_name, add_to_tags=['compress'])

            sample_blends.append(compress_blmtx)
            
            cmds.setAttr(compress_cond + '.operation', 2)
            cmds.setAttr(compress_cond + '.secondTerm', 1.0)
            cmds.setAttr(compress_cond + '.colorIfTrueR', 1.0)
            cmds.setAttr(compress_cond + '.colorIfFalseR', 0.0)
            
            cmds.setAttr(compress_add + '.input2', -1.0)
            
            cmds.setAttr(offset_cond + '.operation', 4)
            cmds.setAttr(offset_cond + '.colorIfTrueR', 1.0)
            cmds.setAttr(offset_cond + '.colorIfFalseR', 0.0)
            
            cmds.connectAttr(self.curve_shape + f'.sample{i:02d}', scale_mult + '.input1')
            cmds.connectAttr(self.drivers[0] + '.spline_scale', scale_mult + '.input2')
            
            cmds.connectAttr(factor_mult + '.output', offset_add + '.input1')
            cmds.connectAttr(offset_mult + '.output', offset_add + '.input2')

            cmds.connectAttr(offset_add + '.output', mpath + '.uValue', f=True)
            cmds.connectAttr(offset_add + '.output', compress_add + '.input1')
            cmds.connectAttr(offset_add + '.output', compress_cond + '.firstTerm')
            
            cmds.connectAttr(compress_mult + '.output', offset_neg + '.input1')
            cmds.connectAttr(self.curve_info + '.arcLength', offset_neg + '.input2')
            cmds.connectAttr(offset_neg + '.output', offset_comp + '.inputTranslate{}'.format(self.aim_axis[-1].upper()))
            
            cmds.connectAttr(offset_comp + '.outputMatrix', offset_mmtx + '.matrixIn[0]')
            cmds.connectAttr(self.drivers[0] + '.worldMatrix[0]', offset_mmtx + '.matrixIn[1]')
            cmds.connectAttr(offset_mmtx + '.matrixSum', compress_blmtx + '.target[1].targetMatrix')
            
            cmds.connectAttr(offset_add + '.output', offset_cond + '.firstTerm')
            cmds.connectAttr(offset_cond + '.outColorR', compress_blmtx + '.target[1].weight')
            
            cmds.connectAttr(scale_mult + '.output', factor_mult + '.input1')
            cmds.connectAttr(length_cond + '.outColorR', factor_mult + '.input2')
            
            cmds.connectAttr(compress_add + '.output', compress_mult + '.input1')
            cmds.connectAttr(self.curve_info + '.arcLength', compress_mult + '.input2')
            cmds.connectAttr(compress_mult + '.output', compress_comp + '.inputTranslate{}'.format(self.aim_axis[-1].upper()))
            
            cmds.connectAttr(compress_comp + '.outputMatrix', compress_mmtx + '.matrixIn[0]')
            cmds.connectAttr(self.drivers[-1] + '.worldMatrix[0]', compress_mmtx + '.matrixIn[1]')
            cmds.connectAttr(compress_mmtx + '.matrixSum', compress_blmtx + '.target[0].targetMatrix')
            
            cmds.connectAttr(compress_cond + '.outColorR', compress_blmtx + '.target[0].weight')
            
            cmds.connectAttr(self.sample_matrices[i] + '.outputMatrix', compress_blmtx + '.inputMatrix')
            
        self.sample_matrices = sample_blends
        
    def _twist_setup(self):
        driver_nearest_nodes = []
        driver_point_mtxs = []
        rotate_axis = self.aim_axis[-1].upper()
        for i, driver in enumerate(self.drivers):
            nearest_node = common.create_node('nearestPointOnCurve', driver, add_to_tags='twist')
            point_mtx = common.create_node('pointMatrixMult', driver, add_to_tags='twist')
            cmds.setAttr(point_mtx + '.inPoint', *AXIS_STR_TO_MVEC[self.up_axis])
            cmds.setAttr(point_mtx + '.vectorMultiply', True)
            cmds.connectAttr(self.position_nodes[i] + '.outputTranslate', nearest_node + '.inPosition')
            cmds.connectAttr(self.curve_shape + '.worldSpace[0]', nearest_node + '.inputCurve')
            cmds.connectAttr(driver + '.worldMatrix[0]', point_mtx + '.inMatrix')
            driver_nearest_nodes.append(nearest_node)
            driver_point_mtxs.append(point_mtx)
        driven_nearest_nodes = []
        for mpath in self.motion_paths:
            remap = common.create_node('ramp', mpath, add_to_tags='twist')
            nearest_node = common.create_node('nearestPointOnCurve', mpath, add_to_tags='twist')
            cmds.connectAttr(remap + '.outColor',  mpath + '.worldUpVector')
            cmds.connectAttr(mpath + '.allCoordinates', nearest_node + '.inPosition')
            cmds.connectAttr(self.curve_shape + '.worldSpace[0]', nearest_node + '.inputCurve')
            cmds.connectAttr(nearest_node + '.parameter', remap + '.vCoord')
            for i, driver in enumerate(self.drivers):
                cmds.connectAttr(driver_point_mtxs[i] + '.output', remap + '.colorEntryList[{}].color'.format(i))
                cmds.connectAttr(driver_nearest_nodes[i] + '.parameter', remap + '.colorEntryList[{}].position'.format(i))
            driven_nearest_nodes.append(nearest_node)


def add_length_attribute(crv, attr_objs):
    curve_shape = common.get_shape(crv)
    curve_info = common.create_node('curveInfo', crv, add_to_tags='length')
    mult = common.create_node('multDoubleLinear', crv, add_to_tags='length')

    cmds.connectAttr(curve_shape + '.worldSpace[0]', curve_info + '.inputCurve')
    cmds.connectAttr(curve_info + '.arcLength', mult + '.input1')
    cmds.setAttr(mult + '.input2', 1/curve.get_length(curve_shape))
    for obj in attr_objs:
        if not cmds.attributeQuery('length', node=obj, exists=True):
            attribute.add_attribute(obj, 'length', keyable=False)
        cmds.connectAttr(mult + '.output', obj + '.length')
        
    return [curve_info, mult]
