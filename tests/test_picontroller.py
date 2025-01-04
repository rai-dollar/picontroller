import ape
import pytest
from web3 import Web3

#from ape import accounts

FORTY_FIVE_DECIMAL_NUMBER   = int(10 ** 45)
TWENTY_SEVEN_DECIMAL_NUMBER = int(10 ** 27)
EIGHTEEN_DECIMAL_NUMBER     = int(10 ** 18)

updateDelay = 3600;

kp = 222002205862
ki = int(EIGHTEEN_DECIMAL_NUMBER)
coBias = 0
perSecondIntegralLeak = 999997208243937652252849536 # 1% per hour
outputUpperBound = 18640000000000000000
outputLowerBound = -51034000000000000000

importedState = [0] * 3

@pytest.fixture
def owner(accounts):
    return accounts[0]

@pytest.fixture
def controller(owner, project):
    controller = owner.deploy(project.PIController, b'test control variable',
            kp,
            ki,
            coBias,
            perSecondIntegralLeak,
            outputUpperBound,
            outputLowerBound,
            importedState,
            sender=owner)

    controller.modifyParametersAddr('seedProposer',  owner, sender=owner)
    return controller

# Use this to match existing controller tests
def assertEq(x, y):
    assert x == y

def assertGt(x, y):
    assert x > y

def assertLt(x, y):
    assert x < y

def relative_error(measuredValue, referenceValue):
    # measuredValue is WAD, referenceValue is a RAY
    # Logic from rate setter

    scaledMeasuredValue = int(measuredValue) *  int(10**9)
    return ((referenceValue - scaledMeasuredValue) * TWENTY_SEVEN_DECIMAL_NUMBER) // referenceValue
