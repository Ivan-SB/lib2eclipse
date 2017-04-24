#include "freertos_setup.h"
#include "cmsis_os.h"

#pragma GCC diagnostic push

#pragma GCC diagnostic warning "-Wconversion"
#pragma GCC diagnostic warning "-Wpadded"
#pragma GCC diagnostic warning "-Wunused"
#pragma GCC diagnostic warning "-Wextra"


/*
#pragma GCC diagnostic push

#pragma GCC diagnostic warning "-Wconversion"
#pragma GCC diagnostic warning "-Wpadded"
#pragma GCC diagnostic warning "-Wunused"
#pragma GCC diagnostic warning "-Wextra"

#pragma GCC diagnostic pop
*/
/*

-Wuninitialised
-Wmissing-declaration
-Wpointer-arith
-Wshadow
-Wlogical-op
-Waggregate-return
-Wfloat-equal
*/


TaskHandle_t xMainHandle;

__weak void vMainTask( void *pvParameters );
__weak void vMainTask( void *pvParameters ) {
  for(;;) {

  }
}

__weak void MX_FREERTOS_Init(void) {
  xTaskCreate(
      vMainTask
      ,  (const portCHAR *)"Test"
      ,  configMINIMAL_STACK_SIZE
      ,  NULL
      ,  tskIDLE_PRIORITY + 1
      ,  &xMainHandle );
}

__weak void HWSetup(void);
__weak void HWSetup(void) {

}

#pragma GCC diagnostic pop
