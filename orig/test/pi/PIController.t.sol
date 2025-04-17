pragma solidity ^0.6.7;

import "ds-test/test.sol";

import {PIController} from '../../src/PIController.sol';

abstract contract Hevm {
    function warp(uint256) virtual public;
}

contract PIControllerTest is DSTest {
    Hevm hevm;

    PIController controller;

    uint256 updateDelay = 3600;

    int256 Kp                                 = 222002205862;
    int256 Ki                                 = int(EIGHTEEN_DECIMAL_NUMBER);
    int256 coBias                             = 0; 
    uint256 baseUpdateCallerReward            = 10 ether;
    uint256 maxUpdateCallerReward             = 30 ether;
    uint256 perSecondCallerRewardIncrease     = 1000002763984612345119745925;
    uint256 perSecondIntegralLeak           = 999997208243937652252849536; // 1% per hour
    int256 outputUpperBound          = 18640000000000000000;
    int256 outputLowerBound          = -51034000000000000000;

    int256[] importedState = new int[](5);
    address self;

    function setUp() public {
      hevm = Hevm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);
      hevm.warp(604411200);

      controller = new PIController(
        'test control variable',
        Kp,
        Ki,
        coBias,
        perSecondIntegralLeak,
        outputUpperBound,
        outputLowerBound,
        importedState
      );

      controller.modifyParameters("seedProposer", address(this));
      self = address(this);
    }

    // --- Math ---
    uint constant FORTY_FIVE_DECIMAL_NUMBER   = 10 ** 45;
    uint constant TWENTY_SEVEN_DECIMAL_NUMBER = 10 ** 27;
    uint constant EIGHTEEN_DECIMAL_NUMBER     = 10 ** 18;

    function rpower(uint x, uint n, uint base) internal pure returns (uint z) {
        assembly {
            switch x case 0 {switch n case 0 {z := base} default {z := 0}}
            default {
                switch mod(n, 2) case 0 { z := base } default { z := x }
                let half := div(base, 2)  // for rounding.
                for { n := div(n, 2) } n { n := div(n,2) } {
                    let xx := mul(x, x)
                    if iszero(eq(div(xx, x), x)) { revert(0,0) }
                    let xxRound := add(xx, half)
                    if lt(xxRound, xx) { revert(0,0) }
                    x := div(xxRound, base)
                    if mod(n,2) {
                        let zx := mul(z, x)
                        if and(iszero(iszero(x)), iszero(eq(div(zx, x), z))) { revert(0,0) }
                        let zxRound := add(zx, half)
                        if lt(zxRound, zx) { revert(0,0) }
                        z := div(zxRound, base)
                    }
                }
            }
        }
    }
    function multiply(uint x, uint y) internal pure returns (uint z) {
        require(y == 0 || (z = x * y) / y == x);
    }
    function wmultiply(uint x, uint y) internal pure returns (uint z) {
        z = multiply(x, y) / EIGHTEEN_DECIMAL_NUMBER;
    }
    function rmultiply(uint x, uint y) internal pure returns (uint z) {
        z = multiply(x, y) / TWENTY_SEVEN_DECIMAL_NUMBER;
    }
    function rdivide(uint x, uint y) internal pure returns (uint z) {
        z = multiply(x, TWENTY_SEVEN_DECIMAL_NUMBER) / y;
    }
    function subtract(int256 a, int256 b) internal pure returns (int256) {
        int256 c = a - b;
        require((b >= 0 && c <= a) || (b < 0 && c > a), "SignedSafeMath: subtraction overflow");
        return c;
    }

    int256 constant private _INT256_MIN = -2**255;
    function multiply(int256 a, int256 b) internal pure returns (int256) {
        // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
        // benefit is lost if 'b' is also tested.
        // See: https://github.com/OpenZeppelin/openzeppelin-contracts/pull/522
        if (a == 0) {
            return 0;
        }

        require(!(a == -1 && b == _INT256_MIN), "SignedSafeMath: multiplication overflow");

        int256 c = a * b;
        require(c / a == b, "SignedSafeMath: multiplication overflow");

        return c;
    }

    function relative_error(uint256 measuredValue, uint256 referenceValue) internal pure returns (int256) {
        // measuredValue is WAD, referenceValue is a RAY
        // Logic from rate setter

        uint256 scaledMeasuredValue = multiply(measuredValue, 10**9);
        int256 relativeError = multiply(subtract(int(referenceValue), int(scaledMeasuredValue)), int(TWENTY_SEVEN_DECIMAL_NUMBER)) / int(referenceValue);
        return relativeError;
    }

    function test_correct_setup() public {
        assertEq(controller.authorities(address(this)), 1);
        assertEq(controller.outputUpperBound(), outputUpperBound);
        assertEq(controller.outputLowerBound(), outputLowerBound);
        assertEq(controller.lastUpdateTime(), 0);
        assertEq(controller.errorIntegral(), 0);
        assertEq(controller.perSecondIntegralLeak(), perSecondIntegralLeak);
        assertEq(controller.controlVariable(), 'test control variable');
        assertEq(Kp, controller.kp());
        assertEq(Ki, controller.ki());
        assertEq(controller.elapsed(), 0);
    }
    function test_modify_parameters() public {
        controller.modifyParameters("kp", int(1));
        controller.modifyParameters("ki", int(1));
        assertEq(int(1), controller.ki());
        assertEq(int(1), controller.kp());

        controller.modifyParameters("outputUpperBound", int(TWENTY_SEVEN_DECIMAL_NUMBER + 1));
        controller.modifyParameters("outputLowerBound", -int(1));
        assertEq(controller.outputUpperBound(), int(TWENTY_SEVEN_DECIMAL_NUMBER + 1));
        assertEq(controller.outputLowerBound(), -int(1));

        controller.modifyParameters("perSecondIntegralLeak", uint(TWENTY_SEVEN_DECIMAL_NUMBER - 5));
        assertEq(controller.perSecondIntegralLeak(), TWENTY_SEVEN_DECIMAL_NUMBER - 5);

    }
    function testFail_modify_parameters_upper_bound() public {
        controller.modifyParameters("outputUpperBound", controller.outputLowerBound() - 1);
    }
    function testFail_modify_parameters_lower_bound() public {
        controller.modifyParameters("outputLowerBound", controller.outputUpperBound() + 1);
    }
    function test_get_next_output_zero_error() public {
        int256 error = relative_error(EIGHTEEN_DECIMAL_NUMBER, TWENTY_SEVEN_DECIMAL_NUMBER);
        (int piOutput,,) =
          controller.getNextPiOutput(error);
        assertEq(piOutput, 0);
        assertEq(controller.errorIntegral(), 0);

        // Verify that it did not change state
        assertEq(controller.authorities(address(this)), 1);

        assertEq(controller.outputUpperBound(), outputUpperBound);
        assertEq(controller.outputLowerBound(), outputLowerBound);
        assertEq(controller.lastUpdateTime(), 0);
        assertEq(controller.errorIntegral(), 0);
        assertEq(controller.lastError(), 0);
        assertEq(controller.perSecondIntegralLeak(), perSecondIntegralLeak);
        assertEq(Kp, controller.kp());
        assertEq(Ki, controller.ki());
        assertEq(controller.elapsed(), 0);
    }
    function test_get_next_output_nonzero_error() public {
        (int piOutput,,) =
          controller.getNextPiOutput(1);
        assertEq(piOutput, Kp * 1/1E18);
        assertEq(controller.errorIntegral(), 0);

        // Verify that it did not change state
        assertEq(controller.authorities(address(this)), 1);

        assertEq(controller.outputUpperBound(), outputUpperBound);
        assertEq(controller.outputLowerBound(), outputLowerBound);
        assertEq(controller.lastUpdateTime(), 0);
        assertEq(controller.errorIntegral(), 0);
        assertEq(controller.lastError(), 0);
        assertEq(controller.perSecondIntegralLeak(), perSecondIntegralLeak);
        assertEq(Kp, controller.kp());
        assertEq(Ki, controller.ki());
        assertEq(controller.elapsed(), 0);
    }
    function test_first_update() public {
        hevm.warp(now + updateDelay + 1);

        controller.update(1);
        assertEq(uint(controller.lastUpdateTime()), now);
        assertEq(uint(controller.lastError()), 1);
        assertEq(uint(controller.errorIntegral()), 0);

    }
    function test_first_update_zero_error() public {
        hevm.warp(now + updateDelay + 1);

        controller.update(0);
        assertEq(uint(controller.lastUpdateTime()), now);
        assertEq(uint(controller.lastError()), 0);
        assertEq(uint(controller.errorIntegral()), 0);

    }
    function testFail_update_same_period_warp() public {
        hevm.warp(now + updateDelay + 1);
        controller.update(0);
        controller.update(0);
    }

    function testFail_update_same_period_no_warp() public {
        controller.update(0);
        controller.update(0);
    }
    function test_zero_integral_persists() public {
        assertEq(controller.errorIntegral(), 0);
        hevm.warp(now + updateDelay);
        assertEq(controller.errorIntegral(), 0);
    }
    function test_nonzero_integral_persists() public {
        hevm.warp(now + updateDelay);
        controller.update(1);
        int initialErrorIntegral = controller.errorIntegral();

        hevm.warp(now + updateDelay);
        assertEq(initialErrorIntegral, controller.errorIntegral());

    }
    function test_first_get_next_output() public {
        // negative error
        int256 error = relative_error(1.01E18, TWENTY_SEVEN_DECIMAL_NUMBER);
        (int piOutput, int pOutput, int iOutput) =
          controller.getNextPiOutput(error);
        assertEq(piOutput, Kp * error/1E18);
        assertEq(controller.errorIntegral(), 0);

        // positive error
        error = relative_error(0.995E18, TWENTY_SEVEN_DECIMAL_NUMBER);
        (piOutput, pOutput, iOutput) =
          controller.getNextPiOutput(error);
        assertEq(piOutput, Kp * 0.005E27/1E18);
        assertEq(controller.errorIntegral(), 0);
    }
    function test_first_get_next_output_with_bias() public {
        int256 bias = 30000;
        controller.modifyParameters("coBias", bias);

        // negative error
        int256 error = relative_error(1.01E18, TWENTY_SEVEN_DECIMAL_NUMBER);
        (int piOutput, int pOutput, int iOutput) =
          controller.getNextPiOutput(error);
        assertEq(piOutput, bias + Kp * error/1E18);
        assertEq(controller.errorIntegral(), 0);

        // positive error
        error = relative_error(0.995E18, TWENTY_SEVEN_DECIMAL_NUMBER);
        (piOutput, pOutput, iOutput) =
          controller.getNextPiOutput(error);
        assertEq(piOutput, bias + Kp * 0.005E27/1E18);
        assertEq(controller.errorIntegral(), 0);

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
