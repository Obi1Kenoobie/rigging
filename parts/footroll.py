import maya.cmds as cmds

from rigging.parts.base import Base
from rigging.utils import math, attribute, connect, globals, common



class FootRoll(object):
    def __init__(self, name, ankle_matrix, ball_matrix, parent=None, heel_offset=-6.0, tip_offset=6.0, aim_axis='-y', up_axis='+z'):
        self.parent = parent
        self.name = name
        self.foot = None
        self.heel = None
        self.tip = None
        self.ball = None
        self.ankle = None
        self.footroll = None

        # Getting all necessary matrices to build foot-roll
        self.ankle_mtx = ankle_matrix
        self.ball_mtx = math.get_align_matrix(self.ankle_mtx, ball_matrix)
        self.aim_axis = aim_axis
        self.up_axis = up_axis

        # calculating tip and heel matrices using some vector and matrix math
        ball_position_vec = math.translation_from_matrix(self.ball_mtx)
        ankle_position_vec = math.translation_from_matrix(self.ankle_mtx)
        foot_aim = ball_position_vec - ankle_position_vec
        foot_aim.normalize()
        tip_position_vec = ball_position_vec + foot_aim * tip_offset
        heel_position_vec =  ankle_position_vec + foot_aim * heel_offset

        self.tip_mtx = math.vectors_to_matrix(row1=(self.ankle_mtx[0], self.ankle_mtx[1], self.ankle_mtx[2]), 
                                              row2=(self.ankle_mtx[4], self.ankle_mtx[5], self.ankle_mtx[6]), 
                                              row3=(self.ankle_mtx[8], self.ankle_mtx[9], self.ankle_mtx[10]),
                                              row4=(tip_position_vec.x, 0, tip_position_vec.z))

        self.heel_mtx = math.vectors_to_matrix(row1=(self.ankle_mtx[0], self.ankle_mtx[1], self.ankle_mtx[2]), 
                                               row2=(self.ankle_mtx[4], self.ankle_mtx[5], self.ankle_mtx[6]), 
                                               row3=(self.ankle_mtx[8], self.ankle_mtx[9], self.ankle_mtx[10]),
                                               row4=(heel_position_vec.x, 0, heel_position_vec.z))

        # calculating ankle up matrix
        ankle_up_position_vec = ball_position_vec + math.get_axis_vector(self.ankle_mtx, self.up_axis)
        self.ankle_up_mtx = math.vectors_to_matrix(row1=(self.ankle_mtx[0], self.ankle_mtx[1], self.ankle_mtx[2]), 
                                                   row2=(self.ankle_mtx[4], self.ankle_mtx[5], self.ankle_mtx[6]), 
                                                   row3=(self.ankle_mtx[8], self.ankle_mtx[9], self.ankle_mtx[10]),
                                                   row4=(ankle_up_position_vec.x, ankle_up_position_vec.y, ankle_up_position_vec.z))
            
        self._build_structure()
        self._build_setup()

    def _build_structure(self):
        self.foot = Base(self.name, self.ankle_mtx, parent=self.parent, obj=False, add_to_tags='foot')
        self.heel = Base(self.name, self.heel_mtx, parent=self.foot.bottom, obj=False, ofs=True, add_to_tags='heel')
        self.tip = Base(self.name, self.tip_mtx, parent=self.heel.bottom, obj=False, ofs=True, add_to_tags='tip')
        self.ball = Base(self.name, self.ball_mtx, parent=self.tip.bottom, obj=False, ofs=True, add_to_tags='ball')
        self.ankle = Base(self.name, self.ankle_mtx, parent=self.ball.bottom, add_to_tags='ankle')
        ankle_up = Base(self.name, self.ankle_up_mtx, parent=self.ball.bottom, obj=False, add_to_tags='ankle_up')
        connect.constraint(self.ball.bottom, 
                           self.ankle.obj, 
                           type='aimConstraint', 
                           aim_vector=globals.AXIS_STR_TO_VEC[self.aim_axis], 
                           up_vector=globals.AXIS_STR_TO_VEC[self.up_axis], 
                           world_up_object=ankle_up.top, 
                           world_up_type='object',
                           world_up_vector=globals.AXIS_STR_TO_VEC[self.up_axis],
                           snap=True)
    
    def _build_setup(self):
        # adding attributes to top group
        attribute.add_attribute(self.foot.top, 'footroll')
        attribute.add_attribute(self.foot.top, 'footroll_angle', min=0.0, dv=45.0)
        
        # creating all necessary nodes for the setup
        footroll_cond = common.create_node('condition', self.name, add_to_tags=['footroll'])
        heel_cond = common.create_node('condition', self.name, add_to_tags=['heel', 'footroll'])
        tip_cond = common.create_node('condition', self.name, add_to_tags=['tip', 'footroll'])
        ball_cond = common.create_node('condition', self.name, add_to_tags=['ball', 'footroll'])
        
        angle_mult = common.create_node('multDoubleLinear', self.name, add_to_tags=['angle', 'footroll'])
        
        angle_add = common.create_node('addDoubleLinear', self.name, add_to_tags=['angle', 'footroll'])

        # setting some values on nodes
        cmds.setAttr('{}.colorIfFalseR'.format(footroll_cond), 0.0)
        cmds.setAttr('{}.operation'.format(footroll_cond), 5)
        cmds.setAttr('{}.colorIfFalseR'.format(heel_cond), 0.0)
        cmds.setAttr('{}.operation'.format(heel_cond), 2)
        cmds.setAttr('{}.colorIfFalseR'.format(tip_cond), 0.0)
        cmds.setAttr('{}.operation'.format(tip_cond), 4)
        cmds.setAttr('{}.operation'.format(ball_cond), 3)
        
        cmds.setAttr('{}.input2'.format(angle_mult), -1.0)

        # connecting everything together
        cmds.connectAttr('{}.footroll'.format(self.foot.top),'{}.firstTerm'.format(heel_cond))
        cmds.connectAttr('{}.footroll'.format(self.foot.top),'{}.colorIfTrueR'.format(heel_cond))
        
        cmds.connectAttr('{}.outColorR'.format(heel_cond), '{}.rotateZ'.format(self.heel.ofs))
        
        cmds.connectAttr('{}.footroll'.format(self.foot.top),'{}.input2'.format(angle_add))
        
        cmds.connectAttr('{}.footroll'.format(self.foot.top),'{}.firstTerm'.format(footroll_cond))
        cmds.connectAttr('{}.footroll'.format(self.foot.top),'{}.colorIfTrueR'.format(footroll_cond))
        
        cmds.connectAttr('{}.footroll_angle'.format(self.foot.top),'{}.input1'.format(angle_add))
        cmds.connectAttr('{}.footroll_angle'.format(self.foot.top),'{}.input1'.format(angle_mult))

        cmds.connectAttr('{}.outColorR'.format(footroll_cond), '{}.firstTerm'.format(tip_cond))
        cmds.connectAttr('{}.outColorR'.format(footroll_cond), '{}.firstTerm'.format(ball_cond))
        cmds.connectAttr('{}.outColorR'.format(footroll_cond), '{}.colorIfTrueR'.format(ball_cond))
        
        cmds.connectAttr('{}.output'.format(angle_mult), '{}.secondTerm'.format(tip_cond))
        cmds.connectAttr('{}.output'.format(angle_mult), '{}.secondTerm'.format(ball_cond))
        cmds.connectAttr('{}.output'.format(angle_mult), '{}.colorIfFalseR'.format(ball_cond))
        
        cmds.connectAttr('{}.output'.format(angle_add), '{}.colorIfTrueR'.format(tip_cond))
        
        cmds.connectAttr('{}.outColorR'.format(tip_cond), '{}.rotateZ'.format(self.tip.ofs))
        
        cmds.connectAttr('{}.outColorR'.format(ball_cond), '{}.rotateZ'.format(self.ball.ofs))
        
