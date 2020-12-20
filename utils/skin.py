import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

from rigging.utils import api, data_io, common
from rigging.utils.name import Name


def get_skincluster(dag_node):
    """Get skin cluster connected to a given shape

    Wrapper for the MEL command

    Args:
        dag_node (str): Shape node deformed by skinCluster

    Returns:
        str: Return connected skin cluster
    """
    dag_node = dag_node.split('.', 1)[0]
    return mel.eval('findRelatedSkinCluster ' + dag_node)


def get_influences(skin):
    """Returns all influences of a given skincluster

    Args:
        skin (str): skinCluster node

    Returns:
        list[str]: Return skin cluster influences
    """
    return cmds.skinCluster(skin, query=True, influence=True)


def get_weights_dict(skin):
    # get the MFnSkinCluster
    skinFn = api.get_mfn_skinCluster(skin)

    # get the MDagPath for all influence
    inf_dags = skinFn.influenceObjects()
    # create a dictionary whose key is the MPlug indice id and
    # whose value is the influence list id
    inf_ids = {}
    infs = []
    for x in xrange(len(inf_dags)):
        inf_path = inf_dags[x].fullPathName()
        inf_id = int(skinFn.indexForInfluenceObject(inf_dags[x]))
        inf_ids[inf_id] = x
        infs.append(inf_path)

    # get the MPlug for the weightList and weights attributes
    wl_plug = skinFn.findPlug('weightList', True)
    w_plug = skinFn.findPlug('weights', True)
    wl_attr = wl_plug.attribute()
    w_attr = w_plug.attribute()
    w_inf_ids = om.MIntArray()

    # the weights are stored in dictionary, the key is the vtx_id, 
    # the value is another dictionary whose key is the influence id and 
    # value is the weight for that influence
    weights = {}
    for vId in xrange(wl_plug.numElements()):
        vtx_weights = {}
        # tell the weights attribute which vertex id it represents
        w_plug.selectAncestorLogicalIndex(vId, wl_attr)

        # get the indices of all non-zero weights for this vert
        w_inf_ids = w_plug.getExistingArrayAttributeIndices()

        # create a copy of the current w_plug
        inf_plug = om.MPlug(w_plug)
        for inf_id in w_inf_ids:
            # tell the inf_plug it represents the current influence id
            inf_plug.selectAncestorLogicalIndex(inf_id, w_attr)

            # add this influence and its weight to this verts weights
            try:
                vtx_weights[inf_ids[inf_id]] = inf_plug.asDouble()
            except KeyError:
                # assumes a removed influence
                pass
        weights[vId] = vtx_weights
    weights_dict = {}
    weights_dict['joints'] = get_influences(skin)
    weights_dict['weights'] = weights
    return weights_dict


def export_weights(dag_node, path):
    skin = get_skincluster(dag_node)
    weight_dict = get_weights_dict(skin)
    data_io.data_io(weight_dict, file_name=dag_node, file_path=path, force_export=True)
    print 'Exported {0} skin weights to: {1}/{0}.json'.format(dag_node, path)


def import_weights(dag_node, path):
    weight_dict = data_io.data_io(mode='import', file_name=dag_node, file_path=path)

    namer = Name(dag_node)
    skin_name = namer.replace(suffix='SC')
    shape = common.get_shape(dag_node)
    influences = weight_dict['joints']
    weights = weight_dict['weights']

    skin = cmds.skinCluster(influences, dag_node, name=skin_name, toSelectedBones=True)[0]

    for inf in influences:
        cmds.setAttr('{}.liw'.format(inf))

    # normalize needs turned off for the prune to work
    skin_norm = cmds.getAttr('{}.normalizeWeights'.format(skin))
    if skin_norm != 0:
        cmds.setAttr('{}.normalizeWeights'.format(skin), 0)
    cmds.skinPercent(skin, shape, nrm=False, prw=100)

    # restore normalize setting
    if skin_norm != 0:
        cmds.setAttr('{}.normalizeWeights'.format(skin), skin_norm)

    for vtx_id, w_data in weights.items():
        wl_attr = '{}.weightList[{}]' .format(skin, vtx_id)
        for inf_id, inf_value in w_data.items():
            w_attr = '.weights[{}]'.format(inf_id)
            cmds.setAttr(wl_attr + w_attr, inf_value)
    print 'Imported {} skinCluster weights.'.format(dag_node)


def add_influences(skin, influences):
    """Add influence to skinCluster

    Args:
        skin (str): existing skinCluster
        influences (list[str]): new influences to add to skinCluster
    """
    existing_influences = cmds.skinCluster(skin, query=True, influence=True)
    new_influences = list(set(influences) - set(existing_influences))
    cmds.skinCluster(skin, edit=True, addInfluence=new_influences, weight=0, lockWeights=True)


def copy_skincluster(source, targets, smooth=True, method='closestPoint', add_missing_influences=True):
    """Copy skin cluster weights from source to targets

    Args:
        source (str): Source shape bound by skin cluster
        targets (list[str]): Shape nodes to copy skin cluster to
        smooth (bool): Weights are smoothly interpolated between closest vertices
        method (str): Method used for vertex correspondence between shapes
        add_missing_influences (bool): Add missing influences to existing target skin clusters

    Returns:
        list[str]: Return target skin cluster nodes
    """
    source_skin = get_skincluster(source)
    all_influences = get_influences(source_skin)

    # filters joints from influences
    joint_list = []
    influence_list = []
    for item in all_influences:
        if cmds.objectType(item) == 'joint':
            joint_list.append(item)
        else:
            influence_list.append(item)

    target_skin_list = []
    for target in targets:
        target_skin = get_skincluster(target)

        if not target_skin:
            target_skin = cmds.skinCluster(joint_list, target, toSelectedBones=True)[0]
            cmds.skinCluster(target_skin, edit=True, addInfluence=influence_list)
        elif add_missing_influences:
            target_influences = get_influences(target_skin)
            missing_influences = list(set(all_influences) - set(target_influences))

            if missing_influences:
                add_influences(target_skin, missing_influences)

        if method == 'uv':
            # TODO: specify UV maps
            cmds.copySkinWeights(sourceSkin=source_skin,
                                 destinationSkin=target_skin,
                                 noMirror=True,
                                 uvSpace=['map1', 'map1'],
                                 influenceAssociation=['name', 'closestJoint', 'oneToOne'],
                                 sampleSpace=0,
                                 smooth=smooth)
        else:
            cmds.copySkinWeights(sourceSkin=source_skin,
                                 destinationSkin=target_skin,
                                 noMirror=True,
                                 surfaceAssociation=method,
                                 influenceAssociation=['name', 'closestJoint', 'oneToOne'],
                                 sampleSpace=0,
                                 smooth=smooth)

        target_skin_list.append(target_skin)

    return target_skin_list