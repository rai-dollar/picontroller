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

from tests.abis import gas_oracle_v2_abi

SEPOLIA_ORACLE = oracle_addresses[11155111]#'0xCc936bE977BeDb5140C5584d8B6043C9068622A6'

REWARDS = '0xc98a372a4b1035dcc64cbd79cc63e4873c85f55a'
controller = project.RewardController.at(REWARDS)
RPC = "https://sepolia.infura.io/v3/809b114c339249a5a58cf4d058ab25a9"

w3 = Web3(HTTPProvider(RPC))

abi = gas_oracle_v2_abi

oracle = w3.eth.contract(address=SEPOLIA_ORACLE, abi=abi)

account = accounts.load("blocknative_dev")
dat_n = 7
dat = bytes.fromhex("000000000000000201963b97894802000000000000074c000000000058aabf01006b00000000000000000000000000000000000000000000000000000000079801420000000000000000000000000000000000000000000000000000000001f473b0b8dbd10edf952e4674eda638856f245d4850e8b37f41646172f68edcbc864de23c107c4fbee34f308101df9c6e925f485d338e6e31209e3c81c9428961421c000000000000000201963b97936802000000000000a4b100000000137a13a501006b000000000000000000000000000000000000000000000000000000989680014200000000000000000000000000000000000000000000000000000000000a9fcd862343ce2703e198cfbf34f52005cd8c61e5009f77062bf3e68ccaadb52e3ddc87238fd750bd62fb997c1408f080de67286a4c3d1bd70bf70cc18d18eb931c000000000000000201963b97911802000000000000000a00000000080582b301006b0000000000000000000000000000000000000000000000000000000db115014200000000000000000000000000000000000000000000000000000000003ba27be7ed61351f4ec5539ba7e62173ba93af0b827e57411367cf2008f7f059e343df963f67bbc962b30222f5a5065c775549af5c5ad2ad48fe7bce0b0f1b24081b000000000000000201963b9775c002000000000000e708000000000113cc0701006b0000000000000000000000000000000000000000000000000000000000070142000000000000000000000000000000000000000000000000000002ce95f33562ae7f55f70a03ae52e6a96f062177d7b6a70a6f5d6b4d0cba5afcaf099ab5028888ae297bc6ac674b352716e290b69b0a95c6434354c4a2ede8736f950d291b000000000000000201963b978d300200000000000000820000000000d5bf5701006b0000000000000000000000000000000000000000000000000000000000fb0142000000000000000000000000000000000000000000000000000000000001e8b1e2365e7da9b2936722c65ad3438c0b3e2dd8832a5a5404c74599203fb6a502f54b578542a5ac0e6d43893fe32af341f830dee652bebc787b44d443b32a571b000000000000000301963b979190020000000000000001000000000153ed1901006b00000000000000000000000000000000000000000000000000001441e19e0070000000000000000000000000000000000000000000000000000000003d2001420000000000000000000000000000000000000000000000000000054e08404ee7c5b14a0b7b3e4f349d256c99f254936eda87d00238819463c3baec27729559b7d89804623948f4257d576975a229842834a4b2c9eb0c7c2bc34ec25478b51b000000000000000201963b9781780200000000000021050000000001ba411c01006b0000000000000000000000000000000000000000000000000000000cb9d90142000000000000000000000000000000000000000000000000000000000032eb210bc11310b713b17f29d1423e93dc75617addb961e979934cb9806c835b1248437edec8de362c5788a6622e519ab2a9916d75c682dcbbeabf78dfaa6e71dc1b")

rewards = controller.update_oracles.call(dat, dat_n, gas=30000000)

print("eth_call rewards")
print(rewards)

import sys;sys.exit()

# update oracle w/ payload
tx = controller.update_oracles(dat, dat_n, sender=account, raise_on_revert=True, gas=30000000)
tx.show_trace(True)

print(tx.events)

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
