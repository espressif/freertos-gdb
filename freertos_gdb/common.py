# SPDX-FileCopyrightText: 2022 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=import-error
import gdb
import enum


class StructProperty(enum.Enum):
    """Class describes struct fields to print
    :param help_: Description of property. Not shown if empty
    :type help_: str
    :param property_: Name of structure's field to grab the value.
    :type property_: str
    :param get_val_fn: Method to grab a value using object and self.property_
    :type get_val_fn: str
    """

    def __init__(self, help_, property_, get_val_fn):
        self._help = help_
        self.property = property_
        self.get_val_fn = get_val_fn

    @property
    def title(self):
        return self.name

    def value_str(self, obj):
        val_fn = getattr(self, self.get_val_fn if obj else 'get_empty_val')
        return str(val_fn(obj))

    def exist(self, struct):
        if self.property == '':
            return True
        return any(item.name == self.property for _, item in enumerate(struct.fields()))

    def print_property_help(self, struct):
        if not self.exist(struct):
            return
        if self._help == '':
            return
        print(self.title + '\t - ' + self._help)

    def get_val(self, obj):
        if obj is None:
            return ''
        if self.property == '':
            return ''
        try:
            type_code = obj[self.property].type.strip_typedefs().code
            # convert gdb.value to int to avoid gdb default printing
            # https://sourceware.org/gdb/onlinedocs/gdb/Output-Formats.html
            if type_code == gdb.TYPE_CODE_INT:
                val = int(obj[self.property])
            else:
                val = obj[self.property]
        except (ValueError, gdb.error):
            val = 'N/A?'
        return val

    @staticmethod
    def get_val_as_is(val):
        return val or ''

    @staticmethod
    def get_empty_val(_):
        return ''

    def get_string_val(self, obj):
        if obj is None:
            return ''
        try:
            name = obj[self.property].string()
        except ValueError:
            name = 'N/A?'
        return name


def print_table(table, headers=None):
    if headers:
        table.insert(0, headers)

    max_column = [0] * len(table[0])
    for _, row in enumerate(table):
        for k, _ in enumerate(max_column):
            max_column[k] = max(len(str(row[k])), max_column[k])

    # print formatted
    for i, row in enumerate(table):
        # print row
        for k, _ in enumerate(max_column):
            print(str(row[k]).rjust(max_column[k]), end=' ')
        print(end='\n')
        # print header separator
        if headers and i == 0:
            header_separator = ' '.join([''.rjust(max_column[i], '-') for i in range(len(max_column))])
            print(header_separator)


class FreeRtosList():
    """Enumerator for an freertos list (ListItem_t)

    :param list_: List to enumerate
    :param cast_type_str: Type name to cast list items as
    :param check_length: If True check uxNumberOfItems to stop iteration. By default check for reaching xListEnd.
    """

    def __init__(self, list_, cast_type_str, check_length: bool = False):
        self.cast_type = gdb.lookup_type(cast_type_str).pointer()
        self.end_marker = list_['xListEnd']
        self.head = self.end_marker['pxNext']  # ptr to start item
        self._length = list_['uxNumberOfItems']
        self.check_length = check_length

    @property
    def length(self):
        return self._length

    def __getitem__(self, idx):
        for i, item in enumerate(self):
            if i == idx:
                return item
        return None

    def __iter__(self):
        curr_node = self.head
        index = 0
        while True:
            if curr_node == self.end_marker.address:
                break
            if self.check_length and index >= self._length:
                break
            tmp_node = curr_node.dereference()
            data = tmp_node['pvOwner'].cast(self.cast_type)
            yield data
            index += 1
            curr_node = tmp_node['pxNext']


class FreeRtos(gdb.Command):
    def __init__(self):
        super().__init__('freertos', gdb.COMMAND_USER, gdb.COMPLETE_NONE, True)
