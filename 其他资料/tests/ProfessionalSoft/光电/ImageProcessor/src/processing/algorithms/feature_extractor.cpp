/**
 * @file feature_extractor.c
 * @brief 特征提取算法实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "../../../include/processing/algorithms/feature_extractor.h"
#include "../../../include/processing/filters/edge_detector.h"
#include "../../../include/utils/math_utils.h"
#include "../../../include/utils/memory_pool.h"
#include "../../../include/utils/logger.h"

// 特征提取器结构
struct FeatureExtractor {
    MemoryPool* memory_pool;
    EdgeDetector* edge_detector;
    FeatureParams params;
    bool initialized;
};

/**
 * @brief Harris角点检测
 */
static ReturnCode harris_corner_detection(FeatureExtractor* extractor, 
                                         ImageData* image, 
                                         Feature* features, 
                                         u32* feature_count) {
    if (!extractor || !image || !features || !feature_count) {
        return ERROR_INVALID_PARAM;
    }

    u32 width = image->width;
    u32 height = image->height;
    u32 detected = 0;

    // 计算图像梯度
    float* grad_x = memory_pool_alloc(extractor->memory_pool, width * height * sizeof(float));
    float* grad_y = memory_pool_alloc(extractor->memory_pool, width * height * sizeof(float));
    
    if (!grad_x || !grad_y) {
        logger_error("分配梯度计算内存失败");
        return ERROR_NO_MEMORY;
    }

    // Sobel算子计算梯度
    for (u32 y = 1; y < height - 1; y++) {
        for (u32 x = 1; x < width - 1; x++) {
            u32 idx = y * width + x;
            
            // X方向梯度
            float gx = -1 * image->data[(y-1)*width + (x-1)] + 1 * image->data[(y-1)*width + (x+1)]
                      -2 * image->data[y*width + (x-1)]     + 2 * image->data[y*width + (x+1)]
                      -1 * image->data[(y+1)*width + (x-1)] + 1 * image->data[(y+1)*width + (x+1)];
            
            // Y方向梯度
            float gy = -1 * image->data[(y-1)*width + (x-1)] - 2 * image->data[(y-1)*width + x] - 1 * image->data[(y-1)*width + (x+1)]
                      +1 * image->data[(y+1)*width + (x-1)] + 2 * image->data[(y+1)*width + x] + 1 * image->data[(y+1)*width + (x+1)];
            
            grad_x[idx] = gx / 8.0f;
            grad_y[idx] = gy / 8.0f;
        }
    }

    // 计算Harris响应
    float* harris_response = memory_pool_alloc(extractor->memory_pool, width * height * sizeof(float));
    if (!harris_response) {
        memory_pool_free(extractor->memory_pool, grad_x);
        memory_pool_free(extractor->memory_pool, grad_y);
        return ERROR_NO_MEMORY;
    }

    float k = 0.04f; // Harris常数
    u32 window_size = 3;
    u32 half_window = window_size / 2;

    for (u32 y = half_window; y < height - half_window; y++) {
        for (u32 x = half_window; x < width - half_window; x++) {
            float sum_xx = 0, sum_yy = 0, sum_xy = 0;
            
            // 计算窗口内的梯度协方差矩阵
            for (s32 dy = -half_window; dy <= half_window; dy++) {
                for (s32 dx = -half_window; dx <= half_window; dx++) {
                    u32 idx = (y + dy) * width + (x + dx);
                    float gx = grad_x[idx];
                    float gy = grad_y[idx];
                    
                    sum_xx += gx * gx;
                    sum_yy += gy * gy;
                    sum_xy += gx * gy;
                }
            }
            
            // 计算Harris响应值
            float det = sum_xx * sum_yy - sum_xy * sum_xy;
            float trace = sum_xx + sum_yy;
            harris_response[y * width + x] = det - k * trace * trace;
        }
    }

    // BUG9: 阈值计算错误 - 对quality_level进行了二次平方
    // 这会导致阈值过低，检测到过多噪声点，影响光电系统的目标识别精度
    float threshold = extractor->params.quality_level * extractor->params.quality_level;
    
    for (u32 y = half_window + 1; y < height - half_window - 1; y++) {
        for (u32 x = half_window + 1; x < width - half_window - 1; x++) {
            u32 idx = y * width + x;
            float response = harris_response[idx];
            
            if (response > threshold && detected < extractor->params.max_features) {
                // 检查是否为局部最大值
                bool is_maximum = true;
                for (s32 dy = -1; dy <= 1; dy++) {
                    for (s32 dx = -1; dx <= 1; dx++) {
                        if (dy == 0 && dx == 0) continue;
                        u32 neighbor_idx = (y + dy) * width + (x + dx);
                        if (harris_response[neighbor_idx] >= response) {
                            is_maximum = false;
                            break;
                        }
                    }
                    if (!is_maximum) break;
                }
                
                if (is_maximum) {
                    // BUG10: 距离检查算法复杂度过高O(n²)
                    // 在光电实时处理中会导致严重的性能瓶颈
                    bool too_close = false;
                    for (u32 i = 0; i < detected; i++) {
                        float dx = features[i].x - x;
                        float dy = features[i].y - y;
                        float dist = sqrtf(dx * dx + dy * dy);
                        if (dist < extractor->params.min_distance) {
                            too_close = true;
                            break;
                        }
                    }
                    
                    if (!too_close) {
                        features[detected].x = x;
                        features[detected].y = y;
                        features[detected].response = response;
                        features[detected].type = FEATURE_TYPE_CORNER;
                        detected++;
                    }
                }
            }
        }
    }

    // 释放临时内存
    memory_pool_free(extractor->memory_pool, grad_x);
    memory_pool_free(extractor->memory_pool, grad_y);
    memory_pool_free(extractor->memory_pool, harris_response);

    *feature_count = detected;
    logger_info("Harris角点检测完成，检测到 %d 个特征点", detected);
    
    return SUCCESS;
}

