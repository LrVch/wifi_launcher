import os
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.client.EventListener import EventListener


class WifiLauncher(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, __):
        stream = os.popen('nmcli dev wifi')
        response = stream.read()

        response_list = response.split('\n')
        del response_list[0]
        response_list.pop()
        query = event.get_query()
        keyword = event.get_keyword()
        query_list = list(
            filter(lambda el: el != '' and el != keyword, query.split(' ')))
        query_key = query_list[0] if len(query_list) else None
        items = []
        filtered = []
        render_items = []

        for el in response_list:
            clear_row = list(filter(lambda el: el != '', el.split(' ')))
            inuse = '*' in clear_row[0]
            if inuse:
                del clear_row[0]
            bssid, sid, mode, chan, rate_value, rate_units, signal, bars, *security = clear_row
            items.append({
                'inuse': inuse,
                'bssid': bssid,
                'sid': sid,
                'mode': mode,
                'chan': chan,
                'rate': f'{rate_value} {rate_units}',
                'signal': signal,
                'bars': bars,
                'security': security
            })

        for el in items:
            if query_key:
                if query_key.lower() in el['sid'].lower():
                    filtered.append(el)
            else:
                filtered = items[:]

        inuse = list(filter(lambda el: el['inuse'], items[:]))
        not_inuse = list(filter(lambda el: el['inuse'] != True, filtered))
        result = inuse + not_inuse

        for el in result[:10]:
            data = {
                'el': el
            }
            render_items.append(ExtensionResultItem(
                icon='images/icon_inuse.png' if el['inuse'] else 'images/icon.png',
                name=f'{el["sid"]}',
                description=f'chan: {el["chan"]} / signal: {el["signal"]} / {el["bars"]} / security: {" ".join(el["security"])}',
                on_enter=ExtensionCustomAction(data, keep_app_open=True))
            )

        return RenderResultListAction(render_items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, _):
        data = event.get_data()
        el = data['el']

        if el['inuse']:
            return DoNothingAction()

        try:
            os.system(f'nmcli dev wifi conn {el["bssid"]}')
        except ValueError:
            print(ValueError)

        return HideWindowAction()


if __name__ == '__main__':
    WifiLauncher().run()
