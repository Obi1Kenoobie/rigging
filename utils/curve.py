import maya.cmds as cmds
import maya.api.OpenMaya as om


def create_knot_vector(cv_num, degree):
    """ Takes number of CV and degree of the curve, and returns knot vector values as list.

    Args:
        cv_num (int): number of CVs
        degree (int): curve degree

    Returns:
        list[int]: list containing knots values
    """
    if cv_num <= degree:
        print "warning, number of CVs can't be less than degree + 1"
        return None
    tails_size = degree
    knots_num = cv_num + degree - 1
    knots_array = [0]*knots_num
    for i in range(0, len(knots_array)-degree+1):
        knots_array[i + degree-1] = i
    tail_value = knots_array[-tails_size-1] + 1
    for i in range(1, tails_size):
        knots_array[-i] = tail_value
    return knots_array
