FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git zip unzip openjdk-17-jdk python3-pip python3-venv \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev automake \
    build-essential lsb-release wget curl sudo \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash builder && \
    echo "builder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER builder
WORKDIR /home/builder

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV ANDROID_SDK_ROOT=/home/builder/.buildozer/android/platform/android-sdk
ENV ANDROID_HOME=/home/builder/.buildozer/android/platform/android-sdk

RUN mkdir -p /home/builder/.buildozer/android/platform/android-sdk/cmdline-tools && \
    cd /tmp && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-6514223_latest.zip -O cmdline-tools.zip && \
    unzip -q cmdline-tools.zip && \
    mv /tmp/tools /home/builder/.buildozer/android/platform/android-sdk/cmdline-tools/latest && \
    rm cmdline-tools.zip

RUN yes | /home/builder/.buildozer/android/platform/android-sdk/cmdline-tools/latest/bin/sdkmanager --licenses && \
    /home/builder/.buildozer/android/platform/android-sdk/cmdline-tools/latest/bin/sdkmanager \
    'platforms;android-33' \
    'build-tools;33.0.2' \
    'platform-tools'

RUN mkdir -p /home/builder/.buildozer/android/platform && \
    cd /home/builder/.buildozer/android/platform && \
    wget -q --tries=3 https://dl.google.com/android/repository/android-ndk-r28c-linux.zip -O android-ndk-r28c-linux.zip && \
    unzip -q android-ndk-r28c-linux.zip && \
    rm android-ndk-r28c-linux.zip

RUN pip3 install --upgrade pip==24.0 && pip3 install buildozer cython

ENV PATH="/home/builder/.local/bin:${PATH}"

WORKDIR /home/builder/app

CMD ["/bin/bash"]
