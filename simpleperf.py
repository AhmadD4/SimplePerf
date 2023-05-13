import socket
import threading
import time
import argparse
import re
import sys
import _thread as thread
import ipaddress


#Set the buffer size to 1000
BUFFER_SIZE = 1000

#Creating handleClient function that handle an individual client connection.
def handleClient(connection, address, format, convert):
    #Define the received_bytes from the client
    received_bytes = 0
    #start the timer
    start_time = time.time()

    while True:
        data = connection.recv(BUFFER_SIZE) #Receive data in chunks of size '1000 B'
        #Check if the client send "BYE" message, that all data has been received? stop!
        if "BYE" in data.decode():
            break
        #Track the number of bytes received and add them to the received_bytes variable!
        received_bytes += len(data)

    #Stop the timer
    end_time = time.time()
    total_duration = end_time - start_time
    #Calculating from bytes per second to megabits per second. 
    #Multiplying by 8 converts from bytes per second to bits per second. 
    #Dividing the result by 1000000 converts from bits per second to megabits per second. 
    rate = (received_bytes / total_duration) * 8 / 1000000
    #Calculating the received_bytes and converts to the chosen format. (conver will be in server())
    received_size = received_bytes / convert

    #Print results to console
    #Here, address[0] is the IP address of the client, and address[1] is the port number of the client.
    print('-----------------------------------------------------------------------')
    print(f'      ID             Interval          Received             Rate')
    print(f'{address[0]}:{address[1]}     0.0 - {total_duration:.1f}       {received_size:.2f} {format}         {rate:.2f} Mbps')
    print('-----------------------------------------------------------------------')

    #Send acknowledgement message to client
    connection.send(b'ACK')
    #Close the connection
    connection.close()


def server(args):
    #Define the IP address, port number and format from the entered data (argparse)
    host = args.bind #default: 127.0.0.1
    port = args.port #in range [1024, 65535], default: 8088
    format = args.format #[B, KB, MB], default: MB

    #Error message for ip-address
    try:
        ipaddress.ip_address(host)
    except:
        print(f"The IP address is {host} not valid")
        sys.exit

    #Error message for port
    if port not in range(1024, 65535):
        print('The port number should be in range [1024, 65525]!')
        return
    
    #Error message for format
    if format not in ['B', 'KB', 'MB']:
        print('Invaild format argument! Allowed formats: B, KB, MB')
        return

    #Calculating to the chosen format. 
    #The line of code uses the index() method to find the position of the format string 
    #in the list of format options ['B', 'KB', 'MB'], and raises 1000 to the power of that position. 
    #For example, the default format is 'MB', convert will be set to 1000000 (1000 to the power of 2, since 'MB' is the third item in the list).
    convert = 1000 ** ['B', 'KB', 'MB'].index(format)

    #Create a new 'socket' object for the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        #Bind it to the host and port variables
        server_socket.bind((host, port))
    except:
        #Print error message
        print("Bind failed. Error :")
        sys.exit

    #Start listening for incoming connections
    server_socket.listen(5)
    #It then prints a message to the console indicating that the server is listening.
    print('---------------------------------------------------------')
    print(f'A simpleperf server is listening on port {port}')
    print('---------------------------------------------------------')

    #this is the main loop of the server
    while True:
        #It waits for a client to connect, accept the connection...
        connectionSocket, addr = server_socket.accept()
        #Print the message that is the server is connected to the client...
        print('-----------------------------------------------------------------------------')
        print(f'A simpleperf client with {addr[0]}:{addr[1]} is connected with {host}:{port}')
        print('-----------------------------------------------------------------------------')
        #Create a new thread to handle the client connection
        client_thread = threading.Thread(target=handleClient, args=(connectionSocket, addr, format, convert))
        client_thread.start()
    