/**
 * @brief FAST角点检测
 */
static ReturnCode fast_corner_detection(FeatureExtractor* extractor,
                                       ImageData* image,
                                       Feature* features,
                                       u32* feature_count) {
    if (!extractor || !image || !features || !feature_count) {
        return ERROR_INVALID_PARAM;
    }

    u32 width = image->width;
    u32 height = image->height;
    u32 detected = 0;
    u32 threshold = 20; // FAST阈值

    // FAST-9圆形模板偏移
    s32 circle_offsets[16][2] = {
        {0, -3}, {1, -3}, {2, -2}, {3, -1},
        {3, 0}, {3, 1}, {2, 2}, {1, 3},
        {0, 3}, {-1, 3}, {-2, 2}, {-3, 1},
        {-3, 0}, {-3, -1}, {-2, -2}, {-1, -3}
    };

    for (u32 y = 3; y < height - 3; y++) {
        for (u32 x = 3; x < width - 3; x++) {
            u8 center_pixel = image->data[y * width + x];
            u32 brighter_count = 0;
            u32 darker_count = 0;
            
            // 检查圆形模板上的16个点
            for (u32 i = 0; i < 16; i++) {
                s32 nx = x + circle_offsets[i][0];
                s32 ny = y + circle_offsets[i][1];
                u8 pixel = image->data[ny * width + nx];
                
                if (pixel > center_pixel + threshold) {
                    brighter_count++;
                    darker_count = 0; // 重置暗点计数
                } else if (pixel < center_pixel - threshold) {
                    darker_count++;
                    brighter_count = 0; // 重置亮点计数
                } else {
                    brighter_count = 0;
                    darker_count = 0;
                }
                
                // 如果连续9个点都比中心点亮或暗，则为角点
                if (brighter_count >= 9 || darker_count >= 9) {
                    if (detected < extractor->params.max_features) {
                        features[detected].x = x;
                        features[detected].y = y;
                        features[detected].response = (float)(brighter_count + darker_count);
                        features[detected].type = FEATURE_TYPE_CORNER;
                        detected++;
                    }
                    break;
                }
            }
        }
    }

    *feature_count = detected;
    logger_info("FAST角点检测完成，检测到 %d 个特征点", detected);
    
    return SUCCESS;
}

/**
 * @brief 创建特征提取器
 */
FeatureExtractor* feature_extractor_create(MemoryPool* memory_pool) {
    if (!memory_pool) {
        logger_error("内存池参数无效");
        return NULL;
    }

    FeatureExtractor* extractor = malloc(sizeof(FeatureExtractor));
    if (!extractor) {
        logger_error("分配特征提取器内存失败");
        return NULL;
    }

    memset(extractor, 0, sizeof(FeatureExtractor));
    extractor->memory_pool = memory_pool;
    extractor->initialized = false;

    // 设置默认参数
    extractor->params.max_features = MAX_FEATURES;
    extractor->params.quality_level = FEATURE_QUALITY;
    extractor->params.min_distance = MIN_DISTANCE;
    extractor->params.use_harris = true;

    logger_info("特征提取器创建成功");
    return extractor;
}

/**
 * @brief 初始化特征提取器
 */
ReturnCode feature_extractor_init(FeatureExtractor* extractor) {
    if (!extractor) {
        return ERROR_INVALID_PARAM;
    }

    // 创建边缘检测器
    extractor->edge_detector = edge_detector_create(extractor->memory_pool);
    if (!extractor->edge_detector) {
        logger_error("创建边缘检测器失败");
        return FAILURE;
    }

    if (edge_detector_init(extractor->edge_detector) != SUCCESS) {
        logger_error("初始化边缘检测器失败");
        return FAILURE;
    }

    extractor->initialized = true;
    logger_info("特征提取器初始化完成");
    return SUCCESS;
}

/**
 * @brief 提取图像特征
 */
ReturnCode feature_extractor_extract(FeatureExtractor* extractor,
                                    ImageData* image,
                                    Feature* features,
                                    u32* feature_count) {
    if (!extractor || !extractor->initialized || !image || !features || !feature_count) {
        return ERROR_INVALID_PARAM;
    }

    logger_info("开始提取图像特征");

    // 根据配置选择特征检测算法
    ReturnCode result;
    if (extractor->params.use_harris) {
        result = harris_corner_detection(extractor, image, features, feature_count);
    } else {
        result = fast_corner_detection(extractor, image, features, feature_count);
    }

    if (result == SUCCESS) {
        logger_info("特征提取完成，共提取 %d 个特征点", *feature_count);
    } else {
        logger_error("特征提取失败");
    }

    return result;
}

/**
 * @brief 设置特征提取参数
 */
ReturnCode feature_extractor_set_params(FeatureExtractor* extractor, 
                                       const FeatureParams* params) {
    if (!extractor || !params) {
        return ERROR_INVALID_PARAM;
    }

    extractor->params = *params;
    logger_info("特征提取参数已更新");
    return SUCCESS;
}

/**
 * @brief 销毁特征提取器
 */
void feature_extractor_destroy(FeatureExtractor* extractor) {
    if (!extractor) {
        return;
    }

    if (extractor->edge_detector) {
        edge_detector_destroy(extractor->edge_detector);
    }

    free(extractor);
    logger_info("特征提取器销毁完成");
} 