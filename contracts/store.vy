#pragma version ~=0.4.0
event TypeVal:
    typ: uint16
    val: uint256

event StoreValues:
    time: uint256


event StoreValuesHeader:
    payload_len: uint16
    scid: uint88
    ts: uint48
    height: uint64

struct Record:
    height: uint64
    timestamp: uint48
    value: uint240

pStore: public(HashMap[uint88, Record])
signers: public(HashMap[address, bool])

#@internal
#@pure
#def get_key(systemid: uint8, cid: uint64, typ: uint16) -> uint88:
#    key_uint256: uint256 = (convert(systemid, uint256) << 64) | convert(cid, uint256)
#    key_uint256 = (key_uint256 << 16) | convert(typ, uint256)
#    return convert(key_uint256, uint88)

@external
@pure
def get_key(sid: uint8, cid: uint64, typ: uint16) -> uint88:
    return self._get_key(sid, cid, typ)

@internal
@pure
def _get_key(sid: uint8, cid: uint64, typ: uint16) -> uint88:
    scid_uint256: uint256 = convert(sid, uint256)  # Step 1: Start with sid
    scid_uint256 = scid_uint256 << 64  # Step 2: Shift sid left by 64 bits
    scid_uint256 = scid_uint256 | convert(cid, uint256)  # Step 3: Add cid
    scid_uint256 = scid_uint256 << 16  # Step 4: Shift left by 16 bits
    #scid_uint256 = scid_uint256 | convert(plen, uint256)  # Step 5: Add plen

    return self._append_type(convert(scid_uint256, uint88), typ)

@external
@view
def get(systemid: uint8, cid: uint64, typ: uint16) -> (uint256, uint64, uint48):
    key: uint88 = self._get_key(systemid, cid, typ)  # Compute the storage key
    s: Record = self.pStore[key]  # Fetch the stored record
    return convert(s.value, uint256), s.height, s.timestamp

@external
@pure
def decode_header(dat: Bytes[4096]) -> (uint16, uint88, uint48, uint64):
    return self._decode_header(dat)

@internal
@pure
def _decode_header(dat: Bytes[4096]) -> (uint16, uint88, uint48, uint64):
    h: uint64 = convert(slice(dat, 23, 8), uint64)  # Extract last 8 bytes of 32-byte block, excluding version
    cid: uint64 = convert(slice(dat, 15, 8), uint64)  # Extract 8 bytes before h
    sid: uint8 = convert(slice(dat, 14, 1), uint8)  # Extract 1 byte before cid
    ts: uint48 = convert(slice(dat, 8, 6), uint48)  # Extract 6 bytes before sid
    plen: uint16 = convert(slice(dat, 6, 2), uint16)  # Extract 2 bytes before ts

    scid_uint256: uint256 = convert(sid, uint256)  # Step 1: Start with sid
    scid_uint256 = scid_uint256 << 64  # Step 2: Shift sid left by 64 bits
    scid_uint256 = scid_uint256 | convert(cid, uint256)  # Step 3: Add cid
    scid_uint256 = scid_uint256 << 16  # Step 4: Shift left by 16 bits

    return plen, convert(scid_uint256, uint88), ts, h


@external
@pure
def decode_sid_cid(dat: Bytes[4096]) -> (uint8, uint64, uint16, uint48, uint64):
    return self._decode_sid_cid(dat)

@internal
@pure
def _decode_sid_cid(dat: Bytes[4096]) -> (uint8, uint64, uint16, uint48, uint64):
    h: uint64 = convert(slice(dat, 23, 8), uint64)  # Extract last 8 bytes of 32-byte block, excluding version
    cid: uint64 = convert(slice(dat, 15, 8), uint64)
    sid: uint8 = convert(slice(dat, 14, 1), uint8)
    plen: uint16 = convert(slice(dat, 6, 2), uint16)
    ts: uint48 = convert(slice(dat, 8, 6), uint48)  # Extract 6 bytes before sid

    return sid, cid, plen, ts, h

@internal
@pure
def check_signature(plen: uint16, offset: uint256, signer: address, dat: Bytes[4096]):
    siglen: uint256 = 32 + 32 * convert(plen, uint256)
    kec: bytes32 = keccak256(slice(dat, offset, siglen))

    r: bytes32 = convert(slice(dat, offset + siglen, 32), bytes32)
    s: bytes32 = convert(slice(dat, offset + siglen + 32, 32), bytes32)
    v: uint8 = convert(slice(dat, offset + siglen + 64, 1), uint8)

    assert v == 27 or v == 28, "Invalid signer v param"
    assert ecrecover(kec, v, r, s) == signer, "ECDSA: invalid signature"

