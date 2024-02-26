import re

import maya.cmds as cmds

from rigging.utils.globals import NODES_SUFFIX, SIDE_SWITCH


# region CONSTANTS
namespace_RE = '(\S+:)?'
side_RE = '(_[lr][fmb]*[\d]*)?'
part_RE = '([A-Za-z][A-Za-z]+[a-z]+[0-9]*)?'
partindex_RE = '([A-Z]+)?'
index_RE = '(_\d+(?=_|$)|_end(?=_|$))?'
tags_RE = '(_[a-z0-9]*[a-zA-z0-9]*[a-z0-9]_+)*'
suffix_RE = '([_a-z]+[a-z])*'
splitname_RE = re.compile(part_RE + partindex_RE + index_RE + side_RE + tags_RE + suffix_RE)
shape_RE = re.compile('Shape\w*\Z')
camelcase_RE = re.compile('\D+([A-Z][a-z]+)')
unpad_RE = re.compile('[1-9]+0*|\D*', re.IGNORECASE)

componentindex_RE = re.compile('\d+')
enddigit_RE = re.compile('\w+\D+')

NONUNIQUE_SUFFIX = 'nonunique'

SYNTAX_LIST = ['namespace',
               'part',
               'partindex',
               'index',
               'side',
               'tags',
               'suffix'
               ]

SYNTAX_DICT = {'namespace': '{namespace}',
               'part': '{part}',
               'partindex': '{partindex}',
               'index': '_{index}',
               'side': '_{side}',
               'tags': '_{tags}',
               'suffix': '_{suffix}'
               }

SYNTAX_STYLE_DICT = {'namespace': 'camelcase',
                     'part': 'camelcase',
                     'partindex': 'upper',
                     'index': 'index',
                     'side': 'lower',
                     'tags': 'lower',
                     'suffix': 'suffix'
                     }

SYNTAX_SHORTNAME_DICT = {'ns': 'namespace',
                         'sd': 'side',
                         'pt': 'part',
                         'pid': 'partindex',
                         'id': 'index',
                         'sfx': 'suffix'}


# exceptions where the shape-name is not matching exactly the name of the transform
SHAPENAME_EXECPTION_DICT = {'curveInterp': ['cint'],
                            'locator': ['shared_ctrl', 'cnstShape', 'locShape'],
                            }


# endregion


