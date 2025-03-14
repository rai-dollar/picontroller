#pragma version ~=0.4.0


from interfaces import IOracle

authorities: public(HashMap[address, bool])

control_variable: public(bytes32)
kp: public(int256)
ki: public(int256)
co_bias: public(int256)
output_upper_bound: public(int256)
output_lower_bound: public(int256)
target_time_since: public(uint256)
min_reward: public(uint256)
max_reward: public(uint256)
min_ts: public(uint256)
max_ts: public(uint256)
min_deviation: public(uint256)
max_deviation: public(uint256)
window_size: public(uint256)
oracle: public(IOracle)

error_integral: public(int256)
last_error: public(int256)
last_output: public(int256)
last_p_output: public(int256)
last_i_output: public(int256)
last_update_time: public(uint256)

updater: public(address)

rewards: public(HashMap[address, uint256])
scales: public(HashMap[uint256, uint256])

EIGHTEEN_DECIMAL_NUMBER: constant(int256) = 10**18


# State Variables
#oracle_values: uint256[N]  # Circular buffer to hold last N values
oracle_values: HashMap[uint256, uint256]  # Circular buffer simulated via mapping
index: uint256  # Pointer to next insert position (0 to N-1)
count: uint256  # Number of elements inserted so far, up to N
rolling_sum: uint256  # Sum of last N values for efficient averaging


#min_reward = 1e-4
#max_reward = 1
#min_ts = 1
#max_ts = 3600
#min_deviation = 0.1
#max_deviation = 5

# coeff
#[-435426.012, -91396091300000.0, 3776907750000000.0, 63953129299.99999, 5670509380.0, 1.92634303e+16]
coeff: public(int256[6])
intercept: public(int256)


@deploy
def __init__(_control_variable: bytes32, _kp: int256, _ki: int256, _co_bias: int256,
             _output_upper_bound: int256, _output_lower_bound: int256, _target_time_since: uint256,
             _min_reward: uint256, _max_reward: uint256, _min_ts: uint256,
             _max_ts: uint256, _min_deviation: uint256, _max_deviation: uint256,
             _window_size: uint256, oracle_address: address,
             _coeff: int256[6], _intercept: int256):
    #
    assert _output_upper_bound >= _output_lower_bound, "PIController/invalid-bounds"
    assert oracle_address.is_contract, "Oracle address is not a contract"

    self.authorities[msg.sender] = True
    self.control_variable = _control_variable
    self.kp = _kp
    self.ki = _ki
    self.co_bias = _co_bias
    self.output_upper_bound = _output_upper_bound
    self.output_lower_bound = _output_lower_bound
    self.target_time_since = _target_time_since
    self.min_reward = _min_reward
    self.max_reward = _max_reward
    self.min_ts = _min_ts
    self.max_ts = _max_ts
    self.min_deviation = _min_deviation
    self.max_deviation = _max_deviation
    self.window_size = _window_size
    self.oracle = IOracle(oracle_address)
    self.coeff = _coeff
    self.intercept = _intercept
    self.last_update_time = 0
    self.last_error = 0
    self.error_integral = 0

@external
def add_authority(account: address):
    assert self.authorities[msg.sender]
    self.authorities[account] = True
    
@external
def remove_authority(account: address):
    assert self.authorities[msg.sender]
    self.authorities[account] = False

@external
def set_scales(chain_ids: uint256[64], scales: uint256[64]):
    assert self.authorities[msg.sender]
    for i: uint256 in range(64):
        self.scales[chain_ids[i]] = scales[i]

@external
def modify_parameters_addr(parameter: String[32], addr: address):
    assert self.authorities[msg.sender]
    if (parameter == "updater"):
        self.updater = addr
    else:
        raise "PIController/modify-unrecognized-param"

@external
def modify_parameters_int(parameter: String[32], val: int256):
    assert self.authorities[msg.sender]
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

    return (self.error_integral + new_time_adjusted_error, new_time_adjusted_error)

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
def update_oracle(chain_id: uint256, new_value: uint256):
    current_value: uint256 = 0
    last_update_time: uint256 = 0
    current_value, last_update_time = staticcall self.oracle.get_value(chain_id)
    target_scale: uint256 = self.scales[chain_id]

    deviation: uint256 = 0
    if new_value > current_value:
        deviation = min((new_value - current_value)*10**18//target_scale, self.max_deviation)
    else:
        deviation = min((current_value - new_value)*10**18//target_scale, self.max_deviation)

    time_since: uint256 = block.timestamp - last_update_time

    reward: int256 = self._calc_reward(convert(time_since, int256), convert(deviation, int256))

    # calculate reward adjustment
    self._add_value(time_since)
    update_interval: int256 = convert(self._get_average(), int256)
    error: int256 = (update_interval - convert(self.target_time_since, int256)) * 10**18 // update_interval
    pi_output: int256 = 0
    p_output: int256 = 0
    i_output: int256 = 0

    pi_output, p_output, i_output = self.update(error)

    reward_adj: int256 = pi_output * reward //10**18

    assert reward_adj > 0

    self.rewards[msg.sender] += convert(reward_adj, uint256)

    extcall self.oracle.update_value(new_value)


def _calc_reward(time_since: int256, deviation: int256) -> int256:
    return min(max(self.coeff[0] + self.coeff[1]*time_since//10**18 + self.coeff[2]*deviation//10**18 + 
           self.coeff[3]*time_since*time_since//10**18//10**18 +
           self.coeff[5]*deviation*deviation//10**18//10**18 + 
           self.intercept, convert(self.min_reward, int256)), convert(self.max_reward, int256))


@internal
def _add_value(new_value: uint256):
   
    #Add a new value to the circular buffer and update rolling sum.
    
    old_value: uint256 = 0

    if self.count < self.window_size:
        # Buffer not full yet
        self.count += 1
    else:
        # Buffer full: value at index will be overwritten
        old_value = self.oracle_values[self.index]

    # Update rolling sum
    self.rolling_sum = self.rolling_sum + new_value - old_value

    # Store new value in buffer
    self.oracle_values[self.index] = new_value

    # Update index (circular increment)
    self.index = (self.index + 1) % self.window_size

@internal
@view
def _get_average() -> uint256:
    if self.count == 0:
        return 0  # Avoid division by zero if no values added yet
    return self.rolling_sum // self.count

@view
@external
def _get_next_average(potential_value: uint256) -> uint256:
    """
    Simulate what the average would be if `potential_value` was added.
    Does NOT update state.
    """
    temp_sum: uint256 = self.rolling_sum
    temp_count: uint256 = self.count

    if self.count < self.window_size:
        # Buffer not full yet
        temp_sum += potential_value
        temp_count += 1
    else:
        # Buffer full: would replace value at `index`
        old_value: uint256 = self.oracle_values[self.index]
        temp_sum = temp_sum + potential_value - old_value

    return temp_sum // temp_count


@internal
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
    return self._get_new_pi_output(error)

@internal
@view
def _get_new_pi_output(error: int256) -> (int256, int256, int256):
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

