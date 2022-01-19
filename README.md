# Freertos-gdb

Python module for user-friendly view freeRTOS-kernel objects in GDB

## Requirements

GDB must built with python 3.6+ support

Check your GDB with command:

```bash
gdb -q -ex "python print('OK' if sys.version_info.major==3 and sys.version_info.minor>=6 else 'NOT SUPPORTED')" -ex "quit"
```

## Install

1. Install the distro using `pip`

```bash
pip install freertos-gdb
```

## Run

Start GDB and run the command

```bash
python import freertos_gdb
```

Also, you could just update `.gdbinit` with this command

## Possible problems and solutions

#### ModuleNotFoundError
```bash
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'freertos_gdb'
Error while executing Python code.
```

#### Solution
Check your `sys.path` inside GDB shell
```
python import sys; print(sys.path)
```

Append `sys.path` with a path to directory which contains `freertos_gdb` module.
Or execute GDB with right `PYTHONPATH` env variable

## Commands

You have `freertos` command with subcommands inside:

```
(gdb) freertos 
"freertos" must be followed by the name of a subcommand.
List of freertos subcommands:

freertos queue --  Generate a print out of the current queues info.
freertos semaphore --  Generate a print out of the current semaphores info.
freertos task --  Generate a print out of the current tasks and their states.
freertos timer --  Generate a print out of the current timers info.
....
```

## Examples

### Tasks

```
(gdb) freertos task
CPU	 - Processing on CPU number
ID	 - TCB_t task memory address
PRI	 - Task priority
B_PRI	 - Base priority.
SS	 - Stack size.
SL	 - Stack limit (available space left).

CPU    ID          NAME       STATUS       PRI    B_PRI    MUTEXES_HELD    SS    SL
-----  ----------  ---------  ---------  -----  -------  --------------  ----  ----
CPU0   0x3ffb6674  IDLE       ready          0        0               0  1104   428
       0x3ffb6dd4  IDLE       ready          0        0               0  1104   428
CPU1   0x3ffbb724  SEM_RECUR  ready          6        6               1  1680   364
       0x3ffafd14  ipc0       suspended     24       24               0   564   456
       0x3ffb4db4  esp_timer  suspended     22       22               0  3648   444
       0x3ffb3c54  ipc1       suspended     24       24               0   592   428
       0x3ffb7734  Tmr Svc    delayed_1      1        1               0  1584   460
       0x3ffaf83c  SENDER1    delayed_1      6        6               0  1600   444
       0x3ffaf998  SENDER2    delayed_1      6        6               0  1548   496
       0x3ffb909c  READER1    delayed_1      6        6               0  1608   436
       0x3ffb99fc  READER2    delayed_1      6        6               0  1608   436
       0x3ffba35c  SEM_BIN1   delayed_1      6        6               0  1624   420
       0x3ffbacbc  SEM_BIN2   delayed_1      6        6               0  1592   452
```

### Queues, Semafores (and mutexes)

To watch queues you must add them to registry via [vQueueAddToRegistry](https://www.freertos.org/vQueueAddToRegistry.html)

```
(gdb) freertos queue 
COUNT	 - Number of items currently in the queue.
I_LEN	 - Length of the queue (number of items could hold, not the number of bytes).
I_SIZE	 - Size of each item that the queue will hold.
TASKS_WAITING_TO_SEND	 - Tasks that are blocked waiting to post onto this queue.
TASKS_WAITING_TO_RECEIVE	 - Tasks that are blocked waiting to read from this queue.
RX_LCK	 - Number of items received from the queue (removed from the queue) while the queue was locked. Set to queueUNLOCKED when the queue is not locked.
TX_LCK	 - Number of items transmitted to the queue (added to the queue) while the queue was locked. Set to queueUNLOCKED when the queue is not locked.

NAME    COUNT    I_LEN    I_SIZE    TASKS_WAITING_TO_SEND    TASKS_WAITING_TO_RECEIVE    RX_LCK    TX_LCK
------  -------  -------  --------  -----------------------  --------------------------  --------  --------
TmrQ    0        10       16                                 0x3ffb7734 Tmr Svc          -1        -1
queue1  10       10       4         0x3ffaf83c SENDER1                                   -1        -1
                                    0x3ffaf998 SENDER2
queue2  0        10       4                                  0x3ffb909c READER1          -1        -1
                                                             0x3ffb99fc READER2
```


```
(gdb) freertos semaphore 
COUNT	 - Number of items currently in the queue.
I_LEN	 - Length of the queue (number of items could hold, not the number of bytes).
MUTEX_HOLDER	 - The handle of the task that holds the lock.
RCALLCOUNT	 - Number of times a recursive mutex has been recursively "taken".
TASKS_WAITING_TO_GIVE	 - Tasks that are blocked waiting to release a lock.
TASKS_WAITING_TO_TAKE	 - Tasks that are blocked waiting to take a lock.

NAME             COUNT    I_LEN    MUTEX_HOLDER          RCALLCOUNT    TASKS_WAITING_TO_GIVE    TASKS_WAITING_TO_TAKE
---------------  -------  -------  --------------------  ------------  -----------------------  -----------------------
BINARY           0        1                                                                     0x3ffba35c SEM_BIN1
                                                                                                0x3ffbacbc SEM_BIN2
COUNTING         5        10
MUTEX            1        1                              0
RECURSIVE_MUTEX  0        1        0x3ffbb724 SEM_RECUR  1628326
```

### Timers

```
(gdb) freertos timer 
TIMER_ID	 - An ID to identify the timer.
OVERFLOW	 - True if timer has been overflow
PERIOD_IN_TICKS	 - How quickly and often the timer expires.
STATUS	 - Holds bits to say if the timer was statically allocated or not, and if it is active or not.

TIMER_ID    NAME      OVERFLOW    PERIOD_IN_TICKS    STATUS  CALLBACK_FN
----------  ------  ----------  -----------------  --------  ---------------------------
0x2         TIMER3           0                400         5  0x400d490c <vTimerCallback>
0x3         TIMER2           0                300         5  0x400d490c <vTimerCallback>
0x5         TIMER1           0                200         5  0x400d490c <vTimerCallback>
0x2         TIMER4           0                500         5  0x400d490c <vTimerCallback>
```