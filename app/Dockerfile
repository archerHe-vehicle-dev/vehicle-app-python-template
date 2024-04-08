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

# syntax=docker/dockerfile:1.2

# Build stage, to create the executable

# Dockerfile，用于构建一个多阶段容器化应用，该应用基于 Python，并且通过一系列步骤编译成静态可执行文件以便于部署
# 这里声明了基础镜像，指定平台为 $TARGETPLATFORM 变量所指的架构。该镜像是 Eclipse Velocitas 维护的一个包含 Python 开发环境的基础镜像
FROM --platform=$TARGETPLATFORM ghcr.io/eclipse-velocitas/devcontainer-base-images/python:v0.3 as builder
ARG TARGETARCH

# 定义一个构建时变量 TARGETARCH，然后更新包列表并安装 python3-dev，这是编译 C/java/c#扩展所需的开发包
# python-dev or python-devel 称为 Python 的开发包，包括了一些用 C / Java / C# 等编写的 Python 扩展，在编译的时候依赖的头文件等信息。在编译一个用 C 语言编写的 Python 扩展模块时，里面会有 #include<Python.h> 这样的语句，因此需要先安装 python-dev or python-devel 开发包

RUN apt-get update && apt-get install -y python3-dev

# 将当前目录下的 .velocitas.json 配置文件和整个 app 目录复制到容器内的 /workspace 目录下
COPY ./.velocitas.json /workspace/.velocitas.json
COPY ./app /workspace/app

# 在 ARM64 架构（aarch64）下，安装额外的依赖如 gcc 和 scons，这可能是由于在特定架构上需要编译某些依赖
# Remove this installation for Arm64 once staticx has a prebuilt wheel for Arm64
RUN /bin/bash -c 'set -ex && \
    ARCH=`uname -m` && \
    if [ "$ARCH" == "aarch64" ]; then \
    echo "ARM64" && \
    apt-get install -y gcc && \
    pip3 install --no-cache-dir scons; \
    fi'

# 使用 pip3 安装多个 Python 包，包括 pyinstaller（用于打包应用）、patchelf（修改 ELF 文件头信息）、staticx（用于制作静态链接的二进制文件），以及从 ./workspace/app 中的应用需求文件中列出的所有依赖
RUN pip3 install --no-cache-dir pyinstaller==5.9.0 \
    && pip3 install --no-cache-dir patchelf==0.17.0.0 \
    && pip3 install --no-cache-dir staticx \
    && pip3 install --no-cache-dir -r ./workspace/app/requirements.txt \
    && pip3 install --no-cache-dir -r ./workspace/app/requirements-links.txt

WORKDIR /workspace

# 改变工作目录至 /workspace 并执行 velocitas init 命令
RUN velocitas init

WORKDIR /workspace/app

# 切换工作目录至应用源码位置，使用 PyInstaller 打包 src/main.py 为主程序，生成单个可执行文件，并且不包含控制台窗口. -F 单个文件  -s 不显示控制台窗口
RUN pyinstaller --clean -F -s src/main.py

WORKDIR /workspace/app/dist

# 移动到打包后的可执行文件所在的目录，并使用 staticx 工具处理已打包的 main 可执行文件，将其变为静态链接的独立可执行文件，命名为 run-exe
RUN staticx main run-exe

# Runner stage, to copy the executable

# 创建一个新的空（scratch）基础镜像，并从名为 builder 的前一阶段构建中复制出已经静态化的 run-exe 文件至新的镜像中的 /dist/ 目录
FROM scratch

COPY --from=builder ./workspace/app/dist/run-exe /dist/

# 设置工作目录为 /dist，并且将 /dist 添加到系统的 PATH 环境变量中，这样可以直接运行 /dist 下的可执行文件
WORKDIR /tmp
WORKDIR /dist

ENV PATH="/dist:$PATH"

# 为最终镜像添加元数据标签，记录其来源为 Eclipse Velocitas 的 GitHub 仓库

LABEL org.opencontainers.image.source="https://github.com/eclipse-velocitas/vehicle-app-python-template"

# 当容器启动时，自动执行 /dist/ 目录下的 run-exe 可执行文件
CMD ["./run-exe"]
