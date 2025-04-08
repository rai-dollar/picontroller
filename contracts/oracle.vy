#pragma version ~=0.4.0

import store

values: public(HashMap[uint64, HashMap[uint16, uint240]])
heights: public(HashMap[uint64, uint64])
update_times: public(HashMap[uint64, uint48])

@deploy
def __init__():
    pass

@external
@view
def get(sid: uint8, cid: uint64, typ: uint16) -> (uint240, uint64, uint48):
    return self.values[cid][typ], self.heights[cid], self.update_times[cid]
    
#@external
#def set_value(chain_id: uint64, new_value: uint256, height: uint64):
#    self.values[cid] = new_value
#    self.heights[chain_id] = height
#    self.update_times[chain_id] = convert(block.timestamp, uint48)

@external
def storeValues(dat: Bytes[4096]):
    sid: uint8 = 0
    cid: uint64 = 0
    basefee_val: uint240 = 0
    tip_val: uint240 = 0
    ts: uint48 = 0
    h: uint64 = 0

    sid, cid, basefee_val, tip_val, ts, h = store._decode(dat, 322)

    self.values[cid][107] = basefee_val
    self.values[cid][322] = tip_val
    self.heights[cid] = h
    self.heights[cid] = h
    self.update_times[cid] = ts
