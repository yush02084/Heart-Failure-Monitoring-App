"""
アラート判定ロジックの境界値テスト。
このロジックはプロダクトの安全性に直結するため、
仕様変更時はここのテストを先に書き換えること。
"""
from app.core.alert_logic import calc_alert_level


class TestCalcAlertLevel:
    # ── level 1 (通常) ──
    def test_normal_weight_normal_breath_returns_1(self):
        assert calc_alert_level(weight=65.0, breath_condition=1, reference_weight=65.0) == 1

    def test_weight_loss_normal_breath_returns_1(self):
        assert calc_alert_level(weight=63.0, breath_condition=1, reference_weight=65.0) == 1

    def test_weight_plus_1_4kg_returns_1(self):
        # +1.5kg未満は通常
        assert calc_alert_level(weight=66.4, breath_condition=1, reference_weight=65.0) == 1

    # ── level 2 (注意) ──
    def test_breath_2_returns_2(self):
        assert calc_alert_level(weight=65.0, breath_condition=2, reference_weight=65.0) == 2

    def test_weight_plus_exactly_1_5kg_returns_2(self):
        # 境界: +1.5kg ちょうどは注意 (>=)
        assert calc_alert_level(weight=66.5, breath_condition=1, reference_weight=65.0) == 2

    def test_weight_plus_1_9kg_returns_2(self):
        assert calc_alert_level(weight=66.9, breath_condition=1, reference_weight=65.0) == 2

    # ── level 3 (警戒) ──
    def test_breath_3_returns_3(self):
        assert calc_alert_level(weight=65.0, breath_condition=3, reference_weight=65.0) == 3

    def test_breath_4_returns_3(self):
        assert calc_alert_level(weight=65.0, breath_condition=4, reference_weight=65.0) == 3

    def test_weight_plus_exactly_2_0kg_returns_3(self):
        # 境界: +2.0kg ちょうどは警戒 (>=)
        assert calc_alert_level(weight=67.0, breath_condition=1, reference_weight=65.0) == 3

    def test_weight_plus_2_5kg_returns_3(self):
        assert calc_alert_level(weight=67.5, breath_condition=1, reference_weight=65.0) == 3

    # ── 優先順位 ──
    def test_severe_breath_and_severe_weight_returns_3(self):
        # 両方該当しても 3
        assert calc_alert_level(weight=68.0, breath_condition=4, reference_weight=65.0) == 3

    def test_caution_breath_but_severe_weight_returns_3(self):
        # 体重が警戒域なら息切れが軽くても 3
        assert calc_alert_level(weight=67.0, breath_condition=2, reference_weight=65.0) == 3

    def test_severe_breath_but_normal_weight_returns_3(self):
        # 息切れが警戒域なら体重が正常でも 3
        assert calc_alert_level(weight=64.0, breath_condition=3, reference_weight=65.0) == 3
