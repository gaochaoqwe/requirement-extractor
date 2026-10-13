#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include "common.h"

typedef struct {
    u8* data;
    u32 capacity;
    u32 head;
    u32 tail;
    u32 size;
} ring_buffer_t;

err_t rb_init(ring_buffer_t* rb, u8* backing, u32 capacity);
err_t rb_push(ring_buffer_t* rb, u8 v);
err_t rb_pop(ring_buffer_t* rb, u8* out);
u32 rb_size(const ring_buffer_t* rb);

#endif
