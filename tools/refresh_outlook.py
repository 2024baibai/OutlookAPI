import httpx

async def do_refresh_token(client_id,refresh_token):
    """
    刷新微软邮箱令牌
    """
    data = {
        'client_id': client_id,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    async with httpx.AsyncClient() as client:
        ret = await client.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', data=data)
        res_json = ret.json()
        #{'token_type': 'Bearer', 'scope': 'https://outlook.office.com/IMAP.AccessAsUser.All https://outlook.office.com/EWS.AccessAsUser.All https://outlook.office.com/POP.AccessAsUser.All https://outlook.office.com/SMTP.Send', 'expires_in': 3599, 'ext_expires_in': 3599, 'access_token': 'EwAoBOl3BAAUxG8T4TQNdaMKj7W5hdXgD68HTzwAAdfiyJx9kIpilFSitt2vxiAo1seUSRs5gBCGQ4R1lSlA7O7NvYvKGbUMuDInTViOTDGuTwNgrnuKHuvkuk2FqNLMAD+By2eRuMpc9zUb4AF8mSjXbU0DfJQAWEcQBdGSZHF3Dzea2STzS/AMvAwmMlva7jgcys7iR+KsZpJ8jx4+BAdBKFP3hQFxOwrrvavALTZ0PxsvqS3fdPGVD53+qdwuE/iS8vfhlEbpGa4yIiR6aUsPIlqu694dn3q3mJRZdayo43fO8fto6OyOKMo3DMeCPsD3mD27mwZiLn/bHED6yTGGE/Bhipte/P++O8zDbkGCzRWoOYilaTmAZVkZa5QQZgAAEKOtvvRPOB5iKWDobDMjzu7wAjKYYshcj2/Cy0QiYwTX8/CG+n7AQBeqrEHPWE0rI9HXI116hJz3xAs12vZWs3JRS652SRS1ondDs7gIvpeVmYOif7ej4qmBvDMsHPQi1sBuxInLUeucZygwg6ISQ2VETmwrUgg4Mkv5ZKn65mxAa+uhovKA/8w161sxBhoDper/Jvbs9B8wQPiFAzXeJBCe5pEaz388xYPzmZGZ286CL6MMnXcUcisEQ7XByiVq0PeJT88kKirzQdJdz7Wty/ccN8nxts18QviamRnmjOdogasS9dc9wkTGVx5euW2+NuAb8I1+5zwWFP6XRvN5NaZXtj1x7OcFCqJWft3WKgP2Pdz0gAk1OX2yUiNump7AkrFyUDIf6aUGi45yoJdtHxGHHnprO3icEzsXNRltkW5wolCuAyprA+7tIVFZn1r3MFuCUJnUbyAWtgj+vNq+Q2tLB+6sdf03DsPMwyZM28mgwJc7YOrRiLyoMDrD/3PVzLs/Yq7GsTOCRaVZarNRFnJMDHmFjRzqm3BcBn+8GUv4VNEE5vdHll8MQXoCuQySzLxghpOntbh4l48XvQEn/OXm63XAD2BSgr5fjEGGJfCAiilGfVxjN/yiUOplStfH8cehKcVIBE1J/zPVJvhczOamJmI1klZ7FasbGZnRTkZPZr6qyqRJ5nXR3IjvMCvAxzh7kmv9QV8E3XtWEPsF3SlJTDd6iZoxX7Wj4H+qUrdCA8QhAhtL5In01tEe1RfQIOvd21cn0eN2nsCEXvvXJsHir+3oR68xiJTlL6T4ma8ZzXNtHqPcLvzozPjlNszvmfZjpHzfMm/BJ/426GWkJKertlhq1rUG+MtY+AFNpgH/eQZt0TUIQIjkdmvOsCfMggR90XA0oyNxwCY0AliicNfmGQjkc2mmh2+wCyUWkjNrbjvSH3CuTd2Aof7KCPE0VeHKBY8gsUiS1WsWarrmvsxPFOA3aLDOUfVQbDld7r3idkcEIXvGWBEq8/5Skz8+f3TYHAM=', 'refresh_token': 'M.C557_SN1.0.U.-ClZDKrEkEmJWHPi7fGvHdtAAOXTLyTtDfZvMsFFkEsDjc48VgEIqgA29jA803wdFZLpXJYOI2MK4NG!bP4Y62jBFqWGiEGZr6ioA0*txZdkQVgdYncAWvGA4xHfZhLwW0tRZP42G7dmpJFQmI*OAizDTJ18QCMVcAD0L4nU990MzQFt5*07NFc6R28eSwQnwLj0NiKkknuLomafDjazWqhyuHeYxCUJ6d9D19rVFnSsJzMSz1gc!juWtrU1dFvPkV0eCdVPH0plO9OB2MOMy7EyvGvHmx!eps*Us7TconoEghCz*jxAn6Z*i8elckGuFWZoyYcXB2SBYeGcWX2u5ELMAna9eiGxAkZfh!HlfSaTMS5!GLTLSMLiTENAvl8ziODuaWcunWDHKZrUUKtt45kfpP3PRcyUGE9UQLNvYi7fM'}
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
    