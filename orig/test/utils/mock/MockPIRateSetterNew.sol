pragma solidity 0.6.7;
// For use with PIController
import "../RateSetterMath.sol";

abstract contract OracleLike {
    function getResultWithValidity() virtual external view returns (uint256, bool);
}
abstract contract OracleRelayerLike {
    function redemptionPrice() virtual external returns (uint256);
}
abstract contract SetterRelayer {
    function relayRate(uint256) virtual external;
}
abstract contract Controller {
    function update(int256) virtual external returns (int256);
    function getNextOutput(int256) virtual external view returns (int256);
    function elapsed() virtual external view returns (uint256);
}

contract MockPIRateSetter is RateSetterMath {
    // --- System Dependencies ---
    // OSM or medianizer for the system coin
    OracleLike                public orcl;
    // OracleRelayer where the redemption price is stored
    OracleRelayerLike         public oracleRelayer;
    // The contract that will pass the new redemption rate to the oracle relayer
    SetterRelayer             public setterRelayer;
    // Controller for the redemption rate
    Controller              public controller;

    // The default redemption rate to calculate in case pi output is smaller than noiseBarrier
    uint256 internal defaultRedemptionRate;          // [TWENTY_SEVEN_DECIMAL_NUMBER]

    // The minimum absolute value of the per-second rate in which the contract will produce a non null redemption rate
    uint256 internal noiseBarrier;                   // [EIGHTEEN_DECIMAL_NUMBER]

    // Flag indicating that the rate computed is per second
    uint256 constant internal defaultGlobalTimeline = 1;

    uint256 internal constant NEGATIVE_RATE_LIMIT         = TWENTY_SEVEN_DECIMAL_NUMBER - 1;
    uint256 internal constant EIGHTEEN_DECIMAL_NUMBER = 10 ** 18;
    uint256 internal constant TWENTY_SEVEN_DECIMAL_NUMBER = 10 ** 27;

    constructor(address orcl_, address oracleRelayer_, address controller_, address setterRelayer_) public {
        defaultRedemptionRate           = TWENTY_SEVEN_DECIMAL_NUMBER;
        oracleRelayer  = OracleRelayerLike(oracleRelayer_);
        orcl           = OracleLike(orcl_);
        setterRelayer  = SetterRelayer(setterRelayer_);
        controller  = Controller(controller_);
    }

    // --- Boolean Logic ---
    function both(bool x, bool y) internal pure returns (bool z) {
        assembly{ z := and(x, y)}
    }
    function either(bool x, bool y) internal pure returns (bool z) {
        assembly{ z := or(x, y)}
    }

    function absolute(int x) internal pure returns (uint z) {
        z = (x < 0) ? uint(-x) : uint(x);
    }

    function modifyParameters(bytes32 parameter, address addr) external {
        if (parameter == "orcl") orcl = OracleLike(addr);
        else if (parameter == "oracleRelayer") oracleRelayer = OracleRelayerLike(addr);
        else if (parameter == "setterRelayer") setterRelayer = SetterRelayer(addr);
        else if (parameter == "controller") {
          controller = Controller(addr);
        }
        else revert("RateSetter/modify-unrecognized-param");
    }

    function modifyParameters(bytes32 parameter, uint256 val) external {
        if (parameter == "nb") {
          require(both(val >= 0, val <= EIGHTEEN_DECIMAL_NUMBER), "MockPIRateSetter/invalid-nb");
          noiseBarrier = val;
        }
    }

    function updateRate(address feeReceiver) public {
        // Get price feed updates
        (uint256 marketPrice, bool hasValidValue) = orcl.getResultWithValidity();
        // If the oracle has a value
        require(hasValidValue, "MockPIRateSetter/invalid-oracle-value");
        // If the price is non-zero
        require(marketPrice > 0, "MockPIRateSetter/null-market-price");
        // Get the latest redemption price
        uint redemptionPrice = oracleRelayer.redemptionPrice();

        uint256 scaledMarketPrice = multiply(marketPrice, 10**9);
        // Calculate the error as (redemptionPrice - marketPrice) * TWENTY_SEVEN_DECIMAL_NUMBER / redemptionPrice
        int256 error = multiply(subtract(int(redemptionPrice), int(scaledMarketPrice)), int(TWENTY_SEVEN_DECIMAL_NUMBER)) / int(redemptionPrice);

        int256 controllerOutput = controller.update(
            error
        );


        uint newRedemptionRate;

        if (
          breaksNoiseBarrier(controllerOutput) &&
          controllerOutput != 0
        ) {
          newRedemptionRate = getBoundedRedemptionRate(controllerOutput);
        } else {
          newRedemptionRate = TWENTY_SEVEN_DECIMAL_NUMBER;
        }

        // Update the rate using the setter relayer
        try setterRelayer.relayRate(newRedemptionRate) {}
        catch(bytes memory revertReason) {}
    }

    function breaksNoiseBarrier(int controllerOutput) public view returns (bool) {
        return absolute(controllerOutput) > noiseBarrier;
    }

    function getBoundedRedemptionRate(int controllerOutput) public view returns (uint256) {
        uint newRedemptionRate;

        // newRedemptionRate cannot be lower than 10^0 (1) because of the way rpower is designed
        bool negativeOutputExceedsHundred = (controllerOutput < 0 && -controllerOutput >= int(defaultRedemptionRate));

        // If it is smaller than 1, set it to the nagative rate limit
        if (negativeOutputExceedsHundred) {
          newRedemptionRate = NEGATIVE_RATE_LIMIT;
        } else {
          // If boundedPIOutput is lower than -int(NEGATIVE_RATE_LIMIT) set newRedemptionRate to 1
          if (controllerOutput < 0 && controllerOutput <= -int(NEGATIVE_RATE_LIMIT)) {
            newRedemptionRate = uint(addition(int(defaultRedemptionRate), -int(NEGATIVE_RATE_LIMIT)));
          } else {
            // Otherwise add defaultRedemptionRate and boundedPIOutput together
            newRedemptionRate = uint(addition(int(defaultRedemptionRate), controllerOutput));
          }
        }

        return newRedemptionRate;
    }
    function getNextRedemptionRate(uint marketPrice, uint redemptionPrice)
      public view returns (uint256, int256, uint256) {
        uint256 scaledMarketPrice = multiply(marketPrice, 10**9);
        int256 error = multiply(subtract(int(redemptionPrice), int(scaledMarketPrice)), int(TWENTY_SEVEN_DECIMAL_NUMBER)) / int(redemptionPrice);

        int controllerOutput = controller.getNextOutput(error);

        if (
          breaksNoiseBarrier(controllerOutput) &&
          controllerOutput != 0
        ) {
          uint newRedemptionRate = getBoundedRedemptionRate(controllerOutput);
          return (newRedemptionRate, error, defaultGlobalTimeline);
        } else {
          return (TWENTY_SEVEN_DECIMAL_NUMBER, error, defaultGlobalTimeline);
        }
    }

}
