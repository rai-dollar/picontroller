kp = -2*10**18
ki = -1*10**17
co_bias = 10**18
output_upper_bound = 10*10**18
output_lower_bound = 10**15 # 1e-3
target_time_since = 1800 * 10**18
default_window_size = 10

# reward calc
reward_type = 322 # 90th maxPf
min_reward = 10**18 # 1
max_reward = 10**22 # 10,000
min_ts = 10**18 #11
max_ts = 72 * 10**20 #7200
min_deviation = 10**17 # 0.1
max_deviation = 5 * 10**18 # 5
#coeff = [10611581, 3777134486958753, 38572373423, 5670509383, 19263385883489428]
coeff = [-46514293247, 38453845085324763136, 96431335480082, 27781636353025, 192269225426609012736]


scales = {42161: 99340000000000000, # Arbitrum
          8453: 144939290000000000, # Base
          59144: 612710000000000000, # Linea
          10: 228550000000000, # Opt
          1868: 228550000000000, # Soneium TODO: UPDATE
          130: 228550000000000, # Unichain TODO: UPDATE
          1: 10**18 #ethereum TODO: update
          }
