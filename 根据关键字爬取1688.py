# -*- coding: utf-8 -*-
# Author :micky
# Data: 2022-07-04 22:45

import urllib
import xlwt
from bs4 import BeautifulSoup
import requests


def writeExcel(ilt, name):
	if (name != ''):
		count = 0
		workbook = xlwt.Workbook(encoding='utf-8')
		worksheet = workbook.add_sheet('temp')
		worksheet.write(count, 0, '序号')
		worksheet.write(count, 1, '价格')
		worksheet.write(count, 2, '名称')
		for g in ilt:
			count = count + 1
			worksheet.write(count, 0, count)
			worksheet.write(count, 1, g[0])
			worksheet.write(count, 2, g[1])
		workbook.save(name + '.xls')
		print('已保存为：' + name + '.xls')
	else:
		printGoodsList(ilt)


def getHTMLText(url):
	kv = {'user-agent': 'Mozilla/5.0'}
	try:
		r = requests.get(url, headers=kv, timeout=30)
		r.raise_for_status()
		r.encoding = r.apparent_encoding
		return r.text
	except:
		return ""


def parsePage(ilt, html):
	try:
		bf = BeautifulSoup(html, 'html.parser')
		price = bf.find_all(attrs={'click-item': "price"})
		title = bf.find_all(attrs={'click-item': "title"})
		for i in range(len(price)):
			ilt.append([price[i].text, title[i].text])
	except:
		print("")


def printGoodsList(ilt):
	tplt = "{:4}\t{:8}\t{:16}"
	print(tplt.format("序号", "价格", "名称"))
	count = 0
	for g in ilt:
		count = count + 1
		print(tplt.format(count, g[0], g[1]))


def main():
	goods = input('搜索商品:')
	depth = int(input('搜索页数:'))
	name = input('输入保存的excel名称(留空print):')
	start_url = 'https://www.1688.com/chanpin/-.html?spm=a261b.2187593.searchbar.2.oUjRZK&keywords=' + urllib.parse.quote(
		goods, safe='/', encoding='gb2312')
	infoList = []
	print('处理中...')
	for i in range(depth):
		try:
			url = start_url + '&beginPage=' + str(i + 1)
			html = getHTMLText(url)
			parsePage(infoList, html)
			print('第%i页成功...' % (i + 1))
		except:
			continue
	writeExcel(infoList, name)
	print('完成!')


main()
