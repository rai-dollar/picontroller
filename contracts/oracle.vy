#pragma version ~=0.4.0


#authorities: public(HashMap[address, uint256])

values: public(HashMap[uint64, uint256])
heights: public(HashMap[uint64, uint64])
update_times: public(HashMap[uint64, uint48])

@deploy
def __init__():
    pass
    #self.authorities[msg.sender] = 1

@external
@view
def get_value(chain_id: uint64) -> (uint256, uint64, uint48):
    return self.values[chain_id], self.heights[chain_id], self.update_times[chain_id]
    
@external
def set_value(chain_id: uint64, new_value: uint256, height: uint64):
    self.values[chain_id] = new_value
    self.heights[chain_id] = height
    self.update_times[chain_id] = convert(block.timestamp, uint48)

