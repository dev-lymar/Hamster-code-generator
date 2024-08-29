def load_proxies_from_file(file_path):
    proxies = []
    with open(file_path, 'r') as file:
        for line in file:
            proxy = line.strip()
            if proxy:
                proxies.append(proxy)
    return proxies


proxies = load_proxies_from_file('proxies.txt')

# Basic configuration of games and proxies
game_configs = [
    {
        'name': 'Bike Ride 3D',
        'app_token': 'd28721be-fd2d-4b45-869e-9f253b554e50',
        'promo_id': '43e35910-c168-4634-ad4f-52fd764a843f',
        'base_delay': 20,
        'attempts': 30,
        'copies': 11,
    },
    {
        'name': 'Chain Cube 2048',
        'app_token': 'd1690a07-3780-4068-810f-9b5bbf2931b2',
        'promo_id': 'b4170868-cef0-424f-8eb9-be0622e8e8e3',
        'base_delay': 20,
        'attempts': 20,
        'copies': 4,
    },
    {
        'name': 'Train Miner',
        'app_token': '82647f43-3f87-402d-88dd-09a90025313f',
        'promo_id': 'c4480ac7-e178-4973-8061-9ed5b2e17954',
        'base_delay': 20,
        'attempts': 15,
        'copies': 4,
    },
    {
        'name': 'Merge Away',
        'app_token': '8d1cc2ad-e097-4b86-90ef-7a27e19fb833',
        'promo_id': 'dc128d28-c45b-411c-98ff-ac7726fbaea4',
        'base_delay': 20,
        'attempts': 30,
        'copies': 6,
    },
    {
        'name': 'Twerk Race 3D',
        'app_token': '61308365-9d16-4040-8bb0-2f4a4c69074c',
        'promo_id': '61308365-9d16-4040-8bb0-2f4a4c69074c',
        'base_delay': 20,
        'attempts': 20,
        'copies': 9,
    },
    {
        'name': 'Polysphere',
        'app_token': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71',
        'promo_id': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71',
        'base_delay': 20,
        'attempts': 25,
        'copies': 17,
    },
    {
        'name': 'Mow and Trim',
        'app_token': 'ef319a80-949a-492e-8ee0-424fb5fc20a6',
        'promo_id': 'ef319a80-949a-492e-8ee0-424fb5fc20a6',
        'base_delay': 20,
        'attempts': 20,
        'copies': 6,
    },
    {
        'name': 'Mud Racing',
        'app_token': '8814a785-97fb-4177-9193-ca4180ff9da8',
        'promo_id': '8814a785-97fb-4177-9193-ca4180ff9da8',
        'base_delay': 20,
        'attempts': 25,
        'copies': 6,
    },
    {
        'name': 'Cafe Dash',
        'app_token': 'bc0971b8-04df-4e72-8a3e-ec4dc663cd11',
        'promo_id': 'bc0971b8-04df-4e72-8a3e-ec4dc663cd11',
        'base_delay': 23,
        'attempts': 35,
        'copies': 17,
    }
]

# Convert the list of proxies to a list
proxy_keys = list(proxies)

# Check if there are enough proxies
total_proxies_needed = sum(config['copies'] for config in game_configs)
if len(proxy_keys) < total_proxies_needed:
    raise ValueError(f"Not enough proxies: {len(proxy_keys)} provided, but {total_proxies_needed} needed.")

# Variable to track the current proxy index
proxy_index = 0

# Generate a list of games based on the number of copies and proxies
games = []

for config in game_configs:
    for i in range(config['copies']):
        if proxy_index >= len(proxies):
            raise ValueError(
                f"Not enough proxies for game copies: {config['name']} needs {config['copies']} copies, "
                f"but only {len(proxies)} proxies are available.")

        game_copy = {
            'name': config['name'],
            'app_token': config['app_token'],
            'promo_id': config['promo_id'],
            'proxy': proxies[proxy_index],
            'base_delay': config['base_delay'],
            'attempts': config['attempts'],
        }
        games.append(game_copy)
        proxy_index += 1
