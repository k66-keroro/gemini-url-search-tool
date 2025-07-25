評価クラス
| | | | | |
|---|---|---|---|---|

|Table Name|Field Name|Data Type|Not Null|Default Value|
|getplmitmplntinfo_p100|SAP 評価クラス|REAL|0||
|mara_dl|評価クラス|REAL|0||
|zp128_p100|評価クラス|REAL|0||
|zp128_p300|評価クラス|REAL|0||
|zs65|評価クラス|REAL|0||
|zs65_sss|評価クラス|INTEGER|0||

保管場所
| | | | | |
|---|---|---|---|---|

|Table Name|Field Name|Data Type|Not Null|Default Value|
|kansei*jisseki|保管場所|INTEGER|0||
|kousu_jisseki|保管場所|REAL|0||
|koutei_jisseki|保管場所|REAL|0||
|pp_dl_csv_seisan_yotei|出庫保管場所*指図番号|REAL|0||
|t_5798|出庫保管場所|REAL|0||
|t_8806|出庫保管場所|REAL|0||
|zm114|保管場所|INTEGER|0||
|zm29|保管場所|INTEGER|0||
|zp02|保管場所|REAL|0||
|zp128_p100|出庫保管場所|REAL|0||
|zp128_p100|入庫保管場所|REAL|0||
|zp128_p300|出庫保管場所|REAL|0||
|zp128_p300|入庫保管場所|REAL|0||
|zp138|保管場所|REAL|0||
|zp160|発注保管場所|REAL|0||
|zp173|保管場所|REAL|0||
|zp173_meisai|保管場所|REAL|0||
|zp51n|入庫保管場所|REAL|0||
|zp58|保管場所|REAL|0||
|zp58|構成品目保管場所|REAL|0||
|zp70|保管場所|REAL|0||
|zs58month|倉庫保管料|REAL|0||
|zs61kday|メイン保管場所|REAL|0||
|zs61kday|保管場所|REAL|0||
|zs65_sss|保管場所|INTEGER|0||

勘定科目コード
| | | | | |
|---|---|---|---|---|
|Table Name|Field Name|Data Type|Not Null|Default Value|
|zs65|勘定科目コード|REAL|0||
|zs65_sss|勘定科目コード|INTEGER|0||
|zm21|勘定コード|REAL|0||
|zp128_p100|GL 勘定|REAL|0||
|zp128_p300|GL 勘定|REAL|0||
|zm114|G／L 勘定コード|INTEGER|0||
|zm87n|Ｇ／Ｌ勘定|REAL|0||

受注
| | | | | |
|---|---|---|---|---|

|Table Name|Field Name|Data Type|Not Null|Default Value|
|zp173|販売伝票明細|REAL|0||
|zp173_meisai|販売伝票明細|REAL|0||
|zs65|販売伝票明細|REAL|0||
|zs65_sss|販売伝票明細|REAL|0||
|zp160|販売伝票 ★|REAL|0||
|zp173|販売伝票|REAL|0||
|zp173_meisai|販売伝票|REAL|0||
|zs45|販売伝票|INTEGER|0||
|zs65|販売伝票|REAL|0||
|zs65_sss|販売伝票|REAL|0||
|kansei_jisseki|受注明細番号|INTEGER|0||
|pp_dl_csv_seisan_yotei|受注明細番号|INTEGER|0||
|pp_dl_csv_ztbp110|受注明細番号|INTEGER|0||
|pp_summary_ztbp080_kojozisseki_d_0|受注明細番号|INTEGER|0||
|t_1205|受注明細番号|INTEGER|0||
|zs58month|受注明細番号|INTEGER|0||
|zs61kday|受注明細番号|INTEGER|0||
|zm21|受注番号|REAL|0||
|zp02|受注伝票明細|REAL|0||
|kansei_jisseki|受注伝票番号|INTEGER|0||
|pp_dl_csv_seisan_yotei|受注伝票番号|REAL|0||
|pp_dl_csv_ztbp110|受注伝票番号|REAL|0||
|pp_summary_ztbp080_kojozisseki_d_0|受注伝票番号|REAL|0||
|t_1205|受注伝票番号|INTEGER|0||
|zp02|受注伝票番号|REAL|0||
|zs58month|受注伝票番号|INTEGER|0||
|zs61kday|受注伝票番号|INTEGER|0||

得意先
| | | | | |
|---|---|---|---|---|

