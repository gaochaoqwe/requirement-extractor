/**
 * @file gps_receiver.h
 * @brief GPS数据接收接口
 */

#ifndef GPS_RECEIVER_H
#define GPS_RECEIVER_H

// GPS数据结构
typedef struct {
    double latitude;      // 纬度
    double longitude;     // 经度
    float altitude;       // 海拔
    float speed;          // 速度 (km/h)
    float direction;      // 方向 (度)
    int satellite_count;  // 卫星数量
    int valid;            // 数据有效标志
    unsigned long timestamp;  // 时间戳
} GPSData;

/**
 * @brief 启动GPS接收器
 * @return 0表示成功，非0表示失败
 */
int gps_receiver_start(void);

/**
 * @brief 停止GPS接收器
 */
void gps_receiver_stop(void);

/**
 * @brief 接收GPS数据
 * @param data GPS数据结构指针
 * @return 0表示成功，非0表示失败
 */
int gps_receive_data(GPSData *data);

/**
 * @brief 更新当前位置
 * @param data GPS数据
 */
void update_current_position(GPSData *data);

#endif // GPS_RECEIVER_H

