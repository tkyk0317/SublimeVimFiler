SublimeVimFiler
===============

vimプラグイン「VimFiler」を元に、同等機能を
sublime-textで使用するためのプラグインです。

## 機能
* ディレクトリを移動できる
1. ファイルをオープンできる
2. 事前に指定したプログラムで「PDF/CHM/WORD/EXCEL/POWERPOINT/MindMap」を開くことができる
3. カレントディレクトリ直下のファイル/ディレクトリを検索できる
4. 検索後のファイル/ディレクトリを開くことができる。
5. ファイル/デイレクトリにマークをつけ、一括コピーまたは削除ができる
6. ソート順を切り替えることができる
7. ドットで始まるファイル/ディレクトリの表示/非表示を切り替えることができる

## 制限事項
1. サポートしているプラットフォームはLinuxのみ
2. 複数SublimeVimFilerを起動することはできない

## 設定項目
* pdf
    PDFファイルを開くプログラムを指定
* office
    WORD/EXCEL/POWERPOINTを開くプログラムを指定
* mind_mao
    マインドマップファイルを開くプログラムを指定
* mind_map_ex
    マインドマップファイルの拡張子を指定
* chm
    CHMファイルを開くプログラムを指定
* ignore_dir
    ファイル/ディレクトリ検索時において、無視するディレクトリを指定
* hide_dotfiles
    ドットで始まるファイルの表示/非表示を指定(true:非表示 false:表示)
* hide_owner
    ファイル/ディレクトリ所有者情報の表示/非表示を指定(true:非表示 false:表示)
* hide_owner
    ファイル/ディレクトリパーミッション情報の表示/非表示を指定(true:非表示 false:表示)
* limit_length
    ファイル/ディレクトリを表示する限界幅を指定
    ただし、バッファの長さが不足している場合は適当な幅で表示する
* bookmark_file
    ブックマークファイルを指定

## キーバインド
* space+f+e
    SublimeVimFiler起動
* j/k
    上下方向へ移動
* h
    一つ上のディレクトリへ移動
* l
    現在カーソル中のディレクトリへ移動
* enter or e
    現在カーソル中のファイルを開く
* ~
    ホームディレクトリへ移動
* r+r
    現在カーソル中のファイル/ディレクトリをrename
* dd
    現在カーソル中のファイル/ディレクトリをdelete
* N
    新規ファイルを作成し、オープンする
* K
    新規ディレクトリを作成する
* m+m
    現在カーソル中のファイル/ディレクトリをmove
* cc
    現在カーソル中のファイル/ディレクトリをcopy
* .(ドット)
    ドットで始まるファイルの表示/非表示を切り替える
* F5
    更新
* b+a
    カレントディレクトリをブックマークへ登録する
* b+o
    登録済みのブックマークをクイックパネル上に表示する
    選択したディレクトリをSublimeVimFiler上で開く
* b+e
    登録済みブックマークを編集するためのファイルを開く
* g+f
    カレントディレクトリ以下から、ファイル/ディレクトリを検索する
    検索結果のバッファ上で[e]押下後、ファイル/ディレクトリを開く
* t+s
    更新時刻で表示順をソートする
* d+s
    ディレクトリが上位に表示されるようソートする
* n+s
    名前で表示順をソートする
* r+s
    表示順を逆順でソートする
* m+a
    現在カーソル上のファイル/カレントディレクトリをマークする
    マークしたファイル/ディレクトリは[c+c/d+d]で一括コピー、削除可能
* m+c
    マークしたファイル/ディレクトリを解除する
* q
    SublimeVimFilerを終了する

## github URL
 * [GitHub](https://github.com/tkyk0317/SublimeVimFiler)
