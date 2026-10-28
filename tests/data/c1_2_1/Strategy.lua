-- 由 scripts/convert_sintef_vrptw.py 生成。
-- 只做 KNN 构造并快照：测试用例不依赖 ALNS 的随机迭代，求解快且可复现。
function solve()
    local parameter = KnnParameter()
    parameter.neighbor_count = 12
    construct_knn(parameter)
    alns({ worker_count = 4, max_iter = 100,
           ruin_operator_params = { { code = "RuinRandomRemovalLoad" }, { code = "RuinRandomRemovalOrder" } },
           repair_operator_params = {
               { code = "RepairGreedy" },
               { code = "RepairGreedy", params = { top_rate = 0.0001 } },
               { code = "RepairRegretK" },
               { code = "RepairRegretK", params = { regret_k = 3 } },
           } })
end
