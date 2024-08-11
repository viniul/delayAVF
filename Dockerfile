FROM fedora:38
WORKDIR /setup
COPY requirements.txt requirements.txt
RUN dnf update -y && dnf install -y python3 pip python3-devel
RUN pip3 install -r requirements.txt
RUN dnf install -y make automake gcc gcc-c++ git
RUN dnf install -y verilator vim jq 
RUN dnf install -y clang tcl-devel readline-devel libffi-devel mercurial bison flex wget
#RUN git clone https://github.com/cliffordwolf/yosys.git && cd yosys && make && make test && make install
RUN wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2023-05-15/oss-cad-suite-linux-x64-20230515.tgz && tar zxvf oss-cad-suite-linux-x64-20230515.tgz
ENV PATH="/setup/oss-cad-suite/bin:${PATH}"
RUN dnf install -y xz cmake which ninja-build
RUN pip install west
RUN west init ~/zephyrproject && cd ~/zephyrproject && west update && west zephyr-export
RUN cd ~ && wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.1/zephyr-sdk-0.16.1_linux-x86_64.tar.xz && tar xvf zephyr-sdk-0.16.1_linux-x86_64.tar.xz && cd zephyr-sdk-0.16.1 &&  ./setup.sh -t riscv64-zephyr-elf
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
RUN dnf install -y stack 
RUN git clone https://github.com/zachjs/sv2v.git /tmp/sv2v  && cd /tmp/sv2v && make && stack install
RUN dnf install -y swig eigen3
RUN git clone https://github.com/The-OpenROAD-Project/OpenSTA.git && cd OpenSTA && git checkout 7358e26 && mkdir build && cd build && cmake .. && make -j && make install