def client(args):
    #Define the IP address, port number, format and time from the entered data (argparse)
    host = args.serverip #default: 127.0.0.1
    port = args.port #in range [1024, 65535], default: 8088
    format = args.format #[B, KB, MB], default: MB
    total_duration = args.time #the total duration in seconds for which data should be generated

    #Error message for ip-address
    try:
        ipaddress.ip_address(host)
    except:
        print(f"The IP address is {host} not valid")
        sys.exit

    #Error message for port
    if port not in range(1024, 65535):
        print('The port number should be in range [1024, 65525]!')
        return
    
    #Error message for format
    if format not in ['B', 'KB', 'MB']:
        print('Invaild format argument! Allowed formats: B, KB, MB')
        return

    #Error message for total duration
    if total_duration < 0:
        print('The total duration must be positiv!')
        return

    #Calculating to the chosen format. 
    #The line of code uses the index() method to find the position of the format string 
    #in the list of format options ['B', 'KB', 'MB'], and raises 1000 to the power of that position. 
    #For example, the default format is 'MB', convert will be set to 1000000 (1000 to the power of 2, since 'MB' is the third item in the list).
    convert = 1000 ** ['B', 'KB', 'MB'].index(format)

    #Define the sent_bytes to the server
    sent_bytes = 0
    #Start the timer
    start_time = time.time()

    #Prints a message to the console indicating that the client is connecting to the server...
    print('----------------------------------------------------------------')
    print(f'A simpleperf client connecting to server {host}, port {port}...')
    print('----------------------------------------------------------------')
    
    
    #Create a single socket connection to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        #Connect
        client_socket.connect((host,port))
    except:
        #Error message
        print("ConnectionError")
        sys.exit()

    #Prints a message to the console indicating that the client is connecting to the server...
    print(f'Client connected with {host} port {port}')

    #'Num' mode:
    #This will transfer specific data from the client to the server, and calculate the time it takes
    if args.num:
        num = args.num
        #'re' module is used to parse the ‘num’ argument into a number and unit 
        match = re.match(r"([0-9]+)([a-z]+)", num, re.I)
        if match:
            #If the pattern matched, extract the number and unit from the match object 
            #and assign them to num and unit variables
            num, unit = match.groups()
            #The unit is converted to uppercase to allow case-insensitive matching
            unit_convert = 1000 ** ['B', 'KB', 'MB'].index(unit.upper())
            #Calculate the total size of data to be sent by multiplying the parsed number with the conversion factor.
            no_of_bytes = int(num) * unit_convert
        else:
            #Error message for num mode
            print('invaild num argument!')
            return
        
        #Sending the specific number of data to the server
        while sent_bytes < no_of_bytes:
            data = bytes(BUFFER_SIZE) 
            client_socket.send(data) 
            sent_bytes += len(data) 

        #Send acknowldgement message when it finish with sending
        client_socket.send(b'BYE') #Send a "BYE" message to signal the end of data transmission
        client_socket.recv(BUFFER_SIZE) #Receive a response from the client to confirm the end of data transmission
        client_socket.close 

        #Calculate the duration from start time to the end
        end_time = time.time()
        duration = end_time - start_time

        #Calculate the rate and size of transfered data
        rate = (sent_bytes / duration) * 8 / 1000000
        sent_size = no_of_bytes / convert

        #Then, print the result
        print('-----------------------------------------------------------------------')
        print(f'     ID               Interval       Transfer          Bandwidth')
        print(f'{host}:{port}       0.0 - {duration:.1f}       {sent_size:.2f} {format}         {rate:.2f} Mbps')
        print('-----------------------------------------------------------------------')            

    #Interval mode:
    #it divides the test into equal intervals of the specified duration, sending data in each interval and measuring the transfer rate for each interval
    elif args.interval:
        z = args.interval

        #Calculates the number of intervals that the test should run for based on the total duration of the test and the specified interval time. 
        # It uses integer division (//) to round down the result to a whole number.
        intervals = total_duration // z

        #Initialize some variables used in the loop that runs the test for each interval. 
        i_sent_bytes = 0
        i_start_time = time.time()
        timer = time.time()

        #Print a header for the output table that will be displayed during the test.
        print(f'     ID             Interval         Transfer          Bandwidth')

        #For loop that will run once for each interval
        for i in range(intervals):
            zr = time.time() #This will be used to measure the interval duration

            #This loop sends data over the network socket until the time for the interval has elapsed
            while time.time() - zr < z:
                data = bytes(BUFFER_SIZE)
                client_socket.send(data)
                i_sent_bytes += len(data) #i_sent_bytes keeps track of the total number of bytes sent during the interval

            #Calculate the duration, transfer rate, and transfer size for the current interval based on the number of bytes sent and the duration of the interval.
            i_end_time = time.time()
            i_duration = i_end_time - start_time
            i_rate = (i_sent_bytes / i_duration) * 8 / 1000000
            i_no_of_bytes = i_sent_bytes / convert

            #Print a row of the output table for the current interval
            print(f'{host}:{port}     {i_start_time - timer:.1f} - {i_end_time - timer:.1f}       {i_no_of_bytes:.2f} {format}         {i_rate:.2f} Mbps')


            i_start_time = i_end_time #Reset this variable to reuse it in the loop
            sent_bytes += i_sent_bytes #Save the total byte that has been sent so far
            i_sent_bytes = 0 #Reset this variable to reuse it in the loop

        
        print('-----------------------------------------------------------------------')

        #Close the network socket
        client_socket.send(b'BYE')
        client_socket.recv(BUFFER_SIZE)
        client_socket.close()


        no_of_bytes = sent_bytes / convert #Calculate the total size of the data that was sent
        total_duration = i_end_time - start_time #Calculate the total duration
        total_rate = (sent_bytes / total_duration) * 8 / 1000000 #Calculate the average data transfer rate

        #Print the total results
        print('-----------------------------------------------------------------------')
        print(f'     ID               Interval          Transfer          Bandwidth')
        print(f'{host}:{port}       0.0 - {i_end_time - timer:.1f}       {no_of_bytes:.2f} {format}         {total_rate:.2f} Mbps')
        print('-----------------------------------------------------------------------')

    #If no thing was specified by user, so the client will send data in normal way to server in specific time and close the socket connection
    else:
        while time.time() - start_time < total_duration:
            data = bytes(BUFFER_SIZE)
            client_socket.send(data)
            sent_bytes += len(data)

        
        client_socket.send(b'BYE')
        client_socket.recv(BUFFER_SIZE)
        client_socket.close()

        end_time = time.time()
        duration = end_time - start_time

        rate = (sent_bytes / duration) * 8 / 1000000
        no_of_bytes = sent_bytes / convert

        print('-----------------------------------------------------------------------')
        print(f'     ID               Interval          Transfer          Bandwidth')
        print(f'{host}:{port}       0.0 - {duration:.1f}       {no_of_bytes:.2f} {format}         {rate:.2f} Mbps')
        print('-----------------------------------------------------------------------')

