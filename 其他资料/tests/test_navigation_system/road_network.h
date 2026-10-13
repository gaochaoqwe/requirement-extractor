/**
 * @file road_network.h
 * @brief 道路网络数据接口
 */

#ifndef ROAD_NETWORK_H
#define ROAD_NETWORK_H

/**
 * @brief 加载道路网络数据
 * @return 0表示成功，非0表示失败
 */
int load_road_network(void);

/**
 * @brief 卸载道路网络数据
 */
void unload_road_network(void);

#endif // ROAD_NETWORK_H

