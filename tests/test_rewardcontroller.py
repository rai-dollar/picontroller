import json
import time
import ape
import pytest
from web3 import Web3, HTTPProvider

from ape import accounts
from ape import Contract

from abis import gas_oracle_v2_abi
import params

TWENTY_SEVEN_DECIMAL_NUMBER = int(10 ** 27)
EIGHTEEN_DECIMAL_NUMBER     = int(10 ** 18)

update_delay = 3600;

SEPOLIA_ORACLE = '0xCc936bE977BeDb5140C5584d8B6043C9068622A6'

@pytest.fixture
def owner(accounts):
    return accounts[0]

@pytest.fixture
def controller(owner, oracle, project, chain):
    controller = owner.deploy(project.RewardController,
            b'test control variable',
            params.kp,
            params.ki,
            params.co_bias,
            params.output_upper_bound,
            params.output_lower_bound,
            params.target_time_since,
            params.min_reward,
            params.max_reward,
            params.default_window_size,
            oracle.address,
            params.coeff,
            sender=owner)

    controller.set_scale(1, 3*10**15, sender=owner)
    controller.set_scale(10, 10000, sender=owner)
    #controller.set_scales([1,10], [3*10**15, 10000], sender=owner)
    #chain.mine(1, timestamp=chain.pending_timestamp+2)
    return controller

@pytest.fixture
def controller_sepolia(owner, project):
    controller = owner.deploy(project.RewardController,
            b'test control variable',
            params.kp,
            params.ki,
            params.co_bias,
            params.output_upper_bound,
            params.output_lower_bound,
            params.target_time_since,
            params.min_reward,
            params.max_reward,
            params.default_window_size,
            SEPOLIA_ORACLE,
            params.coeff,
            sender=owner)

    controller.set_scale(1, 3*10**15, sender=owner)
    controller.set_scale(10, 10000, sender=owner)
    #controller.set_scales([1,10], [3*10**15, 10000], sender=owner)
    #chain.mine(1, timestamp=chain.pending_timestamp+2)
    return controller

@pytest.fixture
def oracle(owner, project):
    oracle = owner.deploy(project.oracle, sender=owner)
    oracle.set_value(1, 1000*10**18, 200, sender=owner)
    return oracle

@pytest.fixture
def store(owner, project):
    store = owner.deploy(project.store, sender=owner)
    return store

@pytest.fixture
def oracle_sepolia(owner, project):
    # Using a JSON file path:
    #with open('tests/gas_oracle_v2.json') as f:
    #    abi = json.load(f)['abi']
    #contract = Contract(SEPOLIA_ORACLE, abi="tests/gas_oracle_v2.json")
    contract = Contract(SEPOLIA_ORACLE, abi=gas_oracle_v2_abi)
    return contract

# Use this to match existing controller tests
def assertEq(x, y):
    assert x == y

def assertGt(x, y):
    assert x > y

def assertLt(x, y):
    assert x < y

def relative_error(measured_value, reference_value):
    # measured_value is WAD, reference_value is a RAY
    assert isinstance(measured_value, int)
    assert isinstance(reference_value, int)

    scaled_measured_value = measured_value *  int(10**9)
    return ((reference_value - scaled_measured_value) * TWENTY_SEVEN_DECIMAL_NUMBER) // reference_value