@external
@pure
def append_type(scida: uint88, typ: uint16) -> uint88:
    return self._append_type(scida, typ)

@internal
@pure
def _append_type(scida: uint88, typ: uint16) -> uint88:
    scidb: uint256 = convert(scida, uint256)  # ✅ Ensure safe conversion
    scidb = (scidb >> 16) << 16  # ✅ Truncate lower 16 bits
    scidb = scidb | convert(typ, uint256)  # ✅ Add `typ`

    assert scidb < 2**88, "scidb overflow!"  # ✅ Prevent overflow
    return convert(scidb, uint88)  # ✅ Convert back safely

@external
@pure
def prepare_header(
    version: uint8,
    height: uint64,
    chain_d: uint64,
    system_id: uint8,
    ts: uint48,
    plen: uint16
) -> bytes32:
    new_buffer: uint256 = 0
    
    new_buffer = (new_buffer << 16) | convert(plen, uint256)       # shift left by 16 bits for uint16
    new_buffer = (new_buffer << 48) | convert(ts, uint256)        # shift left by 48 bits for uint48
    new_buffer = (new_buffer << 8) | convert(system_id, uint256)  # shift left by 8 bits for uint8
    new_buffer = (new_buffer << 64) | convert(chain_d, uint256)  # shift left by 64 bits for uint64
    new_buffer = (new_buffer << 64) | convert(height, uint256)    # shift left by 64 bits for uint64
    new_buffer = (new_buffer << 8) | convert(version, uint256)    # shift left by 8 bits for uint8

    return convert(new_buffer, bytes32)
    
@external
@pure
def encode_parameter(typ: uint16, val: uint256) -> bytes32:
    assert val < 2**240, "Val must fit within 240 bits"
    
    new_buffer: uint256 = 0

    new_buffer = convert(typ, uint256) << 240  # Shift `typ` to the top 16 bits
    new_buffer = new_buffer | val                 # OR `value` into lower bits

    return convert(new_buffer, bytes32)

@external
@pure
def decode(dat: Bytes[4096], requested_typ: uint16) -> (uint8, uint64, uint16, uint240, uint48, uint64):
    return self._decode(dat, requested_typ)

@internal
@pure
def _decode(dat: Bytes[4096], requested_typ: uint16) -> (uint8, uint64, uint16, uint240, uint48, uint64):
    # system_id, c_id, type, val, ts
    assert requested_typ != 0, "requested_typ can't be zero"
    sid: uint8 = 0
    cid: uint64 = 0
    plen: uint16 = 0
    ts: uint48 = 0
    h: uint64 = 0

    sid, cid, plen, ts, h = self._decode_sid_cid(dat)
    plen_int: uint256 = convert(plen, uint256)

    typ: uint16 = 0
    val: uint240 = 0
    for j: uint256 in range(plen_int, bound=256):

        val_b: Bytes[32] = slice(dat, 32 + j*32, 32)  
        typ = convert(slice(val_b, 0, 2), uint16)
        val = convert(slice(val_b, 2, 30), uint240)
        # stop at first typ match
        if typ == requested_typ:
            break

    assert typ == requested_typ, "requested_typ not present"

    return sid, cid, typ, val, ts, h

@external
def store_values(dat: Bytes[4096]):
    plen: uint16 = 0
    scid: uint88 = 0
    ts: uint48 = 0
    h: uint64 = 0
    v: uint8 = 0

    plen, scid, ts, h = self._decode_header(dat)

    start: uint256 = 32
    plen_int: uint256 = convert(plen, uint256)

    for j: uint256 in range(plen_int, bound=4096):

        val_b: Bytes[32] = slice(dat, start + j*32, 32)  
        typ: uint16 = convert(slice(val_b, 0, 2), uint16)
        val: uint240 = convert(slice(val_b, 2, 30), uint240)

        scid = self._append_type(scid, typ)
        record: Record = self.pStore[scid]

        if record.height <= h and record.timestamp <= ts:
            self.pStore[scid] = Record(height=h, timestamp=ts, value=val)

@external
@view
def get_value(dat: Bytes[4096], j: uint256) -> (uint240, uint16):
    plen: uint16 = 0
    scid: uint88 = 0
    ts: uint48 = 0
    h: uint64 = 0
    v: uint8 = 0

    plen, scid, ts, h = self._decode_header(dat)

    start: uint256 = 32 # skip header
    val_b: Bytes[32] = slice(dat, start + j*32, 32) 
    typ: uint16 = convert(slice(val_b, 0, 2), uint16)
    val: uint240 = convert(slice(val_b, 2, 30), uint240)

    return val, typ
