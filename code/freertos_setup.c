#include "freertos_setup.h"

TaskHandle_t xMainHandle;

__weak void vMainTask( void *pvParameters ) {
  for(;;) {

  }
}

__weak void MX_FREERTOS_Init(void) {
  xTaskCreate(
      vMainTask
      ,  (const signed portCHAR *)"Test"
      ,  configMINIMAL_STACK_SIZE
      ,  NULL
      ,  tskIDLE_PRIORITY + 1
      ,  &xMainHandle );
}

__weak void HWSetup(void) {

}
