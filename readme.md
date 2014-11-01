# 神大休講情報監視ツール

## install
``` sh
    $ apt-get install python-mechanize
    $ git clone git@github.com:solorab/ku-kyuko.git
```

## use
``` sh
    $ ./kyuko.py -u <学生番号> -p <パスワード>
```

cronから呼び出すとよい

## feature
-   emailで通知
-   重複通知はしない

## todo
-   password無しで見れる情報源を探す
    -   潜ってる講義の情報も欲しい
-   当日/前日にリマインダ欲しい
-   休講取り止めの通知
-   cacheの定期削除
    -   年末に注意
-   logをちゃんと取る
-   python3に

## license
AGPL v3
