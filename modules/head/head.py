import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control

from rigging.utils import math
from rigging.utils.connect import matrix_constraint



class Head(RigModule):
    def __init__(self, 
                 name='head', 
                 inputs={'head' : 'neck_02_ctrl'},
                 spaces = {'body' : 'body_ctrl'}, 
                 matrices={'head' : om.MMatrix()}, 
                 parent='rig_grp',
                 shape_up='+y', 
                 shape_aim='+x',  
                 **kwargs):
        
        super(Head, self).__init__(name=name, 
                                   inputs=inputs,
                                   spaces=spaces, 
                                   matrices=matrices, 
                                   parent=parent, 
                                   shape_up=shape_up, 
                                   shape_aim=shape_aim, 
                                   **kwargs)
    
    def build(self, **kwargs):
        # Building controls
        head_ctrl = Control(self.name,
                            self.module_matrices['head'],
                            parent=self.hierarchy['fk'],
                            lock_s='xyz',
                            shape_type='fourArrows',
                            line_width=3.0,
                            size=7.0,
                            shape_offset=kwargs['shape_offset'],
                            shape_aim=self.shape_aim,
                            shape_up=self.shape_up,
                            space_names=self.spaces.keys(),
                            space_drivers=self.spaces.values(),
                            split_channels=True
                            )

        matrix_constraint(self.inputs['head'], head_ctrl.top, store=True)
        
        self.module_ctrls.append(head_ctrl.ctrl)