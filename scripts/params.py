kp = -5*10**18
ki = -2*10**15
co_bias = 10**18
output_upper_bound = 10*10**18
output_lower_bound = 10**15 # 1e-3
target_time_since = 1800 * 10**18
default_window_size = 20

# reward calc
reward_type = 322 # 90th maxPf
min_reward = 10**14 #1e-4
max_reward = 10**18 #1
min_ts = 10**18 #11
max_ts = 36 * 10**20 #3600
min_deviation = 10**17 # 0.1
max_deviation = 5 * 10**18 # 5
coeff = [10611581, 3777134486958753, 38572373423, 5670509383, 19263385883489428]


scales = {42161: 99340000000000000, # Arbitrum
          8453: 144939290000000000, # Base
          59144: 612710000000000000, # Linea
          10: 228550000000000, # Opt
          1868: 228550000000000, # Soneium TODO: UPDATE
          130: 228550000000000, # Unichain TODO: UPDATE
          1: 10**18 #ethereum TODO: update
          }
