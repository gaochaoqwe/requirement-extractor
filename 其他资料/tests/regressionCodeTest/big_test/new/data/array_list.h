#ifndef ARRAY_LIST_H
#define ARRAY_LIST_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    void** data;
    size_t size;
    size_t capacity;
    size_t element_size;
} ArrayList;

// Creation and destruction
ArrayList* arraylist_create(size_t element_size);
void arraylist_destroy(ArrayList* list);

// Size operations
size_t arraylist_size(const ArrayList* list);
size_t arraylist_capacity(const ArrayList* list);
bool arraylist_empty(const ArrayList* list);

// Element access
void* arraylist_get(const ArrayList* list, size_t index);
bool arraylist_set(ArrayList* list, size_t index, const void* element);

// Modification operations
bool arraylist_add(ArrayList* list, const void* element);
bool arraylist_insert(ArrayList* list, size_t index, const void* element);
bool arraylist_remove(ArrayList* list, size_t index);
void arraylist_clear(ArrayList* list);

// Search operations
int arraylist_find(const ArrayList* list, const void* element, 
                   int (*compare)(const void*, const void*));
bool arraylist_contains(const ArrayList* list, const void* element,
                       int (*compare)(const void*, const void*));

// Utility operations
bool arraylist_resize(ArrayList* list, size_t new_capacity);
void arraylist_sort(ArrayList* list, int (*compare)(const void*, const void*));
ArrayList* arraylist_copy(const ArrayList* list);

#ifdef __cplusplus
}
#endif

#endif // ARRAY_LIST_H 