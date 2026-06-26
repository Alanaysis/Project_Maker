"""
ARM Exception Handling Module
==============================

Implements basic exception handling for the ARM simulator.

ARM Architecture Background:
ARM has multiple exception modes, each with its own register bank:
- Reset: System starts here
- Undefined Instruction: Invalid/undefined instruction executed
- Software Interrupt (SWI/SVC): Supervisor call for OS services
- Prefetch Abort: Instruction fetch to invalid address
- Data Abort: Data access to invalid address
- IRQ: Interrupt Request (normal interrupt)
- FIQ: Fast Interrupt Request (priority interrupt)

Exception entry:
1. CPSR saved to SPSR_<mode>
2. CPSR mode bits changed to exception mode
3. PC set to exception vector (0x00000000-0x0000001C)
4. T bit cleared (switch to ARM mode for exception handler)

Exception return:
1. CPSR restored from SPSR_<mode>
2. PC set to LR_exception - 4
3. Processor returns to previous mode
"""


class ExceptionType:
    """ARM exception types"""
    RESET = "RESET"
    UNDEFINED_INSTRUCTION = "UNDEFINED_INSTRUCTION"
    SOFTWARE_INTERRUPT = "SOFTWARE_INTERRUPT"
    PREFETCH_ABORT = "PREFETCH_ABORT"
    DATA_ABORT = "DATA_ABORT"
    IRQ = "IRQ"
    FIQ = "FIQ"


class Exception:
    """Represents an ARM exception"""

    def __init__(self, exc_type, address=0, instruction=0):
        self.type = exc_type
        self.address = address  # Address that caused the exception
        self.instruction = instruction  # Instruction that caused the exception
        self.timestamp = 0  # For tracking exception order

    def __repr__(self):
        return f"Exception({self.type}, addr=0x{self.address:08X})"


