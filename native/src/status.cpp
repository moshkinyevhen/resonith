#include "resonith/status.h"

extern "C" const char* resonith_status_string(resonith_status status) {
    switch (status) {
    case RESONITH_STATUS_OK:
        return "ok";
    case RESONITH_STATUS_INVALID_ARGUMENT:
        return "invalid argument";
    case RESONITH_STATUS_TRUNCATED:
        return "truncated";
    case RESONITH_STATUS_BAD_MAGIC:
        return "bad magic";
    case RESONITH_STATUS_UNSUPPORTED_VERSION:
        return "unsupported version";
    case RESONITH_STATUS_CHECKSUM_MISMATCH:
        return "checksum mismatch";
    case RESONITH_STATUS_PROFILE_BOUND:
        return "profile bound";
    case RESONITH_STATUS_MALFORMED:
        return "malformed";
    case RESONITH_STATUS_OUTPUT_TOO_SMALL:
        return "output too small";
    case RESONITH_STATUS_SCRATCH_TOO_SMALL:
        return "scratch too small";
    case RESONITH_STATUS_HASH_MISMATCH:
        return "hash mismatch";
    case RESONITH_STATUS_NOT_FOUND:
        return "not found";
    case RESONITH_STATUS_UNSUPPORTED_FEATURE:
        return "unsupported feature";
    }
    return "unknown status";
}
