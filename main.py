import requests
from mojang import Client
import datetime
import time
import threading


input_filename = "accounts.txt"
output_filename = "token.txt"
client_tokens = []
try:
    with open(input_filename, 'r') as input_file:
        line_count = sum(1 for line in input_file)
    with open(input_filename, 'r') as input_file, open(output_filename, 'w') as output_file:
        for line in input_file:
                line = line.strip()
                pieces = line.split(":")
                email = pieces[0]
                password = pieces[1]
                client = Client(f"{email}", f"{password}")
                bearer_token = client.bearer_token
                client_tokens.append(bearer_token)
    with open(output_filename, 'w') as output_file:
        for token in client_tokens:
            output_file.write(f"{token}\n")
except FileNotFoundError:
        print(f"O arquivo '{input_filename}' não foi encontrado.")

except Exception as e:
        print(f"Ocorreu um erro: {e}")


with open("proxy.txt", "r") as f:
    proxies = f.read().split("\n")
with open("token.txt", 'r') as f:
     tokens = f.read().split("\n")
     
headers_list = []
urls = 'https://api.minecraftservices.com/minecraft/profile/name/Summer/available'
for token in tokens:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    headers_list.append(headers)
while True:
     now = datetime.datetime.now()
     print(now.strftime("%H:%M:%S"))
     if (now.strftime("%H:%M:%S") == "21:57:00"):
          break
     time.sleep(1)
def reque():
    counter = 0
    for i in range(line_count):
        try:
            print(f"Using the proxy: {proxies[counter]}, conta{[counter]}")
            res = requests.get(urls, proxies={"sock5": proxies[counter]},headers=headers_list[counter])
            if(res.status_code == 200):
                print('Sucesso!')
        except:
            print("falha")
        finally:
            counter += 1
            counter % len(proxies)
for _ in range(2):
     threading.Thread(target=reque).start()





     