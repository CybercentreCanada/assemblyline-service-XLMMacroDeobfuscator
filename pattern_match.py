import re
from os import path
from xml.etree import ElementTree

from fuzzywuzzy import process


def get_xml_strings():
    pest_minlen = 6

    api = {}
    blacklist = {}
    powershell = {}

    with open(path.join(path.dirname(__file__), "pestudio/xml/strings.xml"), 'rt') as f:
        tree = ElementTree.parse(f)

    for st in tree.findall('.//agent'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('agent', set()).add(st.text)
    for st in tree.findall('.//av'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('av', set()).add(st.text)
    for st in tree.findall('.//event'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('event', set()).add(st.text)
    for st in tree.findall('.//guid'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('guid', set()).add(st.text)
    for st in tree.findall('.//insult'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('insult', set()).add(st.text)
    for st in tree.findall('.//key'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('key', set()).add(st.text)
    for st in tree.findall('.//oid'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('oid', set()).add(st.text)
    for st in tree.findall('.//os'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('os', set()).add(st.text)
    for st in tree.findall('.//priv'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('priv', set()).add(st.text)
    for st in tree.findall('.//product'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('product', set()).add(st.text)
    for st in tree.findall('.//protocol'):
        blacklist.setdefault('protocol', set()).add(st.text)
    for st in tree.findall('.//reg'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('reg', set()).add(st.text)
    for st in tree.findall('.//sid'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('sid', set()).add(st.text)
    for st in tree.findall('.//string'):
        if len(st.text) > pest_minlen:
            blacklist.setdefault('string', set()).add(st.text)
    # Powershell indicator strings
    for st in tree.findall('.//powershell'):
        if len(st.text) > pest_minlen:
            powershell.setdefault('powershell', set()).add(st.text)

    # Adding Popular API
    with open(path.join(path.dirname(__file__), 'pestudio/xml/functions.xml'), 'rt') as f:
        tree = ElementTree.parse(f)

    for st in tree.findall(".//fct"):
        if st.text is not None:
            if len(st.text) > pest_minlen and st.text is not None:
                api.setdefault('fct', set()).add(st.text.split('::', 1)[0])
    for st in tree.findall(".//lib"):
        if st.attrib['name'] is not None:
            if len(st.attrib['name']) > pest_minlen:
                api.setdefault('lib', set()).add(st.attrib['name'])
    for st in tree.findall('.//topapi'):
        if st.text is not None:
            if len(st.text) > pest_minlen:
                api.setdefault('topapi', set()).add(st.text)

    return api, blacklist, powershell


class PatternMatch(object):
    # Curated list to avoid false positives.
    TDLS = {'ac', 'aco', 'ad', 'adac', 'ads', 'ae', 'aeg', 'aero', 'af', 'afl', 'ag', 'agakhan', 'ai',
            'aig', 'akdn', 'al', 'am', 'amica', 'anz', 'ao', 'apple', 'aq', 'ar', 'army', 'arpa', 'at',
            'au', 'aw', 'aws', 'ax', 'axa', 'az', 'ba', 'baidu', 'bbc', 'bbva', 'bcg', 'bcn', 'bd', 'be',
            'bf', 'bg', 'bh', 'bharti', 'bi', 'bing', 'biz', 'bj', 'blog', 'bm', 'bms', 'bn', 'bnl', 'bo',
            'bom', 'bot', 'br', 'bs', 'bt', 'bv', 'bw', 'by', 'bz', 'bzh', 'ca', 'cba', 'cbn', 'cbre',
            'ceb', 'cf', 'cfa', 'cfd', 'cg', 'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'com', 'cr',
            'crs', 'csc', 'cu', 'cv', 'cw', 'cx', 'cy', 'cz', 'dclk', 'dds', 'de', 'dev', 'dhl', 'dj',
            'dk', 'dm', 'dnp', 'do', 'docs', 'doha', 'domains', 'download', 'drive', 'dtv', 'dubai', 'dvag',
            'dz', 'ec', 'edu', 'er', 'erni', 'es', 'esq', 'et', 'eu', 'eurovision', 'eus', 'fi', 'fj',
            'fk', 'flickr', 'flir', 'flsmidth', 'fly', 'fm', 'fo', 'foo', 'fr', 'frl', 'ftr', 'ga', 'gb',
            'gbiz', 'gd', 'gdn', 'ge', 'gea', 'gl', 'gle', 'gm', 'gmail', 'gmbh', 'gmo', 'gmx', 'gn',
            'goog', 'google', 'gop', 'got', 'gov', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'guru', 'gw', 'gy',
            'hk', 'hkt', 'hm', 'hn', 'host', 'hotmail', 'hr', 'ht', 'htc', 'hu', 'icu', 'id', 'ie',
            'ifm', 'iinet', 'ikano', 'il', 'im', 'imamat', 'imdb', 'immo', 'immobilien', 'in', 'info',
            'ing', 'ink', 'int', 'io', 'ipiranga', 'iq', 'ir', 'is', 'ist', 'istanbul', 'it', 'itau',
            'itv', 'iwc', 'jaguar', 'jcb', 'jcp', 'je', 'jlc', 'jll', 'jm', 'jmp', 'jnj', 'jo', 'jot',
            'jp', 'ke', 'kfh', 'kg', 'kh', 'ki', 'kia', 'kindle', 'km', 'kn', 'kp', 'kpmg', 'kpn', 'kr',
            'krd', 'kw', 'ky', 'kyoto', 'kz', 'la', 'lat', 'lb', 'lc', 'lds', 'li', 'link', 'lk', 'lol',
            'lr', 'ls', 'lt', 'ltd', 'ltda', 'lu', 'lv', 'ly', 'ma', 'madrid', 'mba', 'mc', 'md', 'me',
            'med', 'meme', 'meo', 'mg', 'mh', 'microsoft', 'mil', 'mk', 'ml', 'mlb', 'mls', 'mma',
            'mn', 'mo', 'mobi', 'mobily', 'mov', 'mp', 'mq', 'mr', 'ms', 'mt', 'mtn', 'mtpc', 'mtr',
            'mu', 'mv', 'mw', 'mx', 'my', 'mz', 'na', 'navy', 'nc', 'ne', 'nec', 'net', 'netbank',
            'neustar', 'nexus', 'nf', 'ng', 'ngo', 'nhk', 'ni', 'nico', 'nl', 'nowruz', 'nowtv', 'np',
            'nr', 'nra', 'nrw', 'ntt', 'nu', 'nyc', 'nz', 'obi', 'ollo', 'om', 'ong', 'onl', 'org', 'ott',
            'ovh', 'pa', 'pccw', 'pe', 'pet', 'pf', 'pg', 'ph', 'pid', 'pin', 'ping', 'pk', 'pl', 'pm',
            'pn', 'pnc', 'pohl', 'porn', 'post', 'pr', 'pro', 'prod', 'ps', 'pt', 'pub', 'pw', 'pwc',
            'py', 'qa', 'qpon', 'quebec', 're', 'ren', 'rio', 'ro', 'rocher', 'rs', 'rsvp', 'ru', 'ruhr',
            'rw', 'rwe', 'ryukyu', 'sa', 'sap', 'sapo', 'sarl', 'sas', 'saxo', 'sb', 'sbi', 'sbs',
            'sc', 'sca', 'scb', 'sd', 'se', 'sew', 'sex', 'sfr', 'sg', 'sh', 'si', 'sina', 'site',
            'sj', 'sk', 'skype', 'sl', 'sm', 'sn', 'sncf', 'so', 'sr', 'srl', 'st', 'stc', 'stcgroup',
            'su', 'sv', 'sx', 'sy', 'sydney', 'symantec', 'systems', 'sz', 'tab',
            'taipei', 'taobao', 'tc', 'tci', 'td', 'tdk', 'tel', 'teva', 'tf', 'tg', 'th', 'thd', 'tj',
            'tk', 'tl', 'tm', 'tmall', 'tn', 'to', 'tokyo', 'tr', 'trv', 'tt', 'tube', 'tui', 'tunes',
            'tushu', 'tv', 'tw', 'tz', 'ua', 'ubs', 'ug', 'uk', 'uno', 'uol', 'ups', 'us', 'uy', 'uz',
            'va', 'vc', 've', 'vet', 'vg', 'vi', 'vig', 'vin', 'vip', 'vista', 'vistaprint', 'vn',
            'vu', 'wed', 'weibo', 'weir', 'wf', 'whoswho', 'wien', 'wiki', 'win', 'windows', 'wme', 'ws',
            'wtc', 'wtf', 'xbox', 'xerox', 'xihuan', 'xin', 'xn--11b4c3d', 'xn--1ck2e1b',
            'xn--1qqw23a', 'xn--30rr7y', 'xn--3bst00m', 'xn--3ds443g', 'xn--3e0b707e', 'xn--3pxu8k',
            'xn--42c2d9a', 'xn--45brj9c', 'xn--45q11c', 'xn--4gbrim', 'xn--55qw42g', 'xn--55qx5d',
            'xn--5su34j936bgsg', 'xn--5tzm5g', 'xn--6frz82g', 'xn--6qq986b3xl', 'xn--80adxhks',
            'xn--80ao21a', 'xn--80asehdb', 'xn--80aswg', 'xn--8y0a063a', 'xn--90a3ac', 'xn--90ae',
            'xn--90ais', 'xn--9dbq2a', 'xn--9et52u', 'xn--9krt00a', 'xn--b4w605ferd', 'xn--bck1b9a5dre4c',
            'xn--c1avg', 'xn--c2br7g', 'xn--cck2b3b', 'xn--cg4bki', 'xn--clchc0ea0b2g2a9gcd',
            'xn--czr694b', 'xn--czrs0t', 'xn--czru2d', 'xn--d1acj3b', 'xn--d1alf', 'xn--e1a4c',
            'xn--eckvdtc9d', 'xn--efvy88h', 'xn--estv75g', 'xn--fct429k', 'xn--fhbei', 'xn--fiq228c5hs',
            'xn--fiq64b', 'xn--fiqs8s', 'xn--fiqz9s', 'xn--fjq720a', 'xn--flw351e', 'xn--fpcrj9c3d',
            'xn--fzc2c9e2c', 'xn--fzys8d69uvgm', 'xn--g2xx48c', 'xn--gckr3f0f', 'xn--gecrj9c',
            'xn--h2brj9c', 'xn--hxt814e', 'xn--i1b6b1a6a2e', 'xn--imr513n', 'xn--io0a7i', 'xn--j1aef',
            'xn--j1amh', 'xn--j6w193g', 'xn--jlq61u9w7b', 'xn--jvr189m', 'xn--kcrx77d1x4a', 'xn--kprw13d',
            'xn--kpry57d', 'xn--kpu716f', 'xn--kput3i', 'xn--l1acc', 'xn--lgbbat1ad8j', 'xn--mgb9awbf',
            'xn--mgba3a3ejt', 'xn--mgba3a4f16a', 'xn--mgba7c0bbn0a', 'xn--mgbaam7a8h', 'xn--mgbab2bd',
            'xn--mgbayh7gpa', 'xn--mgbb9fbpob', 'xn--mgbbh1a71e', 'xn--mgbc0a9azcg', 'xn--mgbca7dzdo',
            'xn--mgberp4a5d4ar', 'xn--mgbpl2fh', 'xn--mgbt3dhd', 'xn--mgbtx2b', 'xn--mgbx4cd0ab',
            'xn--mix891f', 'xn--mk1bu44c', 'xn--mxtq1m', 'xn--ngbc5azd', 'xn--ngbe9e0a', 'xn--node',
            'xn--nqv7f', 'xn--nqv7fs00ema', 'xn--nyqy26a', 'xn--o3cw4h', 'xn--ogbpf8fl', 'xn--p1acf',
            'xn--p1ai', 'xn--pbt977c', 'xn--pgbs0dh', 'xn--pssy2u', 'xn--q9jyb4c', 'xn--qcka1pmc',
            'xn--qxam', 'xn--rhqv96g', 'xn--rovu88b', 'xn--s9brj9c', 'xn--ses554g', 'xn--t60b56a',
            'xn--tckwe', 'xn--unup4y', 'xn--vermgensberater-ctb', 'xn--vermgensberatung-pwb', 'xn--vhquv',
            'xn--vuq861b', 'xn--w4r85el8fhu5dnra', 'xn--w4rs40l', 'xn--wgbh1c', 'xn--wgbl6a',
            'xn--xhq521b', 'xn--xkc2al3hye2a', 'xn--xkc2dl3a5ee0h', 'xn--y9a3aq', 'xn--yfro4i67o',
            'xn--ygbi2ammx', 'xn--zfr164b', 'xperia', 'xyz', 'yahoo', 'yamaxun',
            'yandex', 'ye', 'yokohama', 'you', 'youtube', 'yt', 'yun', 'za', 'zappos',
            'zara', 'zero', 'zippo', 'zm', 'zone', 'zuerich', 'zw'}

    # --- PEStudio Patterns ------------------------------------------------------------------------------------------------

    PEST_API, PEST_BLACKLIST, PEST_POWERSHELL = get_xml_strings()

    # --- Regex Patterns ---------------------------------------------------------------------------------------------------

    PAT_DOMAIN = r'(?i)\b(?:[A-Z0-9-]+\.)+(?:XN--[A-Z0-9]{4,18}|[A-Z]{2,12})\b'
    PAT_FILECOM = r'(?i)(?:\b[a-z]?[:]?[- _A-Z0-9.\\~]{0,75}[%]?' \
                  r'(?:ALLUSERPROFILE|APPDATA|commonappdata|CommonProgramFiles|HOMEPATH|LOCALAPPDATA|' \
                  r'ProgramData|ProgramFiles|PUBLIC|SystemDrive|SystemRoot|\\TEMP|USERPROFILE|' \
                  r'windir|system32|syswow64|\\user)[%]?\\[-_A-Z0-9\.\\]{1,200}\b|' \
                  r'/home/[-_A-Z0-9\./]{0,50}|/usr/local[-_A-Z0-9\./]{0,50}|/usr/bin[-_A-Z0-9\./]{0,50}|' \
                  r'/var/log[-_A-Z0-9\./]{0,50}|/etc/(?:shadow|group|passwd))'
    PAT_FILEEXT = r'(?i)\b[a-z]?[:]?[- _A-Z0-9.\\~]{0,200}\w\.' \
                  r'(?:7Z|APK|APP|BAT|BIN|CLASS|CMD|DAT|DOC|DOCX|DLL|EML|EXE|JAR|JPEG|JPG|JS|JSE|LNK|LOG|MSI|' \
                  r'OSX|PAF|PDF|PNG|PPT|PPTX|PS1|RAR|RTF|SCR|SWF|SYS|[T]?BZ[2]?|TXT|TMP|VBE|VBS|WSF|WSH|XLS' \
                  r'|XLSX|ZIP)\b'
    PAT_FILEPDB = r'(?i)\b[-_A-Z0-9.\\]{0,200}\w\.PDB\b'
    PAT_EMAIL = r'(?i)\b[A-Z0-9._%+-]{3,}@(?:[A-Z0-9-]+\.)+(?:XN--[A-Z0-9]{4,18}|[A-Z]{2,12})\b'
    PAT_IP = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    PAT_REGIS = r'(?i)\b[- _A-Z0-9.\\]{0,25}' \
                r'(?:controlset001|controlset002|currentcontrolset|currentversion|HKCC|HKCR|HKCU|HKDD|' \
                r'hkey_classes_root|hkey_current_config|hkey_current_user|hkey_dyn_data|hkey_local_machine|' \
                r'HKLM|hkey_performance_data|hkey_users|HKPD|internet settings|\\sam|\\software|\\system|' \
                r'\\userinit)' \
                r'\\[-_A-Z0-9.\\ ]{1,200}\b'
    PAT_URL = r'(?i)(?:ftp|http|https)://' \
              r'[A-Z0-9.-]{1,}\.(?:XN--[A-Z0-9]{4,18}|[a-z]{2,12}|[0-9]{1,3})' \
              r'(?::[0-9]{1,5})?' \
              r'(?:/[A-Z0-9/\-\.&%\$#=~\?_+]{3,200}){0,1}'
    PAT_ANYHTTP = r'(?i)http://' \
                  r'[A-Z0-9.-]{6,}\.' \
                  r'(?:XN--[A-Z0-9]{4,18}|[a-z]{2,12}|[0-9]{1,3})' \
                  r'(?::[0-9]{1,5})?' \
                  r'/[A-Z0-9/\-\.&%\$#=~\?_+]{5,}[\r\n]*'
    PAT_ANYHTTPS = r'(?i)https://' \
                   r'[A-Z0-9.-]{6,}\.' \
                   r'(?:XN--[A-Z0-9]{4,18}|[a-z]{2,12}|[0-9]{1,3})' \
                   r'(?::[0-9]{1,5})?' \
                   r'/[A-Z0-9/\-\.&%\$#=~\?_+]{5,}[\r\n]*'
    PAT_ANYFTP = r'(?i)ftp://' \
                 r'[A-Z0-9.-]{6,}\.' \
                 r'(?:XN--[A-Z0-9]{4,18}|[a-z]{2,12}|[0-9]{1,3})' \
                 r'(?::[0-9]{1,5})?' \
                 r'/[A-Z0-9/\-\.&%\$#=~\?_+]{5,}[\r\n]*'

    PAT_EXEDOS = r'This program cannot be run in DOS mode'
    PAT_EXEHEADER = r'(?s)MZ.{32,1024}PE\000\000'

    # --- Find Match for IOC Regex, Return Dictionary: {[AL Tag Type:(Match Values)]} --------------------------------------

    def ioc_match(self, formula, cell, ioc_dict, bogon_ip=None, just_network=None):
        # NOTES:
        # '(?i)' makes a regex case-insensitive
        # \b matches a word boundary, it can help speeding up regex search and avoiding some false positives.
        # See http://www.regular-expressions.info/wordboundaries.html
        ioc_found = False

        # ------------------------------------------------------------------------------
        # IP ADDRESSES
        # Pattern_re("IP addresses", r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", weight=10),
        # Here I use \b to make sure there is no other digit around and to speedup search
        # print("ips")
        find_ip = re.findall(self.PAT_IP, formula)
        if len(find_ip) > 0:
            longest_string = max(find_ip, key=len)
            if len(longest_string) == len(formula):
                not_filtered = self.ipv4_filter(formula, bogon=bogon_ip)
                if not_filtered:
                    ioc_dict.setdefault('network.static.ip', set()).add((formula, 'IP Addresses', 1, cell))
                    ioc_found = True
                # If the complete value matches the IP regex, not interested in other regex values
                return ioc_found
            if len(find_ip) == 1:
                for val in find_ip:
                    not_filtered = self.ipv4_filter(val, bogon=bogon_ip)
                    if not_filtered:
                        ioc_dict.setdefault('network.static.ip', set()).add((val, 'IP Addresses', 1, cell))
                        ioc_found = True
            else:
                like_ls = process.extract(str(longest_string), find_ip, limit=50)
                final_values = list(filter(lambda ls: ls[1] < 99, like_ls))
                final_values.append((longest_string, 100))
                for val in final_values:
                    not_filtered = self.ipv4_filter(val[0], bogon=bogon_ip)
                    if not_filtered:
                        ioc_dict.setdefault('network.static.ip', set()).add((val[0], 'IP Addresses', 1, cell))
                        ioc_found = True
        # ------------------------------------------------------------------------------
        # URLs
        # print("urls")
        find_url = re.findall(self.PAT_URL, formula)
        if len(find_url) > 0:
            ret = False
            longest_string = max(find_url, key=len)
            if len(longest_string) == len(formula):
                ret = True
                final_values = [(formula, 100)]
            elif len(find_url) == 1:
                final_values = [(find_url[0], 100)]
            else:
                like_ls = process.extract(str(longest_string), find_url, limit=50)
                final_values = list(filter(lambda ls: ls[1] < 95, like_ls))
                final_values.append((longest_string, 100))

            for val in final_values:
                ioc_dict.setdefault('network.static.uri', set()).add((val[0], 'URLs', 1, cell))
                ioc_found = True

                # Extract domain from URL
                find_domain = re.findall(self.PAT_DOMAIN, val[0])
                if len(find_domain) != 0:
                    longest_string = max(find_domain, key=len)
                    not_filtered = self.domain_filter(longest_string)
                    if not_filtered:
                        ioc_dict.setdefault('network.static.domain', set()).add(
                            (longest_string, 'Domain Names', 1, cell))
                        ioc_found = True
            if ret:
                return ioc_found

        # ------------------------------------------------------------------------------
        # E-MAIL ADDRESSES
        # r'(?i)\b[A-Z0-9._%+-]+@(?:[A-Z0-9-]+\.)+(?:[A-Z]{2}|com|org|net|edu|gov|mil|int|biz|info|mobi|name|aero|asia|jobs|museum)\b',
        # changed to catch all current TLDs registered at IANA (in combination with filter function):
        # TLD = either only chars from 2 to 12, or 'XN--' followed by up to 18 chars and digits
        # print("emails")
        find_email = re.findall(self.PAT_EMAIL, formula)
        if len(find_email) > 0:
            longest_string = max(find_email, key=len)
            if len(longest_string) == len(formula):
                not_filtered = self.email_filter(formula)
                if not_filtered:
                    ioc_dict.setdefault('network.email.address', set()).add((formula, 'Email Addresses', 1, cell))
                    ioc_found = True
                    return ioc_found
            if len(find_email) == 1:
                for val in find_email:
                    not_filtered = self.email_filter(val)
                    if not_filtered:
                        ioc_dict.setdefault('network.email.address', set()).add((val, 'Email Addresses', 1, cell))
                        ioc_found = True
            else:
                like_ls = process.extract(str(longest_string), find_email, limit=50)
                final_values = list(filter(lambda ls: ls[1] < 95, like_ls))
                final_values.append((longest_string, 100))
                for val in final_values:
                    not_filtered = self.email_filter(val[0])
                    if not_filtered:
                        ioc_dict.setdefault('network.email.address', set()).add((val[0], 'Email Addresses', 1, cell))
                        ioc_found = True

        # ------------------------------------------------------------------------------
        # Deobfuscated Domain Names
        # Old: r'(?=^.{1,254}$)(^(?:(?!\d+\.|-)[a-zA-Z0-9_\-]{1,63}(?<!-)\.?)+(?:[a-zA-Z]{2,})$)'
        # Below is taken from email regex above
        # print("domains")
        find_domain = re.findall(self.PAT_DOMAIN, formula)
        if len(find_domain) > 0 and len(max(find_domain, key=len)) > 11:
            longeststring = max(find_domain, key=len)
            if len(longeststring) == len(formula):
                not_filtered = self.domain_filter(formula)
                if not_filtered:
                    ioc_dict.setdefault('network.static.domain', set()).add((formula, 'Domain Names', 1, cell))
                    ioc_found = True
                    return ioc_found
            if len(find_domain) == 1:
                for val in find_domain:
                    not_filtered = self.domain_filter(val)
                    if not_filtered:
                        ioc_dict.setdefault('network.static.domain', set()).add((val, 'Domain Names', 1, cell))
                        ioc_found = True
            else:
                like_ls = process.extract(str(longeststring), find_domain, limit=50)
                final_values = list(filter(lambda ls: ls[1] < 95, like_ls))
                final_values.append((longeststring, 100))
                for val in final_values:
                    not_filtered = self.domain_filter(val[0])
                    if not_filtered:
                        ioc_dict.setdefault('network.static.domain', set()).add((val[0], 'Domain Names', 1, cell))
                        ioc_found = True

        if just_network:
            return ioc_found

        # ------------------------------------------------------------------------------
        # FILENAMES
        # Check length
        # Ends with extension of interest or contains strings of interest
        # print("files")
        filefind_pdb = re.findall(self.PAT_FILEPDB, formula)
        if len(filefind_pdb) > 0:
            if len(max(filefind_pdb, key=len)) > 6:
                longeststring = max(filefind_pdb, key=len)
                if len(longeststring) == len(formula):
                    ioc_dict.setdefault('file.pe.pdb_filename', set()).add((formula, 'Filenames', 0, cell))
                    ioc_found = True
                    return ioc_found
                if len(filefind_pdb) == 1:
                    for val in filefind_pdb:
                        ioc_dict.setdefault('file.pe.pdb_filename', set()).add((val, 'Filenames', 0, cell))
                        ioc_found = True
                else:
                    like_ls = process.extract(str(longeststring), filefind_pdb, limit=50)
                    final_values = list(filter(lambda ls: ls[1] < 95, like_ls))
                    final_values.append((longeststring, 100))
                    for val in final_values:
                        ioc_dict.setdefault('file.pe.pdb_filename', set()).add((val[0], 'Filenames', 0, cell))
                        ioc_found = True
        filefind_ext = re.findall(self.PAT_FILEEXT, formula)
        if len(filefind_ext) > 0:
            if len(max(filefind_ext, key=len)) > 6:
                longeststring = max(filefind_ext, key=len)
                if len(longeststring) == len(formula):
                    ioc_dict.setdefault('file.name.extracted', set()).add((formula, 'Filenames', 0, cell))
                    ioc_found = True
                    return ioc_found
                if len(filefind_ext) == 1:
                    for val in filefind_ext:
                        ioc_dict.setdefault('file.name.extracted', set()).add((val, 'Filenames', 0, cell))
                        ioc_found = True
                else:
                    like_ls = process.extract(str(longeststring), filefind_ext, limit=50)
                    final_values = list(filter(lambda ls: ls[1] < 95, like_ls))
                    final_values.append((longeststring, 100))
                    for val in final_values:
                        ioc_dict.setdefault('file.name.extracted', set()).add((val[0], 'Filenames', 0, cell))
                        ioc_found = True
        filefind_com = re.findall(self.PAT_FILECOM, formula)
        if len(filefind_com) > 0 and len(max(filefind_com, key=len)) > 6:
            longeststring = max(filefind_com, key=len)
            if len(longeststring) == len(formula):
                ioc_dict.setdefault('file.name.extracted', set()).add((formula, 'Filenames', 0, cell))
                ioc_found = True
                return ioc_found
            if len(filefind_com) == 1:
                for val in filefind_com:
                    ioc_dict.setdefault('file.name.extracted', set()).add((val, 'Filenames', 0, cell))
                    ioc_found = True
            else:
                like_ls = process.extract(str(longeststring), filefind_com, limit=50)
                final_values = list(filter(lambda ls: ls[1] < 95, like_ls))
                final_values.append((longeststring, 100))
                for val in final_values:
                    ioc_dict.setdefault('file.name.extracted', set()).add((val[0], 'Filenames', 0, cell))
                    ioc_found = True
        # ------------------------------------------------------------------------------
        # REGISTRYKEYS
        # Looks for alpha numeric characters seperated by at least two sets of '\'s
        # print("reg")
        regfind = re.findall(self.PAT_REGIS, formula)
        if len(regfind) > 0 and len(max(regfind, key=len)) > 15:
            longeststring = max(regfind, key=len)
            if len(longeststring) == len(formula):
                ioc_dict.setdefault('dynamic.registry_key', set()).add((formula, 'Registry Keys', 0, cell))
                ioc_found = True
                return ioc_found
            if len(regfind) == 1:
                for val in regfind:
                    ioc_dict.setdefault('dynamic.registry_key', set()).add((val, 'Registry Keys', 0, cell))
                    ioc_found = True
            else:
                like_ls = process.extract(str(longeststring), regfind, limit=50)
                final_values = list(filter(lambda ls: ls[1] < 90, like_ls))
                final_values.append((longeststring, 100))
                for val in final_values:
                    ioc_dict.setdefault('dynamic.registry_key', set()).add((val[0], 'Registry Keys', 0, cell))
                    ioc_found = True
        # ------------------------------------------------------------------------------
        # PEStudio Blacklist
        # Flags strings from PEStudio's Blacklist
        final_values = []
        for k, i in self.PEST_BLACKLIST.items():
            for e in i:
                if e in formula:
                    final_values.append(e)
        for val in final_values:
            ioc_dict.setdefault('file.string.blacklisted', set()).add((val, 'PEStudio Blacklisted Strings', 0, cell))
            ioc_found = True
        # -----------------------------------------------------------------------------
        # Function/Library Strings
        # Win API strings from PEStudio's Blacklist
        final_values = []
        for k, i in self.PEST_API.items():
            for e in i:
                if e in formula:
                    final_values.append(e)
        for val in final_values:
            ioc_dict.setdefault('file.string.api', set()).add((val, 'Function/Library Strings', 0, cell))
            ioc_found = True
        # -----------------------------------------------------------------------------
        # Powershell Strings
        # Powershell Cmdlets added to PEStudio's strings.xml list
        final_values = []
        for k, i in self.PEST_POWERSHELL.items():
            for e in i:
                if e in formula:
                    final_values.append(e)
        for val in final_values:
            ioc_dict.setdefault('file.powershell.cmdlet', set()).add((val, 'Powershell Strings', 0, cell))
            ioc_found = True

        return ioc_found

    # --- Filters ----------------------------------------------------------------------------------------------------------

    @staticmethod
    def ipv4_filter(value, bogon=None, **_):
        """
        IPv4 address filter:
        - check if string length is >7 (e.g. not just 4 digits and 3 dots)
        - check if not in list of bogon IP addresses
        return True if OK, False otherwise.
        """
        ip = value

        # 0.0.0.0 255.0.0.0e
        # > 255
        if ip.startswith('0'):
            return False
        for x in ip.split('.'):
            if int(x) > 255:
                return False

        # also reject IPs ending with .0 or .255
        if ip.endswith('.0') or ip.endswith('.255'):
            return False

        # BOGON IP ADDRESS RANGES:
        # source: http://www.team-cymru.org/Services/Bogons/bogon-dd.html

        if bogon is not None:
            # extract 1st and 2nd decimal number from IP as int:
            ip_bytes = ip.split('.')
            byte1 = int(ip_bytes[0])
            byte2 = int(ip_bytes[1])
            # print 'ip=%s byte1=%d byte2=%d' % (ip, byte1, byte2)

            # actually we might want to see the following bogon IPs if malware uses them
            # => this should be an option
            # 10.0.0.0 255.0.0.0
            if ip.startswith('10.'):
                return False
            # 100.64.0.0 255.192.0.0
            if ip.startswith('100.') and (byte2 & 192 == 64):
                return False
            # 127.0.0.0 255.0.0.0
            if ip.startswith('127.'):
                return False
            # 169.254.0.0 255.255.0.0
            if ip.startswith('169.254.'):
                return False
            # 172.16.0.0 255.240.0.0
            if ip.startswith('172.') and (byte2 & 240 == 16):
                return False
            # 192.0.0.0 255.255.255.0
            if ip.startswith('192.0.0.'):
                return False
            # 192.0.2.0 255.255.255.0
            if ip.startswith('192.0.2.'):
                return False
            # 192.168.0.0 255.255.0.0
            if ip.startswith('192.168.'):
                return False
            # 198.18.0.0 255.254.0.0
            if ip.startswith('198.') and (byte2 & 254 == 18):
                return False
            # 198.51.100.0 255.255.255.0
            if ip.startswith('198.51.100.'):
                return False
            # 203.0.113.0 255.255.255.0
            if ip.startswith('203.0.113.'):
                return False
            # 224.0.0.0 240.0.0.0
            if byte1 & 240 == 224:
                return False
            # 240.0.0.0 240.0.0.0
            if byte1 & 240 == 240:
                return False

        # otherwise it's a valid IP address
        return True

    def email_filter(self, value, **_):
        # check length, e.g. longer than xy@hp.fr
        # check case? e.g. either lower, upper, or capital (but CamelCase covers
        # almost everything... the only rejected case would be starting with lower
        # and containing upper?)
        # or reject mixed case in last part of domain name? (might filter 50% of
        # false positives)
        # optionally, DNS MX query with caching?

        user, domain = value.split('@', 1)
        if len(user) < 3:
            return False
        if len(domain) < 5:
            return False
        tld = domain.rsplit('.', 1)[1].lower()
        if str(tld) not in self.TDLS:
            return False

        return True

    def domain_filter(self, value, **_):
        # check length
        # check match again tlds set
        if len(value) < 10:
            return False
        # No more than 3 Deobfuscated Domain Names
        if value.count('.') > 3:
            return False
        uniq_char = ''.join(set(str(value)))
        if len(uniq_char) < 6:
            return False
        fld = value.split('.')
        tld = value.rsplit('.', 1)[1].lower()
        # If only two domain levels and either second level < 6 char or tld <= 2 char, or top-level not in list
        if (len(fld) <= 2 and len(fld[0]) < 6) or tld not in self.TDLS:
            return False
        return True
