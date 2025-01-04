/// PIController.sol

pragma solidity 0.6.7;

import "src/SafeMath.sol";
import "src/SignedSafeMath.sol";
import "src/GebMath.sol";

contract PIController is SafeMath, SignedSafeMath {
    // --- Authorities ---
    mapping (address => uint) public authorities;
    function addAuthority(address account) external isAuthority { authorities[account] = 1; }
    function removeAuthority(address account) external isAuthority { authorities[account] = 0; }
    modifier isAuthority {
        require(authorities[msg.sender] == 1, "PIController/not-an-authority");
        _;
    }

    // What variable the controller is intended to control
    bytes32 public controlVariable;
    // This value is multiplied with the error
    int256 public kp;                                      // [EIGHTEEN_DECIMAL_NUMBER]
    // This value is multiplied with errorIntegral
    int256 public ki;                                      // [EIGHTEEN_DECIMAL_NUMBER]

    // Controller output bias
    int256 public coBias;                                  // [TWENTY_SEVEN_DECIMAL_NUMBER]

    // The maximum output value
    int256 public outputUpperBound;       // [TWENTY_SEVEN_DECIMAL_NUMBER]
    // The minimum output value
    int256 public outputLowerBound;       // [TWENTY_SEVEN_DECIMAL_NUMBER]

    // The integral term (sum of error at each update call minus the leak applied at every call)
    int256 public errorIntegral;             // [TWENTY_SEVEN_DECIMAL_NUMBER]
    // The last error 
    int256 public lastError;             // [TWENTY_SEVEN_DECIMAL_NUMBER]
    // The per second leak applied to errorIntegral before the latest error is added
    uint256 public perSecondIntegralLeak;              // [TWENTY_SEVEN_DECIMAL_NUMBER]
    // Timestamp of the last update
    uint256 public lastUpdateTime;                       // [timestamp]

    // Address that can update controller
    address public seedProposer;

    uint256 internal constant TWENTY_SEVEN_DECIMAL_NUMBER = 10 ** 27;
    uint256 internal constant EIGHTEEN_DECIMAL_NUMBER     = 10 ** 18;
    uint256 public constant RAY = 10 ** 27;

    constructor(
        bytes32 controlVariable_,
        int256 kp_,
        int256 ki_,
        int256 coBias_,
        uint256 perSecondIntegralLeak_,
        int256 outputUpperBound_,
        int256 outputLowerBound_,
        int256[] memory importedState // lastUpdateTime, lastError, errorIntegral
    ) public {

        require(outputUpperBound_ >= outputLowerBound_, "PIController/invalid-bounds");
        require(uint(importedState[0]) <= now, "PIController/invalid-imported-time");

        authorities[msg.sender]         = 1;

        controlVariable = controlVariable_;
        kp = kp_;
        ki = ki_;
        coBias = coBias_;
        perSecondIntegralLeak = perSecondIntegralLeak_;
        outputUpperBound = outputUpperBound_;
        outputLowerBound = outputLowerBound_;
        lastUpdateTime = uint(importedState[0]);
        lastError = importedState[1];
        errorIntegral = importedState[2];

    }

    // --- Boolean Logic ---
    function both(bool x, bool y) internal pure returns (bool z) {
        assembly{ z := and(x, y)}
    }
    function either(bool x, bool y) internal pure returns (bool z) {
        assembly{ z := or(x, y)}
    }

    int256 constant private _INT256_MIN = -2**255;

    function rpower(uint x, uint n, uint base) public pure returns (uint z) {
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

    // --- Administration ---
    /*
    * @notify Modify an address parameter
    * @param parameter The name of the address parameter to change
    * @param addr The new address for the parameter
    */
    function modifyParameters(bytes32 parameter, address addr) external isAuthority {
        if (parameter == "seedProposer") {
          seedProposer = addr;
        }
        else revert("PIController/modify-unrecognized-param");
    }
    /*
    * @notify Modify an uint256 parameter
    * @param parameter The name of the parameter to change
    * @param val The new value for the parameter
    */
    function modifyParameters(bytes32 parameter, uint256 val) external isAuthority {
        if (parameter == "perSecondIntegralLeak") {
          require(val <= TWENTY_SEVEN_DECIMAL_NUMBER, "PIController/invalid-perSecondIntegralLeak");
          perSecondIntegralLeak = val;
        }
        else revert("PIController/modify-unrecognized-param");
    }
    /*
    * @notify Modify an int256 parameter
    * @param parameter The name of the parameter to change
    * @param val The new value for the parameter
    */
    function modifyParameters(bytes32 parameter, int256 val) external isAuthority {
        if (parameter == "outputUpperBound") {
          require(val > outputLowerBound, "PIController/invalid-outputUpperBound");
          outputUpperBound = val;
        }
        else if (parameter == "outputLowerBound") {
          require(val < outputUpperBound, "PIController/invalid-outputLowerBound");
          outputLowerBound = val;
        }
        else if (parameter == "kp") {
          kp = val;
        }
        else if (parameter == "ki") {
          ki = val;
        }
        else if (parameter == "coBias") {
          coBias = val;
        }
        else if (parameter == "errorIntegral") {
          errorIntegral = val;
        }
        else revert("PIController/modify-unrecognized-param");
    }

    // --- PI Specific Math ---
    function riemannSum(int x, int y) public pure returns (int z) {
        return addition(x, y) / 2;
    }
    function absolute(int x) internal pure returns (uint z) {
        z = (x < 0) ? uint(-x) : uint(x);
    }

    /*
    * @notice Return bounded controller output
    * @param piOutput The raw output computed from the error and integral terms
    */
    function boundPiOutput(int piOutput) public  view returns (int256) {
        int boundedPIOutput = piOutput;

        if (piOutput < outputLowerBound) {
          boundedPIOutput = outputLowerBound;
        } else if (piOutput > outputUpperBound) {
          boundedPIOutput = outputUpperBound;
        }

        return boundedPIOutput;

    }
    /*
    * @notice If output has reached a bound, undo integral accumulation
    * @param boundedPiOutput The bounded output computed from the error and integral terms
    * @param newErrorIntegral The updated errorIntegral, including the new area
    * @param newArea The new area that was already added to the integral that will subtracted if output has reached a bound
    */
    function clampErrorIntegral(int boundedPiOutput, int newErrorIntegral, int newArea) internal view returns (int256) {
        int clampedErrorIntegral = newErrorIntegral;

        if (both(both(boundedPiOutput == outputLowerBound, newArea < 0), errorIntegral < 0)) {
          clampedErrorIntegral = subtract(clampedErrorIntegral, newArea);
        } else if (both(both(boundedPiOutput == outputUpperBound, newArea > 0), errorIntegral > 0)) {
          clampedErrorIntegral = subtract(clampedErrorIntegral, newArea);
        }

        return clampedErrorIntegral;
    }

    /*
    * @notice Compute a new error Integral
    * @param error The system error
    */
    function getNextErrorIntegral(int error) public view returns (int256, int256) {
        uint256 elapsed = (lastUpdateTime == 0) ? 0 : subtract(now, lastUpdateTime);
        int256 newTimeAdjustedError = multiply(riemannSum(error, lastError), int(elapsed));

        uint256 accumulatedLeak = (perSecondIntegralLeak == 1E27) ? RAY : rpower(perSecondIntegralLeak, elapsed, RAY);
        int256 leakedErrorIntegral = divide(multiply(int(accumulatedLeak), errorIntegral), int(TWENTY_SEVEN_DECIMAL_NUMBER));

        return (addition(leakedErrorIntegral, newTimeAdjustedError), newTimeAdjustedError);
    }

    /*
    * @notice Apply Kp to the error and Ki to the error integral(by multiplication) and then sum P and I
    * @param error The system error TWENTY_SEVEN_DECIMAL_NUMBER
    * @param errorIntegral The calculated error integral TWENTY_SEVEN_DECIMAL_NUMBER
    * @return totalOutput, pOutput, iOutput TWENTY_SEVEN_DECIMAL_NUMBER
    */
    function getRawPiOutput(int error, int errorI) public  view returns (int256, int256, int256) {
        // output = P + I = Kp * error + Ki * errorI
        int pOutput = multiply(error, int(kp)) / int(EIGHTEEN_DECIMAL_NUMBER);
        int iOutput = multiply(errorI, int(ki)) / int(EIGHTEEN_DECIMAL_NUMBER);
        return (addition(coBias, addition(pOutput, iOutput)), pOutput, iOutput);
    }

    /*
    * @notice Process a new error and return controller output
    * @param error The system error TWENTY_SEVEN_DECIMAL_NUMBER
    */
    function update(int error) external returns (int256, int256, int256) {
        // Only the seed proposer can call this
        //require(seedProposer == msg.sender, "PIController/invalid-msg-sender");

        require(now > lastUpdateTime, "PIController/wait-longer");

        (int256 newErrorIntegral, int256 newArea) = getNextErrorIntegral(error);

        (int256 piOutput, int256 pOutput, int256 iOutput) = getRawPiOutput(error, newErrorIntegral);
        
        int256 boundedPiOutput = boundPiOutput(piOutput);

        // If output has reached a bound, undo integral accumulation
        errorIntegral = clampErrorIntegral(boundedPiOutput, newErrorIntegral, newArea);

        lastUpdateTime = now;
        lastError = error;

        return (boundedPiOutput, pOutput, iOutput);

    }
    /*
    * @notice Compute and return the output given an error
    * @param error The system error
    */
    function getNextPiOutput(int error) public view returns (int256, int256, int256) {
        (int newErrorIntegral,) = getNextErrorIntegral(error);
        (int piOutput, int pOutput, int iOutput) = getRawPiOutput(error, newErrorIntegral);
        int boundedPiOutput = boundPiOutput(piOutput);

        return (boundedPiOutput, pOutput, iOutput);

    }

    /*
    * @notice Returns the time elapsed since the last update call
    */
    function elapsed() external view returns (uint256) {
        return (lastUpdateTime == 0) ? 0 : subtract(now, lastUpdateTime);
    }
}
