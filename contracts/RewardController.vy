#pragma version ~=0.4.1

from interfaces import IOracle
import store

event OracleUpdated:
    chain_id: uint64
    new_value: uint256
    deviation: uint256
    time_since: uint256
    time_reward: uint256
    deviation_reward: uint256
    reward_mult: int256

struct Scale:
    chain_id: uint64
    scale: uint256

authorities: public(HashMap[address, bool])

kp: public(int256)
ki: public(int256)
co_bias: public(int256)
output_upper_bound: public(int256)
output_lower_bound: public(int256)
target_time_since: public(uint256)
reward_type: public(uint16)
min_reward: public(uint256)
max_reward: public(uint256)
min_time_reward: public(int256)
max_time_reward: public(int256)
min_deviation_reward: public(int256)
max_deviation_reward: public(int256)
default_window_size: public(uint256)
window_size: HashMap[uint64, uint256]
oracle: public(IOracle)

error_integral: public(int256)
last_error: public(int256)
last_output: public(int256)
last_p_output: public(int256)
last_i_output: public(int256)
last_update_time: public(uint256)

updater: public(address)

rewards: public(HashMap[address, uint256])
scales: public(HashMap[uint64, uint256])

EIGHTEEN_DECIMAL_NUMBER: constant(int256) = 10**18
EIGHTEEN_DECIMAL_NUMBER_U: constant(uint256) = 10**18


# State Variables
oracle_values: HashMap[uint64, HashMap[uint256, uint256]]  # Circular buffer simulated via mapping
index: HashMap[uint64, uint256]  # Pointer to next insert position (0 to N-1)
count: HashMap[uint64, uint256]  # Number of elements inserted so far, up to N
rolling_sum: HashMap[uint64, uint256]  # Sum of last N values for efficient averaging

coeff: public(int256[5])
intercept: public(int256)

