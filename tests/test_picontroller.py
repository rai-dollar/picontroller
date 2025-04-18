import ape
import pytest
from web3 import Web3

#from ape import accounts

FORTY_FIVE_DECIMAL_NUMBER   = int(10 ** 45)
TWENTY_SEVEN_DECIMAL_NUMBER = int(10 ** 27)
EIGHTEEN_DECIMAL_NUMBER     = int(10 ** 18)

update_delay = 3600;

kp = 222002205862
ki = int(EIGHTEEN_DECIMAL_NUMBER)
co_bias = 0
per_second_integral_leak = 999997208243937652252849536 # 1% per hour
output_upper_bound = 18640000000000000000
output_lower_bound = -51034000000000000000

imported_state = [0] * 3

@pytest.fixture
def owner(accounts):
    return accounts[0]

@pytest.fixture
def controller(owner, project):
    controller = owner.deploy(project.PIController, b'test control variable',
            kp,
            ki,
            co_bias,
            per_second_integral_leak,
            output_upper_bound,
            output_lower_bound,
            imported_state,
            sender=owner)

    controller.modify_parameters_addr('updater',  owner, sender=owner)
    return controller

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

class TestPIController:
    def check_state(self, owner, controller):
        assertEq(controller.authorities(owner), 1);
        assertEq(controller.output_upper_bound(), output_upper_bound);
        assertEq(controller.output_lower_bound(), output_lower_bound);
        assertEq(controller.last_update_time(), 0);
        assertEq(controller.error_integral(), 0);
        assertEq(controller.last_error(), 0);
        assertEq(controller.per_second_integral_leak(), per_second_integral_leak);
        assertEq(controller.kp(), kp);
        assertEq(controller.ki(), ki);
        assertEq(controller.elapsed(), 0);

    def test_contract_fixture(self, owner, controller):
        assertEq(controller.authorities(owner), 1);
        assertEq(controller.output_upper_bound(), output_upper_bound);
        assertEq(controller.output_lower_bound(), output_lower_bound);
        assertEq(controller.last_update_time(), 0);
        assertEq(controller.error_integral(), 0);
        assertEq(controller.per_second_integral_leak(), per_second_integral_leak);
        assertEq(bytes.fromhex(controller.control_variable().hex().rstrip("0")).decode('utf8'), 'test control variable');
        assertEq(kp, controller.kp());
        assertEq(ki, controller.ki());
        assertEq(controller.elapsed(), 0);

    def test_modify_parameters(self, owner, controller):
        controller.modify_parameters_int("kp", int(1), sender=owner);
        controller.modify_parameters_int("ki", int(1), sender=owner);
        assertEq(int(1), controller.ki());
        assertEq(int(1), controller.kp());

        controller.modify_parameters_int("output_upper_bound", int(TWENTY_SEVEN_DECIMAL_NUMBER + 1), sender=owner);
        controller.modify_parameters_int("output_lower_bound", -int(1), sender=owner);
        assertEq(controller.output_upper_bound(), int(TWENTY_SEVEN_DECIMAL_NUMBER + 1));
        assertEq(controller.output_lower_bound(), -int(1));

        controller.modify_parameters_uint("per_second_integral_leak", int(TWENTY_SEVEN_DECIMAL_NUMBER - 5), sender=owner);
        assertEq(controller.per_second_integral_leak(), TWENTY_SEVEN_DECIMAL_NUMBER - 5);


    def test_fail_modify_parameters_upper_bound(self, owner, controller):
        with ape.reverts("PIController/invalid-output_upper_bound"):
            controller.modify_parameters_int("output_upper_bound", controller.output_lower_bound() - 1, sender=owner);
    
    def test_fail_modify_parameters_lower_bound(self, owner, controller):
        with ape.reverts("PIController/invalid-output_lower_bound"):
            controller.modify_parameters_int("output_lower_bound", controller.output_upper_bound() + 1, sender=owner);

    def test_get_next_output_zero_error(self, owner, controller):
        error = relative_error(EIGHTEEN_DECIMAL_NUMBER, TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output,_,_) = controller.get_new_pi_output(error);
        assertEq(pi_output, 0);
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_next_output_nonzero_error(self, owner, controller):
        error = relative_error(int(1.1E18), 10**27);
        assertEq(error, -100000000000000000000000000)

        (pi_output,_,_) = controller.get_new_pi_output(error);
        assert pi_output != 0
        assertEq(pi_output, kp * int(error/10**18))
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_zero_error(self, owner, controller):
        error = relative_error(EIGHTEEN_DECIMAL_NUMBER, TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output,_,_) = controller.get_raw_pi_output(error, 0);
        assertEq(pi_output, 0);
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_nonzero_error(self, owner, controller):
        error = int(10**20)
        (pi_output,p_output,i_output) = controller.get_raw_pi_output(error, 0);
        assertEq(p_output, kp * int(error/1E18));
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_small_nonzero_error(self, owner, controller):
        error = int(10**18)
        (pi_output,p_output,i_output) = controller.get_raw_pi_output(error, 0);
        assertGt(pi_output, 0)
        assertEq(p_output, kp * int(error/1E18));
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_large_nonzero_error(self, owner, controller):
        error = int(10**20) * int(10**18)
        (pi_output,p_output,i_output) = controller.get_raw_pi_output(error, 0);
        assertEq(p_output, kp * int(error/1E18));
        assertEq(controller.error_integral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_first_update(self, owner, controller, chain):
        next_ts = chain.pending_timestamp
        controller.update(1, sender=owner)
        assertEq(controller.last_update_time(), next_ts);
        assertEq(controller.last_error(), 1);
        assertEq(controller.error_integral(), 0);

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

    """
   
    def test_zero_integral_persists(self, owner, controller, chain):
        assertEq(controller.error_integral(), 0);
        next_ts = chain.pending_timestamp + 10000000
        assertEq(controller.error_integral(), 0);
    """


    """
    def test_nonzero_integral_persists(self, owner, controller, chain):
        controller.update(1, sender=owner);
        controller.update(1, sender=owner);
        chain.provider.auto_mine = False
        chain.mine(1000, timestamp = chain.pending_timestamp + 1000*12)

        initial_error_integral = controller.error_integral();
        assertGt(initial_error_integral, 0)
        assertEq(initial_error_integral, controller.error_integral());

    """

    def test_first_get_next_output(self, owner, controller):
        # negative error
        error = relative_error(int(1.01E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, kp * int(error/1E18));
        assert pi_output != 0
        assertEq(controller.error_integral(), 0);

        # positive error
        error = relative_error(int(0.995E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, kp * int(0.005E27/1E18));
        assert pi_output != 0
        assertEq(controller.error_integral(), 0);

    def test_first_get_next_output_w_bias(self, owner, controller):
        bias = 30000;
        controller.modify_parameters_int("co_bias", bias, sender=owner);
        # negative error
        error = relative_error(int(1.01E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, bias + kp * int(error/1E18));
        assert pi_output != 0
        assertEq(controller.error_integral(), 0);

        # positive error
        error = relative_error(int(0.995E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, bias + kp * int(0.005E27/1E18));
        assert pi_output != 0
        assertEq(controller.error_integral(), 0);

    def test_first_negative_error(self, owner, controller, chain):
        error = relative_error(int(1.05E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, kp * int(error/1E18));
        assertEq(p_output, kp * int(error/1E18));
        assertEq(i_output, 0);

        next_ts = chain.pending_timestamp
        controller.update(error, sender=owner);
        (update_time, pi_output, p_output, i_output) = controller.last_update()
        assertEq(pi_output, kp * int(error/1E18));
        assertEq(p_output, kp * int(error/1E18));
        assertEq(i_output, 0);

        assertEq(controller.last_update_time(), next_ts);
        assertEq(controller.error_integral(), 0);
        assertEq(controller.last_error(), -10**27//20);

    def test_first_positive_error(self, owner, controller, chain):
        error = relative_error(int(0.95E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assertEq(pi_output, kp * int(error/1E18));
        assertEq(p_output, kp * int(error/1E18));
        assertEq(i_output, 0);

        next_ts = chain.pending_timestamp
        controller.update(error, sender=owner);
        (update_time, pi_output, p_output, i_output) = controller.last_update()
        assertEq(pi_output, kp * int(error/1E18));
        assertEq(p_output, kp * int(error/1E18));
        assertEq(i_output, 0);

        assertEq(controller.last_update_time(), next_ts);
        assertEq(controller.error_integral(), 0);
        assertEq(controller.last_error(), 10**27//20);

    def test_basic_integral(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);
        controller.modify_parameters_uint("per_second_integral_leak", 10**27, sender=owner);

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
        controller.modify_parameters_uint("per_second_integral_leak", 10**27, sender=owner);

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


    """
    TODO: fix after integral leak is fixed
    def test_integral_leaks(self, owner, controller, chain):
        leak = int(0.999999999E27)
        controller.modify_parameters_uint("per_second_integral_leak", leak, sender=owner);
        error = int(-0.0001 * 10**27)

        # First update
        # Need to update twice since first update doesn't create an error integral
        # as elapsed time is 0
        controller.update(error, sender=owner);
        controller.update(error, sender=owner);
        error_integral1 = controller.error_integral();
        assert error_integral1 < 0;

        # Second update
        controller.update(error, sender=owner);
        error_integral2 = controller.error_integral();
        assert error_integral2 > error_integral1;
    """

    def test_integral_leaks2(self, owner, controller, chain):
        leak = 998721603904830360273103599
        #leak = 10**27

        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);
        controller.modify_parameters_uint("per_second_integral_leak", leak, sender=owner);

        error = int(10**23)

        # First update
        # Need to update twice since first update doesn't create an error integral
        # as elapsed time is 0
        controller.update(error, sender=owner);
        assert controller.error_integral() == 0;

        # Second update
        controller.update(error, sender=owner);
        error_integral1 = controller.error_integral();
        assert error_integral1 == error;

        update_delay = 1000
        chain.pending_timestamp += update_delay

        # Third update
        controller.update(error, sender=owner);
        error_integral2 = controller.error_integral();
        assert error_integral2 == error_integral1 + (update_delay+1)*error;


    """
    def test_leaks_sets_integral_to_zero(self, owner, controller, chain):
        #chain.provider.auto_mine = False
        assert controller.error_integral() == 0
        controller.modify_parameters_int("kp", 1000, sender=owner);
        controller.modify_parameters_uint("per_second_integral_leak", 998721603904830360273103599,
                                        sender=owner); # -99% per hour

        first_ts = chain.pending_timestamp
        # First update
        controller.update(10**27//10000, sender=owner);
        #chain.mine(1)
        # Second update
        controller.update(10**27//10000, sender=owner);
        #chain.mine(1)
        # Third update
        controller.update(10**27//10000, sender=owner);
        #chain.mine(1)
        last_ts = chain.pending_timestamp

        error_integral1 = controller.error_integral()
        assert error_integral1 > 0;

        #chain.provider.auto_mine = False
        blocktime = 1
        chain.mine(360000, timestamp = chain.pending_timestamp + 360000*blocktime)
        error = relative_error(int(10**18), int(10**27));
        assert error == 0;

        (pi_output, p_output, i_output) = controller.get_new_pi_output(error);
        assert p_output == 0;

        controller.update(error, sender=owner);
        error_integral2 = controller.error_integral()
        assert error_integral2 < error_integral1;

        chain.mine(360000, timestamp = chain.pending_timestamp + 360000*blocktime)
        controller.update(error, sender=owner);
        last_ts = chain.pending_timestamp
        assert controller.error_integral() == 0;
    """


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
        controller.modify_parameters_int("kp", int(2.25E11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2E4), sender=owner);
        assert controller.ki() == 72000
        controller.modify_parameters_uint("per_second_integral_leak", 10**27, sender=owner);
        chain.mine(update_delay, timestamp=chain.pending_timestamp+update_delay)

        # First update doesn't create an integral or output contribution
        # as elapsed time is set to 0
        error = relative_error(int(1.01E18), 10**27);
        assert error == -1 * 10**25
        (new_integral, new_area) = controller.get_new_error_integral(error);
        assertEq(new_integral, 0);
        assertEq(new_area, 0);
        controller.update(error, sender=owner);
        assertEq(controller.error_integral(), new_integral);

        #chain.mine(update_delay)#, timestamp=chain.pending_timestamp+update_delay)
        next_pending_ts = chain.pending_timestamp + update_delay
        chain.pending_timestamp = next_pending_ts

        # Second update
        error = relative_error(int(1.01E18), 10**27);
        (new_integral, new_area) = controller.get_new_error_integral(error);
        assert new_integral == error * update_delay
        assert new_area == error * update_delay
        controller.update(error, sender=owner);
        assert controller.last_update_time() == next_pending_ts
        assertEq(controller.error_integral() - 1*error, new_integral);

        chain.pending_timestamp += update_delay

        # Third update
        error = relative_error(int(1.01E18), 10**27);
        (new_integral, new_area) = controller.get_new_error_integral(error);
        assert new_integral == error * update_delay * 2 + error
        assert new_area == error * update_delay
        controller.update(error, sender=owner);
        assertEq(controller.error_integral() -1*error, new_integral);


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
        assertEq(pi_output, kp * error//10**18);
        assertEq(p_output, kp * error//10**18);
        assertEq(i_output, 0);
        
        error = relative_error(int(1.05* 10**18), 10**27);
        (pi_output, p_output, i_output) = controller.get_raw_pi_output(error, 0);
        assertEq(pi_output, kp * error//10**18);
        assertEq(p_output, kp * error//10**18);
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
        controller.modify_parameters_uint("per_second_integral_leak", 10**27, sender=owner);

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
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);
        controller.modify_parameters_uint("per_second_integral_leak", 10**27, sender=owner);

        chain.pending_timestamp += update_delay

        error = relative_error(int(1.01* 10**18), 10**27);

        # First error: small, output doesn't hit lower bound
        controller.update(error, sender=owner);
        (_, pi_output, _, _) = controller.last_update()
        assert pi_output < 0;
        assert pi_output > controller.output_lower_bound();
        # Integral is zero for first error
        assertEq(controller.error_integral(), 0);

        chain.pending_timestamp += update_delay

        (leaked_integral, new_area) = controller.get_new_error_integral(error);
        assertEq(leaked_integral, -36000000000000000000000000000);
        assertEq(new_area, -36000000000000000000000000000);

        # Second error: small, output doesn't hit lower bound
        controller.update(error, sender=owner);
        (_, pi_output2, _, _) = controller.last_update()
        assert pi_output2 < pi_output;
        assert pi_output2 > controller.output_lower_bound();
        assertEq(controller.error_integral() -error, -36000000000000000000000000000);

        chain.pending_timestamp += update_delay

        # Third error: very large. Output hits lower bound
        # Integral *does not* accumulate when it hits bound with same sign of current integral
        huge_neg_error = relative_error(int(1.6* 10**18), 10**27);

        controller.update(huge_neg_error, sender=owner);
        (_, pi_output3, _, _) = controller.last_update()
        assertEq(pi_output3, controller.output_lower_bound());
        # Integral doesn't accumulate
        assertEq(controller.error_integral() - error, -36000000000000000000000000000);

        chain.pending_timestamp += update_delay

        # Integral *does* accumulate with a smaller error(doesn't hit output bound)
        small_neg_error = relative_error(int(1.01* 10**18), 10**27);

        controller.update(small_neg_error, sender=owner);
        (_, pi_output4, _, _) = controller.last_update()
        assert controller.error_integral() < -36000000000000000000000000000;
        assert pi_output4 > controller.output_lower_bound();

    def test_upper_clamping(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);
        controller.modify_parameters_uint("per_second_integral_leak", 10**27, sender=owner);
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

        assertEq(pi_output, kp * error//10**18);
        assertEq(p_output, kp * error//10**18);
        assertEq(i_output, 0);
        assertEq(bounded_output, kp * error//10**18);

        # large negative error, hits lower bound
        error = relative_error(int(1.5*10**18), 10**27);
        (pi_output, p_output, i_output) = controller.get_raw_pi_output(error, 0);
        bounded_output = controller.bound_pi_output(pi_output);

        assertEq(pi_output, kp * error//10**18);
        assertEq(p_output, kp * error//10**18);
        assertEq(i_output, 0);
        assertEq(bounded_output, output_lower_bound);

        # large positive error, hits upper bound
        error = relative_error(int(0.5*10**18), 10**27);
        (pi_output, p_output, i_output) = controller.get_raw_pi_output(error, 0);

        bounded_output = controller.bound_pi_output(pi_output);

        assertEq(pi_output, kp * error//10**18);
        assertEq(p_output, kp * error//10**18);
        assertEq(i_output, 0);
        assertEq(bounded_output, output_upper_bound);

    def test_last_error_integral(self, owner, controller, chain):
        controller.modify_parameters_int("kp", int(2.25*10**11), sender=owner);
        controller.modify_parameters_int("ki", int(7.2 * 10**4), sender=owner);
        controller.modify_parameters_uint("per_second_integral_leak", 10**27, sender=owner);

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


"""
    }
    function test_leak_sets_integral_to_zero() public {
        assertEq(uint(controller.error_integral()), 0);

        controller.modify_parameters("kp", int(1000));
        controller.modify_parameters("per_second_integral_leak", uint(998721603904830360273103599)); // -99% per hour
        //controller.modify_parameters("per_second_integral_leak", uint(0.95E27)); // -99% per hour

        // First update
        hevm.warp(now + update_delay);
        (int output, int p_output, int i_output) = controller.update(-0.0001E27);
        //assert(controller.error_integral() == 0);

        // Second update
        hevm.warp(now + update_delay);
        (pi_output, p_output, i_output) = controller.update(-0.0001E27);
        //assert(controller.error_integral() == 0);

        // Third update
        hevm.warp(now + update_delay);
        (pi_output, i_output, p_output) = controller.update(-0.0001E27);

        assert(controller.error_integral() < 0);

        // Final update
        hevm.warp(now + update_delay * 100);

        int256 error = relative_error(1E18, 1E27);
        assertEq(error, 0);

        (pi_output, p_output, i_output) =
          controller.get_new_pi_output(error);
        assertEq(p_output, 0);

        (pi_output, p_output, i_output) = controller.update(error);
        hevm.warp(now + update_delay * 100);
        (pi_output, p_output, i_output) = controller.update(error);
        assertEq(controller.error_integral(), 0);

    }
    function test_get_next_error_integral_leak() public {
        controller.modify_parameters("updater", address(this));
        controller.modify_parameters("kp", int(2.25E11));
        controller.modify_parameters("ki", int(7.2E4));
        controller.modify_parameters("per_second_integral_leak", uint(0.95E27));
        hevm.warp(now + update_delay);

        // First update doesn't create an integral or output contribution
        // as elapsed time is set to 0
        int256 error = relative_error(1.01E18, 1.00E27);
        (int256 new_integral, int256 new_area) = controller.getNewErrorIntegral(error);
        assertEq(new_integral, 0);
        assertEq(new_area, 0);
        controller.update(error);
        assertEq(controller.error_integral(), new_integral);

        hevm.warp(now + update_delay);

        // Second update
        int error2 = relative_error(1.01E18, 1.00E27);
        (int new_integral2, int new_area2) = controller.getNewErrorIntegral(error2);
        assertEq(new_integral2, error2 * int(update_delay));
        assertEq(new_area2, error2 * int(update_delay));

        controller.update(error2);
        assertEq(controller.error_integral(), new_integral2);

        hevm.warp(now + update_delay);

        // Third update
        int error3 = relative_error(1.00E18, 1.00E27);
        assertEq(error3, 0);
        (int new_integral3, int new_area3) = controller.getNewErrorIntegral(error3);
        assertEq(new_area3, (error2 + error3)/2 * int(update_delay));
        assert(new_integral3 -new_area3 > new_integral2);
        controller.update(error3);
        assertEq(controller.error_integral(), new_integral3);

    }

"""