class RigNameError(Exception):
    """ Mill's Rig-Error """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Name(object):
    """Base-class for all Naming-Convention based name-issues

    Args:
        name (str | None): The name that should be used/analysed
        namespace (str | None): The Namespace of the object
        side (str | None): Side of object.
        part(str | None): The main-element of the name.
        partindex(str | None): Alpha-Index for multiple occurences of an element
        index (int | str | None): Numeric index
        pad (int): padding for index
        tags (str | list[str] | None): single tag or List of tags
        suffix (str | None): Suffix of object (or objectType for type-based-suffix)
        add_to_tags (str | list[str] | None): add single tag or List of tags to existing tags
        add_to_suffix (str | list[str] | None): add to existing suffix
        unique (bool): check scene for existing name-conflicts
    """

    def __init__(self, name=None, namespace=None, side=None, part=None, partindex=None,
                 index=None, tags=None, suffix=None, add_to_tags=None, add_to_suffix=None,
                 pad=2, unique=False):

        # globals
        self._syntax_list = SYNTAX_LIST
        self._short_dict = SYNTAX_SHORTNAME_DICT
        self._splitname_RE = splitname_RE

        # init locals
        self._name = None
        self._shape_suffix = None
        self._namespace = namespace
        self._side = side
        self._part = part
        self._partindex = partindex
        self._index = index
        self._tags = tags
        self._suffix = self._spellcheck('suffix', suffix)
        self.padding = pad

        # self.init_dict = {item: None for item in self._syntax_list}

        self._unique = unique
        self._init_name(name)
        self._split_name()  # split name (init self._name if it is None)
        if add_to_tags:
            extra_tags = string_to_list(add_to_tags)
            if self._tags:
                self._tags.extend(extra_tags)
            else:
                self._tags = extra_tags
        if add_to_suffix:
            extra_suffix = self._spellcheck('suffix', add_to_suffix)
            if self._suffix:
                self._suffix += '_' + extra_suffix
            else:
                self._suffix = extra_suffix
        self._name = self.create_name(add_to_tags=add_to_tags,
                                      add_to_suffix=add_to_suffix)
        self._template = self._create_syntax_template()

    def __str__(self):
        """
        Returns string representation of the Name()
        """
        return self.create_name()

    # region PROPERTIES
    @property
    def name(self):
        return self.create_name()

    @property
    def shape_suffix(self):
        if self._shape_suffix is None:
            shp_suffix = shape_RE.findall(self._name)
            if shp_suffix:
                return shp_suffix[0]
        else:
            return self._shape_suffix

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        if namespace is None or namespace == ':':
            self._namespace = None
            return

        if not namespace.endswith(':'):
            namespace += ':'
        self._namespace = namespace

    @property
    def side(self):
        return self._side

    @side.setter
    def side(self, value):
        """Set side-property """
        value = self._check_input(value)
        if value is None:
            self._side = ''
        else:
            self._side = self._spellcheck('side', value)

    @property
    def part(self):
        # warning if <part> is capitalized
        return self._part

    @part.setter
    def part(self, value):
        """Set part-property """
        if value in [None, '', []]:
            self._part = None
        else:
            # last letter is capital >> it is partindex
            if value[-1].isupper():
                part = value[:-1]
                partindex = value[-1]
            else:
                part = value
                partindex = None

            self._part = part
            if partindex is not None:
                self._partindex = partindex

    @property
    def partindex(self):
        return self._partindex

    @partindex.setter
    def partindex(self, value):
        """Set partindex-property """
        self._partindex = value

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        """Set index-property """
        if value is not None:
            self._index = indexer(str(value), self.padding)

    @property
    def tags(self):
        return list_to_string(self._tags)

    @tags.setter
    def tags(self, value):
        """Set tags-property """
        self._tags = string_to_list(self._check_input(value))

    @property
    def suffix(self):
        suffix = self._suffix
        if suffix in [None, '', []]:
            self._suffix = 'tmp'
        return self._suffix

    @suffix.setter
    def suffix(self, value):
        """Set suffix-property """
        self._suffix = self._spellcheck('suffix', self._check_input(value))

    @property
    def basename(self):
        """returns basename consisting of side, part and partindex """
        basename = self.create_name(syntax_list=self._syntax_list[1:4])
        return basename

    @property
    def elem_dict(self):
        elem_dict = {}
        if self._namespace:
            elem_dict['namespace'] = self.namespace
        if self._side:
            elem_dict['side'] = self.side
        if self._part:
            elem_dict['part'] = self.part
        if self._partindex:
            elem_dict['partindex'] = self.partindex
        if self._index:
            elem_dict['index'] = self.index
        if self._tags:
            elem_dict['tags'] = self.tags
        if self._suffix:
            elem_dict['suffix'] = self.suffix
        return elem_dict

    # endregion

    # =========================================================================
    # Public Functions --------------------------------------------------------
    # =========================================================================

    def get(self, *args):
        """Returns elements of the name based on given keywords

        Args:
            *args (str): the keywords for the parts that are wanted

        Returns:
            str or [str]
        """
        # return list
        elem_dict = self.elem_dict
        if len(args) > 1:
            result_list = []
            for elem in args:
                result_list.append(elem_dict.get(elem))
            return result_list
        # or return single element
        else:
            return elem_dict.get(args[0])

    def create_name(self, syntax_list=None, elem_dict=None, unique=None, add_to_tags=None,
                    add_to_suffix=None):
        """ Creates a name based on the given element-dictonary and syntax-list

        Args:
            syntax_list (list[str] | None): List of element to create the name of in the right order
            elem_dict (dict | None): dictionary containing elements of the name
            unique (bool): check scene for existing name-conflicts
            add_to_tags (str | None): add tag to name
            add_to_suffix (str | None): add to suffix

        Returns:
            str: constructed name
        """
        # create unique name option can be set globally or locally
        if unique is None:
            unique = self._unique

        # make sure valid syntax_list exists
        syntax_list = syntax_list or self._syntax_list

        # elem_dict contains values for each part of the naming convention
        elem_dict = elem_dict or self.elem_dict

        if isinstance(elem_dict.get('tags'), list):
            elem_dict['tags'] = list_to_string(elem_dict['tags'])

        if add_to_tags:
            self.add_to_tags(add_to_tags, elem_dict=elem_dict)

        if add_to_suffix:
            self.add_to_suffix(add_to_suffix, elem_dict=elem_dict)

        if elem_dict.get('index'):
            elem_dict['index'] = indexer(elem_dict['index'], self.padding)

        template = self._create_syntax_template(syntax_list, elem_dict)
        name = template.format(**elem_dict)

        if elem_dict.get('suffix') is None:
            elem_dict['suffix'] = 'tmp'

        # this section checks the scene for duplicates of the name or duplicates
        # of the name including 'NONUNIQUE' plus any number.
        # It then generates an addition to the beginning of the suffix with the
        # amount of found name-conflicts.
        if unique is True:
            # if node with same name is found, add 'NONUNIQUE#' to tags
            number_found = len(cmds.ls(name))
            if number_found:
                # temporarily store the existing suffix-part to be able to recover
                # it after generating a 'NONUNIQUE#'-wildcard
                tmp = elem_dict.get('suffix')

                # create wildcard to serch for other nonunique ones
                elem_dict['suffix'] = '_'.join([NONUNIQUE_SUFFIX + '*', elem_dict.get('suffix')])
                wildcard_template = self._create_syntax_template(syntax_list, elem_dict)
                wildcard_name = wildcard_template.format(**elem_dict)
                # find nameconflicts and add them to the 'NONUNIQUE'-index
                number_found += len(cmds.ls(wildcard_name))

                # restore original suffix-part
                elem_dict['suffix'] = tmp

                # create new 'NONUNIQUE'-suffix
                nu_suffix = NONUNIQUE_SUFFIX + str(number_found)
                elem_dict['suffix'] = '_'.join([nu_suffix, elem_dict.get('suffix')])
                template = self._create_syntax_template(syntax_list, elem_dict)
                name = template.format(**elem_dict)
        return name

    def get_basename(self, namespace=True):
        """ creates a name-segment based on side, part and partindex

        Args:
            namespace (bool): if namespace exists, add it to the name
        """
        basename = self.create_name(syntax_list=self._syntax_list[1:4])
        if namespace is True:
            if self.namespace:
                basename = self.namespace + basename
        return basename

    def add_to_tags(self, value, elem_dict=None):
        """ add new tags to existing tags-list

        Args:
            value (str|list[str]): 1 or more tag-name, or tagname with underscores
            elem_dict (dict): dictionary containing elements of the name
        """
        elem_dict = elem_dict or self.elem_dict
        tags = elem_dict.get('tags')
        extra_tags = list_to_string(value)
        if tags:
            elem_dict['tags'] = tags + '_' + extra_tags
        else:
            elem_dict['tags'] = extra_tags

    def remove_from_tags(self, value, elem_dict=None):
        """ removes tags to existing tags-list

        Args:
            value(str|list[str]): 1 or more tag-name, or tagname with underscores
            elem_dict (dict): dictionary containing elements of the name
        """
        elem_dict = elem_dict or self.elem_dict
        tags = elem_dict.get('tags')
        if not tags:
            return
        tags = string_to_list(tags)
        remove_tags = string_to_list(value)
        for tag in remove_tags:
            if tag in tags:
                elem_dict['tags'].remove(tag)

    def add_to_suffix(self, value, elem_dict=None):
        """ add new Suffix-element to existing suffix

        Args:
            value(str|list[str]): 1 or more Suffices, or suffix with underscores
            elem_dict (dict): dictionary containing elements of the name
        """

        elem_dict = elem_dict or self.elem_dict
        suffix = elem_dict.get('suffix')
        extra_suffix = list_to_string(get_suffix_by_nodetype(value))
        if suffix:
            elem_dict['suffix'] = suffix + '_' + extra_suffix
        else:
            elem_dict['suffix'] = extra_suffix

    def flip(self):
        """ generates the mirror-name of the name if possible, else returns the
        original name

        Returns:
            name with flipped side (L <> R)
        """
        if self.side:
            side = SIDE_SWITCH[self.side[0]] + self.side[1:]
            return self.replace(side=side)
        else:
            cmds.warning('Element has no side!')
            return self.name

    def replace(self, syntax_list=None, spellcheck=True, add_to_tags=None,
                add_to_suffix=None, unique=None, pad=None, **kwargs):

        """replaces elements of the name by keyword-argument.
        If *None* is given as value, the element of the name will be removed
        Possible keywords are side, part, partindex, index, tags, suffix


        Names follow this naming-convention:
        *<namespace>:<side>_<part><partindex>_<index>_<tags>_<suffix>*

        Example:
            *L_armB_01_upper_fk_CTRL_OFS*
            Important: 'END' is also recognised as an index and can't be used
            as suffix.
            The format of the elements will also be checked and if neccessary
            fixed before returning the name

        Important: side and part are not optional and need to exist in any name

        Args:
            side (str|None): Side of object.
            part (str|None): The main-element of the name.
            partindex (str|None: Alpha-Index for multiple occurences of an element
            index (int|str|None): Numeric index
            tags (list[str]|None): List of tags
            suffix (str|None): Suffix of object
            pad (int|None): padding for index
            add_to_tags (str|list[str]|None): additional tags
            add_to_suffix (str|None): attachment to existing suffix
            syntax_list (list[str]): Ordered list of elements to create the name from
            spellcheck (bool): Check and fix the format of the given elements
            unique (bool): check scene for existing name-conflicts >> add 'duplicate'-tag

        Returns:
            str: new composed name
        """
        # if no syntax_list is provided use a copy of the standard full list
        syntax_list = syntax_list or self._syntax_list[:]

        # use a duplicate of the elem_dict as it might be manipulated
        elem_dict = self.elem_dict

        for key in kwargs:
            if key in syntax_list:

                if key == 'tags':
                    # format tags to work properly with Name-class
                    elem_dict['tags'] = list_to_string(kwargs.get(key))

                elif key == 'suffix':
                    # deal with descriptive suffices like 'matrixBlend'
                    elem_dict['suffix'] = get_suffix_by_nodetype(kwargs.get(key))

                else:
                    elem_dict[key] = kwargs.get(key)

        # 'add_to_tags' adds on tag or a list of tags to the existing tags
        if add_to_tags:
            self.add_to_tags(add_to_tags, elem_dict)

        # 'add_to_suffix' attached extra element to the suffix
        if add_to_suffix:
            self.add_to_suffix(add_to_suffix, elem_dict)

        if spellcheck:
            for item in elem_dict.keys():
                # check and fix the format of the element
                elem_dict[item] = self._spellcheck(item, elem_dict[item])

        if pad:
            index_value = elem_dict.get('index')
            if index_value:
                elem_dict['index'] = indexer(index_value, padding=pad)

        return self.create_name(syntax_list, elem_dict, unique)

    def wildcard(self, *args):
        """ replaces elements of the name by wildcard-letters '?' and '*'.
        Possible elements are 'side', 'part', 'partindex', 'index', 'tags', 'suffix'

        Args:
            *args (str): argument list of elements to insert wildcards in the name
        """

        elem_dict = self.elem_dict

        for item in args:
            if item == 'index':
                elem_dict['index'] = '?' * self.padding
            elif item == 'partindex':
                elem_dict['partindex'] = '?'
            elif item == 'namespace':
                elem_dict['namespace'] = '*:'
            else:
                elem_dict[item] = '*'

        template = self._create_syntax_template(elem_dict=elem_dict)
        return template.format(**elem_dict)

    def pprint(self):
        """ prints the splited elements of the name """
        for elem in self._syntax_list:
            print ('{0} : {1}'.format(elem, self.elem_dict.get(elem)))

    # region NON PUBLIC
    def _split_name(self):
        """
        uses a regex to filter out the components of a typical name
        <namespace>:<side>_<part><partindex>_<index>_<tags>_<suffix>
        """

        # no name was given, just parts of the name
        if self._name is None:
            self._name = self.get_basename(namespace=False)

        r = self._splitname_RE.search(self._name)
        result_list = list(r.groups())
        # special case 'END' in index
        if result_list[5] == '_end' and not self._suffix:
            raise RigNameError('end is not a valid Suffix!')

        found_dict = {item: None for item in self._syntax_list}
        for key, value in zip(self._syntax_list[1:], result_list):
            # if value is not None and the elem_dict is not yet set by overrides...
            if value is not None:
                value = value.strip('_')
                found_dict[key] = value

        # mix up the dicts:
        elem_dict = self.elem_dict
        for key in self._syntax_list:
            value = elem_dict.get(key, found_dict.get(key))
            self._set_values(key, value)

    def _create_syntax_template(self, syntax_list=None, elem_dict=None):
        """ creates a template string based on the given element-dictonary
        and syntax-list"""
        elem_dict = elem_dict or self.elem_dict
        syntax_list = syntax_list or self._syntax_list
        return ''.join([SYNTAX_DICT[elem] for elem in syntax_list
                        if elem_dict.get(elem) is not None])

    def _spellcheck(self, elem=None, value=None):
        """ Double-check and fix the spelling """
        if elem is not None and value is not None:
            if elem == 'tags':
                pass
            elif elem == 'suffix':
                value = get_suffix_by_nodetype(value).lower()
            else:
                value = namestyle(value,
                                  style=SYNTAX_STYLE_DICT[elem],
                                  padding=self.padding)
        return value

    def _set_values(self, key, value):
        # read out the keyword arguments and assign them through the property-filter
        if key in SYNTAX_STYLE_DICT:
            value = self._spellcheck(elem=key, value=value)
        if key == 'namespace':
            self.namespace = value
        elif key == 'side':
            self.side = value
        elif key == 'part':
            self.part = value
        elif key == 'partindex':
            self.partindex = value
        elif key == 'index':
            self.index = value
        elif key == 'tags':
            self.tags = value
        elif key == 'suffix':
            self.suffix = value

    def _init_name(self, name):
        """
        initialize the name by splitting namespace and finding the shortname
        """
        if name is None:
            return

        # look for namespace
        namespace, name = get_namespace(name, empty=None)
        if self._namespace is None:
            self._namespace = namespace

        # get shortname
        name = get_shortname(name)

        # split shapesuffix from suffix
        name, self._shape_suffix = get_shapesuffix(name)

        # split suffix for NONUNIQUE
        self._name = '_'.join([s for s in name.split('_') if not s.startswith(NONUNIQUE_SUFFIX)])

    def _check_input(self, value):
        # filter out results that could be problematic to deal with and replace them
        if value in ['', []]:
            return None
        else:
            return value
    # endregion


