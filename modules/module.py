import maya.cmds as cmds

from rigging.utils.common import create_node
from rigging.utils.attribute import add_switch, set_attribute_dict
from rigging.utils.name import Name
from rigging.utils.connect import matrix_constraint



class RigModule(object):
    """Rig Module Base Class handling core module methods

    Args:
        name (str | None): The name that should be used/analysed.
        inputs (str | list[str] | None): Input nodes used by the module.
        matrices (dict{str:om.MMatrix}): Matrices used by the module.
        parent (str): Module top group parent.
    """

    def __init__(self, name=None, matrices={}, inputs={}, spaces={}, parent='rig_grp', shape_up='+y', shape_aim='+x', add_to_tags=None, **kwargs):
        self.name = name
        self.namer = Name(name)
        self.add_to_tags = add_to_tags
        self.side = self.namer.side
        self.inputs = inputs
        self.spaces = spaces
        self.module_matrices = matrices
        self.shape_up = shape_up
        self.shape_aim = shape_aim
            
        self.top_group = None
        self.hierarchy = {'ik' : None,
                          'fk' : None,
                          'ikfk' : None,
                          'extra' : None}

        self.module_parent = None
        if cmds.objExists(parent):
            self.module_parent = parent

        self.module_ctrls = []
        self.module_nodes =[]
        self.module_set = None
        self.module_ctrls_set = None

        pre_build_nodes = set(cmds.ls(l=True))

        self._build_structure()
        self._build_spaces_inputs()
        self._build_temp_inputs()
        
        print('\n ---BUILDING {}--- \n'.format(self.__class__.__name__))
        self.build(**kwargs)

        self._create_controls_set()

        post_build_nodes = set(cmds.ls(l=True))

        self.module_nodes = post_build_nodes - pre_build_nodes
        
        self._create_module_set()

    def _build_structure(self):
        self.top_group = create_node('transform', self.name, parent=self.module_parent, add_to_tags=self.add_to_tags, suffix='module')
        
        for key in self.hierarchy:
            self.hierarchy[key] = create_node('transform', self.name, parent=self.top_group, add_to_tags=self.add_to_tags, suffix=key)
            # Add module groups visibility switches
            add_switch(self.top_group, key, nn=key.upper())
            cmds.connectAttr('{}.{}'.format(self.top_group, key), '{}.v'.format(self.hierarchy[key]))

    def _build_spaces_inputs(self):
        spcs_parent = None
        if cmds.objExists('spaces_grp'):
            spcs_parent = 'spaces_grp'
        
        for key, value in self.spaces.items():
            space_driver = value
            # creating temporary space input if space object is missing
            if not cmds.objExists(space_driver):
                namer = Name(space_driver, add_to_suffix='tmpinp')
                name = namer.create_name()
                self.spaces[key] = name
                space_driver = name
                # making sure not to create same transform if already exsists under other modules
                if not cmds.objExists(name):
                    create_node('transform', name, parent=self.hierarchy['extra'])

    def _build_temp_inputs(self):
        for key, value in self.inputs.items():
            if not cmds.objExists(value):
                namer = Name(value, add_to_suffix='tmpinp')
                name = namer.create_name()
                self.inputs[key] = name
                
                # making sure not to create same transform if already exsists under other modules
                if not cmds.objExists(name):
                    create_node('transform', name, parent=self.hierarchy['extra'])
    
    def build(self, **kwargs):
        """ Method meant to be overriden by child class.
        """
        pass
    
    def _create_module_set(self):
        """ ToDo: Method meant to create a set containing all module nodes.
        """
        pass
    
    def _create_controls_set(self):
        self.module_ctrls_set = cmds.sets(self.module_ctrls, name=self.top_group + '_controls')
        cmds.setAttr('{}.ihi'.format(self.module_ctrls_set), True)