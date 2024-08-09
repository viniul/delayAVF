#include <signal.h>
#include <sstream>
#include <fstream>

//#include "ctpl_stl.h"
//#include "json.hpp"

#include "verilated_vcd_c.h"
#include "Vsim_top__Syms.h"
VL_ATTR_COLD void Vsim_top___024root___eval_settle(Vsim_top___024root* vlSelf);

#define NO_PRINT 1
#define SUCCESS_VAL 0x55555555
#define FAILURE_VAL 0xaaaaaaaa

using namespace std;

std::mutex m;
std::condition_variable cv;


void vl_finish(const char* filename, int linenum, const char* hier) VL_MT_UNSAFE {
    // hier is unused in the default implementation.
    (void)hier;
    //VL_PRINTF(  // Not VL_PRINTF_MT, already on main thread
    //    "- %s:%d: Verilog $finish Vincent\n", filename, linenum);
    Verilated::threadContextp()->gotFinish(true);
}

// in cycles, when the important cycle range is over + extra buffer
int timeout = 0;

// enables dump of FFs, used to see the difference between one injection and reference
int dump_regs = 0;

template<typename... Args> void print(const char *fmt, Args... args)
{
#if NO_PRINT == 1
  return;
#endif
  int len = snprintf(NULL, 0, fmt, args...);
  char *text = (char *)malloc(len + 1);
  snprintf(text, len + 1, fmt, args...);
  write(1, text, strlen(text));
  free(text);
}

double sc_time_stamp () {       // Called by $time in Verilog
  print("$time was called in Verilog, which is not supported\n");
  exit(1);
}

void INThandler(int signal)
{
  print("\nCaught ctrl-c\n");
  exit(0);
}

typedef struct {
  IData last_value;
  const char *stdoutfile;
} gpio_context_t;

bool do_gpio(gpio_context_t *context, IData gpio, int main_time) {
  //printf("\n %lu output gpio is %lu\n", main_time, gpio);
  //printf("%c stdoutfile %s \n", gpio, context->stdoutfile);
  if (context->last_value != gpio) {
    context->last_value = gpio;
    if (context->stdoutfile != NULL){ //Somehow commandArgsPlusMatch returns an empty string if no match found?
      //printf("%c stdoutfile %s \n", gpio, context->stdoutfile);
      std::ofstream output(context->stdoutfile + 12, ios_base::app);
      output << (char)gpio;
      //printf("%c stdoutfile %s \n", gpio, context->stdoutfile);
    } else {
      printf("%c", gpio);
    }
    
    return true;
  }
  return false;
}

int hamming_dist(IData n1, IData n2)
{
  IData tmp = n1 ^ n2;
  int res = 0;
  for (; tmp; tmp >>= 1) {
    res += tmp & 1;
  }
  return res;
}

constexpr unsigned int hash_string(const char *s, int off = 0) {
    return !s[off] ? 5381 : (hash_string(s, off+1)*33) ^ s[off];
}

int readVal(Vsim_top___024root* dut, const char* name) {
    CData * Q;
    CData * QN;
    switch (hash_string(name)) {
    /*REPLACEREAD*/
    default:
        fprintf(stderr, "\n ERROR: No flop found matching for %s !\n", name);
        return -1;
    }
    return (int)*Q;
}

int writeVal(Vsim_top___024root* dut, const char* name, int writeValue) {
    CData * Q;
    CData * QN;
    switch (hash_string(name)) {
    /*REPLACEWRITE*/
    default:
        fprintf(stderr, "\n ERROR: No flop found matching for %s !\n", name);
        return -1;
    }
    *Q = writeValue;
    *QN = 1-writeValue;
    return 0;
}

int flipVal(Vsim_top___024root* dut, const char* name) {
    CData * Q;
    CData * QN;

    switch (hash_string(name)) {
    /*REPLACE*/
    default:
        fprintf(stderr, "\n ERROR: No flop found matching for %s!\n", name);
        return -1;
    }
    int value = readVal(dut, name);
// Actually do the flip!
    *Q = 1-value;
    *QN = value;
    return 0;

}

using namespace std;

