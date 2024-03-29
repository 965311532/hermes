from .aliases import aliases
from typing import Union, Callable
import re, logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class TooManyFeatures(ValueError):
    """Raises when there are too many features of a certain kind in the same signal."""

    def __init__(self, message, text):
        self.message = message
        self.text = text
        super().__init__(message, text)


class Hermes:
    def __init__(self, text: str):
        self.text = self.preprocess(text)
        self.features = {}

    # TODO
    def preprocess(self, text: str) -> str:
        return text

    def search_algo(self, algo: Callable, *args, allow_max=1) -> Union[list, None, str]:
        result_algo = algo(self.text, *args)
        if isinstance(result_algo, list):
            if len(result_algo) > allow_max:
                raise TooManyFeatures(f"{algo.__name__} = {result_algo}", self.text)
            if len(result_algo) == 1:
                result_algo = result_algo[0]

        if result_algo:
            log.debug(f"doing {algo.__name__}, found {result_algo}")
        return result_algo if result_algo else None


def search_regex(text: str, regex: str) -> Union[None, list]:
    # i'm not sure this is actually effective
    compiled = re.compile(regex, re.I | re.M)
    search_result = compiled.findall(text)
    return search_result


def search_symbol(text: str):
    """Sequentially goes through all of the aliases until it finds a match"""
    results = list()
    for k in aliases:

        # unpacking the dict
        comp = "|".join([k, *aliases[k]])
        # i.e. '\b(XAUUSD|gold|xau)\b'
        regex = rf"(?:\b({comp})\b)"

        search_result = search_regex(text, regex)
        if search_result:
            log.debug(f"found {k}")
            results.append(k)

    return list(set(results))


def search_close(text: str):
    # manual check close
    blacklist = [
        "if",
        "candle",
        "closer",
        "will",
        "not",
        "might",
        "minute",
        "daily",
        "support",
        "been",
    ]

    if "clos" in text.lower():
        if all(x not in text.lower() for x in blacklist):
            if len(text) <= 100:
                return text
    return None


def interpret(text: str) -> dict:

    SL = r"(?:sl|stops?|stop ?loss)(?:\W{1,3})(\d{1,6}[\.\:]{0,2}\d{0,5})"
    ENTRY = r"(?:entry|price)(?:\W{1,3})(\d{1,6}[\.\:]{0,2}\d{0,5})"
    TP = r"(?:tp|take profits?)(?: ?\d?[^a-zA-Z0-9.]{1,3})(\d{1,6}[\.\:]{0,2}\d{1,5})"
    SIDE = r"(?:\b(buys?!?|longs?!?|sells?!?|shorts?!?)\b)"
    PARTIALS = r"(?:\b((?:take )?partials?|take profits?)\b)"
    BREAKEVEN = r"(?:\b((?:stops? (?:loss )?|sl )to (?:break ?even|bep?|entry))\b)"
    MOVE_SL = r"(?:\b(?:stops? (?:loss )?(?:to )?(\d{1,6}[\.\:]{0,2}\d{0,5}))\b)"

    hermes = Hermes(text)

    data = {
        "symbol": hermes.search_algo(search_symbol),
        "entry": hermes.search_algo(search_regex, ENTRY),
        "sl": hermes.search_algo(search_regex, SL),
        "tp": hermes.search_algo(search_regex, TP, allow_max=10),
        "side": hermes.search_algo(search_regex, SIDE),
        "partials": hermes.search_algo(search_regex, PARTIALS),
        "breakeven": hermes.search_algo(search_regex, BREAKEVEN),
        "close": hermes.search_algo(search_close),
    }

    if data["symbol"] and data["sl"] and data["side"]:
        data["flag"] = "POSITION"

    else:  # these are updates
        allowed = "tp partials breakeven close".split(" ")
        try:
            data["flag"] = [f"update_{x}" for x in data if (data[x] and x in allowed)][
                0
            ].upper()
        except IndexError:  # none of the allowed keywords are in data
            pass

    # only return data that is actually present
    return {k: v for k, v in data.items() if v}


def main():

    test = "Entry: 1.15, SL: 1.12, Side: longs!!!, SL:11.5 Pair: EURUSD!"
    log.debug(test)
    print(interpret(test))


if __name__ == "__main__":
    main()