@deploy
def __init__(_kp: int256, _ki: int256, _co_bias: int256,
             _output_upper_bound: int256, _output_lower_bound: int256, _target_time_since: uint256,
             _reward_type: uint16, _min_reward: uint256, _max_reward: uint256,
             _default_window_size: uint256, oracle: address,
             _coeff: int256[5]):
    #
    assert _output_upper_bound >= _output_lower_bound, "RewardController/invalid-bounds"
    assert oracle.is_contract, "Oracle address is not a contract"

    self.authorities[msg.sender] = True
    self.kp = _kp
    self.ki = _ki
    self.co_bias = _co_bias
    self.output_upper_bound = _output_upper_bound
    self.output_lower_bound = _output_lower_bound
    self.target_time_since = _target_time_since
    self.reward_type = _reward_type
    self.min_reward = _min_reward
    self.max_reward = _max_reward
    self.min_time_reward = convert(_min_reward//2, int256)
    self.max_time_reward = convert(_max_reward//2, int256)
    self.min_deviation_reward = convert(_min_reward//2, int256)
    self.max_deviation_reward = convert(_max_reward//2, int256)
    self.default_window_size = _default_window_size
    self.oracle = IOracle(oracle)
    self.coeff = _coeff
    self.last_update_time = block.timestamp

    self.updater = msg.sender

@external
def add_authority(account: address):
    assert self.authorities[msg.sender]
    self.authorities[account] = True
    
@external
def remove_authority(account: address):
    assert self.authorities[msg.sender]

    self.authorities[account] = False

@external
def set_scales(scales: DynArray[Scale, 64]):
    assert self.authorities[msg.sender]

    for s: Scale in scales:
        self.scales[s.chain_id] = s.scale

@external
def set_scale(chain_id: uint64, scale: uint256):
    assert self.authorities[msg.sender]

    self.scales[chain_id] = scale

@external
def modify_parameters_addr(parameter: String[32], addr: address):
    assert self.authorities[msg.sender]

    if (parameter == "oracle"):
        assert addr.is_contract, "Oracle address is not a contract"
        self.oracle = IOracle(addr)
    else:
        raise "RewardController/modify-unrecognized-param"

@external
def modify_parameters_int(parameter: String[32], val: int256):
    assert self.authorities[msg.sender]

    if (parameter == "output_upper_bound"):
        assert val > self.output_lower_bound, "RewardController/invalid-output_upper_bound"
        self.output_upper_bound = val
    elif (parameter == "output_lower_bound"):
        assert val < self.output_upper_bound, "RewardController/invalid-output_lower_bound"
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
        raise "RewardController/modify-unrecognized-param"

@external
def modify_parameters_uint(parameter: String[32], val: uint256):
    assert self.authorities[msg.sender]
    if (parameter == "target_time_since"):
        self.target_time_since = val
    elif (parameter == "min_reward"):
        assert val < self.max_reward, "RewardController/invalid-min_reward"
        self.min_reward = val
    elif (parameter == "max_reward"):
        assert val > self.min_reward, "RewardController/invalid-max_reward"
        self.max_reward = val
    elif (parameter == "default_window_size"):
        self.default_window_size = val
    else:
        raise "RewardController/modify-unrecognized-param"

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

@external
@view
def clamp_error_integral(bounded_pi_output:int256, new_error_integral: int256, new_area: int256) -> int256:
    return self._clamp_error_integral(bounded_pi_output, new_error_integral, new_area)

@internal
@view
def _clamp_error_integral(bounded_pi_output:int256, new_error_integral: int256, new_area: int256) -> int256: 
    # This logic is strictly for a *reverse-acting* controller where controller
    # output is opposite sign of error(kp and ki < 0)
    clamped_error_integral: int256 = new_error_integral
    if (bounded_pi_output == self.output_lower_bound and new_area > 0 and self.error_integral > 0):
        clamped_error_integral = clamped_error_integral - new_area
    elif (bounded_pi_output == self.output_upper_bound and new_area < 0 and self.error_integral < 0):
        clamped_error_integral = clamped_error_integral - new_area
    return clamped_error_integral

@internal
@view
def _get_new_error_integral(error: int256) -> (int256, int256):
    return (self.error_integral + error, error)

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
@pure
def error(target: int256, measured: int256) -> int256:
    return self._error(target, measured)

@internal
@pure
def _error(target: int256, measured: int256) -> int256:
     return (target - measured) * EIGHTEEN_DECIMAL_NUMBER // target

@external
def update_oracle(dat: Bytes[4096])-> (uint256, uint256):
    sid: uint8 = 0
    cid: uint64 = 0
    typ: uint16 = 0
    new_value: uint240 = 0
    new_ts: uint48 = 0
    new_height: uint64 = 0

    # new values
    sid, cid, typ, new_value, new_ts, new_height = store._decode(dat, self.reward_type)

    new_value_u: uint256 = convert(new_value, uint256)

    current_value: uint256 = 0
    current_height: uint64 = 0
    current_ts: uint48 = 0

    # Current oracle values
    (current_value, current_height, current_ts) = staticcall self.oracle.get(sid, cid, typ)

    target_scale: uint256 = self.scales[cid]
    assert target_scale != 0, "scale for cid is zero"

    # get update deviation and staleness(time_since)
    deviation: uint256 = 0
    if new_value_u > current_value:
        deviation = (new_value_u - current_value)*EIGHTEEN_DECIMAL_NUMBER_U//target_scale
    else:
        deviation = (current_value - new_value_u)*EIGHTEEN_DECIMAL_NUMBER_U//target_scale
  
    # This matches acceptance criteria in oracle
    assert new_height > current_height or (new_height==current_height and new_ts > current_ts), "new values are old"

    time_since: uint256 = convert(new_ts - current_ts, uint256) * EIGHTEEN_DECIMAL_NUMBER_U

    # calculate update reward
    time_reward: int256 = 0
    deviation_reward: int256 = 0
    time_reward, deviation_reward = self._calc_reward(convert(time_since, int256)//1000, convert(deviation, int256))

    # update oracle update_interval process
    self._add_value(cid, time_since)
    update_interval: int256 = convert(self._get_average(cid), int256)

    # get current error from target interval
    target_time_int: int256 = convert(self.target_time_since, int256)
    error: int256 = self._error(target_time_int, update_interval)

    reward_mult: int256 = 0
    p_output: int256 = 0
    i_output: int256 = 0

    # update feedback mechanism and get current reward multiplier
    reward_mult, p_output, i_output = self._update(error)

    # Don't use feedback if number of samples is less than window size
    if self.count[cid] < self._get_window_size(cid):
        reward_mult = EIGHTEEN_DECIMAL_NUMBER

    # adjust rewards with multiplier
    time_reward_adj: int256 = reward_mult * time_reward // EIGHTEEN_DECIMAL_NUMBER
    deviation_reward_adj: int256 = reward_mult * deviation_reward // EIGHTEEN_DECIMAL_NUMBER

    # store rewards
    time_reward_adj_u: uint256 = convert(time_reward_adj, uint256)
    deviation_reward_adj_u: uint256 = convert(deviation_reward_adj, uint256)
    self.rewards[msg.sender] += time_reward_adj_u + deviation_reward_adj_u

    log OracleUpdated(chain_id=cid, new_value=new_value_u,
                      deviation=deviation, time_since=time_since,
                      time_reward=time_reward_adj_u, deviation_reward=deviation_reward_adj_u,
                      reward_mult=reward_mult)

    extcall self.oracle.storeValues(dat)

    return time_reward_adj_u, deviation_reward_adj_u

@external
def update_oracle_mock(chain_id: uint64, new_value: uint256, new_height: uint64) -> (uint256, uint256):
    current_value: uint256 = 0
    current_height: uint64 = 0
    last_update_time: uint48 = 0
    current_value, current_height, last_update_time = staticcall self.oracle.get_value(chain_id)
    target_scale: uint256 = self.scales[chain_id]

    assert target_scale != 0, "Target scale is zero"

    deviation: uint256 = 0
    if new_value > current_value:
        #deviation = min((new_value - current_value)*EIGHTEEN_DECIMAL_NUMBER_U//target_scale, self.max_deviation)
        deviation = (new_value - current_value)*EIGHTEEN_DECIMAL_NUMBER_U//target_scale
    else:
        deviation = (current_value - new_value)*EIGHTEEN_DECIMAL_NUMBER_U//target_scale

    time_since: uint256 = (block.timestamp - convert(last_update_time, uint256)) * EIGHTEEN_DECIMAL_NUMBER_U

    time_reward: int256 = 0
    deviation_reward: int256 = 0
    time_reward, deviation_reward = self._calc_reward(convert(time_since, int256), convert(deviation, int256))

    # calculate reward multiplier
    self._add_value(chain_id, time_since)
    update_interval: int256 = convert(self._get_average(chain_id), int256)
    target_time_int: int256 = convert(self.target_time_since, int256)
    error: int256 = (target_time_int - update_interval) * EIGHTEEN_DECIMAL_NUMBER // target_time_int

    reward_mult: int256 = 0
    p_output: int256 = 0
    i_output: int256 = 0

    reward_mult, p_output, i_output = self._update(error)

    # Don't use feedback if number of samples is less than window size
    if self.count[chain_id] < self._get_window_size(chain_id):
        reward_mult = EIGHTEEN_DECIMAL_NUMBER

    time_reward_adj: int256 = reward_mult * time_reward // EIGHTEEN_DECIMAL_NUMBER
    deviation_reward_adj: int256 = reward_mult * deviation_reward // EIGHTEEN_DECIMAL_NUMBER

    #assert reward_adj > 0, "RewardController: reward_adj is not positive"

    time_reward_adj_u: uint256 = convert(time_reward_adj, uint256)
    deviation_reward_adj_u: uint256 = convert(deviation_reward_adj, uint256)
    self.rewards[msg.sender] += time_reward_adj_u + deviation_reward_adj_u

    extcall self.oracle.set_value(chain_id, new_value, new_height)

    return time_reward_adj_u, deviation_reward_adj_u

@external
@view
def calc_reward(time_since: int256, deviation: int256) -> (int256, int256):
    return self._calc_reward(time_since, deviation)


@external
@view
def calc_time_reward(time_since: int256) -> int256:
    return self._calc_time_reward(time_since)

@internal
@view
def _calc_time_reward(time_since: int256) -> int256:
    return max(min(self.coeff[0]*time_since//EIGHTEEN_DECIMAL_NUMBER + 
           self.coeff[2]*time_since*time_since//EIGHTEEN_DECIMAL_NUMBER//EIGHTEEN_DECIMAL_NUMBER, self.max_time_reward), self.min_time_reward)

@external
@view
def calc_deviation_reward(time_since: int256) -> int256:
    return self._calc_deviation_reward(time_since)

@internal
@view
def _calc_deviation_reward(deviation: int256) -> int256:
    return max(min(self.coeff[1]*deviation//EIGHTEEN_DECIMAL_NUMBER +
           self.coeff[4]*deviation*deviation//EIGHTEEN_DECIMAL_NUMBER//EIGHTEEN_DECIMAL_NUMBER, self.max_deviation_reward), self.min_deviation_reward)

@internal
@view
def _calc_reward(time_since: int256, deviation: int256) -> (int256, int256):
    return self._calc_time_reward(time_since), self._calc_deviation_reward(deviation)

@external
def add_value(chain_id: uint64, new_value: uint256):
    self._add_value(chain_id, new_value)

@external
@view
def get_window_size(chain_id: uint64) -> uint256:
    return self._get_window_size(chain_id)

@internal
@view
def _get_window_size(chain_id: uint64) -> uint256:
    value: uint256 = self.window_size[chain_id]
    if value == 0:
        return self.default_window_size
    return value

@internal
def _add_value(chain_id: uint64, new_value: uint256):
   
    #Add a new value to the circular buffer and update rolling sum.
    window_size: uint256 = self._get_window_size(chain_id)
    
    old_value: uint256 = 0

    #if self.count[chain_id] < self.window_size[chain_id]:
    if self.count[chain_id] < window_size:
        # Buffer not full yet
        self.count[chain_id] += 1
    else:
        # Buffer full: value at index will be overwritten
        old_value = self.oracle_values[chain_id][self.index[chain_id]]

    # Update rolling sum
    self.rolling_sum[chain_id] = self.rolling_sum[chain_id] + new_value - old_value

    # Store new value in buffer
    self.oracle_values[chain_id][self.index[chain_id]] = new_value

    # Update index (circular increment)
    self.index[chain_id] = (self.index[chain_id] + 1) % window_size

@external
@view
def get_average(chain_id: uint64) -> uint256:
    return self._get_average(chain_id)

@internal
@view
def _get_average(chain_id: uint64) -> uint256:
    if self.count[chain_id] == 0:
        return 0  # Avoid division by zero if no values added yet
    return self.rolling_sum[chain_id] // self.count[chain_id]

@external
def resize_buffer(chain_id: uint64, new_window_size: uint256):
    # Resize the buffer to a new window_size and adjust sum/count as needed.
    assert new_window_size > 0, "New window_size must be greater than 0"

    #if new_window_size == self.window_size[chain_id]:
    if new_window_size == self._get_window_size(chain_id):
        return  # No change needed

    # CASE 1: Increasing window_size — simple adjustment
    if new_window_size > self.count[chain_id]:
        self.window_size[chain_id] = new_window_size
        return

    # CASE 2: Decreasing window_size — need to keep last `new_window_size` items
    # Step 1: Identify starting point for last `new_window_size` items
    items_to_keep: uint256 = new_window_size
    start: uint256 = (self.index[chain_id] + (self.count[chain_id] - items_to_keep)) % self.count[chain_id]

    # Step 2: Rebuild buffer from these items
    temp_sum: uint256 = 0

    for i: uint256 in range(items_to_keep, bound=100000):
        pos: uint256 = (start + i) % self.count[chain_id]
        value: uint256 = self.oracle_values[chain_id][pos]  # Value to keep
        self.oracle_values[chain_id][i] = value  # Move to new position
        temp_sum += value

    # Step 3: Update state variables
    self.window_size[chain_id] = new_window_size
    self.count[chain_id] = items_to_keep
    self.rolling_sum[chain_id] = temp_sum
    self.index[chain_id] = items_to_keep % new_window_size  # Where next value will go

    # NOTE: Old values beyond `new_window_size` will remain in storage, but ignored logically.

#@view
#@external
# DONT NEED
#def _get_next_average(potential_value: uint256) -> uint256:
#    """
#    Simulate what the average would be if `potential_value` was added.
#    Does NOT update state.
#    """
#    temp_sum: uint256 = self.rolling_sum
#    temp_count: uint256 = self.count
#
#    if self.count < self.window_size:
#        # Buffer not full yet
#        temp_sum += potential_value
#        temp_count += 1
#    else:
#        # Buffer full: would replace value at `index`
#        old_value: uint256 = self.oracle_values[self.index]
#        temp_sum = temp_sum + potential_value - old_value
#
#    return temp_sum // temp_count


@external
def update(error: int256) -> (int256, int256, int256):
    return self._update(error)

@internal
def _update(error: int256) -> (int256, int256, int256):
    assert block.timestamp  > self.last_update_time, "RewardController/wait-longer"

    new_error_integral: int256 = 0
    new_area: int256 = 0
    (new_error_integral, new_area) = self._get_new_error_integral(error)

    pi_output: int256 = 0
    p_output: int256 = 0
    i_output: int256 = 0
    (pi_output, p_output, i_output) = self._get_raw_pi_output(error, new_error_integral)

    bounded_pi_output: int256 = self._bound_pi_output(pi_output)

    self.error_integral = self._clamp_error_integral(bounded_pi_output, new_error_integral, new_area)

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

