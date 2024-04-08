# Copyright (c) 2022-2024 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""A sample skeleton vehicle app."""

# 导入Python内置的异步I/O框架，用于编写并发代码，支持协程和事件循环等功能
import asyncio

# 导入JSON模块，提供序列化和反序列化JSON数据的功能
import json

# 导入Python的标准日志模块，用于创建和管理日志记录器，从而进行程序运行时的信息输出
import logging

# 导入signal模块，用于处理Unix系统信号，例如进程中断信号(SIGINT)
import signal

from vehicle import Vehicle, vehicle  # type: ignore

# OpenTelemetry,简称 OTel，是一个供应商中立的开源可观测性框架，用于仪表化、生成、收集和导出诸如跟踪、度量、日志等遥测数据。作为行业标准
from velocitas_sdk.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)

# 该类可能代表从Velocitas数据库获取的数据回复
from velocitas_sdk.vdb.reply import DataPointReply

# subscribe_topic 订阅特定主题消息的函数
from velocitas_sdk.vehicle_app import VehicleApp, subscribe_topic

# Configure the VehicleApp logger with the necessary log config and level.
# 函数配置日志记录器工厂，使其符合OpenTelemetry的要求，以便将日志与分布式追踪相结合
logging.setLogRecordFactory(get_opentelemetry_log_factory())
# 函数设置基本的日志格式
logging.basicConfig(format=get_opentelemetry_log_format())
# 设置全局日志记录器级别为“DEBUG”
logging.getLogger().setLevel("DEBUG")
# 取当前模块的日志记录器实例，并赋予变量logger
logger = logging.getLogger(__name__)

GET_SPEED_REQUEST_TOPIC = "sampleapp/getSpeed"
GET_SPEED_RESPONSE_TOPIC = "sampleapp/getSpeed/response"
DATABROKER_SUBSCRIPTION_TOPIC = "sampleapp/currentSpeed"


class SampleApp(VehicleApp):
    """
    Sample skeleton vehicle app.

    The skeleton subscribes to a getSpeed MQTT topic
    to listen for incoming requests to get
    the current vehicle speed and publishes it to
    a response topic.

    It also subcribes to the VehicleDataBroker
    directly for updates of the
    Vehicle.Speed signal and publishes this
    information via another specific MQTT topic
    """

    def __init__(self, vehicle_client: Vehicle):
        # SampleApp inherits from VehicleApp.
        super().__init__()
        self.Vehicle = vehicle_client

    async def on_start(self):
        """Run when the vehicle app starts"""
        # This method will be called by the SDK when the connection to the
        # Vehicle DataBroker is ready.
        # Here you can subscribe for the Vehicle Signals update (e.g. Vehicle Speed).

        ## feed databroker with current speed
        await self.Vehicle.Speed.subscribe(self.on_speed_change)

    async def on_speed_change(self, data: DataPointReply):
        """The on_speed_change callback, this will be executed when receiving a new
        vehicle signal updates."""
        # Get the current vehicle speed value from the received DatapointReply.
        # The DatapointReply containes the values of all subscribed DataPoints of
        # the same callback.
        vehicle_speed = data.get(self.Vehicle.Speed).value

        # Do anything with the received value.
        # Example:
        # - Publishes current speed to MQTT Topic (i.e. DATABROKER_SUBSCRIPTION_TOPIC).

        # 订阅DATABROKER_SUBSCRIPTION_TOPIC，并将当前速度值作为JSON数据发布到该topic
        await self.publish_event(
            DATABROKER_SUBSCRIPTION_TOPIC,
            json.dumps({"speed": vehicle_speed}),
        )

    # 是一个装饰器，用于订阅特定的MQTT topic, publish GET_SPEED_REQUEST_TOPIC事件, 并处理相应的事件
    @subscribe_topic(GET_SPEED_REQUEST_TOPIC)
    async def on_get_speed_request_received(self, data: str) -> None:
        """The subscribe_topic annotation is used to subscribe for incoming
        PubSub events, e.g. MQTT event for GET_SPEED_REQUEST_TOPIC.
        """

        # Use the logger with the preferred log level (e.g. debug, info, error, etc)
        logger.debug(
            "PubSub event for the Topic: %s -> is received with the data: %s",
            GET_SPEED_REQUEST_TOPIC,
            data,
        )

        # Getting current speed from VehicleDataBroker using the DataPoint getter.
        vehicle_speed = (await self.Vehicle.Speed.get()).value

        # Do anything with the speed value.
        # Example:
        # - Publishes the vehicle speed to MQTT topic (i.e. GET_SPEED_RESPONSE_TOPIC).
        await self.publish_event(
            GET_SPEED_RESPONSE_TOPIC,
            json.dumps(
                {
                    "result": {
                        "status": 0,
                        "message": f"""Current Speed = {vehicle_speed}""",
                    },
                }
            ),
        )


# 异步函数main，这意味着它是一个协程函数，可以包含异步操作并在事件循环中协同执行
async def main():
    """Main function"""
    # 日志记录器实例logger，调用其.info()方法记录一条信息，表明SampleApp正在启动
    logger.info("Starting SampleApp...")
    # Constructing SampleApp and running it.
    # SampleApp 与车辆交互逻辑的应用程序类
    vehicle_app = SampleApp(vehicle)
    # 异步等待vehicle_app实例的run方法完成。run方法内部应该执行的是应用程序的核心逻辑，比如连接到车辆、开始处理数据流或其他异步任务
    await vehicle_app.run()


# 获取当前线程的默认事件循环实例，它是所有异步操作的协调者
LOOP = asyncio.get_event_loop()
# 为SIGTERM信号（通常用来终止进程）注册一个处理器。当收到这个信号时，事件循环将会停止运行
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
# 调用事件循环的run_until_complete方法，传入之前定义的main协程。这将启动事件循环，并一直运行直到main函数完成为止
LOOP.run_until_complete(main())
# 关闭事件循环。这一步确保资源正确释放，防止内存泄漏等问题
LOOP.close()
