import copy

from meRig.utils.globals import SIDES_LIST, NODES_SUFFIX


class Name(object):
    """Name object used for the creation and query of names
    """

    def __init__(self, name, side='', base_name='', base_index='', tags=[], index=None, suffix='', padding=2,
                 last=False, node_type=None):

        self._side = side
        self._name = name
        self._base_name = base_name
        self._base_index = base_index
        self._tags = tags
        self._index = index
        self._suffix = suffix
        self._padding = padding
        self._last = last
        self._node_type = node_type

        if self._last:
            self._suffix = 'END'

        if self._node_type in NODES_SUFFIX:
            self._suffix = NODES_SUFFIX[self._node_type]

        self._initialize_name()

        self._name_dict = {'side': self._side,
                           'base_name': self._base_name,
                           'base_index': self._base_index,
                           'tags': self._tags,
                           'index': self._index,
                           'suffix': self._suffix}

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if isinstance(value, basestring):
            self._name = value

    @property
    def side(self):
        return self._side

    @side.setter
    def side(self, value):
        if isinstance(value, basestring):
            self._side = value.upper()
        elif isinstance(value, int) and self.side:
            self._side = self._side + str(value)
        self._name_dict['side'] = self._side

    @property
    def base_name(self):
        return self._base_name

    @base_name.setter
    def base_name(self, value):
        if isinstance(value, basestring):
            self._base_name = value
        self._name_dict['base_name'] = self._base_name

    @property
    def base_index(self):
        return self._base_index

    @base_index.setter
    def base_index(self, value):
        if isinstance(value, basestring):
            self._base_index = value.upper()
        elif isinstance(value, int):
            self._base_index = self._generate_index(value)
        self._name_dict['base_index'] = self._base_index

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        if isinstance(value, basestring):
            self._tags = [value]
        elif isinstance(value, (list,)):
            self._tags = value
        self._name_dict['tags'] = self._tags

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        if isinstance(value, int):
            self._index = self._generate_index(value)
        self._name_dict['index'] = self._index

    @property
    def suffix(self):
        return self._suffix

    @suffix.setter
    def suffix(self, value):
        if isinstance(value, basestring):
            self._suffix = value.upper()
        self._name_dict['suffix'] = self._suffix

    @property
    def node_type(self):
        return self._node_type

    @node_type.setter
    def node_type(self, value):
        if isinstance(value, basestring):
            if value in NODES_SUFFIX:
                self._node_type = value
                self._suffix = NODES_SUFFIX[value]
                self._name_dict['suffix'] = self._suffix
            else:
                self._node_type = value

    @property
    def padding(self):
        return self._padding

    @padding.setter
    def padding(self, value):
        if isinstance(value, int):
            self._padding = value

    @property
    def last(self):
        return self._last

    @last.setter
    def last(self, value):
        if isinstance(value, bool):
            self._last = value
            if value:
                self._name_dict['suffix'] = 'END'

    def create(self, dictionary=None):
        if not dictionary:
            dictionary = self._name_dict
        name = '_'
        name_list = []
        if dictionary['side']:
            name_list.append(dictionary['side'])

        if dictionary['base_name']:
            name_list.append(dictionary['base_name'])

        if dictionary['base_index']:
            name_list.append(dictionary['base_index'])

        if dictionary['index']:
            name_list.append(dictionary['index'])

        if dictionary['tags']:
            tags_string = '_'.join(dictionary['tags'])
            name_list.append(tags_string)

        if dictionary['suffix']:
            name_list.append(dictionary['suffix'])

        return name.join(name_list)

    def replace(self, side='', base_name='', base_index='', tags=[], index=None, suffix='TMP', add_to_tags=[],
                add_to_suffix=''):
        replace_dict = copy.deepcopy(self._name_dict)

        if side:
            replace_dict['side'] = side
        if base_name:
            replace_dict['base_name'] = base_name
        if base_index:
            replace_dict['base_index'] = base_index
        if tags:
            if isinstance(tags, list):
                replace_dict['tags'] = tags
            elif isinstance(tags, basestring):
                replace_dict['tags'] = [tags]
        if index:
            replace_dict['index'] = self._generate_index(index)
        if suffix:
            replace_dict['suffix'] = suffix
        if add_to_tags:
            if isinstance(add_to_tags, list):
                replace_dict['tags'].extend(add_to_tags)
            elif isinstance(add_to_tags, basestring):
                replace_dict['tags'].append(add_to_tags)
        if add_to_suffix:
            replace_dict['suffix'].append(add_to_suffix)

        name = self.create(dictionary=replace_dict)
        return name

    def _initialize_name(self):
        name_elements = self._name.split('_')
        if len(name_elements) == 1:
            if self._base_name == '':
                self._base_name = name_elements[0]

        elif len(name_elements) == 2:
            if self._base_name == '':
                self._base_name = name_elements[0]
            if name_elements[0].isupper() and len(name_elements[0]) <= 3:
                if self._side == '':
                    self._side = name_elements[0]
            if name_elements[1].isupper():
                if self._suffix == '':
                    self._suffix = name_elements[1]
            if name_elements[1].isdigit():
                if not self._index:
                    self._index = name_elements[1]
            else:
                if self._base_name == '':
                    self._base_name = name_elements[1]

        elif len(name_elements) == 3:
            if self._base_name == '':
                self._base_name = name_elements[1]
            if name_elements[0].isupper() and len(name_elements[0]) <= 3:
                if self._side == '':
                    self._side = name_elements[0]
            if name_elements[2].isdigit():
                if not self._index:
                    self._index = name_elements[2]
            if name_elements[2].isupper():
                if self._suffix == '':

                    self._suffix = name_elements[2]
            else:
                self._tags.extend([name_elements[2]])

        elif len(name_elements) == 4:
            if self._base_name == '':
                self._base_name = name_elements[1]
            if name_elements[0].isupper() and len(name_elements[0]) <= 3:
                if self._side == '':
                    self._side = name_elements[0]
            if name_elements[2].isupper():
                if self._base_index == '':
                    self._base_index = name_elements[2]
            if name_elements[2].isdigit():
                if not self._index:
                    self._index = name_elements[2]
            if name_elements[3].isupper():
                if self._suffix == '':
                    self._suffix = name_elements[3]
            else:
                self._tags.extend([name_elements[2], name_elements[3]])

        elif len(name_elements) == 5:
            if self._base_name == '':
                self._base_name = name_elements[1]
            if name_elements[0].isupper() and len(name_elements[0]) <= 3:
                if self._side == '':
                    self._side = name_elements[0]
            if name_elements[2].isupper() or name_elements[2].isdigit():
                if self._base_index == '':
                    self._base_index = name_elements[2]
            if name_elements[3].isdigit():
                if not self._index:
                    self._index = name_elements[3]
            if name_elements[4].isupper():
                if self._suffix == '':
                    self._suffix = name_elements[4]
            else:
                self._tags.extend([name_elements[2], name_elements[3], name_elements[4]])

        elif len(name_elements) == 6:
            if self._base_name == '':
                self._base_name = name_elements[1]
            self._tags.append(name_elements[3])
            if name_elements[0].isupper() and len(name_elements[0]) <= 3:
                if self._side == '':
                    self._side = name_elements[0]
            if name_elements[2].isupper() or name_elements[2].isdigit():
                if self._base_index == '':
                    self._base_index = name_elements[2]
            if name_elements[4].isdigit():
                if not self._index:
                    self._index = name_elements[4]
            if name_elements[5].isupper():
                if self._suffix == '':
                    self._suffix = name_elements[5]
            else:
                self._tags.extend([name_elements[2], name_elements[3], name_elements[4], name_elements[5]])

    def _generate_index(self, index):
        if isinstance(index, int):
            return '{:0{}d}'.format(index, self._padding)
