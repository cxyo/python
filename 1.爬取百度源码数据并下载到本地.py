'''
目的：爬取百度源码数据并下载到本地
'''
# 从网址库里找到请求库里的打开一个网址 模块
from urllib.request import urlopen
# 准备需要打开的网址
url = 'http://www.baidu.com'
# 打开这个网址得到一个响应
resp = urlopen(url)
# 读取里面的数据
data = resp.read()
# 转换解码格式
data = data.decode('utf-8')
datas = urlopen(url).read().decode('utf-8')  # 合并为一行代码
# 保存到本地文件
with open('baidu.html', mode='w', encoding='utf-8') as f:  # 创建文件
	f.write(datas)  # 读取到网页源代码
print('保存成功！')