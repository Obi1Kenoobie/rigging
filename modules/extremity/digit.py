import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control, ControlChain

from rigging.utils import math, globals
from rigging.utils.connect import matrix_constraint



class Digit(RigModule):
    def __init__(self, 
                 name='index_l', 
                 inputs={'digit' : 'hand_01_l_ikfk_srt'}, 
                 matrices={'metacarpal' : om.MMatrix(),
                           'digit_01' : om.MMatrix(), 
                           'digit_02' : om.MMatrix(), 
                           'digit_03' : om.MMatrix()},  
                 parent='rig_grp',
                 is_thumb=False, 
                 **kwargs):
        
        self.is_thumb = is_thumb
        
        super(Digit, self).__init__(name=name, 
                                    inputs=inputs, 
                                    matrices=matrices, 
                                    parent=parent, 
                                    **kwargs)
    
    def build(self):
        parent = self.hierarchy['fk']
        
        # Building controls
        
        # Building metacarpal control and setting it as new parent for digit controls
        if not self.is_thumb:
            syntax_list = ['namespace', 'part', 'tags', 'partindex', 'index', 'side', 'suffix']
            metacarpal_ctrl = Control(self.name, 
                                      self.module_matrices['metacarpal'],
                                      parent=parent,
                                      syntax_list=syntax_list,
                                      add_to_tags='metacarpal',
                                      ofs=True, 
                                      shape_type='arrow',
                                      color=globals.COLOR_SIDE_TO_STR[self.side],
                                      lock_s='xyz',
                                      size=1.0,
                                      shape_up='+z', 
                                      shape_aim='-y', 
                                      shape_offset=[0.0, -1.0, 0.0],
                                      line_width=4.0)

            matrix_constraint(self.inputs['digit'], metacarpal_ctrl.top, store=True)
            
            self.module_ctrls.append(metacarpal_ctrl.ctrl)
            
            parent = metacarpal_ctrl.bottom

        # Building digit controls
        digit_ctrls = ControlChain(self.name,
                                  [self.module_matrices['digit_01'],
                                   self.module_matrices['digit_02'],
                                   self.module_matrices['digit_03']],
                                   parent=parent,
                                   ofs=True, 
                                   shape_type='arrow',
                                   lock_s='xyz',
                                   size=1.0,
                                   shape_up='+z', 
                                   shape_aim='-y', 
                                   shape_offset=[0.0, -1.0, 0.0],
                                   line_width=4.0)

        # Constraining top group of digit chain if digit is thumb
        if self.is_thumb:
            matrix_constraint(self.inputs['digit'], digit_ctrls.top, store=True)
            self.module_ctrls.extend(digit_ctrls.ctrls)
        else:
            # Creating specific set for digit controls
            digit_ctrls_set = cmds.sets(digit_ctrls.ctrls, name=self.namer.create_name(add_to_tags='digit',add_to_suffix='controls'))
            cmds.setAttr('{}.ihi'.format(digit_ctrls_set), True)
            self.module_ctrls.append(digit_ctrls_set)