import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control
from rigging.parts.ikfk import IKFK
from rigging.parts.footroll import FootRoll

from rigging.utils import math
from rigging.utils.connect import matrix_constraint, connect, constraint
from rigging.utils.attribute import add_attribute


class Foot(RigModule):
    def __init__(self, 
                 name='foot_l', 
                 inputs={'foot_fk' : 'foot_l_fk_srt', 
                         'foot_ik' : 'body_offset_ctrl',
                         'foot_ik_driver_position' : 'leg_03_l_ikfk_srt'}, 
                 matrices={'foot' : om.MMatrix(),
                           'foot_ik':om.MMatrix(),
                           'ball' : om.MMatrix()},
                 spaces={'pelvis' : 'pelvis_ctrl',
                         'body' : 'body_ctrl', 
                         'global': 'main_space'},
                 parent='rig_grp',
                 ikfk='global_ctrl.l_leg',
                 heel_offset=-6.0, 
                 tip_offset=6.0, 
                 aim_axis='-y', 
                 up_axis='+z',
                 **kwargs):
        
        self.ikfk = ikfk
        self.output = None
        super(Foot, self).__init__(name=name, 
                                   inputs=inputs, 
                                   matrices=matrices, 
                                   parent=parent,
                                   spaces=spaces,
                                   heel_offset=heel_offset, 
                                   tip_offset=tip_offset, 
                                   aim_axis=aim_axis, 
                                   up_axis=up_axis,  
                                   **kwargs)


        cmds.connectAttr(self.ikfk, '{}.ik'.format(self.top_group))
        cmds.connectAttr(self.ikfk + 'Reversed', '{}.fk'.format(self.top_group))

    def build(self, **kwargs):
        # control color
        ctrl_color = [0.2, 0.2, 1.0]
        if self.side == 'r':
           ctrl_color = [1.0, 0.3, 0.3]

        # foot roll controls syntax list
        syntax_list = ['namespace', 'part', 'tags', 'partindex', 'index', 'side', 'suffix']

        # Calculating important matrices
        ball_mtx = math.get_align_matrix(self.module_matrices['foot'], self.module_matrices['ball'])
        ball_ik_mtx = math.get_align_matrix(ball_mtx, self.module_matrices['ball'], source_aim='+z', source_up='+y', target_aim='+x', target_up='+y')

        # Building controls
        
        
        ### FK CONTROLS ###
        # FK foot control
        foot_fk_name = self.namer.create_name(add_to_tags='fk_tmp')
        foot_fk_ctrl = Control(foot_fk_name, 
                               self.module_matrices['foot'],
                               parent=self.hierarchy['fk'],
                               lock_t='xyz',
                               lock_s='xyz',
                               shape_up='+x', 
                               shape_aim='+z', 
                               size=7.0, 
                               line_width=3.0)


        matrix_constraint(self.inputs['foot_fk'], foot_fk_ctrl.top, store=True)
        
        # FK ball control
        ball_fk_ctrl = Control('ball_{}'.format(self.side), 
                               ball_mtx,
                               parent=foot_fk_ctrl.bottom,
                               add_to_tags=['fk'],
                               lock_r='xy',
                               lock_t='xyz',
                               lock_s='xyz',
                               shape_up='+y', 
                               shape_aim='+z', 
                               size=6.0, 
                               line_width=3.0)
        
        self.module_ctrls.extend([foot_fk_ctrl.ctrl, ball_fk_ctrl.ctrl])
        
        # Building foot roll setup
        footroll = FootRoll(self.name, 
                            self.module_matrices['foot'], 
                            ball_mtx, 
                            parent=self.hierarchy['ik'], 
                            heel_offset=kwargs['heel_offset'], 
                            tip_offset=kwargs['tip_offset'], 
                            aim_axis=kwargs['aim_axis'], 
                            up_axis=kwargs['up_axis'])
        
        matrix_constraint(self.inputs['foot_ik_driver_position'], footroll.foot.top, attr='t', store=True)
        
        ### IK CONTROLS ###
        # IK foot control
        foot_ik_ctrl = Control(self.name, 
                               self.module_matrices['foot_ik'],
                               parent=self.hierarchy['ik'],
                               add_to_tags=['ik'],
                               lock_s='xyz',
                               shape_type='cube',
                               size=10.0, 
                               line_width=3.0,
                               space_names=self.spaces.keys(),
                               space_drivers=self.spaces.values())
        
        # mirroring fix cus Maya doesn't like scaling the way I tell it to
        if self.side == 'r':
            cmds.setAttr('{}.scaleY'.format(foot_ik_ctrl.top), -1.0)
        
        matrix_constraint(foot_ik_ctrl.ctrl, footroll.foot.top, attr='rs')
        
        constraint(self.inputs['foot_ik'], foot_ik_ctrl.top, type='parentConstraint', store=True)
        constraint(self.inputs['foot_ik'], foot_ik_ctrl.top, type='scaleConstraint', store=True)

        # Foot Roll control
        footroll_ctrl = Control(self.name, 
                                self.module_matrices['foot'],
                                parent=footroll.ankle.bottom,
                                add_to_tags=['roll'],
                                syntax_list=syntax_list,
                                lock_r='xy',
                                lock_t='xyz',
                                lock_s='xyz',
                                shape_type='joint',
                                shape_up='+x', 
                                shape_aim='+z',
                                rgb_color=ctrl_color,
                                size=6.0, 
                                line_width=2.0)
                                
        add_attribute(footroll_ctrl.ctrl, 'footroll_angle', dv=30.0, min=0.0)
        cmds.connectAttr('{}.rz'.format(footroll_ctrl.ctrl), '{}.footroll'.format(footroll.foot.top))
        cmds.connectAttr('{}.footroll_angle'.format(footroll_ctrl.ctrl), '{}.footroll_angle'.format(footroll.foot.top))

        # Foot bk control
        foot_bk_ctrl = Control(self.name, 
                               ball_mtx,
                               parent=footroll.ball.bottom,
                               add_to_tags=['bk1'],
                               syntax_list=syntax_list,
                               lock_r='xy',
                               lock_t='xyz',
                               lock_s='xyz',
                               shape_type='cube',
                               shape_up='+x', 
                               shape_aim='+z',
                               rgb_color=ctrl_color,
                               size=6.0, 
                               line_width=2.0)
        
        
        # Heel Control
        heel_ctrl = Control('heel_{}'.format(self.side), 
                             math.get_matrix(footroll.heel.top),
                            parent=footroll.foot.top,
                            lock_r='xy',
                            lock_t='xyz',
                            lock_s='xyz',
                            shape_type='joint',
                            shape_up='+x', 
                            shape_aim='+z', 
                            size=3.0,
                            line_width=1.0,
                            pivot_ctrl=True)
        
        # connecting heel pivot control to footroll ofs pivot 
        cmds.connectAttr('{}.translate'.format(heel_ctrl.pvt), '{}.rotatePivot'.format(footroll.heel.ofs))
        cmds.connectAttr('{}.translate'.format(heel_ctrl.pvt), '{}.scalePivot'.format(footroll.heel.ofs))
        
        # reparenting footroll heel zero under heel control
        cmds.parent(footroll.heel.top, heel_ctrl.bottom, a=True)
        
        # Tip Control
        tip_ctrl = Control('tip_{}'.format(self.side), 
                            math.get_matrix(footroll.tip.top),
                            parent=footroll.heel.bottom,
                            lock_r='xy',
                            lock_t='xyz',
                            lock_s='xyz',
                            shape_type='joint',
                            size=3.0, 
                            line_width=1.0,
                            pivot_ctrl=True)
        
        # reparenting footroll tip zero under tip control
        cmds.parent(footroll.tip.top, tip_ctrl.bottom, a=True)
        
        # connecting tip pivot control to footroll ofs pivot 
        cmds.connectAttr('{}.translate'.format(tip_ctrl.pvt), '{}.rotatePivot'.format(footroll.tip.ofs))
        cmds.connectAttr('{}.translate'.format(tip_ctrl.pvt), '{}.scalePivot'.format(footroll.tip.ofs))
        
        # IK ball control
        ball_ik_ctrl = Control('ball_{}'.format(self.side), 
                               ball_ik_mtx,
                               parent=footroll.tip.bottom,
                               add_to_tags=['ik'],
                               lock_r='yz',
                               lock_t='xyz',
                               lock_s='xyz',
                               size=6.0, 
                               line_width=3.0)
        
        # reparenting footroll ankle zero under ball bk1 control
        cmds.parent(footroll.ankle.top, foot_bk_ctrl.bottom, r=True)
        
        self.module_ctrls.extend([foot_ik_ctrl.ctrl, 
                                  ball_ik_ctrl.ctrl, 
                                  footroll_ctrl.ctrl, 
                                  foot_bk_ctrl.ctrl, 
                                  heel_ctrl.ctrl, 
                                  tip_ctrl.ctrl])

        # Build IKFK setup
        foot_ikfk = IKFK(self.name,
                         [self.module_matrices['foot'],
                         ball_mtx],
                         attr_obj=self.ikfk.split('.')[0],
                         blend_attr=self.ikfk.split('.')[-1],
                         parent=self.hierarchy['ikfk'],
                         driverA_tags='fk_tmp',
                         driverB_tags='ik_tmp',
                         driven_tags='ikfk_tmp')


        matrix_constraint(footroll.ankle.bottom, foot_ikfk.driverB.top)
        matrix_constraint(ball_ik_ctrl.ctrl, foot_ikfk.driverB.bottom)

        matrix_constraint(foot_fk_ctrl.ctrl, foot_ikfk.driverA.top)
        matrix_constraint(ball_fk_ctrl.ctrl, foot_ikfk.driverA.bottom)

        self.output = foot_ikfk.driven.top
        
        
        