class TestRewardController:
    def check_state(self, owner, controller):
        assert controller.authorities(owner) == 1
        assert controller.output_upper_bound() == params.output_upper_bound
        assert controller.output_lower_bound() == params.output_lower_bound
        #assertEq(controller.last_update_time(), 0);
        assert controller.error_integral() == 0
        assert controller.last_error() == 0
        assert controller.kp() == params.kp
        assert controller.ki() == params.ki
        assert controller.elapsed() == 2

    def test_contract_fixture(self, owner, controller):
        assertEq(controller.authorities(owner), 1);
        assertEq(controller.output_upper_bound(), params.output_upper_bound);
        assertEq(controller.output_lower_bound(), params.output_lower_bound);
        #assertEq(controller.last_update_time(), 0);
        assertEq(controller.error_integral(), 0);
        assertEq(bytes.fromhex(controller.control_variable().hex().rstrip("0")).decode('utf8'), 'test control variable');
        assertEq(params.kp, controller.kp());
        assertEq(params.ki, controller.ki());
        assertEq(controller.elapsed(), 2);

    def test_modify_parameters(self, owner, controller):
        controller.modify_parameters_int("kp", int(1), sender=owner);
        controller.modify_parameters_int("ki", int(2), sender=owner);
        controller.modify_parameters_int("co_bias", int(3), sender=owner);
        assert int(1) == controller.kp()
        assert int(2) == controller.ki()
        assert int(3) == controller.co_bias()

        controller.modify_parameters_int("output_upper_bound", int(TWENTY_SEVEN_DECIMAL_NUMBER + 1), sender=owner);
        controller.modify_parameters_int("output_lower_bound", -int(1), sender=owner);
        assert controller.output_upper_bound() == int(TWENTY_SEVEN_DECIMAL_NUMBER + 1)
        assert controller.output_lower_bound() == -int(1)

        controller.modify_parameters_uint("target_time_since", 600, sender=owner);
        controller.modify_parameters_uint("min_reward", 100, sender=owner);
        controller.modify_parameters_uint("max_reward", 1000, sender=owner);
        controller.modify_parameters_uint("min_ts", 100, sender=owner);
        controller.modify_parameters_uint("max_ts", 40000, sender=owner);
        controller.modify_parameters_uint("min_deviation", 10**16, sender=owner);
        controller.modify_parameters_uint("max_deviation", 5* 10**18, sender=owner);
        controller.modify_parameters_uint("default_window_size", 50, sender=owner);

        assert controller.target_time_since() ==  600
        assert controller.min_reward() ==  100
        assert controller.max_reward() ==  1000
        assert controller.min_ts() ==  100
        assert controller.max_ts() ==  40000
        assert controller.min_deviation() ==  10**16
        assert controller.max_deviation() ==  5*10**18
        assert controller.default_window_size() ==  50

    def test_fail_modify_parameters_control_upper_bound(self, owner, controller):
        with ape.reverts("RewardController/invalid-output_upper_bound"):
            controller.modify_parameters_int("output_upper_bound", controller.output_lower_bound() - 1, sender=owner);
    
    def test_fail_modify_parameters_control_lower_bound(self, owner, controller):
        with ape.reverts("RewardController/invalid-output_lower_bound"):
            controller.modify_parameters_int("output_lower_bound", controller.output_upper_bound() + 1, sender=owner);

    def test_get_next_output_zero_error(self, owner, controller):
        error = relative_error(EIGHTEEN_DECIMAL_NUMBER, TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output,_,_) = controller.get_new_pi_output(error);
        assertEq(pi_output, params.co_bias + 0);
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_next_output_nonzero_error(self, owner, controller):
        error = relative_error(int(1.1E18), 10**27);
        assertEq(error, -100000000000000000000000000)

        (pi_output,_,_) = controller.get_new_pi_output(error);
        assert pi_output != 0
        assert controller.error_integral() == 0
        assert pi_output == max(params.co_bias + params.kp * int(error/10**18) + params.ki * int(error/10**18), params.output_lower_bound)

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_zero_error(self, owner, controller):
        error = relative_error(EIGHTEEN_DECIMAL_NUMBER, TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output,_,_) = controller.get_raw_pi_output(error, 0);
        assertEq(pi_output, params.co_bias + 0);
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_nonzero_error(self, owner, controller):
        error = int(10**20)
        (pi_output,p_output,i_output) = controller.get_raw_pi_output(error, 0);
        assertEq(p_output, params.kp * int(error/1E18));
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_small_nonzero_error(self, owner, controller):
        error = int(10**18)
        assert controller.elapsed() == 2
        (pi_output,p_output,i_output) = controller.get_raw_pi_output(error, 0);
        assert controller.elapsed() == 2
        assert pi_output > 0
        assert p_output == params.kp * int(error/1E18)
        assert controller.error_integral() == 0

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_large_nonzero_error(self, owner, controller):
        error = int(10**20) * int(10**18)
        (pi_output,p_output,i_output) = controller.get_raw_pi_output(error, 0);
        assertEq(p_output, params.kp * int(error/1E18));
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_first_update(self, owner, controller, chain):
        next_ts = chain.pending_timestamp
        controller.update(1, sender=owner)
        assertEq(controller.last_update_time(), next_ts);
        assertEq(controller.last_error(), 1);
        assertEq(controller.error_integral(), 1);

    def test_first_update_zero_error(self, owner, controller, chain):
        next_ts = chain.pending_timestamp
        controller.update(0, sender=owner)
        assertEq(controller.last_update_time(), next_ts);
        assertEq(controller.last_error(), 0);
        assertEq(controller.error_integral(), 0);

    def test_two_updates(self, owner, controller, chain):
        controller.update(1, sender=owner)
        controller.update(2, sender=owner)
        assertEq(controller.last_error(), 2);
        assert controller.error_integral() != 0;

    def test_first_get_next_output(self, owner, controller):
        # negative error
        error = relative_error(int(1.01E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, params.kp * int(error/1E18));
        assert pi_output != 0
        assertEq(controller.error_integral(), 0);

        # positive error
        error = relative_error(int(0.995E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, params.kp * int(0.005E27/1E18));
        assert pi_output != 0
        assertEq(controller.error_integral(), 0);

    def test_first_get_next_output_w_bias(self, owner, controller):
        bias = 30000;
        controller.modify_parameters_int("co_bias", bias, sender=owner);
        # negative error
        error = relative_error(int(1.01E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, bias + params.kp * int(error/1E18));
        assert pi_output != 0
        assertEq(controller.error_integral(), 0);

        # positive error
        error = relative_error(int(0.995E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, bias + params.kp * int(0.005E27/1E18));
        assert pi_output != 0
        assertEq(controller.error_integral(), 0);

    def test_first_negative_error(self, owner, controller, chain):
        error = relative_error(int(1.05E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, params.kp * int(error/1E18));
        assertEq(p_output, params.kp * int(error/1E18));
        assertEq(i_output, 0);

        next_ts = chain.pending_timestamp
        controller.update(error, sender=owner);
        (update_time, pi_output, p_output, i_output) = controller.last_update()
        assertEq(pi_output, params.kp * int(error/1E18));
        assertEq(p_output, params.kp * int(error/1E18));
        assertEq(i_output, 0);

        assertEq(controller.last_update_time(), next_ts);
        assertEq(controller.error_integral(), 0);
        assertEq(controller.last_error(), -10**27//20);

    def test_first_positive_error(self, owner, controller, chain):
        error = relative_error(int(0.95E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, params.kp * int(error/1E18));
        assertEq(p_output, params.kp * int(error/1E18));
        assertEq(i_output, 0);

        next_ts = chain.pending_timestamp
        controller.update(error, sender=owner);
        (update_time, pi_output, p_output, i_output) = controller.last_update()
        assertEq(pi_output, params.kp * int(error/1E18));
        assertEq(p_output, params.kp * int(error/1E18));
        assertEq(i_output, 0);

        assertEq(controller.last_update_time(), next_ts);
        assertEq(controller.error_integral(), 0);
        assertEq(controller.last_error(), 10**27//20);

    def test_basic_integral(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);

        chain.pending_timestamp += update_delay

        # First update doesn't create an integral contribution
        # as elapsed time is set to 0
        error1 = relative_error(int(1.01* 10**18), 10**27);
        assertEq(error1, -10**25);
        controller.update(error1, sender=owner);

        (_, output1, _, _) = controller.last_update()
        error_integral1 = controller.error_integral();
        assertEq(output1, error1 * controller.kp() / EIGHTEEN_DECIMAL_NUMBER);
        assertEq(error_integral1, 0);

        chain.pending_timestamp += update_delay

        # Second update
        error2 = relative_error(int(1.01* 10**18), 10**27);
        assertEq(error1, -10**25);
        controller.update(error2, sender=owner);
        (_, output2, _, _) = controller.last_update()

        error_integral2 = controller.error_integral();

        assertEq(error_integral2, error_integral1 + (error1 + error2)//2 * (update_delay + 1));
        assertEq(output2, error2 * controller.kp()/EIGHTEEN_DECIMAL_NUMBER +
                 error_integral2 * controller.ki()/EIGHTEEN_DECIMAL_NUMBER);

        chain.pending_timestamp += update_delay

        # Third update
        error3 = relative_error(int(1.01* 10**18), 10**27);
        controller.update(error3, sender=owner);
        (_, output3, _, _) = controller.last_update()

        error_integral3 = controller.error_integral();

        assertEq(error_integral3, error_integral2 + (error2 + error3)//2 * (update_delay + 1));
        assertEq(output3, error3 * controller.kp()/EIGHTEEN_DECIMAL_NUMBER +
                 error_integral3 * controller.ki()/EIGHTEEN_DECIMAL_NUMBER);
        
    def test_basic_integral2(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);

        # First update doesn't create an integral contribution
        # as elapsed time is set to 0
        error1 = relative_error(int(1.01* 10**18), 10**27);
        assertEq(error1, -10**25);
        controller.update(error1, sender=owner);

        (_, output1, _, _) = controller.last_update()
        error_integral1 = controller.error_integral();
        assertEq(output1, error1 * controller.kp() / EIGHTEEN_DECIMAL_NUMBER);
        assertEq(error_integral1, 0);

        # Second update
        error2 = relative_error(int(1.02* 10**18), 10**27);
        controller.update(error2, sender=owner);
        (_, output2, _, _) = controller.last_update()

        error_integral2 = controller.error_integral();

        assertEq(error_integral2, error_integral1 + (error1 + error2)//2 );
        assertEq(output2, error2 * controller.kp()/EIGHTEEN_DECIMAL_NUMBER +
                 error_integral2 * controller.ki()/EIGHTEEN_DECIMAL_NUMBER);

        # Third update
        error3 = relative_error(int(1.03* 10**18), 10**27);
        controller.update(error3, sender=owner);
        (_, output3, _, _) = controller.last_update()

        error_integral3 = controller.error_integral();

        assertEq(error_integral3, error_integral2 + (error2 + error3)//2 );
        assertEq(output3, error3 * controller.kp()/EIGHTEEN_DECIMAL_NUMBER +
                 error_integral3 * controller.ki()/EIGHTEEN_DECIMAL_NUMBER);


    def test_update_prate(self, owner, controller, chain):

        controller.modify_parameters_int("kp", int(2.25E11), sender=owner);
        controller.modify_parameters_int("ki", 0, sender=owner);
        chain.mine(3600, timestamp=chain.pending_timestamp+3600)

        error = relative_error(int(1.01E18), 10**27);
        assert error == -10 **25;
        controller.update(error, sender=owner);
        (update_time, pi_output, p_output, i_output) = controller.last_update()
        assert pi_output ==  error * int(2.25E11)/ EIGHTEEN_DECIMAL_NUMBER;
        assert pi_output == p_output;

    def test_get_next_error_integral(self, owner, controller, chain):
        update_delay = 3600
        #controller.modify_parameters_int("kp", int(2.25E11), sender=owner);
        #controller.modify_parameters_int("ki", int(7.2E4), sender=owner);
        #assert controller.ki() == 72000
        chain.mine(update_delay//2, timestamp=chain.pending_timestamp+update_delay)

        error = 5* 10**17
        (new_integral, new_area) = controller.get_new_error_integral(error);
        assert new_integral == error
        assert new_area == error
        #update
        controller.update(error, sender=owner);
        assert controller.error_integral() == error

        chain.mine(update_delay//2)#, timestamp=chain.pending_timestamp+update_delay)
        next_pending_ts = chain.pending_timestamp + update_delay
        chain.pending_timestamp = next_pending_ts

        # Second update
        #error = relative_error(int(1.01E18), 10**27);
        (new_integral, new_area) = controller.get_new_error_integral(error);
        assert new_integral == error + error
        assert new_area == error
        #update
        controller.update(error, sender=owner);
        assert controller.last_update_time() == next_pending_ts
        assert controller.error_integral() == new_integral

        chain.pending_timestamp += update_delay

        # Third update
        (new_integral, new_area) = controller.get_new_error_integral(error);
        assert new_integral == 3*error
        assert new_area == error
        controller.update(error, sender=owner);
        assert controller.error_integral()  == 3*error


    def test_last_error(self, owner, controller, chain):
        chain.pending_timestamp += update_delay
        assertEq(controller.last_error(), 0);

        error = relative_error(int(1.01E18), 10**27);
        assertEq(error, -10**25);
        controller.update(error, sender=owner);
        assertEq(controller.last_error(), error);

        chain.pending_timestamp += update_delay

        error = relative_error(int(1.02E18), 10**27);
        assertEq(error, -10**25 * 2);
        controller.update(error, sender=owner);
        assertEq(controller.last_error(), error);

    def test_elapsed(self, owner, controller, chain):
        assertEq(controller.elapsed(), 0);
        controller.update(-10**25, sender=owner);
        assertEq(controller.last_update_time(), chain.pending_timestamp-1);

        chain.pending_timestamp += update_delay

        assertEq(controller.elapsed(), update_delay);
        assertEq(controller.last_update_time(), chain.pending_timestamp-1 - controller.elapsed());
        controller.update(-10**25, sender=owner);
        assertEq(controller.last_update_time(), chain.pending_timestamp-1);

    def test_lower_bound_limit(self, owner, controller, chain):
        chain.pending_timestamp += update_delay
        # create very large error
        error = relative_error(int(1.05*10**18), 1);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);

        assertEq(pi_output, controller.output_lower_bound());

        controller.update(error, sender=owner);
        (update_time, pi_output, p_output, i_output) = controller.last_update()

        assertEq(pi_output, controller.output_lower_bound());

    def test_upper_bound_limit(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(100000000000000000000e18), sender=owner);
        error = relative_error(1, 10**27);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, controller.output_upper_bound());

        controller.update(error, sender=owner);
        (update_time, pi_output, p_output, i_output) = controller.last_update()
        assertEq(pi_output, controller.output_upper_bound());

    def test_raw_output_proportional_calculation(self, owner, controller, chain):
        error = relative_error(10**18, 10**27);
        (pi_output, p_output, i_output) = controller.get_raw_pi_output(error, 0);
        assertEq(pi_output, params.kp * error//10**18);
        assertEq(p_output, params.kp * error//10**18);
        assertEq(i_output, 0);
        
        error = relative_error(int(1.05* 10**18), 10**27);
        (pi_output, p_output, i_output) = controller.get_raw_pi_output(error, 0);
        assertEq(pi_output, params.kp * error//10**18);
        assertEq(p_output, params.kp * error//10**18);
        assertEq(i_output, 0);

    def test_both_gains_zero(self, owner, controller, chain):
        controller.modify_parameters_int("kp", 0, sender=owner);
        controller.modify_parameters_int("ki", 0, sender=owner);
        assertEq(controller.error_integral(), 0);

        error = relative_error(int(1.05*10**18), 10**27);
        assertEq(error, -10**27//20);

        (pi_output, p_output, _) = controller.get_new_pi_output(error);
        assertEq(pi_output, 0);
        assertEq(p_output, 0);
        assertEq(controller.error_integral(), 0);

    def test_update_integral(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);

        chain.pending_timestamp += update_delay

        # First update doesn't create an integral contribution
        # as elapsed time is set to 0
        error1 = relative_error(int(1.01* 10**18), 10**27);
        assertEq(error1, -10**25);
        controller.update(error1, sender=owner);

        (_, output1, _, _) = controller.last_update()
        error_integral1 = controller.error_integral();
        assertEq(output1, error1 * controller.kp() / EIGHTEEN_DECIMAL_NUMBER);
        assertEq(error_integral1, 0);

        chain.pending_timestamp += update_delay
        #assert controller.elapsed() == update_delay

        # Second update
        error2 = relative_error(int(1.01* 10**18), 10**27);
        assertEq(error2, -10**25);
        controller.update(error2, sender=owner);
        (_, pi_output2, _, _) = controller.last_update()

        error_integral2 = controller.error_integral();

        assertEq(error_integral2, error_integral1 + (error1 + error2)//2 * (update_delay + 1));
        assertEq(pi_output2, error2 * controller.kp()/EIGHTEEN_DECIMAL_NUMBER +
                 error_integral2 * controller.ki()/EIGHTEEN_DECIMAL_NUMBER);
        
    def test_lower_clamping(self, owner, controller, chain):
        #controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        #controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);
        #controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        #controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);
        assert controller.kp() < 0
        assert controller.ki() < 0

        chain.pending_timestamp += update_delay

        #error = relative_error(int(1.01* 10**18), 10**27);
        error = controller.error(1800*10**18, 1750*10**18)
        assert error > 0

        # First error: small, output doesn't hit lower bound
        controller.update(error, sender=owner);
        (_, pi_output, _, _) = controller.last_update()
        assert pi_output < controller.co_bias();
        assert pi_output > controller.output_lower_bound();

        assert controller.error_integral() != 0

        chain.pending_timestamp += update_delay

        (new_integral, new_area) = controller.get_new_error_integral(error);
        assert new_integral == error * 2
        assert new_area == error

        # Second error: small, output doesn't hit lower bound
        controller.update(error, sender=owner);
        (_, pi_output2, _, _) = controller.last_update()
        assert pi_output2 < pi_output;
        assert pi_output2 > controller.output_lower_bound();
        assert controller.error_integral() - error == error

        chain.pending_timestamp += update_delay

        # Third error: very large. Output hits lower bound
        # Integral *does not* accumulate when it hits bound with same sign of current integral
        huge_error = controller.error(1800*10**18, 1*10**18)
        assert error > 0

        controller.update(huge_error, sender=owner);
        (_, pi_output3, _, _) = controller.last_update()
        assert pi_output3 == controller.output_lower_bound()

        # Integral doesn't accumulate
        assert controller.error_integral() - error == error

        chain.pending_timestamp += update_delay
        return

        # Integral *does* accumulate with a smaller error(doesn't hit output bound)
        small_neg_error = relative_error(int(1.01* 10**18), 10**27);

        controller.update(small_neg_error, sender=owner);
        (_, pi_output4, _, _) = controller.last_update()
        assert controller.error_integral() < -36000000000000000000000000000;
        assert pi_output4 > controller.output_lower_bound();

    def test_upper_clamping(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);
        controller.modify_parameters_int("output_upper_bound", int(0.00000001 * 10**27), sender=owner);

        chain.pending_timestamp += update_delay

        error = relative_error(int(0.999999* 10**18), 10**27);
        controller.update(error, sender=owner);
        (_, pi_output, _, _) = controller.last_update()
        assert pi_output > 0;
        assert pi_output < controller.output_upper_bound();
        assertEq(controller.error_integral(), 0);

        chain.pending_timestamp += update_delay

        (leaked_integral, new_area) = controller.get_new_error_integral(error);
        assertEq(leaked_integral, error * update_delay);
        assertEq(new_area, error * update_delay);


        controller.update(error, sender=owner);
        (_, pi_output2, _, _) = controller.last_update()
        assert pi_output2 > pi_output;
        assertEq(controller.error_integral(), update_delay * error + error);

        # Integral *does not* accumulate when it hits bound with same sign of current integral
        huge_neg_error = relative_error(1, 10**27);

        chain.pending_timestamp += update_delay

        controller.update(huge_neg_error, sender=owner);
        (_, pi_output3, _, _) = controller.last_update()
        assertEq(pi_output3, controller.output_upper_bound());
        assertEq(controller.error_integral(), update_delay * error + error);
        
        # Integral *does* accumulate with a smaller error(doesn't hit output bound)
        smallPosError = relative_error(int(0.999999*10**18), 10**27);
        chain.pending_timestamp += update_delay

        controller.update(smallPosError, sender=owner);
        (_, output4, _, _) = controller.last_update()
        assert(output4 < controller.output_upper_bound());

    def test_bounded_output_proportional_calculation(self, owner, controller, chain):
        # small error
        error = relative_error(int(1.05*10**18), 10**27);
        (pi_output, p_output, i_output) = controller.get_raw_pi_output(error, 0);
        bounded_output = controller.bound_pi_output(pi_output);

        assertEq(pi_output, params.kp * error//10**18);
        assertEq(p_output, params.kp * error//10**18);
        assertEq(i_output, 0);
        assertEq(bounded_output, params.kp * error//10**18);

        # large negative error, hits lower bound
        error = relative_error(int(1.5*10**18), 10**27);
        (pi_output, p_output, i_output) = controller.get_raw_pi_output(error, 0);
        bounded_output = controller.bound_pi_output(pi_output);

        assertEq(pi_output, params.kp * error//10**18);
        assertEq(p_output, params.kp * error//10**18);
        assertEq(i_output, 0);
        assertEq(bounded_output, params.output_lower_bound);

        # large positive error, hits upper bound
        error = relative_error(int(0.5*10**18), 10**27);
        (pi_output, p_output, i_output) = controller.get_raw_pi_output(error, 0);

        bounded_output = controller.bound_pi_output(pi_output);

        assertEq(pi_output, params.kp * error//10**18);
        assertEq(p_output, params.kp * error//10**18);
        assertEq(i_output, 0);
        assertEq(bounded_output, params.output_upper_bound);

    def test_last_error_integral(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);

        chain.pending_timestamp += update_delay

        error = relative_error(int(1.01*10**18), 10**27);
        controller.update(error, sender=owner);
        (_, pi_output, p_output, i_output) = controller.last_update()
        assertEq(controller.last_error(), error);
        assertEq(controller.error_integral(), 0);

        chain.pending_timestamp += update_delay

        error = relative_error(int(1.01*10**18), 10**27);
        controller.update(error, sender=owner);
        (_, pi_output, p_output, i_output) = controller.last_update()
        assertEq(controller.last_error(), error);
        assertEq(controller.error_integral(), error * update_delay + error);

        chain.pending_timestamp += update_delay
        assertEq(controller.error_integral(), error * update_delay + error);

        controller.update(error, sender=owner);
        assertEq(controller.last_error(), error);
        assertEq(controller.error_integral(), error * 2 * update_delay + 2*error);

        chain.pending_timestamp += update_delay
        assertEq(controller.error_integral(), error * 2 * update_delay + 2*error);

        controller.update(error, sender=owner);
        assertEq(controller.last_error(), error);
        assertEq(controller.error_integral(), error * 3 * update_delay + 3*error);
    # END CONTROL TESTING

    # START REWARD TESTING
    def test_set_scale(self, owner, controller, chain):
        controller.set_scale(1, 3*10**15, sender=owner)
        assert controller.scales(1) == 3*10**15

        controller.set_scale(10, 10000, sender=owner)
        assert controller.scales(10) == 10000

        controller.set_scale(10, 20000, sender=owner)
        assert controller.scales(10) == 20000
        assert controller.scales(1) == 3*10**15

    def test_set_scales(self, owner, controller, chain):
        controller.set_scales([(1, 3*10**15), (10, 10000)], sender=owner)
        assert controller.scales(1) == 3*10**15
        assert controller.scales(10) == 10000

        controller.set_scales([(1, 30*10**15), (10, 10000)], sender=owner)
        assert controller.scales(1) == 30*10**15
        assert controller.scales(10) == 10000
        controller.set_scales([(4, 40*10**15), (11, 11000)], sender=owner)
        assert controller.scales(1) == 30*10**15
        assert controller.scales(10) == 10000
        assert controller.scales(4) == 40*10**15
        assert controller.scales(11) == 11000

    def test_get_average(self, owner, controller, chain):
        assert controller.get_average(1) == 0

    def test_add_value(self, owner, controller, chain):
        controller.add_value(1, 5, sender=owner);
        assert controller.get_average(1) == 5
        controller.add_value(1, 7, sender=owner);
        assert controller.get_average(1) == 6

        assert controller.get_average(2) == 0

    def test_add_value_overflow(self, owner, controller, chain):
        assert controller.get_window_size(1) != 0
        for _ in range(controller.get_window_size(1)):
            controller.add_value(1, 5, sender=owner);

        assert controller.get_average(1) == 5

        controller.add_value(1, 10, sender=owner);

        assert controller.get_average(1) == ((controller.get_window_size(1)- 1)*5 + 10) // controller.get_window_size(1)

    def test_resize_buffer_down(self, owner, controller):
        assert controller.get_window_size(1) != 0

        for _ in range(controller.get_window_size(1)):
            controller.add_value(1, 5, sender=owner);

        controller.resize_buffer(1, controller.get_window_size(1)//2, sender=owner)

        assert controller.get_average(1) == 5


        for _ in range(controller.get_window_size(1)//2):
            controller.add_value(1, 5, sender=owner);

        for _ in range(controller.get_window_size(1)//2):
            controller.add_value(1, 10, sender=owner);

        controller.resize_buffer(1, controller.get_window_size(1)//2, sender=owner)

        assert controller.get_average(1) == 10

    def test_resize_buffer_up(self, owner, controller):
        orig_size = controller.get_window_size(2)
        for _ in range(orig_size):
            controller.add_value(2, 5, sender=owner);

        avg = controller.get_average(2)

        controller.resize_buffer(2, orig_size*2, sender=owner)
        assert controller.get_average(2) == avg

        for _ in range(orig_size):
            controller.add_value(2, 15, sender=owner);
        assert controller.get_average(2) == avg * 2

    def test_time_reward(self, owner, store, controller, chain):
        assert controller.calc_time_reward(0) == controller.min_time_reward()
        assert controller.calc_time_reward(2740774000*10**18) == controller.max_time_reward()

    def test_calc_time_reward_min(self, owner, controller):
        assert controller.min_time_reward() == params.min_reward//2
        assert controller.calc_time_reward(0) - params.min_reward//2 == 0
        assert controller.calc_time_reward(params.min_ts) - params.min_reward//2 == 0

    def test_calc_time_reward_max(self, owner, controller):
        assert controller.max_time_reward() == params.max_reward//2
        assert controller.calc_time_reward(params.max_ts) - params.max_reward//2  < 10**15

    def test_deviation_reward(self, owner, store, controller, chain):
        assert controller.calc_deviation_reward(0) == controller.min_deviation_reward()
        assert controller.calc_time_reward(1000000000*10**18) == controller.max_deviation_reward()

    def test_calc_deviation_reward_min(self, owner, controller):
        assert controller.min_deviation_reward() == params.min_reward//2
        assert controller.calc_deviation_reward(0) - params.min_reward//2 == 0
        assert controller.calc_deviation_reward(params.min_deviation) - params.min_reward//2 < 10**15

    def test_calc_deviation_reward_max(self, owner, controller):
        assert controller.max_deviation_reward() == params.max_reward//2
        assert controller.calc_deviation_reward(params.max_deviation) - params.max_reward//2 < 10**15

    def test_calc_reward(self, owner, controller):
        assert abs(sum(controller.calc_reward(params.min_ts, params.min_deviation)) - params.min_reward) < 10**15
        assert abs(sum(controller.calc_reward(params.max_ts, params.max_deviation)) - params.max_reward) < 10**15
        assert abs(sum(controller.calc_reward(params.max_ts, params.min_deviation)) - params.max_reward//2) < 10**15
        assert abs(sum(controller.calc_reward(params.min_ts, params.max_deviation)) - params.max_reward//2) < 10**15

    def test_update(self, owner, controller, oracle, chain):
        # fast forward to get maximum time since last oracle update
        chain.mine(1, timestamp = chain.pending_timestamp + 1*2)

        update_interval = 100 * 10**18
        target_time = 1800 * 10**18
        error = (update_interval - params.target_time_since) * 10**18 // update_interval
        res = controller.update(error, sender=owner)
        assert not res.failed
        output = controller.last_output()
        assert output != 0
        assert output != 10**18

    def test_update_oracle_mock(self, owner, controller, oracle, chain):
        # fast forward to get maximum time since last oracle update
        chain.mine(1800, timestamp = chain.pending_timestamp + 1800*2)
        tx = controller.update_oracle_mock(1, 1900*10**18, 300, sender=owner);
        chain.mine(1, timestamp = chain.pending_timestamp + 2)

        current_value: uint256 = 0
        current_height: uint64 = 0
        current_ts: uint48 = 0
        current_value, current_height, current_ts = oracle.get_value(1)

        assert current_ts == chain.pending_timestamp - 2

    def test_update_oracle_max_reward(self, owner, controller, chain):
        # fast forward to get maximum time since last oracle update
        chain.mine(1800, timestamp = chain.pending_timestamp + 1800*2)

        tx = controller.update_oracle_mock(1, 1900*10**18, 300, sender=owner);
        chain.mine(1, timestamp = chain.pending_timestamp + 2)
        tx = controller.update_oracle_mock(1, 1910*10**18, 301, sender=owner);
        chain.mine(1, timestamp = chain.pending_timestamp + 2)
        tx = controller.update_oracle_mock(1, 1910*10**18, 302, sender=owner);
        chain.mine(1, timestamp = chain.pending_timestamp + 2)
        tx = controller.update_oracle_mock(1, 1910*10**18, 303, sender=owner);
        chain.mine(1, timestamp = chain.pending_timestamp + 2)
        tx = controller.update_oracle_mock(1, 1910*10**18, 304, sender=owner);
        chain.mine(1, timestamp = chain.pending_timestamp + 2)
        tx = controller.update_oracle_mock(1, 1910*10**18, 305, sender=owner);

        """
        # Decode the logs/events from transaction
        events = list(tx.decode_logs())
        e = events[0]
        assert len(events) == 1
        assert e.reward == params.max_reward
        """

        #assert controller.rewards(owner) == params.max_reward

    def test_update_oracle_min_reward(self, owner, controller, chain):

        # first update
        tx = controller.update_oracle_mock(1, 1900*10**18, 300, sender=owner);

        first_balance = controller.rewards(owner)

        # immediately update again
        tx2 = controller.update_oracle_mock(1, 1900*10**18, 301, sender=owner);

        """
        events = list(tx2.decode_logs())

        e = events[0]

        assert len(events) == 1

        assert e.reward == params.min_reward
        assert controller.rewards(owner) == first_balance + params.min_reward
        """

    def test_prepare_header(self, store, controller):
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

    def _test_fork(self, owner, store, oracle_sepolia, controller_sepolia, chain):

        #a: bytes = b'\x00\x00\x00\x00\x00\x00\x00\x03\x01\x95\xb6+\xfcv\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x01Q\x17\xed\x01\x00k\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1b\x8dy\xed\x00p\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01B\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05N\x08A\x8b\xb7B^\xb0n\xa2XgHC\xabaC\xa1\xab\\L\x98\xcd\x07\x95[\xc1$\xdf\x0f2q\xf4KDe]B5\x90\x92\n2\xcf7\xa8i\xcey\xb5\x90\xac\x03\xdd\xa7\xd5\xfc\xbc\xc5\xe4\xde\x04B\x17C\x00U\x1c'

        w3 = Web3(HTTPProvider('https://rpc.gas.network'))
        address = '0x4245Cb7c690B650a38E680C9BcfB7814D42BfD32'

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=address, abi=abi)

        sid = 2
        cid = 10
        typ = 107

        # read gasnet
        a: bytes = oracle_gasnet.functions.getValues(sid, cid).call()

        # decode gasnet payload
        system_id, c_id, t, new_value, new_ts = store.decode(a, 107)
        assert system_id == sid
        assert c_id == cid
        assert t == typ

        # decode gasnet header
        plen, scid, _, new_height = store.decode_header(a)
        assert plen > 0

        chain.mine(1, timestamp=chain.pending_timestamp+12)

        # get current oracle values
        value, height, ts = oracle_sepolia.get(sid, cid, typ)
        assert value !=0
        assert new_ts != ts
        assert new_value != value
        assert new_height != height

        assert new_height > height
        assert new_ts > ts

        # update #1
        tx = controller_sepolia.update_oracle(a, sender=owner, raise_on_revert=True)
        print(tx.show_trace(True))
        chain.mine(1, timestamp=chain.pending_timestamp+12)

        # get current oracle values
        updated_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, typ)
        assert updated_value == new_value
        assert updated_height == new_height
        assert updated_ts == new_ts

        time.sleep(4)

        # read gasnet
        a: bytes = oracle_gasnet.functions.getValues(sid, cid).call()
        # decode gasnet payload
        system_id, c_id, t, new_value, new_ts = store.decode(a, 107)

        # update #2
        tx = controller_sepolia.update_oracle(a, sender=owner, raise_on_revert=False)
        print(tx.show_trace(True))
        final_value, final_height, final_ts = oracle_sepolia.get(sid, cid, typ)
        assert final_value == new_value
        assert final_ts == new_ts
        assert final_ts > ts


    def _test_fork_loop(self, owner, store, oracle_sepolia, controller_sepolia, chain):

        w3 = Web3(HTTPProvider('https://rpc.gas.network'))
        address = '0x4245Cb7c690B650a38E680C9BcfB7814D42BfD32'

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=address, abi=abi)

        sid = 2
        cid = 10
        typ = 107
        print("")
        for i in range(5):

            # read gasnet
            a: bytes = oracle_gasnet.functions.getValues(sid, cid).call()

            # decode gasnet payload
            system_id, c_id, t, new_value, new_ts = store.decode(a, 107)
            assert system_id == sid
            assert c_id == cid
            assert t == typ
            print(f"Update #{i+1}: {new_value=}, {new_ts=}")

            # decode gasnet header
            plen, scid, _, new_height = store.decode_header(a)
            assert plen > 0

            chain.mine(1, timestamp=chain.pending_timestamp+12)

            # get current oracle values
            value, height, ts = oracle_sepolia.get(sid, cid, typ)
            assert value !=0
            #assert new_ts != ts
            #assert new_value != value
            #assert new_height != height

            assert new_height >= height
            assert new_ts >= ts

            # update
            tx = controller_sepolia.update_oracle(a, sender=owner, raise_on_revert=True)
            tx.show_trace(True)
            chain.mine(1, timestamp=chain.pending_timestamp+12)

            # get current oracle values
            updated_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, typ)
            assert updated_value == new_value
            assert updated_height == new_height
            assert updated_ts == new_ts

            time.sleep(3)

    def test_fork_deployed(self, project, oracle_sepolia):

        controller_deployed_sepolia = project.RewardController.at("0xe48555990092ff02a7cdd0e6b772fba9b7a3e9fd")
        account = accounts.load("blocknative_dev")
        print(account)
        w3 = Web3(HTTPProvider('https://rpc.gas.network'))
        address = '0x4245Cb7c690B650a38E680C9BcfB7814D42BfD32'

        with open('tests/gasnet_oracle_v2.json') as f:
            abi = json.load(f)['abi']

        oracle_gasnet = w3.eth.contract(address=address, abi=abi)

        sid = 2
        cid = 10
        typ = 107

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
        value, height, ts = oracle_sepolia.get(sid, cid, typ)
        """
        assert value !=0
        assert new_ts != ts
        assert new_value != value
        assert new_height != height

        assert new_height > height
        assert new_ts > ts
        """
        assert value !=0

        # update #1
        tx = controller_deployed_sepolia.update_oracle(a, sender=account, raise_on_revert=True, gas=3000000)
        tx.show_trace(True)

        # get current oracle values
        updated_value, updated_height, updated_ts = oracle_sepolia.get(sid, cid, typ)
        assert updated_value != value
        assert updated_height != height
        assert updated_ts != ts

    def test_decode_sepolia(self, owner, store):
        a: bytes = bytes.fromhex("00000000000000030195b2fa97ac020000000000000001000000000151068e01006b00000000000000000000000000000000000000000000000000001b41cc72007000000000000000000000000000000000000000000000000000000000000101420000000000000000000000000000000000000000000000000000054e08416125c490371fffb5a8d98ea858cbc794ef0d639c8a32ceae4fd737da2df952d4752463d591cd2ff3f33cfe8d7b2ab989aa9001ce9b7455722d29a909a4f69e0b1c")


        sid, cid, plen, ts = store.decode_sid_cid(a)
        assert sid == 2
        assert cid == 1