# region NON-PUBLIC FUNCTIONS
def _get_objecttype(node, software='maya', **kwargs):
    """
    to make it easier to implement the nameclass into a different system
    the objectType function is isolated.

    Args:
        node (str): node to be analyzed
        software (str): software used

    Returns:
        str: nodeType
    """
    if software == 'maya':
        return cmds.objectType(node, **kwargs)
# endregion


# region PUBLIC FUNCTIONS
def get_namespace(name, empty=''):
    """ returns namespace and name as list

    Args:
        name (str): name to be analyzed
        empty (str|None): if no namespace, what should be used as a placeholder for the namespace.
            Normally it is either '' or ':'

    Returns:
        tuple(str, str) : namespace, name
    """
    namespace = name.rsplit(':', 1)
    if len(namespace) > 1:
        if namespace[0] == '':
            ns = empty
        else:
            ns = namespace[0] + ':'
        name = namespace[1]
    else:
        ns = empty
    return ns, name


def get_shortname(name):
    """returns shortname

    Args:
        name: name of a node

    Returns:
        str: shortname
    """
    shortname = name.rsplit('|', 1)
    if len(shortname) > 1:  # split was successful
        name = shortname[1]
    return name


def get_shapesuffix(name):
    """returns name and shape-suffix as list

    Args:
        name: name of a node

    Returns:
        tuple(str, str): name, suffix of the shapeNode, usually 'Shape' or 'ShapeOrig'
    """
    # split shapesuffix from suffix
    found = shape_RE.findall(name)
    if found:
        shape_suffix = found[0]
        name = name.replace(shape_suffix, '')
    else:
        shape_suffix = ''
    return name, shape_suffix