class TestPIController:
    def check_state(self, owner, controller):
        assertEq(controller.authorities(owner), 1);
        assertEq(controller.outputUpperBound(), outputUpperBound);
        assertEq(controller.outputLowerBound(), outputLowerBound);
        assertEq(controller.lastUpdateTime(), 0);
        assertEq(controller.errorIntegral(), 0);
        assertEq(controller.lastError(), 0);
        assertEq(controller.perSecondIntegralLeak(), perSecondIntegralLeak);
        assertEq(controller.kp(), kp);
        assertEq(controller.ki(), ki);
        assertEq(controller.elapsed(), 0);

    def test_contract_fixture(self, owner, controller):
        assertEq(controller.authorities(owner), 1);
        assertEq(controller.outputUpperBound(), outputUpperBound);
        assertEq(controller.outputLowerBound(), outputLowerBound);
        assertEq(controller.lastUpdateTime(), 0);
        assertEq(controller.errorIntegral(), 0);
        assertEq(controller.perSecondIntegralLeak(), perSecondIntegralLeak);
        assertEq(bytes.fromhex(controller.controlVariable().hex().rstrip("0")).decode('utf8'), 'test control variable');
        assertEq(kp, controller.kp());
        assertEq(ki, controller.ki());
        assertEq(controller.elapsed(), 0);

    def test_modify_parameters(self, owner, controller):
        controller.modifyParametersInt("kp", int(1), sender=owner);
        controller.modifyParametersInt("ki", int(1), sender=owner);
        assertEq(int(1), controller.ki());
        assertEq(int(1), controller.kp());

        controller.modifyParametersInt("outputUpperBound", int(TWENTY_SEVEN_DECIMAL_NUMBER + 1), sender=owner);
        controller.modifyParametersInt("outputLowerBound", -int(1), sender=owner);
        assertEq(controller.outputUpperBound(), int(TWENTY_SEVEN_DECIMAL_NUMBER + 1));
        assertEq(controller.outputLowerBound(), -int(1));

        controller.modifyParametersUint("perSecondIntegralLeak", int(TWENTY_SEVEN_DECIMAL_NUMBER - 5), sender=owner);
        assertEq(controller.perSecondIntegralLeak(), TWENTY_SEVEN_DECIMAL_NUMBER - 5);

    def test_fail_modify_parameters_upper_bound(self, owner, controller):
        with ape.reverts("PIController/invalid-outputUpperBound"):
            controller.modifyParametersInt("outputUpperBound", controller.outputLowerBound() - 1, sender=owner);
    
    def test_fail_modify_parameters_lower_bound(self, owner, controller):
        with ape.reverts("PIController/invalid-outputLowerBound"):
            controller.modifyParametersInt("outputLowerBound", controller.outputUpperBound() + 1, sender=owner);

    def test_get_next_output_zero_error(self, owner, controller):
        error = relative_error(EIGHTEEN_DECIMAL_NUMBER, TWENTY_SEVEN_DECIMAL_NUMBER);
        (piOutput,_,_) = controller.getNextPiOutput(error);
        assertEq(piOutput, 0);
        assertEq(controller.errorIntegral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_next_output_nonzero_error(self, owner, controller):
        measured = int(1.1e18)
        target = TWENTY_SEVEN_DECIMAL_NUMBER
        error = relative_error(measured, target);
        assertEq(error, -100000000000000000000000000)

        (piOutput,_,_) = controller.getNextPiOutput(error);
        assert piOutput != 0
        assertEq(piOutput, kp * int(error/10**18))
        assertEq(controller.errorIntegral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_zero_error(self, owner, controller):
        error = relative_error(EIGHTEEN_DECIMAL_NUMBER, TWENTY_SEVEN_DECIMAL_NUMBER);
        (piOutput,_,_) = controller.getRawPiOutputExternal(error, 0);
        assertEq(piOutput, 0);
        assertEq(controller.errorIntegral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_nonzero_error(self, owner, controller):
        #(piOutput,pOutput,iOutput) = controller.getNextPiOutput(1);
        error = int(10**20)
        (piOutput,pOutput,iOutput) = controller.getRawPiOutputExternal(error, 0);
        assertEq(pOutput, kp * int(error/1E18));
        assertEq(controller.errorIntegral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_small_nonzero_error(self, owner, controller):
        #(piOutput,pOutput,iOutput) = controller.getNextPiOutput(1);
        error = int(10**18)
        (piOutput,pOutput,iOutput) = controller.getRawPiOutputExternal(error, 0);
        assertGt(piOutput, 0)
        assertEq(pOutput, kp * int(error/1E18));
        assertEq(controller.errorIntegral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_get_raw_output_large_nonzero_error(self, owner, controller):
        #(piOutput,pOutput,iOutput) = controller.getNextPiOutput(1);
        error = int(10**20) * int(10**18)
        (piOutput,pOutput,iOutput) = controller.getRawPiOutputExternal(error, 0);
        assertEq(pOutput, kp * int(error/1E18));
        assertEq(controller.errorIntegral(), 0);

        # Verify did not change state
        self.check_state(owner, controller)

    def test_first_update(self, owner, controller, chain):
        next_ts = chain.pending_timestamp
        controller.update(1, sender=owner)
        assertEq(controller.lastUpdateTime(), next_ts);
        assertEq(controller.lastError(), 1);
        assertEq(controller.errorIntegral(), 0);

    def test_first_update_zero_error(self, owner, controller, chain):
        next_ts = chain.pending_timestamp
        controller.update(0, sender=owner)
        assertEq(controller.lastUpdateTime(), next_ts);
        assertEq(controller.lastError(), 0);
        assertEq(controller.errorIntegral(), 0);

    def test_two_updates(self, owner, controller, chain):
        controller.update(1, sender=owner)
        controller.update(2, sender=owner)
        assertEq(controller.lastError(), 2);
        #assertEq(controller.errorIntegral(), 0);

   
    def test_zero_integral_persists(self, owner, controller, chain):
        assertEq(controller.errorIntegral(), 0);
        next_ts = chain.pending_timestamp + 10000000
        assertEq(controller.errorIntegral(), 0);

    """
    def test_nonzero_integral_persists(self, owner, controller, chain):
        controller.update(1, sender=owner);
        controller.update(1, sender=owner);
        chain.provider.auto_mine = False
        chain.mine(1000, timestamp = chain.pending_timestamp + 1000*12)

        initialErrorIntegral = controller.errorIntegral();
        assertGt(initialErrorIntegral, 0)
        assertEq(initialErrorIntegral, controller.errorIntegral());
    """

    def test_first_get_next_output(self, owner, controller):
        # negative error
        error = relative_error(int(1.01E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (piOutput, pOutput, iOutput) = controller.getNextPiOutput(error);
        assertEq(piOutput, kp * int(error/1E18));
        assert piOutput != 0
        assertEq(controller.errorIntegral(), 0);

        # positive error
        error = relative_error(int(0.995E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (piOutput, pOutput, iOutput) = controller.getNextPiOutput(error);
        assertEq(piOutput, kp * int(0.005E27/1E18));
        assert piOutput != 0
        assertEq(controller.errorIntegral(), 0);

    def test_first_get_next_output_w_bias(self, owner, controller):
        bias = 30000;
        controller.modifyParametersInt("coBias", bias, sender=owner);
        # negative error
        error = relative_error(int(1.01E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (piOutput, pOutput, iOutput) = controller.getNextPiOutput(error);
        assertEq(piOutput, bias + kp * int(error/1E18));
        assert piOutput != 0
        assertEq(controller.errorIntegral(), 0);

        # positive error
        error = relative_error(int(0.995E18), TWENTY_SEVEN_DECIMAL_NUMBER);
        (piOutput, pOutput, iOutput) = controller.getNextPiOutput(error);
        assertEq(piOutput, bias + kp * int(0.005E27/1E18));
        assert piOutput != 0
        assertEq(controller.errorIntegral(), 0);

    def test_first_positive_error(self, owner, controller, chain):
        error = relative_error(1.05E18, TWENTY_SEVEN_DECIMAL_NUMBER);
        (output, pOutput, iOutput) = controller.getNextPiOutput(error);
        assertEq(output, kp * int(error/1E18));
        assertEq(pOutput, kp * int(error/1E18));
        assertEq(iOutput, 0);

        next_ts = chain.pending_timestamp
        controller.update(error, sender=owner);
        (updateTime, output, pOutput, iOutput) = controller.lastUpdate()
        assertEq(output, kp * int(error/1E18));
        assertEq(pOutput, kp * int(error/1E18));
        assertEq(iOutput, 0);

        assertEq(controller.lastUpdateTime(), next_ts);
        assertEq(controller.errorIntegral(), 0);
        assertEq(controller.lastError(), -10**27//20);


    """
    """


"""

    }
    function test_first_positive_error() public {

        hevm.warp(now + updateDelay);

        int256 error = relative_error(1.05E18, TWENTY_SEVEN_DECIMAL_NUMBER);
        (int output, int pOutput, int iOutput) =
          controller.getNextPiOutput(error);
        assertEq(output, Kp * error / 1E18);
        assertEq(pOutput, Kp * error / 1E18);
        assertEq(iOutput, 0);

        (output, pOutput, iOutput) = controller.update(error);
        assertEq(output, Kp * error / 1E18);
        assertEq(pOutput, Kp * error / 1E18);
        assertEq(iOutput, 0);

        assertEq(uint(controller.lastUpdateTime()), now);
        assertEq(controller.errorIntegral(), 0);
        assertEq(controller.lastError(), -0.05E27);
    }
    function test_first_negative_error() public {
        assertEq(uint(controller.errorIntegral()), 0);

        hevm.warp(now + updateDelay);

        int256 error = relative_error(0.95E18, TWENTY_SEVEN_DECIMAL_NUMBER);
        (int output, int pOutput, int iOutput) =
          controller.getNextPiOutput(error);
        assertEq(output, Kp * error/1E18);
        assertEq(pOutput, Kp * error/1E18);
        assertEq(iOutput, 0);

        (output, pOutput, iOutput) = controller.update(error);
        assertEq(output, Kp * error/1E18);
        assertEq(pOutput, Kp * error/1E18);
        assertEq(iOutput, 0);

        assertEq(uint(controller.lastUpdateTime()), now);
        assertEq(controller.errorIntegral(), 0);
        assertEq(controller.lastError(), 0.05E27);
    }
    function test_integral_leaks() public {
        controller.modifyParameters("perSecondIntegralLeak", uint(0.999999999E27));

        // First update
        // Need to update twice since first update doesn't create an error integral
        // as elapsed time is 0
        hevm.warp(now + updateDelay);
        (int output, int pOutput, int iOutput) = controller.update(-0.0001E27);
        hevm.warp(now + updateDelay);
        (output, pOutput, iOutput) = controller.update(-0.0001E27);
        int errorIntegral1 = controller.errorIntegral();
        assert(errorIntegral1 < 0);

        hevm.warp(now + updateDelay);

        // Second update
        (output, pOutput, iOutput) = controller.update(0);
        int errorIntegral2 = controller.errorIntegral();
        assert(errorIntegral2 > errorIntegral1);

    }
    function test_leak_sets_integral_to_zero() public {
        assertEq(uint(controller.errorIntegral()), 0);

        controller.modifyParameters("kp", int(1000));
        controller.modifyParameters("perSecondIntegralLeak", uint(998721603904830360273103599)); // -99% per hour
        //controller.modifyParameters("perSecondIntegralLeak", uint(0.95E27)); // -99% per hour

        // First update
        hevm.warp(now + updateDelay);
        (int output, int pOutput, int iOutput) = controller.update(-0.0001E27);
        //assert(controller.errorIntegral() == 0);

        // Second update
        hevm.warp(now + updateDelay);
        (output, pOutput, iOutput) = controller.update(-0.0001E27);
        //assert(controller.errorIntegral() == 0);

        // Third update
        hevm.warp(now + updateDelay);
        (output, iOutput, pOutput) = controller.update(-0.0001E27);

        assert(controller.errorIntegral() < 0);

        // Final update
        hevm.warp(now + updateDelay * 100);

        int256 error = relative_error(1E18, 1E27);
        assertEq(error, 0);

        (output, pOutput, iOutput) =
          controller.getNextPiOutput(error);
        assertEq(pOutput, 0);

        (output, pOutput, iOutput) = controller.update(error);
        hevm.warp(now + updateDelay * 100);
        (output, pOutput, iOutput) = controller.update(error);
        assertEq(controller.errorIntegral(), 0);

    }
    function test_update_prate() public {
        controller.modifyParameters("seedProposer", address(this));
        controller.modifyParameters("kp", int(2.25E11));
        controller.modifyParameters("ki", int(0));
        hevm.warp(now + updateDelay);

        int256 error = relative_error(1.01E18, 1.00E27);
        assertEq(error, -0.01E27);
        (int256 output, int256 pOutput,) = controller.update(error);
        assertEq(output, error * int(2.25E11)/ int(EIGHTEEN_DECIMAL_NUMBER));
        assertEq(output, pOutput);
    }
    function test_get_next_error_integral() public {
        controller.modifyParameters("seedProposer", address(this));
        controller.modifyParameters("kp", int(2.25E11));
        controller.modifyParameters("ki", int(7.2E4));
        controller.modifyParameters("perSecondIntegralLeak", uint(1E27));
        hevm.warp(now + updateDelay);

        // First update doesn't create an integral or output contribution
        // as elapsed time is set to 0
        int256 error = relative_error(1.01E18, 1.00E27);
        (int256 newIntegral, int256 newArea) = controller.getNextErrorIntegral(error);
        assertEq(newIntegral, 0);
        assertEq(newArea, 0);
        controller.update(error);
        assertEq(controller.errorIntegral(), newIntegral);

        hevm.warp(now + updateDelay);

        // Second update
        error = relative_error(1.01E18, 1.00E27);
        (newIntegral, newArea) = controller.getNextErrorIntegral(error);
        controller.update(error);
        assertEq(newIntegral, error * int(updateDelay));
        assertEq(newArea, error * int(updateDelay));
        assertEq(controller.errorIntegral(), newIntegral);

        hevm.warp(now + updateDelay);

        // Third update
        error = relative_error(1.01E18, 1.00E27);
        (newIntegral, newArea) = controller.getNextErrorIntegral(error);
        assertEq(newArea, error * int(updateDelay));
        assertEq(newIntegral, error * int(updateDelay) * 2);
        controller.update(error);
        assertEq(controller.errorIntegral(), newIntegral);

    }
    function test_get_next_error_integral_leak() public {
        controller.modifyParameters("seedProposer", address(this));
        controller.modifyParameters("kp", int(2.25E11));
        controller.modifyParameters("ki", int(7.2E4));
        controller.modifyParameters("perSecondIntegralLeak", uint(0.95E27));
        hevm.warp(now + updateDelay);

        // First update doesn't create an integral or output contribution
        // as elapsed time is set to 0
        int256 error = relative_error(1.01E18, 1.00E27);
        (int256 newIntegral, int256 newArea) = controller.getNextErrorIntegral(error);
        assertEq(newIntegral, 0);
        assertEq(newArea, 0);
        controller.update(error);
        assertEq(controller.errorIntegral(), newIntegral);

        hevm.warp(now + updateDelay);

        // Second update
        int error2 = relative_error(1.01E18, 1.00E27);
        (int newIntegral2, int newArea2) = controller.getNextErrorIntegral(error2);
        assertEq(newIntegral2, error2 * int(updateDelay));
        assertEq(newArea2, error2 * int(updateDelay));

        controller.update(error2);
        assertEq(controller.errorIntegral(), newIntegral2);

        hevm.warp(now + updateDelay);

        // Third update
        int error3 = relative_error(1.00E18, 1.00E27);
        assertEq(error3, 0);
        (int newIntegral3, int newArea3) = controller.getNextErrorIntegral(error3);
        assertEq(newArea3, (error2 + error3)/2 * int(updateDelay));
        assert(newIntegral3 -newArea3 > newIntegral2);
        controller.update(error3);
        assertEq(controller.errorIntegral(), newIntegral3);

    }
    function test_update_integral() public {
        controller.modifyParameters("seedProposer", address(this));
        controller.modifyParameters("kp", int(2.25E11));
        controller.modifyParameters("ki", int(7.2E4));
        controller.modifyParameters("perSecondIntegralLeak", uint(1E27));
        hevm.warp(now + updateDelay);

        // First update doesn't create an integral contribution
        // as elapsed time is set to 0
        int256 error1 = relative_error(1.01E18, 1.00E27);
        assertEq(error1, -0.01E27);
        (int output1,,) = controller.update(error1);
        int256 errorIntegral1 = controller.errorIntegral();
        assertEq(output1, error1 * controller.kp()/ int(EIGHTEEN_DECIMAL_NUMBER));
        assertEq(errorIntegral1, 0);

        hevm.warp(now + updateDelay);

        // Second update
        int256 error2 = relative_error(1.01E18, 1.00E27);
        assertEq(error2, -0.01E27);
        (int output2,,) = controller.update(error2);
        int256 errorIntegral2 = controller.errorIntegral();
        assertEq(errorIntegral2, errorIntegral1 + (error1 + error2)/2 * int(updateDelay));
        assertEq(output2, error2 * controller.kp()/int(EIGHTEEN_DECIMAL_NUMBER) +
                 errorIntegral2 * controller.ki()/int(EIGHTEEN_DECIMAL_NUMBER));

        hevm.warp(now + updateDelay);

        // Third update
        int256 error3 = relative_error(1.01E18, 1.00E27);
        assertEq(error3, -0.01E27);
        (int output3,,) = controller.update(error3);
        int256 errorIntegral3 = controller.errorIntegral();
        assertEq(errorIntegral3, errorIntegral2 + (error2 + error3)/2 * int(updateDelay));
        assertEq(output3, error3 * controller.kp()/int(EIGHTEEN_DECIMAL_NUMBER) +
                 errorIntegral3 * controller.ki()/int(EIGHTEEN_DECIMAL_NUMBER));
    }
    function test_last_error() public {
        controller.modifyParameters("seedProposer", address(this));
        hevm.warp(now + updateDelay);
        assertEq(controller.lastError(), 0);

        int256 error = relative_error(1.01E18, 1.00E27);
        assertEq(error, -0.01E27);
        (int256 output, int256 pOutput, int256 iOutput) = controller.update(error);
        assertEq(controller.lastError(), error);

        hevm.warp(now + updateDelay);
        error = relative_error(1.02E18, 1.00E27);
        assertEq(error, -0.02E27);
        (output, pOutput, iOutput) = controller.update(error);
        assertEq(controller.lastError(), error);

        hevm.warp(now + updateDelay);
        error = relative_error(0.95E18, 1.00E27);
        assertEq(error, 0.05E27);
        (output, pOutput, iOutput) = controller.update(error);
        assertEq(controller.lastError(), error);

    }
    function test_last_error_integral() public {
        controller.modifyParameters("seedProposer", address(this));
        controller.modifyParameters("kp", int(2.25E11));
        controller.modifyParameters("ki", int(7.2E4));
        controller.modifyParameters("perSecondIntegralLeak", uint(1E27));
        assertEq(controller.errorIntegral(), 0);

        hevm.warp(now + updateDelay);

        int256 error = relative_error(1.01E18, 1.00E27);
        (int256 output, int256 pOutput, int256 iOutput) = controller.update(error);
        assertEq(controller.lastError(), error);
        assertEq(controller.errorIntegral(), 0);

        hevm.warp(now + updateDelay);

        error = relative_error(1.01E18, 1.00E27);
        (output, pOutput, iOutput) = controller.update(error);
        assertEq(controller.lastError(), error);
        assertEq(controller.errorIntegral(), error * int(updateDelay));

        hevm.warp(now + updateDelay);
        assertEq(controller.errorIntegral(), error * int(updateDelay));

        (output, pOutput, iOutput) = controller.update(error);
        assertEq(controller.lastError(), error);
        assertEq(controller.errorIntegral(), error * int(updateDelay) * 2);

        hevm.warp(now + updateDelay * 10);
        assertEq(controller.errorIntegral(), error * int(updateDelay) * 2);

        error = relative_error(1.01E18, 1.00E27);
        (output, pOutput, iOutput) = controller.update(error);
        assertEq(controller.errorIntegral(), error * int(updateDelay) * 12);

    }

    function test_elapsed() public {
        controller.modifyParameters("seedProposer", address(this));
        assertEq(controller.elapsed(), 0);

        hevm.warp(now + updateDelay);
        (int output, int pOutput, int iOutput) = controller.update(-0.01E27);
        assertEq(controller.lastUpdateTime(), now);

        hevm.warp(now + updateDelay * 2);
        assertEq(controller.elapsed(), updateDelay * 2);
        assertEq(controller.lastUpdateTime(), now - controller.elapsed());
        (output, pOutput, iOutput) = controller.update(-0.01E27);
        assertEq(controller.lastUpdateTime(), now);

        hevm.warp(now + updateDelay * 10);
        assertEq(controller.elapsed(), updateDelay * 10);
        assertEq(controller.lastUpdateTime(), now - controller.elapsed());
        (output, pOutput, iOutput) = controller.update(-0.01E27);
        assertEq(controller.lastUpdateTime(), now);

    }
    function test_lower_clamping() public {
        controller.modifyParameters("seedProposer", address(this));
        controller.modifyParameters("kp", int(2.25E11));
        controller.modifyParameters("ki", int(7.2E4));
        controller.modifyParameters("perSecondIntegralLeak", uint(1E27));
        assertEq(uint(controller.errorIntegral()), 0);
        hevm.warp(now + updateDelay);

        int256 error = relative_error(1.01E18, 1.00E27);

        assertEq(error, -0.01E27);

        // First error: small, output doesn't hit lower bound
        (int256 output,,) = controller.update(error);
        assert(output < 0);
        assert(output > controller.outputLowerBound());
        // Integral is zero for first error
        assertEq(controller.errorIntegral(), 0);

        hevm.warp(now + updateDelay);

        (int leakedIntegral, int newArea) =
          controller.getNextErrorIntegral(error);
        assertEq(leakedIntegral, -36000000000000000000000000000);
        assertEq(newArea, -36000000000000000000000000000);

        // Second error: small, output doesn't hit lower bound
        (int output2,,) = controller.update(error);
        assert(output2 < output);
        assert(output2 > controller.outputLowerBound());
        assertEq(controller.errorIntegral(), -36000000000000000000000000000);

        hevm.warp(now + updateDelay);

        // Third error: very large. Output hits lower bound
        // Integral *does not* accumulate when it hits bound with same sign of current integral
        int256 hugeNegError = relative_error(1.6E18, 1.00E27);

        (int output3,,) = controller.update(hugeNegError);
        assertEq(output3, controller.outputLowerBound());
        // Integral doesn't accumulate
        assertEq(controller.errorIntegral(), -36000000000000000000000000000);

        hevm.warp(now + updateDelay);

        // Integral *does* accumulate with a smaller error(doesn't hit output bound)
        int256 smallNegError = relative_error(1.01E18, 1.00E27);

        (int output4,,) = controller.update(smallNegError);
        assert(controller.errorIntegral() < -36000000000000000000000000000);
        //assertEq(controller.errorIntegral(), -36000000000000000000000000000);
        assert(output4 > controller.outputLowerBound());

    }
    function test_upper_clamping() public {
        controller.modifyParameters("seedProposer", address(this));
        controller.modifyParameters("kp", int(2.25E11));
        controller.modifyParameters("ki", int(7.2E4));
        controller.modifyParameters("outputUpperBound", int(0.00000001E27));
        controller.modifyParameters("perSecondIntegralLeak", uint(1E27));
        assertEq(uint(controller.errorIntegral()), 0);

        hevm.warp(now + updateDelay);


        int256 error = relative_error(0.999999E18, 1.00E27);

        assertEq(error, 0.000001E27);

        (int256 output,,) = controller.update(error);
        assert(output > 0);
        assert(output < controller.outputUpperBound());
        assertEq(controller.errorIntegral(), 0);

        hevm.warp(now + updateDelay);
        (int leakedIntegral, int newArea) =
          controller.getNextErrorIntegral(error);
        assertEq(leakedIntegral, error * int(updateDelay));
        assertEq(newArea, error * int(updateDelay));

        (int output2,,) = controller.update(error);
        assert(output2 > output);
        assertEq(controller.errorIntegral(), int(updateDelay) * error);

        // Integral *does not* accumulate when it hits bound with same sign of current integral
        int256 hugeNegError = relative_error(1, 1.00E27);

        hevm.warp(now + updateDelay);
        (int output3,,) = controller.update(hugeNegError);
        assertEq(output3, controller.outputUpperBound());
        assertEq(controller.errorIntegral(), int(updateDelay) * error);

        // Integral *does* accumulate with a smaller error(doesn't hit output bound)
        int256 smallPosError = relative_error(0.999999E18, 1.00E27);

        hevm.warp(now + updateDelay);
        (int output4,,) = controller.update(smallPosError);
        assert(output4 < controller.outputUpperBound());
        //assert(controller.errorIntegral() > int(updateDelay) * error);

    }
    function test_lower_bound_limit() public {
        hevm.warp(now + updateDelay);

        int256 error = relative_error(1.05E18, 1);
        (int output, int pOutput, int iOutput) =
          controller.getNextPiOutput(error);

        assertEq(output, controller.outputLowerBound());

        (output, pOutput, iOutput) =
         controller.update(error);

        assertEq(output, controller.outputLowerBound());

    }
    function test_upper_bound_limit() public {
        controller.modifyParameters("kp", int(100000000000000000000e18));
        hevm.warp(now + updateDelay);

        int256 error = relative_error(1, 1E27);
        //assertEq(error, 0);
        (int output, int pOutput, int iOutput) =
          controller.getNextPiOutput(error);
        //assertEq(output, 0);

        assertEq(output, controller.outputUpperBound());

        (output, pOutput, iOutput) =
         controller.update(error);

        assertEq(output, controller.outputUpperBound());

    }
    function test_raw_output_proportional_calculation() public {

        int256 error = relative_error(1E18, 1E27);
        (int output, int pOutput, int iOutput) =
          controller.getRawPiOutput(error, 0);
        assertEq(output, Kp * error/1e18);
        assertEq(pOutput, Kp * error/1e18);
        assertEq(iOutput, 0);

        error = relative_error(1.05E18, 1E27);
        (output, pOutput, iOutput) =
          controller.getRawPiOutput(error, 0);
        assertEq(output, Kp * error/1e18);
        assertEq(pOutput, Kp * error/1e18);
        assertEq(iOutput, 0);

    }
    function test_bounded_output_proportional_calculation() public {
        // zero error, no bound
        int256 error = relative_error(1.05E18, 1E27);
        (int output, int pOutput, int iOutput) =
          controller.getRawPiOutput(error, 0);

        int boundedOutput = controller.boundPiOutput(output);

        assertEq(output, Kp * error/1e18);
        assertEq(pOutput, Kp * error/1e18);
        assertEq(iOutput, 0);
        assertEq(boundedOutput, Kp * error/1e18);

        // large negative error, hits lower bound
        error = relative_error(1.5E18, 1E27);
        (output, pOutput, iOutput) =
          controller.getRawPiOutput(error, 0);

        boundedOutput = controller.boundPiOutput(output);

        assertEq(output, Kp * error/1e18);
        assertEq(pOutput, Kp * error/1e18);
        assertEq(iOutput, 0);
        assertEq(boundedOutput, outputLowerBound);

        // large positive error, hits upper bound
        error = relative_error(0.5E18, 1E27);
        (output, pOutput, iOutput) =
          controller.getRawPiOutput(error, 0);

        boundedOutput = controller.boundPiOutput(output);

        assertEq(output, Kp * error/1e18);
        assertEq(pOutput, Kp * error/1e18);
        assertEq(iOutput, 0);
        assertEq(boundedOutput, outputUpperBound);
    }

    function test_both_gains_zero() public {
        controller.modifyParameters("kp", int(0));
        controller.modifyParameters("ki", int(0));

        assertEq(uint(controller.errorIntegral()), 0);

        int256 error = relative_error(1.05E18, 1.00E27);
        assertEq(error, -0.05E27);

        (int piOutput, int pOutput,) =
          controller.getNextPiOutput(error);
        assertEq(piOutput, 0);
        assertEq(pOutput, 0);
        assertEq(controller.errorIntegral(), 0);

    }
}
"""
