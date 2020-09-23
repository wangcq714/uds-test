# #!/usr/bin/env python

import uds 
from uds import Uds
from time import sleep


SupportServers = [0x01, 0x2, 0x3, 0x04, 0x07, 0x09, 0x0A, 0x10, 0x11, 0x14, 0x19, 0x22, 0x27, 0x2E, 0x2F, 0x31, 0x3E]


class Main(object):
	"""docstring for main"""
	def __init__(self):
		super(Main, self).__init__()


	def main(self):
		# This creates a Uds object manually
		rawEcu = Uds()

		for ServerID in range(0xFF+1):
			try:
				# This sends the request for Ecu Serial Number
				ResData = rawEcu.send([ServerID])
				if ServerID in SupportServers:
					if ResData is not None \
					   and ((ResData[0] == 0x7F and ResData[1] == ServerID) or ResData[0] == ServerID + 0x40):
						print("Server {0:02X} Test OK".format(ServerID))
						pass
					else:
						print("Server {0:02X} Test Failed: {1}".format(ServerID, ResData))
				else:
					if ResData is not None \
					   and (ResData[0] == 0x7F and ResData[1] == ServerID and ResData[2] == 0x11):
						print("Server {0:02X} Test OK".format(ServerID))
						pass
					else:
						print("Server {0:02X} Test Failed: {1}".format(ServerID, ResData))
			except Exception as ex:
				print("Server {0:02X} Test Failed: {1}".format(ServerID, ex))
				continue

		rawEcu.disconnect()
		sleep(1)
		rawEcu = Uds()
		
		for ServerID in range(0xFF+1):
			try:
				# This sends the request for Ecu Serial Number
				ResData = rawEcu.send([ServerID], functionalReq=True)
				if ServerID in SupportServers:
					if ResData is not None \
					   and ((ResData[0] == 0x7F and ResData[1] == ServerID) or ResData[0] == ServerID + 0x40):
						print("Server {0:02X} Test OK".format(ServerID))
						pass
					else:
						print("Server {0:02X} Test Failed: {1}".format(ServerID, ResData))
				else:
					if ResData is not None \
					   and (ResData[0] == 0x7F and ResData[1] == ServerID and ResData[2] == 0x11):
						print("Server {0:02X} Test OK".format(ServerID))
						pass
					else:
						print("Server {0:02X} Test Failed: {1}".format(ServerID, ResData))
			except Exception as ex:
				# print(ex)
				if str(ex) == "Timeout in waiting for message":
					print("Server {0:02X} Test OK".format(ServerID))
				else:
					print("Server {0:02X} Test Failed: {1}".format(ServerID, str(ex)))
				continue


if __name__ == "__main__":
   
	main = Main()
	main.main()
	



