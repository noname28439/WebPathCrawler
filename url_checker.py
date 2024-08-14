import validators

def check_url_vadidity(url:str):
    return validators.url(url)