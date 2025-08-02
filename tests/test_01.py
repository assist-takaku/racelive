""" ---------------------------------------------------------------------------------------------------------

poetry run streamlit run tests/test_01.py

----------------------------------------------------------------------------------------------------------"""

import streamlit as st
from streamlit.column_config import Column
import pandas as pd

# 例となるデータフレームを作成
data = {'col1': ['data1', 'data2', 'data3'],
        'col2': ['data4', 'data5', 'data6'],
        'col3': ['data7', 'data8', 'data9']}
df = pd.DataFrame(data)


# 列の設定
column_config = {
    'col1': st.column_config.TextColumn(
        'Column 1',
        width='medium',
    ),
    'col2': st.column_config.TextColumn(
        'Column 2',
        width='medium',
    ),
    'col3': st.column_config.TextColumn(
        'Column 3',
        width='medium',
    ),
}


# データフレームを表示
st.dataframe(df, column_config=column_config, use_container_width=True)


# 複数行表示の例 (TextColumnの代わりに特定のフォーマットを使用)
column_config_multi_line = {
    'col1': st.column_config.TextColumn(
        'Column 1',
        width='medium',
        help="複数行表示の例1",
    ),
    'col2': st.column_config.TextColumn(
        'Column 2',
        width='medium',
        help="複数行表示の例2",
    ),
    'col3': st.column_config.TextColumn(
        'Column 3',
        width='medium',
        help="複数行表示の例3",
    ),
}

st.dataframe(df, column_config=column_config_multi_line, use_container_width=True)

