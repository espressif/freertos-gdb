# SPDX-FileCopyrightText: 2022 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=import-error
import gdb
import enum
from .common import StructProperty, FreeRtosList, print_table


class TaskLists(enum.Enum):
    READY = 'pxReadyTasksLists'
    PEND_READ = 'xPendingReadyList'
    SUSPENDED = 'xSuspendedTaskList'
    DELAYED_1 = 'xDelayedTaskList1'
    DELAYED_2 = 'xDelayedTaskList2'
    WAIT_TERM = 'xTasksWaitingTermination'

    def __init__(self, symbol):
        self.symbol = symbol

    @property
    def state(self):
        return self.name.lower()


class TaskProperty(StructProperty):
    CPU = ('Processing on CPU number', '', 'get_val_as_is')
    ID = ('TCB_t task memory address', '', 'get_val_as_is')
    TCB_NUM = ('Number that increments each time a TCB is created', 'uxTCBNumber', 'get_val')
    NAME = ('', 'pcTaskName', 'get_string_val')
    STATUS = ('', '', 'get_val_as_is')
    PRI = ('Task priority', 'uxPriority', 'get_val')
    B_PRI = ('Base priority.', 'uxPriority', 'get_val')
    MUTEXES_HELD = ('', 'uxMutexesHeld', 'get_val')
    SS = ('Used stack size.', 'pxEndOfStack', 'get_ss_val')
    SL = ('Free/unused stack size.', 'pxTopOfStack', 'get_sl_val')
    RTC = ('Stores the amount of time the task has spent in the Running state.', 'ulRunTimeCounter', 'get_val')

    def get_ss_val(self, task):
        return abs(int(task[self.property]) - int(task['pxTopOfStack']))

    def get_sl_val(self, task):
        return abs(int(task['pxStack']) - int(task['pxTopOfStack']))


def get_current_tcbs():
    current_tcb_arr = []
    try:
        current_tcb = gdb.parse_and_eval('pxCurrentTCB')
    except gdb.error as err:
        try:
            current_tcb = gdb.parse_and_eval('pxCurrentTCBs')
        except gdb.error as err:
            print(err, end='\n\n')
            return current_tcb_arr

    if current_tcb.type.code == gdb.TYPE_CODE_ARRAY:
        r = current_tcb.type.range()
        for idx in range(r[0], r[1] + 1):
            current_tcb_arr.append(current_tcb[idx])
    else:
        current_tcb_arr.append(current_tcb)
    return current_tcb_arr


def print_help(tcb_struct):
    for _, item in enumerate(TaskProperty):
        item.print_property_help(tcb_struct)
    print('')


def get_table_row(task_ptr, state, current_tcbs):
    row = []
    task = task_ptr.referenced_value()
    fields = task_ptr.type.target()
    try:
        cpu_id = current_tcbs.index(task_ptr)
        cpu_id_str = 'CPU' + str(cpu_id)
    except ValueError:
        cpu_id_str = ''

    for _, item in enumerate(TaskProperty):
        val = task
        if item is TaskProperty.STATUS:
            val = state

        if item is TaskProperty.CPU:
            val = cpu_id_str

        if item is TaskProperty.ID:
            val = task_ptr

        if not item.exist(fields):
            continue

        row.append(item.value_str(val))
    return row


def get_table_rows(list_, state, current_tcbs):
    table = []
    rtos_list = FreeRtosList(list_, 'TCB_t', check_length=True)
    for _, task_ptr in enumerate(rtos_list):
        if task_ptr == 0:
            print('SEEMS STACK WAS CORRUPTED. TASK POINTER IS NULL.')
        row = get_table_row(task_ptr, state, current_tcbs)
        table.append(row)
    return table


def get_table_headers(tcb_type):
    row = []
    for _, item in enumerate(TaskProperty):
        if not item.exist(tcb_type):
            continue
        row.append(item.title)
    return row


def show():
    table = []
    current_tcbs = get_current_tcbs()

    for _, tl in enumerate(TaskLists):
        try:
            tl_value = gdb.parse_and_eval(tl.symbol)
        except gdb.error as err:
            print(err)
            continue

        if tl_value.type.code == gdb.TYPE_CODE_ARRAY:
            r = tl_value.type.range()
            for idx in range(r[0], r[1] + 1):
                table_rows = get_table_rows(tl_value[idx], tl.state, current_tcbs)
                table.extend(table_rows)
        else:
            table_rows = get_table_rows(tl_value, tl.state, current_tcbs)
            table.extend(table_rows)
    if len(table) == 0:
        return
    tcb_type = gdb.lookup_type('TCB_t')
    print_help(tcb_type)
    print_table(table, get_table_headers(tcb_type))


class FreeRtosTask(gdb.Command):
    """ Generate a print out of the current tasks and their states.
    """

    def __init__(self):
        super().__init__('freertos task', gdb.COMMAND_USER)

    @staticmethod
    def invoke(_, __):
        show()
