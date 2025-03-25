import json
import time
import ape
import pytest
from web3 import Web3, HTTPProvider

from ape import accounts
from ape import Contract
from ape import project

from scripts.abis import gas_oracle_v2_abi
from scripts import params
from scripts.oracles import oracle_addresses

SEPOLIA_ORACLE = oracle_addresses[11155111]#'0xCc936bE977BeDb5140C5584d8B6043C9068622A6'

controller = project.RewardController.at("0xe48555990092ff02a7cdd0e6b772fba9b7a3e9fd")

account = accounts.load("blocknative_dev")

def set_scales(account, controller, params):
    scales = list(zip(params.scales.keys(), params.scales.values()))
    controller.set_scales(scales, sender=account)
    for s in params.scales.keys():
        print(s, controller.scales(s))

# Set scales

set_scales(account, controller, params)
import sys;sys.exit()

oracle_sepolia = Contract(SEPOLIA_ORACLE, abi=gas_oracle_v2_abi)

w3 = Web3(HTTPProvider('https://rpc.gas.network'))
address = '0x4245Cb7c690B650a38E680C9BcfB7814D42BfD32'

with open('tests/gasnet_oracle_v2.json') as f:
    abi = json.load(f)['abi']

oracle_gasnet = w3.eth.contract(address=address, abi=abi)

sid = 2
cid = 10
typ = 107

# read gasnet
a: bytes = oracle_gasnet.functions.getValues(sid, cid).call()

# get current oracle values
value, height, ts = oracle_sepolia.get(sid, cid, typ)
assert value !=0

# update #1
tx = controller.update_oracle(a, sender=account, raise_on_revert=True, gas=3000000)
tx.show_trace(True)

# get current oracle values
updated_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, typ)
assert updated_value != value
assert updated_height != height
assert updated_ts != ts
