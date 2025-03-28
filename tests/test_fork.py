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

        w3 = Web3(HTTPProvider(GASNET-RPC))

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=address, abi=abi)

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
            time.sleep(120)

    def test_fork_deployed(self, project, oracle_sepolia):

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
        assert value !=0

        # update
        tx = controller_deployed_sepolia.update_oracle(a, sender=account, raise_on_revert=True, gas=3000000)
        tx.show_trace(True)

        # get current oracle values
        updated_basefee_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, basefee_typ)
        updated_tip_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, tip_typ)
        assert updated_basefee_value != value
        assert updated_height != height
        assert updated_ts != ts
