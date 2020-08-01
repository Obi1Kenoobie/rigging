import maya.cmds as cmds
import os




def denoise_geometry(geo='', iterations=4, substep=1, start=1, end=120):
    # go to start frame
    cmds.currentTime(start)

    # alembic paths
    tmp_path = os.environ['TMP']
    final_path = 'C://Users//Mario//Documents//maya//projects//jj_rig//cache//alembic//'

    # create geo duplicate
    copy = cmds.duplicate(geo, n='tmp_GEO')[0]
    cmds.connectAttr('{}.outMesh'.format(cmds.listRelatives(geo, s=True)[0]), '{}Shape.inMesh'.format(copy))

    # exporting first alembic
    copy_long = cmds.ls(copy, an=True)[0]
    previous_cache = ''
    current_cache = final_path + 'tmp.abc'
    cmds.AbcExport(
        j='-frameRange {} {} -dataFormat ogawa -root {} -file {}'.format(start, end, copy_long, current_cache))

    cmds.delete(copy)

    for i in range(iterations):
        cmds.currentTime(start)

        # new geo copy
        copy = cmds.duplicate(geo, n='tmp_GEO')[0]

        # import alembics for blend
        alembic1 = cmds.AbcImport(current_cache, mode='import')
        alembic2 = cmds.AbcImport(current_cache, mode='import')

        alembic_geo1 = _get_alembic_geo(alembic1)
        alembic_geo2 = _get_alembic_geo(alembic2)

        previous_cache = current_cache
        # offset alembics to avarage positions
        cmds.setAttr('{}.offset'.format(alembic1), substep)
        cmds.setAttr('{}.offset'.format(alembic2), -1 * substep)

        # drive copy
        cmds.blendShape(alembic_geo1, alembic_geo2, copy, w=[(0, 0.5), (1, 0.5)])

        copy_long = cmds.ls(copy, an=True)[0]
        if i + 1 == iterations:
            current_cache = final_path + 'tmp{}.abc'.format(i)
        else:
            current_cache = tmp_path + 'tmp{}.abc'.format(i)
        cmds.AbcExport(
            j='-frameRange {} {} -dataFormat ogawa -root {} -file {}'.format(start, end, copy_long, current_cache))

        # delete alembics and temp geo
        cmds.delete(copy, alembic_geo1, alembic_geo2)

    final_alembic = cmds.AbcImport(current_cache, mode='import')
    alembic_geo = _get_alembic_geo(final_alembic)
    return alembic_geo


def _get_alembic_geo(alembic_node):
    geo = cmds.listConnections('{}.outPolyMesh[0]'.format(alembic_node))[0]

    return geo


geo = cmds.ls(sl=True)[0]
denoise_geometry(geo=geo, iterations=8, substep=0.5)
