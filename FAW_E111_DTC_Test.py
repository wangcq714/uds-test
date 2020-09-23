# #!/usr/bin/env python

import uds 
from uds import Uds
from time import sleep
import can
import re
from fileio import readdata

import ctypes
from ctypes import *

class Main(object):
	"""docstring for main"""
	def __init__(self):
		super(Main, self).__init__()
		# This creates a Uds object manually
		self.rawUDS = Uds()
		self.rawCAN = can.interface.Bus(bustype='vector', app_name='canoe', channel=0, bitrate=500000)
		self.periodMsgTasks = {}
		self.msgs = {}
		self.resData = []
		self.sa_seed = []
		self.sa_key = []


	def creat_msg(self, msgId:int, msgDataDlc:int=8, msgData:list=[0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]):
		''''''
		try:
			self.msgs[msgId] = can.Message(arbitration_id=msgId, dlc=msgDataDlc, data=msgData)
			print("Message 0x{0:X} creat ok ".format(msgId))
		except Exception as ex:
			print(ex)
			print("Message 0x{0:X} creat fail ".format(msgId))

	def send_msg(self, msg:can.Message):
		''''''
		try:
			self.rawCAN.send(msg)
			print(f"Message sent on {self.rawCAN.channel_info}")
		except can.CanError:
			print("Message NOT sent")

	def create_periodic_msg_task(self, msgId:int, period:float):
		''''''
		try:
			self.periodMsgTasks[msgId] = self.rawCAN.send_periodic(self.msgs[msgId], period)
			print("Task 0x{0:X} creat ok ".format(msgId))
		except Exception as ex:
			print(ex)
			print("Task 0x{0:X} creat fail ".format(msgId))

	def periodic_msg_task_start(self, msgId):
		''''''
		main.periodMsgTasks[msgId].start()

	def modify_msg(self, msgId:int, data:list, **kwargs):
		''''''
		self.msgs[msgId].data = data

	def periodic_msg_task_modify_msg(self, msgId:int):
		''''''
		self.periodMsgTasks[msgId].modify_data(self.msgs[msgId])

	def clear_dtc(self):
		''''''
		try:
			self.resData = []
			self.resData =self.rawUDS.send([0x14, 0xFF, 0xFF, 0xFF], functionalReq=True)
			resDataStr = ' '.join(self.resData)
			print(resDataStr)
			if self.resData[0] == 0x54:
				print("Clear DTC OK")
			else:
				print("Clear DTC Fail")
		except Exception as ex:
			print(ex)
			print("Clear DTC Fail")


	def read_dtc(self, reqData:list, resDataPattern:str):
		''''''
		try:
			self.resData = []
			self.resData = self.rawUDS.send(reqData)
			print(self.resData)
			resDataStr = ['{0:02X}'.format(ele) for ele in self.resData]
			resDataStr = ' '.join(resDataStr)
			print(resDataStr)

			if re.match(resDataPattern, resDataStr, flags=re.IGNORECASE):
				print("合法")
			else:
				print("不合法")

			if self.resData[0] == 0x59:
				print("Read DTC OK")
			else:
				print("Read DTC Fail")
		except Exception as ex:
			print(ex)
			print("Read DTC Fail")

	def check_result(self, expectData):
		''''''
		pass

	def set_fault(self, faultNum):
		''''''
		data = [0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
		# data[faultNum//8] =
		# byte =
		# bit = faultNum%8

		self.modify_msg(0x500, [0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
		self.periodic_msg_task_modify_msg(0x500)

	def unset_fault(self):
		pass

	def diag_req(self):
		''''''
		pass

	def diag_send(self, reqData:list, resDataPattern:str,logSuccessed:str="",  logFailed:str="", responseRequired=True, funcReq=False):
		''''''
		print(["{0:02X}".format(ele) for ele in reqData])
		# print(resDataPattern)
		try:
			self.resData = []
			self.resData = self.rawUDS.send(reqData, functionalReq=funcReq)
			print(["{0:02X}".format(ele) for ele in self.resData])
			resDataStr = ' '.join(['{0:02X}'.format(ele) for ele in self.resData])
			# print(resDataStr)

			if re.match(resDataPattern, resDataStr):
				print(logSuccessed)
				if self.resData[0] == 0x67 and re.match(".*-Seed.*", logSuccessed):
					self.sa_seed = self.resData[2:]
					self.calckey(len(self.sa_seed))

					# print(self.sa_seed)
			else:
				print(logFailed)

		except Exception as ex:
			if str(ex) == "Timeout in waiting for message":
				if resDataPattern == "^$":
					print(logSuccessed)
				else:
					print(logFailed)
			else:
				print(ex)
				print("Diagnostic send fail")

	def calckey(self, sa_len):
		''''''
		securitydll = cdll.LoadLibrary("config/SecurityDll/sdll.dll")

		seed = (ctypes.c_ubyte * sa_len)()
		key = (ctypes.c_ubyte * sa_len)()
		for i in range(sa_len):
			seed[i] = self.sa_seed[i]

		securitydll.CalcKeys(seed, key, sa_len)

		self.sa_key = [ele for ele in key]

		# print(["{0:02X}".format(ele) for ele in list(seed)])
		# print(["{0:02X}".format(ele) for ele in list(key)])

	def main(self):
		''''''
		readData = readdata.ReadData()
		readData.get_file_pathname()
		readData.read_data()
		# print(readData.dataList)
		# print(len(readData.dataList))

		for sub in readData.dataList:
			# print(sub)
			if re.match(r"^Sleep[(][0-9]+([.][0-9]+)?[)]$", sub[0].strip(' ')):
				sleep(float(re.findall(r"^Sleep[(](.+?)[)]$", sub[0].strip(' '))[0]))
				continue
			elif re.match(r"^([#]+|[/]{2,}).*", sub[0].strip(' ')):
				continue

			if re.match(r".*Key[(]\d+[)].*", sub[0].strip(' ')):
				sub[0] = re.sub(r"Key[(]\d+[)]", ' '.join(["{0:02X}".format(ele) for ele in main.sa_key]), sub[0])
			# print(sub[0])

			validData = [ele.strip(' ') for ele in re.split("[?|:]", sub[0])]

			validData[0] = re.split("==", validData[0])

			# print(type(validData))
			# print(len(validData))
			# print(validData)
			# print(re.split(' +', validData[0][0]))
			# print(validData[0][1])
			# print(re.split(' +', validData[0][1]))

			reqData = [int(ele, 16) for ele in re.split(' +', validData[0][0])] if not re.match('^FUN', validData[0][0]) else [int(ele, 16) for ele in re.split(' +', validData[0][0])[1:]]
			resDataPattern = '^' + validData[0][1] + '$'
			logSuccessed = validData[1]
			logFailed = validData[2]
			funcReq = False if not re.match('^FUN', validData[0][0]) else True

			main.diag_send(reqData, resDataPattern, logSuccessed, logFailed, funcReq=funcReq)


if __name__ == "__main__":
   
	main = Main()
	main.main()
	# main.creat_msg(0x500)
	# main.create_periodic_msg_task(0x500, 0.01)
	# main.periodic_msg_task_start(0x500)
	#
	#
	# main.creat_msg(0x501)
	# main.create_periodic_msg_task(0x501, 0.01)
	# main.periodic_msg_task_start(0x501)
	#
	# sleep(5)
	#
	# main.modify_msg(0x500, [0x12, 0x34, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
	# main.periodic_msg_task_modify_msg(0x500)

	# main.diag_send([0x3E, 0x80], "^$", "Test OK", "Test Failed")
	# main.diag_send([0x19, 0x02, 0x2F], "^59 02( [0-9A-Fa-f]{2})(( [0-9A-Fa-f]{2}){4})*( 16 08 00 26)(( [0-9A-Fa-f]{2}){4})*$", "Test OK", "Test Failed")
	# sleep(5)

	# main.read_dtc([0x19, 0x02, 0x2F], ".*")
	# main.clear_dtc()



