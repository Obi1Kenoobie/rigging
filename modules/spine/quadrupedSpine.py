import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.modules.module import RigModule

from rigging.parts.control import Control
from rigging.parts.base import Base
from rigging.parts.spline import SplineSampler

from rigging.utils.connect import matrix_constraint
from rigging.utils.globals import AXIS_NORM
from rigging.utils.name import create_chain_names



class QuadrupedSpine(RigModule):
    def __init__(self, 
                 name='spine', 
                 inputs={'spine' : 'body_offset_ctrl'}, 
                 matrices={'pelvis' : om.MMatrix(),
                           'chest' : om.MMatrix(),
                           'spine_end' : om.MMatrix(),
                           'hip_l' : om.MMatrix(),
                           'hip_r' : om.MMatrix()},
                 parent='rig_grp',
                 shape_up='+y', 
                 shape_aim='+z',
                 bones_number=5,
                 **kwargs):
        
        self.body_ctrl = None
        self.pelvis_ctrl = None
        self.chest_ctrl = None
        self.spine_ctrl = None
        self.spine_end = None
        self.bones_samples = []
        self.bones_number = bones_number

        super(QuadrupedSpine, self).__init__(name=name, 
                                         inputs=inputs, 
                                         matrices=matrices, 
                                         parent=parent,
                                         shape_up=shape_up, 
                                         shape_aim=shape_aim,  
                                         **kwargs)
        

    def _drive_spine_ctrl(self):
            # build spline
            spine_spline = SplineSampler('spine',
                                         drivers=[self.pelvis_ctrl.ctrl, self.chest_ctrl.ctrl],
                                         driven = [None, self.spine_ctrl.top, None],
                                         attr_objs=[self.pelvis_ctrl.ctrl, self.chest_ctrl.ctrl],
                                         degree=2,
                                         bezier=False,
                                         use_tangents=True,
                                         aim_axis='+z',
                                         up_axis='+y',
                                         offset_matrix=False,
                                         twist=True,
                                         object_up=None,
                                         scale=True,
                                         periodic=False,
                                         add_to_tags=['driver'],
                                         suffix='crv',
                                         stretch=False,
                                         length_attr=False)
            
            cmds.setAttr(f'{spine_spline.curve}.v', False)
            cmds.parent(spine_spline.curve, self.hierarchy['ik'])
            
    
    def _create_bone_samples(self):
        base_names = create_chain_names(self.bones_number, name=self.name, add_to_tags=['bone', 'sample'])
        for name in base_names:
            sample_srt = Base(name,om.MMatrix(), parent=self.hierarchy['ikfk'], zero=False)
            self.bones_samples.append(sample_srt.obj)
        
        bones_spline = SplineSampler('spine',
                                     drivers=[self.pelvis_ctrl.ctrl, self.spine_ctrl.ctrl, self.chest_ctrl.ctrl, self.spine_end.obj],
                                     driven = self.bones_samples,
                                     attr_objs=[self.pelvis_ctrl.ctrl, self.spine_ctrl.ctrl, self.chest_ctrl.ctrl],
                                     degree=3,
                                     bezier=False,
                                     use_tangents=False,
                                     aim_axis='+z',
                                     up_axis='+y',
                                     offset_matrix=True,
                                     twist=True,
                                     object_up=None,
                                     scale=True,
                                     periodic=False,
                                     add_to_tags=['bones'],
                                     suffix='crv',
                                     stretch=True,
                                     length_attr=True)

        cmds.setAttr(f'{bones_spline.curve}.v', False)
        cmds.parent(bones_spline.curve, self.hierarchy['ik'])
    
    def build(self):
        # Building controls

        self.body_ctrl = Control('body',
                                 self.module_matrices['pelvis'],
                                 lock_s='xyz',
                                 shape_type='cube',
                                 parent=self.hierarchy['fk'],
                                 shape_aim=self.shape_aim,
                                 shape_up=self.shape_up,
                                 size=6,
                                 line_width=4.0)
        
        # constraining body control to body offset control
        matrix_constraint(self.inputs['spine'], self.body_ctrl.zero, store=True)
        
        
        
        # Spine Controls
        hip_l_ctrl = Control('hip_l',
                             self.module_matrices['hip_l'],
                             lock_s='xyz',
                             lock_t='xyz',
                             shape_type='fourBentArrows',
                             parent=self.body_ctrl.ctrl,
                             shape_aim=self.shape_aim,
                             shape_up=self.shape_up,
                             size=1,
                             line_width=3.0)
        
        hip_r_ctrl = Control('hip_r',
                             self.module_matrices['hip_r'],
                             lock_s='xyz',
                             lock_t='xyz',
                             shape_type='fourBentArrows',
                             parent=hip_l_ctrl.ctrl,
                             shape_aim=self.shape_aim,
                             shape_up=self.shape_up,
                             size=1,
                             line_width=3.0)
        
        self.pelvis_ctrl = Control('pelvis',
                                   self.module_matrices['pelvis'],
                                   lock_s='xyz',
                                   shape_type='cube',
                                   parent=hip_r_ctrl.ctrl,
                                   rgb_color=[0.6, 0.4, 0.0],
                                   shape_aim=self.shape_aim,
                                   shape_up=self.shape_up,
                                   size=5,
                                   line_width=3.0)
                              
        self.chest_ctrl = Control('chest',
                                   self.module_matrices['chest'],
                                   lock_s='xyz',
                                   shape_type='cube',
                                   parent=self.body_ctrl.ctrl,
                                   rgb_color=[0.8, 0.2, 0.0],
                                   shape_aim=self.shape_aim,
                                   shape_up=self.shape_up,
                                   size=4,
                                   line_width=3.0)
        
        self.spine_ctrl = Control('spine',
                                   om.MMatrix(),
                                   lock_s='xyz',
                                   shape_type='square',
                                   parent=self.hierarchy['ik'],
                                   rgb_color=[0.7, 0.3, 0.0],
                                   shape_aim=AXIS_NORM[self.shape_aim],
                                   shape_up=AXIS_NORM[self.shape_up],
                                   size=3,
                                   line_width=3.0)
 
        self.spine_end = Base('spineEnd', self.module_matrices['spine_end'], parent=self.chest_ctrl.ctrl, last=False)
        
        # drive spine ctrl
        self._drive_spine_ctrl()
        
        # drive bone samples
        self._create_bone_samples()
        
        self.module_ctrls.extend([self.body_ctrl.ctrl, 
                                  self.pelvis_ctrl.ctrl, 
                                  self.chest_ctrl.ctrl, 
                                  self.spine_ctrl.ctrl,
                                  hip_l_ctrl.ctrl,
                                  hip_r_ctrl.ctrl])