class ExceptionHandler:
    """
    ARM exception handler

    Manages exception processing including:
    - Mode switching
    - Register state saving/restoring
    - Exception vector handling
    """

    # Exception vector addresses
    EXCEPTION_VECTORS = {
        ExceptionType.RESET: 0x00000000,
        ExceptionType.UNDEFINED_INSTRUCTION: 0x00000004,
        ExceptionType.SOFTWARE_INTERRUPT: 0x00000008,
        ExceptionType.PREFETCH_ABORT: 0x0000000C,
        ExceptionType.DATA_ABORT: 0x00000010,
        ExceptionType.IRQ: 0x00000018,
        ExceptionType.FIQ: 0x0000001C,
    }

    # Exception mode bits for CPSR
    EXCEPTION_MODES = {
        ExceptionType.RESET: 0x13,       # SVC mode
        ExceptionType.UNDEFINED_INSTRUCTION: 0x1B,  # Undefined mode
        ExceptionType.SOFTWARE_INTERRUPT: 0x13,  # SVC mode
        ExceptionType.PREFETCH_ABORT: 0x17,  # Abort mode
        ExceptionType.DATA_ABORT: 0x17,  # Abort mode
        ExceptionType.IRQ: 0x12,  # IRQ mode
        ExceptionType.FIQ: 0x11,  # FIQ mode
    }

    def __init__(self):
        self.exception_log = []
        self.exception_count = 0
        self.in_exception = False

    def handle_exception(self, cpu, exc_type, address=0, instruction=0):
        """
        Handle an ARM exception.

        Args:
            cpu: The ARM CPU simulator instance
            exc_type: Exception type (ExceptionType constant)
            address: Address that caused the exception
            instruction: Instruction that caused the exception

        Returns:
            True if exception was handled, False if fatal
        """
        self.exception_count += 1
        exc = Exception(exc_type, address, instruction)
        exc.timestamp = self.exception_count
        self.exception_log.append(exc)

        if exc_type == ExceptionType.RESET:
            return self._handle_reset(cpu)
        elif exc_type == ExceptionType.UNDEFINED_INSTRUCTION:
            return self._handle_undefined(cpu, address, instruction)
        elif exc_type == ExceptionType.SOFTWARE_INTERRUPT:
            return self._handle_swi(cpu, instruction)
        elif exc_type == ExceptionType.DATA_ABORT:
            return self._handle_data_abort(cpu, address)
        elif exc_type == ExceptionType.PREFETCH_ABORT:
            return self._handle_prefetch_abort(cpu, address)
        elif exc_type == ExceptionType.IRQ:
            return self._handle_irq(cpu)
        elif exc_type == ExceptionType.FIQ:
            return self._handle_fiq(cpu)

        return False

    def _handle_reset(self, cpu):
        """Handle reset exception - start execution at address 0"""
        cpu.regs.set_pc(0x00000000)
        cpu.regs.cpsr.value = (cpu.regs.cpsr.value & ~cpu.regs.cpsr.MODE_MASK) | 0x13
        self.in_exception = True
        return True

    def _handle_undefined(self, cpu, address, instruction):
        """Handle undefined instruction exception"""
        # Save current state
        cpu.regs.save_spsr("UND")

        # Switch to undefined mode
        cpsr = cpu.regs.cpsr
        cpsr.value = (cpsr.value & ~cpsr.MODE_MASK) | 0x1B
        cpsr.value &= ~cpsr.T_FLAG  # Switch to ARM mode

        # Save LR_und
        cpu.regs.set_lr(cpu.regs.get_pc() - 4)

        # Jump to undefined instruction vector
        cpu.regs.set_pc(0x00000004)
        self.in_exception = True
        return True

    def _handle_swi(self, cpu, instruction):
        """Handle software interrupt (SVC) exception"""
        # Save current state
        cpu.regs.save_spsr("SVC")

        # Switch to SVC mode
        cpsr = cpu.regs.cpsr
        cpsr.value = (cpsr.value & ~cpsr.MODE_MASK) | 0x13
        cpsr.value &= ~cpsr.T_FLAG  # Switch to ARM mode

        # Save LR_svc (return address)
        lr = cpu.regs.get_lr()
        cpu.regs.set_lr(lr & ~0x1F)  # Clear mode bits

        # Jump to SVC vector
        cpu.regs.set_pc(0x00000008)
        self.in_exception = True
        return True

    def _handle_data_abort(self, cpu, address):
        """Handle data abort exception"""
        cpu.regs.save_spsr("ABT")

        cpsr = cpu.regs.cpsr
        cpsr.value = (cpsr.value & ~cpsr.MODE_MASK) | 0x17
        cpsr.value &= ~cpsr.T_FLAG

        cpu.regs.set_lr(cpu.regs.get_pc() - 4)
        cpu.regs.set_pc(0x00000010)
        self.in_exception = True
        return True

    def _handle_prefetch_abort(self, cpu, address):
        """Handle prefetch abort exception"""
        cpu.regs.save_spsr("ABT")

        cpsr = cpu.regs.cpsr
        cpsr.value = (cpsr.value & ~cpsr.MODE_MASK) | 0x17
        cpsr.value &= ~cpsr.T_FLAG

        cpu.regs.set_lr(cpu.regs.get_pc() - 4)
        cpu.regs.set_pc(0x0000000C)
        self.in_exception = True
        return True

    def _handle_irq(self, cpu):
        """Handle IRQ exception"""
        cpu.regs.save_spsr("IRQ")

        cpsr = cpu.regs.cpsr
        cpsr.value = (cpsr.value & ~cpsr.MODE_MASK) | 0x12
        cpsr.value &= ~cpsr.T_FLAG

        cpu.regs.set_lr(cpu.regs.get_pc() - 4)
        cpu.regs.set_pc(0x00000018)
        self.in_exception = True
        return True

    def _handle_fiq(self, cpu):
        """Handle FIQ exception"""
        cpu.regs.save_spsr("FIQ")

        cpsr = cpu.regs.cpsr
        cpsr.value = (cpsr.value & ~cpsr.MODE_MASK) | 0x11
        cpsr.value &= ~cpsr.T_FLAG

        cpu.regs.set_lr(cpu.regs.get_pc() - 4)
        cpu.regs.set_pc(0x0000001C)
        self.in_exception = True
        return True

    def exception_return(self, cpu):
        """
        Return from exception.

        Restores CPSR from SPSR and sets PC to LR - 4.
        """
        mode = cpu.regs.cpsr.mode
        mode_name = self._mode_to_name(mode)

        if mode_name in cpu.regs.spsr:
            cpu.regs.restore_spsr(mode_name)

        lr = cpu.regs.get_lr()
        # Return address is LR - 4 (for most exceptions)
        if mode == 0x12 or mode == 0x11:  # IRQ or FIQ
            cpu.regs.set_pc(lr - 4)
        else:
            cpu.regs.set_pc(lr - 8)  # For SVC, ABT, UND

        self.in_exception = False
        return True

    def _mode_to_name(self, mode):
        """Convert mode bits to name"""
        mode_names = {
            0x10: "USER", 0x11: "FIQ", 0x12: "IRQ",
            0x13: "SVC", 0x17: "ABT", 0x1B: "UND", 0x1F: "SYS"
        }
        return mode_names.get(mode, "UNKNOWN")

    def get_exception_log(self):
        """Return the exception log"""
        return self.exception_log

    def clear_exception_log(self):
        """Clear the exception log"""
        self.exception_log = []
        self.exception_count = 0
