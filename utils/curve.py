import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.utils.name import Name
from rigging.utils.api import get_mfn_nurbsCurve, mpoint_to_list
from rigging.utils.math import lerp


def create_knot_vector(cv_num, degree, periodic=False):
    """ Takes number of CV and degree of the curve, and returns knot vector values as list.

    Args:
        cv_num (int): number of CVs.
        degree (int): curve degree.
        periodic (bool): If True will return the knots vector as for a periodic curve.

    Returns:
        list[int]: list containing knots values.
    """
    if cv_num <= degree:
        print "warning, number of CVs can't be less than degree + 1"
        return None
    knots_num = cv_num + degree - 1
    if periodic:
        knot_max_value = cv_num - 1
        knot_min_value = cv_num - knots_num
        return range(knot_min_value, knot_max_value + 1)
    else:
        tails_size = degree
        knots_array = [0]*knots_num
        for i in range(0, len(knots_array)-degree+1):
            knots_array[i + degree-1] = i
        tail_value = knots_array[-tails_size-1] + 1
        for i in range(1, tails_size):
            knots_array[-i] = tail_value
        return knots_array


def create(name, points, degree=3, bezier=False, periodic=False, suffix='CRV'):
    """ Creates a curve with cvs at the given points.

    Args:
        name (str): name of the curve.
        points (list[list[float, float, float]]): list o positions.
        degree (int): degree of the curve.
        bezier (bool): if True will create a bezier type curve.
        periodic (bool): if True will create a closed and periodic curve.
        suffix (str): custom suffix for the curve.

    Returns:

    """
    namer = Name(name, suffix=suffix)

    # periodic curves require the last points to be the same as the "degree" points
    if periodic:
        end_points = points[:degree]
        points.extend(end_points)
    knots = create_knot_vector(len(points), degree=degree, periodic=periodic)
    return cmds.curve(name=namer.name, degree=degree, knot=knots, point=points, periodic=periodic, bezier=bezier)


def closet_point_on_curve(point, curve):
    """ Use to get closest point on curve and its parameter.

    Args:
        point (list[float]): position coordinates.
        curve (str): curve transform or its shape name.

    Returns:
        list[list[float], float]: closest point position and its parameter.
    """
    curve_fn = get_mfn_nurbsCurve(curve)
    mpoint, param = curve_fn.closestPoint(om.MPoint(point), tolerance=0.001, space=om.MSpace.kObject)
    return [mpoint_to_list(mpoint), param]


def get_point_at_param(curve, param):
    """ Use to get the point on curve at the specified parameter.

    Args:
        curve (str): curve transform or its shape.
        param (float): parameter.

    Returns:
        list[float]: point on curve at specified parameter.
    """
    curve_fn = get_mfn_nurbsCurve(curve)
    return mpoint_to_list(curve_fn.getPointAtParam(param))


def get_length(curve):
    """ Use to get curve length.

    Args:
        curve (str): curve transform or shape.

    Returns:
        float: curve's length.
    """
    curve_fn = get_mfn_nurbsCurve(curve)
    return curve_fn.length()


def get_param_at_length(curve, length):
    """ Use to get curve parameter at given length.

    Args:
        curve (str): curve transform or shape.
        length (float): some length value between 0 and curve length.

    Returns:
        float: parameter at length.
    """
    curve_fn = get_mfn_nurbsCurve(curve)
    return curve_fn.findParamFromLength(length)


def lerp_curve(curve, num=10):
    """ Function used to get "num" positions evenly spaced along the given curve.

    Args:
        curve (str): curve transform or shape.
        num (int): number of positions.

    Returns:
        list[list[float, float, float]]: list of positions along the curve.
    """
    length = get_length(curve)
    lerp_length = lerp(0, length, num=num)
    lerp_param = [get_param_at_length(curve, l) for l in lerp_length]
    return [get_point_at_param(curve, param) for param in lerp_param]
