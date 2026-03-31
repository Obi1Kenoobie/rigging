from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om



### UTILS ###
def get_scene_fps():
    # get current time unit
    time_unit = cmds.currentUnit(q=True, t=True)

    # get the index in the list defined for the settings windows
    index = mel.eval(f'getIndexFromCurrentUnitCmdValue("{time_unit}")') - 1

    # get the ui name for the tiem unit (something fps)
    fps_name = mel.eval(f'getTimeUnitDisplayString({index});')

    # if you want the number now you can process the name since it will be consistent
    fps_number = float(fps_name.split(' ')[0])
    
    return fps_number


def get_scene_unit_multiply():
    # get current linear unit
    linear_unit = cmds.currentUnit(q=True, l=True)

    unit_dict = {
            'mm' : 1000,
            'cm' : 100,
            'm' : 1, 
            'km' : 0.001
        }

    return unit_dict[linear_unit]


def get_current_transform_velocity(dag_obj):
    current_frame = cmds.currentTime(q=True)

    current_pos = om.MVector(cmds.xform(dag_obj, q=True, t=True, ws=True))

    cmds.currentTime(current_frame - 1)

    prev_pos = om.MVector(cmds.xform(dag_obj, q=True, t=True, ws=True))

    cmds.currentTime(current_frame)
    
    # calculating velocity and multiply the value based on scene units
    velocity_vec = ( ( current_pos - prev_pos ) / get_scene_fps() ) * get_scene_unit_multiply() 

    velocity = velocity_vec.length()
    
    return [velocity, velocity_vec]


def apply_slide_fix(threshold=3.0, smooth_amount=0.0):
    velocity_smoothing = False
    if smooth_amount > 0:
        velocity_smoothing = True

    for obj in cmds.ls(sl=True):
        # checking for anim layer
        anim_layer = cmds.animLayer(q=True, blr=True)
        if anim_layer:
            anim_layer = anim_layer[0]
            parent_layer = cmds.animLayer(anim_layer, q=True, p=True)

            cmds.animLayer(anim_layer,e=True, ca=parent_layer)

        # get current timeline range
        time_range_min = cmds.playbackOptions(q=True, minTime=True)
        time_range_max = cmds.playbackOptions(q=True, maxTime=True)


        # calculate velocity
        current_time = time_range_min
        velocities = []
        while(current_time <= time_range_max):
            cmds.currentTime(current_time)
            velocities.append(get_current_transform_velocity(obj)[0])
            cmds.currentTime(current_time + 1)
            current_time = cmds.currentTime(q=True)

        cmds.currentTime(time_range_min)

        # getting velocity as percentage of max velocity
        max_velocity = max(velocities)
        velocity_perc = [(value * 100)/max_velocity for value in velocities]

        # creating a debug locator to better visualize the velocity graph
        loc_name = f'{obj}_velocityDebug'
        if cmds.objExists(loc_name):
            cmds.delete(loc_name)
        debug_loc = cmds.spaceLocator(n=loc_name)[0]
        cmds.addAttr(debug_loc, at='float', ln='velocity', k=True)
        cmds.addAttr(debug_loc, at='float', ln='threshold', k=True)
        if velocity_smoothing:
            cmds.addAttr(debug_loc, at='float', ln='smoothed_velocity', k=True)
        cmds.addAttr(debug_loc, at='float', ln='result', k=True)

        # key debug attributes
        i=0
        for time in range(int(time_range_min), int(time_range_max + 1)):
            vel_value = velocity_perc[i]
            cmds.setKeyframe(debug_loc, at='velocity', al='BaseAnimation', t=time, v=vel_value)
            cmds.setKeyframe(debug_loc, at='threshold', al='BaseAnimation', t=time, v=threshold)
            if velocity_smoothing:
               cmds.setKeyframe(debug_loc, at='smoothed_velocity', al='BaseAnimation', t=time, v=vel_value)
            i+=1

        # smoothing velocity attribute if needed
        if velocity_smoothing:
            cmds.selectKey(debug_loc, at='smoothed_velocity', cl=True)
            cmds.selectKey(debug_loc, at='smoothed_velocity', time=(int(time_range_min), int(time_range_max)))
            cmds.filterCurve(f='gaussian', w=smooth_amount, sc=8, uq=True, sk=True)


        # calculating result velocity and listing static frames
        i=0
        k=0
        static_ranges = []
        static_range = []
        for time in range(int(time_range_min), int(time_range_max + 1)):
            vel_value = velocity_perc[i]
            compare_value = vel_value
            
            # using smooth velocity values if needed
            if velocity_smoothing:
                compare_value = cmds.getAttr(f'{debug_loc}.smoothed_velocity',time=time)
            
            # setting velocity to 0 if value is below selected threshold
            if compare_value <= threshold or vel_value <= threshold:
                cmds.setKeyframe(debug_loc, at='result', al='BaseAnimation', t=time, v=0.0)
                static_range.append(time)
            else:
                cmds.setKeyframe(debug_loc, at='result', al='BaseAnimation', t=time, v=vel_value)
                k += 1
                if static_range:
                    static_ranges.append(static_range)
                static_range = []
            i += 1
        
        if static_range and not static_range in static_ranges:
            static_ranges.append(static_range)

        # calculate average positions of static ranges
        average_positions = []
        for sr in static_ranges:
            positions = [cmds.getAttr(f'{obj}.t', time=t)[0] for t in sr]
            if positions:
                average_positions.append(
                                    [
                                        sum(i for i, j, k in positions) / len(positions),
                                        sum(j for i, j, k in positions) / len(positions),
                                        sum(k for i, j, k in positions) / len(positions)
                                    ]
                                )

        # updating selection translation keys with new average positions
        for i, ap in enumerate(average_positions):
            for frame in static_ranges[i]:
                cmds.setKeyframe(obj, at='tx', time=frame, v=ap[0])
                cmds.setKeyframe(obj, at='ty', time=frame, v=ap[1])
                cmds.setKeyframe(obj, at='tz', time=frame, v=ap[2])


        # adding some colour to debug attributes
        velocity_anim_node = cmds.listConnections(f'{debug_loc}.velocity', type='animCurveTU')[0]
        threshold_anim_node = cmds.listConnections(f'{debug_loc}.threshold', type='animCurveTU')[0]
        result_anim_node = cmds.listConnections(f'{debug_loc}.result', type='animCurveTU')[0]
        cmds.setAttr(f'{velocity_anim_node}.curveColor', *(1, 1, 0), type='double3')
        cmds.setAttr(f'{velocity_anim_node}.useCurveColor', True)
        cmds.setAttr(f'{threshold_anim_node}.curveColor', *(1, 0, 0), type='double3')
        cmds.setAttr(f'{threshold_anim_node}.useCurveColor', True)
        cmds.setAttr(f'{result_anim_node}.curveColor', *(0, 1, 0), type='double3')
        cmds.setAttr(f'{result_anim_node}.useCurveColor', True)
        if velocity_smoothing:
            smothing_anim_node = cmds.listConnections(f'{debug_loc}.smoothed_velocity', type='animCurveTU')[0]
            cmds.setAttr(f'{smothing_anim_node}.curveColor', *(0, 0, 1), type='double3')
            cmds.setAttr(f'{smothing_anim_node}.useCurveColor', True)

        cmds.select(obj)
        cmds.selectKey(obj, cl=True)
        for rng in static_ranges:
            cmds.selectKey(obj, at='t', k=True, time=(rng[0]-10, rng[-1]+10))
            cmds.filterCurve(f='gaussian', w=3.0, sc=8, uq=True, sk=True)


