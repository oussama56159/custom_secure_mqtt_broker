/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define WIFI_CHECK_INTERVAL_MS 30000
#define PUBLISH_INTERVAL_MS    5000
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart1;
UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
#define RX_BUFFER_SIZE 512
uint8_t rx;
char rxBuffer[RX_BUFFER_SIZE];
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */
uint8_t NORA_SendCommand(const char *cmd);
void NORA_ClearBuffer(void);
uint8_t NORA_IsWiFiConnected(void);
void NORA_ConnectWiFi(void);
void NORA_ConnectMQTT(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  MX_GPIO_Init();
  MX_USART2_UART_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  char msg[] = "STM32 UART is working!\r\n";
  HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), HAL_MAX_DELAY);

  NORA_SendCommand("AT");

    if (NORA_IsWiFiConnected())
    {
        HAL_UART_Transmit(&huart1, (uint8_t*)"Already connected\r\n", strlen("Already connected\r\n"), HAL_MAX_DELAY);

    }
    else
    {
        NORA_ConnectWiFi();
        NORA_ConnectMQTT();
    }
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  uint32_t lastWifiCheck = HAL_GetTick();
  uint32_t lastPublish   = HAL_GetTick();

  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

    /* Check WiFi/MQTT connection chaque 30 sec  */
	if (HAL_GetTick() - lastWifiCheck >= WIFI_CHECK_INTERVAL_MS)
	   {
	     lastWifiCheck = HAL_GetTick();

	     uint8_t wifiOk = NORA_IsWiFiConnected();
	       if (!wifiOk)
	        {
	          HAL_UART_Transmit(&huart1, (uint8_t*)"WiFi lost, reconnecting...\r\n",
	                                 strlen("WiFi lost, reconnecting...\r\n"), HAL_MAX_DELAY);
	            NORA_ConnectWiFi();
	            NORA_ConnectMQTT();
	     }

	      }
    /* Publish  data chaque  5 seconds */
	 if (HAL_GetTick() - lastPublish >= PUBLISH_INTERVAL_MS)
	    {
	        lastPublish = HAL_GetTick();

	        if (!NORA_SendCommand("AT+UMQPS=0,0,0,\"sensors/temperature\",\"25.6\""))
	        {
	            HAL_UART_Transmit(&huart1, (uint8_t*)"Publish failed, MQTT likely down\r\n",
	                               strlen("Publish failed, MQTT likely down\r\n"), HAL_MAX_DELAY);
	            NORA_ConnectMQTT();
	        }
	    }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 4;
  RCC_OscInitStruct.PLL.PLLN = 168;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 4;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_USART1_UART_Init(void)
{
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_USART2_UART_Init(void)
{
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_GPIO_Init(void)
{
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
}

/* USER CODE BEGIN 4 */
/* Change NORA_SendCommand to return 1 on OK, 0 on ERROR/timeout */
uint8_t NORA_SendCommand(const char *cmd)
{
    char txBuffer[128];

    memset(rxBuffer, 0, sizeof(rxBuffer));
    NORA_ClearBuffer();

    sprintf(txBuffer,"%s\r\n",cmd);

    HAL_UART_Transmit(&huart2, (uint8_t *)txBuffer, strlen(txBuffer), HAL_MAX_DELAY);
    HAL_UART_Transmit(&huart1, (uint8_t *)"> ", 2, HAL_MAX_DELAY);
    HAL_UART_Transmit(&huart1, (uint8_t *)txBuffer, strlen(txBuffer), HAL_MAX_DELAY);

    uint16_t index=0;
    uint32_t startTick=HAL_GetTick();
    uint8_t gotOK = 0;

    while(index < RX_BUFFER_SIZE-1)
    {
        if(HAL_UART_Receive(&huart2,&rx,1,50)==HAL_OK)
        {
            rxBuffer[index++]=rx;
            rxBuffer[index]=0;

            if(strstr(rxBuffer,"\r\nOK\r\n")!=NULL)
            {
                gotOK = 1;
                break;
            }

            if(strstr(rxBuffer,"\r\nERROR\r\n")!=NULL)
                break;
        }

        if(HAL_GetTick()-startTick>8000)
            break;
    }

    HAL_UART_Transmit(&huart1, (uint8_t*)rxBuffer, strlen(rxBuffer), HAL_MAX_DELAY);
    HAL_UART_Transmit(&huart1, (uint8_t*)"\r\n", 2, HAL_MAX_DELAY);

    return gotOK;
}
void NORA_ClearBuffer(void)
{
    while (HAL_UART_Receive(&huart2, &rx, 1, 10) == HAL_OK)
    {
        // Discard received byte
    }
}

/* Returns 1 if the module reports a WiFi IP, 0 otherwise */
uint8_t NORA_IsWiFiConnected(void)
{
    NORA_SendCommand("AT+UWSNST?");
    return (strstr(rxBuffer, "+UWSNST:0,192.168.") != NULL) ? 1 : 0;
}

void NORA_ConnectWiFi(void)
{
    HAL_UART_Transmit(&huart1, (uint8_t *)"Connecting to WiFi...\r\n",
                       strlen("Connecting to WiFi...\r\n"), HAL_MAX_DELAY);

    NORA_SendCommand("AT+UWSCP=0,\"Ooredoo 5G_865FA6\"");
    NORA_SendCommand("AT+UWSSW=0,\"2Q8SSZ5PB6\",0");
    NORA_SendCommand("AT+UWSIPD=0");
    NORA_SendCommand("AT+UWSC=0");

    HAL_Delay(5000);

    NORA_SendCommand("AT+UWSNST?");
}

void NORA_ConnectMQTT(void)
{
    NORA_SendCommand("AT+UMQTLS=0,2,\"ca_crt\",\"temp_sensor_crt\",\"temp_sensor_key\"");
    NORA_SendCommand("AT+UMQCP=0,\"192.168.1.228\",8883,\"temperature_sensor\",\"temperature_sensor\",\"906271\"");
    NORA_SendCommand("AT+UMQC=0");
    HAL_Delay(2000);
}
/* USER CODE END 4 */

void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
