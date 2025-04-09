import json
import time
import ape
import pytest
from web3 import Web3, HTTPProvider

from ape import accounts
from ape import Contract

from abis import gas_oracle_v2_abi
import params
from fixture import owner, store, oracle_sepolia, controller_sepolia

from oracles import oracle_addresses
SEPOLIA_ORACLE = oracle_addresses[11155111]
GASNET_ORACLE = '0x4245Cb7c690B650a38E680C9BcfB7814D42BfD32'
GASNET_RPC = 'https://rpc.gas.network'

class TestFork:
    def test_fork(self, owner, store, oracle_sepolia, controller_sepolia, chain):
        # ape test  tests/test_fork.py::TestFork::test_fork  --network ethereum:local:foundry

        w3 = Web3(HTTPProvider(GASNET_RPC))

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=GASNET_ORACLE, abi=abi)

        sid = 2
        cid = 1
        basefee_typ = 107
        tip_typ = 322

        # read gasnet
        a: bytes = oracle_gasnet.functions.getValues(sid, cid).call()

        # decode gasnet payload
        system_id, c_id, new_basefee_value, new_tip_value, new_ts, new_h = controller_sepolia.decode(a, tip_typ)
        print(f"{new_basefee_value=}")
        print(f"{new_tip_value=}")
        print(f"{new_ts=}")
        print(f"{new_h=}")
        assert system_id == sid
        assert c_id == cid

        # decode gasnet header
        #plen, scid, _, new_height = store.decode_header(a)
        #assert plen > 0

        chain.mine(1, timestamp=chain.pending_timestamp+12)

        # get current oracle values
        current_basefee_value, current_height, current_ts = oracle_sepolia.get(sid, cid, basefee_typ)
        current_tip_value, current_height, current_ts = oracle_sepolia.get(sid, cid, tip_typ)
        print(f"{current_basefee_value=}")
        print(f"{current_tip_value=}")
        print(f"{current_ts=}")
        print(f"{current_height=}")
        assert current_basefee_value !=0
        assert current_tip_value !=0
        assert new_ts != current_ts
        assert new_h != current_height
        #assert new_basefee_value != current_basefee_value
        #assert new_tip_value != current_tip_value

        assert new_h > current_height
        assert new_ts > current_ts

        # update #1
        tx = controller_sepolia.update_oracle(a, sender=owner, raise_on_revert=True)
        print(tx.show_trace(True))

        events = list(tx.decode_logs())
        e = events[0]
        assert len(events) == 1
        print(f"{e.time_reward/10**18=}, {e.deviation_reward/10**18=}")

        chain.mine(1, timestamp=chain.pending_timestamp+12)

        # get current oracle values
        updated_basefee_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, basefee_typ)
        updated_tip_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, tip_typ)
        assert updated_basefee_value == new_basefee_value
        assert updated_tip_value == new_tip_value
        assert updated_height == new_h
        assert updated_ts == new_ts

    def test_multi(self, owner, store, oracle_sepolia, controller_sepolia, chain):

        w3 = Web3(HTTPProvider(GASNET_RPC))

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=GASNET_ORACLE, abi=abi)

        sid = 2
        cid_1 = 42161
        cid_2 = 10
        basefee_typ = 107
        tip_typ = 322

        # read gasnet
        payload_1: bytes = oracle_gasnet.functions.getValues(sid, cid_1).call()
        payload_2: bytes = oracle_gasnet.functions.getValues(sid, cid_2).call()
        payload_multi = payload_1 + payload_2

        chain.mine(1, timestamp=chain.pending_timestamp+12)

        # get current oracle values
        current_basefee_value_1, current_height_1, current_ts_1 = oracle_sepolia.get(sid, cid_1, basefee_typ)
        current_tip_value_1, current_height_1, current_ts_1 = oracle_sepolia.get(sid, cid_1, tip_typ)
        print(f"{current_basefee_value_1=}")
        print(f"{current_tip_value_1=}")
        print(f"{current_ts_1=}")
        print(f"{current_height_1=}")
        current_basefee_value_2, current_height_2, current_ts_2 = oracle_sepolia.get(sid, cid_2, basefee_typ)
        current_tip_value_2, current_height_2, current_ts_2 = oracle_sepolia.get(sid, cid_2, tip_typ)
        print(f"{current_basefee_value_2=}")
        print(f"{current_tip_value_2=}")
        print(f"{current_ts_2=}")
        print(f"{current_height_2=}")

        #assert new_h > current_height
        #assert new_ts > current_ts

        # update 
        tx = controller_sepolia.update_oracles(payload_multi, 2, sender=owner, raise_on_revert=True)
        print(tx.show_trace(False))

        events = list(tx.decode_logs())
        e_1 = events[0]
        e_2 = events[1]
        assert len(events) == 2
        print(f"{e_1.time_reward/10**18=}, {e_1.deviation_reward/10**18=}")
        print(f"{e_2.time_reward/10**18=}, {e_2.deviation_reward/10**18=}")

        chain.mine(1, timestamp=chain.pending_timestamp+12)

        # get current oracle values
        updated_basefee_value_1, updated_height_1, updated_ts_1 = oracle_sepolia.get(sid, cid_1, basefee_typ)
        updated_tip_value_1, updated_height_1, updated_ts_1 = oracle_sepolia.get(sid, cid_1, tip_typ)
        print(f"{updated_basefee_value_1=}")
        print(f"{updated_tip_value_1=}")
        print(f"{updated_ts_1=}")
        print(f"{updated_height_1=}")
        updated_basefee_value_2, updated_height_2, updated_ts_2 = oracle_sepolia.get(sid, cid_2, basefee_typ)
        updated_tip_value_2, updated_height_2, updated_ts_2 = oracle_sepolia.get(sid, cid_2, tip_typ)
        print(f"{updated_basefee_value_2=}")
        print(f"{updated_tip_value_2=}")
        print(f"{updated_ts_2=}")
        print(f"{updated_height_2=}")

        # update  with same payload
        tx = controller_sepolia.update_oracles(payload_multi, 2, sender=owner, raise_on_revert=True)

        events = list(tx.decode_logs())
        # everything was a duplicate so no rewards
        assert len(events) == 0

    def test_ts(self, owner, store, oracle_sepolia, controller_sepolia, chain):

        w3 = Web3(HTTPProvider(GASNET_RPC))

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=GASNET_ORACLE, abi=abi)

        sid = 2
        cid_1 = 42161
        cid_2 = 10
        basefee_typ = 107
        tip_typ = 322

        # read gasnet
        payload_1: bytes = oracle_gasnet.functions.getValues(sid, cid_1).call()

        _, _, new_basefee_value_1, new_tip_value_1, new_ts_1, new_h_1 = controller_sepolia.decode(payload_1, tip_typ)
        print(f"{cid_1=}, {new_ts_1=}, {new_h_1=}")

    def test_multi_partial(self, owner, store, oracle_sepolia, controller_sepolia, chain):

        w3 = Web3(HTTPProvider(GASNET_RPC))

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=GASNET_ORACLE, abi=abi)

        sid = 2
        cid_1 = 42161
        cid_2 = 10
        basefee_typ = 107
        tip_typ = 322

        # read gasnet
        payload_1: bytes = oracle_gasnet.functions.getValues(sid, cid_1).call()
        payload_2: bytes = oracle_gasnet.functions.getValues(sid, cid_2).call()
        payload_multi = payload_1 + payload_2

        _, _, new_basefee_value_1, new_tip_value_1, new_ts_1, new_h_1 = controller_sepolia.decode(payload_1, tip_typ)

        chain.mine(1, timestamp=chain.pending_timestamp+12)

        # get current oracle values
        current_basefee_value_1, current_height_1, current_ts_1 = oracle_sepolia.get(sid, cid_1, basefee_typ)
        current_tip_value_1, current_height_1, current_ts_1 = oracle_sepolia.get(sid, cid_1, tip_typ)
        print(f"{current_basefee_value_1=}")
        print(f"{current_tip_value_1=}")
        print(f"{current_ts_1=}")
        print(f"{current_height_1=}")
        current_basefee_value_2, current_height_2, current_ts_2 = oracle_sepolia.get(sid, cid_2, basefee_typ)
        current_tip_value_2, current_height_2, current_ts_2 = oracle_sepolia.get(sid, cid_2, tip_typ)
        print(f"{current_basefee_value_2=}")
        print(f"{current_tip_value_2=}")
        print(f"{current_ts_2=}")
        print(f"{current_height_2=}")

        #assert new_h > current_height
        #assert new_ts > current_ts

        # update 
        tx = controller_sepolia.update_oracles(payload_multi, 2, sender=owner, raise_on_revert=True)
        #print(tx.show_trace(False))

        events = list(tx.decode_logs())
        e_1 = events[0]
        e_2 = events[1]
        assert len(events) == 2
        print(f"{e_1.time_reward/10**18=}, {e_1.deviation_reward/10**18=}")
        print(f"{e_2.time_reward/10**18=}, {e_2.deviation_reward/10**18=}")

        chain.mine(1, timestamp=chain.pending_timestamp+12)

        # get current oracle values
        updated_basefee_value_1, updated_height_1, updated_ts_1 = oracle_sepolia.get(sid, cid_1, basefee_typ)
        updated_tip_value_1, updated_height_1, updated_ts_1 = oracle_sepolia.get(sid, cid_1, tip_typ)
        print(f"{updated_basefee_value_1=}")
        print(f"{updated_tip_value_1=}")
        print(f"{updated_ts_1=}")
        print(f"{updated_height_1=}")
        updated_basefee_value_2, updated_height_2, updated_ts_2 = oracle_sepolia.get(sid, cid_2, basefee_typ)
        updated_tip_value_2, updated_height_2, updated_ts_2 = oracle_sepolia.get(sid, cid_2, tip_typ)
        print(f"{updated_basefee_value_2=}")
        print(f"{updated_tip_value_2=}")
        print(f"{updated_ts_2=}")
        print(f"{updated_height_2=}")

        # wait to make sure new estimates are on gasnet
        time.sleep(30)

        # read gasnet
        payload_1b: bytes = oracle_gasnet.functions.getValues(sid, cid_1).call()
        _, _, new_basefee_value_1b, new_tip_value_1b, new_ts_1b, new_h_1b = controller_sepolia.decode(payload_1b, tip_typ)
        # make sure we have new data for cid_1
        assert new_ts_1b != new_ts_1, f"new payload for cid_1 isn't new"
        assert new_h_1b != new_h_1, f"new payload for cid_1 isn't new"

        # use new payload for cid_1 but keep old cid_2
        payload_multi_2 = payload_1b + payload_2

        # update 
        tx = controller_sepolia.update_oracles(payload_multi_2, 2, sender=owner, raise_on_revert=True)
        #print(tx.show_trace(False))

        events = list(tx.decode_logs())
        assert len(events) == 1
        assert events[0].chain_id == cid_1


    def test_fork_loop(self, owner, store, oracle_sepolia, controller_sepolia, chain):

        w3 = Web3(HTTPProvider(GASNET_RPC))

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=GASNET_ORACLE, abi=abi)

        sid = 2
        cid = 1
        basefee_typ = 107
        tip_typ = 322

        print("")
        for i in range(5):
            print(f"update {i}")
            # read gasnet
            a: bytes = oracle_gasnet.functions.getValues(sid, cid).call()

            # decode gasnet payload
            system_id, c_id, new_basefee_value, new_tip_value, new_ts, new_h = controller_sepolia.decode(a, tip_typ)
            print(f"{new_basefee_value=}")
            print(f"{new_tip_value=}")
            print(f"{new_ts=}")
            print(f"{new_h=}")
            assert system_id == sid
            assert c_id == cid

            # decode gasnet header
            #plen, scid, _, new_height = store.decode_header(a)
            #assert plen > 0

            chain.mine(1, timestamp=chain.pending_timestamp+12)

            # get current oracle values
            current_basefee_value, current_height, current_ts = oracle_sepolia.get(sid, cid, basefee_typ)
            current_tip_value, current_height, current_ts = oracle_sepolia.get(sid, cid, tip_typ)
            print(f"{current_basefee_value=}")
            print(f"{current_tip_value=}")
            print(f"{current_ts=}")
            print(f"{current_height=}")
            assert current_basefee_value !=0
            assert current_tip_value !=0
            assert new_ts != current_ts
            assert new_h != current_height
            #assert new_basefee_value != current_basefee_value
            #assert new_tip_value != current_tip_value
            current_gasprice_value = current_basefee_value + current_tip_value
            new_gasprice_value = new_basefee_value + new_tip_value

            deviation = controller_sepolia.calc_deviation(cid, new_gasprice_value, current_gasprice_value)
            print(f"{deviation/10**18=}")
            assert new_h > current_height
            assert new_ts > current_ts

            # update
            rewards_before = controller_sepolia.rewards(owner)
            tx = controller_sepolia.update_oracle(a, sender=owner, raise_on_revert=True)
            events = list(tx.decode_logs())
            e = events[0]
            assert len(events) == 1
            print(f"{e.time_reward/10**18=}, {e.deviation_reward/10**18=}")
            rewards_after = controller_sepolia.rewards(owner)
            assert rewards_before + e.time_reward + e.deviation_reward == rewards_after
            chain.mine(1, timestamp=chain.pending_timestamp+12)

            # get current oracle values
            updated_basefee_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, basefee_typ)
            updated_tip_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, tip_typ)
            assert updated_basefee_value == new_basefee_value
            assert updated_tip_value == new_tip_value
            assert updated_height == new_h
            assert updated_ts == new_ts
            time.sleep(30)

    def test_deployed(self, project, oracle_sepolia):

        controller_deployed_sepolia = project.RewardController.at("0xe48555990092ff02a7cdd0e6b772fba9b7a3e9fd")
        account = accounts.load("blocknative_dev")
        print(account)
        w3 = Web3(HTTPProvider(GASNET_RPC))

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=GASNET_ORACLE, abi=abi)

        sid = 2
        cid = 10
        basefee_typ = 107
        tip_typ = 322

        # read gasnet
        a: bytes = oracle_gasnet.functions.getValues(sid, cid).call()

        """
        # decode gasnet payload
        system_id, c_id, t, new_value, new_ts = controller_deployed_sepolia.decode(a, 107)
        assert system_id == sid
        assert c_id == cid
        assert t == typ
        # decode gasnet payload

        # decode gasnet header
        plen, scid, _, new_height = controller_deployed_sepolia.decode_header(a)
        assert plen > 0
        """

        # get current oracle values
        basefee_value, height, ts = oracle_sepolia.get(sid, cid, basefee_typ)
        tip_value, height, ts = oracle_sepolia.get(sid, cid, tip_typ)
        """
        assert value !=0
        assert new_ts != ts
        assert new_value != value
        assert new_height != height

        assert new_height > height
        assert new_ts > ts
        """
        #assert value !=0

        # update
        tx = controller_deployed_sepolia.update_oracle(a, sender=account, raise_on_revert=True, gas=3000000)
        tx.show_trace(True)

        # get current oracle values
        updated_basefee_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, basefee_typ)
        updated_tip_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, tip_typ)
        assert updated_basefee_value != value
        assert updated_height != height
        assert updated_ts != ts

    def test_deployed_multi(self, project, oracle_sepolia):

        controller_deployed_sepolia = project.RewardController.at("0xe48555990092ff02a7cdd0e6b772fba9b7a3e9fd")
        account = accounts.load("blocknative_dev")
        print(account)
        w3 = Web3(HTTPProvider(GASNET_RPC))

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=GASNET_ORACLE, abi=abi)

        sid = 2
        cid_1 = 1
        cid_2 = 10
        basefee_typ = 107
        tip_typ = 322

        # read gasnet
        a: bytes = oracle_gasnet.functions.getValues(sid, cid_1).call()
        b: bytes = oracle_gasnet.functions.getValues(sid, cid_2).call()
        payload = a + b

        """
        # decode gasnet payload
        system_id, c_id, t, new_value, new_ts = controller_deployed_sepolia.decode(a, 107)
        assert system_id == sid
        assert c_id == cid
        assert t == typ
        # decode gasnet payload

        # decode gasnet header
        plen, scid, _, new_height = controller_deployed_sepolia.decode_header(a)
        assert plen > 0
        """

        # get current oracle values
        basefee_value_1, bf_height_1, bf_ts_1 = oracle_sepolia.get(sid, cid_1, basefee_typ)
        tip_value_1, tip_height_1, tip_ts_1 = oracle_sepolia.get(sid, cid_1, tip_typ)
        basefee_value_2, bf_height_2, bf_ts_2 = oracle_sepolia.get(sid, cid_2, basefee_typ)
        tip_value_2, tip_height_2, tip_ts_2 = oracle_sepolia.get(sid, cid_2, tip_typ)

        # update
        tx = controller_deployed_sepolia.update_oracles(payload, 2, sender=account, raise_on_revert=True, gas=3000000)
        tx.show_trace(True)

        # get current oracle values
        updated_basefee_value_1, updated_bf_height_1, updated_bf_ts_1 = oracle_sepolia.get(sid, cid_1, basefee_typ)
        updated_tip_value_1, updated_tip_height_1, updated_tip_ts_1 = oracle_sepolia.get(sid, cid_1, tip_typ)
        updated_basefee_value_2, updated_bf_height_2, updated_bf_ts_2 = oracle_sepolia.get(sid, cid_2, basefee_typ)
        updated_tip_value_2, updated_tip_height_2, updated_tip_ts_2 = oracle_sepolia.get(sid, cid_2, tip_typ)
        assert updated_basefee_value_1 != basefee_value_1
        assert updated_bf_height_1 != bf_height_1
        assert updated_bf_ts_1 != bf_ts_1
        assert updated_tip_value_1 != tip_value_1
        assert updated_tip_height_1 != tip_height_1
        assert updated_tip_ts_1 != tip_ts_1

        assert updated_basefee_value_2 != basefee_value_2
        assert updated_bf_height_2 != bf_height_2
        assert updated_bf_ts_2 != bf_ts_2
        assert updated_tip_value_2 != tip_value_2
        assert updated_tip_height_2 != tip_height_2
        assert updated_tip_ts_2 != tip_ts_2
