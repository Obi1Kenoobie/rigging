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
                 suffix='CTRL', 
                 obj_type='transform', 
                 offset_matrix=False,
                 last=False,
                 keep_rotation=False,
                 shape_type='circle',
                 lock_t='',
                 lock_r='',
                 lock_s='',
                 size=1.0,
                 color=None,
                 space_names=None,
                 space_drivers=None,
                 split_channels=False):

        super(Control, self).__init__(name, 
                                      matrix,
                                      parent=parent, 
                                      zero=zero,
                                      spc=spc, 
                                      ofs=ofs, 
                                      obj=obj, 
                                      mtx=mtx,
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
        
        attribute.lock_srt(self.ctrl, translate=lock_t, rotate=lock_r, scale=lock_s)
        if not lock_r == 'xyz':
            attribute.display_rotate_order(self.ctrl)

        self.shape = create(name, shape_type=shape_type, color=color, size=size, parent=self.ctrl)


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
                 suffix='CTRL',
                 obj_type='transform',
                 offset_matrix=False,
                 last=False,
                 keep_rotation=False,
                 shape_type='circle',
                 lock_t='',
                 lock_r='',
                 lock_s='',
                 size=1.0,
                 color=None,
                 space_names=None,
                 space_drivers=None,
                 split_channels=False):
        super(ControlChain, self).__init__(name,
                                           matrices,
                                           parent=parent,
                                           zero=zero,
                                           spc=spc,
                                           ofs=ofs,
                                           obj=obj,
                                           mtx=mtx,
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
            attribute.lock_srt(ctrl, translate=lock_t, rotate=lock_r, scale=lock_s)
            if not lock_r == 'xyz':
                attribute.display_rotate_order(ctrl)

            self.shapes.append(create(ctrl, shape_type=shape_type, color=color, size=size, parent=ctrl))