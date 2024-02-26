import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control
from rigging.parts.ikfk import IKFK

from rigging.utils import math
from rigging.utils.connect import matrix_constraint, connect, constraint



class Hand(RigModule):
    def __init__(self, 
                 name='hand_l', 
                 inputs={'hand_fk' : 'lowerarm_l_fk_ctrl', 
                         'hand_ik' : 'body_ctrl',
                         'hand_ik_driver_position' : 'arm_03_l_ikfk_srt'}, 
                 matrices={'hand' : om.MMatrix()},
                 spaces={'clavicle' : 'clavicle_l_ctrl', 
                         'body' : 'body_ctrl', 
                         'global': 'main_space'},
                 parent='rig_grp',
                 ikfk='global_ctrl.l_arm',
                 **kwargs):
        
        self.ikfk = ikfk
        self.output = None
        super(Hand, self).__init__(name=name, 
                                   inputs=inputs, 
                                   matrices=matrices, 
                                   parent=parent,
                                   spaces=spaces, 
                                   **kwargs)


        cmds.connectAttr(self.ikfk, '{}.ik'.format(self.top_group))
        cmds.connectAttr(self.ikfk + 'Reversed', '{}.fk'.format(self.top_group))

    def build(self):
        # Building controls
        
        # FK hand control
        hand_fk_name = self.namer.create_name(add_to_tags='fk_tmp')
        hand_fk_ctrl = Control(hand_fk_name, 
                               self.module_matrices['hand'],
                               parent=self.hierarchy['fk'],
                               lock_t='xyz',
                               lock_s='xyz',
                               shape_up='+x', 
                               shape_aim='+z', 
                               size=7.0, 
                               line_width=3.0)


        matrix_constraint(self.inputs['hand_fk'], hand_fk_ctrl.top, store=True)

        self.module_ctrls.append(hand_fk_ctrl.ctrl)

        # IK hand control
        hand_ik_name = self.namer.create_name(add_to_tags='ik_tmp')
        hand_ik_ctrl = Control(hand_ik_name, 
                               self.module_matrices['hand'],
                               parent=self.hierarchy['ik'],
                               lock_s='xyz',
                               shape_type='cube',
                               size=8.0, 
                               line_width=3.0,
                               space_names=self.spaces.keys(),
                               space_drivers=self.spaces.values())
        
        matrix_constraint(self.inputs['hand_ik'], hand_ik_ctrl.top, store=True)
        self.module_ctrls.append(hand_ik_ctrl.ctrl)
        # Build IKFK setup
        hand_ikfk = IKFK(self.name,
                          [self.module_matrices['hand']],
                          attr_obj=self.ikfk.split('.')[0],
                          blend_attr=self.ikfk.split('.')[-1],
                          parent=self.hierarchy['ikfk'],
                          driverA_tags='fk_tmp',
                          driverB_tags='ik_tmp',
                          driven_tags='ikfk_tmp')

        matrix_constraint(hand_ik_ctrl.bottom, hand_ikfk.driverB.top, attr='r')
        matrix_constraint(self.inputs['hand_ik_driver_position'], hand_ikfk.driverB.top, attr='ts',store=True)
        matrix_constraint(hand_fk_ctrl.ctrl, hand_ikfk.driverA.top, store=True)
        
        self.output = hand_ikfk.driven.top
        
        
        