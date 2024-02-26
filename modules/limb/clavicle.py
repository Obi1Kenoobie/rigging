import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control

from rigging.utils import math
from rigging.utils.connect import matrix_constraint



class Clavicle(RigModule):
    def __init__(self, 
                 name='clavicle_l', 
                 inputs={'clavicle' : 'spine_03_ctrl'}, 
                 matrices={'clavicle' : om.MMatrix()}, 
                 parent='rig_grp', 
                 **kwargs):
        super(Clavicle, self).__init__(name=name, 
                                       inputs=inputs, 
                                       matrices=matrices, 
                                       parent=parent, 
                                       **kwargs)
    
    def build(self):
        # Building controls
        clavicle_ctrl = Control(self.name, 
                                self.module_matrices['clavicle'],
                                parent=self.hierarchy['fk'], 
                                shape_type='arrow',
                                lock_s='xyz',
                                size=5.0,
                                shape_up='+z', 
                                shape_aim='+x', 
                                shape_offset=[8.0, 0.0, 10.0],
                                line_width=4.0)


        matrix_constraint(self.inputs['clavicle'], clavicle_ctrl.top, store=True)
        
        self.module_ctrls.append(clavicle_ctrl.ctrl)