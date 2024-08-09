CONFIG = config.cfg
include $(CONFIG)

# List of directories to check
DIRECTORIES := /setup/oss-cad-suite/share/verilator/include/ /usr/share/verilator/include/ /usr/local/share/verilator/include/

# Function to check if a directory exists
define check_directory
$(shell if [ -d "$(1)" ]; then echo "$(1)"; fi)
endef

# Set variable based on existence of directories
VERILATOR_PATH := $(firstword $(foreach dir,$(DIRECTORIES),$(call check_directory,$(dir))))

# If none of the directories exist, show an error message
ifndef VERILATOR_PATH
$(error None of the directories exist)
endif




CELL_IMPL = $(STDCELL_IMPL)
RTL = rtl/*.v
VERILATOR_OPTS = -CFLAGS -DVL_USER_FINISH=1 +define+GPIO_ADDR=$(GPIO_ADDR) +define+TIMER_ADDR=$(TIMER_ADDR) +define+MEMSIZE=$(MEMSIZE) --cc --savable --trace --trace-underscore -Wno-LATCH --build -j 0


all:
	verilator $(VERILATOR_OPTS)  --Mdir build_tmp/testbench_verilator_dir -exe $(RTL) $(IBEX_FILE) $(CELL_IMPL) --top-module sim_top sim_main.cpp
	verilator $(VERILATOR_OPTS) -CFLAGS -fPIC --Mdir build_tmp/testbench_library_verilator_dir $(RTL) $(IBEX_FILE) $(CELL_IMPL) --top-module sim_top build_tmp/sim_main.cpp
	g++ -DVL_USER_FINISH=1 -c -I build_tmp/testbench_library_verilator_dir -I $(VERILATOR_PATH)/vltstd/ -I $(VERILATOR_PATH) build_tmp/sim_main.cpp -fPIC -o build_tmp/testbench_library.o
	g++ -DVL_USER_FINISH=1 -shared -I build_tmp/testbench_library_verilator_dir -I $(VERILATOR_PATH)/vltstd/ -I $(VERILATOR_PATH) -fPIC -o build_tmp/testbench_library.so build_tmp/testbench_library.o $(VERILATOR_PATH)/verilated.cpp $(VERILATOR_PATH)/verilated_vcd_c.cpp $(VERILATOR_PATH)/verilated_threads.cpp $(VERILATOR_PATH)/verilated_save.cpp  build_tmp/testbench_library_verilator_dir/Vsim_top__ALL.a

.PHONY: from_template
from_template: 
	#Vincent: I think paths are all relative to build_tmp, so we just compile as sim_main.template.cpp, without giving the buiild_tmp directory
	verilator $(VERILATOR_OPTS) --Mdir build_tmp/testbench_verilator_dir_out -exe $(RTL) $(IBEX_FILE) $(CELL_IMPL) --top-module sim_top sim_main.template.cpp
# Dummy target to demonstrate the selected directory
.PHONY: print_directory
print_directory: $(info Selected directory  $(VERILATOR_PATH))
