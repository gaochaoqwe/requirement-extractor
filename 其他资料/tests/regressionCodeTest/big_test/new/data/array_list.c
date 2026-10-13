#include "array_list.h"
#include <stdlib.h>
#include <string.h>

#define INITIAL_CAPACITY 8
#define GROWTH_FACTOR 2

// Creation and destruction
ArrayList* arraylist_create(size_t element_size) {
    ArrayList* list = malloc(sizeof(ArrayList));
    if (!list) return NULL;
    
    list->data = malloc(INITIAL_CAPACITY * sizeof(void*));
    if (!list->data) {
        free(list);
        return NULL;
    }
    
    list->size = 0;
    list->capacity = INITIAL_CAPACITY;
    list->element_size = element_size;
    
    return list;
}

void arraylist_destroy(ArrayList* list) {
    if (!list) return;
    
    arraylist_clear(list);
    free(list->data);
    free(list);
}

// Size operations
size_t arraylist_size(const ArrayList* list) {
    return list ? list->size : 0;
}

size_t arraylist_capacity(const ArrayList* list) {
    return list ? list->capacity : 0;
}

bool arraylist_empty(const ArrayList* list) {
    return list ? (list->size == 0) : true;
}

// Element access
void* arraylist_get(const ArrayList* list, size_t index) {
    if (!list || index >= list->size) return NULL;
    return list->data[index];
}

bool arraylist_set(ArrayList* list, size_t index, const void* element) {
    if (!list || index >= list->size || !element) return false;
    
    if (list->data[index]) {
        free(list->data[index]);
    }
    
    list->data[index] = malloc(list->element_size);
    if (!list->data[index]) return false;
    
    memcpy(list->data[index], element, list->element_size);
    return true;
}

// Modification operations
bool arraylist_add(ArrayList* list, const void* element) {
    if (!list || !element) return false;
    
    if (list->size >= list->capacity) {
        if (!arraylist_resize(list, list->capacity * GROWTH_FACTOR)) {
            return false;
        }
    }
    
    list->data[list->size] = malloc(list->element_size);
    if (!list->data[list->size]) return false;
    
    memcpy(list->data[list->size], element, list->element_size);
    list->size++;
    
    return true;
}

bool arraylist_insert(ArrayList* list, size_t index, const void* element) {
    if (!list || !element || index > list->size) return false;
    
    if (list->size >= list->capacity) {
        if (!arraylist_resize(list, list->capacity * GROWTH_FACTOR)) {
            return false;
        }
    }
    
    // Shift elements to the right
    for (size_t i = list->size; i > index; i--) {
        list->data[i] = list->data[i - 1];
    }
    
    list->data[index] = malloc(list->element_size);
    if (!list->data[index]) return false;
    
    memcpy(list->data[index], element, list->element_size);
    list->size++;
    
    return true;
}

bool arraylist_remove(ArrayList* list, size_t index) {
    if (!list || index >= list->size) return false;
    
    if (list->data[index]) {
        free(list->data[index]);
    }
    
    // Shift elements to the left
    for (size_t i = index; i < list->size - 1; i++) {
        list->data[i] = list->data[i + 1];
    }
    
    list->size--;
    return true;
}

void arraylist_clear(ArrayList* list) {
    if (!list) return;
    
    for (size_t i = 0; i < list->size; i++) {
        if (list->data[i]) {
            free(list->data[i]);
            list->data[i] = NULL;
        }
    }
    
    list->size = 0;
}

// Search operations
int arraylist_find(const ArrayList* list, const void* element, 
                   int (*compare)(const void*, const void*)) {
    if (!list || !element || !compare) return -1;
    
    for (size_t i = 0; i < list->size; i++) {
        if (compare(list->data[i], element) == 0) {
            return (int)i;
        }
    }
    
    return -1;
}

bool arraylist_contains(const ArrayList* list, const void* element,
                       int (*compare)(const void*, const void*)) {
    return arraylist_find(list, element, compare) != -1;
}

// Utility operations
bool arraylist_resize(ArrayList* list, size_t new_capacity) {
    if (!list || new_capacity < list->size) return false;
    
    void** new_data = realloc(list->data, new_capacity * sizeof(void*));
    if (!new_data) return false;
    
    list->data = new_data;
    list->capacity = new_capacity;
    
    return true;
}

void arraylist_sort(ArrayList* list, int (*compare)(const void*, const void*)) {
    if (!list || !compare || list->size <= 1) return;
    
    qsort(list->data, list->size, sizeof(void*), compare);
}

ArrayList* arraylist_copy(const ArrayList* list) {
    if (!list) return NULL;
    
    ArrayList* copy = arraylist_create(list->element_size);
    if (!copy) return NULL;
    
    for (size_t i = 0; i < list->size; i++) {
        if (!arraylist_add(copy, list->data[i])) {
            arraylist_destroy(copy);
            return NULL;
        }
    }
    
    return copy;
} 