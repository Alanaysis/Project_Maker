/*
 * netlist_parser.c - Circuit Netlist Parser
 *
 * Parses a simplified text-based netlist format into the internal Netlist
 * representation. This is the first step in the STA flow.
 *
 * Netlist Format:
 *   circuit <name>
 *   clock <name> <period_ns> <duty_cycle>
 *   register <name> <clock> <ccq_max> <ccq_min> <setup> <hold>
 *   gate <name> <type> <delay> <setup> <hold>
 *   connect <source> <dest> [wire_delay]
 *   pi <name>
 *   po <name>
 *
 * Example:
 *   circuit counter
 *   clock clk 1.0 0.5
 *   register ff1 clk 20 10 10 5
 *   register ff2 clk 20 10 10 5
 *   gate mux1 MUXF 15 8 4
 *   connect ff1.q mux1.a
 *   connect mux1.y ff2.d
 */

#include "timing_analysis.h"

/*
 * trim_whitespace - Remove leading and trailing whitespace from a string
 *
 * Modifies the string in place and returns a pointer to the trimmed start.
 */
static char *trim_whitespace(char *str) {
    char *end;

    /* Trim leading space */
    while (*str == ' ' || *str == '\t' || *str == '\n' || *str == '\r') {
        str++;
    }

    /* Empty string */
    if (*str == 0) {
        return str;
    }

    /* Trim trailing space */
    end = str + strlen(str) - 1;
    while (end > str && (*end == ' ' || *end == '\t' || *end == '\n' || *end == '\r')) {
        end--;
    }

    /* Null-terminate */
    end[1] = '\0';

    return str;
}

/*
 * find_gate_by_name - Find a gate index by name
 *
 * Searches the netlist's gate table for a gate with the given name.
 *
 * Returns: Gate index (0-based), or -1 if not found
 */
static int find_gate_by_name(const Netlist *nl, const char *name) {
    for (int i = 0; i < nl->gate_count; i++) {
        if (strcmp(nl->gates[i].name, name) == 0) {
            return i;
        }
    }
    return -1;
}

/*
 * find_register_by_name - Find a register index by name
 *
 * Searches the netlist's register table for a register with the given name.
 *
 * Returns: Register index (0-based), or -1 if not found
 */
static int find_register_by_name(const Netlist *nl, const char *name) {
    for (int i = 0; i < nl->register_count; i++) {
        if (strcmp(nl->registers[i].name, name) == 0) {
            return i;
        }
    }
    return -1;
}

/*
 * parse_netlist - Parse a circuit netlist from a string
 *
 * Parses the text-based netlist format and populates the Netlist structure.
 * This function handles all netlist elements: circuit name, clocks, registers,
 * gates, connections, and primary I/O.
 *
 * The parsing follows a line-by-line approach, identifying each line's
 * command type and extracting the relevant parameters.
 *
 * Returns: 0 on success, -1 on error
 */
