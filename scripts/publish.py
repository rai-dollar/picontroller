from ape import networks

def main():
    with networks.ethereum.sepolia.use_provider("infura"):
        networks.provider.network.explorer.publish_contract("0x05d57a15102bF7E80081321F9F5d7B8b390E887b")