def get_namespacelist():
    """ collect and sort all useful namespaces

    Returns:
        tuple(str, str): name, suffix of the shapeNode, usually 'Shape' or 'ShapeOrig'
    """
    cmds.namespace(set=':')
    namespace_list = ['{0}:'.format(ns) for ns in cmds.namespaceInfo(lon=True)
                     if ns not in ('UI', 'shared')]
    namespace_list.append(':')
    namespace_list.sort()
    return namespace_list


def remove_namespace(name, dest=':'):
    """ moves content of name to destination and removes name"""
    if name == ':':
        print (" -- can't remove world-namespace --")
    else:
        cmds.namespace(set=dest)
        cmds.namespace(f=True, mv=(name, dest))
        cmds.namespace(rm=name)


def get_suffixlist(obj_list):
    """little helperfunction to list all found suffixes of a selection

    Args:
        obj_list (list[str]): list of nodes
    """
    suffix_set = set()
    for obj in obj_list:
        try:
            sfx = obj.rsplit('_', 1)[1]
            suffix_set.add(sfx)
        except:
            pass
    for obj in suffix_set:
        print( obj )


def create_abc_dict(item_list):
    """ Creates a dictionary where elements are grouped alphabetical
    by their first letter

    Args:
        item_list (list[str]): List of names

    Returns:
        dict: sorted dictionary based on the first letters of the itemlist
    """
    abc_dict = {}
    abc_list = sorted(list(set([item[0].upper() for item in item_list])))

    for abc in abc_list:
        collect_list = sorted([item for item in item_list
                               if item[0].upper() == abc])
        abc_dict.setdefault(abc, collect_list)

    return abc_dict


