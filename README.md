## 站点公开信息搜索工具
### 功能说明
通过Google和Baidu搜索引擎自带的高级搜索功能检索特定域名的索引信息，可通过自定义的高级搜索语句进行检索，并输出到特定文件中。
当只通过site关键词检索域名时，将输出两种搜索引擎检索子域名情况。

### 实现说明
Google搜索：就是爬虫而已，其中因为Google的机器人检测机制，在每次请求Google页面前进行随机的等待，如果可以切换代理就更完美了，要不然可以增加等待时间，但影响效率。
Baidu搜索：与Google不同的是Baidu的搜索结果URL，是经过加密的，通过二次请求的方式可获得真实的URL，因此采用了多线程请求。

### 使用说明
usage: sitedork.py [-h] [-l limit] -d domain

Information Dork tool for searching domains,files and emails.

optional arguments:

	-h, --help	show this help message and exit

	-l limit, --limit limit		results of searching limit(default:1000)

	-d domain, --domain domain 	domain name for searching
