/**
 * ota_state_machine.c - OTA Update State Machine
 *
 * The OTA update process is modeled as a finite state machine (FSM).
 * This ensures orderly progression through update stages and proper
 * error handling at each step.
 *
 * State Diagram:
 *
 *   [IDLE] --> [CHECKING] --> [DOWNLOADING] --> [VERIFYING]
 *                                                |
 *           [FAILED] <-- [ROLLBACK] <-- [FLASHING]
 *                ^            |
 *                |            v
 *                +-- [REBOOTING] --> [COMPLETE]
 *
 * State transitions:
 *   IDLE -> CHECKING: Start firmware check
 *   CHECKING -> DOWNLOADING: New firmware available
 *   CHECKING -> IDLE: No update needed
 *   DOWNLOADING -> VERIFYING: Download complete
 *   DOWNLOADING -> FAILED: Download error
 *   VERIFYING -> FLASHING: Verification passed
 *   VERIFYING -> FAILED: Verification failed
 *   FLASHING -> REBOOTING: Flash write complete
 *   FLASHING -> ROLLBACK: Flash error
 *   REBOOTING -> COMPLETE: Reboot successful
 *   REBOOTING -> ROLLBACK: Boot failed
 *   ROLLBACK -> IDLE: Rollback complete
 *   COMPLETE -> IDLE: Update cycle complete
 */

#include "ota_firmware.h"
#include <string.h>

/* Initialize state machine */
void ota_state_machine_init(OTA_StateMachine *sm) {
    if (!sm) return;
    sm->current_state = OTA_STATE_IDLE;
    sm->last_state = OTA_STATE_IDLE;
    sm->error_code = OTA_STATUS_OK;
    sm->progress = 0.0f;
    sm->start_time = 0;
    sm->end_time = 0;
}

/* Set state machine to a new state */
void ota_state_machine_set_state(OTA_StateMachine *sm, ota_state_t state) {
    if (!sm) return;
    sm->last_state = sm->current_state;
    sm->current_state = state;
}

/* Convert state to human-readable string */
const char *ota_state_to_string(ota_state_t state) {
    switch (state) {
        case OTA_STATE_IDLE:          return "IDLE";
        case OTA_STATE_CHECKING:      return "CHECKING";
        case OTA_STATE_DOWNLOADING:   return "DOWNLOADING";
        case OTA_STATE_VERIFYING:     return "VERIFYING";
        case OTA_STATE_FLASHING:      return "FLASHING";
        case OTA_STATE_REBOOTING:     return "REBOOTING";
        case OTA_STATE_ROLLBACK:      return "ROLLBACK";
        case OTA_STATE_COMPLETE:      return "COMPLETE";
        case OTA_STATE_FAILED:        return "FAILED";
        default:                      return "UNKNOWN";
    }
}
