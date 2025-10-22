import webbrowser
import json
from confings.Consts import PathsConsts

def get_access_token(client_id: int, scope: int) -> None:
    assert isinstance(client_id, int), 'clinet_id must be positive integer'
    assert isinstance(scope, str), 'scope must be string'
    assert client_id > 0, 'clinet_id must be positive integer'
    url = """\
    https://oauth.vk.com/authorize?client_id={client_id}&\
    group_ids=[!ids!]?\
    redirect_uri=https://oauth.vk.com/blank.hmtl&\
    scope={scope}&\
    &response_type=token&\
    display=page\
    """.replace(" ", "").format(client_id=client_id, scope=scope)
    # Работа для Chrome. Можно вызывать и просто браузер по умолчанию
    print(url)
    #webbrowser.open_new_tab(url)

def get():
    tmp_dict = json.load(open(PathsConsts.PRIVATES_PATH, 'r'))
    get_access_token(tmp_dict['app_id'], tmp_dict['rights'])