-- 由 sintef/vrptw/convert_sintef_vrptw.py 生成。
-- 只做 KNN 构造并快照：测试用例不依赖 ALNS 的随机迭代，求解快且可复现。
function solve()
    construct_knn({ neighbor_count = 8 })
    alns({ worker_count = 4,
           max_iter = 100,
           max_sub_iter = 20,
           max_unimproved_iter = 500,
           print_operator_statistics = true,
           max_stagnate_iter = 5,
           operator_weight_update_interval_iter = 5,
           ruin_operator_params = { { code = "RuinRandomRemovalLoad", params = { select_load_min_rate = 0.0001, select_load_max_rate = 0.01 } },
                                    { code = "RuinRandomRemovalLoad", params = { select_load_min_rate = 0.01, select_load_max_rate = 0.25 } },
                                    { code = "RuinRandomRemovalOrder", params = { select_order_min_rate = 0.0001, select_order_max_rate = 0.1 } },
                                    { code = "RuinRandomRemovalOrder", params = { select_order_min_rate = 0.1, select_order_max_rate = 0.3 } },
                                    { code = "RuinWorstRemovalOrder", params = { select_order_min_rate = 0.0001, select_order_max_rate = 0.1 } },
                                    { code = "RuinWorstRemovalOrder", params = { select_order_min_rate = 0.1, select_order_max_rate = 0.3 } }
           },
           repair_operator_params = {
               { code = "RepairGreedy" },
               { code = "RepairGreedy", params = { top_rate = 0.0001 } },
               { code = "RepairRegretK" },
               { code = "RepairRegretK", params = { regret_k = 3 } },
           },
           local_search = {
               max_evaluated = 300,
               improvement = "first",
           }
    })

    local_search({ improvement = "best" })
end