int parse_netlist(Netlist *nl, const char *netlist_text) {
    char *text = strdup(netlist_text);
    char *line = strtok(text, "\n");
    char command[64];
    int ret;

    /* Initialize netlist */
    memset(nl, 0, sizeof(Netlist));
    nl->gate_count = 0;
    nl->register_count = 0;
    nl->net_count = 0;
    nl->port_count = 0;
    nl->clock_count = 0;

    while (line != NULL) {
        line = trim_whitespace(line);

        /* Skip empty lines and comments */
        if (line[0] == '\0' || line[0] == '#') {
            line = strtok(NULL, "\n");
            continue;
        }

        /* Parse command */
        ret = sscanf(line, "%63s", command);
        if (ret != 1) {
            line = strtok(NULL, "\n");
            continue;
        }

        if (strcmp(command, "circuit") == 0) {
            /* Parse circuit name */
            char name[64];
            sscanf(line, "%*s %63s", name);
            strncpy(nl->name, name, sizeof(nl->name) - 1);
            nl->name[sizeof(nl->name) - 1] = '\0';

        } else if (strcmp(command, "clock") == 0) {
            /* Parse clock definition: clock <name> <period_ns> <duty_cycle> */
            if (nl->clock_count >= MAX_CLOCKS) {
                fprintf(stderr, "Error: Too many clocks (max %d)\n", MAX_CLOCKS);
                free(text);
                return -1;
            }
            ClockDef *clk = &nl->clocks[nl->clock_count];
            sscanf(line, "%*s %63s %lf %lf",
                   clk->name, &clk->period, &clk->duty_cycle);
            /* Convert period from ns to ps */
            clk->period = ns_to_ps(clk->period);
            clk->edge_offset = 0.0;
            clk->skew = 0.0;
            clk->is_global = (nl->clock_count == 0) ? 1 : 0;
            clk->register_count = 0;
            nl->clock_count++;

        } else if (strcmp(command, "register") == 0) {
            /* Parse register definition: register <name> <clock> <ccq_max> <ccq_min> <setup> <hold> */
            if (nl->register_count >= MAX_NODES) {
                fprintf(stderr, "Error: Too many registers (max %d)\n", MAX_NODES);
                free(text);
                return -1;
            }
            nl->registers[nl->register_count].name[0] = '\0';
            nl->registers[nl->register_count].clock_name[0] = '\0';
            sscanf(line, "%*s %63s %63s %lf %lf %lf %lf",
                   nl->registers[nl->register_count].name,
                   nl->registers[nl->register_count].clock_name,
                   &nl->registers[nl->register_count].ccq_max,
                   &nl->registers[nl->register_count].ccq_min,
                   &nl->registers[nl->register_count].setup,
                   &nl->registers[nl->register_count].hold);
            /* Convert delays from ns to ps */
            nl->registers[nl->register_count].ccq_max = ns_to_ps(nl->registers[nl->register_count].ccq_max);
            nl->registers[nl->register_count].ccq_min = ns_to_ps(nl->registers[nl->register_count].ccq_min);
            nl->registers[nl->register_count].setup = ns_to_ps(nl->registers[nl->register_count].setup);
            nl->registers[nl->register_count].hold = ns_to_ps(nl->registers[nl->register_count].hold);
            nl->registers[nl->register_count].is_init_reg = 0;
            nl->registers[nl->register_count].gate_index = nl->register_count;
            nl->register_count++;

        } else if (strcmp(command, "gate") == 0) {
            /* Parse gate definition: gate <name> <type> <delay_ns> <setup> <hold> */
            if (nl->gate_count >= MAX_GATES) {
                fprintf(stderr, "Error: Too many gates (max %d)\n", MAX_GATES);
                free(text);
                return -1;
            }
            GateDelay *gate = &nl->gates[nl->gate_count];
            sscanf(line, "%*s %63s %63s %lf %lf %lf",
                   gate->name, gate->type_name,
                   &gate->input_to_output_delay,
                   &gate->setup_time, &gate->hold_time);
            /* Convert delays from ns to ps */
            gate->input_to_output_delay = ns_to_ps(gate->input_to_output_delay);
            gate->setup_time = ns_to_ps(gate->setup_time);
            gate->hold_time = ns_to_ps(gate->hold_time);
            gate->capacitance = 0.0;
            nl->gate_count++;

        } else if (strcmp(command, "connect") == 0) {
            /* Parse net connection: connect <source> <dest> [wire_delay_ns] */
            if (nl->net_count >= MAX_NETLIST) {
                fprintf(stderr, "Error: Too many nets (max %d)\n", MAX_NETLIST);
                free(text);
                return -1;
            }
            nl->nets[nl->net_count].name[0] = '\0';
            nl->nets[nl->net_count].source[0] = '\0';
            nl->nets[nl->net_count].dest[0] = '\0';
            nl->nets[nl->net_count].wire_delay = 0.0;
            sscanf(line, "%*s %63s %63s %lf",
                   nl->nets[nl->net_count].name,
                   nl->nets[nl->net_count].source,
                   nl->nets[nl->net_count].dest,
                   &nl->nets[nl->net_count].wire_delay);
            /* Convert wire delay from ns to ps */
            nl->nets[nl->net_count].wire_delay = ns_to_ps(nl->nets[nl->net_count].wire_delay);
            nl->net_count++;

        } else if (strcmp(command, "pi") == 0) {
            /* Parse primary input: pi <name> */
            if (nl->port_count >= MAX_PORTS) {
                fprintf(stderr, "Error: Too many ports (max %d)\n", MAX_PORTS);
                free(text);
                return -1;
            }
            nl->ports[nl->port_count].name[0] = '\0';
            sscanf(line, "%*s %63s", nl->ports[nl->port_count].name);
            nl->ports[nl->port_count].type = 0; /* PI */
            nl->port_count++;

        } else if (strcmp(command, "po") == 0) {
            /* Parse primary output: po <name> */
            if (nl->port_count >= MAX_PORTS) {
                fprintf(stderr, "Error: Too many ports (max %d)\n", MAX_PORTS);
                free(text);
                return -1;
            }
            nl->ports[nl->port_count].name[0] = '\0';
            sscanf(line, "%*s %63s", nl->ports[nl->port_count].name);
            nl->ports[nl->port_count].type = 1; /* PO */
            nl->port_count++;

        } else if (strcmp(command, "init_reg") == 0) {
            /* Parse init register: init_reg <name> <clock> <ccq_max> <ccq_min> <setup> <hold> */
            if (nl->register_count >= MAX_NODES) {
                fprintf(stderr, "Error: Too many registers (max %d)\n", MAX_NODES);
                free(text);
                return -1;
            }
            nl->registers[nl->register_count].name[0] = '\0';
            nl->registers[nl->register_count].clock_name[0] = '\0';
            sscanf(line, "%*s %63s %63s %lf %lf %lf %lf",
                   nl->registers[nl->register_count].name,
                   nl->registers[nl->register_count].clock_name,
                   &nl->registers[nl->register_count].ccq_max,
                   &nl->registers[nl->register_count].ccq_min,
                   &nl->registers[nl->register_count].setup,
                   &nl->registers[nl->register_count].hold);
            nl->registers[nl->register_count].ccq_max = ns_to_ps(nl->registers[nl->register_count].ccq_max);
            nl->registers[nl->register_count].ccq_min = ns_to_ps(nl->registers[nl->register_count].ccq_min);
            nl->registers[nl->register_count].setup = ns_to_ps(nl->registers[nl->register_count].setup);
            nl->registers[nl->register_count].hold = ns_to_ps(nl->registers[nl->register_count].hold);
            nl->registers[nl->register_count].is_init_reg = 1;
            nl->registers[nl->register_count].gate_index = nl->register_count;
            nl->register_count++;
        }

        line = strtok(NULL, "\n");
    }

    free(text);
    return 0;
}

/*
 * parse_netlist_file - Parse a netlist from a file
 *
 * Reads the entire file into a string and calls parse_netlist().
 *
 * Returns: 0 on success, -1 on error
 */
int parse_netlist_file(Netlist *nl, const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open file '%s'\n", filename);
        return -1;
    }

    fseek(fp, 0, SEEK_END);
    long fsize = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    char *text = malloc(fsize + 1);
    fread(text, 1, fsize, fp);
    text[fsize] = '\0';

    fclose(fp);

    int ret = parse_netlist(nl, text);
    free(text);

    return ret;
}
