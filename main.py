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
		self.sa_key = [0x0, 0x0, 0x0, 0x0]
		self.varsDict = {}
		self.cmdsDict = {}
		self.dataLogList = []
		self.errorLogList = []


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

	def diag_send(self, reqData:list, resDataPattern:str,logSuccessed:str="",  logFailed:str="", responseRequired=True, funcReq=False) -> bool:
		''''''
		ret =False
		print(["{0:02X}".format(ele) for ele in reqData])
		# print(resDataPattern)
		try:
			self.resData = []
			self.resData = self.rawUDS.send(reqData, functionalReq=funcReq)
			print(["{0:02X}".format(ele) for ele in self.resData])
			resDataStr = ' '.join(['{0:02X}'.format(ele) for ele in self.resData])
			# print(resDataStr)

			if re.match(resDataPattern, resDataStr):
				ret = True
				if logSuccessed:
					print(re.findall(r"^.*Log\((.*?)\).*$", logSuccessed)[0])
				if self.resData[0] == 0x67 and re.match(".*-Seed.*", logSuccessed):
					self.sa_seed = self.resData[2:]
					self.calckey(len(self.sa_seed))

					# print(self.sa_seed)
			else:
				ret = False
				if logFailed:
					print(re.findall(r"^.*Log\((.*?)\).*$", logFailed)[0])

		except Exception as ex:
			if str(ex) == "Timeout in waiting for message":
				if resDataPattern == "^$":
					ret = True
					if logSuccessed:
						print(re.findall(r"^.*Log\((.*?)\).*$", logSuccessed)[0])
				else:
					ret = False
					if logFailed:
						print(re.findall(r"^.*Log\((.*?)\).*$", logFailed)[0])
			else:
				ret = False
				print(ex)
				print("Diagnostic send fail")

		return ret

	def calckey(self, sa_len):
		''''''
		securitydll = cdll.LoadLibrary("config/SecurityDll/sdll.dll")

		seed = (ctypes.c_ubyte * sa_len)()
		key = (ctypes.c_ubyte * sa_len)()
		for i in range(sa_len):
			seed[i] = self.sa_seed[i]

		securitydll.CalcKeys(seed, key, sa_len)

		self.sa_key = [ele for ele in key]

	def precompile(self, dataDict):
		''''''
		keymin = min(sorted(dataDict.keys()))
		keymax = max(sorted(dataDict.keys()))

		for key in range(keymin, keymax+1):
			dataDict[key] = re.split(r"([#]+|[/]{2,})", dataDict[key].strip(' '))[0].strip(' ')
			if re.match(r"^\t* *\t* *$", dataDict[key].strip(' ')):
				dataDict[key] = ""
			# print(dataDict[key])
		key = keymin
		while True:
			if re.match(r"^:<<EOF$", dataDict[key].strip(' ')):
				dataDict[key] = ""
				key += 1
				while True:
					if re.match(r"^EOF$", dataDict[key].strip(' ')):
						dataDict[key] = ""
						break
					dataDict[key] = ""
					key += 1

					if key > keymax:
						raise Exception(":<<EOF...EOF error")
			key += 1
			if key > keymax:
				break

		print(dataDict)

	def preprocessing(self, dataDict):
		''''''
		if not dataDict:
			return

		keymin = min(sorted(dataDict.keys()))
		keymax= max(sorted(dataDict.keys()))

		key = keymin
		while True:
			if re.match(r"^while +.*$", dataDict[key].strip(' ')):
				commands = re.findall(r"^while +(.+?)$", dataDict[key].strip(' '))[0]
				if re.match(r"^\[ ((\$[A-Za-z]+)|([0-9]+)) -(eq|ne|gt|ge|lt|le) ((\$[A-Za-z]+)|([0-9]+)) \]$", commands)\
						or re.match(r"^\({2} ?((\$[A-Za-z]+)|([0-9]+)) ((==)|(!=)|(>)|(>=)|(<)|(<=)) ((\$[A-Za-z]+)|([0-9]+)) ?\){2}$", commands):
					self.cmdsDict[key] = commands
				else:
					raise Exception("line {0} commands syntax errors".format(key+1))
				whilekey = key
				key += 1
				if re.match(r"^do$", dataDict[key].strip(' ')):
					self.cmdsDict[key] = ""
				else:
					raise Exception("while do ... done   do error")

				key += 1
				subDataDict = {}
				while True:
					if re.match(r"^\t.*$", dataDict[key].strip(' ')):
						subDataDict[key] = dataDict[key][1:]
					elif re.match(r"^\t* *\t* *$", dataDict[key].strip(' ')):
						subDataDict[key] = ""
					else:
						break
					key += 1

				self.preprocessing(subDataDict)

				if re.match(r"^done$", dataDict[key].strip(' ')):
					self.cmdsDict[key] = " goto " + str(whilekey)
					self.cmdsDict[whilekey] += " ? : goto " + str(key+1)
				else:
					raise Exception("while do ... done   done error")

			elif re.match(r"^if +.*; *then$", dataDict[key].strip(' ')):
				commands = re.findall(r"^if *(.+?); *then$", dataDict[key].strip(' '))[0]
				if re.match(r"^\[ ((\$[A-Za-z]+)|([0-9]+)) -(eq|ne|gt|ge|lt|le) ((\$[A-Za-z]+)|([0-9]+)) \]$", commands)\
						or re.match(r"^\({2} ?((\$[A-Za-z]+)|([0-9]+)) ((==)|(!=)|(>)|(>=)|(<)|(<=)) ((\$[A-Za-z]+)|([0-9]+)) ?\){2}$", commands):
					self.cmdsDict[key] = commands
				else:
					raise Exception("line {0} commands syntax errors".format(key + 1))
				# print(self.cmdsDict[key])
				ifkey = key
				gotofikey = []
				key += 1
				subDataDict = {}
				while True:
					if re.match(r"^\t.*$", dataDict[key].strip(' ')):
						subDataDict[key] = dataDict[key][1:]
					elif re.match(r"^\t* *\t* *$", dataDict[key].strip(' ')):
						subDataDict[key] = ""
					else:
						gotofikey.append(key-1)
						break
					key += 1
				self.preprocessing(subDataDict)

				while True:
					if re.match(r"^elif +.*; *then$", dataDict[key].strip(' ')):
						self.cmdsDict[ifkey] += " ? : goto " + str(key)
						ifkey = key

						commands = re.findall(r"^elif +(.+?); *then$", dataDict[key].strip(' '))[0]
						if re.match(r"^\[ ((\$[A-Za-z]+)|([0-9]+)) -(eq|ne|gt|ge|lt|le) ((\$[A-Za-z]+)|([0-9]+)) \]$", commands)\
								or re.match(r"^\({2} ?((\$[A-Za-z]+)|([0-9]+)) ((==)|(!=)|(>)|(>=)|(<)|(<=)) ((\$[A-Za-z]+)|([0-9]+)) ?\){2}$", commands):
							self.cmdsDict[key] = commands
						else:
							raise Exception("line {0} commands syntax errors".format(key + 1))

						key += 1
						subDataDict = {}
						while True:
							if re.match(r"^\t.*$", dataDict[key].strip(' ')):
								subDataDict[key] = dataDict[key][1:]
							elif re.match(r"^\t* *\t* *$", dataDict[key].strip(' ')):
								subDataDict[key] = ""
							else:
								gotofikey.append(key - 1)
								break
							key += 1
						self.preprocessing(subDataDict)
					elif re.match(r"^else$", dataDict[key].strip(' ')):
						self.cmdsDict[ifkey] += " ? : goto " + str(key)
						ifkey = -1
						self.cmdsDict[key] = ""
						key += 1
						subDataDict = {}
						while True:
							if re.match(r"^\t.*$", dataDict[key].strip(' ')):
								subDataDict[key] = dataDict[key][1:]
							elif re.match(r"^\t* *\t* *$", dataDict[key].strip(' ')):
								subDataDict[key] = ""
							else:
								break
							key += 1
						self.preprocessing(subDataDict)
					elif re.match(r"^fi$", dataDict[key].strip(' ')):
						if ifkey != -1:
							self.cmdsDict[ifkey] += " ? : goto " + str(key)
						self.cmdsDict[key] = ""
						for subkey in gotofikey:
							self.cmdsDict[subkey] += " ; goto " + str(key)
						break
					else:
						raise Exception("if...elif...else...fi error")

			else:
				self.cmdsDict[key] = dataDict[key].strip(' ')

			key += 1
			if key > keymax:
				break

	def __parse_conditions_judgment_square_brackets(self, cmd) -> tuple:
		'''[[commands]]'''
		ret = False

		extractionData = re.findall(r"^\[ (.*?) (.*?) (.*?) \] \? : goto (.*?)$", cmd)
		lValue = int(extractionData[0][0] if not re.match(r"^\$[A-Za-z]+$", extractionData[0][0]) else self.varsDict[
			extractionData[0][0][1:]])
		comparisonOperator = extractionData[0][1]
		rValue = int(extractionData[0][2] if not re.match(r"^\$[A-Za-z]+$", extractionData[0][2]) else self.varsDict[
			extractionData[0][2][1:]])
		PCJump = int(extractionData[0][3])

		if (comparisonOperator == "-eq" and lValue == rValue)\
		or (comparisonOperator == "-ne" and lValue != rValue)\
		or (comparisonOperator == "-gt" and lValue > rValue)\
		or (comparisonOperator == "-ge" and lValue >= rValue)\
		or (comparisonOperator == "-lt" and lValue < rValue)\
		or (comparisonOperator == "-le" and lValue <= rValue):
			ret = True
		else:
			pass

		return (ret, PCJump)

	def __parse_conditions_judgment_parenthesis(self, cmd) -> tuple:
		'''((commands))'''
		ret = False
		extractionData = re.findall(r"^\({2} ?(.*?) (.*?) (.*?) ?\){2} \? : goto (.*?)$", cmd)
		lValue = int(extractionData[0][0] if not re.match(r"^\$[A-Za-z]+$", extractionData[0][0]) else self.varsDict[
			extractionData[0][0][1:]])
		comparisonOperator = extractionData[0][1]
		rValue = int(extractionData[0][2] if not re.match(r"^\$[A-Za-z]+$", extractionData[0][2]) else self.varsDict[
			extractionData[0][2][1:]])
		PCJump = int(extractionData[0][3])

		if (comparisonOperator == "==" and lValue == rValue)\
		or (comparisonOperator == "!=" and lValue != rValue)\
		or (comparisonOperator == ">" and lValue > rValue)\
		or (comparisonOperator == ">=" and lValue >= rValue)\
		or (comparisonOperator == "<" and lValue < rValue)\
		or (comparisonOperator == "<=" and lValue <= rValue):
			ret = True
		else:
			pass

		return (ret, PCJump)

	def __parse_diag_msg(self, cmd):
		''''''
		if re.match(r".*Key[(]\d+[)].*", cmd):
			cmd = re.sub(r"Key[(]\d+[)]", ' '.join(["{0:02X}".format(ele) for ele in self.sa_key]), cmd)

		validData = [ele.strip(' ') for ele in re.split("[?|:]", cmd)]

		validData[0] = re.split("==", validData[0])

		# print(type(validData))
		# print(len(validData))
		# print(validData)
		# print(re.split(' +', validData[0][0]))
		# print(validData[0][1])
		# print(re.split(' +', validData[0][1]))

		reqData = [int(ele if not re.match("^\$[A-Za-z]+", ele) else str(self.varsDict[ele[1:]]), 16) for ele in
				   re.split(' +', validData[0][0])] if not re.match('^FUN', validData[0][0]) else [
			int(ele if not re.match("^\$[A-Za-z]+", ele) else str(self.varsDict[ele[1:]]), 16) for ele in
			re.split(' +', validData[0][0])[1:]]
		# print(reqData)
		resDataPattern = '^' + validData[0][1] + '$'
		logSuccessed = validData[1]
		logFailed = validData[2]
		funcReq = False if not re.match('^FUN', validData[0][0]) else True

		if self.diag_send(reqData, resDataPattern, logSuccessed, logFailed, funcReq=funcReq):
			self.dataLogList.append(logSuccessed)
		else:
			self.dataLogList.append(logFailed)
			self.errorLogList.append(logFailed)

	def cmd_parse(self):
		''''''
		PC = 0
		print(self.cmdsDict)
		while True:
			jump = False
			for cmd in [sub.strip(' ') for sub in self.cmdsDict[PC].split(';')]:
				if re.match(r"^[A-Za-z]+=[0-9]+$", cmd):
					self.varsDict[re.split("=", cmd)[0]] = int(re.split("=", cmd)[1])

				elif re.match(r"^[A-Za-z]+\+{2}$", cmd):
					self.varsDict[(re.findall(r"^(.*?)\+{2}$", cmd)[0])] += 1

				elif re.match(r"^[A-Za-z]+\-{2}$", cmd):
					self.varsDict[(re.findall(r"^(.*?)\-{2}$", cmd)[0])] -= 1

				elif re.match(r"^[A-Za-z]+\+=[0-9]+$", cmd):
					self.varsDict[re.split("=", cmd)[0]] += int(re.split("=", cmd)[1])

				elif re.match(r"^[A-Za-z]+\-=[0-9]+$", cmd):
					self.varsDict[re.split("=", cmd)[0]] -= int(re.split("=", cmd)[1])

				elif re.match(r"^\[ ((\$[A-Za-z]+)|([0-9]+)) -(eq|ne|gt|ge|lt|le) ((\$[A-Za-z]+)|([0-9]+)) \] \? : goto [0-9]+$", cmd):
					ret = self.__parse_conditions_judgment_square_brackets(cmd)
					if not ret[0]:
						PC = ret[1]
						jump = True
						break

				elif re.match(r"^\({2} ?((\$[A-Za-z]+)|([0-9]+)) ((==)|(!=)|(>)|(>=)|(<)|(<=)) ((\$[A-Za-z]+)|([0-9]+)) ?\){2} \? : goto [0-9]+$", cmd):
					ret = self.__parse_conditions_judgment_parenthesis(cmd)
					if not ret[0]:
						PC = ret[1]
						jump = True
						break

				elif re.match(r"^goto [0-9]+$", cmd):
					PC = int(re.findall(r"^goto (.*?)$", cmd)[0])
					jump = True
					break

				elif re.match(r"^Sleep\([0-9]+([.][0-9]+)?\)$", cmd):
					sleep(float(re.findall(r"^Sleep[(](.+?)[)]$", cmd)[0]))

				elif re.match(r"^CreateMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2})), [1-8]{1}, \[0x[0-9A-Fa-f]{2}(, 0x[0-9A-Fa-f]{2}){0,7}\]\)$", cmd):
					extractionData = re.findall(r"^CreateMessage\((.*?), (.*?), (.*?)\)$", cmd)
					self.creat_msg(int(extractionData[0][0], 16), int(extractionData[0][1]), eval(extractionData[0][2]))
					# print(self.msgs)

				elif re.match(r"^StartMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2})), [0-9]+([.][0-9]+)?\)$", cmd):
					extractionData = re.findall(r"^StartMessage\((.*?), (.*?)\)$", cmd)
					self.create_periodic_msg_task(int(extractionData[0][0], 16), float(extractionData[0][1]))
					self.periodic_msg_task_start(int(extractionData[0][0], 16))

				elif re.match(r"^StopMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2}))\)$", cmd):
					self.periodic_msg_task_stop(int(re.findall(r"^StopMessage\((.*?)\)$", cmd)[0], 16))
					# print(self.msgs)

				elif re.match(r"^SetMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2})), \[0x[0-9A-Fa-f]{2}(, 0x[0-9A-Fa-f]{2}){0,7}\]\)$", cmd):
					extractionData = re.findall(r"^SetMessage\((.*?), (.*?)\)$", cmd)
					self.modify_msg(int(extractionData[0][0], 16), eval(extractionData[0][1]))
					self.periodic_msg_task_modify_msg(int(extractionData[0][0], 16))

				elif re.match(r"^SendMessage\(0x(([0-9 A-F]{1,2})|([0-7]{1}[0-9 A-F]{2})), [1-8]{1}, \[0x[0-9A-Fa-f]{2}(, 0x[0-9A-Fa-f]{2}){0,7}\]\)$", cmd):
					extractionData = re.findall(r"^SendMessage\((.*?), (.*?), (.*?)\)$", cmd)
					self.send_msg(can.Message(arbitration_id=int(extractionData[0][0], 16), dlc=int(extractionData[0][1]), data=eval(extractionData[0][2])))

				elif re.match(r"^echo *\".*\"$", cmd):
					extractionData = re.findall(r"^echo *(.*?)$", cmd)
					print(extractionData[0])

				elif re.match(r"^.*\?.*:.*$", cmd):
					self.__parse_diag_msg(cmd)

				elif re.match(r"^$", cmd):
					pass

				else:
					raise Exception("line {0}: Unrecognized Command".format(PC + 1))

			if not jump:
				PC += 1

			if PC >= len(self.cmdsDict):
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

	print(main.dataLogList)
	print(main.errorLogList)
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