/*
int do_sim(std::vector<std::string> faulted_flops, int inject_cycle, char *stdoutfile, int argc, char **argv,char **env){
    const std::unique_ptr<VerilatedContext> contextp{new VerilatedContext};
    contextp->commandArgs(argc, argv);
    gpio_context_t gpio_context = { 0, stdoutfile };
    const std::unique_ptr<Vsim_top> top{new Vsim_top{contextp.get()}};
    bool done = false;
    uint64_t cycleNum = 0;
    while (!(done || contextp->gotFinish())) {
      //printf("\n Doing cycle %d", cycleNum);
        //if (t > 200)
        //    top->resetn = 1;
        top->clk = !top->clk;
        if (runFaultInjection && (top->clk == 1) && (cycleNum == inject_cycle)) {
            for (auto & flop : faulted_flops) {
                //printf("Flipping %s at cycle %d \n", flop.c_str(), cycleNum);
                int ret;
                if (runDelaySimulation) {
                    ret = writeVal(top->rootp, flop.c_str(), faulted_flops_vals[flop]);
                } else {
                    ret = flipVal(top->rootp, flop.c_str());
                }
                if (ret==-1) {
                    continue;
                    if (stdoutfile != NULL){
                        stdoutfile = NULL;
                        free(stdoutfile);
                    }
                    //free(stdoutfile);
                    //return -1;
                }
            }
        }
        //printf("\n Doing eval %d", cycleNum); 
        top->eval();
        //printf("\n eval done %d \n", cycleNum);
        if (tfp) tfp->dump (t);
        //if (trace_fd && top->clk && top->trace_valid) fprintf(trace_fd, "%9.9lx\n", top->trace_data);
        if (timeout && (t >= timeout)) {
            fprintf(stderr, "Timeout:simulationing at time %lu cycle %lu \n", t, cycleNum);
            //REPLACEDUMP

            done = true;
        }
        t += 31.25;
        if(top->clk == 1) cycleNum+=1;
        //printf("\n Calling do_gpio \n");
        //printf("Stdoutfile  context %s \n", gpio_context.stdoutfile);
        do_gpio(&gpio_context, top->gpio, cycleNum);
    }
    if (tfp) tfp->close();
    if (tfp) {
        delete tfp;
    };
    //delete top;
    if (stdoutfile != NULL){
        stdoutfile = NULL;
        free(stdoutfile);
    }
    return 0;
}*/

int run_json_config(int argc, char **argv, char **env){
    //Hashmap:
    //{"injection_points":
    // ["flops": <>, "cycles": []]
    //
    //
    //}


    //Hashmap: String to int
    //std::vector<std::tuple<std::vector<string>, std::vector<int>> fault_campaign; 
    //std::string basepath = "";
    //List of tuple: List of flops to cycle to fault
    // for (auto &t: fault_campaign){
    //    std::vector <string> faulted_flops = std::get<1>(t);
    //    for(auto cycle: std::get<2>(t)){
    //        std::string stdoutfile = basepath + ",".join(faulted_flops) + cycle;
    //        do_sim(std::get<1>(t), cycle, stdoutfile.c_str(), argc, argv, env);
    //    }
    //}
    return 0;
}

