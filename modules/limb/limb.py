import maya.cmds as cmds
import maya.api.OpenMaya as om

from math import degrees

from rigging.modules.module import RigModule

from rigging.parts.base import Base
from rigging.parts.control import Control
from rigging.parts.ikfk import IKFK
from rigging.parts.ik import IK

from rigging.utils import math
from rigging.utils.connect import matrix_constraint, constraint
from rigging.utils.globals import AXIS_STR_TO_VEC, AXIS_NORM
from rigging.utils.common import create_node



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
        

class ZLimb(RigModule):
    def __init__(self, 
                 name='leg_l',
                 fk_names=['upperleg', 'lowerleg', 'tarsal', 'ankle'],
                 inputs={'input_fk' : 'pelvis_ctrl', 
                         'polevector' : 'main_space', 
                         'input_ik' : 'foot_l_ankle_srt',
                         'input_footroll' : 'foot_l_ik_ctrl'}, 
                 spaces={'body' : 'body_ctrl', 
                         'global' : 'main_space', 
                         'foot' : 'foot_l_ankle_srt'},
                 matrices={'bone01' : om.MMatrix(),
                           'bone02' : om.MMatrix(),
                           'bone03' : om.MMatrix(),
                           'bone04' : om.MMatrix()}, 
                 parent='rig_grp',
                 ikfk='global_ctrl.l_leg',
                 pv_distance=50.0,
                 **kwargs):

        self.ikfk = ikfk
        self.fk_names = fk_names
        self.footroll_output=None
        self.pv_distance = pv_distance
        self.output = None
        super(ZLimb, self).__init__(name=name, 
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
        
        # FK third control
        third_fk_name = '{}_{}_fk_tmp'.format(self.fk_names[2], self.side)
        third_fk_ctrl = Control(third_fk_name, 
                                 self.module_matrices['bone03'],
                                 parent=second_fk_ctrl.bottom,
                                 lock_t='xyz',
                                 lock_s='xyz',
                                 shape_up='+x', 
                                 shape_aim='+z', 
                                 size=8.0, 
                                 line_width=3.0)
        
        # FK last driver srt
        fourth_fk_name = '{}_{}_fk_tmp'.format(self.fk_names[3], self.side)
        fourth_fk_srt = Base(fourth_fk_name, 
                             self.module_matrices['bone04'],
                             parent=third_fk_ctrl.bottom)

        self.module_ctrls.extend([first_fk_ctrl.ctrl, second_fk_ctrl.ctrl, third_fk_ctrl.ctrl])
        
        # FK driver objects
        fk_drivers = [first_fk_ctrl.ctrl, second_fk_ctrl.ctrl, third_fk_ctrl.ctrl, fourth_fk_srt.obj]
        
        # Adding FK controls to FK set
        fk_ctrls_set = cmds.sets([first_fk_ctrl.ctrl, second_fk_ctrl.ctrl, third_fk_ctrl.ctrl], name=self.namer.create_name(add_to_tags='fk',add_to_suffix='controls'))
        cmds.setAttr('{}.ihi'.format(fk_ctrls_set), True)
        self.module_ctrls.append(fk_ctrls_set)
        
        # IK ankle driver
        ankle_ik_name = '{}_{}'.format(self.fk_names[3], self.side)
        ankle_ik_srt = Base(ankle_ik_name, 
                           self.module_matrices['bone04'],
                           add_to_tags='ik',
                           parent=self.hierarchy['ik'])
        
        #cmds.setAttr('{}.v'.format(ankle_ik_srt.top), False)
        matrix_constraint(self.inputs['input_ik'], ankle_ik_srt.top, store=True)
        
        # IK leg base srt
        base_ik_name = '{}_{}'.format(self.fk_names[0], self.side)
        base_ik_ctrl = Control(base_ik_name, 
                              self.module_matrices['bone01'],
                              parent=ankle_ik_srt.obj,
                              add_to_tags='ik',
                              lock_s='xyz',
                              shape_type='pin',
                              shape_up='+y', 
                              shape_aim='+z', 
                              size=10.0, 
                              line_width=3.0)


        matrix_constraint(self.inputs['input_fk'], base_ik_ctrl.top, store=True)

        # IK tarsal ctrl
        tarsal_ik_name = '{}_{}'.format(self.fk_names[2], self.side)
        tarsal_ik_ctrl = Control(tarsal_ik_name, 
                                 self.module_matrices['bone04'],
                                 parent=ankle_ik_srt.obj,
                                 ofs=True, 
                                 add_to_tags='ik',
                                 lock_t='xyz',
                                 lock_s='xyz',
                                 shape_type='cube',
                                 shape_up='+x', 
                                 shape_aim='+z', 
                                 size=8.0, 
                                 line_width=3.0)
        
        # Tarsal auto aiming setup
        axis_vec, axis_str = math.get_closest_axis_to_vector(self.module_matrices['bone04'], self.module_matrices['bone01'])
        
        # Aming at base ctrl
        constraint(
                base_ik_ctrl.ctrl, 
                tarsal_ik_ctrl.top, 
                aim_vector=axis_vec,
                world_up_object=base_ik_ctrl.ctrl,
                world_up_type='none',
                up_vector=AXIS_STR_TO_VEC[AXIS_NORM[axis_str]], 
                type='aimConstraint'
        )
        
        # building auto offset based on leg extension
        self._setup_tarsal_auto_offset(tarsal_ik_ctrl, base_ik_ctrl, axis_str)

        # IK pole vector control
        pv_position = math.get_polevector_position_vector([self.module_matrices['bone01'], 
                                                           self.module_matrices['bone02'], 
                                                           self.module_matrices['bone03']],
                                                           pv_distance=self.pv_distance)
                                                           
        pv_mtx = math.create_matrix(translation=[pv_position.x, pv_position.y, pv_position.z], rotation=[-90.0, .0, .0])
        if self.side == 'r':
            pv_mtx = math.create_matrix(translation=[pv_position.x, pv_position.y, pv_position.z], rotation=[90.0, .0, 180.0])

        pv_name = self.namer.create_name(add_to_tags='pv_ik_tmp')
        pv_space_names = list(self.spaces.keys())
        pv_space_names.append('ik_base')
        pv_spaces = list(self.spaces.values())
        pv_spaces.append(base_ik_ctrl.ctrl)
        pv_ctrl = Control(pv_name, 
                          pv_mtx,
                          parent=self.hierarchy['ik'],
                          lock_r='xyz',
                          lock_s='xyz',
                          shape_type='diamond',
                          size=4.0, 
                          line_width=5.0,
                          space_names=pv_space_names,
                          space_drivers=pv_spaces)
        
        if self.side == 'r':
            cmds.setAttr('{}.scaleY'.format(pv_ctrl.top), -1.0)

        constraint(self.inputs['polevector'], pv_ctrl.top, type='parentConstraint', store=True)
        constraint(self.inputs['polevector'], pv_ctrl.top, type='scaleConstraint', store=True)

        self.module_ctrls.append(pv_ctrl.ctrl)
        
        # Build main IK chain
        main_ik_chain = IK(self.name,
                      [self.module_matrices['bone01'], 
                       self.module_matrices['bone02'], 
                       self.module_matrices['bone03']],
                      add_to_tags='ik',
                      parent=self.hierarchy['ik'],
                      handle_parent=tarsal_ik_ctrl.ctrl,
                      pole_vector=pv_ctrl.ctrl,
                      solver='ikRPsolver',
                      joint_display='none')
        
        matrix_constraint(base_ik_ctrl.ctrl, main_ik_chain.top, store=True)
        
        cmds.setAttr('{}.v'.format(main_ik_chain.ik_handle), False)
        
        ik_drivers = main_ik_chain.objs[:-1]
        
        # Build tarsal IK chain
        tarsal_ik_chain = IK(self.fk_names[2],
                          [self.module_matrices['bone03'], 
                           self.module_matrices['bone04']],
                          add_to_tags='ik',
                          parent=self.hierarchy['ik'],
                          handle_parent=tarsal_ik_ctrl.ctrl,
                          solver='ikSCsolver',
                          joint_display='none')
        
        matrix_constraint(main_ik_chain.bottom, tarsal_ik_chain.top, store=True)
        
        cmds.setAttr('{}.v'.format(tarsal_ik_chain.ik_handle), False)
        
        ik_drivers.extend(tarsal_ik_chain.objs)

        # Build footroll position chain
        footroll_ik_srt = Base(
                        '{}_{}'.format(self.fk_names[2], self.side),
                        self.module_matrices['bone04'],
                        add_to_tags='ik_footroll',
                        parent=self.hierarchy['ik'])
        
        cmds.setAttr('{}.v'.format(footroll_ik_srt.top), False)
        matrix_constraint(self.inputs['input_footroll'], footroll_ik_srt.top, store=True)

        footroll_ik_chain = IK(self.name,
                      [self.module_matrices['bone01'], 
                       self.module_matrices['bone02'], 
                       self.module_matrices['bone03'],
                       self.module_matrices['bone04']],
                      add_to_tags='ik_footroll',
                      parent=self.hierarchy['ik'],
                      handle_parent=footroll_ik_srt.obj,
                      solver='ikSCsolver',
                      joint_display='none')
        
        self.footroll_output = footroll_ik_chain.bottom
        matrix_constraint(self.inputs['input_fk'], footroll_ik_chain.top, store=True)

        
        # Build IKFK setup
        limb_ikfk = IKFK(self.name,
                         [self.module_matrices['bone01'],
                         self.module_matrices['bone02'],
                         self.module_matrices['bone03'],
                         self.module_matrices['bone04']],
                         attr_obj=self.ikfk.split('.')[0],
                         blend_attr=self.ikfk.split('.')[-1],
                         parent=self.hierarchy['ikfk'],
                         driverA_tags='fk_tmp',
                         driverB_tags='ik_tmp',
                         driven_tags='ikfk_tmp')
        
        self.output = limb_ikfk.driven.bottom
        
        for i in range(4):
            # IK driver constraint
            matrix_constraint(ik_drivers[i], limb_ikfk.driverB.objs[i])
            
            # FK driver constraint
            matrix_constraint(fk_drivers[i], limb_ikfk.driverA.objs[i])
        
    def _setup_tarsal_auto_offset(self, driven_obj, driver_obj, aim_axis):
        ''' Uses the difference between the total leg length and the root to tarsal control length 
            to calculate a rotation offset to be applied to the tarsal control.
            When the leg extends the offset will make the leg bones align. Z -> \
        '''
        
        # Getting leg total length
        leg_length = (
                math.get_vector_between(self.module_matrices['bone01'], self.module_matrices['bone02']).length() +
                math.get_vector_between(self.module_matrices['bone03'], self.module_matrices['bone02']).length() +
                math.get_vector_between(self.module_matrices['bone04'], self.module_matrices['bone03']).length()
        )
        
        # getting tarsal angle relative to ik vector
        ik_vec = math.get_vector_between(self.module_matrices['bone04'], self.module_matrices['bone01'])
        tarsal_vec = math.get_vector_between(self.module_matrices['bone04'], self.module_matrices['bone03'])
        tarsal_angle = degrees(ik_vec.angle(tarsal_vec))
        
        # creating setup nodes
        dist = create_node('distanceBetween', self.fk_names[-2], add_to_tags='auto_offset')
        mult = create_node('multDoubleLinear', self.fk_names[-2], add_to_tags='auto_offset')
        add = create_node('addDoubleLinear', self.fk_names[-2], add_to_tags='auto_offset')
        rng = create_node('setRange', self.fk_names[-2], add_to_tags='auto_offset')
        
        # connecting nodes
        cmds.connectAttr('{}.worldMatrix[0]'.format(driver_obj.ctrl), '{}.inMatrix1'.format(dist))
        cmds.connectAttr('{}.worldMatrix[0]'.format(driven_obj.top), '{}.inMatrix2'.format(dist))
        
        cmds.setAttr('{}.input2'.format(mult), -1.0)
        cmds.connectAttr('{}.distance'.format(dist), '{}.input1'.format(mult))
        
        cmds.setAttr('{}.input1'.format(add), leg_length)
        cmds.connectAttr('{}.output'.format(mult), '{}.input2'.format(add))
        
        cmds.setAttr('{}.minX'.format(rng),tarsal_angle)
        cmds.setAttr('{}.oldMaxX'.format(rng), cmds.getAttr('{}.output'.format(add)))
        cmds.connectAttr('{}.output'.format(add), '{}.valueX'.format(rng))
        
        rotate_axis = AXIS_NORM[aim_axis][-1]
        cmds.connectAttr('{}.outValueX'.format(rng), '{}.r{}'.format(driven_obj.ofs, rotate_axis))