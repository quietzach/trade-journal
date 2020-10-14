import robin_stocks as r
import robin_stocks.authentication as authentication
import robin_stocks.helper as helper
import robin_stocks.urls as urls

import pandas as pd
from trader.data.importers.csv_importer import GenericImporter


def import_orders():
    # TODO: Check if logged in
    # get all orders (assumed logged in)
    orders = r.get_all_stock_orders()

    r.logout()

    clean_orders = []
    for order in orders:
        filled = float(order['cumulative_quantity'])
        if len(order['executions']) > 0:
            instrument = r.helper.request_get(order['instrument'])
            symbol = instrument['symbol']
            side = order['side']
            fees = order['fees']
            price = order['average_price']
            #         quantity = order['quantity'] # intented quantity for order
            quantity = order['cumulative_quantity']  # filled quantity
            timestamp = order['created_at']
            clean_orders.append({
                'Timestamp': timestamp,
                'Symbol': symbol,
                'Quantity': quantity,
                'Price': price,
                'Side': side.upper(),
                'Commission': 0.0,
                'Fee': fees,
                'Type': 'SHARE'
            })
    #         print(f'Symbol: {symbol}, Side: {side}, Fees: {fees}, Price: {price}, Quantity: {quantity}, Timestamp: {timestamp}')

    rh_executions = pd.DataFrame(clean_orders,
                                 columns=['Timestamp', 'Symbol', 'Quantity', 'Price',
                                          'Side', 'Commission', 'Fee', 'Type'])

    # import data
    importer = GenericImporter()
    importer.load_dataframe(rh_executions)
    importer.import_data()

    return True


def login(username, password, expiresIn=86400, scope='internal', by_sms=True):
    device_token = authentication.generate_device_token()

    # Challenge type is used if not logging in with two-factor authentication.
    if by_sms:
        challenge_type = "sms"
    else:
        challenge_type = "email"

    url = urls.login_url()
    payload = {
        'client_id': 'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS',
        'expires_in': expiresIn,
        'grant_type': 'password',
        'password': password,
        'scope': scope,
        'username': username,
        'challenge_type': challenge_type,
        'device_token': device_token
    }
    data = helper.request_post(url, payload)
    payload['login_response'] = data
    return payload


def respond_challenge(username, password, device_token, mfa_token=None, sms_code=None, expiresIn=86400, scope='internal', by_sms=True):

    if by_sms:
        challenge_type = "sms"
    else:
        challenge_type = "email"

    payload = {
        'client_id': 'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS',
        'expires_in': expiresIn,
        'grant_type': 'password',
        'password': password,
        'scope': scope,
        'username': username,
        'challenge_type': challenge_type,
        'device_token': device_token
    }

    url = urls.login_url()

    if mfa_token:
        payload['mfa_required'] = True
        payload['mfa_code'] = mfa_token

    # data = payload['login_response']
    data = payload

    response = {
        'status': "Success"
    }

    # Handle case where mfa or challenge is required.
    if data:
        if 'mfa_required' in data:
            res = helper.request_post(url, payload, jsonify_data=False)
            data = res.json()
        elif 'challenge' in data:
            challenge_id = data['challenge']['id']
            res = authentication.respond_to_challenge(challenge_id, sms_code)
            helper.update_session('X-ROBINHOOD-CHALLENGE-RESPONSE-ID', challenge_id)
            data = helper.request_post(url, payload)
        # Update Session data with authorization or raise exception with the information present in data.
        if 'access_token' in data:
            token = '{0} {1}'.format(data['token_type'], data['access_token'])
            helper.update_session('Authorization', token)
            helper.set_login_state(True)
            data['detail'] = "Logged in with brand new authentication code."
        else:
            response['status'] = data['detail']
            # raise Exception(data['detail'])
    else:
        response['status'] = 'Error: Trouble connecting to robinhood API.'
        # raise Exception('Error: Trouble connecting to robinhood API. Check internet connection.')


    # import orders
    import_orders()

    return response