import ape
import pytest
from web3 import Web3

from ape import accounts

FORTY_FIVE_DECIMAL_NUMBER   = int(10 ** 45)
TWENTY_SEVEN_DECIMAL_NUMBER = int(10 ** 27)
EIGHTEEN_DECIMAL_NUMBER     = int(10 ** 18)

update_delay = 3600;

#kp = 222002205862
#ki = int(EIGHTEEN_DECIMAL_NUMBER)
#co_bias = 0
#output_upper_bound = 18640000000000000000
#output_lower_bound = -51034000000000000000


kp = 5*10**15
ki = 2*10**14
co_bias = 10**18
output_upper_bound = 10*10**18
output_lower_bound = 10**15 # 1e-3
target_time_since = 1800 * 10**18
min_reward = 10**14 #1e-4
max_reward = 10**18 #1
min_ts = 10**18 #11
max_ts = 36 * 10**20 #3600
min_deviation = 10**17 # 0.1
max_deviation = 5 * 10**18 # 5
default_window_size = 20
coeff = [10611581, 3777134486958753, 38572373423, 5670509383, 19263385883489428]

@pytest.fixture
def owner(accounts):
    return accounts[0]

@pytest.fixture
def oracle(owner, project):
    oracle = owner.deploy(project.oracle, sender=owner)
    oracle.set_value(1, 1000*10**18, 200, sender=owner)
    return oracle

@pytest.fixture
def store(owner, project):
    store = owner.deploy(project.store, sender=owner)
    return store

# Use this to match existing controller tests
def assertEq(x, y):
    assert x == y

def assertGt(x, y):
    assert x > y

def assertLt(x, y):
    assert x < y

class TestStore:
    def test_prepare_header(self, store):
        version = 1
        height = 12345678
        chainid = 56
        systemid = 2
        ts = 9876543210
        plen = 512

        expected_value = (
            (plen << (48 + 8 + 64 + 64 + 8)) |
            (ts << (8 + 64 + 64 + 8)) |
            (systemid << (64 + 64 + 8)) |
            (chainid << (64 + 8)) |
            (height << 8) |
            version
        )
        expected_bytes32 = expected_value.to_bytes(32, byteorder='big')

        result = store.prepare_header(version, height, chainid, systemid, ts, plen)

        assert result == expected_bytes32, "Header packing failed in Vyper!"

    def test_decode_header(self, store, owner):
        # Define the input hex data as bytes
        a: bytes = bytes.fromhex("0000000000000003019460ee47e9020000000000000001000000000149dad401006b0000000000000000000000000000000000000000000000000011dab0f6ee0070000000000000000000000000000000000000000000000000000a04855e220141000000000000000000000000000000000000000000000000000005290f62089b3891d48dd725e0c8370155fee14aac001fe061f23d0c8003469af1d8e4201200d1e03e17bbfcfd866fc50d153be546ffadc022c046f1dd82441242a1f28e1c")

        plen, scid, ts, h = store.decode_header(a)
        assert h == 21617364
        assert ts == 1736793016297
        assert plen == 3
        assert scid == 2417851639229258349477888

    def test_append_type(self, store, owner):
        # Define the input hex data as bytes
        scid = 2417851639229258349477888;
        typ = 107;
        #scid: uint88 = convert(2417851639229258349477888, uint88)
        #typ: uint16 = 107

        scida = store.append_type(scid, typ)
        assert scida == scid + typ

    def test_get_key(self, store, owner):
        scid = store.get_key(2, 1, 107)
        assert scid == 2417851639229258349477888 + 107

    def test_store_values(self, store, owner):
        # Define the input hex data as bytes
        a: bytes = bytes.fromhex("0000000000000003019460ee47e9020000000000000001000000000149dad401006b0000000000000000000000000000000000000000000000000011dab0f6ee0070000000000000000000000000000000000000000000000000000a04855e220141000000000000000000000000000000000000000000000000000005290f62089b3891d48dd725e0c8370155fee14aac001fe061f23d0c8003469af1d8e4201200d1e03e17bbfcfd866fc50d153be546ffadc022c046f1dd82441242a1f28e1c")

        store.store_values(a, sender=owner)

        # Simulate block timestamp update
        #owner.provider.set_timestamp(1736793026)

        # Retrieve and validate stored data
        endf, h, ts = store.get(2, 1, 107)
        assert endf == 76683474670
        assert h == 21617364
        assert ts == 1736793016297

        endf, h, ts = store.get(2, 1, 112)
        assert endf == 43025522210
        assert h == 21617364
        assert ts == 1736793016297

        endf, h, ts = store.get(2, 1, 321)
        assert endf == 86576994
        assert h == 21617364
        assert ts == 1736793016297

    def test_get_value(self, store, owner):
        a: bytes = bytes.fromhex("0000000000000003019460ee47e9020000000000000001000000000149dad401006b0000000000000000000000000000000000000000000000000011dab0f6ee0070000000000000000000000000000000000000000000000000000a04855e220141000000000000000000000000000000000000000000000000000005290f62089b3891d48dd725e0c8370155fee14aac001fe061f23d0c8003469af1d8e4201200d1e03e17bbfcfd866fc50d153be546ffadc022c046f1dd82441242a1f28e1c")
        """
        print("first full val")
        print(a[32:64].hex())
        print("first val typ")
        print(int(a[32:64][:2].hex(), 16))

        print("second full val")
        print(a[64:96].hex())
        print("second val typ")
        print(int(a[64:96][:2].hex(), 16))

        print("3rd full val")
        print(a[96:128].hex())
        print("3rd val typ")
        print(int(a[96:128][:2].hex(), 16))
        """

        val, typ = store.get_value(a, 0)
        assert (val, typ) == (76683474670, 107)
        val, typ = store.get_value(a, 1)
        assert (val, typ) == (43025522210, 112)
        val, typ = store.get_value(a, 2)
        assert (val, typ) == (86576994, 321)

    def test_decode(self, store, owner):
        a: bytes = bytes.fromhex("0000000000000003019460ee47e9020000000000000001000000000149dad401006b0000000000000000000000000000000000000000000000000011dab0f6ee0070000000000000000000000000000000000000000000000000000a04855e220141000000000000000000000000000000000000000000000000000005290f62089b3891d48dd725e0c8370155fee14aac001fe061f23d0c8003469af1d8e4201200d1e03e17bbfcfd866fc50d153be546ffadc022c046f1dd82441242a1f28e1c")

        sid, cid, typ, val, ts = store.decode(a, 107)
        assert typ == 107
        assert val == 76683474670
        assert sid == 2
        assert cid == 1
