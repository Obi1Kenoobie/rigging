import json
import os
import maya.cmds as cmds

DEFAULT_PATH = 'C:/Users/{}/Documents/maya'.format(os.environ['USR'])


class Data(object):
    def __init__(self, init=None):
        if init is not None:
            self.__dict__.update(init)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]

    def __contains__(self, key):
        return key in self.__dict__

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __iter__(self):
        return iter(self.__dict__)

    def __unicode__(self):
        return unicode(repr(self.__dict__))


def data_io(data, mode='export', file_name=None, asset_name=None, file_path=None, file_type=None, force_export=False):
    if isinstance(data, Data):
        data = data.__dict__
    elif not isinstance(data, dict):
        cmds.error('Data must be either a dictionary or a Data() object')

    path = file_path
    if not path:
        root_name = 'MayaIO'
        root_path = DEFAULT_PATH + '//' + root_name
        if not os.path.exists(root_path):
            if mode == 'export':
                os.mkdir(root_path)
            else:
                cmds.error('Root directory not found!')

        folder_name = 'MiscIO'
        if file_type == 'skinCluster':
            folder_name = 'SkinIO'
        elif file_type == 'controlShape':
            folder_name = 'CtrlIO'

        if not asset_name:
            asset_name = 'Default'

        path = root_path + '//' + folder_name + '//' + asset_name
        if not os.path.exists(path):
            if mode == 'export':
                os.mkdir(path)
            else:
                return cmds.error('directory not found!')

    if not file_name:
        file_name = 'tmp'

    full_path = path + '//' + file_name + '.json'

    if mode == 'export':
        if os.path.exists(full_path) and force_export is False:
            status = cmds.confirmDialog(title='Confirm', message='Override exsisting file?', button=['Yes', 'No'],
                                        defaultButton='Yes', cancelButton='No', dismissString='No')
            if not status == 'Yes':
                return None
        with open(full_path, "w") as write_file:
            json.dump(data, write_file, indent=4, sort_keys=True)

        return 'Data exported successfully! path: {}'.format(full_path)

    elif mode == 'import':
        with open(full_path, "r") as read_file:
            data = json.load(data, read_file)
            return data