def main():
    #Create an ArgumentParse to parse the command line arguments
    parser = argparse.ArgumentParser(description='SimplePerf that measure the bandwidth and transfer rate.')
    #Add various command line arguments
    parser.add_argument('-s', '--server', action='store_true', help='enable server mode')
    parser.add_argument('-c', '--client', action='store_true', help='enable client mode')
    parser.add_argument('-b', '--bind', default='127.0.0.1', help='the IP address to bind to')
    parser.add_argument('-I', '--serverip', help='the IP address of the server to connect to')
    parser.add_argument('-p', '--port', type=int, default=8088, help='the port number to use')
    parser.add_argument('-t', '--time', type=int, default=10, help='the duration of the test in seconds')
    parser.add_argument('-P', '--parallel', type=int, default=1, help='the number of parallel connections to use')
    parser.add_argument('-f', '--format', choices=['B', 'KB', 'MB'], default='MB', help='the transfer rate format to use')
    parser.add_argument('-n', '--num', metavar="<number><unit>", default=0, help="number of bytes to send")
    parser.add_argument('-i', '--interval', type=int, default=0, help='the interval to print results in seconds')
    #Parse the command line arguments
    args = parser.parse_args()

    #A server or client cannot run –s and –c at the same time
    if args.server and args.client:
        print('Cannot specify both server and client mode')
        return

    #Check if neither server nor client mode is enabled, and print an error message if so
    if not args.server and not args.client:
        print('Must specify either server or client mode')
        return

    #if server mode is enabled, call the server() function
    if args.server:
        server(args)

    #if client mode is enabled, call the client() function
    if args.client:
        if args.parallel > 1:
            for i in range(args.parallel):
                parallel = threading.Thread(target = client, args= (args,))
                parallel.start()
        else:

            client(args)

#Run the main function if this script is being run directly
if __name__ == '__main__':
    main()     