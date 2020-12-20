import maya.cmds as cmds

from rigging.utils import math, common
from rigging.utils.space import add_space
from rigging.utils.name import Name, generate_name_list


class Base(object):
    def __init__(self, 
                 name, 
                 matrix,
                 parent=None, 
                 zero=True,
                 spc=False, 
                 ofs=False, 
                 obj=True, 
                 mtx=False,
                 suffix='SRT', 
                 obj_type='transform', 
                 offset_matrix=False,
                 last=False,
                 keep_rotation=False,
                 space_drivers=None,
                 space_names=None,
                 split_channels=False):

        self.suffix = suffix
        if last:
            self.suffix = 'END'

        self.namer = Name(name, suffix=self.suffix)
        self.name = self.namer.create()
        self.side = self.namer.side
        self.matrix = matrix
        self.zero = None
        self.spc = None
        self.ofs = None
        self.obj = None
        self.mtx = None
        self.top = None
        self.bottom = None
        self.base = self
        hierarchy_list = []

        if not spc and space_drivers:
            spc = True

        if zero:
            self.zero = self.create_zero()
            hierarchy_list.append(self.zero)
        if spc:
            self.spc = self.create_spc()
            hierarchy_list.append(self.spc)
        if ofs:
            self.ofs = self.create_ofs()
            hierarchy_list.append(self.ofs)
        if obj:
            self.obj = self.create_obj(obj_type)
            hierarchy_list.append(self.obj)
        if mtx:
            self.mtx = self.create_mtx()
            hierarchy_list.append(self.mtx)
        
        self.top = hierarchy_list[0]
        self.bottom = hierarchy_list[-1]
        
        # parenting stuff
        for i in range(1, len(hierarchy_list)):
            cmds.parent(hierarchy_list[i], hierarchy_list[i-1], absolute=True)
        
        if parent:
            if obj_type == 'joint':
                cmds.parent(self.top, parent, relative=True)
            else:
                cmds.parent(self.top, parent, absolute=True)

        if offset_matrix:
            if parent:
                parent_matrix = math.get_matrix(parent)
                self.matrix = math.offset_matrix(parent_matrix, self.matrix)
            math.set_offset_parent_matrix(self.top, self.matrix)
            common.zero(self.top)
        else:
            math.set_matrix(self.top, self.matrix)
        
        if keep_rotation:
            if offset_matrix:
                parent_offset_matrix = math.get_offset_parent_matrix(self.top)
                rotation = math.rotation_from_matrix(parent_offset_matrix)
                position_matrix = math.get_translation_matrix(math.translation_from_matrix(parent_offset_matrix))
                cmds.xform(self.obj, ro=rotation)    
                math.set_offset_parent_matrix(self.top, position_matrix)
            else:
                rotation = cmds.xform(self.top, q=True, ro=True)
                cmds.xform(self.obj, ro=rotation)
                common.zero(self.zero, translation=False)

        if space_drivers:
            if not space_names:
                space_names = space_drivers

            add_space(self.spc,
                      attr_obj=self.obj,
                      space_drivers=space_drivers,
                      space_names=space_names,
                      split_channels=split_channels)

    @staticmethod
    def _create_transform(obj_type, name):
        return common.create_node(obj_type, name, use_node_type=False)

    def create_zero(self):
        zero_name = self.namer.replace(add_to_suffix=['ZERO'])
        return self._create_transform('transform', zero_name)
    
    def create_spc(self):
        spc_name = self.namer.replace(add_to_suffix=['SPC'])
        return self._create_transform('transform', spc_name)

    def create_ofs(self):
        ofs_name = self.namer.replace(add_to_suffix=['OFS'])
        return self._create_transform('transform', ofs_name)

    def create_obj(self, obj_type):
        return self._create_transform(obj_type, self.name)
        
    def create_mtx(self):
        mtx_name = self.namer.replace(add_to_suffix=['MTX'])
        return self._create_transform('transform', mtx_name)


class BaseChain(object):
    def __init__(self,
                 name,
                 matrices,
                 parent=None,
                 zero=True,
                 spc=False,
                 ofs=False,
                 obj=True,
                 mtx=False,
                 suffix='SRT',
                 obj_type='transform',
                 offset_matrix=False,
                 last=False,
                 keep_rotation=False,
                 space_drivers=None,
                 space_names=None,
                 split_channels=False):

        self.namer = Name(name, suffix=suffix)
        self.name = self.namer.create()
        self.side = self.namer.side
        self.matrices = matrices
        self.parent = parent
        self.zeros = []
        self.spcs = []
        self.ofsts = []
        self.objs = []
        self.mtxs = []
        self.top = None
        self.bottom = None
        self.tops = []
        self.bottoms = []
        self.bases = []
        self.base_cain = self

        name_list = generate_name_list(self.namer, len(self.matrices), last=last)
        obj_parent = self.parent
        is_last = False
        for i in range(len(self.matrices)):
            if i != 0:
                space_names = None
                space_drivers = None
            if last and i == len(self.matrices)-1:
                is_last = True
            obj_name = name_list[i]
            matrix = matrices[i]
            base_obj = Base(obj_name, 
                            matrix, 
                            parent=obj_parent,
                            zero=zero,
                            spc=spc,
                            ofs=ofs,
                            obj=obj,
                            mtx=mtx,
                            suffix=suffix,
                            obj_type=obj_type,
                            offset_matrix=offset_matrix,
                            last=is_last,
                            keep_rotation=keep_rotation,
                            space_drivers=space_drivers,
                            space_names=space_names,
                            split_channels=split_channels)

            self.zeros.append(base_obj.zero)
            self.spcs.append(base_obj.spc)
            self.ofsts.append(base_obj.ofs)
            self.objs.append(base_obj.obj)
            self.mtxs.append(base_obj.mtx)
            self.bases.append(base_obj.base)
            self.tops.append(base_obj.top)
            self.bottoms.append(base_obj.bottom)

            obj_parent = base_obj.bottom

        self.top = self.tops[0]
        self.bottom = self.bottoms[-1]
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            