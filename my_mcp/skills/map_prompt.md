# 地图能力

你已接入 **高德地图 MCP Server**，可使用与路线、地点、POI 等相关的工具。

## 重要：路线规划工具的参数格式

**所有路线规划类工具**（`maps_direction_driving`、`maps_direction_transit_integrated`、`maps_direction_walking`、`maps_bicycling` 等）的 `origin` 和 `destination` 参数**必须是经纬度坐标**，格式为 `"经度,纬度"`（例如：`"116.397128,39.916527"`），**不能直接使用地址文字**。

## 使用流程

当用户询问**驾车/公交/步行路线、导航、怎么去**时：

1. **如果用户提供的是地址文字**（如"育新地铁站"、"清华大学"）：
   - **先调用地理编码工具**（`maps_regeocode` 或 `maps_geo`）将地址转换为经纬度坐标
   - 从地理编码结果中提取 `lon`（经度）和 `lat`（纬度）
   - 将坐标格式化为 `"lon,lat"` 字符串（例如：`"116.397128,39.916527"`）
   - **再用坐标调用路线规划工具**（如 `maps_direction_transit_integrated`），将格式化后的坐标字符串作为 `origin` 和 `destination` 参数

2. **如果用户已提供经纬度坐标**：
   - 直接使用坐标调用路线规划工具

3. **如果工具返回 `INVALID_PARAMS` 错误**：
   - 检查 `origin` 和 `destination` 是否为 `"经度,纬度"` 格式
   - 如果不是坐标格式，先调用地理编码工具获取坐标，再重试路线规划

## 其他工具

- 用户询问**地点搜索、周边、POI**时，使用搜索/地理编码类工具（`maps_text_search`、`maps_around_search`、`maps_regeocode` 等）。
- 这些工具通常接受地址文字作为输入，无需预先转换。
