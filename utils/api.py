import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds


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