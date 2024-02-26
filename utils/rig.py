import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.parts.control import Control
from rigging.utils import common, math, attribute, connect, name, globals


class Rig(object):
    """ Asset Rig base class.
            Args:
            asset_name (str): asset name (eg. chHuman, vhCar, ppProp)
            rig_type (str): type of rig (eg. anim, cfx, muscle, skin)
            rig (bool): if True will create rig_GRP
            extras (bool): if Ture will create extras_GRP
            geo (bool): if True will create geo_GRP
            skeleton (bool): if True will create skeleton_GRP
            lods (list[str]): list of different level of detail groups (created only if geo is True)
            ikfk (list[str]): list of IKFK switch attributes to add to the global control
            global_ctrl (str): global control base name
            main_ctrl (str): main control base name
            root_ctrl (str): root control base name 
    """

    def __init__(self, asset_name, matrix=om.MMatrix(), shape_up='+y', shape_aim='+x', rig_type='anim', rig=True, extras=True, geo=True, skeleton=True, spaces=True,
                 lods=['proxy', 'anim', 'render'], ikfk=None, global_ctrl='global', main_ctrl='body_offset_tmp', 
                 root_ctrl='root'):
        # main rig object variables.
        self.asset_name = asset_name
        self.global_matrix = matrix
        self.shape_up = shape_up
        self.shape_aim = shape_aim
        self.rig_type = rig_type
        self.rig_hierarchy = {
            'rig' : rig,
            'skeleton' : skeleton,
            'geo' : geo,
            'spaces' : spaces,
            'extras' : extras
        }
        self.global_space = None
        self.main_space = None
        self.lods = lods
        
        self.top_group = None
        self.global_ctrl = global_ctrl
        self.main_ctrl = main_ctrl
        self.root_ctrl = root_ctrl
        self.controls_set = None

        self.rig_modules = []
        self.rig_controls = []
        self.rig_modules_ctrl_sets=[]
        self.ikfk = ikfk
        
        # creating rig structure.
        self._build_rig_structure()
        
        # rig modules get built here.
        print('\n --------BUILDING MODULES START------- \n')
        self.build()
        print('\n --------BUILDING MODULES END------- \n')

        # replacing temporary inputs with driver objects
        print('\n --------REPLACING TEMPORARY INPUTS------- \n')
        replace_temporary_inputs()
        
        # anything that needs to be done after building the rig goes here.
        print('\n --------POST BUILD START------- \n')
        self.post_build()
        print('\n --------POST BUILD START------- \n')

        # parenting modules control sets under main control set.
        for module in self.rig_modules:
            self.rig_controls.extend(module.module_ctrls)
            self.rig_modules_ctrl_sets.append(module.module_ctrls_set)
            cmds.sets(module.module_ctrls_set, add=self.controls_set)
        
        # cleaning up
        print('\n --------CLEAN UP START------- \n')
        self.clean_up()
        print('\n --------CLEAN UP END------- \n')

        
    def _build_rig_structure(self):
        """ Method used to create rig base hierarchy.
        """

        self.top_group = cmds.createNode('transform', name='{}{}Rig'.format(self.asset_name, self.rig_type.capitalize()))
        
        # Default rig controls.
        self.global_ctrl = Control(self.global_ctrl,
                                   self.global_matrix,
                                   shape_type='hexagon',
                                   parent=self.top_group,
                                   zero=True,
                                   color='yellow',
                                   shape_up=self.shape_up,
                                   shape_aim = self.shape_aim,
                                   size=40,
                                   line_width=4.0)

        self.main_ctrl = Control(self.main_ctrl,
                                 self.global_matrix,
                                 shape_type='square',
                                 parent=self.global_ctrl.obj,
                                 zero=False,
                                 lock_s='xyz',
                                 shape_up=self.shape_up,
                                 shape_aim = self.shape_aim,
                                 size=40,
                                 color='yellow',
                                 line_width=4.0)
        
        shp_ofs = math.to_mvector(globals.AXIS_STR_TO_VEC[self.shape_aim]) * -10
        self.root_ctrl = Control(self.root_ctrl,
                                 self.global_matrix,
                                 shape_type='arrow',
                                 parent=self.global_ctrl.obj,
                                 zero=False,
                                 lock_s='xyz',
                                 shape_up = self.shape_up,
                                 shape_aim=self.shape_aim,
                                 size=10,
                                 shape_offset=[shp_ofs.x, shp_ofs.y, shp_ofs.z],
                                 color='yellow',
                                 line_width=4.0)
        
        self.rig_controls.extend([self.global_ctrl.ctrl, self.main_ctrl.ctrl, self.root_ctrl.ctrl])

        # create rig controls set.
        self.controls_set = cmds.sets([self.global_ctrl.ctrl, self.main_ctrl.ctrl, self.root_ctrl.ctrl], name=self.top_group + 'Controls')
        cmds.setAttr('{}.ihi'.format(self.controls_set), True)
        
        # Default rig spaces.
        self.global_space = common.create_node('transform', 'global', suffix='space', parent=self.top_group)
        self.main_space = common.create_node('transform', 'main', suffix='space', parent=self.top_group)

        connect.matrix_constraint(self.global_ctrl.obj, self.global_space)
        connect.matrix_constraint(self.main_ctrl.obj, self.main_space)
        
        # Rig main groups.
        attribute.add_header_attribute(self.global_ctrl.obj, 'VISIBILITY')

        if self.rig_hierarchy['rig']:
            rig_group = common.create_node('transform', 'rig', suffix='grp', parent=self.top_group)
            attr = attribute.add_switch(self.global_ctrl.obj, 'controls', keyable=False, nn='CONTROLS')
            cmds.connectAttr(self.global_ctrl.obj + '.{}'.format(attr), rig_group + '.v')

        if self.rig_hierarchy['skeleton']:
            skeleton_group = common.create_node('transform', 'skeleton', suffix='grp', parent=self.top_group)
            attr = attribute.add_switch(self.global_ctrl.obj, 'skeleton', keyable=False, nn='SKELETON')
            cmds.connectAttr(self.global_ctrl.obj + '.{}'.format(attr), skeleton_group + '.v')

        if self.rig_hierarchy['geo']:
            geo_group = common.create_node('transform', 'geo', suffix='grp', parent=self.top_group)
            attr = attribute.add_switch(self.global_ctrl.obj, 'geo', keyable=False, nn='GEO')
            cmds.connectAttr(self.global_ctrl.obj + '.{}'.format(attr), geo_group + '.v')
            attribute.add_header_attribute(self.global_ctrl.obj, 'GEOMETRY')
            attribute.add_enum_attribute(self.global_ctrl.obj, 'LOD', enum_names=self.lods, keyable=False)
            attribute.add_enum_attribute(self.global_ctrl.obj, 'status', enum_names=['unlocked', 'template', 'locked'], keyable=False)
            cmds.setAttr(geo_group + '.overrideEnabled', True)
            cmds.connectAttr(self.global_ctrl.obj + '.status', geo_group + '.overrideDisplayType')
            for i, lod in enumerate(self.lods):
                group = common.create_node('transform', lod, suffix='grp', parent=geo_group)
                connect.sdk(self.global_ctrl.obj + '.LOD', [i-1, i, i+1], group + '.v', [0, 1, 0])
        
        if self.rig_hierarchy['spaces']:
            extras_group = common.create_node('transform', 'spaces', suffix='grp', parent=self.top_group)
        
        if self.rig_hierarchy['extras']:
            extras_group = common.create_node('transform', 'extras', suffix='grp', parent=self.top_group)
        

        if self.ikfk:
            attribute.add_header_attribute(self.global_ctrl.obj, 'IKFK')
            for attr in self.ikfk:
                attribute.add_switch(self.global_ctrl.obj, attr, keyable=True, reverse=True)
            
    def build(self):
        """ Method meant to be overriden by child class.
        """
        pass
        
    def post_build(self):
        """ Method meant to be overriden by child class.
        """
        pass
        
    def clean_up(self):
        """ Method meant to be overriden by child class.
        """
        pass

def replace_temporary_inputs():
    tmp_inputs = cmds.ls('*_tmpinp')
    for node in tmp_inputs:
        dict_attrs =cmds.listAttr(node, ud=True)
        input_node = node.replace('_tmpinp', '')
        if cmds.objExists(input_node):
            print(input_node)
            print(dict_attrs)
            for attr in dict_attrs:
                conn_dict = attribute.get_attribute_dict(node, attr)
                conn_dict['attributes'][0] = input_node
                connect.rebuild_connection(conn_dict)
                print('{} has been rebuilt.'.format(attr))
        cmds.delete(node)
    