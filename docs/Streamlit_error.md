`2025-07-28 08:55:02.941 Serialization of dataframe to Arrow table was unsuccessful. Applying automatic fixes for column types to make the dataframe Arrow-compatible.
Traceback (most recent call last):
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\streamlit\dataframe_util.py", line 821, in convert_pandas_df_to_arrow_bytes
    table = pa.Table.from_pandas(df)
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\table.pxi", line 4623, in pyarrow.lib.Table.from_pandas
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in dataframe_to_arrays
    arrays = [convert_column(c, f)
             ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in <listcomp>
    arrays = [convert_column(c, f)
              ^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 603, in convert_column
    raise e
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 597, in convert_column
    result = pa.array(col, type=type_, from_pandas=True, safe=safe)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\array.pxi", line 358, in pyarrow.lib.array
  File "pyarrow\\array.pxi", line 85, in pyarrow.lib._ndarray_to_array
  File "pyarrow\\error.pxi", line 92, in pyarrow.lib.check_status
pyarrow.lib.ArrowInvalid: ("Could not convert '合計' with type str: tried to convert to int64", 'Conversion failed for column 週区分 with type object')
2025-07-28 08:55:42.668 Serialization of dataframe to Arrow table was unsuccessful. Applying automatic fixes for column types to make the dataframe Arrow-compatible.
Traceback (most recent call last):
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\streamlit\dataframe_util.py", line 821, in convert_pandas_df_to_arrow_bytes
    table = pa.Table.from_pandas(df)
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\table.pxi", line 4623, in pyarrow.lib.Table.from_pandas
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in dataframe_to_arrays
    arrays = [convert_column(c, f)
             ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in <listcomp>
    arrays = [convert_column(c, f)
              ^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 603, in convert_column
    raise e
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 597, in convert_column
    result = pa.array(col, type=type_, from_pandas=True, safe=safe)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\array.pxi", line 358, in pyarrow.lib.array
  File "pyarrow\\array.pxi", line 85, in pyarrow.lib._ndarray_to_array
  File "pyarrow\\error.pxi", line 92, in pyarrow.lib.check_status
pyarrow.lib.ArrowInvalid: ("Could not convert '合計' with type str: tried to convert to int64", 'Conversion failed for column 週区分 with type object')
2025-07-28 08:55:44.673 Serialization of dataframe to Arrow table was unsuccessful. Applying automatic fixes for column types to make the dataframe Arrow-compatible.
Traceback (most recent call last):
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\streamlit\dataframe_util.py", line 821, in convert_pandas_df_to_arrow_bytes
    table = pa.Table.from_pandas(df)
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\table.pxi", line 4623, in pyarrow.lib.Table.from_pandas
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in dataframe_to_arrays
    arrays = [convert_column(c, f)
             ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in <listcomp>
    arrays = [convert_column(c, f)
              ^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 603, in convert_column
    raise e
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 597, in convert_column
    result = pa.array(col, type=type_, from_pandas=True, safe=safe)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\array.pxi", line 358, in pyarrow.lib.array
  File "pyarrow\\array.pxi", line 85, in pyarrow.lib._ndarray_to_array
  File "pyarrow\\error.pxi", line 92, in pyarrow.lib.check_status
pyarrow.lib.ArrowInvalid: ("Could not convert '合計' with type str: tried to convert to int64", 'Conversion failed for column 週区分 with type object')
2025-07-28 08:56:23.747 Serialization of dataframe to Arrow table was unsuccessful. Applying automatic fixes for column types to make the dataframe Arrow-compatible.
Traceback (most recent call last):
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\streamlit\dataframe_util.py", line 821, in convert_pandas_df_to_arrow_bytes
    table = pa.Table.from_pandas(df)
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\table.pxi", line 4623, in pyarrow.lib.Table.from_pandas
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in dataframe_to_arrays
    arrays = [convert_column(c, f)
             ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in <listcomp>
    arrays = [convert_column(c, f)
              ^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 603, in convert_column
    raise e
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 597, in convert_column
    result = pa.array(col, type=type_, from_pandas=True, safe=safe)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\array.pxi", line 358, in pyarrow.lib.array
  File "pyarrow\\array.pxi", line 85, in pyarrow.lib._ndarray_to_array
  File "pyarrow\\error.pxi", line 92, in pyarrow.lib.check_status
pyarrow.lib.ArrowInvalid: ("Could not convert '合計' with type str: tried to convert to int64", 'Conversion failed for column 週区分 with type object')
2025-07-28 08:56:26.740 Serialization of dataframe to Arrow table was unsuccessful. Applying automatic fixes for column types to make the dataframe Arrow-compatible.
Traceback (most recent call last):
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\streamlit\dataframe_util.py", line 821, in convert_pandas_df_to_arrow_bytes
    table = pa.Table.from_pandas(df)
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\table.pxi", line 4623, in pyarrow.lib.Table.from_pandas
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in dataframe_to_arrays
    arrays = [convert_column(c, f)
             ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 616, in <listcomp>
    arrays = [convert_column(c, f)
              ^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 603, in convert_column
    raise e
  File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyarrow\pandas_compat.py", line 597, in convert_column
    result = pa.array(col, type=type_, from_pandas=True, safe=safe)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pyarrow\\array.pxi", line 358, in pyarrow.lib.array
  File "pyarrow\\array.pxi", line 85, in pyarrow.lib._ndarray_to_array
  File "pyarrow\\error.pxi", line 92, in pyarrow.lib.check_status
pyarrow.lib.ArrowInvalid: ("Could not convert '合計' with type str: tried to convert to int64", 'Conversion failed for column 週区分 with type object')`
