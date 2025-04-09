# rewardcontroller

## Dependencies

tested w/ Python 3.11

`python -m venv venv`
`source venv/bin/activate`
`pip install -r requirements.txt`


## Tests

`ape test tests/test_rewardcontroller.py`


## Deploy to Sepolia

### Deploy
`ape run scripts/deploy.py --network ethereum:sepolia:infura`

### Configure

TODO: integrate this with deployment

`ape run scripts/set_scales.py --network ethereum:sepolia:infura`

### Update

`ape run scripts/update.py --network ethereum:sepolia:infura`
