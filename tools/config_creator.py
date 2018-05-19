import json, codecs


def create_new_cfg():
    config = {}
    try:
        config['username'] = validate_input('Account username: ', 3)
        config['password'] = validate_input('Account password: ', 3)
        config['character'] = validate_input('Enter the character name the bot will run on: ', 3)
        config['superadmin'] = validate_input('Enter the name of the character you wish to be super-admin: ', 3)
        config['dimension'] = validate_input('Choose dimension (1 - Rubi-Ka(Live), 2 - Test ,3 - Proxy)[1]: ', 1, 1, ['1', '2', 3])
        print('Database info, press enter to use default values.')
        config['db_name'] = validate_input('Database name?[mangopie]', 0, 'mangopie')
        config['db_host'] = validate_input('Database host?[mongodb://localhost:27017/]', 0, 'mongodb://localhost:27017/')

        with open('./conf/config.json', 'wb') as f:
            json.dump(config, codecs.getwriter('utf-8')(f), ensure_ascii=False, indent=4, sort_keys=False)
    except KeyboardInterrupt:
        exit(0)


def validate_input(prompt, min_length=None, default=None, strictChoice=None):
    while True:
        ui = input(prompt)
        if len(ui) < min_length and default is None:
            print('Invalid input, try again!')
        elif strictChoice is not None and ui not in strictChoice and default is None:
            print('%s is not a valid dimension!' % ui)
        elif len(ui) == 0 and default is not None:
            return default
        else:
            break
    return ui
