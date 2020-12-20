import maya.api.OpenMaya as om

SIDES_LIST = ['C', 'L', 'R', 'CF', 'CB', 'LF', 'LB', 'RF', 'RB']

NODES_SUFFIX = {'addDoubleLinear': 'ADL',
                'addMatrix': 'ADDM',
                'angleBetween': 'ABT',
                'blendColors': 'BLC',
                'blendShape': 'BLS',
                'blendTwoAttr': 'BLA',
                'blendWeighted': 'BLW',
                'blendMatrix' : 'BLM',
                'choice': 'CHC',
                'clamp': 'CLMP',
                'closestPointOnMesh': 'CPM',
                'closestPointOnSurface': 'CPS',
                'cluster': 'CLS',
                'composeMatrix': 'CMM',
                'condition': 'CND',
                'curveInfo': 'CRVI',
                'decomposeMatrix': 'DMM',
                'deformBend': 'DBND',
                'deformSine': 'DSIN',
                'deformSquash': 'DSQS',
                'deformTwist': 'DTWS',
                'deformWave': 'DWAV',
                'deltaMush': 'DMSH',
                'distanceBetween': 'DIST',
                'expression': 'EXPR',
                'ffd': 'FFD',
                'follicle': 'FLC',
                'fourByFourMatrix': 'FFM',
                'ikEffector': 'EFF',
                'ikHandle': 'IKH',
                'ikMCsolver': 'IKMCS',
                'ikPASolver': 'IKPAS',
                'ikRPsolver': 'IKRPS',
                'ikSCsolver': 'IKSCS',
                'ikSolver': 'IKS',
                'ikSplineSolver': 'IKSPS',
                'jiggle': 'JGL',
                'joint': 'JNT',
                'lattice': 'LAT',
                'locator': 'LOC',
                'motionPath': 'MPTH',
                'multDoubleLinear': 'MDL',
                'multMatrix': 'MM',
                'multiplyDivide': 'MDV',
                'nearestPointOnCurve': 'NPC',
                'pairBlend': 'PBLD',
                'passMatrix': 'PSM',
                'plusMinusAverage': 'PMA',
                'pointMatrixMultiply': 'PMM',
                'pointOnCurveInfo': 'PCI',
                'pointOnSurfaceInfo': 'PSI',
                'ramp': 'RMP',
                'remapColor': 'RMC',
                'remapValue': 'RMV',
                'reverse': 'REV',
                'setRange': 'RNG',
                'shrinkWrap': 'SHW',
                'skinCluster': 'SC',
                'softMod': 'SMOD',
                'softModHandle': 'SMODH',
                'surfaceInfo': 'SURI',
                'tension': 'TEN',
                'transform': 'TMP',
                'vectorProduct': 'VCP',
                'wire': 'WIRE',
                'wrap': 'WRAP',
                'wtAddMatrix': 'WTAM'}
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
COLOR_SIDE_TO_STR = {'C': 'yellow',
                     'L': 'blue',
                     'R': 'red',
                     'CF': 'yellow',
                     'CB': 'yellow',
                     'LF': 'blue',
                     'LB': 'blue',
                     'RF': 'red',
                     'RB': 'red'}
COLOR_INDEX = [17, 22, 25, 6, 18, 5, 13, 20, 12, 14, 26, 7, 9, 10, 24, 11, 16, 2, 3, 1]
COLOR_STR_TO_INDEX = dict(zip(COLOR_STR, COLOR_INDEX))
COLOR_INDEX_TO_STR = dict(zip(COLOR_STR, COLOR_INDEX))

OVERRIDE_TYPES = ['transform', 'mesh', 'nurbsCurve', 'nurbsSurface']

# axis vectors
AXIS_STR = ['+x', '-x', '+y', '-y', '+z', '-z']
AXIS_NEG = {'+x': '-x', '+y': '-y', '+z': '-z', '-x': '+x', '-y': '+y', '-z': '+z'}
AXIS_NORM = {'+x': '+y', '+y': '+z', '+z': '+x', '-x': '-y', '-y': '-z', '-z': '-x'}
AXIS_VEC = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]
AXIS_MVEC = [om.MVector(axis[0], axis[1], axis[2]) for axis in AXIS_VEC]

AXIS_STR_TO_VEC = dict(zip(AXIS_STR, AXIS_VEC))
AXIS_STR_TO_MVEC = dict(zip(AXIS_STR, AXIS_MVEC))