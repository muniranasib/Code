import socket

HOST = "192.168.12.66"
PORT = 2222 #Porten som serveren skal lytte til for tilkobling

Server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Definerer Server som en socketvariabel

Server.bind((HOST, PORT)) #Binder variabelen til HOST adresse og PORT

Server.listen() #Lytter etter tilkoblinger

Client, addr = Server.accept() #Aksepterer tilkobling og opretter en socketvariabel Client, lagrer IP adressen til Client i variabelen addr


print(addr) #Printer Client adresse

data = Client.recv(1024) #Venter på data fra Client og lagrer mottatt data i variabelen data

print(data) #Printer mottat data
Server.close() #Lukker serveren



