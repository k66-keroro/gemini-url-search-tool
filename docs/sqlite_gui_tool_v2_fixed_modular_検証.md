`|   |
|---|
|ファイル処理開始: zf26.csv|
|ファイル処理エラー: Error tokenizing data. C error: Expected 1 fields in line 46, saw 2|
||
|Traceback (most recent call last):|
|File "C:\Users\sem3171\claude-test\src\core\sqlite_gui_tool\admin_tab.py", line 724, in _process_single_file|
|df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, dtype=str)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 948, in read_csv|
|return _read(filepath_or_buffer, kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 611, in _read|
|parser = TextFileReader(filepath_or_buffer, **kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1448, in __init__|
|self._engine = self._make_engine(f, self.engine)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1723, in _make_engine|
|return mapping[engine](f, **self.options)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\c_parser_wrapper.py", line 93, in __init__|
|self._reader = parsers.TextReader(src, **kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "parsers.pyx", line 579, in pandas._libs.parsers.TextReader.__cinit__|
|File "parsers.pyx", line 668, in pandas._libs.parsers.TextReader._get_header|
|File "parsers.pyx", line 879, in pandas._libs.parsers.TextReader._tokenize_rows|
|File "parsers.pyx", line 890, in pandas._libs.parsers.TextReader._check_tokenize_status|
|File "parsers.pyx", line 2050, in pandas._libs.parsers.raise_parser_error|
|UnicodeDecodeError: 'shift_jis' codec can't decode byte 0x87 in position 59787: illegal multibyte sequence|
||
|During handling of the above exception, another exception occurred:|
||
|Traceback (most recent call last):|
|File "C:\Users\sem3171\claude-test\src\core\sqlite_gui_tool\admin_tab.py", line 727, in _process_single_file|
|df = pd.read_csv(file_path, encoding='cp932', sep=delimiter, dtype=str)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 948, in read_csv|
|return _read(filepath_or_buffer, kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 617, in _read|
|return parser.read(nrows)|
|^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1748, in read|
|) = self._engine.read(  # type: ignore[attr-defined]|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\c_parser_wrapper.py", line 234, in read|
|chunks = self._reader.read_low_memory(nrows)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "parsers.pyx", line 843, in pandas._libs.parsers.TextReader.read_low_memory|
|File "parsers.pyx", line 904, in pandas._libs.parsers.TextReader._read_rows|
|File "parsers.pyx", line 879, in pandas._libs.parsers.TextReader._tokenize_rows|
|File "parsers.pyx", line 890, in pandas._libs.parsers.TextReader._check_tokenize_status|
|File "parsers.pyx", line 2058, in pandas._libs.parsers.raise_parser_error|
|pandas.errors.ParserError: Error tokenizing data. C error: Expected 1 fields in line 46, saw 2|
||
||
|ファイル処理失敗: zf26.csv|
|   |
|---|
|ファイル処理開始: ZS58MONTH.csv|
|ファイル処理エラー: Error tokenizing data. C error: Expected 1 fields in line 106, saw 7|
||
|Traceback (most recent call last):|
|File "C:\Users\sem3171\claude-test\src\core\sqlite_gui_tool\admin_tab.py", line 724, in _process_single_file|
|df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, dtype=str)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 948, in read_csv|
|return _read(filepath_or_buffer, kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 611, in _read|
|parser = TextFileReader(filepath_or_buffer, **kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1448, in __init__|
|self._engine = self._make_engine(f, self.engine)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1723, in _make_engine|
|return mapping[engine](f, **self.options)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\c_parser_wrapper.py", line 93, in __init__|
|self._reader = parsers.TextReader(src, **kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "parsers.pyx", line 579, in pandas._libs.parsers.TextReader.__cinit__|
|File "parsers.pyx", line 668, in pandas._libs.parsers.TextReader._get_header|
|File "parsers.pyx", line 879, in pandas._libs.parsers.TextReader._tokenize_rows|
|File "parsers.pyx", line 890, in pandas._libs.parsers.TextReader._check_tokenize_status|
|File "parsers.pyx", line 2050, in pandas._libs.parsers.raise_parser_error|
|UnicodeDecodeError: 'shift_jis' codec can't decode byte 0x87 in position 60726: illegal multibyte sequence|
||
|During handling of the above exception, another exception occurred:|
||
|Traceback (most recent call last):|
|File "C:\Users\sem3171\claude-test\src\core\sqlite_gui_tool\admin_tab.py", line 727, in _process_single_file|
|df = pd.read_csv(file_path, encoding='cp932', sep=delimiter, dtype=str)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 948, in read_csv|
|return _read(filepath_or_buffer, kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 617, in _read|
|return parser.read(nrows)|
|^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1748, in read|
|) = self._engine.read(  # type: ignore[attr-defined]|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\c_parser_wrapper.py", line 234, in read|
|chunks = self._reader.read_low_memory(nrows)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "parsers.pyx", line 843, in pandas._libs.parsers.TextReader.read_low_memory|
|File "parsers.pyx", line 904, in pandas._libs.parsers.TextReader._read_rows|
|File "parsers.pyx", line 879, in pandas._libs.parsers.TextReader._tokenize_rows|
|File "parsers.pyx", line 890, in pandas._libs.parsers.TextReader._check_tokenize_status|
|File "parsers.pyx", line 2058, in pandas._libs.parsers.raise_parser_error|
|pandas.errors.ParserError: Error tokenizing data. C error: Expected 1 fields in line 106, saw 7|
||
||
|ファイル処理失敗: ZS58MONTH.csv|
|ファイル処理開始: ZS61KDAY.csv|
|ファイル処理エラー: Error tokenizing data. C error: Expected 1 fields in line 23, saw 4|
||
|Traceback (most recent call last):|
|File "C:\Users\sem3171\claude-test\src\core\sqlite_gui_tool\admin_tab.py", line 724, in _process_single_file|
|df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, dtype=str)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 948, in read_csv|
|return _read(filepath_or_buffer, kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 611, in _read|
|parser = TextFileReader(filepath_or_buffer, **kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1448, in __init__|
|self._engine = self._make_engine(f, self.engine)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1723, in _make_engine|
|return mapping[engine](f, **self.options)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\c_parser_wrapper.py", line 93, in __init__|
|self._reader = parsers.TextReader(src, **kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "parsers.pyx", line 579, in pandas._libs.parsers.TextReader.__cinit__|
|File "parsers.pyx", line 668, in pandas._libs.parsers.TextReader._get_header|
|File "parsers.pyx", line 879, in pandas._libs.parsers.TextReader._tokenize_rows|
|File "parsers.pyx", line 890, in pandas._libs.parsers.TextReader._check_tokenize_status|
|File "parsers.pyx", line 2050, in pandas._libs.parsers.raise_parser_error|
|UnicodeDecodeError: 'shift_jis' codec can't decode byte 0x87 in position 53279: illegal multibyte sequence|
||
|During handling of the above exception, another exception occurred:|
||
|Traceback (most recent call last):|
|File "C:\Users\sem3171\claude-test\src\core\sqlite_gui_tool\admin_tab.py", line 727, in _process_single_file|
|df = pd.read_csv(file_path, encoding='cp932', sep=delimiter, dtype=str)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 948, in read_csv|
|return _read(filepath_or_buffer, kwds)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 617, in _read|
|return parser.read(nrows)|
|^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\readers.py", line 1748, in read|
|) = self._engine.read(  # type: ignore[attr-defined]|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\io\parsers\c_parser_wrapper.py", line 234, in read|
|chunks = self._reader.read_low_memory(nrows)|
|^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^|
|File "parsers.pyx", line 843, in pandas._libs.parsers.TextReader.read_low_memory|
|File "parsers.pyx", line 904, in pandas._libs.parsers.TextReader._read_rows|
|File "parsers.pyx", line 879, in pandas._libs.parsers.TextReader._tokenize_rows|
|File "parsers.pyx", line 890, in pandas._libs.parsers.TextReader._check_tokenize_status|
|File "parsers.pyx", line 2058, in pandas._libs.parsers.raise_parser_error|
|pandas.errors.ParserError: Error tokenizing data. C error: Expected 1 fields in line 23, saw 4|
||
||
|ファイル処理失敗: ZS61KDAY.csv|`