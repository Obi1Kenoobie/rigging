import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.base import Base
from rigging.parts.control import Control
from rigging.parts.ikfk import IKFK
from rigging.parts.ik import IK

from rigging.utils import math
from rigging.utils.connect import matrix_constraint, constraint



class Limb(RigModule):
    def __init__(self, 
                 name='arm_l',
                 fk_names=['upperarm', 'lowerarm', 'wrist'],
                 inputs={'input_fk' : 'clavicle_l_ctrl', 
                         'polevector' : 'main_space', 
                         'input_ik' : 'hand_01_l_ik_srt'}, 
                 spaces={'clavicle' : 'clavicle_l_ctrl', 
                         'body' : 'body_ctrl', 
                         'global' : 'main_space', 
                         'hand' : 'hand_01_l_ik_srt'},
                 matrices={'bone01' : om.MMatrix(),
                           'bone02' : om.MMatrix(),
                           'bone03' : om.MMatrix()}, 
                 parent='rig_grp',
                 ikfk='global_ctrl.l_arm',
                 isLeg=False,
                 pv_distance=50.0,
                 **kwargs):

        self.ikfk = ikfk
        self.fk_names = fk_names
        self.isLeg = isLeg
        self.footroll_output=None
        self.pv_distance = pv_distance
        self.output = None
        super(Limb, self).__init__(name=name, 
                                   inputs=inputs, 
                                   matrices=matrices, 
                                   parent=parent,
                                   spaces=spaces,
                                   **kwargs)


        cmds.connectAttr(self.ikfk, '{}.ik'.format(self.top_group))
        cmds.connectAttr(self.ikfk + 'Reversed', '{}.fk'.format(self.top_group))

    def build(self):
        # Building controls
        # FK first control
        first_fk_name = '{}_{}_fk_tmp'.format(self.fk_names[0], self.side)
        first_fk_ctrl = Control(first_fk_name, 
                                self.module_matrices['bone01'],
                                parent=self.hierarchy['fk'],
                                lock_t='xyz',
                                lock_s='xyz',
                                shape_up='+x', 
                                shape_aim='+z', 
                                size=12.0, 
                                line_width=3.0,
                                space_names=list(self.spaces.keys())[:-1],
                                space_drivers=list(self.spaces.values())[:-1],
                                split_channels=True)
        
        matrix_constraint(self.inputs['input_fk'], first_fk_ctrl.top, store=True)
        
        # FK second control
        second_fk_name = '{}_{}_fk_tmp'.format(self.fk_names[1], self.side)
        second_fk_ctrl = Control(second_fk_name, 
                                 self.module_matrices['bone02'],
                                 parent=first_fk_ctrl.bottom,
                                 lock_t='xyz',
                                 lock_s='xyz',
                                 shape_up='+x', 
                                 shape_aim='+z', 
                                 size=8.0, 
                                 line_width=3.0)
        
        # FK last driver srt
        third_fk_name = '{}_{}_fk_tmp'.format(self.fk_names[2], self.side)
        third_fk_srt = Base(third_fk_name, 
                             self.module_matrices['bone03'],
                             parent=second_fk_ctrl.bottom)

        self.module_ctrls.extend([first_fk_ctrl.ctrl, second_fk_ctrl.ctrl])
        
        # FK driver objects
        fk_drivers = [first_fk_ctrl.ctrl, second_fk_ctrl.ctrl, third_fk_srt.obj]
        
        # Adding FK controls to FK set
        fk_ctrls_set = cmds.sets([first_fk_ctrl.ctrl, second_fk_ctrl.ctrl], name=self.namer.create_name(add_to_tags='fk',add_to_suffix='controls'))
        cmds.setAttr('{}.ihi'.format(fk_ctrls_set), True)
        self.module_ctrls.append(fk_ctrls_set)

        # IK hand driver
        hand_ik_name = '{}_{}'.format(self.fk_names[2], self.side)
        hand_ik_srt = Base(hand_ik_name, 
                           self.module_matrices['bone03'],
                           add_to_tags='ik',
                           parent=self.hierarchy['ik'])
        
        cmds.setAttr('{}.v'.format(hand_ik_srt.top), False)
        matrix_constraint(self.inputs['input_ik'], hand_ik_srt.top, store=True)
        
        # IK pole vector control
        pv_position = math.get_polevector_position_vector([self.module_matrices['bone01'], 
                                                           self.module_matrices['bone02'], 
                                                           self.module_matrices['bone03']],
                                                           pv_distance=self.pv_distance)
                                                           
        pv_mtx = math.create_matrix(translation=[pv_position.x, pv_position.y, pv_position.z], rotation=[-90.0, .0, .0])
        if self.side == 'r':
            pv_mtx = math.create_matrix(translation=[pv_position.x, pv_position.y, pv_position.z], rotation=[90.0, .0, 180.0])

        pv_name = self.namer.create_name(add_to_tags='pv_ik_tmp')
        pv_ctrl = Control(pv_name, 
                          pv_mtx,
                          parent=self.hierarchy['ik'],
                          lock_r='xyz',
                          lock_s='xyz',
                          shape_type='diamond',
                          size=4.0, 
                          line_width=5.0,
                          space_names=self.spaces.keys(),
                          space_drivers=self.spaces.values())
        
        if self.side == 'r':
            cmds.setAttr('{}.scaleY'.format(pv_ctrl.top), -1.0)

        constraint(self.inputs['polevector'], pv_ctrl.top, type='parentConstraint', store=True)
        constraint(self.inputs['polevector'], pv_ctrl.top, type='scaleConstraint', store=True)

        self.module_ctrls.append(pv_ctrl.ctrl)
        
        # Build IK chain
        ik_chain = IK(self.name,
                      [self.module_matrices['bone01'], 
                       self.module_matrices['bone02'], 
                       self.module_matrices['bone03']],
                      add_to_tags='ik',
                      parent=self.hierarchy['ik'],
                      handle_parent=hand_ik_srt.obj,
                      pole_vector=pv_ctrl.ctrl,
                      solver='ikRPsolver',
                      joint_display='none')
        
        matrix_constraint(self.inputs['input_fk'], ik_chain.top, store=True)
        
        # Build footroll position chain
        if self.isLeg:
            footroll_ik_srt = Base(
                            '{}_{}'.format(self.fk_names[2], self.side),
                            self.module_matrices['bone03'],
                            add_to_tags='ik_footroll',
                            parent=self.hierarchy['ik'])
            
            cmds.setAttr('{}.v'.format(footroll_ik_srt.top), False)
            matrix_constraint(self.inputs['input_footroll'], footroll_ik_srt.top, store=True)
            footroll_ik_chain = IK(self.name,
                          [self.module_matrices['bone01'], 
                           self.module_matrices['bone02'], 
                           self.module_matrices['bone03']],
                          add_to_tags='ik_footroll',
                          parent=self.hierarchy['ik'],
                          handle_parent=footroll_ik_srt.obj,
                          pole_vector=pv_ctrl.ctrl,
                          solver='ikRPsolver',
                          joint_display='none')
            
            self.footroll_output = footroll_ik_chain.bottom
            matrix_constraint(self.inputs['input_fk'], footroll_ik_chain.top, store=True)
        
        # Build IKFK setup
        limb_ikfk = IKFK(self.name,
                         [self.module_matrices['bone01'],
                         self.module_matrices['bone02'],
                         self.module_matrices['bone03']],
                         attr_obj=self.ikfk.split('.')[0],
                         blend_attr=self.ikfk.split('.')[-1],
                         parent=self.hierarchy['ikfk'],
                         driverA_tags='fk_tmp',
                         driverB_tags='ik_tmp',
                         driven_tags='ikfk_tmp')
        
        self.output = limb_ikfk.driven.bottom
        
        for i in range(3):
            # IK driver constraint
            matrix_constraint(ik_chain.objs[i], limb_ikfk.driverB.objs[i])
            
            # FK driver constraint
            matrix_constraint(fk_drivers[i], limb_ikfk.driverA.objs[i])
        
        
        
        
        