# OneKeySync
跨平台的本地文件同步工具(python3 练习)

# Usage:

sync.config.json
```json
{
    "reverse": false,
    "win_define": {
        "demo": "C:"
    },
    "linux_define": {
        "demo": "/home/ho/demo"
    },
    "folder": [
        "%demo%/sync/test:%demo%/sync/test"
    ]
}
```