def camelcase(name, cap=False):
    """ camelCase a str of elements connected by underscore

    Args:
        name (str): Name
        cap (bool): capitalize result if True

    Returns:
        str

    .. note::

        This_is_an_example >> thisIsAnExample
    """

    if '_' in name:
        split_list = name.lower().split('_')
        if len(split_list) > 1:
            for i, item in enumerate(split_list):
                if i > 0:
                    split_list[i] = item.capitalize()
                name = ''.join(split_list)

    if name.isupper():
        name = name.lower()

    if cap:
        return name[0].upper() + name[1:]
    else:
        return name[0].lower() + name[1:]


def indexer(name, padding=2):
    """ format name according index-guidelines (accepts 'END' as index)

    Args:
        name (str): Name
        padding (int): amount of leading zeros

    Returns:
        str
    """

    if name == 'end':
        return name
    elif name == '*':
        return name
    else:
        return pad(unpad(name), padding)


def namestyle(name, style=None, padding=3):
    """ format name according to style

    Args:
        name (str): Name
        style (str): Styles available: *UPPER, lower, camelCase, Capitalize*
        padding (int): leading zeros

    Returns:
        str
    """
    if style == 'upper':
        return name.upper()
    elif style == 'lower':
        return name.lower()
    elif style == 'camelcase':
        return camelcase(name)
    elif style == 'capitalize':
        return camelcase(name, cap=True)
    elif style == 'index':
        return indexer(name, padding)
    elif style == 'suffix':
        suffix = name.lower()
        if suffix.endswith('SHAPE'):
            suffix = suffix[:-5] + 'Shape'
        return suffix
    else:
        return name


