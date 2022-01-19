// This code contains all supported freertos_gdb features to check it with GDB freertos commands
#include <stdio.h>
#include "sdkconfig.h"
#include "esp_event.h"
#include "freertos/timers.h"

TickType_t op_delay = 1000;
QueueHandle_t queue1;
QueueHandle_t queue2;

SemaphoreHandle_t semaphore_binary;
SemaphoreHandle_t semaphore_counting;
SemaphoreHandle_t semaphore_mutex;
SemaphoreHandle_t semaphore_recursive_mutex;

#define NUM_TIMERS 5

TimerHandle_t xTimers[ NUM_TIMERS ];
char *timer_names[NUM_TIMERS] = { "TIMER0", "TIMER1", "TIMER2", "TIMER3", "TIMER4" };

void vTimerCallback( TimerHandle_t xTimer ) {
const uint32_t ulMaxExpiryCountBeforeStopping = 10;
uint32_t ulCount;
   configASSERT( xTimer );

   ulCount = ( uint32_t ) pvTimerGetTimerID( xTimer );
   ulCount++;

   if( ulCount >= ulMaxExpiryCountBeforeStopping )
   {
       xTimerStop( xTimer, 0 );
   }
   else
   {
      vTimerSetTimerID( xTimer, ( void * ) ulCount );
   }
}

void sender_task(void *pvParameters) {
  uint32_t count = 0;
  while(1) {
    xQueueSend(queue1, &count, op_delay);
    count++;
  }
}

void reader_task(void *pvParameters){
  uint32_t buf;
  while(1) {
    xQueueReceive(queue2, &buf, op_delay);
  }
}

void sem_bin_take(void *pvParameters){
  while(1) {
    xSemaphoreTake(semaphore_binary, op_delay);
  }
}

void sem_recur_mut_take(void *pvParameters){
  while(1) {
    xSemaphoreTakeRecursive(semaphore_recursive_mutex, op_delay);
  }
}


void app_main(void)
{
    queue1 = xQueueCreate(10, sizeof(uint32_t));
    if (queue1) {
        vQueueAddToRegistry(queue1, "queue1");
        xTaskCreate(sender_task, "SENDER1", 2046, NULL, 6, NULL);
        xTaskCreate(sender_task, "SENDER2", 2046, NULL, 6, NULL);
    }

    queue2 = xQueueCreate(10, sizeof(uint32_t));
    if (queue2) {
        vQueueAddToRegistry(queue2, "queue2");
        xTaskCreate(reader_task, "READER1", 2046, NULL, 6, NULL);
        xTaskCreate(reader_task, "READER2", 2046, NULL, 6, NULL);
    }

    semaphore_binary = xSemaphoreCreateBinary();
    if (semaphore_binary) {
        vQueueAddToRegistry(semaphore_binary, "BINARY");
        xTaskCreate(sem_bin_take, "SEM_BIN1", 2046, NULL, 6, NULL);
        xTaskCreate(sem_bin_take, "SEM_BIN2", 2046, NULL, 6, NULL);
    }
    
    semaphore_counting = xSemaphoreCreateCounting(10, 5);
    if (semaphore_counting) {
        vQueueAddToRegistry(semaphore_counting, "COUNTING");
    }

    semaphore_mutex = xSemaphoreCreateMutex();
    if (semaphore_mutex) {
        vQueueAddToRegistry(semaphore_mutex, "MUTEX");
    }

    semaphore_recursive_mutex = xSemaphoreCreateRecursiveMutex();
    if (semaphore_recursive_mutex) {
        vQueueAddToRegistry(semaphore_recursive_mutex, "RECURSIVE_MUTEX");
        xTaskCreate(sem_recur_mut_take, "SEM_RECUR", 2046, NULL, 6, NULL);
    }
    
    for(int x = 0; x < NUM_TIMERS; x++ ) {
        xTimers[ x ] = xTimerCreate
                  ( timer_names[x], ( 100 * x ) + 100, pdTRUE, ( void * ) 0, vTimerCallback);

        if( xTimers[ x ] != NULL ) {
            xTimerStart( xTimers[ x ], 0 );
        }
    }

    return;
}
