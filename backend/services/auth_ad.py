import ldap3
import httpx, logging, asyncio
from core.config import settings

log = logging.getLogger(__name__)

def authenticate_user(username: str, password: str) -> dict | None:
    """
    Autentica contra Active Directory usando dominio y credenciales.
    Devuelve 'DOMINIO\\USER' si es válido, None si no.
    """

    server = ldap3.Server(settings.AD_SERVER, get_info=ldap3.NONE, connect_timeout=5)
    user_dn = f"{username}@{settings.AD_DOMAIN}"

    log.info(f"Login → {user_dn} @ {settings.AD_SERVER}")

    try:
        conn = ldap3.Connection(server, user=user_dn, password=password, authentication=ldap3.SIMPLE, auto_bind=True)        
        log.info(f"Connection LDAP → {conn.authentication}")
        
        if not conn.bind():
            log.error(f"Bind error: {conn.result}")
            return None

        search_filter = f"(sAMAccountName={username})"
        search_base = settings.AD_SEARCH_BASE

        conn.search(
            search_base=search_base,
            search_filter=search_filter,
            attributes=['cn', 'displayName', 'givenName', 'sn', 'sAMAccountName', 'mail']
        )

        if not conn.entries:
            log.warning(f"No se encontró usuario: {username}")
            conn.unbind()
            return None

        user_entry = conn.entries[0]

        display_name = str(user_entry.displayName) if 'displayName' in user_entry else None
        cn = str(user_entry.cn) if 'cn' in user_entry else None
        given_name = str(user_entry.givenName) if 'givenName' in user_entry else None
        sn = str(user_entry.sn) if 'sn' in user_entry else None
        name = display_name or cn or f"{given_name} {sn}".strip()

        user_info = {
            'user': username.lower(),
            'username': name,
            'mail': str(user_entry.mail) if 'mail' in user_entry else None
        }

        log.info(f"Autenticación exitosa → Usuario: {username}, Nombre: {name}")
        conn.unbind()
        return user_info
    except Exception as e:
        log.error(f"LDAP error: {e}")
        return None


