import re
from aliases import aliases

def interpret(text: str) -> dict:

    log = logging.getLogger('intepreter')
    
    # we'll use a std dict to return the values
    cols = "symbol, sl, entry, side, tps, flag".split(', ')
    data = {k: None for k in cols}
    
    # goes through all the aliases to find a match in the text
    for k in aliases:

        comp = '|'.join([k, *aliases[k]])         # unpacking the dict
        reg = rf"(?:\b({comp})\b)"                # i.e. '\b(XAUUSD|gold|xau)\b'
        pair = re.compile(reg, re.I|re.M)
        
        if pair.search(text):
            data['symbol'] = k
            break

    # compiling sl regex
    slRE = r'(?:sl|stops?|stop ?loss)(?:\W{1,3})(\d{1,6}[\.\:]{0,2}\d{0,5})'
    slC = re.compile(slRE, re.I|re.M)

    # compiling entry regex
    entryRE = r'(?:entry|price)(?:\W{1,3})(\d{1,6}[\.\:]{0,2}\d{0,5})'
    entryC = re.compile(entryRE, re.I|re.M)

    # compiling tp regex
    tpRE = r'(?:tp|take profits?)(?: ?\d?[^a-zA-Z0-9.]{1,3})(\d{1,6}[\.\:]{0,2}\d{1,5})'
    tpC = re.compile(tpRE, re.I|re.M)

    # compiling side regex
    sideRE = r'(?:\b(buys?!?|longs?!?|sells?!?|shorts?!?)\b)'
    sideC = re.compile(sideRE, re.I|re.M)

    # compiling partials regex
    partialsRE = r'(?:\b((?:take )?partials?|take profits?)\b)'
    partialsC = re.compile(partialsRE, re.I|re.M)

    # compiling breakeven regex
    beRE = r'(?:\b((?:stops? (?:loss )?|sl )to (?:break ?even|bep?|entry))\b)'
    beC = re.compile(beRE, re.I|re.M)
    
    # move_sl
    move_slRE = r"(?:\b(?:stops? (?:loss )?(?:to )?(\d{1,6}[\.\:]{0,2}\d{0,5}))\b)"
    move_slC = re.compile(move_slRE, re.I|re.M)
    
    # manual check close
    close_match = None
    blacklist = ['if', 'candle', 'closer', 'will', 'not', 'might', 'minute', 'daily', 'support', 'been']
    if 'clos' in text.lower():
        if all(x not in text.lower() for x in blacklist):
            if len(text)<=100:
                close_match = text

    # regex results
    sl_match = slC.search(text)
    entry_match = entryC.search(text)
    side_match = sideC.search(text)
    partials_match = partialsC.search(text)
    tp_match = tpC.findall(text)
    be_match = beC.search(text)
    move_sl_match = move_slC.search(text)

    try: # assigns values
        data['sl'] = sl_match.groups()[0]
    except AttributeError:
        pass
    
    try:
        data['entry'] = entry_match.groups()[0]
    except AttributeError:
        pass
    
    try:
        data['side'] = SIDE.BUY if any(
            w in side_match.groups()[0].lower() for w in ['buy', 'long']) else SIDE.SELL
    except AttributeError:
        try: # there is no side data but let's see if we can infer it from the numbers
            if data['entry'] > data['sl']:
                data['side'] = SIDE.BUY
            else: data['side'] = SIDE.SELL
        except TypeError:
            pass
        
    # adds tps
    data['tps'] = tp_match

    # if data[side] is missing it means that there was no sl, no entry and no direction
    if data['side'] is None:

        # could be a close signal
        if close_match is not None:
            data['flag'] = FLAG.CLOSE

        elif be_match is not None:
            data['flag'] = FLAG.BREAKEVEN
        
        elif move_sl_match is not None:
            data['flag'] = FLAG.MOVE_SL
            data['sl'] = move_sl_match.groups()[0]

        # could be a partials signal
        elif partials_match is not None:
            data['flag'] = FLAG.PARTIALS

        # could be a update-tp
        elif len(tp_match) > 0:
            data['flag'] = FLAG.UPDATE_TP

        else: # it's just a text
            data['flag'] = FLAG.MESSAGE

        return data

    # no sl, no symbol or no side, returns with 'no-data' flag
    if any(x is None for x in [sl_match, data['symbol'], data['side']]):
        data['flag'] = FLAG.ERROR
        return data

    # the only other case is limit & market order
    data['flag'] = FLAG.ORDER
    return data