import socket, asyncio
from threading import Thread
from multiprocessing import Process
from struct import pack, unpack, calcsize
from pickle import loads
import cv2 as cv


HOST_IP = socket.gethostbyname(socket.gethostname())
HOST_PORT = 6969
HOST_ADDR = (HOST_IP, HOST_PORT)

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(HOST_ADDR)

serverSocket.listen()
print(f'listening on {HOST_ADDR}')

def show_client(addr,client_socket):
	try:
		print('CLIENT {} CONNECTED!'.format(addr))
		if client_socket: # if a client socket exists
			data = b""
			payload_size = calcsize("Q")
			while True:
				while len(data) < payload_size:
					packet = client_socket.recv(4*1024) # 4K
					if not packet: break
					data+=packet
				packed_msg_size = data[:payload_size]
				data = data[payload_size:]
				msg_size = unpack("Q",packed_msg_size)[0]
				
				while len(data) < msg_size:
					data += client_socket.recv(4*1024)
				frame_data = data[:msg_size]
				data  = data[msg_size:]
				frame = loads(frame_data)
				text  =  f"CLIENT: {addr}"
				cv.imshow(f"FROM {addr}",frame)
				key = cv.waitKey(1) & 0xFF
				if key  == ord('q'):
					break
			client_socket.close()
	except Exception as e:
		print(f"CLINET {addr} DISCONNECTED")
		pass

while True:
	clients = []
	clients.append(serverSocket.accept())
	print(f'New connection from {clients[-1][1]}')
	Process(target=show_client, args=(clients[-1][1],clients[-1][0])).start()