from mojangauth.mojang.client import MojangAuth
import time
import datetime
import requests
import threading
from pyfiglet import Figlet
from termcolor import colored
text = Figlet(font='big')
print(colored(text.renderText('SunFlower Claimer'),'yellow'))
input_filename = "accounts.txt"
output_filename = "token.txt"
client_tokens = []
username = "Test"
session = {}
try:
    print("Autenticando contas...")
    with open(input_filename, 'r') as input_file:
        line_count = sum(1 for line in input_file)
    with open(input_filename, 'r') as input_file, open(output_filename, 'w') as output_file:
        for line in input_file:
                line = line.strip()
                pieces = line.split(":")
                email = pieces[0]
                password = pieces[1]
                client = MojangAuth(f"{email}", f"{password}")
                bearer_token = client.bearer_token
                output_file.write(f"{bearer_token}\n")
                client_tokens.append(bearer_token)
                time.sleep(2)
except FileNotFoundError:
        print(f"O arquivo '{input_filename}' não foi encontrado.")

except Exception as e:
        print(f"Ocorreu um erro: {e}")


with open("proxy.txt", "r") as f:
    proxies = f.read().split("\n")
with open("token.txt", 'r') as f:
     tokens = f.read().split("\n")

headers_list = []
urls = f'https://api.minecraftservices.com/minecraft/profile/name/{username}/available'
url2 = f'https://api.minecraftservices.com/minecraft/profile/name/{username}'
for token in tokens:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    headers_list.append(headers)

def reque():
    counter = 1
    for i in range(line_count):
        try:
            print(f"Using the proxy: {proxies[counter]}, conta{[counter]}",counter)
            res = requests.get(urls, proxies={"sock5": proxies[counter-1]},headers=headers_list[counter])
            data = res.json()
            if data['status'] == 'AVAILABLE':
                get_username = requests.put(url2,proxies={"sock5": proxies[counter]},headers=headers_list[0])
                if get_username.status_code == '200':
                     print("SUCESSO")
                else:
                     print("Não pegou")
            else:
                 print("Duplicado")
        except:
            print("falha")
        finally:
            counter += 1
            counter % len(proxies)
print("Começando requests...")
for _ in range(15):
     threading.Thread(target=reque).start()
