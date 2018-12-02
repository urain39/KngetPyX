# KngetPy Sankaku V2.x

[![Build status](https://ci.appveyor.com/api/projects/status/tona2atf9w5342r6/branch/master?svg=true)](https://ci.appveyor.com/project/urain39/kngetpyx/branch/master)

**Supported:**

- Python2(recommend 2.7)
- Python3(recommend 3.6)

**Required:**

- knget(>=0.1.8)

### User Guide ###

```shell
python -m kngetx <tags> < <begin> [end] >

For example:
	python -m kngetx 'seifuku' 1 1
```

**NOTE**: No longer support login for Sankakucomplex!

![HolyShit!](images/a5cc28c8.jpg)

### Custom configuration ###

```json

{
  "custom": {
    "base_url": "https://capi-beta.sankakucomplex.com",
    "page_limit": 10,
    "user_agent": "Mozilla/5.0 (Linux; LittleKaiju)",
    "load_time_fake": "1, 2",
    "post_rating": "s",
    "post_min_score": 0,
    "post_tags_blacklist": "video mp4 webm",
    "save_history": false,
    "history_path": "history.txt",
    "save_cookies": false,
    "cookies_path": "cookies.txt",
    "disable_dbgrun": true
  },
  "download": {
    "timeout": 30,
    "maxsize": 10,
    "bufsize": 1048576,
    "retry_wait": 8,
    "retry_count": 3
  }
}
```
