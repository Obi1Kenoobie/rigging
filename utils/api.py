import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

from rigging.utils.common import get_shape

def get_mselectionlist(dag_node):
    msel_list = om.MSelectionList()
    msel_list.add(dag_node)
    return msel_list
    

def get_dagpath(dag_node):
    msel_list = get_mselectionlist(dag_node)
    return msel_list.getDagPath(0)
    

def get_mobj(dag_node):
    msel_list = get_mselectionlist(dag_node)
    return msel_list.getDependNode(0)


def get_mplug(dag_node):
    msel_list = get_mselectionlist(dag_node)
    return msel_list.getPlug(0)


def get_mfn_nurbsCurve(dag_node):
    if cmds.objectType(dag_node, isType='transform'):
        dag_node = get_shape(dag_node)
    mobj = get_mobj(dag_node)
    return om.MFnNurbsCurve(mobj)


def get_mfn_skinCluster(dag_node):
    mobj = get_mobj(dag_node)
    return oma.MFnSkinCluster(mobj)


def mpoint_to_list(mpoint):
    return [mpoint.x, mpoint.y, mpoint.z]