def unpad(name):
    """Removes padding from index

    Args:
        name: amy name

    Returns:
        str
    """
    if name is not None:
        regex = unpad_RE
        match_list = regex.findall(str(name))
        return ''.join(match_list)


def pad(index, padding=2):
    """Add padding to number
    Args:
        index (str): any index
        padding (int): amount of padding

    Returns:
        str
    """
    return index.zfill(padding)


def get_typesuffix(node):
    """ Creates a suffix based on the object-type by using predefined names """
    obj_type = _get_objecttype(node)
    return NODES_SUFFIX[obj_type]


def get_index(name):
    """ extracts the integer index of a given component-string """
    index = name.split('[', 1)[-1]
    index = index.rsplit(']', 1)[0]
    return int(index)


def remove_enddigits(name):
    """ removes any digit found at the end of a string """
    regex = enddigit_RE
    try:
        name = name.rsplit('|', 1)[1]
    except IndexError:
        pass

    new_name = regex.findall(name)[0]
    return new_name


def fix_shapenames(obj):
    """ Fixes the name of any shape-node based on it's transform-name """
    node = None
    shp_list = []
    # sort out transforms and shapes
    if cmds.objectType(obj) in ('transform', 'joint'):
        node = obj
        shp_list = get_shapes(obj)
    else:
        shp_list.append(obj)
        node = get_parent(obj)

    # filter out instances

    shp_list[:] = [shp for shp in shp_list]

    namer = Name(node)
    if len(shp_list) == 1:  # if only one shape exists
        shp_name = namer.create_name() + 'Shape'
        print ('{0} >> {1}'.format(shp_list[0], shp_name))
        cmds.rename(shp_list[0], shp_name)

    else:
        for shp in shp_list:  # if several shapenodes exist, rename by type
            if namer.suffix == 'ctrl' and cmds.objectType(shp) == 'nurbsCurve':
                shp_name = namer.replace(suffix='ctrlShape')
            else:
                shp_name = namer.replace(suffix=get_typesuffix(shp) + 'Shape')
            cmds.rename(shp, shp_name)


