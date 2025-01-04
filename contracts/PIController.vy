#pragma version >0.3.10

authorities: public(HashMap[address, uint256])


controlVariable: public(bytes32)
kp: public(int256)
ki: public(int256)
coBias: public(int256)
outputUpperBound: public(int256)
outputLowerBound: public(int256)
errorIntegral: public(int256)
lastError: public(int256)
perSecondIntegralLeak: public(uint256)
lastOutput: public(int256)
lastPOutput: public(int256)
lastIOutput: public(int256)
lastUpdateTime: public(uint256)

seedProposer: public(address)

TWENTY_SEVEN_DECIMAL_NUMBER: constant(uint256) = 10 ** 27
EIGHTEEN_DECIMAL_NUMBER: constant(int256) = 10**18
RAY: public(constant(uint256)) = 10 ** 27


@external
@view
def my_exp_uint256_external(x: uint256, n: uint256, b: uint256) -> uint256:  
    y: uint256 = n
    w: uint256 = x
    z: uint256 = 0
    
    if x == 0:
        if n == 0:
            z = b
            
    if n % 2 == 0:
        z = b
    else:
        z = x
    half: uint256 = b//2
    zx: uint256 = 0
    xxRound: uint256 = 0
    zxRound: uint256 = 0
    xx: uint256 = 0

    #1
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #2
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #3
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #4
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #5
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #6
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #7
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #8
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
        
    return z    
