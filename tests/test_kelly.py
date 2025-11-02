"""Kelly公式测试用例"""

import pytest
from src.kelly import kelly, kelly_from_odds


class TestKellyFormula:
    """Kelly公式测试类"""

    def test_kelly_from_odds_basic(self):
        """测试基本赔率计算方法"""
        b = 2.0  # 赔率
        p = 0.6  # 胜率60%
        result = kelly_from_odds(b, p)
        assert result == (0.6 * (2 + 1) - 1) / 2

    def test_kelly_from_odds_zero_odds(self):
        """测试赔率为0的情况"""
        result = kelly_from_odds(1.0, 0.5)
        assert result == 0

    def test_kelly_basic(self):
        """测试基本Kelly公式"""
        p = 0.55
        q = 0.45
        win_return = 0.1
        lose_return = 0.1
        result = kelly(p, q, win_return, lose_return)
        assert isinstance(result, float)

    def test_kelly_positive_expectation(self):
        """测试正期望值场景"""
        p = 0.6
        q = 0.4
        win_return = 0.2
        lose_return = 0.1
        result = kelly(p, q, win_return, lose_return)
        assert result > 0

    def test_kelly_negative_expectation(self):
        """测试负期望值场景（应该抛出异常）"""
        p = 0.4
        q = 0.6
        win_return = 0.1
        lose_return = 0.2
        with pytest.raises(ValueError, match="胜率小于失败率"):
            kelly(p, q, win_return, lose_return)

    def test_kelly_zero_edge(self):
        """测试边界情况"""
        p = 0.5
        q = 0.5
        win_return = 0.1
        lose_return = 0.1
        result = kelly(p, q, win_return, lose_return)
        assert result == 0

    def test_kelly_high_win_rate(self):
        """测试高胜率场景"""
        p = 0.8
        q = 0.2
        win_return = 0.15
        lose_return = 0.1
        result = kelly(p, q, win_return, lose_return)
        assert 0 < result < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