### UI ###
def get_maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class FootSlideFixUI(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super(FootSlideFixUI, self).__init__(parent)

        self.setWindowTitle("Foot Sliding Fix Tool")
        self.setFixedWidth(260)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        # Labels
        self.threshold_label = QtWidgets.QLabel("Threshold")
        self.smoothing_label = QtWidgets.QLabel("Smoothing")

        # LineEdits (float input)
        self.threshold_edit = QtWidgets.QLineEdit("3.0")
        self.smoothing_edit = QtWidgets.QLineEdit("0.0")

        float_validator = QtGui.QDoubleValidator(0.0, 10000.0, 3)
        float_validator.setNotation(QtGui.QDoubleValidator.StandardNotation)

        self.threshold_edit.setValidator(float_validator)
        self.smoothing_edit.setValidator(float_validator)

        self.threshold_edit.setFixedWidth(80)
        self.smoothing_edit.setFixedWidth(80)

        # Button
        self.run_button = QtWidgets.QPushButton("Run")
        self.run_button.setFixedWidth(100)

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        # Row 1
        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(self.threshold_label)
        row1.addStretch()
        row1.addWidget(self.threshold_edit)
        #row1.addStretch()

        # Row 2
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.smoothing_label)
        row2.addStretch()
        row2.addWidget(self.smoothing_edit)
        #row2.addStretch()

        # Button row (centered)
        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.run_button)
        button_row.addStretch()

        main_layout.addLayout(row1)
        main_layout.addLayout(row2)
        main_layout.addStretch()
        main_layout.addLayout(button_row)

    def create_connections(self):
        self.run_button.clicked.connect(self.on_execute)

    def on_execute(self):
        threshold = float(self.threshold_edit.text() or 0.0)
        smooth_amount = float(self.smoothing_edit.text() or 0.0)

        apply_slide_fix(threshold, smooth_amount)


def run():
    global example_ui
    try:
        example_ui.close()
        example_ui.deleteLater()
    except:
        pass

    example_ui = FootSlideFixUI()
    example_ui.show()


run()