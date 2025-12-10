import maya.cmds as cmds

from rigging.utils import math, common
from rigging.utils.space import add_space
from rigging.utils.name import Name, create_chain_names


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
                 mtx_type='transform',
                 pvt=False,
                 syntax_list=None,
                 add_to_tags=None,
                 suffix='srt', 
                 obj_type='transform',
                 joint_display='bone',
                 offset_matrix=False,
                 last=False,
                 keep_rotation=False,
                 space_drivers=None,
                 space_names=None,
                 split_channels=False):
        self.syntax_list = syntax_list
        self.add_to_tags = add_to_tags
        self.suffix = suffix
        if last:
            self.suffix = 'end'

        self.namer = Name(name, suffix=self.suffix)
        self.name = self.namer.create_name(syntax_list=self.syntax_list)
        self.side = self.namer.side
        self.matrix = matrix
        self.zero = None
        self.spc = None
        self.ofs = None
        self.obj = None
        self.mtx = None
        self.mtx_type = mtx_type
        self.mtx_shape = None
        self.pvt=None
        self.top = None
        self.bottom = None
        self.base = self
        hierarchy_list = []
        joint_display_dict = {'bone' : 0,
                              'multi' : 1,
                              'none' : 2}
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
            if obj_type == 'joint':
                cmds.setAttr('{}.drawStyle'.format(self.obj), joint_display_dict[joint_display])
        if mtx:
            self.mtx = self.create_mtx()
            if self.mtx_type == 'locator':
                self.mtx_shape = common.get_shape(self.mtx)
                cmds.setAttr(self.mtx_shape + '.visibility', False)
        if pvt:
            self.pvt = self.create_pvt()

        self.top = hierarchy_list[0]
        self.bottom = hierarchy_list[-1]
        
        # parenting stuff
        for i in range(1, len(hierarchy_list)):
            cmds.parent(hierarchy_list[i], hierarchy_list[i-1], absolute=True)

        if mtx:
            cmds.parent(self.mtx, self.bottom, absolute=True)
        
        if pvt and obj:
            obj_parent = common.get_parent(self.obj)
            cmds.parent(self.pvt, obj_parent, relative=True)
            # connecting pvt transform to rotate and scale pivot of main object transform
            cmds.connectAttr('{}.translate'.format(self.pvt), '{}.rotatePivot'.format(self.obj))
            cmds.connectAttr('{}.translate'.format(self.pvt), '{}.scalePivot'.format(self.obj))
            
            
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
                      split_channels=split_channels,
                      store=True)

    @staticmethod
    def _create_transform(obj_type, name):
        return common.create_node(obj_type, name, syntax_list)

    def create_zero(self):
        return common.create_node('transform', self.name, syntax_list=self.syntax_list, suffix=self.suffix, add_to_tags=self.add_to_tags, add_to_suffix='zero')
    
    def create_spc(self):
        return common.create_node('transform', self.name, syntax_list=self.syntax_list, suffix=self.suffix, add_to_tags=self.add_to_tags, add_to_suffix='spc')

    def create_ofs(self):
        return common.create_node('transform', self.name, syntax_list=self.syntax_list, suffix=self.suffix, add_to_tags=self.add_to_tags, add_to_suffix='ofs')

    def create_obj(self, obj_type):
        return common.create_node(obj_type, self.name, syntax_list=self.syntax_list,  add_to_tags=self.add_to_tags, suffix=self.suffix)
        
    def create_mtx(self):
        return common.create_node(self.mtx_type, self.name, syntax_list=self.syntax_list, suffix=self.suffix, add_to_tags=self.add_to_tags, add_to_suffix='mtx')
    
    def create_pvt(self):
        return common.create_node('transform', self.name, syntax_list=self.syntax_list, suffix='pvt_' + self.suffix, add_to_tags=self.add_to_tags)


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
                 mtx_type='transform',
                 pvt=False,
                 syntax_list=None,
                 add_to_tags=None,
                 suffix='srt',
                 obj_type='transform',
                 freeze_joint=False,
                 joint_display='bone',
                 offset_matrix=False,
                 last=False,
                 keep_rotation=False,
                 space_drivers=None,
                 space_names=None,
                 split_channels=False):
        self.syntax_list = syntax_list
        self.suffix = suffix
        self.namer = Name(name, suffix=self.suffix)
        self.name = self.namer.create_name()
        self.side = self.namer.side
        self.matrices = matrices
        self.parent = parent
        self.zeros = []
        self.spcs = []
        self.ofsts = []
        self.objs = []
        self.mtxs = []
        self.mtx_shapes = []
        self.pvts = []
        self.top = None
        self.bottom = None
        self.tops = []
        self.bottoms = []
        self.bases = []
        self.base_cain = self

        name_list = create_chain_names(len(self.matrices), last_is_end=last, name=self.name)
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
                            mtx_type=mtx_type,
                            pvt=pvt,
                            add_to_tags=add_to_tags,
                            syntax_list=syntax_list,
                            suffix=suffix,
                            obj_type=obj_type,
                            joint_display=joint_display,
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
            if mtx_type == 'locator':
                self.mtx_shapes.append(base_obj.mtx_shape)
            self.pvts.append(base_obj.pvt)
            self.bases.append(base_obj.base)
            self.tops.append(base_obj.top)
            self.bottoms.append(base_obj.bottom)

            if obj_type == 'joint' and freeze_joint:
                cmds.makeIdentity(base_obj.obj, apply=True, rotate=True)
            obj_parent = base_obj.bottom

        self.top = self.tops[0]
        self.bottom = self.bottoms[-1]