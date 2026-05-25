"""数据接入层（骨架）。

第一版基于 ``akshare`` 拉取 A 股行情、基本面、资金流向等数据；
后期在此抽象统一的 ``DataSource`` 接口，兼容 ``tushare`` 等其他数据源，
并支持本地缓存（Redis / MySQL）与失败重试。

约定模块布局：
    - sources/akshare_source.py
    - sources/tushare_source.py
    - cache.py        : 缓存策略
    - schema.py       : 标准化 DataFrame 列约定
"""
