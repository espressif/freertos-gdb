# SPDX-FileCopyrightText: 2022 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=import-error
import gdb
from .common import StructProperty, FreeRtosList, print_table


class TimerProperty(StructProperty):
    TIMER_ID = ('An ID to identify the timer.', 'pvTimerID', 'get_val')
    NAME = ('', 'pcTimerName', 'get_string_val')
    NUMBER = ('Timer number', 'uxTimerNumber', 'get_val')
    OVERFLOW = ('True if timer has been overflow', '', 'get_empty_val')
    PERIOD_IN_TICKS = ('How quickly and often the timer expires.', 'xTimerPeriodInTicks', 'get_val')
    STATUS = ('Holds bits to say if the timer was statically allocated or not, and if it is active or not.',
              'ucStatus', 'get_val')
    CALLBACK_FN = ('', 'pxCallbackFunction', 'get_val')


class Timers:
    def __init__(self):
        try:
            self._current = gdb.parse_and_eval('xActiveTimerList1')
            self._overflow = gdb.parse_and_eval('xActiveTimerList2')
            self._timer_struct = gdb.lookup_type('Timer_t')
        except gdb.error as err:
            raise err

    def show(self):
        table = []

        # extend table with current timers
        rows = self.get_timer_list_table(self._current)
        table.extend(rows)

        # extend table with overflow timers
        rows = self.get_timer_list_table(self._overflow)
        table.extend(rows)

        if len(table) == 0:
            return

        # print the table
        self.print_help()
        print_table(table, self.get_table_headers())

    def get_timer_list_table(self, lst):
        table = []
        rtos_list = FreeRtosList(lst, 'Timer_t')
        for _, timer_ptr in enumerate(rtos_list):
            row = self.get_table_row(timer_ptr, lst == self._overflow)
            table.append(row)
        return table

    def get_table_headers(self):
        return [item.title for _, item in enumerate(TimerProperty) if item.exist(self._timer_struct)]

    def print_help(self):
        for _, item in enumerate(TimerProperty):
            item.print_property_help(self._timer_struct)
        print('')

    @staticmethod
    def get_table_row(timer_ptr, overflow):
        row = []
        timer = timer_ptr.dereference()
        for _, item in enumerate(TimerProperty):
            if item == TimerProperty.OVERFLOW:
                row.append(int(overflow))
                continue

            if not item.exist(timer.type.target()):
                continue

            row.append(item.value_str(timer))
        return row


class FreeRtosTimer(gdb.Command):
    """ Generate a print out of the current timers info.
    """

    def __init__(self):
        super().__init__('freertos timer', gdb.COMMAND_USER)

    @staticmethod
    def invoke(_, __):
        try:
            Timers().show()
        except gdb.error as err:
            print(err)