def get_component(name):
    """ splits name into name and component-element """
    if '.' in name:
        i = name.index('.')
        return name[:i], name[i:]
    else:
        return name, ''


def remove_last_element(name):
    """ removes last element of a camelCase-Name """
    r = camelcase_RE.search(name)
    last_element = list(r.groups())[-1]
    return name.replace(last_element, '')


def split_last_element(name):
    """ splits last element of a camelCase-Name and returns the splitted parts"""
    r = camelcase_RE.search(name)
    last_element = list(r.groups())[-1]
    return name.replace(last_element, ''), last_element


def get_suffix_by_nodetype(node):
    """ get the suffix by nodetype """
    suffix = NODES_SUFFIX.get(node, node)
    return suffix


def get_mirrorname(name):
    """ replace the side if possible """
    ns, name = get_namespace(name)
    short_name = get_shortname(name)
    return '{0}{1}{2}'.format(ns, SIDE_SWITCH[short_name[0]], short_name[1:])


def mirror_partindex_generator(amount=3):
    """ create a tring like 'ABCDDCBA' for even or 'DCBABCD' for odd numbers """
    num = amount // 2
    offset = amount % 2
    indices = ''.join([chr(65 + i) for i in range(num)])
    result = '{0}{1}{2}'.format(indices, offset * chr(65 + num), indices[::-1])
    return result


