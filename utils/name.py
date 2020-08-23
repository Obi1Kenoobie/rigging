import copy
import re

from rigging.utils.globals import SIDES_LIST, NODES_SUFFIX


namespace_RE = '(\S+:)?'
side_RE = '([CLR][FMB]*[\d]*_)?'
part_RE = '([A-Za-z][A-Za-z]+[a-z]+[0-9]*)?'
part_index_RE = '([A-Z]+)?'
index_RE = '(_\d+(?=_)|_END(?=_))?'
tags_RE = '(_[a-z0-9]*[a-zA-Z0-9]*[a-z0-9_]+)*'
suffix_RE = '([_A-Z]+[A-Z])*'

RE_compile = re.compile(namespace_RE + side_RE + part_RE + part_index_RE + index_RE + tags_RE + suffix_RE)

NAME_COMPONENTS_LIST = ['namespace', 'side', 'part', 'part_index', 'index', 'tags', 'suffix']


class Name(object):
    """Name object used for the creation and query of names
    """

    def __init__(self, name, namespace=None, side=None, part=None, part_index=None, tags=[], index=None, suffix=None,
                 padding=2, last=False, node_type=None):
        self._name = name
        self.name_RE = RE_compile.search(self._name)
        self._namespace = namespace
        self._side = side
        self._part = part
        self._part_index = part_index
        self._tags = tags
        self._index = index
        self._suffix = suffix
        self._padding = padding
        self._last = last
        self._node_type = node_type
        
        self._initialize_name()

        if self._last:
            self._suffix = 'END'

        if self._node_type in NODES_SUFFIX and self._suffix == None:
            self._suffix = NODES_SUFFIX[self._node_type]


        self._name_dict = {'namespace': self._namespace,
                           'side': self._side,
                           'part': self._part,
                           'part_index': self._part_index,
                           'index': self._index,
                           'tags': self._tags,
                           'suffix': self._suffix}

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if isinstance(value, basestring):
            self._name = value

    @property
    def namespace(self):
        return self._name

    @namespace.setter
    def namespace(self, value):
        if isinstance(value, basestring):
            self._namespace = value

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
    def part(self):
        return self._part

    @part.setter
    def part(self, value):
        if isinstance(value, basestring):
            self._part = value
        self._name_dict['part'] = self._part

    @property
    def part_index(self):
        return self._part_index

    @part_index.setter
    def part_index(self, value):
        if isinstance(value, basestring):
            self._part_index = value.upper()
        elif isinstance(value, int):
            self._part_index = self._generate_index(value)
        self._name_dict['part_index'] = self._part_index

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        if isinstance(value, int):
            self._index = self._generate_index(value)
        self._name_dict['index'] = self._index

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

        if dictionary['part']:
            name_list.append(dictionary['part'])

        if dictionary['part_index']:
            name_list.append(dictionary['part_index'])

        if dictionary['index']:
            name_list.append(dictionary['index'])

        if dictionary['tags']:
            tags_string = '_'.join(dictionary['tags'])
            name_list.append(tags_string)

        if dictionary['suffix']:
            if isinstance(dictionary['suffix'], list):
                suffix_string = '_'.join(dictionary['suffix'])
                name_list.append(suffix_string)
            else:
                name_list.append(dictionary['suffix'])

        name = name.join(name_list)
        
        if dictionary['namespace']:
            name = dictionary['namespace'] + ':' + name

        return name 

    def replace(self, namespace=None, side=None, part=None, part_index=None, tags=[], index=None, suffix=[],
                add_to_tags=None, add_to_suffix=None):
        replace_dict = copy.deepcopy(self._name_dict)
        if namespace:
            replace_dict['namespace'] = namespace
        if side:
            replace_dict['side'] = side
        if part:
            replace_dict['part'] = part
        if part_index:
            replace_dict['part_index'] = part_index
        if tags:
            if isinstance(tags, list):
                replace_dict['tags'] = tags
            elif isinstance(tags, basestring):
                replace_dict['tags'] = [tags]
        if index:
            replace_dict['index'] = self._generate_index(index)
        if suffix:
            replace_dict['suffix'] = [suffix]
        if add_to_tags:
            if isinstance(add_to_tags, list):
                if replace_dict['tags']:
                    replace_dict['tags'].extend(add_to_tags)
                else:
                    replace_dict['tags'] = add_to_tags
            elif isinstance(add_to_tags, basestring):
                replace_dict['tags'].append(add_to_tags)
        if add_to_suffix:
            if isinstance(replace_dict['suffix'], list):
                replace_dict['suffix'].append(add_to_suffix)
            else:
                list(replace_dict['suffix']).append(add_to_suffix)
        name = self.create(dictionary=replace_dict)
        return name

    def _initialize_name(self):
        parsed_components = [component.strip('_') if component else component for component in self.name_RE.groups()]
        parsed_dict = dict(zip(NAME_COMPONENTS_LIST, parsed_components))
        if not self._namespace:
            self._namespace = parsed_dict['namespace']
        if not self.side:
            self._side = parsed_dict['side']
        if not self._part:
            self._part = parsed_dict['part']
        if not self._part_index:
            self._part_index = parsed_dict['part_index']
        if not self._index:
            self._index = parsed_dict['index']
        if not self._tags:
            parsed_tags = parsed_dict['tags']
            if parsed_tags and '_' in parsed_tags:
                parsed_tags = filter(None, parsed_tags.split('_'))
            self._tags = parsed_tags
        if not self._suffix:
            parsed_suffix = parsed_dict['suffix']
            if parsed_suffix and '_' in parsed_suffix:
                parsed_suffix = filter(None, parsed_suffix.split('_'))
            self._suffix = parsed_suffix

    def _generate_index(self, index):
        if isinstance(index, int):
            return '{:0{}d}'.format(index, self._padding)


def generate_name_list(name_object, num):
    return [name_object.replace(index=i+1) for i in range(0, num)]