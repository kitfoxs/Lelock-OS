"""Published provider routes. Credentials remain inside the provider's unmodified client."""
from __future__ import annotations
import shutil

PROVIDERS={
 'sillytavern': {'label':'Keep SillyTavern model','kind':'host_tools','login':'SillyTavern configuration','account_chat':False},
 'codex': {'label':'ChatGPT / Codex','kind':'official_app_server','binary':'codex','login':'browser_or_device','account_chat':True},
 'antigravity': {'label':'Google Antigravity','kind':'native_headless','binary':'agy','login':'native_cli','account_chat':True,
   'warning':'Native runtime has its own tools and permissions. It is not fully contained by Lelock policy.'},
 'claude-code': {'label':'Claude Code — native application','kind':'native_only','binary':'claude','login':'native_cli','account_chat':False,
   'warning':'Native sign-in is supported. This application does not proxy Claude subscription credentials into Tavern chat.'},
 'opencode': {'label':'OpenCode — native application','kind':'native_only','binary':'opencode','login':'native_cli','account_chat':False},
 'hermes': {'label':'Hermes — existing standalone runtime','kind':'native_only','binary':'hermes','login':'native_cli','account_chat':False},
}

def catalog():
    return [{"id":k,**v,"installed":bool(shutil.which(v['binary'])) if 'binary'in v else True} for k,v in PROVIDERS.items()]

def native_login_command(provider):
    # Fixed operator commands, not shell strings supplied by cards or models.
    return {'antigravity':['agy'],'claude-code':['claude'],'opencode':['opencode','auth','login'],
            'hermes':['hermes','model']}[provider]
