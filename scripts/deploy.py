from scripts.oracles import oracle_addresses
from scripts import params
from web3 import Web3, HTTPProvider
import ape
from ape import accounts
from ape import project

from ape_accounts import import_account_from_private_key

def deploy(params, chain_id, owner, project):
    controller = owner.deploy(project.RewardController,
            params.kp,
            params.ki,
            params.co_bias,
            params.output_upper_bound,
            params.output_lower_bound,
            params.target_time_since,
            params.min_reward,
            params.max_reward,
            params.default_window_size,
            oracle_addresses[chain_id],
            params.coeff,
            publish=True,
            sender=owner)

    controller.set_scales(params.scales.keys(), params.scales.values(), sender=owner)

    return controller


def main():
    #web3 = Web3(HTTPProvider('https://sepolia.infura.io/v3/809b114c339249a5a58cf4d058ab25a9'))
    #print(f"chainid: {web3.eth.chain_id}")
    account = accounts.load("blocknative_dev")
    #account = accounts.load("local_dev")

    #pk = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
    #account = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

    controller = deploy(params, 11155111, account, project)
    print(f"{controller.address=}")
