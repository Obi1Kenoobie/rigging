import maya.cmds as cmds
import maya.OpenMaya as om

from rigging.utils import name, data_io, common


def create(name, shape_type=None, shape_up='+y', shape_aim='+x', color=None, size=1.0, **kwargs):
    pass


def mirror(dag_node):
    pass


def export_shape(dag_node, file_name=None, asset_name=None, file_path=None, world=False):
    data = get_shape_data(dag_node, world=world)
    data_io.data_io(data, mode='export', file_name=file_name, asset_name=asset_name, file_path=file_path, file_type='controlShape')


def import_shape(dag_node):
    pass


def is_nurbsCurve(curve_shape):
    if cmds.objectType(curve_shape) == 'transform':
        curve_shape = common.get_shape(curve_shape)

    return cmds.objectType(curve_shape) == 'nurbsCurve'


def get_shape_degree(curve_shape):
    return cmds.getAttr(curve_shape + '.degree')


def get_shape_spans(curve_shape):
    return cmds.getAttr(curve_shape + '.spans')


def get_cvs(curve_shape):
    return cmds.ls(curve_shape + '.cv[*]', flatten=True)


def get_cv_num(curve_shape):
    return len(get_cvs(curve_shape))


def get_cv_positions(curve_shape, world=False):
    return [cmds.xform(cv, q=True, t=True, ws=world) for cv in get_cvs(curve_shape)]


def get_shape_form(curve_shape):
    form = ['open', 'closed', 'periodic']
    return form[cmds.getAttr(curve_shape + '.form')]


def get_shape_knots(curve_shape):
    knots = om.MDoubleArray()
    curveFn = api.get_mfn_nurbsCurve(curve_shape)
    curveFn.getKnots(knots)
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
        shape_dict.knots = get_shape_knots(shp)
        shape_dict.positions = get_cv_positions(shp, world=world)
        shape_dict.color = common.get_override_color(shp)

        shapes_dict[shp] = shape_dict

    data.shapes = shapes_dict

    return data
