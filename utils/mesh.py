import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigging.utils.api import get_mfn_mesh, get_dagpath


def unlock_normals(dag_node, lock=False):
    mfn_mesh = get_mfn_mesh(dag_node)
    vert_iter = om.MItMeshVertex(get_dagpath(dag_node))
    
    verts = om.MIntArray()
    while not vert_iter.isDone():
        verts.append(vert_iter.index())
        vert_iter.next()
        
    if not lock:
        mfn_mesh.unlockVertexNormals(verts)
    else:
        mfn_mesh.lockVertexNormals(verts)


def lock_normals(dag_node):
    unlock_normals(dag_node, lock=True)

