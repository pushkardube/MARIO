/*
MIT License

Copyright (c) 2024 Society of Robotics and Automation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <math.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_system.h"
#include "driver/uart.h"

#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <std_msgs/msg/float64_multi_array.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <rmw_microros/rmw_microros.h>
#include <sra_board.h>

#include "esp32_serial_transport.h"

#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){printf("Failed status on line %d: %d. Restarting.\n",__LINE__,(int)temp_rc);esp_restart();}}
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){printf("Failed status on line %d: %d. Continuing.\n",__LINE__,(int)temp_rc);}}

#define ARRAY_LEN 200
#define pi 3.141592653589
#define SMOOTHING_STEPS 20
#define SMOOTHING_DELAY 20

typedef struct {
    float current_base;
    float current_shoulder;
    float current_elbow;
    float current_gripper;
} servo_positions;

static servo_positions current_pos = {0, 0, 0, 0};

rcl_subscription_t subscriber;
std_msgs__msg__Float64MultiArray recv_msg;

servo_config servo_a = {        // GRIPPER
    .servo_pin = SERVO_A,
    .min_pulse_width = CONFIG_SERVO_A_MIN_PULSEWIDTH,
    .max_pulse_width = CONFIG_SERVO_A_MAX_PULSEWIDTH,
    .max_degree = CONFIG_SERVO_A_MAX_DEGREE,
    .mcpwm_num = MCPWM_UNIT_0,
    .timer_num = MCPWM_TIMER_0,
    .gen = MCPWM_OPR_A,
};

servo_config servo_b = {        // ELBOW
    .servo_pin = SERVO_B,
    .min_pulse_width = CONFIG_SERVO_B_MIN_PULSEWIDTH,
    .max_pulse_width = CONFIG_SERVO_B_MAX_PULSEWIDTH,
    .max_degree = CONFIG_SERVO_B_MAX_DEGREE,
    .mcpwm_num = MCPWM_UNIT_0,
    .timer_num = MCPWM_TIMER_0,
    .gen = MCPWM_OPR_B,
};

servo_config servo_c = {        // ARM/SHOULDER
    .servo_pin = SERVO_C,
    .min_pulse_width = CONFIG_SERVO_C_MIN_PULSEWIDTH,
    .max_pulse_width = CONFIG_SERVO_C_MAX_PULSEWIDTH,
    .max_degree = CONFIG_SERVO_C_MAX_DEGREE,
    .mcpwm_num = MCPWM_UNIT_0,
    .timer_num = MCPWM_TIMER_1,
    .gen = MCPWM_OPR_A,
};

servo_config servo_d = {        // BASE
    .servo_pin = SERVO_D,
    .min_pulse_width = CONFIG_SERVO_D_MIN_PULSEWIDTH,
    .max_pulse_width = CONFIG_SERVO_D_MAX_PULSEWIDTH,
    .max_degree = CONFIG_SERVO_D_MAX_DEGREE,
    .mcpwm_num = MCPWM_UNIT_0,
    .timer_num = MCPWM_TIMER_1,
    .gen = MCPWM_OPR_B,
};

void smooth_servo_motion(servo_config *servo, float current_angle, float target_angle) {
    float step = (target_angle - current_angle) / SMOOTHING_STEPS;
    for (int i = 0; i < SMOOTHING_STEPS; i++) {
        set_angle_servo(servo, current_angle + step * (i + 1));
        vTaskDelay(pdMS_TO_TICKS(SMOOTHING_DELAY));
    }
}

void subscription_callback(const void * msgin)
{
    const std_msgs__msg__Float64MultiArray * msg = (const std_msgs__msg__Float64MultiArray *)msgin;

    float target_base     = msg->data.data[0] * (180.0 / pi);
    float target_shoulder = msg->data.data[1] * (180.0 / pi);
    float target_elbow    = msg->data.data[2] * (180.0 / pi);
    float target_gripper  = (1.57 - msg->data.data[3]) * (180.0 / pi);

    if (fabs(target_base - current_pos.current_base) > 0.5) {
        smooth_servo_motion(&servo_d, current_pos.current_base, target_base);
        current_pos.current_base = target_base;
    }
    if (fabs(target_shoulder - current_pos.current_shoulder) > 0.5) {
        smooth_servo_motion(&servo_c, current_pos.current_shoulder, target_shoulder);
        current_pos.current_shoulder = target_shoulder;
    }
    if (fabs(target_elbow - current_pos.current_elbow) > 0.5) {
        smooth_servo_motion(&servo_b, current_pos.current_elbow, target_elbow);
        current_pos.current_elbow = target_elbow;
    }
    if (fabs(target_gripper - current_pos.current_gripper) > 0.5) {
        smooth_servo_motion(&servo_a, current_pos.current_gripper, target_gripper);
        current_pos.current_gripper = target_gripper;
    }
}

void micro_ros_task(void * arg)
{
    rcl_allocator_t allocator = rcl_get_default_allocator();
    rclc_support_t support;

    enable_servo();
    current_pos.current_gripper  = read_servo(&servo_a);
    current_pos.current_elbow    = read_servo(&servo_b);
    current_pos.current_shoulder = read_servo(&servo_c);
    current_pos.current_base     = read_servo(&servo_d);

    printf("Waiting for micro-ROS agent...\n");
    while (rmw_uros_ping_agent(1000, 1) != RMW_RET_OK) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }
    printf("Agent found!\n");

    RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));

    rcl_node_t node = rcl_get_zero_initialized_node();
    RCCHECK(rclc_node_init_default(&node, "Set_servo_angles", "", &support));

    RCCHECK(rclc_subscription_init_default(
        &subscriber,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float64MultiArray),
        "/forward_position_controller/commands"));

    rclc_executor_t executor = rclc_executor_get_zero_initialized_executor();
    RCCHECK(rclc_executor_init(&executor, &support.context, 2, &allocator));
    RCCHECK(rclc_executor_set_timeout(&executor, RCL_MS_TO_NS(1000)));

    recv_msg.data.data     = (double *) malloc(ARRAY_LEN * sizeof(double));
    recv_msg.data.size     = 0;
    recv_msg.data.capacity = ARRAY_LEN;

    RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &recv_msg, &subscription_callback, ON_NEW_DATA));

    rclc_executor_spin(&executor);

    RCCHECK(rcl_subscription_fini(&subscriber, &node));
    RCCHECK(rcl_node_fini(&node));
    vTaskDelete(NULL);
}

void app_main(void)
{
    static size_t uart_port = UART_NUM_0;
    rmw_uros_set_custom_transport(
        true,
        (void *) &uart_port,
        esp32_serial_open,
        esp32_serial_close,
        esp32_serial_write,
        esp32_serial_read
    );

    xTaskCreate(micro_ros_task,
            "uros_task",
            CONFIG_MICRO_ROS_APP_STACK,
            NULL,
            CONFIG_MICRO_ROS_APP_TASK_PRIO,
            NULL);
}
