"""Kelly 公式示例脚本。

包含两种等价计算形式：
- 基于赔率与胜率的形式
- 基于胜/负概率与盈亏比例的广义形式

"""

import random


def kelly_from_odds(b, p):
    """根据赔率 b 与获胜概率 p 计算凯利比例。"""
    return (p * (b + 1) - 1) / b


def kelly(p, q, win_return, lose_return):
    """计算凯利公式（广义形式）。

    Args:
        p (float): 获胜概率
        q (float): 失败概率 (= 1 - p)
        win_return (float): 净利润率
        lose_return (float): 净亏损率
    Returns:
        float: 最大化利润的投资本金占比(%)
    """
    if p < q:
        raise ValueError("胜率小于失败率, 不建议进行投资行为！")
    return (p * win_return - q * lose_return) / win_return * lose_return


def main() -> None:
    """演示使用凯利公式进行多轮模拟。"""
    # b 赔率，p 获胜概率 n 下注次数
    # 赔率计算方式：赚的钱(包含本金) / 亏损的钱
    # pre_money 本金
    # result 投注比例
    b = 5.0
    p = 0.5
    n = 1000
    p, win_return, lose_return = 0.55, 0.1, 0.1
    q = 1 - p
    result = kelly(p, q, win_return, lose_return)
    money = 10
    print(f"本金{money:.4f}\n赔率为{b:.4f}\n胜率为{p:.4f}\n投注比例 {result:.4f}")
    x = [1]
    y = [money]

    for i in range(2, n + 1):
        te = random.random()
        if te <= p:
            money *= 1 + result * (b - 1.0)
        else:
            money *= 1 - result
        x.append(i)
        y.append(money)
        outcome = "猜错" if te > 0.5 else "猜对"
        print(f"概率为{te:.2f} {outcome} 剩余金钱：{money:.2f}")
    print(f"运行{n}次后,最后剩余{money:.2f}")


if __name__ == '__main__':
    main()
