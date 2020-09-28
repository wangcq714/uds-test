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
		self.varsDict = {}
		self.cmdTable = []


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

	def periodic_msg_task_stop(self, msgId):
		''''''
		main.periodMsgTasks[msgId].stop()

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
				if logSuccessed:
					print(re.findall(r"^.*Log\((.*?)\).*$", logSuccessed)[0])
				if self.resData[0] == 0x67 and re.match(".*-Seed.*", logSuccessed):
					self.sa_seed = self.resData[2:]
					self.calckey(len(self.sa_seed))

					# print(self.sa_seed)
			else:
				if logSuccessed:
					print(re.findall(r"^.*Log\((.*?)\).*$", logFailed)[0])

		except Exception as ex:
			if str(ex) == "Timeout in waiting for message":
				if resDataPattern == "^$":
					if logSuccessed:
						print(re.findall(r"^.*Log\((.*?)\).*$", logSuccessed)[0])
				else:
					if logSuccessed:
						print(re.findall(r"^.*Log\((.*?)\).*$", logFailed)[0])
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

	def precompile(self, dataDict):
		''''''
		keymin = min(sorted(dataDict.keys()))
		keymax = max(sorted(dataDict.keys()))

		for key in range(keymin, keymax+1):
			dataDict[key] = re.split(r"([#]+|[/]{2,})", dataDict[key].strip(' '))[0].strip(' ')
			# print(dataDict[key])


	def preprocessing(self, dataDict):
		''''''
		keymin = min(sorted(dataDict.keys()))
		keymax= max(sorted(dataDict.keys()))

		key = keymin
		while True:
			# print(dataDict[key])

			if re.match(r"^$", dataDict[key].strip(' ')):
				pass

			elif re.match(r"^([#]+|[/]{2,}).*", dataDict[key].strip(' ')):
				pass

			elif re.match(r"^[A-Za-z]+=[0-9]+$", dataDict[key].strip(' ')):
				# print(re.split("=", dataDict[key]))
				self.cmdTable.append(dataDict[key])
				self.varsDict[re.split("=", dataDict[key])[0]] = int(re.split("=", dataDict[key])[1])
				# print(self.varsDict)

			elif re.match(r"^while \[ .* \]$", dataDict[key].strip(' ')):
				self.cmdTable.append(re.findall(r"^while \[ (.+?) \]$", dataDict[key].strip(' '))[0])
				cmdTableIndexWhileStart = len(self.cmdTable) - 1
				key += 1
				if re.match(r"^do$", dataDict[key].strip(' ')):
					pass
				else:
					raise Exception("while do ... done   do error")

				key += 1
				subDataDict = {}
				while True:
					if re.match(r"^\t.*$", dataDict[key].strip(' ')):
						subDataDict[key] = dataDict[key][1:]
					else:
						break
					key += 1
				print(subDataDict)

				if subDataDict:
					self.preprocessing(subDataDict)

				if re.match(r"^done$", dataDict[key].strip(' ')):
					self.cmdTable.append(" goto " + str(cmdTableIndexWhileStart))
					self.cmdTable[cmdTableIndexWhileStart] += " : ? goto " + str(len(self.cmdTable))
				else:
					raise Exception("while do ... done   done error")

				# print(self.cmdTable)

			else:
				self.cmdTable.append(dataDict[key])

			key += 1
			if key > keymax:
				break

	def cmd_parse(self):
		''''''

		PC = 0
		while True:
			if re.match(r"^[A-Za-z]+[+]{2}$", self.cmdTable[PC].strip(' ')):
				self.varsDict[(re.findall(r"^(.*?)[+]{2}$", self.cmdTable[PC].strip(' '))[0])] += 1
				PC += 1
				# print(PC)

			elif re.match(r"^[A-Za-z]+=[0-9]+$", self.cmdTable[PC].strip(' ')):
				self.varsDict[re.split("=", self.cmdTable[PC])[0]] = int(re.split("=", self.cmdTable[PC])[1])
				PC += 1

			elif re.match(r"^[A-Za-z]+\+=[0-9]+$", self.cmdTable[PC].strip(' ')):
				self.varsDict[re.split("=", self.cmdTable[PC])[0]] += int(re.split("=", self.cmdTable[PC])[1])
				PC += 1

			elif re.match(r"^\$[A-Za-z]+ -le [0-9]+ : .* ? goto [0-9]+$", self.cmdTable[PC].strip(' ')):
				if self.varsDict[((re.findall(r"^\$(.*?) -le [0-9]+ : .* ? goto [0-9]+$", self.cmdTable[PC].strip(' '))[0]))] < int(re.findall(r"^\$[A-Za-z]+ -le (.*?) : .* ? goto [0-9]+$", self.cmdTable[PC].strip(' '))[0]):
					PC += 1
				else:
					PC = int(re.findall(r"^\$[A-Za-z]+ -le [0-9]+ : .* ? goto (.*?)$", self.cmdTable[PC].strip(' '))[0])

			elif re.match(r"^goto [0-9]+$", self.cmdTable[PC].strip(' ')):
				PC = int(re.findall(r"^goto (.*?)$", self.cmdTable[PC].strip(' '))[0])

			elif re.match(r"^Sleep\([0-9]+([.][0-9]+)?\)$", self.cmdTable[PC].strip(' ')):
				sleep(float(re.findall(r"^Sleep[(](.+?)[)]$", self.cmdTable[PC].strip(' '))[0]))
				PC += 1

			elif re.match(r"^CreateMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2})), [1-8]{1}, \[0x[0-9A-Fa-f]{2}(, 0x[0-9A-Fa-f]{2}){0,7}\]\)$", self.cmdTable[PC].strip(' ')):
				extractionData = re.findall(r"^CreateMessage\((.*?), (.*?), (.*?)\)$", self.cmdTable[PC].strip(' '))
				self.creat_msg(int(extractionData[0][0], 16), int(extractionData[0][1]), eval(extractionData[0][2]))
				# print(self.msgs)
				PC += 1

			elif re.match(r"^StartMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2})), [0-9]+([.][0-9]+)?\)$", self.cmdTable[PC].strip(' ')):
				# print(re.findall(r"^StartMessage\((.*?), (.*?)\)$", self.cmdTable[PC].strip(' ')))
				extractionData = re.findall(r"^StartMessage\((.*?), (.*?)\)$", self.cmdTable[PC].strip(' '))
				self.create_periodic_msg_task(int(extractionData[0][0], 16), float(extractionData[0][1]))
				self.periodic_msg_task_start(int(extractionData[0][0], 16))
				PC += 1

			elif re.match(r"^StopMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2}))\)$", self.cmdTable[PC].strip(' ')):
				self.periodic_msg_task_stop(int(re.findall(r"^StopMessage\((.*?)\)$", self.cmdTable[PC].strip(' '))[0], 16))
				# print(self.msgs)
				PC += 1

			elif re.match(r"^SetMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2})), \[0x[0-9A-Fa-f]{2}(, 0x[0-9A-Fa-f]{2}){0,7}\]\)$", self.cmdTable[PC].strip(' ')):
				extractionData = re.findall(r"^SetMessage\((.*?), (.*?)\)$", self.cmdTable[PC].strip(' '))
				self.modify_msg(int(extractionData[0][0], 16), eval(extractionData[0][1]))
				self.periodic_msg_task_modify_msg(int(extractionData[0][0], 16))
				PC += 1

			elif re.match(r"^SendMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2})), [1-8]{1}, \[0x[0-9A-Fa-f]{2}(, 0x[0-9A-Fa-f]{2}){0,7}\]\)$", self.cmdTable[PC].strip(' ')):
				extractionData = re.findall(r"^SendMessage\((.*?), (.*?), (.*?)\)$", self.cmdTable[PC].strip(' '))
				self.send_msg(can.Message(arbitration_id=int(extractionData[0][0], 16), dlc=int(extractionData[0][1]), data=eval(extractionData[0][2])))
				PC += 1

			elif re.match(r".*\?.*:.*", self.cmdTable[PC].strip(' ')):

				if re.match(r".*Key[(]\d+[)].*", self.cmdTable[PC].strip(' ')):
					self.cmdTable[PC] = re.sub(r"Key[(]\d+[)]", ' '.join(["{0:02X}".format(ele) for ele in self.sa_key]), self.cmdTable[PC])

				validData = [ele.strip(' ') for ele in re.split("[?|:]", self.cmdTable[PC])]

				validData[0] = re.split("==", validData[0])

				# print(type(validData))
				# print(len(validData))
				print(validData)
				# print(re.split(' +', validData[0][0]))
				# print(validData[0][1])
				# print(re.split(' +', validData[0][1]))

				reqData = [int(ele if not re.match("^\$[A-Za-z]+", ele) else str(self.varsDict[ele[1:]]), 16) for ele in re.split(' +', validData[0][0])] if not re.match('^FUN', validData[0][0]) else [int(ele if not re.match("^\$[A-Za-z]+", ele) else str(self.varsDict[ele[1:]]), 16) for ele in re.split(' +', validData[0][0])[1:]]
				# print(reqData)
				resDataPattern = '^' + validData[0][1] + '$'
				logSuccessed = validData[1]
				logFailed = validData[2]
				funcReq = False if not re.match('^FUN', validData[0][0]) else True

				self.diag_send(reqData, resDataPattern, logSuccessed, logFailed, funcReq=funcReq)
				PC += 1
			else:
				PC += 1


			if PC >= len(self.cmdTable):
				break



	def main(self, dataDict):
		''''''
		self.precompile(dataDict)
		self.preprocessing(dataDict)
		self.cmd_parse()



if __name__ == "__main__":

	readData = readdata.ReadData()
	readData.get_file_pathname()
	readData.read_data()
	main = Main()
	main.main(readData.dataDict)


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
	#
	# main.periodic_msg_task_stop(0x500)
	#
	# sleep(5)

	# main.diag_send([0x3E, 0x80], "^$", "Test OK", "Test Failed")
	# main.diag_send([0x19, 0x02, 0x2F], "^59 02( [0-9A-Fa-f]{2})(( [0-9A-Fa-f]{2}){4})*( 16 08 00 26)(( [0-9A-Fa-f]{2}){4})*$", "Test OK", "Test Failed")
	# sleep(5)

	# main.read_dtc([0x19, 0x02, 0x2F], ".*")
	# main.clear_dtc()



