#include "diag.h"

u32 diag_u32_saturating_add(u32 a, u32 b)
{
    u32 r = a + b;
    if (r < a) {
        return 0xFFFFFFFFu;
    }
    return r;
}

int diag_is_ascii_printable(const char* s)
{
    u32 i = 0u;
    if (s == 0) {
        return 0;
    }
    while (s[i] != '\0') {
        unsigned char c = (unsigned char)s[i];
        if (c < 32u || c > 126u) {
            return 0;
        }
        i++;
    }
    return 1;
}
