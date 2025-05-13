#include "util.h"

long util_GetFileSize(FILE* file) {
    long currPos = ftell(file);
    fseek(file, 0, SEEK_END);
    long len = ftell(file);
    fseek(file, currPos, SEEK_SET);
    return len;
}
