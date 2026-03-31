import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control, ControlChain
from rigging.parts.spline import SplineSampler
from rigging.parts.base import Base

from rigging.utils import math
from rigging.utils.connect import matrix_constraint
from rigging.utils.name import create_chain_names



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
        
        self.ctrl = None
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
        self.ctrl = Control(
                        self.name,
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

        matrix_constraint(self.inputs['input'], self.ctrl.top, store=True)
        
        self.module_ctrls.append(self.ctrl.ctrl)


class GenericChain(RigModule):
    def __init__(
                self, 
                name='chain', 
                inputs={'input' : 'global_ctrl'},
                spaces = {}, 
                matrices=[], 
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
        
        self.ctrls = None
        super(GenericChain, self).__init__(
                                    name=name, 
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
                                    **kwargs
                                )
    
    def build(self, **kwargs):
        # Building controls at matrices
        self.ctrls = ControlChain(
                        self.name,
                        self.module_matrices,
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

        matrix_constraint(self.inputs['input'], self.ctrls.top, store=True)
        
        self.module_ctrls.extend(self.ctrls.ctrls)


class GenericSpline(GenericChain):
    def __init__(
                self, 
                name='chain', 
                inputs={'input' : 'global_ctrl'},
                spaces = {}, 
                matrices=[],
                samples=3,
                sample_params=None,
                bezier=False,
                use_tangents=False,
                aim_axis='+x',
                up_axis='+y',
                twist=True,
                scale=True,
                stretch=True,
                length_attr=False,
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
        
        self.bezier= bezier
        self.samples = samples
        self.sample_params = sample_params
        self.use_tangents = use_tangents
        self.aim_axis = aim_axis
        self.up_axis = up_axis
        self.twist = twist
        self.scale = scale
        self.stretch = stretch
        self.length_attr = length_attr
        self.spline = None
        self.matrices = matrices
        super(GenericSpline, self).__init__(
                                    name=name, 
                                    inputs=inputs,
                                    spaces = spaces, 
                                    matrices=matrices[:-1], 
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
                                    color=None,
                                    rgb_color=None,
                                    pivot_ctrl=False,
                                    **kwargs
                                )
        
        self.build_spline_sampler()
        
    def build_spline_sampler(self):
        end_driver = Base(
                    self.name,
                    self.matrices[-1],
                    zero=False,
                    parent=self.ctrls.bottom,
                    last=True)
        
        drivers = self.ctrls.ctrls
        drivers.append(end_driver.obj)
        degree = 3
        if len(drivers) <= 3:
            degree = len(drivers) - 1
        
        names = create_chain_names(self.samples, name=self.name, add_to_tags='sample')
        driven = [Base(name, om.MMatrix(), zero=False, parent=self.hierarchy['fk']).obj for name in names]
        sampler = SplineSampler(
                        self.name,
                        drivers=drivers,
                        driven=driven,
                        attr_objs=drivers,
                        sample_params=self.sample_params,
                        degree=degree,
                        bezier=self.bezier,
                        use_tangents=self.use_tangents,
                        aim_axis=self.aim_axis,
                        up_axis=self.up_axis,
                        offset_matrix=True,
                        twist=self.twist,
                        object_up=None,
                        scale=self.scale,
                        periodic=False,
                        add_to_tags='fk',
                        suffix='crv',
                        stretch=self.stretch,
                        length_attr=self.length_attr
        )
        
        cmds.setAttr(f'{sampler.curve}.v', False)
        cmds.parent(sampler.curve, self.hierarchy['fk'])