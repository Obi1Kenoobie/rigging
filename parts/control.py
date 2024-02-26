import maya.cmds as cmds

from rigging.parts.base import Base, BaseChain
from rigging.utils.shape import create
from rigging.utils import attribute
from rigging.utils.space import add_space


class Control(Base):
    def __init__(self, 
                 name, 
                 matrix,
                 parent=None, 
                 zero=True,
                 spc=False, 
                 ofs=False, 
                 obj=True, 
                 mtx=False,
                 mtx_type='transform',
                 syntax_list=None,
                 add_to_tags=None,
                 suffix='ctrl', 
                 obj_type='transform', 
                 offset_matrix=False,
                 last=False,
                 keep_rotation=False,
                 shape_type='circle',
                 lock_t='',
                 lock_r='',
                 lock_s='',
                 size=1.0,
                 shape_up='+y', 
                 shape_aim='+x', 
                 shape_offset=[0.0, 0.0, 0.0],
                 line_width=1.0,
                 color=None,
                 rgb_color=None,
                 space_names=None,
                 space_drivers=None,
                 split_channels=False,
                 pivot_ctrl=False):

        super(Control, self).__init__(name, 
                                      matrix,
                                      parent=parent, 
                                      zero=zero,
                                      spc=spc, 
                                      ofs=ofs, 
                                      obj=obj, 
                                      mtx=mtx,
                                      mtx_type=mtx_type,
                                      pvt=pivot_ctrl,
                                      syntax_list=syntax_list,
                                      add_to_tags=add_to_tags,
                                      suffix=suffix, 
                                      obj_type=obj_type, 
                                      offset_matrix=offset_matrix,
                                      last=last,
                                      keep_rotation=keep_rotation,
                                      space_names=space_names,
                                      space_drivers=space_drivers,
                                      split_channels=split_channels)
        
        self.ctrl = self.obj
        self.control = self.base
        attribute.lock_srt(self.ctrl, translate=lock_t, rotate=lock_r, scale=lock_s, visibility=True)
        if not lock_r == 'xyz':
            attribute.display_rotate_order(self.ctrl)

        self.shape = create(self.ctrl, 
                            shape_type=shape_type, 
                            shape_aim=shape_aim, 
                            shape_up=shape_up, 
                            offset=shape_offset, 
                            color=color, 
                            rgb_color=rgb_color, 
                            line_width=line_width, 
                            size=size, 
                            parent=self.ctrl)
        
        if pivot_ctrl:
            attribute.add_switch(self.ctrl, 'pivotCtrl', default=False)
            cmds.connectAttr('{}.pivotCtrl'.format(self.ctrl), '{}.v'.format(self.pvt))
            attribute.lock_srt(self.pvt, translate='')
            attribute.lock_hide_visibility(self.pvt)
            self.pivot_shape = create(self.pvt, 
                                      shape_type='joint',
                                      offset=shape_offset, 
                                      color='magenta', 
                                      line_width=line_width, 
                                      size=size * 0.25, 
                                      parent=self.pvt)
            

class ControlChain(BaseChain):
    def __init__(self,
                 name,
                 matrices,
                 parent=None,
                 zero=True,
                 spc=False,
                 ofs=False,
                 obj=True,
                 mtx=False,
                 mtx_type='transform',
                 syntax_list=None,
                 add_to_tags=None,
                 suffix='ctrl',
                 obj_type='transform',
                 offset_matrix=False,
                 last=False,
                 keep_rotation=False,
                 shape_type='circle',
                 lock_t='',
                 lock_r='',
                 lock_s='',
                 size=1.0,
                 shape_up='+y', 
                 shape_aim='+x', 
                 shape_offset=[0.0, 0.0, 0.0],
                 line_width=1.0,
                 color=None,
                 rgb_color=None, 
                 space_names=None,
                 space_drivers=None,
                 split_channels=False,
                 pivot_ctrl=False):
        super(ControlChain, self).__init__(name,
                                           matrices,
                                           parent=parent,
                                           zero=zero,
                                           spc=spc,
                                           ofs=ofs,
                                           obj=obj,
                                           mtx=mtx,
                                           mtx_type=mtx_type,
                                           pvt=pivot_ctrl,
                                           syntax_list=syntax_list,
                                           add_to_tags=add_to_tags,
                                           suffix=suffix,
                                           obj_type=obj_type,
                                           offset_matrix=offset_matrix,
                                           last=last,
                                           keep_rotation=keep_rotation,
                                           space_drivers=space_drivers,
                                           space_names=space_names,
                                           split_channels=split_channels)

        self.ctrls = self.objs
        self.controls = self.bases

        self.shapes = []
        for ctrl in self.ctrls:
            attribute.lock_srt(ctrl, translate=lock_t, rotate=lock_r, scale=lock_s, visibility=True)
            if not lock_r == 'xyz':
                attribute.display_rotate_order(ctrl)

            self.shapes.append(create(ctrl,
                                      shape_type=shape_type, 
                                      shape_aim=shape_aim, 
                                      shape_up=shape_up, 
                                      offset=shape_offset, 
                                      color=color, 
                                      rgb_color=rgb_color, 
                                      line_width=line_width, 
                                      size=size,
                                      parent=ctrl))