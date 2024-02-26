import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control

from rigging.utils import math
from rigging.utils.connect import matrix_constraint



class Generic(RigModule):
    def __init__(self, 
                 name='head', 
                 inputs={'input' : 'global_ctrl'},
                 spaces = {}, 
                 matrices={'matrix' : om.MMatrix()}, 
                 parent='rig_grp',
                 shape_up='+y', 
                 shape_aim='+x',
                 ofs=False, 
                mtx=False,
                syntax_list=None,
                add_to_tags=None,
                shape_type='circle',
                lock_t='',
                lock_r='',
                lock_s='xyz',
                size=1.0, 
                shape_offset=[0.0, 0.0, 0.0],
                line_width=1.0,
                color=None,
                rgb_color=None,
                pivot_ctrl=False,
                 **kwargs):
        

        super(Generic, self).__init__(name=name, 
                                    inputs=inputs,
                                    spaces=spaces, 
                                    matrices=matrices, 
                                    parent=parent, 
                                    shape_up=shape_up, 
                                    shape_aim=shape_aim,
                                    ofs=ofs, 
                                    mtx=mtx,
                                    syntax_list=syntax_list,
                                    add_to_tags=add_to_tags,
                                    shape_type=shape_type,
                                    lock_t=lock_t,
                                    lock_r=lock_r,
                                    lock_s=lock_s,
                                    size=size, 
                                    shape_offset=shape_offset,
                                    line_width=line_width,
                                    color=color,
                                    rgb_color=rgb_color,
                                    pivot_ctrl=pivot_ctrl,
                                    **kwargs)
    
    def build(self, **kwargs):
        # Building controls
        ctrl = Control(self.name,
                        self.module_matrices['matrix'],
                        parent=self.hierarchy['fk'],
                        lock_t=kwargs['lock_t'],
                        lock_r=kwargs['lock_r'],
                        lock_s=kwargs['lock_s'],
                        ofs=kwargs['ofs'], 
                        mtx=kwargs['mtx'],
                        mtx_type='transform',
                        syntax_list=kwargs['syntax_list'],
                        add_to_tags=self.add_to_tags,
                        shape_type=kwargs['shape_type'],
                        color=kwargs['color'],
                        rgb_color=kwargs['rgb_color'],
                        line_width=kwargs['line_width'],
                        size=kwargs['size'],
                        shape_offset=kwargs['shape_offset'],
                        shape_aim=self.shape_aim,
                        shape_up=self.shape_up,
                        space_names=self.spaces.keys(),
                        space_drivers=self.spaces.values(),
                        pivot_ctrl=kwargs['pivot_ctrl'],
                        )

        matrix_constraint(self.inputs['input'], ctrl.top, store=True)
        
        self.module_ctrls.append(ctrl.ctrl)