def mirror_side_generator(amount=3):
    """ create a string like 'LLLRRR' for even or 'LLLCRRR' for odd numbers """
    num = amount // 2
    offset = amount % 2
    result = '{0}{1}{2}'.format(num * 'L', offset * 'C', num * 'R')
    return result


def string_to_list(value):
    """ filter tags input and return list """
    # value is single string
    if isinstance(value, str):
        # create list if underscores are found in string
        value = [item for item in value.split('_') if item != '']
        return value
    # value is list >> return list without None-values
    elif isinstance(value, list):
        value = [item for item in value if item is not None]
        if value is []:
            value = None
        return value


def list_to_string(value):
    """ filter tags input and return list """
    # value is single string
    if isinstance(value, str):
        return value
    # value is list >> return list without None-values
    elif isinstance(value, list):
        value = [item for item in value if item is not None]
        if value is []:
            return None
        return '_'.join(value)
# endregion


# region WRAPPER FUNCTIONS FOR NAME CLASS
def create_name(**kwargs):
    """ creates a name based on the given element-dictonary and syntax-list.
        *(Uses the Name-Class)*
    """
    return Name(**kwargs).create_name()


def replace(name, **kwargs):
    """ replaces name-elements by keyword-argument.
        *(Uses the Name-Class)*
    """
    return Name(name).replace(**kwargs)


def create_chain_names(count, startindex=1, last_is_end=False, force_index=True, **kwargs):
    """creates a chain of names

    Args:
        count (int | list[str]): length of chain or list of tags
        startindex (int): Start chain index
        last_is_end (bool): if True, last element of chain will get the index 'END'
        force_index (bool): create index even if length of chain is only 1
        **kwargs: pass through attributes to NameClass

    Returns:
        list[str]: list of chain-names
    """

    add_to_tags = kwargs.get('add_to_tags')
    if add_to_tags:
        del kwargs['add_to_tags']
    namer = Name(**kwargs)
    out = []

    # if a list of tags is given, use them
    if isinstance(count, list):
        # make sure the new tags are set before the existing ones
        existing_tags = namer.tags
        if existing_tags:
            existing_tags = '_' + existing_tags
        else:
            existing_tags = ''
        for tag in count:
            tags = '{0}{1}'.format(tag, existing_tags)
            out.append(namer.replace(tags=tags, add_to_tags=add_to_tags))

    # otherwise use the length
    elif isinstance(count, int):
        if count == 1:
            if force_index is True:
                out.append(namer.replace(index=1, add_to_tags=add_to_tags))
            else:
                out.append(namer.replace(add_to_tags=add_to_tags))
        else:
            index_list = range(startindex, count + startindex)

            # add all the numbers
            for index in index_list:
                out.append(namer.replace(index=index, add_to_tags=add_to_tags))
    else:
        raise ValueError("value must be of type list or int!")

    # replace the last one if needed
    if last_is_end:
        index = 'end'
        out[-1] = namer.replace(index=index, add_to_tags=add_to_tags)
    return out


def get_parent(dag_node, **kwargs):
    parent = cmds.listRelatives(dag_node, parent=True, **kwargs)
    if parent:
        return parent[0]
        

def get_shapes(dag_node, **kwargs):
    return cmds.listRelatives(dag_node, shapes=True, **kwargs)
# endregion