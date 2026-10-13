/**
 * @file map_loader.h
 * @brief 地图数据加载接口
 */

#ifndef MAP_LOADER_H
#define MAP_LOADER_H

/**
 * @brief 加载地图瓦片
 * @param lat 纬度
 * @param lon 经度
 * @return 0表示成功，非0表示失败
 */
int load_map_tiles(double lat, double lon);

#endif // MAP_LOADER_H

