# SPDX-FileCopyrightText: 2022 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=import-error
import gdb
from .common import StructProperty, FreeRtosList, print_table
from .task import TaskProperty


class QueueProperty(StructProperty):
    NAME = ('', '', '')
    COUNT = ('Number of items currently in the queue.', 'uxMessagesWaiting', 'get_val')
    I_LEN = ('Length of the queue (number of items could hold, not the number of bytes).', 'uxLength', 'get_val')
    # queue property, always 0 for semaphores
    I_SIZE = ('Size of each item that the queue will hold.', 'uxItemSize', 'get_val')
    # mutex property
    MUTEX_HOLDER = ('The handle of the task that holds the lock.', '', 'get_empty_val')
    # mutex property
    RCALLCOUNT = ('Number of times a recursive mutex has been recursively "taken".', '', 'get_empty_val')
    # queue property
    TASKS_WAITING_TO_SEND = ('Tasks that are blocked waiting to post onto this queue.',
                             'xTasksWaitingToSend', 'get_empty_val')
    # queue property
    TASKS_WAITING_TO_RECEIVE = ('Tasks that are blocked waiting to read from this queue.',
                                'xTasksWaitingToReceive', 'get_empty_val')
    # semaphore property
    TASKS_WAITING_TO_GIVE = ('Tasks that are blocked waiting to release a lock.',
                             'xTasksWaitingToSend', 'get_empty_val')
    # semaphore property
    TASKS_WAITING_TO_TAKE = ('Tasks that are blocked waiting to take a lock.',
                             'xTasksWaitingToReceive', 'get_empty_val')
    # queue property
    RX_LCK = ('Number of items received from the queue (removed from the queue) while the queue was locked. Set to '
              'queueUNLOCKED when the queue is not locked.', 'cRxLock', 'get_val')
    # queue property
    TX_LCK = ('Number of items transmitted to the queue (added to the queue) while the queue was locked. Set to '
              'queueUNLOCKED when the queue is not locked.', 'cTxLock', 'get_val')
    NUMBER = ('Queue number set via \"vQueueSetQueueNumber()\"', 'uxQueueNumber', 'get_val')
    TYPE = ('Queue type.', 'ucQueueType', 'get_val')


class Queues:
    def __init__(self, is_semaphore):
        self._queues = []
        self._is_sem = is_semaphore
        self._queue_type = gdb.lookup_type("Queue_t")
        self._queue_ptr_type = self._queue_type.pointer()
        self._tcb_ptr_type = gdb.lookup_type('TCB_t').pointer()

    def print_table_help(self):
        for _, item in enumerate(QueueProperty):
            if self.queue_sem_field_filter(item):
                continue
            if not item.exist(self._queue_type):
                continue
            item.print_property_help(self._queue_type)
        print('')

    def get_table_headers(self):
        row = []
        for _, item in enumerate(QueueProperty):
            if self.queue_sem_field_filter(item):
                continue
            if not item.exist(self._queue_type):
                continue
            row.append(item.title)
        return row

    def queue_sem_field_filter(self, item):
        if self._is_sem:
            if item in (
                    QueueProperty.TASKS_WAITING_TO_SEND,
                    QueueProperty.TASKS_WAITING_TO_RECEIVE,
                    QueueProperty.I_SIZE,
                    QueueProperty.RX_LCK,
                    QueueProperty.TX_LCK):
                return True
        else:
            if item in (
                    QueueProperty.TASKS_WAITING_TO_GIVE,
                    QueueProperty.TASKS_WAITING_TO_TAKE,
                    QueueProperty.MUTEX_HOLDER,
                    QueueProperty.RCALLCOUNT):
                return True
        return False

    def add_queue(self, queue_registery):
        if queue_registery['xHandle'] == 0:
            return
        name = queue_registery['pcQueueName'].string()
        queue = queue_registery['xHandle'].cast(self._queue_ptr_type).dereference()
        if (not self._is_sem and queue['uxItemSize'] == 0) or \
                (self._is_sem and queue['uxItemSize'] != 0):
            return
        self._queues.append((name, queue))

    def show(self):
        table = []
        for idx, _ in enumerate(self._queues):
            table.extend(self.get_table_rows(idx))
        if len(table) == 0:
            return
        self.print_table_help()
        print_table(table, self.get_table_headers())

    def get_table_rows(self, q_id):
        table = []
        name, queue = self._queues[q_id]
        rcv_list = FreeRtosList(queue['xTasksWaitingToReceive'], 'TCB_t')
        snd_list = FreeRtosList(queue['xTasksWaitingToSend'], 'TCB_t')

        for list_id in range(max(rcv_list.length, snd_list.length, 1)):
            row = []
            if list_id != 0:
                name, queue = ('', None)
            for _, item in enumerate(QueueProperty):

                if self.queue_sem_field_filter(item):
                    continue

                if item == QueueProperty.NAME:
                    row.append(name)
                    continue
                if item in (QueueProperty.TASKS_WAITING_TO_RECEIVE, QueueProperty.TASKS_WAITING_TO_TAKE):
                    row.append(get_task_id_name_str(rcv_list[list_id]))
                    continue
                if item in (QueueProperty.TASKS_WAITING_TO_SEND, QueueProperty.TASKS_WAITING_TO_GIVE):
                    row.append(get_task_id_name_str(snd_list[list_id]))
                    continue

                # if queue is mutex
                if queue is not None and queue['pcHead'] == 0:
                    if item == QueueProperty.MUTEX_HOLDER:
                        task_ptr = queue['u']['xSemaphore']['xMutexHolder'].cast(self._tcb_ptr_type)
                        row.append(get_task_id_name_str(None if task_ptr == 0 else task_ptr))
                        continue
                    if item == QueueProperty.RCALLCOUNT:
                        row.append(queue['u']['xSemaphore']['uxRecursiveCallCount'])
                        continue

                if not item.exist(self._queue_type.target()):
                    continue

                row.append(item.value_str(queue))
            table.append(row)
        return table


def get_task_id_name_str(task):
    task_id = TaskProperty.ID.get_val_as_is(task)
    task_name = TaskProperty.NAME.get_string_val(task)
    return f'{task_id} {task_name}'


def show_queues_list(is_semaphore):
    queue_registry_help = """Set configQUEUE_REGISTRY_SIZE > 0

    And call \"vQueueAddToRegistry()\" from a code to track your queue"""

    try:
        queue_registry = gdb.parse_and_eval('xQueueRegistry')
    except gdb.error as err:
        print(f'{err}\n{queue_registry_help}')
        return
    queues = Queues(is_semaphore)
    for idx in range(queue_registry.type.range()[1] + 1):
        queues.add_queue(queue_registry[idx])

    queues.show()


class FreeRtosQueue(gdb.Command):
    """ Generate a print out of the current queues info.
    """

    def __init__(self):
        super().__init__('freertos queue', gdb.COMMAND_USER)

    @staticmethod
    def invoke(_, __):
        show_queues_list(False)


class FreeRtosSemaphore(gdb.Command):
    """ Generate a print out of the current semaphores info.
    """

    def __init__(self):
        super().__init__('freertos semaphore', gdb.COMMAND_USER)

    @staticmethod
    def invoke(_, __):
        show_queues_list(True)
