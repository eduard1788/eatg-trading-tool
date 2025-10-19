from ib_insync import util
from ib_utilities import IBKRApiConn
from account_info import GetInfo


###############################
### 1 Connect to IB Gateway ###
###############################

user = input("Who are you?")
client = IBKRApiConn(user)
print(f"This is your user: {client.user}")
print(f"These are your associated accounts: {client.account}")
print(f"Connection port: {client.conn_port}")
print(f"Client ID: {client.client_id}")

try:
    if client.ib.isConnected():
        print(f"Account already connected!")
    else:
        print(f"isConnected() returning: {client.ib.isConnected()}")
        print(f"Trying to connect...")
        print(f"Connecting...")
        client.ib_connect()
        print(f"Account successfully connected!")
except Exception as error:
    print(f"Error while trying to establish connection: {error}")

# input(f"{user}, Now let's disconnect. input anything.")

# client.ib_disconnect()


############################################################
### 2 Load file to update and get dictionary with sheets ###
############################################################


###########################
### 3 Get Summary sheet ###
###########################

input(f"{user}, Let's fetch the Summary df and print it. Input anything to continue...")
client_info = GetInfo()
df = client_info.get_summary_df(client.ib, client.account)
df.to_excel('C:/0.Repositories/' + 'Summary' + '.xlsx' , index = False)

input(f"{user}, Keeping connection alive...")

# 4 Get Trades sheet

# 5 Get Active Orders sheet

# 6 Get Positions sheet

# 7 Concatenate all and print

