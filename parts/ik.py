import maya.cmds as cmds

from rigging.utils.solver import ik
from rigging.parts.base import BaseChain


class IK(BaseChain):
    def __init__(self,
                 name,
                 matrices,
                 add_to_suffix=None,
                 add_to_tags=None,
                 parent=None,
                 handle_parent=None,
                 pole_vector=None,
                 solver='ikRPsolver',
                 joint_display='bone',
                 zero=False,
                 ofs=False,
                 obj=True,
                 mtx=False,
                 suffix='jnt',
                 syntax_list=None,
                 last=False,
                 keep_rotation=False,
                 **kwargs):
        super(IK, self).__init__(name,
                                 matrices,
                                 parent=parent,
                                 zero=zero,
                                 spc=False,
                                 ofs=ofs,
                                 obj=obj,
                                 mtx=mtx,
                                 suffix=suffix,
                                 syntax_list=syntax_list,
                                 add_to_tags=add_to_tags,
                                 obj_type='joint',
                                 joint_display=joint_display,
                                 freeze_joint=True,
                                 last=last,
                                 keep_rotation=keep_rotation)

        # joint names
        self.jnts = self.objs

        # joint base objects
        self.joints = self.bases

        ik_list = ik(name,
                     self.objs[0],
                     self.objs[-1],
                     parent=handle_parent,
                     add_to_suffix=add_to_suffix,
                     add_to_tags=add_to_tags,
                     suffix=None,
                     solver=solver,
                     pole_vector=pole_vector, 
                     **kwargs)

        self.ik_handle = ik_list[0]
        self.ik_effector = ik_list[1]


