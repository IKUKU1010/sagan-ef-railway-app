class DictObj:
    """Wrap a dict so attribute access works on plain dicts from sqlite"""
    def __init__(self, d):
        self.__dict__.update(d)
    def __getattr__(self, k):
        return None

def wrap(client_dict):
    """Wrap client dict and nested lists for PDF generators"""
    c = DictObj(client_dict)
    c.accounts = [DictObj(a) for a in client_dict.get('accounts', [])]
    c.liabilities = [DictObj(l) for l in client_dict.get('liabilities', [])]
    c.fica_account = DictObj(client_dict['fica_account']) if client_dict.get('fica_account') else None
    c.private_reserve_account = DictObj(client_dict['private_reserve_account']) if client_dict.get('private_reserve_account') else None
    c.trust_account = DictObj(client_dict['trust_account']) if client_dict.get('trust_account') else None
    return c
