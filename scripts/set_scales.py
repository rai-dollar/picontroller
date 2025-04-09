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

REWARDS = '0xc98a372a4b1035dcc64cbd79cc63e4873c85f55a'
controller = project.RewardController.at(REWARDS)

def set_scales(account, controller, params):
    scales = list(zip(params.scales.keys(), params.scales.values()))
    controller.set_scales(scales, sender=account)
    for s in params.scales.keys():
        print(s, controller.scales(s))

account = accounts.load("blocknative_dev")
set_scales(account, controller, params)
