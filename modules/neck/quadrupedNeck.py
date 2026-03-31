import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control
from rigging.parts.base import Base
from rigging.parts.spline import SplineSampler

from rigging.utils.common import create_node
from rigging.utils.attribute import add_proxy_attribute
from rigging.utils.connect import matrix_constraint, aim_matrix_constraint
from rigging.utils.globals import AXIS_NORM, AXIS_NEG, AXIS_STR_TO_VEC
from rigging.utils.name import create_chain_names
from rigging.utils import math



class QuadrupedNeck(RigModule):
    def __init__(self, 
                 name='neck', 
                 inputs={'neck_base' : 'spineEnd_srt',
                         'neck_end' : 'head_ctrl'}, 
                 matrices={'neck_base' : om.MMatrix(),
                           'neck_end' : om.MMatrix()},
                 spaces={'body' : 'body_ctrl', 
                         'global' : 'main_space'},
                 parent='rig_grp',
                 shape_up='+y', 
                 shape_aim='+z',
                 bones_number=5,
                 tangents_offset = 1.0,
                 **kwargs):
        
        self.neck_base_ctrl = None
        self.neck_base_tangent_ctrl = None
        self.neck_ctrl = None
        self.neck_end_tangent_ctrl = None
        self.neck_end = None
        self.bones_samples = []
        self.bones_number = bones_number
        self.tangents_offset = tangents_offset
        self.bones_spline = None

        super(QuadrupedNeck, self).__init__(name=name, 
                                             inputs=inputs, 
                                             matrices=matrices, 
                                             parent=parent,
                                             spaces=spaces,
                                             shape_up=shape_up, 
                                             shape_aim=shape_aim,  
                                             **kwargs)
    
    def _drive_neck_ctrl(self):
        # build spline
        neck_spline = SplineSampler('neck',
                                     drivers=[
                                        self.neck_base_ctrl.ctrl, 
                                        self.neck_base_tangent_ctrl.ctrl, 
                                        self.neck_end_tangent_ctrl.ctrl, 
                                        self.neck_end.obj],
                                     driven = [None, self.neck_ctrl.top, None],
                                     degree=3,
                                     bezier=False,
                                     use_tangents=False,
                                     aim_axis='+z',
                                     up_axis='+y',
                                     offset_matrix=False,
                                     twist=True,
                                     object_up=None,
                                     scale=True,
                                     periodic=False,
                                     add_to_tags=['driver'],
                                     suffix='crv',
                                     stretch=False,
                                     length_attr=False)
        
        cmds.setAttr(f'{neck_spline.curve}.v', False)
        cmds.parent(neck_spline.curve, self.hierarchy['ik'])
    
    def _create_bone_samples(self):
        base_names = create_chain_names(self.bones_number, name=self.name, add_to_tags=['bone', 'sample'])
        for name in base_names:
            sample_srt = Base(name,om.MMatrix(), parent=self.hierarchy['ikfk'], zero=False)
            self.bones_samples.append(sample_srt.obj)
        
        self.bones_spline = SplineSampler('neck',
                                         drivers=[
                                            self.neck_base_ctrl.ctrl, 
                                            self.neck_base_tangent_ctrl.ctrl,
                                            self.neck_ctrl.ctrl,
                                            self.neck_end_tangent_ctrl.ctrl, 
                                            self.neck_end.obj],
                                         driven = self.bones_samples,
                                         attr_objs=[self.neck_base_ctrl.ctrl, self.neck_ctrl.ctrl],
                                         degree=3,
                                         bezier=False,
                                         use_tangents=False,
                                         aim_axis='+z',
                                         up_axis='+y',
                                         offset_matrix=True,
                                         twist=True,
                                         object_up=None,
                                         scale=True,
                                         periodic=False,
                                         add_to_tags=['bones'],
                                         suffix='crv',
                                         stretch=True,
                                         length_attr=True)

        cmds.setAttr(f'{self.bones_spline.curve}.v', False)
        cmds.parent(self.bones_spline.curve, self.hierarchy['ik'])
    
    def _create_tangents_aim_setup(self):
        # add auto aim and ease-in attributes to controls
        add_proxy_attribute([self.neck_base_ctrl.ctrl, self.neck_ctrl.ctrl, self.neck_base_tangent_ctrl.ctrl, self.neck_end_tangent_ctrl.ctrl], 'autoAim', min=0.0, max=1.0, dv=1.0)
        add_proxy_attribute([self.neck_base_ctrl.ctrl, self.neck_ctrl.ctrl, self.neck_base_tangent_ctrl.ctrl, self.neck_end_tangent_ctrl.ctrl], 'aimEaseIn', min=0.0, dv=2)
        
        # create setup nodes
        base_aim = create_node('aimMatrix', 'neck', add_to_tags=['base', 'aim'])
        end_aim = create_node('aimMatrix', 'neck', add_to_tags=['end', 'aim'])
        base_decomp = create_node('decomposeMatrix', 'neck', add_to_tags=['base', 'aim'])
        end_decomp = create_node('decomposeMatrix', 'neck', add_to_tags=['end', 'aim'])
        neck_vec =  create_node('plusMinusAverage', 'neck', add_to_tags='vector')
        base_up = create_node('pointMatrixMult', 'neck', add_to_tags=['base', 'up'])
        vec_mult = create_node('vectorProduct', 'neck', add_to_tags='vector')
        vec_cond = create_node('condition', 'neck', add_to_tags=['vector', 'weight'])
        neck_dist = create_node('distanceBetween', 'neck', add_to_tags=['ends'])
        neck_diff = create_node('plusMinusAverage', 'neck', add_to_tags=['length'])
        neck_result = create_node('plusMinusAverage', 'neck', add_to_tags=['length', 'weight'])
        weight_range = create_node('setRange', 'neck', add_to_tags=['length', 'weight'])
        weight_add = create_node('addDoubleLinear', 'neck', add_to_tags='weight')
        weight_clamp = create_node('clamp', 'neck', add_to_tags='weight')
        weight_env = create_node('multDoubleLinear', 'neck', add_to_tags=['weight', 'envelope'])
        
        # setting attributes
        cmds.setAttr(base_aim + '.primaryInputAxis', *AXIS_STR_TO_VEC[self.shape_aim], type='double3')
        cmds.setAttr(end_aim + '.primaryInputAxis', *AXIS_STR_TO_VEC[AXIS_NEG[self.shape_aim]], type='double3')

        cmds.setAttr(f'{neck_vec}.operation', 2)
        
        cmds.setAttr(f'{base_up}.inPoint{self.shape_up[-1].upper()}', 1.0)
        cmds.setAttr(f'{base_up}.vectorMultiply', True)
        
        cmds.setAttr(f'{vec_mult}.operation', 1)
        cmds.setAttr(f'{vec_mult}.normalizeOutput', True)

        cmds.setAttr(f'{vec_cond}.operation', 4)
        cmds.setAttr(f'{vec_cond}.colorIfTrueR', 1.0)
        cmds.setAttr(f'{vec_cond}.colorIfFalseR', 0.0)
        
        cmds.setAttr(f'{neck_diff}.input1D[0]', cmds.getAttr(f'{self.bones_spline.curve_info}.arcLength'))
        cmds.setAttr(f'{neck_diff}.operation', 2)
        
        cmds.setAttr(f'{neck_result}.input1D[0]', 1.0)
        cmds.setAttr(f'{neck_result}.operation', 2)
        
        cmds.setAttr(f'{weight_range}.minX', 0.0)
        cmds.setAttr(f'{weight_range}.maxX', 1.0)
        cmds.setAttr(f'{weight_range}.oldMinX', cmds.getAttr(f'{neck_result}.output1D'))
        
        cmds.setAttr(f'{weight_clamp}.minR', 0.0)
        cmds.setAttr(f'{weight_clamp}.maxR', 1.0)
        
        # connections
        cmds.connectAttr(f'{self.namer.name}_end_dmm.outputTranslate', f'{neck_vec}.input3D[0]')
        cmds.connectAttr(f'{self.namer.name}_base_dmm.outputTranslate', f'{neck_vec}.input3D[1]')
        cmds.connectAttr(f'{neck_vec}.output3D', f'{vec_mult}.input2')
        
        cmds.connectAttr(f'{self.neck_base_ctrl.ctrl}.worldMatrix[0]', f'{base_up}.inMatrix')
        cmds.connectAttr(f'{base_up}.output', f'{vec_mult}.input1')
        cmds.connectAttr(f'{vec_mult}.outputX', f'{vec_cond}.firstTerm')
        
        cmds.connectAttr(f'{vec_cond}.outColorR', f'{weight_add}.input1')
        
        cmds.connectAttr(f'{self.neck_base_ctrl.ctrl}.worldMatrix[0]', f'{neck_dist}.inMatrix1')
        cmds.connectAttr(f'{self.neck_end.obj}.worldMatrix[0]', f'{neck_dist}.inMatrix2')
        cmds.connectAttr(f'{neck_dist}.distance', f'{neck_diff}.input1D[1]')
        
        cmds.connectAttr(f'{neck_diff}.output1D', f'{neck_result}.input1D[1]')
        cmds.connectAttr(f'{neck_result}.output1D', f'{weight_range}.valueX')
        cmds.connectAttr(f'{self.neck_base_ctrl.ctrl}.aimEaseIn', f'{weight_range}.oldMaxX')
        cmds.connectAttr(f'{weight_range}.outValueX', f'{weight_add}.input2')
        
        cmds.connectAttr(f'{weight_add}.output', f'{weight_env}.input1')
        cmds.connectAttr(f'{self.neck_base_ctrl.ctrl}.autoAim', f'{weight_env}.input2')
        cmds.connectAttr(f'{weight_env}.output', f'{weight_clamp}.inputR')
        
        cmds.connectAttr(f'{weight_clamp}.outputR', f'{base_aim}.envelope')
        cmds.connectAttr(f'{weight_clamp}.outputR', f'{end_aim}.envelope')
        
        cmds.connectAttr(f'{self.neck_base_ctrl.ctrl}.worldMatrix[0]', f'{base_aim}.inputMatrix')
        cmds.connectAttr(f'{self.neck_end.obj}.worldMatrix[0]', f'{end_aim}.inputMatrix')
        cmds.connectAttr(f'{self.neck_end.obj}.worldMatrix[0]', f'{base_aim}.primaryTargetMatrix')
        cmds.connectAttr(f'{self.neck_base_ctrl.ctrl}.worldMatrix[0]', f'{end_aim}.primaryTargetMatrix')
        cmds.connectAttr(f'{base_aim}.outputMatrix', f'{base_decomp}.inputMatrix')
        cmds.connectAttr(f'{end_aim}.outputMatrix', f'{end_decomp}.inputMatrix')
        
        cmds.connectAttr(f'{base_decomp}.outputRotate{AXIS_NORM[self.shape_aim][-1].upper()}', f'{self.neck_base_tangent_ctrl.top}.r{AXIS_NORM[self.shape_aim][-1]}')
        cmds.connectAttr(f'{end_decomp}.outputRotate{AXIS_NORM[self.shape_aim][-1].upper()}', f'{self.neck_end_tangent_ctrl.top}.r{AXIS_NORM[self.shape_aim][-1]}')
        
    def build(self):
        # Building controls and tangents drivers
        self.neck_base_ctrl = Control(
                                    'neck',
                                    self.module_matrices['neck_base'],
                                    lock_s='xyz',
                                    shape_type='cube',
                                    parent=self.hierarchy['ik'],
                                    space_names=['body', 'world'],
                                    space_drivers=[self.spaces['body'], self.spaces['global']],
                                    split_channels=True,
                                    shape_aim=self.shape_aim,
                                    shape_up=self.shape_up,
                                    add_to_tags = 'base',
                                    size=5,
                                    line_width=3.0)
        
        matrix_constraint(self.inputs['neck_base'], self.neck_base_ctrl.zero, store=True)
        
        self.neck_base_tangent_ctrl = Control(
                                        'neck',
                                        self.module_matrices['neck_base'],
                                        lock_s='xyz',
                                        ofs=True,
                                        shape_type='pin',
                                        parent=self.neck_base_ctrl.ctrl,
                                        space_names=['body', 'world'],
                                        split_channels=True,
                                        shape_aim=self.shape_aim,
                                        shape_up=self.shape_up,
                                        add_to_tags = ['base', 'tangent'],
                                        size=2,
                                        line_width=3.0)
        
        # base tangent offset position
        bto = [elem * self.tangents_offset for elem in AXIS_STR_TO_VEC[self.shape_aim]]
        
        cmds.setAttr(f'{self.neck_base_tangent_ctrl.ofs}.t', bto[0], bto[1], bto[2], type='double3')
        
        self.neck_ctrl = Control(
                            'neck',
                            om.MMatrix(),
                            lock_s='xyz',
                            shape_type='square',
                            parent=self.hierarchy['ik'],
                            shape_aim=AXIS_NORM[self.shape_aim],
                            shape_up=AXIS_NORM[self.shape_up],
                            size=4,
                            line_width=3.0)
        
        self.neck_end = Base('neck', self.module_matrices['neck_end'], parent=self.hierarchy['ik'], add_to_tags='end')
        
        matrix_constraint(self.inputs['neck_end'], self.neck_end.zero, store=True)
        
        self.neck_end_tangent_ctrl = Control(
                                        'neck',
                                        self.module_matrices['neck_end'],
                                        lock_s='xyz',
                                        ofs=True,
                                        shape_type='pin',
                                        parent=self.neck_end.obj,
                                        space_names=['body', 'world'],
                                        split_channels=True,
                                        shape_aim=self.shape_aim,
                                        shape_up=self.shape_up,
                                        add_to_tags = ['end', 'tangent'],
                                        size=2,
                                        line_width=3.0)
        
        # end tangent offset position
        eto = [elem * self.tangents_offset * -1.0 for elem in AXIS_STR_TO_VEC[self.shape_aim]]
        
        cmds.setAttr(f'{self.neck_end_tangent_ctrl.ofs}.t', eto[0], eto[1], eto[2], type='double3')
        
        # adding tengent controls visibility attribute to main controls
        add_proxy_attribute([self.neck_base_ctrl.ctrl, self.neck_ctrl.ctrl],  'tangentsVisibility', attr_type='bool', dv=False)
        cmds.connectAttr(f'{self.neck_base_ctrl.ctrl}.tangentsVisibility', f'{self.neck_base_tangent_ctrl.top}.v')
        cmds.connectAttr(f'{self.neck_base_ctrl.ctrl}.tangentsVisibility', f'{self.neck_end_tangent_ctrl.top}.v')
        
        # Driving neck control
        self._drive_neck_ctrl()
        
        self.module_ctrls.extend([
                        self.neck_base_ctrl.ctrl,
                        self.neck_base_tangent_ctrl.ctrl,
                        self.neck_ctrl.ctrl,
                        self.neck_end_tangent_ctrl.ctrl
                    ])

        # drive bone samples
        self._create_bone_samples()
        
        # create tangents auto aim setup
        self._create_tangents_aim_setup()
        
test = QuadrupedNeck(
     matrices={'neck_base' : math.get_matrix('spine_end'),
               'neck_end' : math.get_matrix('head')},
)