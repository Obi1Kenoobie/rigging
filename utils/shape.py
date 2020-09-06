import maya.cmds as cmds

from rigging.utils import name, data_io, common, api


def create(name, shape_type=None, shape_up='+y', shape_aim='+x', color=None, size=1.0, **kwargs):
    pass


def mirror(dag_node, force=False):
    pass


def export_shape(dag_node, file_name=None, asset_name=None, file_path=None, world=False, force_export=False):
    data = get_shape_data(dag_node, world=world)
    data_io.data_io(data, mode='export', file_name=file_name, asset_name=asset_name, file_path=file_path, file_type='controlShape', force_export=force_export)


def import_shape(dag_node):
    pass


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
    space = 2
    if world:
        space = 4
    cvs_pos = api.get_mfn_nurbsCurve(curve_shape).cvPositions(space=space)
    if as_list:
        return [[pos[0], pos[1], pos[2]] for pos in cvs_pos]
    else:
        return cvs_pos


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
    data.side = name.Name(data.name).side

    shapes_list = common.get_shapes(data.name)

    shapes_dict = data_io.Data()
    for shp in shapes_list:
        shape_dict = data_io.Data()
        shape_dict.degree = get_shape_degree(shp)
        shape_dict.spans = get_shape_spans(shp)
        shape_dict.form = get_shape_form(shp)
        shape_dict.knots = get_shape_knots(shp, as_list=True)
        shape_dict.positions = get_cv_positions(shp, world=world, as_list=True)
        shape_dict.color = common.get_override_color(shp)

        shapes_dict[shp] = shape_dict.__dict__

    data.shapes = shapes_dict.__dict__

    return data
