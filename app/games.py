from proxies import proxies

# Basic configuration of games and proxies
game_configs = [
    {
        'name': 'Riding Extreme 3D',
        'app_token': 'd28721be-fd2d-4b45-869e-9f253b554e50',
        'promo_id': '43e35910-c168-4634-ad4f-52fd764a843f',
        'proxies': ['proxy1', 'proxy2', 'proxy3', 'proxy4', 'proxy5', 'proxy6'],
        'base_delay': 20,
        'attempts': 30,
        'copies': 6,
    },
    {
        'name': 'Chain Cube 2048',
        'app_token': 'd1690a07-3780-4068-810f-9b5bbf2931b2',
        'promo_id': 'b4170868-cef0-424f-8eb9-be0622e8e8e3',
        'proxies': ['proxy7', 'proxy8'],
        'base_delay': 20,
        'attempts': 20,
        'copies': 2,
    },
    {
        'name': 'My Clone Army',
        'app_token': '74ee0b5b-775e-4bee-974f-63e7f4d5bacb',
        'promo_id': 'fe693b26-b342-4159-8808-15e3ff7f8767',
        'proxies': ['proxy11', 'proxy12', 'proxy13', 'proxy14', 'proxy15', 'proxy16', 'proxy17'],
        'base_delay': 130,
        'attempts': 30,
        'copies': 8,
    },
    {
        'name': 'Train Miner',
        'app_token': '82647f43-3f87-402d-88dd-09a90025313f',
        'promo_id': 'c4480ac7-e178-4973-8061-9ed5b2e17954',
        'proxies': ['proxy9', 'proxy10'],
        'base_delay': 20,
        'attempts': 15,
        'copies': 2,
    },
    {
        'name': 'Merge Away',
        'app_token': '8d1cc2ad-e097-4b86-90ef-7a27e19fb833',
        'promo_id': 'dc128d28-c45b-411c-98ff-ac7726fbaea4',
        'proxies': ['proxy19', 'proxy20', 'proxy21', 'proxy22'],
        'base_delay': 20,
        'attempts': 30,
        'copies': 4,
    },
    {
        'name': 'Twerk Race 3D',
        'app_token': '61308365-9d16-4040-8bb0-2f4a4c69074c',
        'promo_id': '61308365-9d16-4040-8bb0-2f4a4c69074c',
        'proxies': ['proxy23', 'proxy24', 'proxy25', 'proxy26', 'proxy18'],
        'base_delay': 20,
        'attempts': 20,
        'copies': 5,
    },
    {
        'name': 'Polysphere',
        'app_token': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71',
        'promo_id': '2aaf5aee-2cbc-47ec-8a3f-0962cc14bc71',
        'proxies': ['proxy27', 'proxy28', 'proxy29', 'proxy30'],
        'base_delay': 20,
        'attempts': 20,
        'copies': 5,
    }
]

# Generation a list of games based on the number of copies and proxies
games = []

for config in game_configs:
    for i in range(config['copies']):
        game_copy = {
            'name': config['name'],
            'app_token': config['app_token'],
            'promo_id': config['promo_id'],
            'proxy': proxies[config['proxies'][i % len(config['proxies'])]],
            'base_delay': config['base_delay'],
            'attempts': config['attempts'],
        }
        games.append(game_copy)
