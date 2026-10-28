# SINTEF Homberger C1_2_1 测试夹具

由 [`scripts/convert_sintef_vrptw.py`](../../../scripts/convert_sintef_vrptw.py) 从
SINTEF TOP 的 200-customers 实例 `C1_2_1.TXT` 生成，表结构沿用 yunpyopt 既有的
CSV 夹具格式（`Location.csv`、`CargoOrder.csv`、`CargoSubOrder.csv` 等）。

## 来源

- 实例：`C1_2_1.TXT`（Homberger 200 customers，50 vehicles，capacity 200）
- 页面：<https://www.sintef.no/projectweb/top/vrptw/200-customers/>

## 映射约定

| 实例字段 | 案例字段 |
| --- | --- |
| `XCOORD.` / `YCOORD.` | `Location.Lng` / `Location.Lat`（平面坐标直填，路由只用 `DistMatrix`） |
| `DEMAND` | `CargoSubOrderDimensionValue.weight` |
| `CAPACITY` | `VehicleModelDimensionValue.weight` |
| `READY TIME` / `DUE DATE` | `CargoOrder.EarliestDropDateTime` / `LatestDropDateTime`，基准时间 `2026-01-01 00:00`，1 单位 = 1 分钟 |
| `SERVICE TIME` | `WorkFixed.FixedDropTime`（秒，`90 min = 5400 s`） |
| 车场 | `DEPOT`，订单从 `DEPOT` 提货、送到客户 |
| 距离/时间 | `Distance = 欧氏距离 × 1000`（米），`Time = 欧氏距离 × 60`（秒） |

## 与原始实例的差异

1. **车辆数 60（原始 50）**：当前 KNN 构造在 50 辆时只能装载 195 单，且未分配列表
   仍为空；夹具留出余量，保证 200 单全部可分配。
2. **ORD056 的最晚卸货时间放宽到 22:31（车场 due）**：yun 以“最晚客户 due”作为
   计划结束时间；放宽这一单后，计划结束时间才能保持在车场关闭时间 1351 min，
   从而保留 VRPTW 的“车辆在车场关闭前回场”语义。

重新生成：

```bash
python scripts/convert_sintef_vrptw.py /path/to/C1_2_1.TXT tests/data/c1_2_1 --vehicles 60
```
