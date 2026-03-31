from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds

from rigging.utils.math import get_matrix, set_matrix, get_align_matrix, get_polevector_position_vector, get_translation_matrix
from rigging.utils.attribute import set_attribute_dict, get_attribute_dict, add_string_attribute
from rigging.utils.name import get_namespace

from functools import wraps



def undo(func):
    """ Puts the wrapped `func` into a single Maya Undo action, then 
        undoes it when the function enters the finally: block """
    @wraps(func)
    def _undofunc(*args, **kwargs):
        try:
            # start an undo chunk
            cmds.undoInfo(ock=True)
            return func(*args, **kwargs)
        finally:
            # after calling the func, end the undo chunk and undo
            cmds.undoInfo(cck=True)

    return _undofunc


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class IKFKMatchUI(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(IKFKMatchUI, self).__init__(parent)

        self.setWindowTitle("IK/FK Match Tool")
        self.setMinimumSize(270, 80)
        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        
        self.key_controls = True
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.ikfkmatch_btn = QtWidgets.QPushButton()
        self.ikfkmatch_btn.setText('IK<>FK')
        self.ikfkmatch_btn.setIconSize(QtCore.QSize(50, 50))
        self.ikfkmatch_btn.setToolTip("Select A Control eg.: foot_ik_l_ctrl, lowerarm_l_fk_ctrl")
        
        self.key_controls_check = QtWidgets.QCheckBox("Key Controls")
        self.key_controls_check.setToolTip("If unchecked will simply match without keying controls")
        self.key_controls_check.setCheckState(QtCore.Qt.Checked)

    def create_layout(self):
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.addWidget(self.ikfkmatch_btn)
        main_layout.addWidget(self.key_controls_check)
        main_layout.addStretch(1)

    def create_connections(self):
        self.ikfkmatch_btn.clicked.connect(self.ik_fk_match)
        self.key_controls_check.stateChanged.connect(self.set_key_controls)
    
    def set_key_controls(self):
        if self.key_controls_check.checkState() == QtCore.Qt.Checked:
            self.key_controls = True
        
        else:
            self.key_controls = False
    
    @undo
    def ik_fk_match(self):
        selected_ctrl = cmds.ls(sl=True)[0]
        ns, base_name = get_namespace(selected_ctrl)
        
        # check if selected control has switcher
        if cmds.attributeQuery('switcher', node=selected_ctrl, exists=True):
            # get dictionary describing matching
            switcher_dict = get_attribute_dict(selected_ctrl, 'switcher')
            
            # calculating switch setting
            switch_attr = next(iter(switcher_dict))
            switch_status = cmds.getAttr(ns + switch_attr)
            switch_set = not switch_status
            
            # if switch is set to False we need to match IK if is set to True we need to match FK
            mode = 'IK'
            not_mode = 'FK'
            if switch_status:
                mode = 'FK'
                not_mode = 'IK'
            
            # get current frame
            cf = cmds.currentTime(query=True)
            
            # switching mode
            if self.key_controls:
                cmds.setKeyframe(ns + switch_attr, t= cf - 1)
            cmds.setAttr(ns + switch_attr, switch_set)
            
            if self.key_controls:
                cmds.setKeyframe(ns + switch_attr)

            # setting matching positions and orientations
            for ctrl in switcher_dict[switch_attr][mode]:
                ctrl_list = switcher_dict[switch_attr][mode][ctrl]
                
                ctrl = ns + ctrl
                
                # if pv control set its position
                if len(ctrl_list) == 3:
                    pv_pos = get_polevector_position_vector(
                                                        [
                                                    get_matrix(ns + ctrl_list[0]),
                                                    get_matrix(ns + ctrl_list[1]),
                                                    get_matrix(ns + ctrl_list[2])
                                                ],
                                                
                                                pv_distance=40.0
                    )
                    
                    pos_mtx = get_translation_matrix([pv_pos.x, pv_pos.y, pv_pos.z])
                    set_matrix(ctrl, pos_mtx)
                    
                else:
                    # first setting position then aligning control to target
                    pos_obj = ns + ctrl_list[0]
                    ori_obj = ns + ctrl_list[1]
                    source_aim = ctrl_list[2][0]
                    target_aim = ctrl_list[2][1]
                    source_up = ctrl_list[3][0]
                    target_up = ctrl_list[3][1]

                    set_matrix(ctrl, get_matrix(pos_obj))

                    rot_mtx = get_align_matrix(
                                        get_matrix(ori_obj), 
                                        get_matrix(ctrl), 
                                        source_aim=source_aim, 
                                        source_up=source_up, 
                                        target_aim=target_aim, 
                                        target_up=target_up)
                    
                    set_matrix(ctrl, rot_mtx)
                
                # key currnet active mode controls
                if self.key_controls:
                    cmds.setKeyframe(ctrl + '.translate')
                    cmds.setKeyframe(ctrl + '.rotate')
                    cmds.setKeyframe(ctrl + '.scale')
            
            # setting a key on previous mode controls 1 frame before current one
            if self.key_controls:
                for ctrl in switcher_dict[switch_attr][not_mode]:
                    ctrl = ns + ctrl
                    
                    cmds.setKeyframe(ctrl + '.translate', time= cf - 1)
                    cmds.setKeyframe(ctrl + '.rotate', time= cf - 1)
                    cmds.setKeyframe(ctrl + '.scale', time= cf - 1)
            
            cmds.sl(cl=True)

def run():
    try:
        ikfkmatch_ui.close() # pylint: disable=E0601
        ikfkmatch_ui.deleteLater()
    except:
        pass

    ikfkmatch_ui = IKFKMatchUI()
    ikfkmatch_ui.show()
    
    return ikfkmatch_ui