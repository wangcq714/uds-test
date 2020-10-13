import os

from platform import system

class WriteData(object):
	"""write"""
	def __init__(self):
		self.first_open_data_log = False
		self.first_open_error_log = False
	
	def mkdir(self, path:str): 
		# 去除首位空格、尾部\
	    path=path.strip()
			# 判断结果
	    if not os.path.exists(path):
			os.makedirs(path)

	def write_data_log(self, dataList):
		"""写入Table.c文件"""
		# 如果第一次写入，新建一个.c文件，否则接续写
		self.mkdir("output")
		if self.first_open_data_log == False:
			self.first_open_data_log = True
			with open("log/data.log",'w') as logFile:
				for tmp in dataList:
					logFile.write(tmp)
				logFile.write("\n"*2)
		else:
			with open("log/data.log",'a') as logFile:
				for tmp in dataList:
					logFile.write(tmp)
				logFile.write("\n"*2)

	def write_error_log(self, dataList):
		"""写入Table.c文件"""
		# 如果第一次写入，新建一个.c文件，否则接续写
		self.mkdir("output")
		if self.first_open_error_log == False:
			self.first_open_error_log = True
			with open("log/error.log",'w') as logFile:
				for tmp in dataList:
					logFile.write(tmp)
				logFile.write("\n"*2)
		else:
			with open("log/error.log",'a') as logFile:
				for tmp in dataList:
					logFile.write(tmp)
				logFile.write("\n"*2)






