import requests

def do_refresh_token(client_id, refresh_token):
    """
    刷新微软邮箱令牌
    """
    data = {
        'client_id': client_id,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    resp = requests.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', data=data, timeout=30)
    res_json = resp.json()
    if res_json.get('refresh_token'):
        return res_json
    else:
        return None
        


if __name__ == "__main__":
    email_line='ninyvobkqv44@outlook.com----pkgmlgtbv577----9e5f94bc-e8a4-4e73-b8be-63364c29d753----M.C557_SN1.0.U.-ClEDTHzX5ioGUCXC0KfG3ftik4Cnz4uneUP7NUZdH1NbJPJ*K0dVW3wHAJhf!2W4R2qcUwOP33jFwcgglgm9dhQtS7TCmgVMBLndxfug0aq147jYiMYb5tnq1X1j5jqIa0Xisu*jvFyKJEIHlPh8v4sESWuhwEz75d7mXCkbwzQ8ZM7Lvnz7AA72ePrTyGOs*we02kX71FeEiZi6bIhHd1xroFyXJoRIj27NpwXj9WXcRUJNBDMOvcTD79tRNYsa4lCpT3z3rb6ajn5HDPWM1elL0mUiRCRUJFODbevFYlZH3*zUefTdzt6Pr3nxHsPO4KTjg6nWApI5Brpr0Uoi6w917u4yASV3J4Lam3mnSQQ7xzsiZ5OiCRARVrHMtV5IMPqeYSpFne7P4W7OCs31pnsqPcWppSNUe5fRJcumLawy'
    email,password,client_id,refresh_token=email_line.split('----')
    import asyncio
    loop=asyncio.get_event_loop()
    new_refresh_token=loop.run_until_complete(do_refresh_token(client_id,refresh_token))
    