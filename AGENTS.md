# FitFlow AI 编码规范

## Python 函数文档字符串

- 函数和方法的说明统一使用中文。
- 使用 Sphinx/reStructuredText 风格，并依次说明功能、参数和返回值。
- 每个对外输入参数使用 `:param 参数名:` 说明；不为 `self` 和 `cls` 单独写参数说明。
- 使用 `:return:` 说明返回结果；返回 `None` 时写明“无返回值”。
- 函数名、参数名、类型名和 API 字段名继续使用英文。

示例：

```python
def calculate_total_cost(price: float, discount: float, tax_rate: float) -> float:
    """
    计算折扣和税费后的总费用。

    :param price: 商品原价。
    :param discount: 折扣比例。
    :param tax_rate: 税率。
    :return: 折扣和税费计算后的总费用。
    """
```
