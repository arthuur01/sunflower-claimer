import ast
import base64
import logging
from typing import Any, Dict, List, Optional, Tuple
import re

import requests

from mojang._http_client import _HTTPClient
from mojang._types import Profile, Skin, Cape, NameInformation
from mojang.errors import (
    MojangError,
    BadRequest,
    LoginFailure,
)

from mojang._utils import _assert_valid_username


_log = logging.getLogger(__name__)


_BASE_API_URL = "https://api.minecraftservices.com"


class MojangAuth(_HTTPClient):
    # Potential Xbox Live login failure errors
    _XERRORS = {
        2148916233: "The account doesn't have an Xbox account.",
        2148916235: "The account is from a country where Xbox Live is not available/banned.",
        2148916236: "The account needs adult verification on Xbox page. (South Korea)",
        2148916237: "The account needs adult verification on Xbox page. (South Korea)",
        2148916238: "The account is a child (under 18) and cannot proceed unless the account is added to a Family by an adult.",
    }

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        bearer_token: Optional[str] = None,
        session: Optional[requests.Session] = None,
        retry_on_ratelimit: Optional[bool] = False,
        ratelimit_sleep_time: Optional[int] = 60,
        debug_mode: Optional[bool] = False,
        token_final: Optional[requests.Session] = None,
    ):
        super().__init__(session, retry_on_ratelimit, ratelimit_sleep_time, debug_mode)

        self.email = email
        self.password = password
        self.bearer_token = bearer_token
        self.token_final = token_final

        if bearer_token:
            self._set_authorization_header(bearer_token)
        elif email is None and password is None:
            raise TypeError(
                "Either an email/password or bearer token must be supplied."
            )
        else:
           
            self._login()
            
        
        


    def _validate_session(self) -> None:
        resp = self.request(
            "get", f"{_BASE_API_URL}/entitlements/mcstore", ignore_codes=[401]
        )

        # The response content is empty if the authorization token isn't set or valid
        if not resp.text:
            raise LoginFailure("The bearer token is invalid.")

        

        data = resp.json()

    def _get_oauth2_token_and_url(self) -> Tuple[str, str]:
        """Begins the Microsoft OAuth2 Flow"""
        params = {
            "client_id": "000000004C12AE6F",
            "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
            "scope": "service::user.auth.xboxlive.com::MBI_SSL",
            "display": "touch",
            "response_type": "token",
            "locale": "en",
        }

        resp = self.request(
            "get", "https://login.live.com/oauth20_authorize.srf", params=params
        )

        # Parses the values via regex since the HTML can't be parsed
        value = re.search(r'value="(.+?)"', resp.text)[0].replace('value="', "")[:-1]
        url = re.search(r"urlPost:'(.+?)'", resp.text)[0].replace("urlPost:'", "")[:-1]

        return value, url

    def _authenticate_with_microsoft(self, token: str, url: str) -> Tuple[str, str]:
        """Authenticates with Microsoft"""
        payload = {
            "login": self.email,
            "loginfmt": self.email,
            "passwd": self.password,
            "PPFT": token,
        }

        resp = self.request("post", url, data=payload)
        if "access_token" not in resp.url:
            raise LoginFailure

        raw_login_data = resp.url.split("#")[1]
        data = dict(item.split("=") for item in raw_login_data.split("&"))

        access_token = requests.utils.unquote(data["access_token"])
        refresh_token = requests.utils.unquote(data["refresh_token"])

        return access_token, refresh_token

    def _authenticate_with_xboxlive(self, access_token: str) -> Tuple[str, str]:
        """Authenticates with XBL"""
        json_data = {
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": access_token,
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
        }

        resp = self.request(
            "post", "https://user.auth.xboxlive.com/user/authenticate", json=json_data
        )

        xbl_token = resp.json()["Token"]
        user_hash = resp.json()["DisplayClaims"]["xui"][0]["uhs"]

        return xbl_token, user_hash

    def _get_xsts_token(self, xbl_token: str) -> str:
        """Gets the XSTS token which is required to authenticate with Minecraft services"""
        json_data = {
            "Properties": {"SandboxId": "RETAIL", "UserTokens": [xbl_token]},
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT",
        }

        resp = self.request(
            "post",
            "https://xsts.auth.xboxlive.com/xsts/authorize",
            ignore_codes=[401],
            json=json_data,
        )

        if resp.status_code == 401:
            data = resp.json()
            if data.get("XErr"):
                if data["XErr"] in self._XERRORS:
                    raise LoginFailure(data["XErr"])
            raise MojangError(response=resp)

        return resp.json()["Token"]

    def _authenticate_with_minecraft(self, user_hash, xsts_token):
        json_payload = {
            "identityToken": f"XBL3.0 x={user_hash};{xsts_token}",
            "ensureLegacyEnabled": True,
        }

        resp = self.request(
            "post",
            f"{_BASE_API_URL}/authentication/login_with_xbox",
            json=json_payload,
        )

        return resp.json()
    def _login(self):
        token, url = self._get_oauth2_token_and_url()
        access_token, refresh_token = self._authenticate_with_microsoft(token, url)
        xbl_token, user_hash = self._authenticate_with_xboxlive(access_token)
        xsts_token = self._get_xsts_token(xbl_token)
        data = self._authenticate_with_minecraft(user_hash, xsts_token)


        self.bearer_token = data["access_token"]
        
        