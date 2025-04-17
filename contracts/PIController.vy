#pragma version >0.3.10

authorities: public(HashMap[address, uint256])


control_variable: public(bytes32)
kp: public(int256)
ki: public(int256)
co_bias: public(int256)
output_upper_bound: public(int256)
output_lower_bound: public(int256)
error_integral: public(int256)
last_error: public(int256)
per_second_integral_leak: public(uint256)
last_output: public(int256)
last_p_output: public(int256)
last_i_output: public(int256)
last_update_time: public(uint256)

updater: public(address)

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
def __init__(_control_variable: bytes32, _kp: int256, _ki: int256, _co_bias: int256,
_per_second_integral_leak: uint256, _output_upper_bound: int256,
_output_lower_bound: int256, imported_state: int256[3]):
    #
    assert _output_upper_bound >= _output_lower_bound, "PIController/invalid-bounds"
    assert convert(imported_state[0], uint256) <= block.timestamp, "PIController/invalid-imported-time"
    self.authorities[msg.sender] = 1
    self.control_variable = _control_variable
    self.kp = _kp
    self.ki = _ki
    self.co_bias = _co_bias
    self.per_second_integral_leak = _per_second_integral_leak
    self.output_upper_bound = _output_upper_bound
    self.output_lower_bound = _output_lower_bound
    self.last_update_time = convert(imported_state[0], uint256)
    self.last_error = imported_state[1]
    self.error_integral = imported_state[2]

@external
def add_authority(account: address):
    self.authorities[account] = 1
    
@external
def remove_authority(account: address):
    self.authorities[account] = 0

@external
def modify_parameters_addr(parameter: String[32], addr: address):
    if (parameter == "updater"):
        self.updater = addr
    else:
        raise "PIController/modify-unrecognized-param"

@external
def modify_parameters_uint(parameter: String[32], val: uint256):
    if (parameter == "per_second_integral_leak"):
        assert val <= TWENTY_SEVEN_DECIMAL_NUMBER, "PIController/invalid-per_second_integral_leak"
        self.per_second_integral_leak = val
    else:
        raise "PIController/modify-unrecognized-param"

@external
def modify_parameters_int(parameter: String[32], val: int256):
    if (parameter == "output_upper_bound"):
        assert val > self.output_lower_bound, "PIController/invalid-output_upper_bound"
        self.output_upper_bound = val
    elif (parameter == "output_lower_bound"):
        assert val < self.output_upper_bound, "PIController/invalid-output_lower_bound"
        self.output_lower_bound = val
    elif (parameter == "kp"):
        self.kp = val
    elif (parameter == "ki"):
        self.ki = val
    elif (parameter == "co_bias"):
        self.co_bias = val
    elif (parameter == "error_integral"):
        self.error_integral = val
    else:
        raise "PIController/modify-unrecognized-param"

@internal
@view
def _riemann_sum(x: int256, y: int256)-> int256:
    return (x + y) // 2

@internal
@view
def _bound_pi_output(pi_output: int256) -> int256:
    bounded_pi_output: int256 = pi_output
    if pi_output < self.output_lower_bound:
        bounded_pi_output = self.output_lower_bound
    elif pi_output > self.output_upper_bound:
        bounded_pi_output = self.output_upper_bound

    return bounded_pi_output

@external
@view
def bound_pi_output(pi_output: int256) -> int256:
    return self._bound_pi_output(pi_output)

@internal
@view
def clamp_error_integral(bounded_pi_output:int256, new_error_integral: int256, new_area: int256) -> int256:
    clamped_error_integral: int256 = new_error_integral
    if (bounded_pi_output == self.output_lower_bound and new_area < 0 and self.error_integral < 0):
        clamped_error_integral = clamped_error_integral - new_area
    elif (bounded_pi_output == self.output_upper_bound and new_area > 0 and self.error_integral > 0):
        clamped_error_integral = clamped_error_integral - new_area
    return clamped_error_integral

@internal
@view
def _get_new_error_integral(error: int256) -> (int256, int256):
    elapsed: uint256 = 0 if (self.last_update_time == 0) else block.timestamp - self.last_update_time
    
    new_time_adjusted_error: int256 = self._riemann_sum(error, self.last_error) * convert(elapsed, int256)

    #accumulated_leak: uint256 = RAY if self.per_second_integral_leak == convert(1E27, uint256) else self.my_exp_uint256(self.per_second_integral_leak, elapsed, RAY)

    accumulated_leak: uint256 = RAY
    leaked_error_integral: int256 = (convert(accumulated_leak, int256) * self.error_integral) // convert(TWENTY_SEVEN_DECIMAL_NUMBER, int256)
    
    return (leaked_error_integral + new_time_adjusted_error, new_time_adjusted_error)

@external
@view
def get_new_error_integral(error: int256) -> (int256, int256):
    return self._get_new_error_integral(error)

@internal
@view
def _get_raw_pi_output(error: int256, errorI: int256) -> (int256, int256, int256):
    # // output = P + I = Kp * error + Ki * errorI
    p_output: int256 = (error * self.kp) // EIGHTEEN_DECIMAL_NUMBER
    i_output: int256 = (errorI * self.ki) // EIGHTEEN_DECIMAL_NUMBER

    return (self.co_bias + p_output + i_output, p_output, i_output)

@external
@view
def get_raw_pi_output(error: int256, errorI: int256) -> (int256, int256, int256):
    return self._get_raw_pi_output(error, errorI)
    
@external
def update(error: int256) -> (int256, int256, int256):
    assert self.updater == msg.sender, "PIController/invalid-msg-sender"

    assert block.timestamp > self.last_update_time, "PIController/wait-longer"

    new_error_integral: int256 = 0
    new_area: int256 = 0
    (new_error_integral, new_area) = self._get_new_error_integral(error)

    pi_output: int256 = 0
    p_output: int256 = 0
    i_output: int256 = 0
    (pi_output, p_output, i_output) = self._get_raw_pi_output(error, new_error_integral)

    bounded_pi_output: int256 = self._bound_pi_output(pi_output)

    self.error_integral = self.clamp_error_integral(bounded_pi_output, new_error_integral, new_area)

    self.last_update_time = block.timestamp
    self.last_error = error

    self.last_output = bounded_pi_output
    self.last_p_output = p_output
    self.last_i_output = i_output

    return (bounded_pi_output, p_output, i_output)

@external
@view
def last_update() -> (uint256, int256, int256, int256):
    return (self.last_update_time, self.last_output, self.last_p_output, self.last_i_output)

@external
@view
def get_new_pi_output(error: int256) -> (int256, int256, int256):
    new_error_integral: int256 = 0
    tmp: int256 = 0
    (new_error_integral, tmp) = self._get_new_error_integral(error)

    pi_output: int256 = 0
    p_output: int256 = 0
    i_output: int256 = 0
    (pi_output, p_output, i_output) = self._get_raw_pi_output(error, new_error_integral)

    bounded_pi_output: int256 = self._bound_pi_output(pi_output)

    return (bounded_pi_output, p_output, i_output)

@external
@view
def elapsed() -> uint256:
    return 0 if self.last_update_time == 0 else block.timestamp - self.last_update_time

