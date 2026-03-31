import maya.api.OpenMaya as om

SIDES_LIST = ['', 'l', 'r', 'f', 'b', 'lf', 'lb', 'rf', 'rb']
SIDE_SWITCH = {'': '', 'l': 'r', 'r': 'l'}

NODES_SUFFIX = {'addDoubleLinear': 'adl',
                'addMatrix': 'addm',
                'aimMatrix': 'aimm',
                'angleBetween': 'abt',
                'blendColors': 'blc',
                'blendMatrix': 'blm',
                'blendShape': 'bls',
                'blendTwoAttr': 'bla',
                'blendWeighted': 'blw',
                'choice': 'chc',
                'clamp': 'clmp',
                'closestPointOnMesh': 'cpm',
                'closestPointOnSurface': 'cps',
                'cluster': 'cls',
                'composeMatrix': 'cmm',
                'condition': 'cnd',
                'curveInfo': 'crvi',
                'decomposeMatrix': 'dmm',
                'deformBend': 'dbnd',
                'deformSine': 'dsin',
                'deformSquash': 'dsqs',
                'deformTwist': 'dtws',
                'deformWave': 'dwav',
                'deltaMush': 'dmsh',
                'distanceBetween': 'dist',
                'expression': 'expr',
                'ffd': 'ffd',
                'follicle': 'flc',
                'fourByFourMatrix': 'ffm',
                'ikEffector': 'eff',
                'ikHandle': 'ikh',
                'ikMCsolver': 'ikmcs',
                'ikPASolver': 'ikpas',
                'ikRPsolver': 'ikrps',
                'ikSCsolver': 'ikscs',
                'ikSolver': 'iks',
                'ikSplineSolver': 'iksps',
                'jiggle': 'jgl',
                'joint': 'jnt',
                'lattice': 'lat',
                'locator': 'loc',
                'motionPath': 'mpth',
                'multDoubleLinear': 'mdl',
                'multMatrix': 'mm',
                'multiplyDivide': 'mdv',
                'nearestPointOnCurve': 'npc',
                'orientConstraint': 'ocns',
                'pairBlend': 'pbld',
                'parentConstraint': 'cns',
                'aimConstraint': 'aimcns',
                'passMatrix': 'psm',
                'plusMinusAverage': 'pma',
                'pointConstraint': 'pcns',
                'pointMatrixMult': 'pmm',
                'pointOnCurveInfo': 'pci',
                'pointOnSurfaceInfo': 'psi',
                'poleVectorConstraint': 'pvcns',
                'ramp': 'rmp',
                'remapColor': 'rmc',
                'remapValue': 'rmv',
                'reverse': 'rev',
                'scaleConstraint': 'scns',
                'setRange': 'rng',
                'shrinkWrap': 'shw',
                'skinCluster': 'sc',
                'softMod': 'smod',
                'softModHandle': 'smodh',
                'surfaceInfo': 'suri',
                'tension': 'ten',
                'transform': None,
                'vectorProduct': 'vcp',
                'wire': 'wire',
                'wrap': 'wrap',
                'wtAddMatrix': 'wtam'}
# colors
COLOR_STR = ['yellow',
             'light yellow',
             'dark yellow',
             'blue',
             'light blue',
             'dark blue',
             'red',
             'light red',
             'dark red',
             'green',
             'light green',
             'dark green',
             'magenta',
             'brown',
             'light brown',
             'dark brown',
             'white',
             'grey',
             'light grey',
             'dark grey',
             'black']
COLOR_SIDE_TO_STR = {'': 'yellow',
                     'l': 'blue',
                     'r': 'red',
                     'f': 'yellow',
                     'b': 'yellow',
                     'lf': 'blue',
                     'lb': 'blue',
                     'rf': 'red',
                     'rb': 'red'}
COLOR_INDEX = [17, 22, 25, 6, 18, 5, 13, 20, 12, 14, 26, 7, 9, 10, 24, 11, 16, 2, 3, 1]
COLOR_STR_TO_INDEX = dict(zip(COLOR_STR, COLOR_INDEX))
COLOR_INDEX_TO_STR = dict(zip(COLOR_STR, COLOR_INDEX))

OVERRIDE_TYPES = ['transform', 'mesh', 'nurbsCurve', 'nurbsSurface']

ROTATION_ORDER = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']

# axis vectors
AXIS_STR = ['+x', '-x', '+y', '-y', '+z', '-z']
AXIS_LONG = ['px', 'nx', 'py', 'ny', 'pz', 'nz']
AXIS_NEG = {'+x': '-x', '+y': '-y', '+z': '-z', '-x': '+x', '-y': '+y', '-z': '+z'}
AXIS_NORM = {'+x': '+y', '+y': '+z', '+z': '+x', '-x': '-y', '-y': '-z', '-z': '-x'}
AXIS_PREV = {'+x': '+z', '+y': '+x', '+z': '+y', '-x': '-z', '-y': '-x', '-z': '-y'}
AXIS_VEC = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]
AXIS_ATTR = [0, 0, 1, 1, 2, 2]
AXIS_MVEC = [om.MVector(axis[0], axis[1], axis[2]) for axis in AXIS_VEC]

AXIS_STR_TO_VEC = dict(zip(AXIS_STR, AXIS_VEC))
AXIS_STR_TO_MVEC = dict(zip(AXIS_STR, AXIS_MVEC))
AXIS_STR_TO_LONG = dict(zip(AXIS_STR, AXIS_LONG))
AXIS_STR_TO_ATTR = dict(zip(AXIS_STR, AXIS_ATTR))