|Table Name|Field Name|Data Type|Not Null|Default Value|
|t_1205|得意先コード|INTEGER|0||
|zf26|得意先コード|INTEGER|0||
|zs191|得意先|REAL|0||
|zs58month|出荷先コード|INTEGER|0||
|zs61kday|出荷先コード|INTEGER|0||
|zs58month|エンドユーザコード|REAL|0||
|zs61kday|エンドユーザコード|REAL|0||
|zs191|エンドユーザ|REAL|0||
|zf26|請求先コード|REAL|0||
|zf26|TSR コード|REAL|0||
|zs58month|受注先コード|INTEGER|0||
|zs61kday|受注先コード|INTEGER|0||
|zp160|受注先|REAL|0||

指図 nw wbs
| | | | | |
|---|---|---|---|---|

|Table Name|Field Name|Data Type|Not Null|Default Value|
|kansei*jisseki|指図番号|INTEGER|0||
|kansei_jisseki|WBS 要素|REAL|0||
|zm114|製造指図|REAL|0||
|zp70|指図番号|REAL|0||
|zp51n|子指図番号|REAL|0||
|pp_dl_csv_ztbp110|ネットワーク番号*指図番号*親|REAL|0||
|pp_dl_csv_ztbp110|ネットワーク番号*指図番号|INTEGER|0||
|zs61kday|ネットワーク番号　指図番号|REAL|0||
|zm29|ネットワーク・指図番号|INTEGER|0||
|zs58month|ネットワーク／指図番号|REAL|0||
|zm29|WBS 番号|REAL|0||
|zm21|WBS 要素|INTEGER|0||
|t_5798|親ネットワーク番号|REAL|0||
|t_8806|親ネットワーク番号|REAL|0||
|zm21|ネットワーク|REAL|0||

品目
| | | | | |
|---|---|---|---|---|
|Table Name|Field Name|Data Type|Not Null|Default Value|
|mara_dl|品目|INTEGER|0||
|zp138|品目|INTEGER|0||

購買
| | | | | |
|---|---|---|---|---|

|Table Name|Field Name|Data Type|Not Null|Default Value|
|zp51n|購買発注番号|REAL|0||
|zs61kday|購買発注番号|REAL|0||
|zp160|購買発注 ★|REAL|0||
|zm21|購買発注|REAL|0||
|zp173_meisai|購買発注|REAL|0||
|zs58month|購買伝票明細|INTEGER|0||
|zs61kday|購買伝票明細|INTEGER|0||
|zs58month|購買伝票番号|REAL|0||
|zs61kday|購買伝票番号|REAL|0||
|t_5798|購買伝票|REAL|0||
|t_8806|購買伝票|REAL|0||
|zm87n|購買伝票|INTEGER|0||
|zp58|購買伝票|REAL|0||
|zm87n|購買情報番号|REAL|0||
|zp35|購買情報番号|REAL|0||
|zm21|購買情報|REAL|0||
|zp160|購買依頼明細|INTEGER|0||
|zp160|購買依頼 ★|REAL|0||
|t_5798|購買依頼|REAL|0||
|t_8806|購買依頼|REAL|0||
|zm21|購買依頼|INTEGER|0||
|zp58|購買依頼|REAL|0||
|zm21|購買ｸﾞﾙｰﾌﾟ|INTEGER|0||
|zp128_p100|購買グループ|REAL|0||
|zp128_p300|購買グループ|REAL|0||
|zp35|購買グループ|REAL|0||
|zp70|購買グループ|REAL|0||
|zp70|伝票番号|REAL|0||

入出庫
| | | | | |
|---|---|---|---|---|

|Table Name|Field Name|Data Type|Not Null|Default Value|
|zm114|入出庫予定明細番号|INTEGER|0||
|zm114|入出庫予定番号|INTEGER|0||
|zp138|入出庫予定|INTEGER|0||
|zp58|入出庫予定|INTEGER|0||
|zp58|入出庫明細|INTEGER|0||
|pp_summary_ztbp080_kojozisseki_d_0|入出庫伝票番号|REAL|0||
|zp173_meisai|入出庫伝票番号|REAL|0||
|zp173_meisai|入出庫伝票年|INTEGER|0||
|pp_summary_ztbp080_kojozisseki_d_0|入出庫伝票の明細|INTEGER|0||
|zm29|入出庫伝票|INTEGER|0||
