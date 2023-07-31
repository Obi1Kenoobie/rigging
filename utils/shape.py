import os
import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.utils import data_io, common, api, globals
from rigging.utils.name import Name

SHAPES_PATH = os.path.dirname(os.path.realpath(__file__)) + "\\_shapes"


def create(name, 
           shape_type=None, 
           shape_up='+y', 
           shape_aim='+x', 
           color=None, 
           size=1.0, 
           parent=None, 
           positions=[], 
           knots=[], 
           degree=1, 
           form=1):

    namer = Name(name)
    side = namer.side
    shape_name = name + 'Shape'

    if shape_type:
        data = import_shape(file_name=shape_type, file_path=SHAPES_PATH)
        for key in data['shapes']:
            color = data['shapes'][key]['color']
            positions = data['shapes'][key]['positions']
            knots = data['shapes'][key]['knots']
            degree = data['shapes'][key]['degree']
            form = data['shapes'][key]['form']
    
    # scaling things up
    positions = [[pos[0]*size, pos[1]*size, pos[2]*size] for pos in positions]
    cvs = om.MPointArray(positions)
    knots = om.MDoubleArray(knots)

    if not color and side:
        color = globals.COLOR_SIDE_TO_STR[side]

    if not parent:
        parent = cmds.createNode('transform', name=name)
    
    parent = api.get_mobj(parent)

    nurbsFn = om.MFnNurbsCurve()
    shape = nurbsFn.create(cvs, knots, degree, form, False, False, parent=parent)
    shapFn = om.MFnDependencyNode(shape)
    shapFn.setName(shape_name)
    common.set_override_color(shape_name, color=color)
    return shape_name


def mirror(dag_node, world=False):
    namer = Name(dag_node)
    side = namer.side
    if not side:
        return cmds.warning('object has not specific side.')
    base_side = 'L_'
    mirror_side = 'R_'
    if 'R' in side:
        base_side = 'R_'
        mirror_side = 'L_'
    shapes = common.get_shapes(dag_node)

    # find mirror transform
    mirror_obj = dag_node.replace(base_side, mirror_side)
    if cmds.objExists(mirror_obj):
        mirror_shapes = common.get_shapes(mirror_obj)
        if not len(mirror_shapes) == len(shapes):
            return cmds.warning('couldn\'t find equal number of shapes under mirror object.')
        else:
            for i, shape in enumerate(shapes):
                mirror_positions = [om.MPoint(point.x*-1, point.y, point.z) for point in get_cv_positions(shape, world=world)]
                set_cv_positions(mirror_shapes[i], mirror_positions, world=world)
    else:
        return cmds.warning('Couldn\'t find mirror object.')


def export_shape(dag_node, file_name=None, asset_name=None, file_path=None, world=False, force_export=False):
    if not file_name:
        file_name = dag_node
    data = get_shape_data(dag_node, world=world)
    data_io.data_io(data=data, mode='export', file_name=file_name, asset_name=asset_name, file_path=file_path, file_type='controlShape', force_export=force_export)


def import_shape(file_name=None, file_path=None):
    return data_io.data_io(mode='import', file_name=file_name, file_path=file_path)


def is_nurbsCurve(curve_shape):
    if cmds.objectType(curve_shape) == 'transform':
        curve_shape = common.get_shape(curve_shape)

    return cmds.objectType(curve_shape) == 'nurbsCurve'


def get_shape_degree(curve_shape):
    return api.get_mfn_nurbsCurve(curve_shape).degree


def get_shape_spans(curve_shape):
    return api.get_mfn_nurbsCurve(curve_shape).numSpans


def get_cvs(curve_shape):
    return cmds.ls(curve_shape + '.cv[*]', flatten=True)


def get_cv_num(curve_shape):
    return api.get_mfn_nurbsCurve(curve_shape).numCVs


def get_cv_positions(curve_shape, world=False, as_list=False):
    space = om.MSpace.kObject
    if world:
        space = om.MSpace.kWorld
    cvs_pos = api.get_mfn_nurbsCurve(curve_shape).cvPositions(space=space)
    if as_list:
        return [[pos[0], pos[1], pos[2]] for pos in cvs_pos]
    else:
        return cvs_pos


def set_cv_positions(curve_shape, cv_positions, world=False):
    space = om.MSpace.kObject
    if world:
        space = om.MSpace.kWorld
    positions_marray = cv_positions
    if isinstance(cv_positions, list):
        positions_marray = om.MPointArray(cv_positions)
    curve_fn = api.get_mfn_nurbsCurve(curve_shape)
    curve_fn.setCVPositions(positions_marray, space=space)
    curve_fn.updateCurve()


def get_shape_form(curve_shape):
    return api.get_mfn_nurbsCurve(curve_shape).form


def get_shape_knots(curve_shape, as_list=False):
    knots = api.get_mfn_nurbsCurve(curve_shape).knots()
    if as_list:
        return [knot for knot in knots]
    return knots


def get_shape_data(dag_node, world=False):
    data = data_io.Data()

    data.type = 'nurbsCurve'
    data.name = dag_node
    data.side = Name(data.name).side

    shapes_list = common.get_shapes(dag_node)
    shapes_dict = data_io.Data()
    if shapes_list:
        for shp in shapes_list:
            if is_nurbsCurve(shp):
                shape_dict = data_io.Data()
                shape_dict.degree = get_shape_degree(shp)
                shape_dict.spans = get_shape_spans(shp)
                shape_dict.form = get_shape_form(shp)
                shape_dict.knots = get_shape_knots(shp, as_list=True)
                shape_dict.positions = get_cv_positions(shp, world=world, as_list=True)
                shape_dict.color = common.get_override_color(shp)

                shapes_dict[shp] = shape_dict.__dict__
            else:
                continue

        data.shapes = shapes_dict.__dict__

    return data
