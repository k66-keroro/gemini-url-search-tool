`  URL: http://localhost:8502

────────────────────────── Traceback (most recent call last) ───────────────────────────
  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\streamlit
  \runtime\scriptrunner\exec_code.py:128 in exec_func_with_error_handling

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\streamlit
  \runtime\scriptrunner\script_runner.py:669 in code_to_exec

  C:\Users\sem3171\claude-test\pc-production-dashboard\app\dashboard.py:511 in
  <module>

    508 │   )
    509
    510 if __name__ == "__main__":
  ❱ 511 │   main()
    512

  C:\Users\sem3171\claude-test\pc-production-dashboard\app\dashboard.py:502 in main

    499 │
    500 │   # 最終更新時刻の表示
    501 │   if '更新時刻' in df.columns and not df['更新時刻'].isna().all():
  ❱ 502 │   │   latest_update = df['更新時刻'].max()
    503 │   │   st.markdown(f"**最終データ更新**: {latest_update}")
    504 │
    505 │   st.markdown(

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\co
  re\series.py:6189 in max

    6186 │   │   numeric_only: bool = False,
    6187 │   │   **kwargs,
    6188 │   ):
  ❱ 6189 │   │   return NDFrame.max(self, axis, skipna, numeric_only, **kwargs)
    6190 │
    6191 │   @doc(make_doc("sum", ndim=1))
    6192 │   def sum(

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\co
  re\generic.py:11962 in max

    11959 │   │   numeric_only: bool_t = False,
    11960 │   │   **kwargs,
    11961 │   ):
  ❱ 11962 │   │   return self._stat_function(
    11963 │   │   │   "max",
    11964 │   │   │   nanops.nanmax,
    11965 │   │   │   axis,

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\co
  re\generic.py:11935 in _stat_function

    11932 │   │
    11933 │   │   validate_bool_kwarg(skipna, "skipna", none_allowed=False)
    11934 │   │
  ❱ 11935 │   │   return self._reduce(
    11936 │   │   │   func, name=name, axis=axis, skipna=skipna, numeric_only=numeric_
    11937 │   │   )
    11938

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\co
  re\series.py:6129 in _reduce

    6126 │   │   │   │   │   f"Series.{name} does not allow {kwd_name}={numeric_only}
    6127 │   │   │   │   │   "with non-numeric dtypes."
    6128 │   │   │   │   )
  ❱ 6129 │   │   │   return op(delegate, skipna=skipna, **kwds)
    6130 │
    6131 │   @Appender(make_doc("any", ndim=1))
    6132 │   # error: Signature of "any" incompatible with supertype "NDFrame"

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\co
  re\nanops.py:147 in f

     144 │   │   │   │   else:
     145 │   │   │   │   │   result = alt(values, axis=axis, skipna=skipna, **kwds)
     146 │   │   │   else:
  ❱  147 │   │   │   │   result = alt(values, axis=axis, skipna=skipna, **kwds)
     148 │   │   │
     149 │   │   │   return result
     150

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\co
  re\nanops.py:404 in new_func

     401 │   │   if datetimelike and mask is None:
     402 │   │   │   mask = isna(values)
     403 │   │
  ❱  404 │   │   result = func(values, axis=axis, skipna=skipna, mask=mask, **kwargs)
     405 │   │
     406 │   │   if datetimelike:
     407 │   │   │   result = _wrap_results(result, orig_values.dtype, fill_value=iNaT

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas\co
  re\nanops.py:1092 in reduction

    1089 │   │   values, mask = _get_values(
    1090 │   │   │   values, skipna, fill_value_typ=fill_value_typ, mask=mask
    1091 │   │   )
  ❱ 1092 │   │   result = getattr(values, meth)(axis)
    1093 │   │   result = _maybe_null_out(result, axis, mask, values.shape)
    1094 │   │   return result
    1095

  C:\Users\sem3171\AppData\Local\Programs\Python\Python311\Lib\site-packages\numpy\cor
  e\_methods.py:41 in _amax

     38 # small reductions
     39 def _amax(a, axis=None, out=None, keepdims=False,
     40 │   │     initial=_NoValue, where=True):
  ❱  41 │   return umr_maximum(a, axis, None, out, keepdims, initial, where)
     42
     43 def _amin(a, axis=None, out=None, keepdims=False,
     44 │   │     initial=_NoValue, where=True):
────────────────────────────────────────────────────────────────────────────────────────
TypeError: '>=' not supported between instances of 'str' and 'float'`





