import json
import time
import ape
import pytest
from web3 import Web3, HTTPProvider
from eth_abi import decode

from ape import accounts, networks
from ape import Contract
from ape import project

from scripts.abis import gas_oracle_v2_abi
from scripts import params
from scripts.oracles import oracle_addresses

SEPOLIA_ORACLE = oracle_addresses[11155111]#'0xCc936bE977BeDb5140C5584d8B6043C9068622A6'
REWARDS = '0xf99F837971FAa3C48802231347d3e771ECf5002c'
controller = project.RewardController.at(REWARDS)

oracle_sepolia = Contract(SEPOLIA_ORACLE, abi=gas_oracle_v2_abi)

# Gasnet
w3 = Web3(HTTPProvider('https://rpc.gas.network'))
address = '0x4245Cb7c690B650a38E680C9BcfB7814D42BfD32'
with open('tests/gasnet_oracle_v2.json') as f:
    abi = json.load(f)['abi']
oracle_gasnet = w3.eth.contract(address=address, abi=abi)

def call_update_oracle(account, controller, dat):
    # Returns (time_reward, deviation_reward)
    # Encode the input data
    call_data = controller.update_oracle.encode_input(dat)

    # Create call dict
    call = {
        "from": account.address,
        "to": controller.address,
        "data": call_data,
    }

    # Make the eth_call
    response = networks.provider.make_request("eth_call", [call, "latest"])
    return decode(['uint256', 'uint256'], bytes.fromhex(response[2:]))

account = accounts.load("blocknative_dev")

rewards_before = controller.rewards(account)
total_rewards = controller.total_rewards()
print(f"{rewards_before=}")
print(f"{total_rewards=}")

sid = 2
cid = 1
tip_typ = params.tip_reward_type

# read gasnet
dat: bytes = oracle_gasnet.functions.getValues(sid, cid).call()
sid, cid, new_basefee_value, new_tip_value, new_ts, new_height = controller.decode(dat, tip_typ)
new_gasprice_value = new_basefee_value + new_tip_value

# get current oracle values
current_basefee_value, current_height, current_ts = oracle_sepolia.get(sid, cid, 107)
current_tip_value, current_height, current_ts = oracle_sepolia.get(sid, cid, tip_typ)
current_value = current_basefee_value + current_tip_value
print(f"{current_value=}, {current_height=}, {current_ts=}")

#eth_call update oracle
time_reward, deviation_reward = call_update_oracle(account, controller, dat)
exp_reward = time_reward + deviation_reward
print(f"{exp_reward=}")
print(f"{time_reward/10**18=}, {deviation_reward/10**18=}")

deviation = controller.calc_deviation(cid, new_gasprice_value, current_value)
print(f"{deviation/10**18=}")
import sys;sys.exit()


# update oracle w/ gasnet payload
tx = controller.update_oracle(dat, sender=account, raise_on_revert=True, gas=3000000)
tx.show_trace(True)

# get current oracle values
updated_basefee_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, 107)
updated_tip_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, tip_typ)
updated_value = updated_basefee_value + updated_tip_value
assert updated_height != current_height
assert updated_ts != current_ts

print(f"{updated_value=}, {updated_height=}, {updated_ts=}")

rewards_after = controller.rewards(account)
print(f"{rewards_after=}")
reward_emitted = (rewards_after - rewards_before)
print(f"{reward_emitted=}")
print(f"{reward_emitted/10**18=}")
