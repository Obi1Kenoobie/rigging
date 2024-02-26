import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control

from rigging.utils import math
from rigging.utils.connect import matrix_constraint



class BipedSpine(RigModule):
    def __init__(self, 
                 name='spine', 
                 inputs={'spine' : 'body_offset_ctrl'}, 
                 matrices={'pelvis' : om.MMatrix(),
                           'spine_01' : om.MMatrix(),
                           'spine_02' : om.MMatrix(),
                           'spine_03' : om.MMatrix()}, 
                 parent='rig_grp',
                 shape_up='+y', 
                 shape_aim='+x', 
                 **kwargs):
        super(BipedSpine, self).__init__(name=name, 
                                         inputs=inputs, 
                                         matrices=matrices, 
                                         parent=parent,
                                         shape_up=shape_up, 
                                         shape_aim=shape_aim,  
                                         **kwargs)
    
    def build(self):
        # Building controls
        
        # calculating body matrix
        body_ctrl_mtx = math.lerp_matrices(self.module_matrices['pelvis'],
                                           self.module_matrices['spine_01'], num=3)[1]

        body_ctrl = Control('body',
                            body_ctrl_mtx,
                            lock_s='xyz',
                            shape_type='octagon',
                            parent=self.hierarchy['fk'],
                            rgb_color=[0.9, 0.1, 0.0],
                            shape_aim=self.shape_aim,
                            shape_up=self.shape_up,
                            size=25,
                            line_width=4.0)
        
        # constraining body control to body offset control
        matrix_constraint(self.inputs['spine'], body_ctrl.zero, store=True)
        
        pelvis_ctrl = Control('pelvis',
                              self.module_matrices['pelvis'],
                              lock_s='xyz',
                              shape_type='circle',
                              parent=body_ctrl.ctrl,
                              rgb_color=[0.6, 0.4, 0.0],
                              shape_aim=self.shape_aim,
                              shape_up=self.shape_up,
                              size=20,
                              line_width=3.0)
                              
        spine01_ctrl = Control('spine_01',
                               self.module_matrices['spine_01'],
                               lock_s='xyz',
                               shape_type='square',
                               parent=body_ctrl.ctrl,
                               rgb_color=[0.8, 0.2, 0.0],
                               shape_aim=self.shape_aim,
                               shape_up=self.shape_up,
                               size=30,
                               line_width=3.0)
        
        spine02_ctrl = Control('spine_02',
                               self.module_matrices['spine_02'],
                               lock_s='xyz',
                               shape_type='square',
                               parent=spine01_ctrl.ctrl,
                               rgb_color=[0.7, 0.3, 0.0],
                               shape_aim=self.shape_aim,
                               shape_up=self.shape_up,
                               size=30,
                               line_width=3.0)
 
        spine03_ctrl = Control('spine_03',
                               self.module_matrices['spine_03'],
                               lock_s='xyz',
                               shape_type='square',
                               parent=spine02_ctrl.ctrl,
                               rgb_color=[0.5, 0.5, 0.0],
                               shape_aim=self.shape_aim,
                               shape_up=self.shape_up,
                               size=30,
                               line_width=3.0)                              
        
        self.module_ctrls.extend([body_ctrl.ctrl, 
                                  pelvis_ctrl.ctrl, 
                                  spine01_ctrl.ctrl, 
                                  spine02_ctrl.ctrl, 
                                  spine03_ctrl.ctrl])