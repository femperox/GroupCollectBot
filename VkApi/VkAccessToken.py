import webbrowser
import json
import os

def get_access_token(client_id: int, scope: int) -> None:
    assert isinstance(client_id, int), 'clinet_id must be positive integer'
    assert isinstance(scope, str), 'scope must be string'
    assert client_id > 0, 'clinet_id must be positive integer'
    url = """\
    https://oauth.vk.com/authorize?client_id={client_id}&\
    redirect_uri=https://oauth.vk.com/blank.hmtl&\
    scope={scope}&\
    &response_type=token&\
    display=page\
    """.replace(" ", "").format(client_id=client_id, scope=scope)
    # Работа для Chrome. Можно вызывать и просто браузер по умолчанию
    webbrowser.open_new_tab(url)

tmp_dict = json.load(open(os.getcwd()+'/confings/privates.json', 'r'))
get_access_token(tmp_dict['app_id'], tmp_dict['rights'])