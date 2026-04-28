"""
アラートレベル算出ロジック
alert_logic_version = 1
"""
from __future__ import annotations
from typing import Optional


def calc_alert_level(
    weight: float,
    breath_condition: int,
    reference_weight: float,
) -> int:
    """
    Args:
        weight: 今日の体重(kg)
        breath_condition: 1=普通 2=ちょっと 3=けっこう 4=とても
        reference_weight: 比較基準体重（3日前 or base_weight）

    Returns:
        0: 入力途絶（この関数では返さない）
        1: 通常
        2: 注意
        3: 警戒
    """
    diff = weight - reference_weight

    # 警戒: 息切れ強い OR 体重+2kg以上
    if breath_condition >= 3 or diff >= 2.0:
        return 3

    # 注意: 息切れ少し OR 体重+1.5kg以上
    if breath_condition == 2 or diff >= 1.5:
        return 2

    return 1


ALERT_EMOJI = {0: "⚪", 1: "🟢", 2: "🟡", 3: "🔴"}
ALERT_LABEL = {0: "入力途絶", 1: "通常", 2: "注意", 3: "警戒"}
ALERT_COLOR_CLASS = {0: "alert-0", 1: "alert-1", 2: "alert-2", 3: "alert-3"}
BREATH_LABEL = {1: "普通", 2: "ちょっと苦しい", 3: "けっこう苦しい", 4: "とても苦しい"}
ALERT_LOGIC_VERSION = 1
