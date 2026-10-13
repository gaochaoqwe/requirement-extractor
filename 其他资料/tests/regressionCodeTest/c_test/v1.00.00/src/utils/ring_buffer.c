#include "ring_buffer.h"

err_t rb_init(ring_buffer_t* rb, u8* backing, u32 capacity)
{
    if (rb == 0 || backing == 0 || capacity == 0u) {
        return ERR_INVALID_ARG;
    }
    rb->data = backing;
    rb->capacity = capacity;
    rb->head = 0u;
    rb->tail = 0u;
    rb->size = 0u;
    return ERR_OK;
}

err_t rb_push(ring_buffer_t* rb, u8 v)
{
    if (rb == 0 || rb->data == 0) {
        return ERR_INVALID_ARG;
    }
    if (rb->size >= rb->capacity) {
        return ERR_OVERFLOW;
    }

    rb->data[rb->head] = v;
    rb->head = (rb->head + 1u) % rb->capacity;
    rb->size++;
    return ERR_OK;
}

err_t rb_pop(ring_buffer_t* rb, u8* out)
{
    if (rb == 0 || rb->data == 0 || out == 0) {
        return ERR_INVALID_ARG;
    }
    if (rb->size == 0u) {
        return ERR_UNDERFLOW;
    }

    *out = rb->data[rb->tail];
    rb->tail = (rb->tail + 1u) % rb->capacity;
    rb->size--;
    return ERR_OK;
}

u32 rb_size(const ring_buffer_t* rb)
{
    if (rb == 0) {
        return 0u;
    }
    return rb->size;
}
