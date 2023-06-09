from ua_parser import user_agent_parser
from ua_parser.user_agent_parser import (
    USER_AGENT_PARSERS,
    OS_PARSERS,
    DEVICE_PARSERS,
    UserAgentParser,
    DeviceParser
)


# Snote/0.0.1 iOS/16.4.1 (device)

USER_AGENT_PARSERS.insert(0,UserAgentParser(r"^((?i)snote)\/(\d+)\.(\d+).(\d+)",'app'))
DEVICE_PARSERS.insert(0,DeviceParser(r"snote.*\((.*)\)$"))

def parse(ua):
    parsed = user_agent_parser.Parse(ua)
    client_type = 'app'
    if parsed['user_agent']['family']!='app':
        client_type='web'
    client_version = (0,0,0)
    if client_type!='web':
        client_version = (
            parsed['user_agent']['major'],
            parsed['user_agent']['minor'],
            parsed['user_agent']['patch']
        )
    os = parsed['os']['family']
    return client_type,client_version,os

def version_to_number(version):
    return version[0]*10000+version[1]*100+version[2]

def version_from_number(number):
    number_str = str(number)
    number_str = number_str.rjust(6,'0')
    return (
        int(number_str[:-4]),
        int(number_str[-4:-2]),
        int(number_str[-2:])
    )