#pragma version ~=0.4.0


#authorities: public(HashMap[address, uint256])

values: public(HashMap[uint256, uint256])
update_times: public(HashMap[uint256, uint256])

@deploy
def __init__():
    pass
    #self.authorities[msg.sender] = 1

@external
@view
def get_value(chain_id: uint256) -> (uint256, uint256):
    return self.values[chain_id], self.update_times[chain_id]
    
@external
def set_value(chain_id: uint256, new_value: uint256):
    self.values[chain_id] = new_value
    self.update_times[chain_id] = block.timestamp

