"""口径回归测试：概览计数必须与各模块列表取到的真实条目一致。

跑法：backend/.venv/bin/python -m pytest（需安装 pytest），
或直接 backend/.venv/bin/python -m app.tests.test_caliber。
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.catalog import MODULE_SPECS
from app.main import app

client = TestClient(app)

# 示例数据固定数字：任何机器、任何时间启动都应当一致
EXPECTED_CARDS = {
    "业务模块": 18,
    "今日新增": 54,
    "待处理": 54,
    "异常量": 7,
}


def _overview() -> dict:
    return client.get("/api/overview").json()


def test_overview_cards_are_deterministic() -> None:
    cards = {card["label"]: card["value"] for card in _overview()["cards"]}
    assert cards == EXPECTED_CARDS


def test_overview_pending_matches_module_lists() -> None:
    overview = {row["name"]: row for row in _overview()["modules"]}
    for key, spec in MODULE_SPECS.items():
        data = client.get(f"/api/{key}", params={"size": 200}).json()
        items = data["items"]
        # 待处理 = 状态不是末态的条目，与列表里 pending 标记完全一致
        pending_items = [item for item in items if item["status"] != spec.terminal_status]
        assert all(item["pending"] for item in pending_items)
        assert not any(
            item["pending"] for item in items if item["status"] == spec.terminal_status
        )
        assert len(pending_items) == overview[key]["pending"]
        abnormal_items = [
            item for item in items if item["status"] in spec.abnormal_statuses
        ]
        assert len(abnormal_items) == overview[key]["abnormal"]


def test_every_pending_row_reachable_through_status_filter() -> None:
    for key, spec in MODULE_SPECS.items():
        data = client.get(f"/api/{key}", params={"size": 200}).json()
        for item in data["items"]:
            if item["status"] == spec.terminal_status:
                continue
            filtered = client.get(f"/api/{key}", params={"status": item["status"]}).json()
            assert any(row["id"] == item["id"] for row in filtered["items"])


def test_empty_filter_params_return_full_list() -> None:
    # 前端空输入框会序列化成 keyword=&status=，不能把列表过滤成空
    data = client.get("/api/section", params={"keyword": "", "status": ""}).json()
    assert data["total"] == 3


def test_list_response_carries_stats() -> None:
    data = client.get("/api/section").json()
    labels = [item["label"] for item in data["stats"]]
    assert labels == ["在用区段", "限速区段", "封闭区段"]
    assert sum(item["value"] for item in data["stats"]) >= 0


if __name__ == "__main__":
    test_overview_cards_are_deterministic()
    test_overview_pending_matches_module_lists()
    test_every_pending_row_reachable_through_status_filter()
    test_empty_filter_params_return_full_list()
    test_list_response_carries_stats()
    print("caliber tests passed")