int main(int argc, char **argv, char **env)
{
    
    bool done = 0;
    //fprintf(stderr, "Built with %s %s.\n", Verilated::productName(), Verilated::productVersion());
    //fprintf(stderr, "Recommended: Verilator 4.0 or later.\n");
    const std::unique_ptr<VerilatedContext> contextp{new VerilatedContext};
    contextp->commandArgs(argc, argv);
    const char* ret_val =  contextp->commandArgsPlusMatch("json_config");
    if (ret_val[0]){
        //We do the json config
        run_json_config(argc, argv, env);
    }
    ret_val =  contextp->commandArgsPlusMatch("stdoutfile");
    char *stdoutfile = NULL;
    if (ret_val[0]){
        stdoutfile = (char *)malloc(sizeof(char)*(strlen(ret_val)+1));
        strcpy(stdoutfile, ret_val );
        {
            std::ofstream output(stdoutfile + 12); //Overwrite fiel to empty file
        }
    } 
    //printf("Stdoutfile %s \n", stdoutfile);
    gpio_context_t gpio_context = { 0, stdoutfile };
    //printf("Stdoutfile  context %s \n", gpio_context.stdoutfile);
    //do_gpio(&gpio_context, 'D', 0);
    //return 0;
    //Verilated::commandArgs(argc, argv); //This creates a global context, which is not what we want!
    //Vpicorv32_wrapper* top = new Vpicorv32_wrapper;
    const std::unique_ptr<Vsim_top> top{new Vsim_top{contextp.get()}};

    // Tracing (vcd)
    VerilatedVcdC* tfp = NULL;
    //const char* flag_vcd = Verilated::commandArgsPlusMatch("vcd");
    const char* flag_vcd = contextp->commandArgsPlusMatch("vcd");
    if (flag_vcd && 0==strcmp(flag_vcd, "+vcd")) {
        //Verilated::traceEverOn(true);
        contextp->traceEverOn(true);
        tfp = new VerilatedVcdC;
        top->trace (tfp, 99);
        tfp->open("build_tmp/testbench.vcd");
    }

    // Tracing (data bus, see showtrace.py)
    FILE *trace_fd = NULL;
    //const char* flag_trace = Verilated::commandArgsPlusMatch("trace");
    const char* flag_trace =  contextp->commandArgsPlusMatch("trace");
    if (flag_trace && 0==strcmp(flag_trace, "+trace")) {
        trace_fd = fopen("build_tmp/testbench.trace", "w");
    }
    //const char* stdoutfile =  contextp->commandArgsPlusMatch("stdoutfile");
    //std::ofstream output(stdoutfile + 12);
    if (flag_trace && 0==strcmp(flag_trace, "+trace")) {
        trace_fd = fopen("build_tmp/testbench.trace", "w");
    }

    bool runFaultInjection = false;
    bool runDelaySimulation = false;
    //const char *bad_flop = Verilated::commandArgsPlusMatch("bad_flop=");
    char *bad_flop = NULL;
    ret_val = contextp->commandArgsPlusMatch("bad_flop=");
    if (ret_val[0]){
        bad_flop = (char *) malloc(sizeof(char)*(strlen(ret_val)+1));
        strcpy(bad_flop, ret_val);
    } 
    //char store_flop[50];
    std::vector<std::string> faulted_flops;
    std::map<std::string, int> faulted_flops_vals;
    //printf("Stdoutfile  context before bad_flop parser %s \n", gpio_context.stdoutfile);
    
    if (bad_flop != NULL) {
        //std::cout << "bad flop arg " << bad_flop << std::endl;
        std::stringstream badFlopStream; //bad_flop);
        badFlopStream << (bad_flop+ 10);
        runFaultInjection = true;
        while( badFlopStream.good() )
        {
            string substr;
            getline( badFlopStream, substr, ',' );
            faulted_flops.push_back( substr );
            
            //std::cout << "Pushing flop " << substr << std::endl;
        }
        const char *delay_simulation = contextp->commandArgsPlusMatch("delay_simulation");
        if (delay_simulation[0]) {
            runDelaySimulation = true;
            for (auto & flop : faulted_flops) {
                //VU: We initialize to zero in case we inject in the first cycle
                //int value = readVal(top->picorv32_wrapper, flop.c_str());
                faulted_flops_vals[flop] = 0;//value;
            }
        }
    }
    if (bad_flop != NULL){
        free(bad_flop);
        bad_flop = NULL;
    }
    //printf("Stdoutfile  context beofre timeoutout parser %s \n", gpio_context.stdoutfile);
    vluint64_t timeout = 0;
    const char *arg_timeout = contextp->commandArgsPlusMatch("timeout="); //Verilated::commandArgsPlusMatch("timeout=");
    //printf("Stdoutfile  context after timeout parser %s \n", gpio_context.stdoutfile);
    if (arg_timeout[0])
        timeout = atoi(arg_timeout+9);
    //printf("Stdoutfile  context %s \n", gpio_context.stdoutfile);
    //printf("Timeout: %d\n", timeout);

    const char *bad_cycle = contextp->commandArgsPlusMatch("bad_cycle="); //Verilated::commandArgsPlusMatch("bad_cycle=");
    int inject_cycle;
    if (bad_cycle[0]) {
        inject_cycle = atoi(bad_cycle + 11);
        //printf("Fault injection time: %d\n", inject_cycle);
    }

    top->clk = 0;
    vluint64_t t = 0;
    uint64_t cycleNum = 0;
    //while (!(done || Verilated::gotFinish())) {
    while (!(done || contextp->gotFinish())) {
      //printf("\n Doing cycle %d", cycleNum);
        //if (t > 200)
        //    top->resetn = 1;
        top->clk = !top->clk;
        if (runFaultInjection && (top->clk == 1) && runDelaySimulation && (cycleNum == (inject_cycle -1))) {
            for (auto & flop : faulted_flops) {
                int value = readVal(top->rootp, flop.c_str());
                faulted_flops_vals[flop] = value;
            }
        }

        if (runFaultInjection && (top->clk == 1) && (cycleNum == inject_cycle)) {
            for (auto & flop : faulted_flops) {
                //printf("Flipping %s at cycle %d \n", flop.c_str(), cycleNum);
                int ret;
                if (runDelaySimulation) {
                    ret = writeVal(top->rootp, flop.c_str(), faulted_flops_vals[flop]);
                } else {
                    ret = flipVal(top->rootp, flop.c_str());
                }
                if (ret==-1) {
                    continue;
                    if (stdoutfile != NULL){
                        stdoutfile = NULL;
                        free(stdoutfile);
                    }
                    //free(stdoutfile);
                    //return -1;
                }
            }
        }
        //printf("\n Doing eval %d", cycleNum); 
        top->eval();
        //printf("\n eval done %d \n", cycleNum);
        if (tfp) tfp->dump (t);
        //if (trace_fd && top->clk && top->trace_valid) fprintf(trace_fd, "%9.9lx\n", top->trace_data);
        if (timeout && (t >= timeout)) {
            fprintf(stderr, "Timeout:simulationing at time %lu cycle %lu \n", t, cycleNum);
            /*REPLACEDUMP*/

            done = true;
        }
        t += 31.25;
        if(top->clk == 1) cycleNum+=1;
        //printf("\n Calling do_gpio \n");
        //printf("Stdoutfile  context %s \n", gpio_context.stdoutfile);
        do_gpio(&gpio_context, top->gpio, cycleNum);
    }
    if (tfp) tfp->close();
    if (tfp) {
        delete tfp;
    };
    //delete top;
    if (stdoutfile != NULL){
        stdoutfile = NULL;
        free(stdoutfile);
    }
    return 0;
}
