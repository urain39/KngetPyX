# KngetPy Sankaku V2.2

### 使用方法 ###

```shell
python <标签> <[起始页]结束页>

示例:
	python 'seifuku' 10
```



### 自定义配置 ###

```ini
; KngetPy Project.
; File auto-generated by .\knget.py
;
; Edit the base_url in the custom section
; to download different kind of images on site.
;
; Project links:
;   https://github.com/urain39/KngetPy
;   https://github.com/urain39/IniFilePy
;

[account]
username=knget
password=knget.py

[custom]
base_url=https://capi.sankakucomplex.com
;base_url=https://iapi.sankakucomplex.com
page_limit=10
json_regex=Post.register\((\{.+\})\)
top_tags_count=10
load_time_fake=3-5     - 加载时间欺骗，躲避部分反爬虫检测
user_agent=SCChannelApp/3.0 (Android; black)
;user_agent=SCChannelApp/3.0 (Android; idol)

post_rating=e q s
post_min_score=50
post_tags_blacklist=

[download]
debug=0
thread=8
timeout=120
maxsize=150
bufsize=1048576
retry_wait=8
retry_count=3

```

