import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import ControlChain

from rigging.utils import math
from rigging.utils.connect import matrix_constraint



class BipedNeck(RigModule):
    def __init__(self, 
                 name='neck', 
                 inputs={'neck' : 'spine_03_ctrl'}, 
                 matrices={'neck_01' : om.MMatrix(),
                           'neck_02' : om.MMatrix()}, 
                 parent='rig_grp', 
                 shape_up='+y', 
                 shape_aim='+x', 
                 **kwargs):
        super(BipedNeck, self).__init__(name=name, 
                                        inputs=inputs, 
                                        matrices=matrices, 
                                        parent=parent,
                                        shape_up=shape_up, 
                                        shape_aim=shape_aim,  
                                        **kwargs)
    
    def build(self):
        # Building controls
        neck_ctrls = ControlChain(self.name,
                                  [self.module_matrices['neck_01'],
                                  self.module_matrices['neck_02']],
                                  parent=self.hierarchy['fk'],
                                  lock_s='xyz',
                                  shape_aim=self.shape_aim,
                                  shape_up=self.shape_up,
                                  line_width=3.0,
                                  size=10.0
                                  )
        
        matrix_constraint(self.inputs['neck'], neck_ctrls.top, store=True)
        
        self.module_ctrls.extend(neck_ctrls.ctrls)