from eth_abi import encode

# Define the constructor argument types and values
types = ["int256"]
values = [-5*10**18]

encoded = encode(types, values)
print(encoded.hex())
