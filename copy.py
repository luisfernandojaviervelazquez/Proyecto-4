###############################################################################
#
# Filename: copy.py
# Author: Jose R. Ortiz and ... (hopefully some students contribution)
# Student Contributor: Luis Fernando Javier Velazquez Sosa
# Description:
# 	Copy client for the DFS
#
#

import socket
import sys
import os.path

from Packet import *

def usage():
	print ("""Usage:\n\tFrom DFS: python %s <server>:<port>:<dfs file path> <destination file>\n\tTo   DFS: python %s <source file> <server>:<port>:<dfs file path>""" % (sys.argv[0], sys.argv[0]))
	sys.exit(0)

def copyToDFS(address, fname, path):
	""" Contact the metadata server to ask to copu file fname,
	    get a list of data nodes. Open the file in path to read,
	    divide in blocks and send to the data nodes. 
	"""

	# Create a connection to the data server
	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock.connect(address)
	# Fill code

	# Read file
	fd = open(path, "rb")#rb es read bytes
	fileData = fd.read()
	fd.close()
	# Fill code

	# Create a Put packet with the fname and the length of the data,
	# and sends it to the metadata server
	fileSize = len(fileData) #to know the length of the data
	pack = Packet()
	pack.BuildPutPacket(fname,fileSize)
	sock.sendall(bytes(pack.getEncodedPacket(),"utf-8"))
	# Fill code

	# If no error or file exists
	received = sock.recv(1024)
	sock.close()

	if received == "DUP":
		print("This is a Duplicated File")
		return
	# Get the list of data nodes.
	else:
		pack.DecodePacket(received)
		dataNodes = pack.getDataNodes()

	# Divide the file in blocks
		blocks = []
		dataNodeSize = len(dataNodes)
		blockSize = int(fileSize/dataNodeSize)

		#aqui hago un for que va de 0 hasta fileSize y incrementa la cantidad de blockSize
		for i in range(0,fileSize,blockSize):
			if (i/blockSize)+1 == dataNodeSize:
				#aqui busca y le da append al data despues de donde esta el valor de i
				blocks.append(fileData[i:])
				#y rompe el loop para seguir al lo proximó
				break
			else:
				#empieza desde indice i y acaba en el indice i+blockSize
				blocks.append(fileData[i:i+blockSize])

	# Send the blocks to the data servers
	for i in dataNodes:
		#create a connection
		dataNodeSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		dataNodeSocket.connect((i[0],i[1]))
		pack.BuildPutPacket(fname,fileSize)
		dataNodeSocket.sendall(bytes(pack.getEncodedPacket(),"utf-8"))
		received = dataNodeSocket.recv(1024)
		dataBlock = blocks.pop(0)

		if received == "OK":
			dataSize = len(dataBlock)
			dataNodeSocket.send(bytes(dataSize))
			received = dataNodeSocket.recv(1024)
			while (dataBlock):
				dataNodeSocket.sendall(dataBlock[0:1024])
				dataBlock = dataBlock[1024:]
				
			dataNodeSocket.sendall(bytes("OK"))
			received = dataNodeSocket.recv(1024)
			i.append(received)
		dataNodeSocket.close()

	# Fill code

	# Notify the metadata server where the blocks are saved.
	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock.connect(address)
	pack.BuildDataBlockPacket(fname,dataNodes)
	sock.sendall(bytes(pack.getEncodedPacket(),"utf-8"))
	sock.close()
	# Fill code
	
def copyFromDFS(address, fname, path):
	""" Contact the metadata server to ask for the file blocks of
	    the file fname.  Get the data blocks from the data nodes.
	    Saves the data in path.
	"""
	# Contact the metadata server to ask for information of fname
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(address)
	packet = Packet()
	packet.BuildGetPacket(fname)
	sock.sendall(bytes(packet.getEncodedPacket(),"utf-8"))
	# Fill code

	# If there is no error response Retreive the data blocks
	recieved = sock.recv(1024)
	packet.DecodePacket(recieved)
	dataNodeList = packet.getDataNodes()
	# Fill code

    # Save the file
	file = open(path,'wb')#write byte
	for dataNode in dataNodeList:
		dataNodeSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		dataNodeSocket.connect((dataNode[0],dataNode[1]))
		packet.BuildDataBlockPacket((dataNode[2]))
		dataNodeSocket.sendall(bytes(packet.getEncodedPacket(),"utf-8"))
		dataNodeSize = int(dataNodeSocket.recv(1024))
		dataNodeSocket.sendall(bytes("OK"))

		data = 0
		information = b""
		while data > dataNodeSize:
			recieved = dataNodeSocket.recv(1024)
			information = information + recieved
			data+=1024
			dataNodeSocket.sendall(bytes("OK"))
		file.write(information)
		dataNodeSocket.close()
	file.close()
	# Fill code

if __name__ == "__main__":
#	client("localhost", 8000)
	if len(sys.argv) < 3:
		usage()

	file_from = sys.argv[1].split(":")
	file_to = sys.argv[2].split(":")

	if len(file_from) > 1:
		ip = file_from[0]
		port = int(file_from[1])
		from_path = file_from[2]
		to_path = sys.argv[2]

		if os.path.isdir(to_path):
			print ("Error: path %s is a directory.  Please name the file." % to_path)
			usage()

		copyFromDFS((ip, port), from_path, to_path)

	elif len(file_to) > 2:
		ip = file_to[0]
		port = int(file_to[1])
		to_path = file_to[2]
		from_path = sys.argv[1]

		if os.path.isdir(from_path):
			print ("Error: path %s is a directory.  Please name the file." % from_path)
			usage()

		copyToDFS((ip, port), to_path, from_path)


