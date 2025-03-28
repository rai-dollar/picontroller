from ape import project
from eth_abi import encode
from scripts import params
from scripts.oracles import oracle_addresses

# Get the constructor inputs from the ABI
abi = project.RewardController.contract_type
constructor_abi = abi.constructor

# Get the expected input types
input_types = [inp.type for inp in constructor_abi.inputs]
print(input_types)

# Your constructor arguments
#['int256', 'int256', 'int256', 'int256', 'int256', 'uint256', 'uint256', 'uint256', 'uint256', 'address', 'int256[5]']
args = [params.kp,
            params.ki,
            params.co_bias,
            params.output_upper_bound,
            params.output_lower_bound,
            params.target_time_since,
            params.reward_type,
            params.min_reward,
            params.max_reward,
            params.default_window_size,
            oracle_addresses[11155111],
            params.coeff]  # Fill in with actual args

# Encode them
encoded = encode(input_types, args)
print(encoded.hex())
