# import pandas
import numpy
from pandas import read_csv
# import numpy

from tkinter.filedialog import askopenfilename
from openpyxl.utils import get_column_letter, column_index_from_string


# 定义一个文件IO类
class ReadData(object):
	"""Route Table"""
	def get_file_pathname(self):
		"""获取路由表路径"""
		self.pathName = askopenfilename(filetypes = [("Excel",".xh")])
		if self.pathName == ():
			self.pathName = ""
			self.dataDict= {}
		# print(self.pathName)
		# print(type(self.pathName))

	def read_data(self):
		""""""
		self.dataDict = {}
		if self.pathName != "":
			# 读取全部数据按行存入字典中
			with open(self.pathName, 'r') as file:
				for index, line in enumerate(file):
					self.dataDict[index] = line[:-1]
				print(self.dataDict)




if __name__ == '__main__':
	readData = ReadData()
	readData.get_file_pathname()
	readData.read_data()
	print(readData.dataDict)
	print(len(readData.dataDict))