#
@internal
@view
def my_exp_uint256(x: uint256, n: uint256, b: uint256) -> uint256:  
    y: uint256 = n
    w: uint256 = x
    z: uint256 = 0
    
    if x == 0:
        if n == 0:
            z = b
            
    if n % 2 == 0:
        z = b
    else:
        z = x
    half: uint256 = b//2
    zx: uint256 = 0
    xxRound: uint256 = 0
    zxRound: uint256 = 0
    xx: uint256 = 0

    #1
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #2
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #3
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #4
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #5
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #6
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #7
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
    #8
    y = y//2
    xx = w * w
    if xx//w != w:
        raise "0,0"
    xxRound = xx + half
    if xxRound < xx:
        raise "0,0"
    w = xxRound//b
    if y % 2 > 0:
        zx = z * w
        if (w != 0 and (z*w)//w != z):
            raise "0,0"
        zxRound = zx + half
        if zxRound < zx:
            raise "0,0"
        z = zxRound //b
        
    return z                  


@internal
@view
def exp_uint256(a: uint256, b: uint256) -> uint256:
    #if a < 2 or b < 2:
    #    # Default to EVM in these special cases
    #    return a ** b  # dev: Vyper Would Revert

    x: uint256 = a
    n: uint256 = b
    y: uint256 = 1

    # NOTE: Do this at most 8 times... e.g. log_2(256)

    # 1/8
    if n % 2 == 0:
        x *= x  # dev: SafeMath Check
        n //= 2
    else:
        y *= x  # dev: SafeMath Check
        x *= x  # dev: SafeMath Check
        n -= 1
        n //= 2

    # 2/8
    if n <= 1:
        return x * y

    if n % 2 == 0:
        x *= x  # dev: SafeMath Check
        n //= 2
    else:
        y *= x  # dev: SafeMath Check
        x *= x  # dev: SafeMath Check
        n -= 1
        n //= 2

    # 3/8
    if n <= 1:
        return x * y

    if n % 2 == 0:
        x *= x  # dev: SafeMath Check
        n //= 2
    else:
        y *= x  # dev: SafeMath Check
        x *= x  # dev: SafeMath Check
        n -= 1
        n //= 2

    # 4/8
    if n <= 1:
        return x * y

    if n % 2 == 0:
        x *= x  # dev: SafeMath Check
        n //= 2
    else:
        y *= x  # dev: SafeMath Check
        x *= x  # dev: SafeMath Check
        n -= 1
        n //= 2

    # 5/8
    if n <= 1:
        return x * y
    if n % 2 == 0:
        x *= x  # dev: SafeMath Check
        n //= 2
    else:
        y *= x  # dev: SafeMath Check
        x *= x  # dev: SafeMath Check
        n -= 1
        n //= 2

    # 6/8
    if n <= 1:
        return x * y

    if n % 2 == 0:
        x *= x  # dev: SafeMath Check
        n //= 2
    else:
        y *= x  # dev: SafeMath Check
        x *= x  # dev: SafeMath Check
        n -= 1
        n //= 2

    # 7/8
    if n <= 1:
        return x * y

    if n % 2 == 0:
        x *= x  # dev: SafeMath Check
        n //= 2
    else:
        y *= x  # dev: SafeMath Check
        x *= x  # dev: SafeMath Check
        n -= 1
        n //= 2

    # 8/8
    if n <= 1:
        return x * y

    if n % 2 == 0:
        x *= x  # dev: SafeMath Check
        n //= 2
    else:
        y *= x  # dev: SafeMath Check
        x *= x  # dev: SafeMath Check
        n -= 1
        n //= 2

    assert n <= 1, UNREACHABLE  # dev: exceeded expected number of iterations

    return x * y  # dev: SafeMath Check
@deploy
def __init__(_controlVariable: bytes32, _kp: int256, _ki: int256, _coBias: int256, _perSecondIntegralLeak: uint256, _outputUpperBound: int256, _outputLowerBound: int256, importedState: int256[3]):
    #
    assert _outputUpperBound >= _outputLowerBound, "PIController/invalid-bounds"
    assert convert(importedState[0], uint256) <= block.timestamp, "PIController/invalid-imported-time"
    self.authorities[msg.sender] = 1
    self.controlVariable = _controlVariable
    self.kp = _kp
    self.ki = _ki
    self.coBias = _coBias
    self.perSecondIntegralLeak = _perSecondIntegralLeak
    self.outputUpperBound = _outputUpperBound
    self.outputLowerBound = _outputLowerBound
    self.lastUpdateTime = convert(importedState[0], uint256)
    self.lastError = importedState[1]
    self.errorIntegral = importedState[2]

@external
def addAuthority(account: address):
    self.authorities[account] = 1
    
@external
def removeAuthority(account: address):
    self.authorities[account] = 0

@external
def modifyParametersAddr(parameter: String[32], addr: address):
    #if (convert(parameter, String[32]) == "seedProposer"):
    if (parameter == "seedProposer"):
        self.seedProposer = addr
    else:
        raise "PIController/modify-unrecognized-param"

@external
def modifyParametersUint(parameter: String[32], val: uint256):
    if (parameter == "perSecondIntegralLeak"):
        assert val <= TWENTY_SEVEN_DECIMAL_NUMBER, "PIController/invalid-perSecondIntegralLeak"
        self.perSecondIntegralLeak = val
    else:
        raise "PIController/modify-unrecognized-param"

@external
def modifyParametersInt(parameter: String[32], val: int256):
    if (parameter == "outputUpperBound"):
        assert val > self.outputLowerBound, "PIController/invalid-outputUpperBound"
        self.outputUpperBound = val
    elif (parameter == "outputLowerBound"):
        assert val < self.outputUpperBound, "PIController/invalid-outputLowerBound"
        self.outputLowerBound = val
    elif (parameter == "kp"):
        self.kp = val
    elif (parameter == "ki"):
        self.ki = val
    elif (parameter == "coBias"):
        self.coBias = val
    elif (parameter == "errorIntegral"):
        self.errorIntegral = val
    else:
        raise "PIController/modify-unrecognized-param"

@internal
@view
def riemannSum(x: int256, y: int256)-> int256:
    #print(x, y, (x + y) // 2)
    return (x + y) // 2

@internal
@view
def boundPiOutput(piOutput: int256) -> int256:
    boundedPiOutput: int256 = piOutput
    if piOutput < self.outputLowerBound:
        boundedPiOutput = self.outputLowerBound
    elif piOutput > self.outputUpperBound:
        boundedPiOutput = self.outputUpperBound

    return boundedPiOutput


@internal
@view
def clampErrorIntegral(boundedPiOutput:int256, newErrorIntegral: int256, newArea: int256) -> int256:
    clampedErrorIntegral: int256 = newErrorIntegral
    if (boundedPiOutput == self.outputLowerBound and newArea < 0 and self.errorIntegral < 0):
        clampedErrorIntegral = clampedErrorIntegral - newArea
    elif (boundedPiOutput == self.outputUpperBound and newArea > 0 and self.errorIntegral > 0):
        clampedErrorIntegral = clampedErrorIntegral - newArea
    return clampedErrorIntegral

@internal
#@external
@view
def getNextErrorIntegral(error: int256) -> (int256, int256):
    elapsed: uint256 = 0 if (self.lastUpdateTime == 0) else block.timestamp - self.lastUpdateTime
    
    newTimeAdjustedError: int256 = self.riemannSum(error, self.lastError) * convert(elapsed, int256)
    #uint256 accumulatedLeak = (perSecondIntegralLeak == 1E27) ? RAY : rpower(perSecondIntegralLeak, elapsed, RAY);
    #accumulatedLeak: uint256 = RAY if self.perSecondIntegralLeak == convert(1E27, uint256) else (self.perSecondIntegralLeak//RAY) ** elapsed
    #accumulatedLeak: uint256 = RAY if self.perSecondIntegralLeak == convert(1E27, uint256) else pow_mod256(self.perSecondIntegralLeak, elapsed)//RAY

    accumulatedLeak: uint256 = RAY if self.perSecondIntegralLeak == convert(1E27, uint256) else self.my_exp_uint256(self.perSecondIntegralLeak, elapsed, RAY)

    #accumulatedLeak: uint256 = RAY
    leakedErrorIntegral: int256 = (convert(accumulatedLeak, int256) * self.errorIntegral) // convert(TWENTY_SEVEN_DECIMAL_NUMBER, int256)
    
    return (leakedErrorIntegral + newTimeAdjustedError, newTimeAdjustedError)

@external
@view
def getNextIntegral(error: int256) -> (int256, int256):
    elapsed: uint256 = 0 if (self.lastUpdateTime == 0) else block.timestamp - self.lastUpdateTime
    newTimeAdjustedError: int256 = self.riemannSum(error, self.lastError) * convert(elapsed, int256)
    #uint256 accumulatedLeak = (perSecondIntegralLeak == 1E27) ? RAY : rpower(perSecondIntegralLeak, elapsed, RAY);
    #accumulatedLeak: uint256 = RAY if self.perSecondIntegralLeak == convert(1E27, uint256) else (self.perSecondIntegralLeak//RAY) ** elapsed
    #accumulatedLeak: uint256 = RAY if self.perSecondIntegralLeak == convert(1E27, uint256) else pow_mod256(self.perSecondIntegralLeak//RAY, elapsed)

    accumulatedLeak: uint256 = RAY
    leakedErrorIntegral: int256 = (convert(accumulatedLeak, int256) * self.errorIntegral) // convert(TWENTY_SEVEN_DECIMAL_NUMBER, int256)
    return (leakedErrorIntegral + newTimeAdjustedError, newTimeAdjustedError)

@internal
@view
def getRawPiOutput(error: int256, errorI: int256) -> (int256, int256, int256):
    # // output = P + I = Kp * error + Ki * errorI
    pOutput: int256 = (error * self.kp) // EIGHTEEN_DECIMAL_NUMBER
    iOutput: int256 = (errorI * self.ki) // EIGHTEEN_DECIMAL_NUMBER

    return (self.coBias + pOutput + iOutput, pOutput, iOutput)

@external
@view
def getRawPiOutputExternal(error: int256, errorI: int256) -> (int256, int256, int256):
    # // output = P + I = Kp * error + Ki * errorI
    pOutput: int256 = (error * self.kp) // EIGHTEEN_DECIMAL_NUMBER
    iOutput: int256 = (errorI * self.ki) // EIGHTEEN_DECIMAL_NUMBER

    return (self.coBias + pOutput + iOutput, pOutput, iOutput)

@external
def update(error: int256) -> (int256, int256, int256):
    assert self.seedProposer == msg.sender, "PIController/invalid-msg-sender"

    assert block.timestamp > self.lastUpdateTime, "PIController/wait-longer"

    newErrorIntegral: int256 = 0
    newArea: int256 = 0
    (newErrorIntegral, newArea) = self.getNextErrorIntegral(error)

    piOutput: int256 = 0
    pOutput: int256 = 0
    iOutput: int256 = 0
    (piOutput, pOutput, iOutput) = self.getRawPiOutput(error, newErrorIntegral)

    boundedPiOutput: int256 = self.boundPiOutput(piOutput)

    self.errorIntegral = self.clampErrorIntegral(boundedPiOutput, newErrorIntegral, newArea)

    self.lastUpdateTime = block.timestamp
    self.lastError = error

    self.lastOutput = boundedPiOutput
    self.lastPOutput = pOutput
    self.lastIOutput = iOutput

    return (boundedPiOutput, pOutput, iOutput)

@external
@view
def lastUpdate() -> (uint256, int256, int256, int256):
    return (self.lastUpdateTime, self.lastOutput, self.lastPOutput, self.lastIOutput)

@external
@view
def getNextPiOutput(error: int256) -> (int256, int256, int256):
    newErrorIntegral: int256 = 0
    tmp: int256 = 0
    (newErrorIntegral, tmp) = self.getNextErrorIntegral(error)

    piOutput: int256 = 0
    pOutput: int256 = 0
    iOutput: int256 = 0
    (piOutput, pOutput, iOutput) = self.getRawPiOutput(error, newErrorIntegral)

    boundedPiOutput: int256 = self.boundPiOutput(piOutput)

    return (boundedPiOutput, pOutput, iOutput)

@external
@view
def elapsed() -> uint256:
    return 0 if self.lastUpdateTime == 0 else block.timestamp - self.lastUpdateTime

