from datetime import date, timedelta


def get_next_week_start(current_date: date) -> date:
    """
    计算当前自然周之后的下一个星期一。

    :param current_date: 用于确定当前自然周的日期。
    :return: 下一个自然周的星期一日期。
    """
    days_until_next_monday = 7 - current_date.weekday()
    return current_date + timedelta(days=days_until_next_monday)