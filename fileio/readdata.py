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
		self.pathName = askopenfilename(filetypes = [("Excel",".csv")])
		if self.pathName == ():
			self.pathName = ""
			self.dataList = []
		# print(self.pathName)
		# print(type(self.pathName))

	def read_data(self):
		"""从路由表中读取数据"""
		self.dataList = []
		if self.pathName != "":
			dataFrame = read_csv(self.pathName, header=None, na_values="")
			self.dataList = dataFrame.fillna("None").values.tolist()
		# print(self.dataList)




if __name__ == '__main__':
	readData = ReadData()
	readData.get_file_pathname()
	readData.read_data()
	print(readData.dataList)
	print(len(readData.dataList))





