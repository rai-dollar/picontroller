from web3 import Web3, HTTPProvider
import json
# Configure w3, e.g., w3 = Web3(...)

w3 = Web3(HTTPProvider('https://rpc.gas.network'))
address = '0x4245Cb7c690B650a38E680C9BcfB7814D42BfD32'

with open('gas_oracle_v2.json') as f:
    abi = json.load(f)['abi']
#abi = '[{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"address","name":"minter_","type":"address"},...'
contract_instance = w3.eth.contract(address=address, abi=abi)

# read state:
ret =contract_instance.functions.getValues(2,1).call()
print(ret)
