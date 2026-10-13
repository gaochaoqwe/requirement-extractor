#include "helper.h"
 
int perform(int v) {
    return doubleValue(v) + 1; // cross-file call to helper.cpp
} 